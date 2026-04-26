"""LM Studio client with token/time metering for Exp10.

config.py 의 API_CHAT_URL 을 호출. metering 은 OpenAI 와 동일 인터페이스.
LM Studio 는 로컬이라 cost_usd=0.
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path

# experiments/ 를 sys.path 에 추가하여 config import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from config import API_CHAT_URL, API_TIMEOUT, MODEL_NAME, SAMPLING_PARAMS


@dataclass
class LMStudioMeter:
    """단일 LM Studio 호출의 측정 결과."""
    raw_response: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    cost_usd: float            # 항상 0.0 (로컬)
    model: str
    error: str | None = None


def call_with_meter(
    messages: list[dict],
    model: str = MODEL_NAME,
    timeout: int = API_TIMEOUT,
    response_format: dict | None = None,
    sampling_overrides: dict | None = None,
) -> LMStudioMeter:
    """LM Studio API 호출 + metering."""
    sampling = dict(SAMPLING_PARAMS)
    if sampling_overrides:
        sampling.update(sampling_overrides)

    payload: dict = {"model": model, "messages": messages}
    for k, v in sampling.items():
        if v is not None:
            payload[k] = v
    if response_format is not None:
        payload["response_format"] = response_format

    headers = {"Content-Type": "application/json"}

    start = time.time()
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(API_CHAT_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        return LMStudioMeter(
            raw_response="", input_tokens=0, output_tokens=0,
            duration_ms=int((time.time() - start) * 1000),
            cost_usd=0.0, model=model, error=str(e),
        )

    duration_ms = int((time.time() - start) * 1000)
    content = data["choices"][0]["message"]["content"] or ""
    usage = data.get("usage", {})
    return LMStudioMeter(
        raw_response=content,
        input_tokens=usage.get("prompt_tokens", 0),
        output_tokens=usage.get("completion_tokens", 0),
        duration_ms=duration_ms, cost_usd=0.0, model=model, error=None,
    )
