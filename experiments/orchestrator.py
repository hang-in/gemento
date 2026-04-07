"""제멘토 오케스트레이터.

루프 실행 엔진: 문신을 LLM에 전달하고, 응답을 파싱하여 새 문신을 생성한다.
컨텍스트는 매 루프마다 완전히 초기화된다.
"""

from __future__ import annotations

import copy
import json
import re
import time
from dataclasses import dataclass

import httpx

from schema import (
    Tattoo, Phase, AssertionStatus,
    VALID_TRANSITIONS, EMERGENCY_VERIFY_ALLOWED_FROM,
    create_initial_tattoo,
)
from system_prompt import build_prompt
from config import (
    MODEL_NAME, OLLAMA_GENERATE_URL, OLLAMA_TIMEOUT,
    ASSERTION_SOFT_CAP, ASSERTION_HARD_CAP,
    CONFIDENCE_FLOOR, CONFIDENCE_PROMOTION_MIN, CONFIDENCE_CAP_NO_TOOL,
    MAX_LOOPS,
)


def call_ollama(messages: list[dict], model: str = MODEL_NAME) -> str:
    """Ollama chat API를 호출하고 응답 텍스트를 반환한다."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 4096,
        },
    }
    with httpx.Client(timeout=OLLAMA_TIMEOUT) as client:
        resp = client.post(OLLAMA_GENERATE_URL, json=payload)
        resp.raise_for_status()
        return resp.json()["message"]["content"]


def extract_json_from_response(raw: str) -> dict | None:
    """LLM 응답에서 JSON 블록을 추출한다."""
    # ```json ... ``` 블록 탐색
    match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # 전체를 JSON으로 파싱 시도
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # { } 블록 탐색
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def select_assertions(tattoo: Tattoo, soft_cap: int = ASSERTION_SOFT_CAP) -> list:
    """규칙 기반 assertion 선택. LLM에게 맡기지 않는다.

    선택 전략 (RT 결론 반영):
    1. active assertion만 대상
    2. confidence 내림차순 정렬
    3. soft cap까지 선택
    """
    active = tattoo.active_assertions
    if len(active) <= soft_cap:
        return active
    # confidence 내림차순, 동률이면 최신(source_loop 높은 것) 우선
    sorted_assertions = sorted(
        active,
        key=lambda a: (a.confidence, a.source_loop),
        reverse=True,
    )
    return sorted_assertions[:soft_cap]


def apply_llm_response(tattoo: Tattoo, response: dict, loop_index: int) -> Tattoo:
    """LLM 응답을 기반으로 새 문신을 생성한다.

    불변 규칙:
    - goal은 변경하지 않는다
    - assertion은 추가/무효화만 가능
    - phase 전이는 규칙을 따른다
    """
    new_tattoo = Tattoo(
        task_id=tattoo.task_id,
        loop_index=loop_index,
        parent_id=tattoo.tattoo_id,
        objective=tattoo.objective,  # 불변
        constraints=list(tattoo.constraints),  # 불변
        termination=tattoo.termination,  # 불변
        phase=tattoo.phase,
        assertions=copy.deepcopy(tattoo.assertions),
        open_questions=list(tattoo.open_questions),
        next_directive="",
    )

    # 1. Assertion 무효화
    for inv in response.get("invalidated_assertions", []):
        new_tattoo.invalidate_assertion(inv["id"], inv.get("reason", "LLM invalidated"))

    # 2. 새 Assertion 추가 (승격 기준 적용)
    for new_a in response.get("new_assertions", []):
        conf = min(new_a.get("confidence", 0.5), CONFIDENCE_CAP_NO_TOOL)
        if conf < CONFIDENCE_PROMOTION_MIN:
            # 승격 기준 미달 → open_questions로 격리
            q = f"[low confidence] {new_a.get('content', '')}"
            new_tattoo.open_questions.append(q)
            continue
        # hard cap 체크
        if len(new_tattoo.active_assertions) >= ASSERTION_HARD_CAP:
            continue
        new_tattoo.add_assertion(
            content=new_a.get("content", ""),
            confidence=conf,
            source_loop=loop_index,
        )

    # 3. 질문 해결/추가
    resolved = set(response.get("resolved_questions", []))
    new_tattoo.open_questions = [
        q for q in new_tattoo.open_questions if q not in resolved
    ]
    for nq in response.get("new_questions", []):
        if nq not in new_tattoo.open_questions:
            new_tattoo.open_questions.append(nq)

    # 4. Phase 전이
    requested_phase = response.get("phase_transition")
    if requested_phase:
        target = Phase(requested_phase)
        if new_tattoo.can_transition_to(target):
            new_tattoo.phase = target

    # 5. 긴급 VERIFY 체크
    overall_conf = response.get("overall_confidence", 1.0)
    new_tattoo.confidence = overall_conf
    if overall_conf < CONFIDENCE_FLOOR and new_tattoo.phase in EMERGENCY_VERIFY_ALLOWED_FROM:
        new_tattoo.phase = Phase.VERIFY

    # 6. next_directive
    new_tattoo.next_directive = response.get("next_directive", "")

    # 7. 무결성 확정
    new_tattoo.finalize_integrity(parent_chain_hash=tattoo.chain_hash)

    return new_tattoo


@dataclass
class LoopLog:
    """한 루프의 실행 로그."""
    loop_index: int
    tattoo_in: dict
    raw_response: str
    parsed_response: dict | None
    tattoo_out: dict
    duration_ms: int
    error: str | None = None


def run_loop(tattoo: Tattoo, loop_index: int) -> tuple[Tattoo, LoopLog]:
    """단일 루프를 실행한다.

    1. 문신 선택 (assertion 필터링)
    2. 프롬프트 생성
    3. LLM 호출
    4. 응답 파싱
    5. 새 문신 생성
    """
    # 문신 선택: 표시용 문신에서 assertion을 필터링
    selected = select_assertions(tattoo)
    display_tattoo = Tattoo(
        tattoo_id=tattoo.tattoo_id,
        task_id=tattoo.task_id,
        loop_index=tattoo.loop_index,
        parent_id=tattoo.parent_id,
        created_at=tattoo.created_at,
        objective=tattoo.objective,
        constraints=tattoo.constraints,
        termination=tattoo.termination,
        phase=tattoo.phase,
        assertions=selected,
        open_questions=tattoo.open_questions,
        next_directive=tattoo.next_directive,
        assertion_hash=tattoo.assertion_hash,
        chain_hash=tattoo.chain_hash,
        confidence=tattoo.confidence,
    )
    tattoo_json = display_tattoo.to_json()
    messages = build_prompt(tattoo_json)

    start = time.time()
    error = None
    parsed = None

    try:
        raw = call_ollama(messages)
        parsed = extract_json_from_response(raw)
    except Exception as e:
        raw = ""
        error = str(e)

    duration_ms = int((time.time() - start) * 1000)

    if parsed:
        new_tattoo = apply_llm_response(tattoo, parsed, loop_index)
    else:
        # 파싱 실패: 문신 변경 없이 다음 루프에서 재시도
        new_tattoo = copy.deepcopy(tattoo)
        new_tattoo.loop_index = loop_index
        new_tattoo.parent_id = tattoo.tattoo_id
        new_tattoo.next_directive = "이전 루프의 응답 파싱에 실패했다. next_directive를 다시 수행하라."
        new_tattoo.finalize_integrity(parent_chain_hash=tattoo.chain_hash)
        if not error:
            error = "JSON parse failed"

    log = LoopLog(
        loop_index=loop_index,
        tattoo_in=tattoo.to_dict(),
        raw_response=raw,
        parsed_response=parsed,
        tattoo_out=new_tattoo.to_dict(),
        duration_ms=duration_ms,
        error=error,
    )

    return new_tattoo, log


def run_chain(
    task_id: str,
    objective: str,
    constraints: list[str] | None = None,
    termination: str = "모든 open_questions가 해결되고 confidence >= 0.8이면 수렴",
    max_loops: int = MAX_LOOPS,
) -> tuple[Tattoo, list[LoopLog]]:
    """전체 루프 체인을 실행한다."""
    tattoo = create_initial_tattoo(
        task_id=task_id,
        objective=objective,
        constraints=constraints,
        termination=termination,
    )

    logs: list[LoopLog] = []

    for i in range(1, max_loops + 1):
        print(f"  Loop {i} | phase={tattoo.phase.value} | "
              f"assertions={len(tattoo.active_assertions)} | "
              f"confidence={tattoo.confidence:.2f}")

        tattoo, log = run_loop(tattoo, i)
        logs.append(log)

        if log.error:
            print(f"    ⚠ Error: {log.error}")

        # 수렴 체크
        if tattoo.phase == Phase.CONVERGED:
            print(f"  ✓ Converged at loop {i}")
            break

    return tattoo, logs
