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
