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
    MODEL_NAME, API_CHAT_URL, API_TIMEOUT,
    ASSERTION_SOFT_CAP, ASSERTION_HARD_CAP,
    CONFIDENCE_FLOOR, CONFIDENCE_PROMOTION_MIN, CONFIDENCE_CAP_NO_TOOL,
    MAX_LOOPS, SAMPLING_PARAMS,
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


def call_model(
    messages: list[dict],
    model: str = MODEL_NAME,
    tools: list[dict] | None = None,
    tool_functions: dict | None = None,
    max_tool_rounds: int = 5,
) -> tuple[str, list[dict]]:
    """OpenAI-compatible chat API 호출. tools 제공 시 tool_calls 루프 자동 처리.

    반환: (final_content, tool_call_log)
      - final_content: 최종 assistant 메시지 content (str)
      - tool_call_log: [{"name": str, "arguments": dict, "result": Any, "error": str|None}, ...]

    MAX_LOOPS vs max_tool_rounds: tool loop는 단일 A 호출 내부 루프이고
    MAX_LOOPS(MAX_TOTAL_CYCLES)는 A-B-C 사이클 수준의 별개 개념이다.
    """
    use_tools = bool(tools and tool_functions)
    payload: dict = {
        "model": "",  # LM Studio가 로드된 모델을 자동 선택하도록 빈 값 전송
        "messages": list(messages),  # 복사본 — tool 메시지 append용
    }
    # SAMPLING_PARAMS 의 None 이 아닌 값만 spread
    for _k, _v in SAMPLING_PARAMS.items():
        if _v is not None:
            # LM Studio 로컬 서버는 이 subset 조합이 가장 안정적임
            if _k in ["temperature", "max_tokens", "top_p"]:
                payload[_k] = _v
    if use_tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
        # tools와 json response_format은 LM Studio에서 충돌 가능 — 제거
    # LM Studio는 response_format=json_object 를 400으로 거부할 수 있어 프롬프트만으로 JSON 유도

    tool_call_log: list[dict] = []

    with httpx.Client(timeout=httpx.Timeout(API_TIMEOUT, connect=30.0)) as client:
        for _round in range(max_tool_rounds + 1):
            resp = client.post(API_CHAT_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
            message = data["choices"][0]["message"]
            tool_calls = message.get("tool_calls") or []

            if not tool_calls:
                return message.get("content") or "", tool_call_log

            # tool_calls 처리
            payload["messages"].append({"role": "assistant", "content": message.get("content"), "tool_calls": tool_calls})
            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                try:
                    fn_args = json.loads(tc["function"]["arguments"])
                    result = tool_functions[fn_name](**fn_args)
                    err = None
                except Exception as e:
                    result = None
                    err = str(e)
                tool_call_log.append({"name": fn_name, "arguments": fn_args if err is None else {}, "result": result, "error": err})
                payload["messages"].append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result) if result is not None else json.dumps({"error": err}),
                })

            if _round >= max_tool_rounds:
                raise RuntimeError("tool loop exceeded")

    return "", tool_call_log


def _escape_control_chars_in_json_strings(candidate: str) -> str:
    """Escape raw control chars inside quoted JSON strings.

    Local models often emit Markdown/newlines inside a JSON string value. That is
    invalid JSON, but the surrounding object is otherwise usable.
    """
    out: list[str] = []
    in_string = False
    escaped = False
    for ch in candidate:
        if in_string:
            if escaped:
                out.append(ch)
                escaped = False
            elif ch == "\\":
                out.append(ch)
                escaped = True
            elif ch == '"':
                out.append(ch)
                in_string = False
            elif ch == "\n":
                out.append("\\n")
            elif ch == "\r":
                out.append("\\r")
            elif ch == "\t":
                out.append("\\t")
            else:
                out.append(ch)
        else:
            out.append(ch)
            if ch == '"':
                in_string = True
    return "".join(out)


