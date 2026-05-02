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
