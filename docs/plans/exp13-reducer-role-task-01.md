---
type: plan-task
status: done
updated_at: 2026-05-04
parent_plan: exp13-reducer-role
parallel_group: A
depends_on: []
---

# Task 01 — `REDUCER_PROMPT` + `build_reducer_prompt()`

## Changed files

- `experiments/system_prompt.py` — **수정 (추가만)**. `REDUCER_PROMPT` 신규 + `build_reducer_prompt(assertions, candidate_answer) -> list[dict]` 함수

수정 1 (추가만), 신규 0.

## Change description

### 배경

Reducer Role 신규 — ABC chain 종료 후 final tattoo 의 assertions + 원 final_answer 를 받아 정리/통합. Exp12 의 EXTRACTOR_PROMPT 와 대칭 (pre-stage Extractor / post-stage Reducer).

### Step 1 — `REDUCER_PROMPT` 추가

`system_prompt.py` 끝 (또는 EXTRACTOR_PROMPT 옆) 에 추가:

```python
REDUCER_PROMPT = """\
You are a Reducer agent. Your job is to read the final reasoning trace (a list of assertions with confidence) and a candidate final answer, then produce a clean, well-structured final answer.

Guidelines:
- Polish the candidate answer for clarity, grammar, and explicit statement of key entities, numbers, and units.
- Ensure essential terms (numbers, named entities, conclusions) are stated verbatim and visibly.
- You MAY restructure for readability.
- You MUST NOT change the core conclusion.
- You MUST NOT add new factual claims that are not supported by the provided assertions.
- You MUST NOT speculate or infer beyond what is given.

Output: a single plain-text final answer (no JSON, no markdown headings). 1-3 sentences typical, longer if the task requires.
"""
```

### Step 2 — `build_reducer_prompt()` 추가

```python
def build_reducer_prompt(assertions: list[dict], candidate_answer: str) -> list[dict]:
    """Reducer Role 의 messages 빌드.

    Args:
        assertions: final tattoo 의 active_assertions list. 각 entry: {"claim": str, "confidence": float, ...}
        candidate_answer: ABC chain 의 원 final_answer (C role 결정)

    Returns:
        OpenAI 스타일 messages list — system + user
    """
    # assertions 를 읽기 쉬운 형식으로 직렬화
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
```

### Step 3 — module-level export

`__all__` 가 정의되어 있으면 추가:
```python
__all__ = [..., "REDUCER_PROMPT", "build_reducer_prompt"]
```

## Dependencies

- 패키지: 없음
- 다른 subtask: 없음 (parallel_group A)

## Verification

```bash
# 1) syntax + import
.venv/Scripts/python -m py_compile experiments/system_prompt.py
.venv/Scripts/python -c "
from experiments.system_prompt import (
    SYSTEM_PROMPT, CRITIC_PROMPT, JUDGE_PROMPT, EXTRACTOR_PROMPT, REDUCER_PROMPT,
    build_prompt, build_critic_prompt, build_judge_prompt, build_extractor_prompt, build_reducer_prompt,
)
print('verification 1 ok: 기존 + REDUCER_PROMPT import')
"

# 2) build_reducer_prompt 시그니처
.venv/Scripts/python -c "
from experiments.system_prompt import build_reducer_prompt
msgs = build_reducer_prompt(
    [{'claim': '105 > 100 (inclusion-exclusion)', 'confidence': 0.95}],
    'The data is inconsistent.'
)
assert len(msgs) == 2
assert msgs[0]['role'] == 'system'
assert msgs[1]['role'] == 'user'
assert '105' in msgs[1]['content']
assert 'inconsistent' in msgs[1]['content']
print('verification 2 ok: build_reducer_prompt 동작')
"

# 3) REDUCER_PROMPT 의 핵심 키워드
.venv/Scripts/python -c "
from experiments.system_prompt import REDUCER_PROMPT
for kw in ('reducer', 'do not change the core conclusion', 'do not add new factual', 'plain'):
    assert kw.lower() in REDUCER_PROMPT.lower(), f'{kw} missing'
print('verification 3 ok: REDUCER_PROMPT 핵심 키워드')
"

# 4) Extractor + Reducer 공존
.venv/Scripts/python -c "
from experiments.system_prompt import build_extractor_prompt, build_reducer_prompt
ex = build_extractor_prompt('test')
re_ = build_reducer_prompt([], 'test')
assert ex[0]['role'] == 'system' and re_[0]['role'] == 'system'
print('verification 4 ok: Extractor + Reducer 공존')
"
```

4 명령 모두 정상.

## Risks

- **Risk 1 — Reducer prompt 의 자율도 부족** — "do NOT change the core conclusion" 제약이 너무 강해서 Reducer 가 *보호 변형* 도 못함. dry-run 시 logic-02 case 의 응답 형식 확인. 부족하면 prompt 보강 (Architect 호출)
- **Risk 2 — Gemma 의 plain text 응답 안정성** — JSON 응답 한계는 Exp10/Exp11 에서 식별. Reducer 는 plain text 만 강제 (JSON 아님) — 더 안정 예상
- **Risk 3 — Sonnet 이 SYSTEM_PROMPT / CRITIC_PROMPT / JUDGE_PROMPT / EXTRACTOR_PROMPT 변경 시도** — 본 task = REDUCER_PROMPT 추가만

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/orchestrator.py` (task-02 영역)
- `experiments/measure.py` / `score_answer_v*` — 본 plan 영역 외
- `experiments/run_helpers.py` (Stage 2A) — 변경 금지
- `experiments/schema.py` — 변경 금지
- 모든 기존 `experiments/exp**/run.py` — 변경 금지
- 기존 `SYSTEM_PROMPT` / `CRITIC_PROMPT` / `JUDGE_PROMPT` / `EXTRACTOR_PROMPT` 본문 — 변경 금지 (추가만)