def _loads_json_lenient(candidate: str) -> dict | None:
    candidate = candidate.strip()
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        try:
            parsed = json.loads(_escape_control_chars_in_json_strings(candidate))
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def _recover_partial_json(candidate: str) -> dict | None:
    """Brace 가 짝 안 맞는 partial JSON 을 복구 시도.

    전략:
    1. 첫 '{' 위치부터 brace count 추적, depth=0 으로 닫힌 마지막 위치까지 잘라 lenient 시도.
    2. 그래도 안 되면 부족한 만큼 '}' 추가 + 미완성 string/콤마 정리 후 재시도.
    """
    if not candidate:
        return None
    start = candidate.find("{")
    if start == -1:
        return None
    body = candidate[start:]
    depth = 0
    in_string = False
    escaped = False
    last_complete_close = -1
    for i, ch in enumerate(body):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    last_complete_close = i
    # 1) depth=0 으로 닫힌 위치까지 자른 본을 lenient parse 시도
    if last_complete_close != -1:
        parsed = _loads_json_lenient(body[: last_complete_close + 1])
        if parsed:
            return parsed
    # 2) depth > 0 이면 부족한 만큼 '}' 채워서 시도
    if depth > 0:
        trimmed = body.rstrip().rstrip(",")
        # 미완성 string (홀수 따옴표) 안전 처리: 마지막 `"` 부터 잘라냄
        if trimmed.count('"') % 2 == 1:
            trimmed = trimmed[: trimmed.rfind('"')].rstrip()
        # 끝이 `:` 또는 `,` 면 마지막 key:value pair 미완성 — 그 직전 `,` 까지 자름
        while trimmed and trimmed[-1] in ":,":
            last_comma = trimmed.rfind(",")
            if last_comma == -1:
                # 객체에 살릴 pair 없음 — 빈 객체로
                return _loads_json_lenient("{}")
            trimmed = trimmed[:last_comma].rstrip()
        candidate2 = trimmed + ("}" * depth)
        return _loads_json_lenient(candidate2)
    return None


def extract_json_from_response(raw: str) -> dict | None:
    """LLM 응답에서 JSON 블록을 추출한다. (JSON Mode 대응)"""
    if not raw:
        return None

    # 1. JSON Mode일 경우 응답 자체가 JSON 문자열일 가능성이 높음
    parsed = _loads_json_lenient(raw)
    if parsed:
        return parsed

    # 2. 마크다운 블록이 포함된 경우 fence 내부 전체를 추출
    for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, re.IGNORECASE):
        parsed = _loads_json_lenient(match.group(1))
        if parsed:
            return parsed

    # 3. 텍스트 중간에 JSON이 섞인 경우
    start = raw.find('{')
    end = raw.rfind('}')
    if start != -1 and end != -1 and end > start:
        parsed = _loads_json_lenient(raw[start:end + 1])
        if parsed:
            return parsed

    # --- v3 patch (exp10-v3-scorer-false-positive-abc-json-parse, 2026-04-29) ---
    # 4. 시작 fence 만 있고 닫는 fence 없는 경우: 시작 fence 다음부터 raw 끝까지 lenient
    fence_open = re.search(r"```(?:json)?\s*\n", raw, re.IGNORECASE)
    if fence_open and "```" not in raw[fence_open.end():]:
        partial = raw[fence_open.end():]
        parsed = _loads_json_lenient(partial)
        if parsed:
            return parsed
        # 5. partial JSON 복구 시도
        parsed = _recover_partial_json(partial)
        if parsed:
            return parsed

    # 6. 마지막 fallback — 전체 raw 를 partial JSON 복구
    parsed = _recover_partial_json(raw)
    if parsed:
        return parsed

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


def apply_llm_response(tattoo: Tattoo, response: dict, loop_index: int, hard_cap: int | None = None) -> tuple[Tattoo, str | None]:
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
        _cap = hard_cap if hard_cap is not None else ASSERTION_HARD_CAP
        if len(new_tattoo.active_assertions) >= _cap:
            continue
        assertion = new_tattoo.add_assertion(
            content=new_a.get("content", ""),
            confidence=conf,
            source_loop=loop_index,
        )
        # Long-context chunked mode: evidence_ref 첨부 (기존 실험에선 None)
        if new_a.get("evidence_ref") is not None:
            assertion.evidence_ref = new_a["evidence_ref"]

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


