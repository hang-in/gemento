"""Google AI Studio (Gemini API) client with token/time/cost metering for Exp10.

Endpoint: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
default model: gemini-2.5-flash
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from . import resolve_gemini_key


# 2025-04 기준 Gemini 2.5 Flash 공시 가격 (per 1M tokens)
# https://ai.google.dev/pricing — 사용자가 실험 시점에 재확인 필요
GEMINI_25_FLASH_INPUT_COST_PER_1M = 0.075
GEMINI_25_FLASH_OUTPUT_COST_PER_1M = 0.30

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TIMEOUT = 120
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


@dataclass
class CallMeter:
    """단일 LLM 호출의 측정 결과."""
    raw_response: str          # text content
    input_tokens: int
    output_tokens: int
    duration_ms: int
    cost_usd: float
    model: str
    error: str | None = None


def _convert_messages_to_gemini(messages: list[dict]) -> tuple[str | None, list[dict]]:
    """OpenAI 스타일 messages → Gemini API 형식 변환.

    Returns:
        (system_instruction_text or None, contents list)

    Gemini 는 system 을 별도 필드로 받음. messages 의 첫 번째가 system 이면 분리.
    """
    system_text: str | None = None
    contents: list[dict] = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "system":
            # 여러 system 있으면 합침
            system_text = (system_text + "\n" + content) if system_text else content
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
    return system_text, contents


def call_with_meter(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    timeout: int = DEFAULT_TIMEOUT,
    api_key: str | None = None,
    response_mime_type: str | None = "application/json",
    input_cost_per_1m: float = GEMINI_25_FLASH_INPUT_COST_PER_1M,
    output_cost_per_1m: float = GEMINI_25_FLASH_OUTPUT_COST_PER_1M,
) -> CallMeter:
    """Gemini API 호출 + metering. response_mime_type='application/json' 으로 JSON 응답 강제 가능."""
    key = api_key or resolve_gemini_key()
    if not key:
        return CallMeter(
            raw_response="", input_tokens=0, output_tokens=0,
            duration_ms=0, cost_usd=0.0, model=model,
            error="GEMINI_API_KEY not found in env/gemento/.env/secall/.env"
        )

    system_text, contents = _convert_messages_to_gemini(messages)

    payload: dict = {"contents": contents}
    generation_config: dict = {}
    if response_mime_type:
        generation_config["responseMimeType"] = response_mime_type
    if generation_config:
        payload["generationConfig"] = generation_config
    if system_text:
        payload["systemInstruction"] = {"parts": [{"text": system_text}]}

    url = f"{GEMINI_BASE_URL}/{model}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}

    start = time.time()
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        return CallMeter(
            raw_response="", input_tokens=0, output_tokens=0,
            duration_ms=int((time.time() - start) * 1000),
            cost_usd=0.0, model=model, error=str(e),
        )

    duration_ms = int((time.time() - start) * 1000)

    # Gemini 응답 파싱 — candidates[0].content.parts[].text 합침
    content_text = ""
    candidates = data.get("candidates") or []
    if candidates:
        parts = (candidates[0].get("content") or {}).get("parts") or []
        content_text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))

    usage = data.get("usageMetadata") or {}
    in_tok = usage.get("promptTokenCount", 0)
    out_tok = usage.get("candidatesTokenCount", 0)
    cost = (
        in_tok * input_cost_per_1m / 1_000_000
        + out_tok * output_cost_per_1m / 1_000_000
    )
    return CallMeter(
        raw_response=content_text, input_tokens=in_tok, output_tokens=out_tok,
        duration_ms=duration_ms, cost_usd=cost, model=model, error=None,
    )
