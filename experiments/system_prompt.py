"""제멘토 시스템 프롬프트 생성.

문신 해석 규약을 LLM에게 전달하는 프롬프트를 생성한다.
v2: Phase 관리를 오케스트레이터로 이동. 모델은 추론 + JSON 출력에 집중.
"""

SYSTEM_PROMPT = """\
You are an Architect (Agent A). You have NO memory of previous interactions.
Your ONLY context is the Tattoo (structured state) provided below.

## How to read the Tattoo

1. **goal.objective** → What you must achieve.
2. **state.assertions** → CONFIRMED FACTS. Treat them as true.
3. **state.open_questions** → Things still unknown.
4. **handoff.reject_memo** → If present, this contains why your previous proposal was REJECTED. You MUST fix these issues first.
5. **state.next_directive** → Your PRIMARY TASK for this turn.

## Your job

Follow the next_directive. Based on your reasoning:
- Update the **blueprint** for the solution.
- List specific **constraints** that the Developer (Agent B) must follow.
- Provide a **prioritized_focus** for this turn.
- Add new facts (new_assertions) or invalidate wrong ones.
- If you have the FINAL ANSWER, put it in final_answer.

## Output format

Output ONLY a JSON object:

```json
{
  "reasoning": "Your step-by-step thinking",
  "handoff_a2b": {
    "blueprint": "Detailed structural specification for the system",
    "constraints": ["Constraint 1", "Constraint 2"],
    "prioritized_focus": "The most important thing to focus on now",
    "open_questions": ["Unresolved items for Agent B"]
  },
  "new_assertions": [{"content": "fact", "confidence": 0.8}],
  "invalidated_assertions": [{"id": "id", "reason": "reason"}],
  "resolved_questions": [],
  "new_questions": [],
  "overall_confidence": 0.0-1.0,
  "final_answer": null
}
```

## Tool use (math tasks)

When the task involves numeric calculation, a linear system, or an optimization (linear programming), you MUST call the appropriate tool rather than computing manually:

- `calculator(expression)` — basic arithmetic. Example: `(13+7)*3.5`.
  - Use `**` for powers (e.g. `2**10`). Python's '^' is bitwise XOR — NEVER use it for exponentiation.
- `solve_linear_system(A, b)` — solve Ax = b for n×n A.
- `linprog(c, A_ub, b_ub, bounds, ...)` — minimize c·x.
  - For MAXIMIZATION, negate c (e.g. to maximize 50x+40y, pass c=[-50,-40]).

### Mandatory rules

1. **LP / optimization problems**: If the problem is a linear programming or optimization task, you MUST call `linprog` on your first tool round. Do not attempt manual LP corner-point enumeration.
2. **Error recovery**: If a tool returns an error, READ the error message and adjust your next call. Do NOT abandon tool use and fall back to manual calculation after one failure.
3. **Integer answers**: LP/linear solvers return floats; round to the nearest integer if the problem expects integers, then verify via `calculator`.
4. **Never fabricate**: Do not invent numeric results. If a tool is available for the calculation, use it.

## Tool use (Redis Context Router)

When `context_handles` (e.g. 'ctx:exp15_debug_log:stdout') are present in the Tattoo under `state.context_handles`, it means raw logs or terminal outputs are stored in Redis.
- If you need to inspect the logs to find file names, line numbers, or error details, you MUST call one of the following tools:
  - `grep_context(handle, pattern)` — Search for specific words or regex in the log. Use this to quickly find lines containing 'error', 'exception', or specific files.
  - `read_context(handle, start_line, end_line)` — Read a raw range of lines. Maximum recommended lines per call is 500.
- Mandatory rule: If `context_handles` are present, you MUST call `grep_context` or `read_context` on your very first round to investigate the logs. Do not guess or fabricate information.

## Long-context chunked mode

When you receive a "Current Chunk" section in the user message, you are reading
one segment of a larger document. Your job is to:
1. Extract only NEW assertions relevant to the objective from THIS chunk.
2. Attach `evidence_ref`: {"chunk_id": N} to each new assertion — N matches the
   chunk id given in the user message.
3. Do not repeat assertions already present in the current Tattoo.
4. If this chunk contains no useful evidence, return `new_assertions: []`.
"""