def run_loop(
    tattoo: Tattoo,
    loop_index: int,
    phase_prompt_args: tuple[int, int] | None = None,
    use_tools: bool = False,
    tool_functions: dict | None = None,
) -> tuple[Tattoo, LoopLog, str | None, list[dict]]:
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
    if phase_prompt_args is not None:
        from system_prompt import build_prompt_with_phase
        messages = build_prompt_with_phase(tattoo_json, cycle=phase_prompt_args[0], max_cycles=phase_prompt_args[1])
    else:
        messages = build_prompt(tattoo_json)

    start = time.time()
    error = None
    parsed = None
    final_answer = None
    raw = ""

    tool_call_log: list[dict] = []
    if use_tools:
        from tools import TOOL_SCHEMAS
        _tools = TOOL_SCHEMAS
        _tool_fns = tool_functions or {}
    else:
        _tools = None
        _tool_fns = None

    for attempt in range(2):
        try:
            raw, tool_call_log = call_model(messages, tools=_tools, tool_functions=_tool_fns)
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

    return new_tattoo, log, final_answer, tool_call_log


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
    tool_calls: list[dict] = None  # A가 사용한 tool call 로그 (use_tools=True 시)

    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []


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
    max_cycles: int = MAX_TOTAL_CYCLES,
    use_phase_prompt: bool = False,
    use_tools: bool = False,
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

    for cycle in range(1, max_cycles + 1):
        phase_str = tattoo.phase.value
        a_tool_calls: list[dict] = []

        # ── A: 제안자 ──
        tattoo.next_directive = PHASE_DIRECTIVES.get(tattoo.phase, "Continue reasoning.")
        if logger:
            logger.cycle_start(cycle, phase_str, len(tattoo.active_assertions), tattoo.confidence)
        else:
            print(f"  Cycle {cycle} | phase={phase_str} | "
                  f"assertions={len(tattoo.active_assertions)} | "
                  f"confidence={tattoo.confidence:.2f}")

        phase_args = (cycle, max_cycles) if use_phase_prompt else None
        _tool_fns = None
        if use_tools:
            from tools import TOOL_FUNCTIONS
            _tool_fns = TOOL_FUNCTIONS
        tattoo, a_log, answer, a_tool_calls = run_loop(
            tattoo, cycle, phase_prompt_args=phase_args,
            use_tools=use_tools, tool_functions=_tool_fns,
        )

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
            if use_phase_prompt:
                from system_prompt import build_critic_prompt_with_phase
                b_messages = build_critic_prompt_with_phase(
                    prompt,
                    assertions_for_b,
                    handoff_a2b=tattoo.handoff_a2b.to_dict() if tattoo.handoff_a2b else None,
                    cycle=cycle,
                    max_cycles=max_cycles,
                )
            else:
                b_messages = build_critic_prompt(
                    prompt,
                    assertions_for_b,
                    handoff_a2b=tattoo.handoff_a2b.to_dict() if tattoo.handoff_a2b else None,
                )
            for attempt in range(2):
                try:
                    b_raw, _ = call_model(b_messages)
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

        if use_phase_prompt:
            from system_prompt import build_judge_prompt_with_phase
            c_messages = build_judge_prompt_with_phase(
                problem=prompt,
                current_phase=phase_str,
                current_critique=current_critique,
                previous_critique=previous_critique,
                assertion_count=len(tattoo.active_assertions),
                handoff_b2c=tattoo.handoff_b2c.to_dict() if tattoo.handoff_b2c else None,
                cycle=cycle,
                max_cycles=max_cycles,
            )
        else:
            c_messages = build_judge_prompt(
                problem=prompt,
                current_phase=phase_str,
                current_critique=current_critique,
                previous_critique=previous_critique,
                assertion_count=len(tattoo.active_assertions),
            )

        for attempt in range(2):
            try:
                c_raw, _ = call_model(c_messages)
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
                            tool_calls=a_tool_calls,
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
            tool_calls=a_tool_calls,
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

    print(f"  ⚠ Max cycles ({max_cycles}) reached without convergence")
    return tattoo, logs, final_answer


