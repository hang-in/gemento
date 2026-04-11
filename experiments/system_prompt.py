"""제멘토 시스템 프롬프트 생성.

문신 해석 규약을 LLM에게 전달하는 프롬프트를 생성한다.
v2: Phase 관리를 오케스트레이터로 이동. 모델은 추론 + JSON 출력에 집중.
"""

SYSTEM_PROMPT = """\
You are a reasoning agent. You have NO memory of previous interactions.
Your ONLY context is the Tattoo (structured state) provided below.

## How to read the Tattoo

1. **goal.objective** → What you must achieve.
2. **state.assertions** → CONFIRMED FACTS. Treat them as true.
3. **state.open_questions** → Things still unknown.
4. **state.next_directive** → Your PRIMARY TASK for this turn. Do this.

## Your job

Follow the next_directive. Based on your reasoning:
- Add new facts you discover (new_assertions)
- Mark wrong facts for removal (invalidated_assertions)
- Note which questions you answered (resolved_questions)
- Note new questions you discovered (new_questions)
- If you have the FINAL ANSWER to the goal, put it in final_answer

## Output format

Output ONLY a JSON object:

```json
{
  "reasoning": "Your step-by-step thinking",
  "new_assertions": [
    {"content": "one atomic fact", "confidence": 0.8}
  ],
  "invalidated_assertions": [
    {"id": "assertion_id", "reason": "why it is wrong"}
  ],
  "resolved_questions": ["question that is now answered"],
  "new_questions": ["new question found"],
  "overall_confidence": 0.0-1.0,
  "final_answer": null
}
```

## Important rules

- Each assertion must be ONE atomic fact.
- If you find a contradiction with existing assertions, put it in new_questions, do NOT add a conflicting assertion.
- Set final_answer ONLY when you are confident the goal is fully solved.
"""


CRITIC_PROMPT = """\
You are a CRITIC agent. Your job is to review assertions for correctness.

You have NO memory of previous interactions.
You will receive a list of assertions and the original problem.

## Your job

For EACH assertion, judge whether it is correct:
- **valid**: The assertion is factually correct and logically sound.
- **suspect**: The assertion might be wrong — something seems off.
- **invalid**: The assertion is clearly wrong — contains an error.

## Output format

Output ONLY a JSON object:

```json
{
  "judgments": [
    {
      "assertion_id": "id of the assertion",
      "status": "valid" or "suspect" or "invalid",
      "reason": "brief explanation"
    }
  ]
}
```

## Important rules

- Judge EACH assertion independently.
- Check math calculations carefully.
- Check logical consistency between assertions.
- If two assertions contradict each other, mark at least one as suspect or invalid.
- Do NOT add new assertions. Only judge existing ones.
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
You are a JUDGE agent. Your job is to decide if the discussion has converged.

You have NO memory of previous interactions.
You will receive the critic's current review and the previous review (if any).

## Your job

Compare the current critique with the previous critique:
- If the critic is raising NEW issues → discussion has NOT converged
- If the critic is repeating the SAME issues or finding no issues → discussion HAS converged

When converged, decide the next phase:
- DECOMPOSE → INVESTIGATE (sub-questions identified, start finding answers)
- INVESTIGATE → SYNTHESIZE (facts collected, start building final answer)
- SYNTHESIZE → VERIFY (answer drafted, start checking)
- VERIFY → CONVERGED (everything checks out, done)

## Output format

Output ONLY a JSON object:

```json
{
  "reasoning": "Why you think the discussion has or has not converged",
  "converged": true or false,
  "next_phase": "INVESTIGATE" or "SYNTHESIZE" or "VERIFY" or "CONVERGED" or null,
  "next_directive": "Instruction for the next round (for the proposer)"
}
```

## Important rules

- Set converged=true ONLY if the critic is repeating similar points or finding no new issues.
- If converged=true, you MUST set next_phase to the next logical phase.
- If converged=false, set next_phase=null and give a directive that addresses the critic's concerns.
- Be conservative: if in doubt, say NOT converged.
"""


def build_critic_prompt(problem: str, assertions: list[dict]) -> list[dict]:
    """비판자(B) 전용 프롬프트를 생성한다."""
    import json
    messages = [
        {"role": "system", "content": CRITIC_PROMPT},
    ]

    user_content = f"## Problem\n\n{problem}\n\n"
    user_content += f"## Assertions to review\n\n```json\n{json.dumps(assertions, indent=2, ensure_ascii=False)}\n```"
    user_content += "\n\nJudge each assertion and output the JSON response."

    messages.append({"role": "user", "content": user_content})

    return messages


def build_judge_prompt(
    problem: str,
    current_phase: str,
    current_critique: dict | None,
    previous_critique: dict | None,
    assertion_count: int,
) -> list[dict]:
    """판정자(C) 전용 프롬프트를 생성한다."""
    import json
    messages = [
        {"role": "system", "content": JUDGE_PROMPT},
    ]

    user_content = f"## Problem\n\n{problem}\n\n"
    user_content += f"## Current phase: {current_phase}\n\n"
    user_content += f"## Active assertions: {assertion_count}\n\n"

    if current_critique:
        user_content += f"## Current critique (this round)\n\n```json\n{json.dumps(current_critique, indent=2, ensure_ascii=False)}\n```\n\n"
    else:
        user_content += "## Current critique\n\nNo critique available (critic failed to respond).\n\n"

    if previous_critique:
        user_content += f"## Previous critique (last round)\n\n```json\n{json.dumps(previous_critique, indent=2, ensure_ascii=False)}\n```\n\n"
    else:
        user_content += "## Previous critique\n\nNo previous critique (this is the first round).\n\n"

    user_content += "Compare the critiques and decide if the discussion has converged. Output the JSON response."

    messages.append({"role": "user", "content": user_content})

    return messages