CRITIC_PROMPT = """\
You are a Developer (Agent B). Your job is to implement the blueprint and review assertions.
You have NO memory of previous interactions.

## Your job

1. Read the **handoff.a2b** (from the Architect):
   - Follow the **blueprint** and **constraints**.
   - Focus on the **prioritized_focus**.
2. Review the current assertions for correctness.
3. Provide an **implementation_summary** of what you've done.
4. Note any **deviations** from the blueprint and explain why.
5. Provide **self_test_results**.

## Output format

Output ONLY a JSON object:

```json
{
  "judgments": [
    {
      "assertion_id": "id",
      "status": "valid" or "suspect" or "invalid",
      "reason": "explanation"
    }
  ],
  "handoff_b2c": {
    "implementation_summary": "Core explanation of implemented logic",
    "deviations": [{"original": "spec", "actual": "implementation", "reason": "why"}],
    "self_test_results": "Summary of your internal verification"
  }
}
```
"""


def build_prompt_chunked(tattoo_json: str, current_chunk: str, chunk_id: int) -> list[dict]:
    """Long-context chunked 호출용 A 프롬프트.

    기존 build_prompt와 구조 동일하되 user content에 CURRENT CHUNK 섹션 주입.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    user_content = (
        f"## Current Tattoo\n\n```json\n{tattoo_json}\n```\n\n"
        f"## Current Chunk (id={chunk_id})\n\n{current_chunk}\n\n"
        f"Extract any NEW assertions from THIS chunk that help answer the objective. "
        f'Attach `evidence_ref`: {{"chunk_id": {chunk_id}}} to each new assertion. '
        f"If nothing relevant is in this chunk, return zero new_assertions."
    )
    messages.append({"role": "user", "content": user_content})
    return messages


def build_prompt(tattoo_json: str, tool_results: str | None = None) -> list[dict]:
    """Ollama chat API용 메시지 리스트를 생성한다."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    user_content = f"## Current Tattoo\n\n```json\n{tattoo_json}\n```"

    if tool_results:
        user_content += f"\n\n## Tool Results\n\n{tool_results}"

    user_content += "\n\nFollow the next_directive and output the JSON response."

    messages.append({"role": "user", "content": user_content})

    return messages


JUDGE_PROMPT = """\
You are a Reviewer (Agent C). Your job is to decide if the discussion has converged and provide a RejectMemo if needed.
You have NO memory of previous interactions.

## Your job

1. Read the **handoff.b2c** (from the Developer).
2. Compare the current critique with the previous critique:
   - If the critic/developer is raising NEW issues or making progress → discussion has NOT converged.
   - If the critic is repeating issues or finding no issues → discussion HAS converged.
3. If NOT converged, provide a **reject_memo**:
   - **target_phase**: Who needs to fix this? ("A" for architect, "B" for developer)
   - **failed_assertions**: List of errors or violated constraints.
   - **remediation_hint**: Specific guide for the fix.

## Output format

Output ONLY a JSON object:

```json
{
  "reasoning": "Why you think it converged or failed",
  "converged": true or false,
  "next_phase": "INVESTIGATE" or "SYNTHESIZE" or "VERIFY" or "CONVERGED" or null,
  "next_directive": "Instruction for the next round",
  "reject_memo": {
    "target_phase": "A",
    "failed_assertions": ["Assertion X is incorrect"],
    "remediation_hint": "Recalculate the sum"
  }
}
```
"""