def log_detail(msg: str):
    """상세 로그를 experiments/run.log에 기록한다."""
    with open("run.log", "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
        f.flush()


def run_abc_chunked(
    task_id: str,
    question: str,
    chunks: list[dict],  # chunker.Chunk.to_dict() 리스트
    constraints: list[str] | None = None,
    termination: str = "모든 증거가 종합되고 최종 답변이 확정되면 종료",
    logger=None,
    max_final_cycles: int = 5,
    assertion_soft_cap: int = 64,  # chunk iteration 단계에서는 크게 허용
) -> tuple[Tattoo, list[ABCCycleLog], str | None]:
    """Long-context ABC: chunk별로 A 호출하며 증거 누적, 최종 B+C 수렴.

    반환: (tattoo, cycle_logs, final_answer) — run_abc_chain과 동일 인터페이스.
    """
    from system_prompt import build_prompt_chunked, build_critic_prompt, build_judge_prompt

    tattoo = create_initial_tattoo(
        task_id=task_id,
        objective=question,
        constraints=constraints,
        termination=termination,
    )

    logs: list[ABCCycleLog] = []
    final_answer = None
    
    log_detail(f"=== [Long-Context ABC] Task: {task_id} ===")
    log_detail(f"Objective: {question}")
    log_detail(f"Total Chunks: {len(chunks)}")

    # Phase 1: chunk iteration — A per chunk, evidence 누적
    tattoo.phase = Phase.INVESTIGATE
    total = len(chunks)
    for chunk in chunks:
        chunk_id = chunk["chunk_id"]
        tattoo.next_directive = (
            f"Read CURRENT CHUNK (id={chunk_id}/{total - 1}) and extract NEW assertions "
            f"that help answer the question. Attach evidence_ref={{\"chunk_id\": {chunk_id}}} "
            f"to each new assertion. If the chunk has no relevant evidence, return new_assertions: []."
        )

        # select only up to assertion_soft_cap assertions for the prompt (토큰 절약)
        selected = select_assertions(tattoo, soft_cap=assertion_soft_cap)
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
        )
        tattoo_json = display_tattoo.to_json()

        messages = build_prompt_chunked(
            tattoo_json=tattoo_json,
            current_chunk=chunk["content"],
            chunk_id=chunk_id,
        )

        start = time.time()
        raw = ""
        parsed = None
        error = None
        for attempt in range(2):
            try:
                raw, _ = call_model(messages)
                parsed = extract_json_from_response(raw)
            except Exception as e:
                raw = ""
                error = str(e)
            if parsed:
                error = None
                break
            if attempt == 0:
                print(f"    chunk {chunk_id} ↻ retry")
        duration_ms = int((time.time() - start) * 1000)

        if parsed:
            log_detail(f"\n[Chunk {chunk_id}] Agent A Reasoning:\n{parsed.get('reasoning')}")
            tattoo, answer = apply_llm_response(tattoo, parsed, loop_index=chunk_id, hard_cap=ASSERTION_HARD_CAP * 20)
            if answer:
                final_answer = answer
            new_count = len(parsed.get("new_assertions", []))
            log_detail(f"[Chunk {chunk_id}] New Assertions: {new_count} (Total Active: {len(tattoo.active_assertions)})")
        else:
            new_count = 0
            if not error:
                error = "JSON parse failed"
            log_detail(f"[Chunk {chunk_id}] ⚠ Failed to parse: {error}")

        if logger:
            pass  # logger 확장은 향후 추가
        else:
            print(f"  Chunk {chunk_id}/{total - 1} | assertions={len(tattoo.active_assertions)} "
                  f"new={new_count} | {duration_ms}ms{' ⚠ ' + error if error else ''}")

        # 간이 log — LoopLog 재사용
        chunk_loop_log = LoopLog(
            loop_index=chunk_id,
            tattoo_in={},
            raw_response=raw,
            parsed_response=parsed,
            tattoo_out={},
            duration_ms=duration_ms,
            error=error,
        )
        logs.append(ABCCycleLog(
            cycle=chunk_id,
            phase="CHUNK_ITERATE",
            a_log=chunk_loop_log,
            b_judgments=None, b_raw="", b_duration_ms=0, b_error=None,
            c_decision=None, c_raw="", c_duration_ms=0, c_error=None,
            phase_transition=None,
        ))

    # Phase 2: 최종 종합 — B→C 루프 (max_final_cycles)
    tattoo.phase = Phase.SYNTHESIZE
    previous_critique = None
    log_detail("\n--- Phase 2: Final Synthesis (B+C) ---")

    for cycle in range(1, max_final_cycles + 1):
        print(f"  Final cycle {cycle}/{max_final_cycles} | assertions={len(tattoo.active_assertions)}")

        # B (Critic)
        b_start = time.time()
        b_raw = ""
        b_parsed = None
        b_error = None
        assertions_for_b = [a.to_dict() for a in tattoo.active_assertions]
        if assertions_for_b:
            b_messages = build_critic_prompt(
                question,
                assertions_for_b,
                handoff_a2b=tattoo.handoff_a2b.to_dict() if tattoo.handoff_a2b else None,
            )
            for attempt in range(2):
                try:
                    b_raw, _ = call_model(b_messages)
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

        if b_parsed and b_parsed.get("handoff_b2c"):
            tattoo.handoff_b2c = HandoffB2C.from_dict(b_parsed["handoff_b2c"])
        if b_parsed and "judgments" in b_parsed:
            log_detail(f"[Final Cycle {cycle}] Agent B Judgments: {len(b_parsed['judgments'])} assertions.")
            for j in b_parsed["judgments"]:
                if j.get("status") == "invalid":
                    tattoo.invalidate_assertion(j.get("assertion_id", ""), j.get("reason", "Critic invalidated"))
                    log_detail(f"  - Invalidated {j.get('assertion_id')}: {j.get('reason')}")
        current_critique = b_parsed

        print(f"    B: {'⚠ ' + b_error if b_error else str(len(b_parsed.get('judgments', []))) + ' judged'} | {b_duration}ms")

        # C (Judge)
        c_start = time.time()
        c_raw = ""
        c_parsed = None
        c_error = None
        c_messages = build_judge_prompt(
            problem=question,
            current_phase=tattoo.phase.value,
            current_critique=current_critique,
            previous_critique=previous_critique,
            assertion_count=len(tattoo.active_assertions),
        )
        for attempt in range(2):
            try:
                c_raw, _ = call_model(c_messages)
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

        if c_parsed:
            log_detail(f"[Final Cycle {cycle}] Agent C Reasoning:\n{c_parsed.get('reasoning')}")
            if c_parsed.get("final_answer"):
                final_answer = c_parsed["final_answer"]
                log_detail(f"[Final Cycle {cycle}] Agent C Answer: {final_answer[:200]}...")
            if c_parsed.get("converged"):
                tattoo.phase = Phase.CONVERGED
                print(f"    C: CONVERGED | {c_duration}ms")
                log_detail(f"=== [Long-Context ABC] CONVERGED at Cycle {cycle} ===")
                logs.append(ABCCycleLog(
                    cycle=total + cycle,
                    phase="SYNTHESIZE",
                    a_log=chunk_loop_log,
                    b_judgments=b_parsed, b_raw=b_raw[:500],
                    b_duration_ms=b_duration, b_error=b_error,
                    c_decision=c_parsed, c_raw=c_raw[:500],
                    c_duration_ms=c_duration, c_error=c_error,
                    phase_transition="SYNTHESIZE→CONVERGED",
                ))
                return tattoo, logs, final_answer
            else:
                print(f"    C: not converged | {c_duration}ms")
                log_detail(f"[Final Cycle {cycle}] C decision: NOT CONVERGED. Directive: {c_parsed.get('next_directive')}")
        else:
            print(f"    C: {'⚠ ' + c_error if c_error else 'no output'} | {c_duration}ms")

        previous_critique = current_critique
        logs.append(ABCCycleLog(
            cycle=total + cycle,
            phase="SYNTHESIZE",
            a_log=chunk_loop_log,
            b_judgments=b_parsed, b_raw=b_raw[:500],
            b_duration_ms=b_duration, b_error=b_error,
            c_decision=c_parsed, c_raw=c_raw[:500],
            c_duration_ms=c_duration, c_error=c_error,
            phase_transition=None,
        ))

    print(f"  ⚠ Max final cycles ({max_final_cycles}) reached without convergence")
    log_detail("=== [Long-Context ABC] MAX CYCLES REACHED ===")
    return tattoo, logs, final_answer
