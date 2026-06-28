"""실험 15 cross-model 사이드테스트: Ephemeral Context Router on ministral-3:8b (Ollama Cloud).

목적: H15 (Context 외부화) 가 canonical 모델 gemma4:e4b 밖의 cross-family 소형 dense
모델(ministral-3:8b)로 일반화되는지 *예비* 확인.

⚠ 배경 — orchestrator.py:521-528 의 model_caller 경로는 모델이 돌려준 tool_calls 를
   실행하지 않는다 (tool_call_log=[] 로 버림). 따라서 cloud 모델로 Router arm(B/D)을
   돌리려면 caller 내부에서 tool-execution loop 를 완결해야 한다. 본 스크립트의
   make_ollama_cloud_tool_caller 가 그 역할을 한다 — 공유 orchestrator/Stage6 경로
   불변 (단일 신규 파일, side 브랜치 격리).

실행: 사용자 승인 하에 Ollama Cloud 로 직접 실행 (로컬 VRAM 무관).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# gemento/experiments 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from tools.context_tools import get_redis_client, CONTEXT_TOOL_FUNCTIONS
from orchestrator import run_abc_chain
from _external import resolve_ollama_cloud_key

_DIR = Path(__file__).resolve().parent
RESULTS_DIR = _DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_CLOUD_URL = "https://ollama.com/v1/chat/completions"
MODEL_ID = "ministral-3:8b"
MAX_TOOL_ITERS = 6  # caller 내부 tool-loop 상한 (무한 루프 방지)


def make_ollama_cloud_tool_caller(model_id: str, api_key_slot: int = 1):
    """Ollama Cloud caller with an INTERNAL tool-execution loop.

    model_caller signature: (messages, tools=None, **kwargs) -> (content_str, meta_dict).

    tools 가 주어지면 모델이 돌려준 tool_calls 를 CONTEXT_TOOL_FUNCTIONS 로 직접 실행하고
    결과를 messages 에 append 후 재호출하는 OpenAI-style tool loop 를 caller 내부에서
    완결한다. tool_calls 가 없으면 content 를 최종 응답으로 반환.
    """
    key = resolve_ollama_cloud_key(slot=api_key_slot)

    def _post(messages: list[dict], tools=None) -> tuple[dict, str | None]:
        payload: dict = {
            "model": model_id,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 4096,
        }
        if tools:
            payload["tools"] = tools
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        try:
            with httpx.Client(timeout=180) as client:
                resp = client.post(OLLAMA_CLOUD_URL, headers=headers, json=payload)
                resp.raise_for_status()
                return resp.json(), None
        except httpx.HTTPStatusError as e:
            body = ""
            try:
                body = e.response.text[:300]
            except Exception:
                pass
            return {}, f"HTTP {e.response.status_code}: {body}"
        except Exception as e:
            return {}, str(e)

    def _caller(messages: list[dict], tools=None, **kwargs) -> tuple[str, dict]:
        start = time.time()
        # messages 를 복사해서 누적 (호출자 측 messages 오염 방지)
        convo = list(messages)
        in_tok = out_tok = 0
        tool_rounds = 0
        last_err = None

        for _ in range(MAX_TOOL_ITERS + 1):
            data, err = _post(convo, tools=tools)
            if err:
                last_err = err
                break
            usage = data.get("usage") or {}
            in_tok += usage.get("prompt_tokens", 0)
            out_tok += usage.get("completion_tokens", 0)

            choices = data.get("choices") or []
            if not choices:
                last_err = "no choices in response"
                break
            msg = choices[0].get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            content = msg.get("content") or ""

            if not tool_calls:
                # 최종 응답
                meta = {
                    "input_tokens": in_tok, "output_tokens": out_tok,
                    "duration_ms": int((time.time() - start) * 1000),
                    "cost_usd": 0.0, "error": None, "reasoning_tokens": 0,
                    "tool_rounds": tool_rounds,
                }
                return content, meta

            # tool_calls 실행
            tool_rounds += 1
            convo.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
            for tc in tool_calls:
                fn = (tc.get("function") or {})
                name = fn.get("name")
                raw_args = fn.get("arguments") or "{}"
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                except json.JSONDecodeError:
                    args = {}
                func = CONTEXT_TOOL_FUNCTIONS.get(name)
                if func is None:
                    result = {"error": f"unknown tool: {name}"}
                else:
                    try:
                        result = func(**args)
                    except Exception as ex:
                        result = {"error": f"tool execution failed: {ex}"}
                convo.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "name": name,
                    "content": json.dumps(result, ensure_ascii=False),
                })
            # 루프 계속 → 모델 재호출

        # 루프 상한 도달 or 에러: 마지막 content 반환 (없으면 빈 문자열)
        meta = {
            "input_tokens": in_tok, "output_tokens": out_tok,
            "duration_ms": int((time.time() - start) * 1000),
            "cost_usd": 0.0, "error": last_err or "max tool iters reached",
            "reasoning_tokens": 0, "tool_rounds": tool_rounds,
        }
        return "", meta

    return _caller


def setup_redis_log() -> str:
    """exp15 run.py 와 동일한 35KB mock Rust 빌드 로그를 Redis 에 적재."""
    redis_key = "ctx:exp15_xmodel_log:stdout"
    r = get_redis_client()
    lines = []
    for i in range(1, 801):
        if i == 342:
            lines.append("error[E0432]: unresolved import `crate::router::SemanticRouter` in src/main.rs:342")
        elif i == 512:
            lines.append("warning: unused import: `std::collections::HashMap` in src/utils.py:12")
        elif i == 789:
            lines.append("error: aborting due to previous error; 1 warning emitted")
        else:
            lines.append(f"[INFO] 2026-06-28 10:15:{i:02d} - Building crate gemento v1.0.0 (step {i}/800)... success")
    r.set(redis_key, "\n".join(lines))
    print(f"  [Setup] 35KB mock compilation log → Redis key: {redis_key}")
    return redis_key


def main():
    print("=" * 80)
    print(f"실험 15 cross-model 사이드테스트: {MODEL_ID} (Ollama Cloud) A/B/C/D")
    print("=" * 80)

    if not resolve_ollama_cloud_key(slot=1):
        print("  [ABORT] OLLAMA_CLOUD_API_KEY not found (env or .env)")
        sys.exit(1)

    redis_key = setup_redis_log()
    r = get_redis_client()
    raw_log = r.get(redis_key)

    objective = "Find the exact file name, line number, and unresolved import module that caused the compilation failure."
    scoring_keywords = [["src/main.rs"], ["342"], ["SemanticRouter"]]

    def score(ans) -> float:
        if not ans:
            return 0.0
        if isinstance(ans, dict):
            ans = json.dumps(ans, ensure_ascii=False)
        elif not isinstance(ans, str):
            ans = str(ans)
        matched = sum(1 for grp in scoring_keywords if all(t.lower() in ans.lower() for t in grp))
        return matched / len(scoring_keywords)

    caller = make_ollama_cloud_tool_caller(MODEL_ID, api_key_slot=1)
    constraints = ["에러가 발생한 파일과 라인을 정확히 기재하라", "unresolved import 모듈명을 적어라"]

    prompt_stuffing = (
        "Here is the raw compilation output log:\n\n"
        f"```text\n{raw_log}\n```\n\n"
        "Find the file name, line number, and the module import error details."
    )
    prompt_router = (
        "A compilation error occurred during build. The raw output is cached in Redis.\n"
        f"Available Context Handle: {redis_key}\n\n"
        "Please inspect the log and find the exact file name, line number, and unresolved import module error."
    )

    arms = [
        ("stuffing",          dict(prompt=prompt_stuffing, context_router=False, error_blocks=False)),
        ("router_basic",      dict(prompt=prompt_router,   context_router=True,  error_blocks=False, context_handles=[redis_key])),
        ("error_blocks_only", dict(prompt=prompt_router,   context_router=False, error_blocks=True,  context_handles=[redis_key])),
        ("hybrid",            dict(prompt=prompt_router,   context_router=True,  error_blocks=True,  context_handles=[redis_key])),
    ]

    results = {}
    for name, kw in arms:
        print("\n" + "-" * 50)
        print(f"[Arm {name}] running on {MODEL_ID} ...")
        print("-" * 50)
        start = time.time()
        try:
            tattoo, logs, ans = run_abc_chain(
                task_id=f"exp15_xmodel_{name}",
                objective=objective,
                constraints=constraints,
                max_cycles=5,
                model_caller=caller,
                **kw,
            )
            dur = time.time() - start
            results[name] = {
                "score": score(ans),
                "duration": dur,
                "answer": ans,
                "cycles": len(logs),
                "tool_calls": [c.tool_calls for c in logs if c.tool_calls],
            }
        except Exception as e:
            results[name] = {"score": 0.0, "duration": time.time() - start,
                             "answer": None, "cycles": 0, "error": str(e)}
        rr = results[name]
        print(f"  → score={rr['score']:.1%} | dur={rr['duration']:.1f}s | cycles={rr.get('cycles')} | err={rr.get('error')}")
        print(f"  → answer={rr['answer']}")

    out = {
        "experiment": "exp15_context_router_crossmodel",
        "model": MODEL_ID,
        "provider": "ollama_cloud",
        "note": "arm당 n=1 예비 cross-model 사이드테스트. caller 내부 tool-loop 사용.",
        "results": results,
    }
    out_path = RESULTS_DIR / f"exp15_crossmodel_{MODEL_ID.replace(':', '_').replace('-', '_')}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\n  → results saved: {out_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
