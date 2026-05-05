"""Groq Cloud API client with token/time/cost metering.

OpenAI-compatible endpoint: https://api.groq.com/openai/v1/chat/completions
LPU-based inference, very fast (~2200 tok/s for Llama 3.1 8B).

Free tier (2026-05): 30 RPM / 6K TPM / 1000 RPD per model. 128K context for
most models. No credit card required. See https://console.groq.com/docs/rate-limits.

Cross-model 용도: Stage 6 cross-model replication (H1 / H7 / H8 / H9a / H11 / H12)
의 외부 모델 baseline. Llama 3.1 8B / Llama 3.3 70B / Qwen QwQ 32B / DeepSeek R1
Distill 70B 다중 모델 비교 시 본 client 사용.

cost_usd 는 free tier 시 $0. paid tier 갱신 시 별도 상수 추가.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from . import resolve_groq_key


GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_TIMEOUT = 120

# 2026-05-05 기준 Groq 활성 production 모델 — 사용자가 실험 시점 재확인 권장.
# https://console.groq.com/docs/models — Qwen QwQ 32B / DeepSeek R1 Distill 등은 decommissioned.
LLAMA_3_1_8B = "llama-3.1-8b-instant"        # 8B, 128K, ~2200 tok/s. cross-model main
LLAMA_3_3_70B = "llama-3.3-70b-versatile"    # 70B, 128K. ceiling check
GPT_OSS_20B = "openai/gpt-oss-20b"           # 20B, 128K. mid-size
GPT_OSS_120B = "openai/gpt-oss-120b"         # 120B, 128K. high ceiling
# Preview (paid only — 무료 cross-model 미사용):
# QWEN3_32B = "qwen/qwen3-32b"  # $0.29/$0.59 per 1M tokens


# 무료 티어 비용 = $0. paid tier 시 입력/출력 단가 갱신.
# 예: Llama 3.1 8B paid = $0.05/$0.08 per 1M tokens (2026-05 기준)
DEFAULT_INPUT_COST_PER_1M = 0.0
DEFAULT_OUTPUT_COST_PER_1M = 0.0


@dataclass
class CallMeter:
    """단일 LLM 호출의 측정 결과. gemini_client.CallMeter 의 superset.

    reasoning_tokens 필드는 GPT-OSS 등 reasoning model (o1-style) 에서 채워짐.
    일반 모델 (Llama 3.1 8B 등) 에서는 0.
    """
    raw_response: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    cost_usd: float
    model: str
    error: str | None = None
    reasoning_tokens: int = 0     # GPT-OSS 등 reasoning model
    reasoning_text: str | None = None  # 내부 reasoning trace (디버그용)


def call_with_meter(
    messages: list[dict],
    model: str = LLAMA_3_1_8B,
    timeout: int = DEFAULT_TIMEOUT,
    api_key: str | None = None,
    response_format: dict | None = None,
    temperature: float = 0.1,
    max_tokens: int = 4096,
    input_cost_per_1m: float = DEFAULT_INPUT_COST_PER_1M,
    output_cost_per_1m: float = DEFAULT_OUTPUT_COST_PER_1M,
    tools: list | None = None,
    tool_choice: str | dict | None = None,
) -> CallMeter:
    """Groq API 호출 + metering.

    OpenAI Chat Completions 호환. response_format={'type':'json_object'} 로 JSON 강제.
    tools/tool_choice 는 Llama 3.1+ 의 OpenAI tool-calling 호환.
    """
    key = api_key or resolve_groq_key()
    if not key:
        return CallMeter(
            raw_response="", input_tokens=0, output_tokens=0,
            duration_ms=0, cost_usd=0.0, model=model,
            error="GROQ_API_KEY not found in env or gemento/.env",
        )

    payload: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format
    if tools:
        payload["tools"] = tools
    if tool_choice:
        payload["tool_choice"] = tool_choice

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    start = time.time()
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(GROQ_BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
        # rate limit (429) / auth (401) / invalid request (400) 식별
        body = ""
        try:
            body = e.response.text[:500]
        except Exception:
            pass
        return CallMeter(
            raw_response="", input_tokens=0, output_tokens=0,
            duration_ms=int((time.time() - start) * 1000),
            cost_usd=0.0, model=model,
            error=f"HTTP {e.response.status_code}: {body}",
        )
    except Exception as e:
        return CallMeter(
            raw_response="", input_tokens=0, output_tokens=0,
            duration_ms=int((time.time() - start) * 1000),
            cost_usd=0.0, model=model, error=str(e),
        )

    duration_ms = int((time.time() - start) * 1000)

    # OpenAI 호환 응답 파싱 — choices[0].message.content (+ reasoning for o1-style)
    content_text = ""
    reasoning_text: str | None = None
    choices = data.get("choices") or []
    if choices:
        msg = (choices[0].get("message") or {})
        content_text = msg.get("content") or ""
        reasoning_text = msg.get("reasoning")  # GPT-OSS 등에서만 존재

    usage = data.get("usage") or {}
    in_tok = usage.get("prompt_tokens", 0)
    out_tok = usage.get("completion_tokens", 0)
    # reasoning_tokens 는 completion_tokens 안에 포함되어 있음 (별도 차감 안 함)
    reasoning_tok = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
    cost = (
        in_tok * input_cost_per_1m / 1_000_000
        + out_tok * output_cost_per_1m / 1_000_000
    )
    return CallMeter(
        raw_response=content_text, input_tokens=in_tok, output_tokens=out_tok,
        duration_ms=duration_ms, cost_usd=cost, model=model, error=None,
        reasoning_tokens=reasoning_tok, reasoning_text=reasoning_text,
    )