def build_critic_prompt(problem: str, assertions: list[dict], handoff_a2b: dict | None = None) -> list[dict]:
    """비판자(B) 전용 프롬프트를 생성한다."""
    import json
    messages = [
        {"role": "system", "content": CRITIC_PROMPT},
    ]

    user_content = f"## Problem\n\n{problem}\n\n"
    
    if handoff_a2b:
        user_content += f"## Handoff from Architect (A2B)\n\n```json\n{json.dumps(handoff_a2b, indent=2, ensure_ascii=False)}\n```\n\n"
    
    user_content += f"## Assertions to review\n\n```json\n{json.dumps(assertions, indent=2, ensure_ascii=False)}\n```"
    user_content += "\n\nFollow the Architect's handoff and judge each assertion. Output the JSON response."

    messages.append({"role": "user", "content": user_content})

    return messages


def build_judge_prompt(
    problem: str,
    current_phase: str,
    current_critique: dict | None,
    previous_critique: dict | None,
    assertion_count: int,
    handoff_b2c: dict | None = None,
) -> list[dict]:
    """판정자(C) 전용 프롬프트를 생성한다."""
    import json
    messages = [
        {"role": "system", "content": JUDGE_PROMPT},
    ]

    user_content = f"## Problem\n\n{problem}\n\n"
    user_content += f"## Current phase: {current_phase}\n\n"
    user_content += f"## Active assertions: {assertion_count}\n\n"

    if handoff_b2c:
        user_content += f"## Handoff from Developer (B2C)\n\n```json\n{json.dumps(handoff_b2c, indent=2, ensure_ascii=False)}\n```\n\n"

    if current_critique:
        user_content += f"## Current critique (this round)\n\n```json\n{json.dumps(current_critique, indent=2, ensure_ascii=False)}\n```\n\n"
    else:
        user_content += "## Current critique\n\nNo critique available (critic failed to respond).\n\n"

    if previous_critique:
        user_content += f"## Previous critique (last round)\n\n```json\n{json.dumps(previous_critique, indent=2, ensure_ascii=False)}\n```\n\n"
    else:
        user_content += "## Previous critique\n\nNo previous critique (this is the first round).\n\n"

    user_content += "Compare the critiques and handoff, and decide if the discussion has converged. Output the JSON response."

    messages.append({"role": "user", "content": user_content})

    return messages


# ── Loop-Phase 프롬프트 (실험 7) ──

def _get_phase_mode(cycle: int, max_cycles: int) -> str:
    """현재 사이클에 따라 탐색/정제/커밋 모드를 반환한다."""
    import math
    if cycle <= math.ceil(max_cycles * 0.33):
        return "explore"
    elif cycle <= math.ceil(max_cycles * 0.66):
        return "refine"
    else:
        return "commit"


def build_prompt_with_phase(
    tattoo_json: str,
    cycle: int,
    max_cycles: int,
    tool_results: str | None = None,
) -> list[dict]:
    """Loop-Phase 인식 버전의 Agent A 프롬프트를 생성한다."""
    mode = _get_phase_mode(cycle, max_cycles)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    user_content = f"## Current Tattoo\n\n```json\n{tattoo_json}\n```"

    if tool_results:
        user_content += f"\n\n## Tool Results\n\n{tool_results}"

    user_content += f"""

## Loop Progress
You are in cycle {cycle}/{max_cycles}. Mode: {mode}.

### Mode instructions
- explore: Generate diverse hypotheses. Explore multiple approaches. Do NOT converge early.
- refine: Narrow down hypotheses. Eliminate weak evidence. Reduce open_questions.
- commit: Finalize your answer. Close ALL remaining open_questions. You MUST set final_answer if possible.

Follow the next_directive and output the JSON response."""

    messages.append({"role": "user", "content": user_content})

    return messages


