"""제멘토 오케스트레이터.

루프 실행 엔진: 문신을 LLM에 전달하고, 응답을 파싱하여 새 문신을 생성한다.
컨텍스트는 매 루프마다 완전히 초기화된다.

v2: Phase 전이를 오케스트레이터가 관리한다. 모델에게 메타 판단을 맡기지 않는다.
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
    HandoffA2B, HandoffB2C, RejectMemo
)
from system_prompt import build_prompt
from config import (
    MODEL_NAME, OLLAMA_GENERATE_URL, OLLAMA_TIMEOUT,
    ASSERTION_SOFT_CAP, ASSERTION_HARD_CAP,
    CONFIDENCE_FLOOR, CONFIDENCE_PROMOTION_MIN, CONFIDENCE_CAP_NO_TOOL,
    MAX_LOOPS,
)

# ── Phase별 next_directive 템플릿 ──
PHASE_DIRECTIVES = {
    Phase.DECOMPOSE: "Break the problem into sub-questions. List what needs to be figured out.",
    Phase.INVESTIGATE: "Answer the open questions. Add new facts as assertions.",
    Phase.SYNTHESIZE: "Combine all confirmed facts into a final answer. You MUST set final_answer with your complete answer.",
    Phase.VERIFY: "Check all assertions for correctness. Invalidate any that are wrong. You MUST set final_answer with your complete answer — this is your last chance.",
}

# ── Phase 전이 규칙 (오케스트레이터가 관리) ──
PHASE_MAX_LOOPS = {
    Phase.DECOMPOSE: 2,
    Phase.INVESTIGATE: 4,
    Phase.SYNTHESIZE: 2,
    Phase.VERIFY: 2,
}


def call_ollama(messages: list[dict], model: str = MODEL_NAME) -> str:
    """Ollama chat API를 호출하고 응답 텍스트를 반환한다."""
    payload = {
        "model": model,
        "messages": messages,
        "format": "json",       # 엔진 수준에서 JSON 출력 강제 (가장 중요)
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 4096,
            "num_ctx": 4096,
            "num_gpu": 35,
            "f16_kv": True,
            "num_thread": 8,
        },
    }
    with httpx.Client(timeout=httpx.Timeout(OLLAMA_TIMEOUT, connect=30.0)) as client:
        resp = client.post(OLLAMA_GENERATE_URL, json=payload)
        resp.raise_for_status()
        return resp.json()["message"]["content"]


def extract_json_from_response(raw: str) -> dict | None:
    """LLM 응답에서 JSON 블록을 추출한다. (JSON Mode 대응)"""
    if not raw:
        return None
    
    # 1. JSON Mode일 경우 응답 자체가 JSON 문자열일 가능성이 높음
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
        
    # 2. 마크다운 블록이 포함된 경우 추출
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 3. 텍스트 중간에 JSON이 섞인 경우 (최후의 수단)
    try:
        start = raw.find('{')
        end = raw.rfind('}')
        if start != -1 and end != -1:
            return json.loads(raw[start:end+1])
    except Exception:
        pass

    return None


def select_assertions(tattoo: Tattoo, soft_cap: int = ASSERTION_SOFT_CAP) -> list:
    """규칙 기반 assertion 선택."""
    active = tattoo.active_assertions
    if len(active) <= soft_cap:
        return active
    sorted_assertions = sorted(
        active,
        key=lambda a: (a.confidence, a.source_loop),
        reverse=True,
    )
    return sorted_assertions[:soft_cap]


def decide_phase_transition(tattoo: Tattoo, loops_in_current_phase: int) -> Phase | None:
    """오케스트레이터가 phase 전이를 결정한다.

    조건 기반 전이 + 강제 전이 (max loops 초과 시).
    """
    phase = tattoo.phase
    max_in_phase = PHASE_MAX_LOOPS.get(phase, 2)

    if phase == Phase.DECOMPOSE:
        if tattoo.open_questions:
            return Phase.INVESTIGATE
        if loops_in_current_phase >= max_in_phase:
            return Phase.INVESTIGATE

    elif phase == Phase.INVESTIGATE:
        if not tattoo.open_questions and tattoo.active_assertions:
            return Phase.SYNTHESIZE
        if loops_in_current_phase >= max_in_phase:
            return Phase.SYNTHESIZE

    elif phase == Phase.SYNTHESIZE:
        if loops_in_current_phase >= max_in_phase:
            return Phase.VERIFY

    elif phase == Phase.VERIFY:
        if loops_in_current_phase >= max_in_phase:
            return Phase.CONVERGED

    return None


def apply_llm_response(tattoo: Tattoo, response: dict, loop_index: int) -> tuple[Tattoo, str | None]:
    """LLM 응답을 기반으로 새 문신을 생성한다."""
    new_tattoo = Tattoo(
        task_id=tattoo.task_id,
        loop_index=loop_index,
        parent_id=tattoo.tattoo_id,
        objective=tattoo.objective,
        constraints=list(tattoo.constraints),
        termination=tattoo.termination,
        phase=tattoo.phase,
        assertions=copy.deepcopy(tattoo.assertions),
        open_questions=list(tattoo.open_questions),
        next_directive="",
        handoff_a2b=tattoo.handoff_a2b,
        handoff_b2c=tattoo.handoff_b2c,
        reject_memo=tattoo.reject_memo,
    )

    # ── HandoffA2B 파싱 (Architect A의 응답) ──
    if response.get("handoff_a2b"):
        new_tattoo.handoff_a2b = HandoffA2B.from_dict(response["handoff_a2b"])

    # 1. Assertion 무효화
    for inv in response.get("invalidated_assertions", []):
        new_tattoo.invalidate_assertion(inv["id"], inv.get("reason", "LLM invalidated"))

    # 2. 새 Assertion 추가 (v2: confidence cap 제거)
    for new_a in response.get("new_assertions", []):
        try:
            conf = float(new_a.get("confidence", 0.5))
        except (TypeError, ValueError):
            conf = 0.5
        conf = max(0.0, min(1.0, conf))
        if conf < CONFIDENCE_PROMOTION_MIN:
            q = f"[low confidence] {new_a.get('content', '')}"
            new_tattoo.open_questions.append(q)
            continue
        if len(new_tattoo.active_assertions) >= ASSERTION_HARD_CAP:
            continue
        new_tattoo.add_assertion(
            content=new_a.get("content", ""),
            confidence=conf,
            source_loop=loop_index,
        )

    # 3. 질문 해결/추가 (방어 로직: 요소가 dict인 경우 대응)
    raw_resolved = response.get("resolved_questions", [])
    resolved_list = []
    for r in raw_resolved:
        if isinstance(r, dict):
            # dict인 경우 가장 그럴듯한 키값을 찾거나 전체를 문자열화
            resolved_list.append(str(r.get("question", r.get("content", str(r)))))
        else:
            resolved_list.append(str(r))
    
    resolved_set = set(resolved_list)
    new_tattoo.open_questions = [
        q for q in new_tattoo.open_questions if str(q) not in resolved_set
    ]
    
    raw_new_q = response.get("new_questions", [])
    for nq in raw_new_q:
        q_str = str(nq.get("question", nq.get("content", str(nq)))) if isinstance(nq, dict) else str(nq)
        if q_str not in new_tattoo.open_questions:
            new_tattoo.open_questions.append(q_str)

    # 4. Confidence
    try:
        overall_conf = float(response.get("overall_confidence", 0.7))
    except (TypeError, ValueError):
        overall_conf = 0.7
    new_tattoo.confidence = max(0.0, min(1.0, overall_conf))

    # 5. final_answer 확인
    final_answer = response.get("final_answer")
    if final_answer and new_tattoo.phase in (Phase.SYNTHESIZE, Phase.VERIFY):
        new_tattoo.phase = Phase.CONVERGED
        new_tattoo.next_directive = str(final_answer)

    # 6. 무결성 확정
    new_tattoo.finalize_integrity(parent_chain_hash=tattoo.chain_hash)

    return new_tattoo, final_answer


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


def run_loop(tattoo: Tattoo, loop_index: int) -> tuple[Tattoo, LoopLog, str | None]:
    """단일 루프를 실행한다."""
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
    final_answer = None
    raw = ""

    for attempt in range(2):
        try:
            raw = call_ollama(messages)
            parsed = extract_json_from_response(raw)
        except Exception as e:
            raw = ""
            error = str(e)
        if parsed:
            error = None
            break
        if attempt == 0:
            print(f"    ↻ JSON parse retry (attempt {attempt + 1})")

    duration_ms = int((time.time() - start) * 1000)

    if parsed:
        new_tattoo, final_answer = apply_llm_response(tattoo, parsed, loop_index)
    else:
        new_tattoo = copy.deepcopy(tattoo)
        new_tattoo.loop_index = loop_index
        new_tattoo.parent_id = tattoo.tattoo_id
        new_tattoo.next_directive = "이전 응답 파싱 실패. 다시 시도하라."
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

    return new_tattoo, log, final_answer


def run_chain(
    task_id: str,
    objective: str,
    constraints: list[str] | None = None,
    termination: str = "모든 open_questions가 해결되고 confidence >= 0.8이면 수렴",
    max_loops: int = MAX_LOOPS,
) -> tuple[Tattoo, list[LoopLog], str | None]:
    """전체 루프 체인을 실행한다.

    v2: 오케스트레이터가 phase 전이를 관리한다.
    """
    tattoo = create_initial_tattoo(
        task_id=task_id,
        objective=objective,
        constraints=constraints,
        termination=termination,
    )

    logs: list[LoopLog] = []
    final_answer = None
    loops_in_current_phase = 0
    current_phase = tattoo.phase

    for i in range(1, max_loops + 1):
        # Phase별 next_directive 자동 설정
        tattoo.next_directive = PHASE_DIRECTIVES.get(tattoo.phase, "Continue reasoning.")

        print(f"  Loop {i} | phase={tattoo.phase.value} | "
              f"assertions={len(tattoo.active_assertions)} | "
              f"questions={len(tattoo.open_questions)} | "
              f"confidence={tattoo.confidence:.2f}")

        tattoo, log, answer = run_loop(tattoo, i)
        logs.append(log)

        if answer:
            final_answer = answer

        if log.error:
            print(f"    ⚠ Error: {log.error}")

        # Phase 추적
        if tattoo.phase == current_phase:
            loops_in_current_phase += 1
        else:
            current_phase = tattoo.phase
            loops_in_current_phase = 1

        # 수렴 체크
        if tattoo.phase == Phase.CONVERGED:
            print(f"  ✓ Converged at loop {i}")
            break

        # 오케스트레이터 강제 phase 전이
        new_phase = decide_phase_transition(tattoo, loops_in_current_phase)
        if new_phase and new_phase != tattoo.phase:
            old = tattoo.phase.value
            tattoo.phase = new_phase
            loops_in_current_phase = 0
            current_phase = new_phase
            print(f"    → Phase: {old} → {new_phase.value} (orchestrator)")

            if new_phase == Phase.CONVERGED:
                print(f"  ✓ Converged at loop {i} (forced)")
                break

    return tattoo, logs, final_answer


# ── A-B-C 직렬 파이프라인 ──

@dataclass
class ABCCycleLog:
    """A-B-C 한 사이클의 로그."""
    cycle: int
    phase: str
    a_log: LoopLog
    b_judgments: dict | None
    b_raw: str
    b_duration_ms: int
    b_error: str | None
    c_decision: dict | None
    c_raw: str
    c_duration_ms: int
    c_error: str | None
    phase_transition: str | None  # "DECOMPOSE→INVESTIGATE" 등


# Phase 전이 유효성 맵 (C가 출력하는 next_phase 검증용)
VALID_NEXT_PHASE = {
    "DECOMPOSE": "INVESTIGATE",
    "INVESTIGATE": "SYNTHESIZE",
    "SYNTHESIZE": "VERIFY",
    "VERIFY": "CONVERGED",
}

MAX_CYCLES_PER_PHASE = 3
MAX_TOTAL_CYCLES = 12


def run_abc_chain(
    task_id: str,
    objective: str,
    prompt: str,
    constraints: list[str] | None = None,
    termination: str = "모든 비판이 수렴하고 최종 답변이 확정되면 종료",
    logger=None,
) -> tuple[Tattoo, list[ABCCycleLog], str | None]:
    """A-B-C 직렬 파이프라인을 실행한다.

    A (제안자) → B (비판자) → C (판정자) 사이클 반복.
    C가 phase 전이를 결정. Python은 안전장치(최대 사이클)만 강제.
    """
    from system_prompt import build_critic_prompt, build_judge_prompt

    tattoo = create_initial_tattoo(
        task_id=task_id,
        objective=f"{objective}\n\nProblem:\n{prompt}",
        constraints=constraints,
        termination=termination,
    )

    logs: list[ABCCycleLog] = []
    final_answer = None
    cycles_in_current_phase = 0
    previous_critique = None

    for cycle in range(1, MAX_TOTAL_CYCLES + 1):
        phase_str = tattoo.phase.value

        # ── A: 제안자 ──
        tattoo.next_directive = PHASE_DIRECTIVES.get(tattoo.phase, "Continue reasoning.")
        if logger:
            logger.cycle_start(cycle, phase_str, len(tattoo.active_assertions), tattoo.confidence)
        else:
            print(f"  Cycle {cycle} | phase={phase_str} | "
                  f"assertions={len(tattoo.active_assertions)} | "
                  f"confidence={tattoo.confidence:.2f}")

        tattoo, a_log, answer = run_loop(tattoo, cycle)

        if answer:
            final_answer = answer

        if logger:
            new_count = len(a_log.parsed_response.get("new_assertions", [])) if a_log.parsed_response else 0
            logger.agent_a(a_log.duration_ms, new_count, bool(answer), a_log.error)
            if a_log.parsed_response:
                logger.agent_a_reasoning(a_log.parsed_response.get("reasoning", ""))
        elif a_log.error:
            print(f"    A ⚠ {a_log.error}")

        # ── B: 비판자 ──
        b_start = time.time()
        b_error = None
        b_parsed = None
        b_raw = ""

        assertions_for_b = [a.to_dict() for a in tattoo.active_assertions]
        if assertions_for_b:
            b_messages = build_critic_prompt(
                prompt, 
                assertions_for_b, 
                handoff_a2b=tattoo.handoff_a2b.to_dict() if tattoo.handoff_a2b else None
            )
            for attempt in range(2):
                try:
                    b_raw = call_ollama(b_messages)
                    b_parsed = extract_json_from_response(b_raw)
                except Exception as e:
                    b_raw = ""
                    b_error = str(e)
                if b_parsed:
                    b_error = None
                    break
                if attempt == 0:
                    print(f"    B ↻ retry")
            if not b_parsed and not b_error:
                b_error = "JSON parse failed"
        else:
            b_error = "no assertions to critique"

        b_duration = int((time.time() - b_start) * 1000)

        # ── HandoffB2C 파싱 ──
        if b_parsed and b_parsed.get("handoff_b2c"):
            tattoo.handoff_b2c = HandoffB2C.from_dict(b_parsed["handoff_b2c"])

        # B의 비판 결과로 assertion 무효화
        if b_parsed and "judgments" in b_parsed:
            # ... (기존 비판 처리 유지)
            for j in b_parsed["judgments"]:
                if j.get("status") == "invalid":
                    aid = j.get("assertion_id", "")
                    reason = j.get("reason", "Critic invalidated")
                    tattoo.invalidate_assertion(aid, reason)

            invalid_count = sum(1 for j in b_parsed["judgments"] if j.get("status") == "invalid")
            suspect_count = sum(1 for j in b_parsed["judgments"] if j.get("status") == "suspect")
            if logger:
                logger.agent_b(b_duration, len(b_parsed["judgments"]), invalid_count, suspect_count, b_error)
                logger.agent_b_details(b_parsed["judgments"])
            else:
                print(f"    B: {len(b_parsed['judgments'])} judged, "
                      f"{invalid_count} invalid, {suspect_count} suspect | {b_duration}ms")
        else:
            if logger:
                logger.agent_b(b_duration, 0, 0, 0, b_error or "no output")
            else:
                print(f"    B: {'⚠ ' + b_error if b_error else 'no output'} | {b_duration}ms")

        # 비판 기록을 문신에 저장
        current_critique = b_parsed
        tattoo.critique_log.append({
            "cycle": cycle,
            "phase": phase_str,
            "judgments": b_parsed.get("judgments") if b_parsed else None,
        })
        # critique_log는 최근 3개만 유지 (토큰 절약)
        if len(tattoo.critique_log) > 3:
            tattoo.critique_log = tattoo.critique_log[-3:]

        # ── C: 판정자 ──
        c_start = time.time()
        c_error = None
        c_parsed = None
        c_raw = ""
        phase_transition = None

        c_messages = build_judge_prompt(
            problem=prompt,
            current_phase=phase_str,
            current_critique=current_critique,
            previous_critique=previous_critique,
            assertion_count=len(tattoo.active_assertions),
        )

        for attempt in range(2):
            try:
                c_raw = call_ollama(c_messages)
                c_parsed = extract_json_from_response(c_raw)
            except Exception as e:
                c_raw = ""
                c_error = str(e)
            if c_parsed:
                c_error = None
                break
            if attempt == 0:
                print(f"    C ↻ retry")
        if not c_parsed and not c_error:
            c_error = "JSON parse failed"

        c_duration = int((time.time() - c_start) * 1000)

        # C의 결정 처리
        if c_parsed:
            converged = c_parsed.get("converged", False)
            next_phase_str = c_parsed.get("next_phase")
            c_directive = c_parsed.get("next_directive", "")

            if converged and next_phase_str:
                # next_phase 유효성 검증
                expected = VALID_NEXT_PHASE.get(phase_str)
                if next_phase_str == expected:
                    old_phase = phase_str
                    tattoo.phase = Phase(next_phase_str)
                    cycles_in_current_phase = 0
                    previous_critique = None  # 새 phase에서 비판 기록 리셋
                    phase_transition = f"{old_phase}→{next_phase_str}"

                    if logger:
                        logger.agent_c(c_duration, True, next_phase_str, c_error)
                        logger.agent_c_reasoning(c_parsed.get("reasoning", ""))
                        logger.phase_transition(old_phase, next_phase_str)
                    else:
                        print(f"    C: CONVERGED → {next_phase_str} | {c_duration}ms")

                    if next_phase_str == "CONVERGED":
                        tattoo.finalize_integrity(parent_chain_hash=tattoo.chain_hash)
                        if logger:
                            logger.cycle_end(cycle)
                        log = ABCCycleLog(
                            cycle=cycle, phase=phase_str,
                            a_log=a_log,
                            b_judgments=b_parsed, b_raw=b_raw[:500],
                            b_duration_ms=b_duration, b_error=b_error,
                            c_decision=c_parsed, c_raw=c_raw[:500],
                            c_duration_ms=c_duration, c_error=c_error,
                            phase_transition=phase_transition,
                        )
                        logs.append(log)
                        if not logger:
                            print(f"  ✓ Converged at cycle {cycle} (C decided)")
                        return tattoo, logs, final_answer
                else:
                    # C가 잘못된 phase를 출력 — 무시
                    if logger:
                        logger.agent_c(c_duration, True, f"{next_phase_str} (invalid, expected {expected})", None)
                    else:
                        print(f"    C: converged but invalid next_phase={next_phase_str} "
                              f"(expected {expected}) — ignored | {c_duration}ms")
            else:
                # 수렴하지 않음 ── C의 directive 및 RejectMemo 반영 ──
                if c_directive:
                    tattoo.next_directive = c_directive
                
                if c_parsed.get("reject_memo"):
                    tattoo.reject_memo = RejectMemo.from_dict(c_parsed["reject_memo"])
                
                if logger:
                    logger.agent_c(c_duration, False, None, c_error)
                    logger.agent_c_reasoning(c_parsed.get("reasoning", ""))
                else:
                    print(f"    C: not converged | {c_duration}ms")
        else:
            if logger:
                logger.agent_c(c_duration, False, None, c_error or "no output")
            else:
                print(f"    C: {'⚠ ' + c_error if c_error else 'no output'} | {c_duration}ms")

        # 이전 비판 저장 (C의 다음 판단용)
        previous_critique = current_critique

        # 무결성 갱신
        tattoo.finalize_integrity(parent_chain_hash=tattoo.chain_hash)

        if logger:
            logger.cycle_end(cycle)

        # 로그 저장
        log = ABCCycleLog(
            cycle=cycle, phase=phase_str,
            a_log=a_log,
            b_judgments=b_parsed, b_raw=b_raw[:500],
            b_duration_ms=b_duration, b_error=b_error,
            c_decision=c_parsed, c_raw=c_raw[:500],
            c_duration_ms=c_duration, c_error=c_error,
            phase_transition=phase_transition,
        )
        logs.append(log)

        cycles_in_current_phase += 1

        # 안전장치: C가 전이를 결정하지 못하면 Python이 강제
        if cycles_in_current_phase >= MAX_CYCLES_PER_PHASE:
            expected = VALID_NEXT_PHASE.get(phase_str)
            if expected:
                old_phase = phase_str
                tattoo.phase = Phase(expected)
                cycles_in_current_phase = 0
                previous_critique = None
                if logger:
                    logger.safety_limit(old_phase, expected)
                else:
                    print(f"    → Phase: {old_phase} → {expected} (safety limit)")

                if expected == "CONVERGED":
                    if not logger:
                        print(f"  ✓ Converged at cycle {cycle} (safety)")
                    return tattoo, logs, final_answer

        # final_answer가 이미 있고 VERIFY를 지나면 수렴
        if final_answer and tattoo.phase == Phase.CONVERGED:
            print(f"  ✓ Converged at cycle {cycle}")
            return tattoo, logs, final_answer

    print(f"  ⚠ Max cycles ({MAX_TOTAL_CYCLES}) reached without convergence")
    return tattoo, logs, final_answer
