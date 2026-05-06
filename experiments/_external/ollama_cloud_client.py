"""Ollama Cloud API client with token/time/cost metering.

OpenAI-compatible endpoint: https://ollama.com/v1/chat/completions
Bearer token auth (public key 와 별개의 API key 필요 — https://ollama.com/settings/keys).

Free tier (2026-05): GPU-time based, "light usage" — burst 호출 가능 (Groq 의 30 RPM 같은
hard rate limit 없음). 5h session reset / 7d weekly reset. 1 concurrent model only.

Cross-model 용도: Stage 6 cross-model replication 의 main 외부 모델 baseline.
qwen3.5 / gemma4 / ministral-3 / nemotron-3-nano 등 다중 size 비교.

cost_usd 는 free tier 시 $0. paid tier ($20 Pro / $100 Max) 시 별도 추적 가능.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from . import resolve_ollama_cloud_key


OLLAMA_CLOUD_BASE_URL = "https://ollama.com/v1/chat/completions"
DEFAULT_TIMEOUT = 180

# 2026-05-06 기준 Ollama Cloud 활성 모델 (GET /v1/models 검증).
# https://ollama.com/search?c=cloud — 시점별 변동 가능, 호출 시 재확인 권장.
GEMMA_3_4B = "gemma3:4b"             # 4B, gemento E4B (effective 4B) 와 동급 — best baseline cross-model
GEMMA_3_12B = "gemma3:12b"           # 12B, Gemma family scaling up
GEMMA_3_27B = "gemma3:27b"           # 27B, Gemma family large
GEMMA_4_31B = "gemma4:31b"           # 31B, Gemma 4 family
RNJ_1_8B = "rnj-1:8b"                # 8B, gemento E4B size class up
MINISTRAL_3_3B = "ministral-3:3b"    # 3B, E4B 보다 작음
MINISTRAL_3_14B = "ministral-3:14b"  # 14B, Mistral mid-size
GPT_OSS_20B_OLLAMA = "gpt-oss:20b"   # 20B, OpenAI open-source
GPT_OSS_120B_OLLAMA = "gpt-oss:120b" # 120B, ceiling check
QWEN_3_NEXT_80B = "qwen3-next:80b"   # 80B, Qwen 차세대
NEMOTRON_3_NANO_30B = "nemotron-3-nano:30b"  # 30B, NVIDIA
DEVSTRAL_SMALL_2 = "devstral-small-2:24b"    # 24B, dev


# 무료 티어 비용 = $0. paid tier 시 단가 갱신.
DEFAULT_INPUT_COST_PER_1M = 0.0
DEFAULT_OUTPUT_COST_PER_1M = 0.0


@dataclass
class CallMeter:
    """단일 LLM 호출의 측정 결과. groq_client.CallMeter 와 동일 schema."""
    raw_response: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    cost_usd: float
    model: str
    error: str | None = None
    reasoning_tokens: int = 0     # reasoning model (있다면)
    reasoning_text: str | None = None


def call_with_meter(
    messages: list[dict],
    model: str = GEMMA_3_4B,
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
    """Ollama Cloud API 호출 + metering.

    OpenAI Chat Completions 호환. response_format={'type':'json_object'} 로 JSON 강제.
    tools/tool_choice 는 모델별 호환성 다름 (Qwen/Llama 호환, 일부 모델 미호환).
    """
    key = api_key or resolve_ollama_cloud_key()
    if not key:
        return CallMeter(
            raw_response="", input_tokens=0, output_tokens=0,
            duration_ms=0, cost_usd=0.0, model=model,
            error="OLLAMA_CLOUD_API_KEY not found in env or gemento/.env",
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
            response = client.post(OLLAMA_CLOUD_BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
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

    # OpenAI 호환 응답 파싱
    content_text = ""
    reasoning_text: str | None = None
    choices = data.get("choices") or []
    if choices:
        msg = (choices[0].get("message") or {})
        content_text = msg.get("content") or ""
        reasoning_text = msg.get("reasoning")  # reasoning model 일 경우

    usage = data.get("usage") or {}
    in_tok = usage.get("prompt_tokens", 0)
    out_tok = usage.get("completion_tokens", 0)
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


def with_quota_retry(max_retries: int = 3, initial_wait: float = 30.0):
    """429 / quota exceeded 응답 시 exponential backoff. Ollama Cloud 는 GPU time 기반이라
    Groq 의 RPM 보다 회복 시간이 길 수 있음 — initial_wait=30s.
    """
    def decorator(fn):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                result: CallMeter = fn(*args, **kwargs)
                if result.error and ("HTTP 429" in result.error or "quota" in result.error.lower()):
                    if attempt < max_retries:
                        wait = initial_wait * (2 ** attempt)
                        print(f"  [quota] wait {wait}s (attempt {attempt+1}/{max_retries})")
                        time.sleep(wait)
                        continue
                return result
            return result
        return wrapper
    return decorator


@with_quota_retry(max_retries=2, initial_wait=30.0)
def call_with_meter_retry(messages, model=GEMMA_3_4B, **kwargs) -> CallMeter:
    """call_with_meter 의 quota retry wrapper."""
    return call_with_meter(messages, model=model, **kwargs)