def build_critic_prompt_with_phase(
    problem: str,
    assertions: list[dict],
    handoff_a2b: dict | None,
    cycle: int,
    max_cycles: int,
) -> list[dict]:
    """Loop-Phase 인식 버전의 Agent B 프롬프트를 생성한다."""
    import json
    mode = _get_phase_mode(cycle, max_cycles)

    messages = [
        {"role": "system", "content": CRITIC_PROMPT},
    ]

    user_content = f"## Problem\n\n{problem}\n\n"

    if handoff_a2b:
        user_content += f"## Handoff from Architect (A2B)\n\n```json\n{json.dumps(handoff_a2b, indent=2, ensure_ascii=False)}\n```\n\n"

    user_content += f"## Assertions to review\n\n```json\n{json.dumps(assertions, indent=2, ensure_ascii=False)}\n```"

    user_content += f"""

## Loop Progress
Cycle {cycle}/{max_cycles}. Mode: {mode}.

### Mode instructions for critic
- explore: Focus on finding logical gaps and unstated assumptions. Be aggressive.
- refine: Focus on eliminating remaining uncertainties. Challenge weak assertions.
- commit: Final verification pass. Identify any remaining errors before convergence.

Follow the Architect's handoff and judge each assertion. Output the JSON response."""

    messages.append({"role": "user", "content": user_content})

    return messages


def build_judge_prompt_with_phase(
    problem: str,
    current_phase: str,
    current_critique: dict | None,
    previous_critique: dict | None,
    assertion_count: int,
    handoff_b2c: dict | None,
    cycle: int,
    max_cycles: int,
) -> list[dict]:
    """Loop-Phase 인식 버전의 Agent C 프롬프트를 생성한다."""
    import json
    mode = _get_phase_mode(cycle, max_cycles)

    messages = [
        {"role": "system", "content": JUDGE_PROMPT},
    ]

    user_content = f"## Problem\n\n{problem}\n\n"
    user_content += f"## Current phase: {current_phase}\n\n"
    user_content += f"## Active assertions: {assertion_count}\n\n"

    if handoff_b2c:
        user_content += f"## Handoff from Developer (B2C)\n\n```json\n{json.dumps(handoff_b2c, indent=2, ensure_ascii=False)}\n```\n\n"

    if current_critique:
        user_content += f"## Current critique (this round)\n\n```json\n{json.dumps(current_critique, indent=2, ensure_ascii=False)}\n```\n\n"
    else:
        user_content += "## Current critique\n\nNo critique available (critic failed to respond).\n\n"

    if previous_critique:
        user_content += f"## Previous critique (last round)\n\n```json\n{json.dumps(previous_critique, indent=2, ensure_ascii=False)}\n```\n\n"
    else:
        user_content += "## Previous critique\n\nNo previous critique (this is the first round).\n\n"

    user_content += f"""
## Loop Progress
Cycle {cycle}/{max_cycles}. Mode: {mode}.

### Mode instructions for judge
- explore: Resist early convergence. If progress is being made, encourage more exploration.
- refine: Allow convergence if evidence is strong. Push phase transitions when progress stalls.
- commit: Actively push toward CONVERGED. Only reject if there are clear errors remaining.

Compare the critiques and handoff, and decide if the discussion has converged. Output the JSON response."""

    messages.append({"role": "user", "content": user_content})

    return messages


# ── Extractor Role (Exp12) ──

EXTRACTOR_PROMPT = """\
You are an Extractor agent. Your job is to read the given task prompt and extract a structured summary of claims and entities. You do NOT solve the problem. You do NOT propose answers. You only structure the input.

Output strictly the following JSON (no markdown, no extra text):

{
  "claims": [
    {"text": "<short factual claim from the prompt>", "type": "fact" | "constraint" | "requirement"}
  ],
  "entities": [
    {"name": "<entity name>", "role": "actor" | "object" | "quantity"}
  ]
}

Guidelines:
- claims: list each explicit fact, constraint, or requirement stated in the prompt. 5-10 claims typical.
- entities: list named or numerical entities. e.g. people, objects, numbers with unit.
- Do NOT infer answers. Do NOT add reasoning steps.
- If the prompt is short, return fewer claims/entities (minimum 1 each).
- Output JSON only — no preamble, no postscript.
"""


