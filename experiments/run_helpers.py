"""Multi-trial 실행 도구 공통 helper.

healthcheck / abort 정책 + 결과 JSON top-level meta 표준화 (subtask 03 에서 확장).
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class TrialError(Enum):
    """trial error 분류. fatal 여부는 ``is_fatal_error`` 참조."""

    NONE = "none"
    CONNECTION_ERROR = "connection_error"  # WinError 10061, refused, ENOTFOUND, dns
    TIMEOUT = "timeout"                     # ReadTimeout, asyncio.TimeoutError
    PARSE_ERROR = "parse_error"             # JSON parse fail
    MODEL_ERROR = "model_error"             # 모델 응답 자체의 error (4xx, 5xx 본문)
    OTHER = "other"                         # 미분류


# 분류용 substring (소문자 비교, 보수적 시작)
_PATTERN_CONNECTION = (
    "connection refused",
    "winerror 10061",
    "대상 컴퓨터에서 연결을 거부",
    "connection reset",
    "connection aborted",
    "no route to host",
    "name or service not known",
    "name resolution",
    "getaddrinfo failed",
    "[errno 111]",  # linux ECONNREFUSED
)
_PATTERN_TIMEOUT = (
    "readtimeout",
    "timeout",
    "timed out",
)
_PATTERN_PARSE = (
    "json parse",
    "jsondecodeerror",
    "expecting value",
    "expecting property name",
)


def classify_trial_error(error_msg: str | None) -> TrialError:
    """error 문자열을 TrialError 로 분류.

    None 또는 빈 문자열이면 NONE. 패턴 매칭은 소문자 substring (보수적).
    """
    if not error_msg:
        return TrialError.NONE
    s = str(error_msg).lower()
    for pat in _PATTERN_CONNECTION:
        if pat in s:
            return TrialError.CONNECTION_ERROR
    for pat in _PATTERN_TIMEOUT:
        if pat in s:
            return TrialError.TIMEOUT
    for pat in _PATTERN_PARSE:
        if pat in s:
            return TrialError.PARSE_ERROR
    return TrialError.OTHER


def is_fatal_error(err: TrialError) -> bool:
    """fatal = 즉시 abort 가 정합한 error 분류.

    현재 정책: CONNECTION_ERROR 단독 fatal. TIMEOUT/PARSE/MODEL/OTHER 는 non-fatal
    (trial 단위 fail 으로 기록하되 run 전체 중단은 안 함).
    """
    return err == TrialError.CONNECTION_ERROR


def check_error_rate(
    trials: list[dict[str, Any]], threshold: float = 0.30
) -> tuple[bool, float]:
    """저장 직전 trial 별 error 비율 검사.

    Returns:
        (ok, rate). ok=False 면 호출자가 저장 거부 또는 사용자 알림.
        rate = error 가 None 이 아니거나 final_answer 가 None 인 trial 의 비율.
    """
    if not trials:
        return True, 0.0
    bad = sum(
        1
        for t in trials
        if t.get("error") is not None or t.get("final_answer") is None
    )
    rate = bad / len(trials)
    return rate < threshold, rate


def build_result_meta(
    *,
    experiment: str,
    model_name: str,
    model_engine: str,
    model_endpoint: str | None,
    sampling_params: dict[str, Any],
    scorer_version: str,
    taskset_version: str | None = None,
    started_at: str | None = None,
    ended_at: str | None = None,
    schema_version: str = "1.0",
) -> dict[str, Any]:
    """결과 JSON top-level meta 표준 dict 반환 (subtask 03 에서 호출).

    각 도구의 결과 저장 직전에 호출하여 dict 의 top-level 에 unpack 추천.
    """
    meta: dict[str, Any] = {
        "schema_version": schema_version,
        "experiment": experiment,
        "model": {
            "name": model_name,
            "engine": model_engine,
            "endpoint": model_endpoint,
        },
        "sampling_params": dict(sampling_params),
        "scorer_version": scorer_version,
    }
    if taskset_version is not None:
        meta["taskset_version"] = taskset_version
    if started_at is not None:
        meta["started_at"] = started_at
    if ended_at is not None:
        meta["ended_at"] = ended_at
    return meta


def get_taskset_version() -> str | None:
    """taskset.json 의 git short hash 반환. 깨지면 None.

    git 미설치 / 변경된 파일 등 경계 상황은 None 반환 (silent fallback).
    """
    import subprocess
    from pathlib import Path

    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h", "experiments/tasks/taskset.json"],
            capture_output=True, text=True, cwd=Path(__file__).resolve().parent.parent,
            timeout=5,
        )
        h = (result.stdout or "").strip()
        return h or None
    except Exception:
        return None


def normalize_sampling_params(raw: dict) -> dict:
    """client 별 sampling_params 표현 차이를 표준 dict 로 정규화.

    표준 키: temperature, top_p, max_tokens, seed.
    raw 의 다른 키는 보존하되 표준 키 우선.
    """
    standard = ("temperature", "top_p", "max_tokens", "seed")
    out: dict = {k: raw.get(k) for k in standard if k in raw}
    for k, v in raw.items():
        if k not in standard:
            out[k] = v
    return out


def parse_result_meta(result_data: dict) -> dict:
    """결과 JSON dict 의 top-level meta 를 표준 dict 로 정규화.

    schema_version="1.0" 이면 그대로 반환 (build_result_meta 출력 호환).
    schema_version 부재 (v0) 면 도구별 ad-hoc 키에서 가능한 만큼 추출하고
    부재 필드는 None.

    Returns:
        {schema_version, experiment, model{name,engine,endpoint},
         sampling_params, scorer_version, taskset_version, started_at, ended_at}
    """
    schema = result_data.get("schema_version")
    if schema == "1.0":
        return {
            "schema_version": "1.0",
            "experiment": result_data.get("experiment"),
            "model": result_data.get("model") or {"name": None, "engine": None, "endpoint": None},
            "sampling_params": result_data.get("sampling_params") or {},
            "scorer_version": result_data.get("scorer_version"),
            "taskset_version": result_data.get("taskset_version"),
            "started_at": result_data.get("started_at"),
            "ended_at": result_data.get("ended_at"),
        }

    # v0 (구 결과) — 도구별 ad-hoc 키 보수적 추출
    return {
        "schema_version": "0",
        "experiment": result_data.get("experiment"),
        "model": {
            "name": result_data.get("model"),
            "engine": None,
            "endpoint": None,
        },
        "sampling_params": result_data.get("sampling_params") or {},
        "scorer_version": None,
        "taskset_version": None,
        "started_at": result_data.get("started_at"),
        "ended_at": result_data.get("ended_at"),
    }
