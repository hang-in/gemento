"""Native Ollama /api/chat caller with per-request num_ctx control + internal tool loop.

gemento 의 기본 call_model 은 /v1/chat/completions (OpenAI-compat) 를 쓰며 num_ctx 를
요청 단위로 제어할 수 없고, model_caller 경로는 tool_calls 를 실행하지 않는다
(orchestrator.py:521-528). 본 caller 는 그 두 한계를 모두 우회한다:

  1. Ollama 네이티브 /api/chat 호출 → options.num_ctx 로 컨텍스트를 요청 단위 제어.
  2. caller 내부에서 tool 실행 루프 완결 (CONTEXT_TOOL_FUNCTIONS 직접 실행).
  3. 호출별 tool_rounds / 토큰 / truncation 신호를 stats dict 에 누적 (측정 갭 보완).

공유 orchestrator/Stage6 코드 불변 — side 브랜치 격리용 신규 모듈.
"""
from __future__ import annotations

import json
import time

import httpx

from tools.context_tools import CONTEXT_TOOL_FUNCTIONS

MAX_TOOL_ITERS = 8


def make_ollama_native_caller(base_url: str, model: str, num_ctx: int,
                              stats: dict | None = None,
                              max_tokens: int = 4096, temperature: float = 0.1,
                              extra_tool_schemas=None, extra_tool_fns=None):
    """model_caller signature: (messages, tools=None, **kwargs) -> (content_str, meta).

    base_url: 예 'http://127.0.0.1:11435' (터널). /api/chat 가 붙는다.
    num_ctx: 이 caller 가 거는 모든 요청의 컨텍스트 길이 (요인 변수).
    stats: 주어지면 caller 가 calls/tool_rounds/in_tok/out_tok 를 누적 (driver 가 trial 별 측정).
    """
    url = base_url.rstrip("/") + "/api/chat"
    _exec = {**CONTEXT_TOOL_FUNCTIONS, **(extra_tool_fns or {})}

    def _post(messages, tools):
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": "10m",
            "options": {"num_ctx": num_ctx, "temperature": temperature, "num_predict": max_tokens},
        }
        if tools:
            payload["tools"] = tools
        with httpx.Client(timeout=600) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()

    def _caller(messages, tools=None, **kwargs):
        eff_tools = list(tools or [])
        if extra_tool_schemas:
            eff_tools = eff_tools + list(extra_tool_schemas)
        start = time.time()
        convo = list(messages)
        in_tok = out_tok = tool_rounds = 0
        last_err = None
        final_content = ""

        for _ in range(MAX_TOOL_ITERS + 1):
            try:
                data = _post(convo, eff_tools or None)
            except Exception as e:
                last_err = str(e)
                break
            in_tok += data.get("prompt_eval_count", 0) or 0
            out_tok += data.get("eval_count", 0) or 0
            msg = data.get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            content = msg.get("content") or ""

            if not tool_calls:
                final_content = content
                break

            tool_rounds += 1
            convo.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
            for tc in tool_calls:
                fn = tc.get("function") or {}
                name = fn.get("name")
                raw_args = fn.get("arguments")
                if isinstance(raw_args, str):
                    try:
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        args = {}
                else:
                    args = raw_args or {}
                func = _exec.get(name)
                if func is None:
                    result = {"error": f"unknown tool: {name}"}
                else:
                    try:
                        result = func(**args)
                    except Exception as ex:
                        result = {"error": f"tool execution failed: {ex}"}
                convo.append({
                    "role": "tool",
                    "tool_name": name,
                    "content": json.dumps(result, ensure_ascii=False),
                })
        else:
            last_err = last_err or "max tool iters reached"

        if stats is not None:
            stats["calls"] = stats.get("calls", 0) + 1
            stats["tool_rounds"] = stats.get("tool_rounds", 0) + tool_rounds
            stats["in_tok"] = stats.get("in_tok", 0) + in_tok
            stats["out_tok"] = stats.get("out_tok", 0) + out_tok

        meta = {
            "input_tokens": in_tok, "output_tokens": out_tok,
            "duration_ms": int((time.time() - start) * 1000),
            "cost_usd": 0.0, "error": last_err, "reasoning_tokens": 0,
            "tool_rounds": tool_rounds,
        }
        return final_content, meta

    return _caller