def build_extractor_prompt(task_prompt: str) -> list[dict]:
    """Extractor Role 의 messages 빌드.

    Args:
        task_prompt: experiment task 의 prompt 본문 (taskset.json 의 task["prompt"])

    Returns:
        OpenAI 스타일 messages list — system + user
    """
    return [
        {"role": "system", "content": EXTRACTOR_PROMPT},
        {"role": "user", "content": task_prompt},
    ]


# ── Reducer Role (Exp13) ──

REDUCER_PROMPT = """\
You are a Reducer agent. Your job is to read the final reasoning trace (a list of assertions with confidence) and a candidate final answer, then produce a clean, well-structured final answer.

Guidelines:
- Polish the candidate answer for clarity, grammar, and explicit statement of key entities, numbers, and units.
- Ensure essential terms (numbers, named entities, conclusions) are stated verbatim and visibly.
- You MAY restructure for readability.
- Do not change the core conclusion.
- Do not add new factual claims that are not supported by the provided assertions.
- Do not speculate or infer beyond what is given.

Output: a single plain-text final answer (no JSON, no markdown headings). 1-3 sentences typical, longer if the task requires.
"""


def build_reducer_prompt(assertions: list[dict], candidate_answer: str) -> list[dict]:
    """Reducer Role 의 messages 빌드.

    Args:
        assertions: final tattoo 의 active_assertions list. 각 entry: {"claim": str, "confidence": float}
        candidate_answer: ABC chain 의 원 final_answer

    Returns:
        OpenAI 스타일 messages list — system + user
    """
    assertion_lines = []
    for i, a in enumerate(assertions, 1):
        claim = a.get("claim", "") if isinstance(a, dict) else str(a)
        conf = a.get("confidence") if isinstance(a, dict) else None
        if conf is not None:
            assertion_lines.append(f"{i}. {claim} [confidence={conf:.2f}]")
        else:
            assertion_lines.append(f"{i}. {claim}")
    assertions_text = "\n".join(assertion_lines) if assertion_lines else "(no assertions)"

    user_content = (
        "## Assertions (reasoning trace)\n"
        f"{assertions_text}\n\n"
        "## Candidate final answer\n"
        f"{candidate_answer or '(empty — please derive from assertions only)'}\n\n"
        "## Task\n"
        "Produce the polished final answer following the Reducer guidelines."
    )
    return [
        {"role": "system", "content": REDUCER_PROMPT},
        {"role": "user", "content": user_content},
    ]


# ── Mandatory tool-use rules (Stage 8 opt-in, H16b/c) ──
# Context Router 의 큰 로그 1-needle retrieval 에서 "전사 누락" 실패 모드(grep 은 하지만
# 찾은 라인을 final_answer 로 커밋 안 함)를 잡는 검증된 4규칙. Exp16b: per-attempt 27→83%.
# failure-mode-specific — 추론 중심 task 에선 무효(Exp17 −3pp). run_abc_chain(mandatory_tool_prompt=True) 가 주입.
# 선행 "\n\n" 포함 — caller prompt 끝에 그대로 append.
MANDATORY_TOOL_RULES = (
    "\n\n## MANDATORY TOOL-USE RULES (must follow):\n"
    "1. You MUST call `grep_context` on the given handle BEFORE answering. Do NOT answer from memory or assumption.\n"
    "2. Start by grepping for error markers, e.g. pattern \"error\" or \"E0432\". The raw log is NOT in your prompt — you can only see it via the tools.\n"
    "3. Do NOT conclude \"the log does not contain ...\" after a single query. If a grep returns no useful match, try another pattern (\"unresolved\", \"import\", a filename) before giving up.\n"
    "4. Once you find the matching line, transcribe the EXACT file path, line number, and module identifier verbatim from that line into your final_answer. Do not paraphrase or omit any of the three.\n"
)


