---
type: plan-task
status: pending
updated_at: 2026-05-05
parent_plan: stage-6-cross-model-llm-as-judge
parallel_group: A
depends_on: []
---

# Task 01 — Groq client 확장 + LLM-as-judge 인프라

## Changed files

- `experiments/_external/groq_client.py` — **수정 (추가만)**. batch helper + rate limit retry decorator + judge wrapper helper
- `experiments/_external/llm_judge.py` — **신규**. `judge_answer()` / `compare_answers()` helper. Groq GPT-OSS 120B 기반 의미적 채점

수정 1 (추가만), 신규 1.

## Change description

### 배경

Stage 6 의 두 갈래 (cross-model + LLM-as-judge) 의 인프라. 기존 Groq client (commit `b389534`) 는 단일 호출만 — batch 처리 / rate limit 재시도 / judge wrapper 추가 필요.

### Step 1 — `groq_client.py` 의 rate limit retry decorator

Groq free tier 의 30 RPM / 6K TPM / 1000 RPD 한도 → 429 응답 시 자동 wait + retry.

```python
def with_rate_limit_retry(max_retries: int = 3, initial_wait: float = 5.0):
    """429 응답 시 exponential backoff 재시도. wait 초 × 2^attempt."""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                result: CallMeter = fn(*args, **kwargs)
                if result.error and "HTTP 429" in (result.error or ""):
                    if attempt < max_retries:
                        wait = initial_wait * (2 ** attempt)
                        print(f"  [rate limit] wait {wait}s (attempt {attempt+1}/{max_retries})")
                        time.sleep(wait)
                        continue
                return result
            return result
        return wrapper
    return decorator


# 사용
@with_rate_limit_retry(max_retries=3, initial_wait=5.0)
def call_with_meter_retry(messages, model=LLAMA_3_1_8B, **kwargs) -> CallMeter:
    return call_with_meter(messages, model=model, **kwargs)
```

기존 `call_with_meter` 보존 — 새 `call_with_meter_retry` 가 wrapper.

### Step 2 — batch helper (선택, 시간 여유 시)

cross-model run 시 trial 간 sleep 추가 — 30 RPM 한도 (= 2초/req) 안에서 안전하게.

```python
def batch_call(messages_list: list, model: str, sleep_between: float = 2.5, **kwargs) -> list[CallMeter]:
    """여러 메시지 순차 호출 + sleep. RPM 한도 회피."""
    results = []
    for i, messages in enumerate(messages_list):
        if i > 0:
            time.sleep(sleep_between)
        results.append(call_with_meter_retry(messages, model=model, **kwargs))
    return results
```

### Step 3 — `llm_judge.py` 신규

H12 / H13 의 의미적 채점 헬퍼.

```python
"""LLM-as-judge auxiliary evaluation for H12 (Reducer) and H13 (Search Tool).

P1-3 in docs/reference/paper-review-action-items-2026-05-05.md.

Uses Groq GPT-OSS 120B (reasoning model) as cross-evaluator.
"""
from __future__ import annotations
import json
from .groq_client import call_with_meter_retry, GPT_OSS_120B


JUDGE_SYSTEM_PROMPT = """You are an expert evaluator of question answering. \
Given a question, an expected answer, and a candidate answer, you assess whether \
the candidate answer is semantically correct.

Output a single JSON object: {"correct": true|false, "score": 0-5, "reason": "<one sentence>"}

Scoring rubric:
- 5: candidate fully captures the expected answer with correct facts
- 4: candidate captures the core fact but with minor omissions or imprecise phrasing
- 3: candidate is partially correct (some facts right, some wrong/missing)
- 2: candidate is mostly wrong but has some related correct content
- 1: candidate is clearly wrong or contradicts the expected answer
- 0: candidate is empty, irrelevant, or refuses to answer

"correct" is true iff score >= 4."""


def judge_answer(
    question: str,
    expected_answer: str,
    candidate_answer: str,
    model: str = GPT_OSS_120B,
) -> dict:
    """단일 답변의 의미적 채점.

    Returns:
        {"correct": bool, "score": int 0-5, "reason": str, "raw_response": str, "error": str|None}
    """
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"## Question\n{question}\n\n"
            f"## Expected answer\n{expected_answer}\n\n"
            f"## Candidate answer\n{candidate_answer or '(empty)'}\n\n"
            f"Output the JSON verdict only."
        )},
    ]
    result = call_with_meter_retry(
        messages, model=model,
        response_format={"type": "json_object"},
        max_tokens=2048,
    )
    if result.error:
        return {"correct": None, "score": None, "reason": None, "error": result.error}
    try:
        parsed = json.loads(result.raw_response)
        return {
            "correct": bool(parsed.get("correct")),
            "score": int(parsed.get("score", 0)),
            "reason": parsed.get("reason", ""),
            "raw_response": result.raw_response,
            "error": None,
        }
    except Exception as e:
        return {"correct": None, "score": None, "reason": None,
                "raw_response": result.raw_response, "error": f"parse failed: {e}"}


PAIR_COMPARE_SYSTEM = """You compare two candidate answers (A and B) to the same question. \
Decide which is semantically more correct given the expected answer. Order is randomized — \
do not assume A is always the baseline.

Output a single JSON object: {"winner": "A"|"B"|"tie", "score_A": 0-5, "score_B": 0-5, "reason": "<one sentence>"}"""


def compare_answers(
    question: str,
    expected_answer: str,
    answer_A: str,
    answer_B: str,
    model: str = GPT_OSS_120B,
) -> dict:
    """두 답변의 직접 비교 — paired evaluation. order randomized 권장 (caller 책임)."""
    messages = [
        {"role": "system", "content": PAIR_COMPARE_SYSTEM},
        {"role": "user", "content": (
            f"## Question\n{question}\n\n"
            f"## Expected answer\n{expected_answer}\n\n"
            f"## Answer A\n{answer_A or '(empty)'}\n\n"
            f"## Answer B\n{answer_B or '(empty)'}\n\n"
            f"Output the JSON verdict only."
        )},
    ]
    result = call_with_meter_retry(
        messages, model=model,
        response_format={"type": "json_object"},
        max_tokens=2048,
    )
    if result.error:
        return {"winner": None, "error": result.error}
    try:
        parsed = json.loads(result.raw_response)
        return {
            "winner": parsed.get("winner"),
            "score_A": int(parsed.get("score_A", 0)),
            "score_B": int(parsed.get("score_B", 0)),
            "reason": parsed.get("reason", ""),
            "raw_response": result.raw_response,
            "error": None,
        }
    except Exception as e:
        return {"winner": None, "error": f"parse failed: {e}",
                "raw_response": result.raw_response}
```

