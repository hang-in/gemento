---
type: plan-task
status: todo
updated_at: 2026-05-03
parent_plan: exp12-extractor-role-pre-search
parallel_group: A
depends_on: []
---

# Task 01 — `EXTRACTOR_PROMPT` + `build_extractor_prompt()`

## Changed files

- `experiments/system_prompt.py` — **수정 (추가만)**. `EXTRACTOR_PROMPT` 신규 + `build_extractor_prompt(task_prompt: str) -> list[dict]` 함수

수정 1 (추가만), 신규 0.

## Change description

### 배경

Extractor Role 신규 — task prompt 의 원문/문맥에서 claim/entity 사전 추출. A 의 부담 감소 + assertion 안정화 (가설 H11). 기존 `SYSTEM_PROMPT` (Proposer A) / `CRITIC_PROMPT` (B) / `JUDGE_PROMPT` (C) 패턴 그대로 추가.

### Step 1 — `experiments/system_prompt.py` 의 기존 prompt 정찰

```bash
.venv/Scripts/python -c "
import inspect
import experiments.system_prompt as sp
prompts = [n for n in dir(sp) if n.endswith('PROMPT')]
print('기존 PROMPT 상수:', prompts)
funcs = [n for n in dir(sp) if n.startswith('build_')]
print('기존 build 함수:', funcs)
"
```

기대: `SYSTEM_PROMPT`, `CRITIC_PROMPT`, `JUDGE_PROMPT` + `build_prompt`, `build_critic_prompt`, `build_judge_prompt` 등.

### Step 2 — `EXTRACTOR_PROMPT` 추가

`system_prompt.py` 끝 (또는 JUDGE_PROMPT 옆) 에 추가:

```python
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
```

### Step 3 — `build_extractor_prompt()` 함수 추가

기존 `build_prompt` / `build_critic_prompt` 패턴 따름:

```python
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
```

### Step 4 — module-level export 확인

`system_prompt.py` 의 `__all__` 가 정의되어 있으면 추가:

```python
__all__ = [..., "EXTRACTOR_PROMPT", "build_extractor_prompt"]
```

`__all__` 미정의 시 추가 0 (Python convention 자동 export).

## Dependencies

- 패키지: 없음 (마크다운/Python 텍스트 추가만)
- 다른 subtask: 없음 (parallel_group A, 첫 노드)

## Verification

```bash
# 1) syntax + import
.venv/Scripts/python -m py_compile experiments/system_prompt.py
.venv/Scripts/python -c "
from experiments.system_prompt import (
    SYSTEM_PROMPT, CRITIC_PROMPT, JUDGE_PROMPT, EXTRACTOR_PROMPT,
    build_prompt, build_critic_prompt, build_judge_prompt, build_extractor_prompt,
)
print('verification 1 ok: 기존 + EXTRACTOR_PROMPT import')
"

# 2) build_extractor_prompt 시그니처
.venv/Scripts/python -c "
from experiments.system_prompt import build_extractor_prompt
msgs = build_extractor_prompt('A store sells apples...')
assert len(msgs) == 2
assert msgs[0]['role'] == 'system'
assert msgs[1]['role'] == 'user'
assert 'EXTRACTOR' in msgs[0]['content'] or 'Extractor' in msgs[0]['content']
print('verification 2 ok: build_extractor_prompt 동작')
"

# 3) EXTRACTOR_PROMPT 의 핵심 키워드
.venv/Scripts/python -c "
from experiments.system_prompt import EXTRACTOR_PROMPT
for kw in ('claims', 'entities', 'JSON', 'do NOT solve', 'do NOT propose'):
    assert kw.lower() in EXTRACTOR_PROMPT.lower(), f'{kw} missing'
print('verification 3 ok: EXTRACTOR_PROMPT 핵심 키워드')
"
```

3 명령 모두 정상.

## Risks

- **Risk 1 — Gemma 의 JSON 응답 한계**: Exp10 v3 의 4 fail 패턴. EXTRACTOR_PROMPT 가 strict JSON 강제 + simple schema 라 일반 A prompt 보다 안정적 예상. 단 dry-run 시 검증
- **Risk 2 — A prompt 와의 schema 호환**: Extractor 결과를 A 의 input 에 prefix 로 주입 시, A 가 Extractor 의 claims 를 자기 assertions 와 혼동 가능. **prompt 명시: "A 는 Extractor claims 를 *입력 정리* 로 받고 자기 assertions 별도 작성"** — task-02 의 prefix 형식에서 명세
- **Risk 3 — Extractor prompt 의 잘못된 추출**: synthesis task 의 multi-source data 또는 logic 의 inconsistent data 같은 task 에서 Extractor 가 잘못 추출. dry-run 시 logic-02 / synthesis-* 표본 확인
- **Risk 4 — Sonnet 이 SYSTEM_PROMPT / CRITIC_PROMPT / JUDGE_PROMPT 변경 시도**: 본 task = EXTRACTOR_PROMPT 추가만. 기존 prompt 변경 금지

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/orchestrator.py` (task-02 영역)
- `experiments/measure.py` / `score_answer_v*` — 본 plan 영역 외
- `experiments/run_helpers.py` (Stage 2A) — 변경 금지
- `experiments/schema.py` — 변경 금지
- 모든 기존 `experiments/exp**/run.py` — 변경 금지
- `experiments/_external/gemini_client.py` — 변경 금지 (Exp11 영역)
- 기존 `SYSTEM_PROMPT` / `CRITIC_PROMPT` / `JUDGE_PROMPT` 본문 — 변경 금지 (추가만)