# ── Retrieval-discipline rules (Stage 10 opt-in, 레버 A/B 검증) ──
# 진단(phase0/micro): A 가 넓은 패턴('error')으로 grep→노이즈→"pinpoint 불가"라며
# 좁히지 않고 assertion 없이 종료(empty tattoo)→judge 굶음→final_answer=None.
# 레버 A/B(task A, n=6): finalized 17%→67%(+50pp), empty_tattoo 83%→33%. under-query
# 조기포기 실패 특화 — MANDATORY_TOOL_RULES(단일-needle 전사누락)와 독립.
# run_abc_chain(retrieval_discipline_prompt=True) 가 주입. 선행 "\n\n" 포함.
RETRIEVAL_DISCIPLINE_RULES = (
    "\n\n## RETRIEVAL DISCIPLINE (must follow while the failing item is still unknown):\n"
    "1. A broad search term (e.g. \"error\") returns mostly noise. Do NOT conclude that you "
    "\"cannot pinpoint the cause\" after a broad query returns unrelated volume.\n"
    "2. NARROW the search instead: try exact failure phrases such as \"Failed with result\", "
    "\"Main process exited\", or unit-name patterns like \".service\". Iterate with more specific "
    "patterns until you identify the failing unit.\n"
    "3. You MUST record at least one candidate service unit as a new_assertion before ending a "
    "cycle; never finish a cycle empty-handed while the failing unit is still unknown.\n"
)


# ── A2A Planner/Executor (Stage 12 opt-in, Exp24) ──
# scoped_emit_probe.py 가 검증한 경로 정식 편입: broad A-stage 의 emit 불안정(Phase0/§21
# 진단: A 가 ~50% chain 에서 assertion 0개 emit)을 Planner(도구로 finding 텍스트 산출)/
# Executor(finding 을 clean scoped 입력으로 도구 없이 emit) 두 단계로 분리해 완화한다.
# run_abc_chain(a2a_proposer=True) 가 opt-in. 기본 False 시 A-stage 완전 무변경(불변식).
A2A_PLANNER_SYSTEM = (
    "You are the PLANNER in a two-stage diagnostic pipeline. Your job is ONLY to find the "
    "single most important fact needed to answer the objective — e.g. which systemd service "
    "unit is crash-looping. Use the provided tools (grep_context / list_failed_units) to "
    "locate it in the cached log. Output ONE short plain-text sentence stating the finding "
    "(e.g. 'The crash-looping unit is gohttpserver.service.'). Do NOT output JSON, do NOT "
    "emit assertions — another agent will record it. If you cannot find it, say so plainly."
)


def build_a2a_planner_prompt(tattoo_json: str) -> list[dict]:
    """A2A Planner(Stage 12) 프롬프트: 도구로 finding 텍스트를 산출한다."""
    return [
        {"role": "system", "content": A2A_PLANNER_SYSTEM},
        {"role": "user", "content": f"Current tattoo (state):\n{tattoo_json}\n\n"
                                    "Find the single key fact and state it in one sentence."},
    ]


def build_a2a_executor_prompt(finding: str, tattoo_json: str) -> list[dict]:
    """A2A Executor(Stage 12) 프롬프트: probe(scoped_emit_probe) 조건 재현 —
    finding 을 clean scoped 입력으로, 도구 없이 emit."""
    scoped = (
        f"FACT (already established by the planner): {finding}\n\n"
        "Your ONLY task: record this established fact as a new_assertion (content: the fact, "
        "e.g. which unit is crash-looping and that it is failing), confidence >= 0.8. "
        "Do NOT call tools; the fact is already known. Emit at least one new_assertion."
    )
    # 기존 proposer schema/파서(extract_json_from_response, apply_llm_response) 재사용을
    # 위해 build_prompt 계열과 동일 형식 사용 — SYSTEM_PROMPT 기반 proposer 메시지에
    # scoped user 를 덧붙인다.
    msgs = build_prompt(tattoo_json)
    msgs.append({"role": "user", "content": scoped})
    return msgs