### Step 4 — `_external/__init__.py` export

```python
from .llm_judge import judge_answer, compare_answers
```

`__all__` 갱신.

## Dependencies

- Stage 5 commit `b389534` (Groq client smoke test 완료)
- 패키지: 없음
- 환경 변수: `GROQ_API_KEY` (`.env` 등록 완료)

## Verification

```bash
# 1) syntax + import
.venv/Scripts/python -m py_compile experiments/_external/groq_client.py experiments/_external/llm_judge.py
.venv/Scripts/python -c "
from experiments._external.llm_judge import judge_answer, compare_answers
from experiments._external.groq_client import call_with_meter_retry, GPT_OSS_120B
print('verification 1 ok: imports')
"

# 2) judge_answer smoke test (1 호출, free tier, GPT-OSS 120B)
.venv/Scripts/python -c "
from experiments._external.llm_judge import judge_answer
result = judge_answer(
    question='What is 17 * 23?',
    expected_answer='391',
    candidate_answer='The answer is 391.',
)
assert result['correct'] is True
assert result['score'] >= 4
assert result['error'] is None
print(f'verification 2 ok: judge_answer = {result}')
"

# 3) compare_answers smoke test
.venv/Scripts/python -c "
from experiments._external.llm_judge import compare_answers
result = compare_answers(
    question='What is the capital of Japan?',
    expected_answer='Tokyo',
    answer_A='The capital is Tokyo.',
    answer_B='I am not sure, possibly Osaka.',
)
assert result['winner'] == 'A'
assert result['score_A'] > result['score_B']
print(f'verification 3 ok: compare_answers = {result}')
"

# 4) rate limit decorator (mock 429 — 본격 테스트는 task-04 시점)
.venv/Scripts/python -c "
from experiments._external.groq_client import with_rate_limit_retry
import inspect
src = inspect.getsource(with_rate_limit_retry)
assert 'HTTP 429' in src
assert 'exponential' in src or '2 \*\* attempt' in src
print('verification 4 ok: rate limit decorator 구조')
"
```

4 명령 모두 정상.

## Risks

- **Risk 1 — JSON 응답 강제 실패**: GPT-OSS 가 reasoning model 이라 `response_format=json_object` 불안정 가능. parse 실패 시 reason field 만 누락, error key 채우는 graceful fallback 적용
- **Risk 2 — judge 의 self-bias**: GPT-OSS 120B 가 *특정 답변 스타일 (장문 vs 단답)* 선호 가능. paired comparison 시 order randomization 의무 (caller 책임 — task-03 의 run.py 에서 50% A/B swap)
- **Risk 3 — rate limit 위반**: 1000 RPD 한도 — 본 task 의 verification 4 호출 정도는 안전. task-04 시 batch 호출 시 sleep_between=2.5s 적용
- **Risk 4 — Sonnet 이 기존 `call_with_meter` 본체 변경**: 본 task = wrapper / decorator / 신규 module 만. `call_with_meter` 본체 절대 변경 금지

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/orchestrator.py` (task-02 영역)
- `experiments/cross_model/run.py` (task-03 영역, 미존재)
- `experiments/measure.py` / `score_answer_v*`
- `experiments/run_helpers.py`
- `experiments/schema.py`
- `experiments/_external/gemini_client.py` (Exp11 영역)
- 모든 기존 `experiments/exp**/run.py`
- 결과 JSON

`groq_client.py` 에서 변경 금지 영역:
- 기존 `call_with_meter` 본체 (signature + 핵심 로직). decorator + wrapper 만 추가
- 기존 모델 상수 (LLAMA_3_1_8B / GPT_OSS_120B 등)
- `CallMeter` schema (단 reasoning_tokens 필드 등 기존 추가는 보존)
