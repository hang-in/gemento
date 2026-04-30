---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: scorer-failure-label-reference
parallel_group: B
depends_on: []
---

# Task 02 — `FailureLabel` enum + `schema.py` 추가

## Changed files

- `experiments/schema.py` — **수정 (추가만)**. `FailureLabel` enum 추가

수정 1 (추가만), 신규 0.

## Change description

### 배경

failure label 의 표준 enum 신규. namingConventions.md §9.3 + Stage 2C 의 `ErrorMode` enum 의 정의 그대로. `experiments/schema.py` 에 추가하여 다른 도구가 import.

### Step 1 — `experiments/schema.py` 의 기존 구조 정찰

```bash
.venv/Scripts/python -c "
import experiments.schema as s
import inspect
classes = [name for name, obj in inspect.getmembers(s) if inspect.isclass(obj) and obj.__module__ == 'experiments.schema']
print('기존 classes:', classes)
"
```

기대: `Tattoo`, `Assertion`, `HandoffEntry` 등 기존 dataclass / TypedDict. 본 task 는 신규 enum 추가만 — 기존 변경 0.

### Step 2 — `FailureLabel` enum 추가

`experiments/schema.py` 의 적절한 위치 (파일 끝 또는 dataclass 정의 후) 에 추가:

```python
from enum import Enum


class FailureLabel(Enum):
    """trial result 의 failure / success 분류.

    namingConventions.md §9.3 와 Stage 2C `ErrorMode` 의 표준 정의.
    Stage 2C 의 `experiments/exp_h4_recheck/analyze.py:ErrorMode` 는 본 enum 의 alias.

    분류 의미:
    - NONE: 정답 (acc_v3 ≥ 0.5 등 task 별 기준)
    - FORMAT_ERROR: JSON parse / schema 위반 (final_answer 없음 또는 malformed)
    - WRONG_SYNTHESIS: 형식은 OK 인데 내용 틀림 (acc < 0.5, len > 10)
    - EVIDENCE_MISS: evidence_ref 누락 또는 잘못된 출처 (heuristic, Stage 2C+)
    - NULL_ANSWER: final_answer 가 None / 빈 문자열
    - CONNECTION_ERROR: WinError 10061 등 (Stage 2A `TrialError.CONNECTION_ERROR` 와 동기)
    - PARSE_ERROR: Stage 2A `TrialError.PARSE_ERROR` 와 동기
    - TIMEOUT: Stage 2A `TrialError.TIMEOUT` 와 동기
    - OTHER: 미분류
    """

    NONE = "none"
    FORMAT_ERROR = "format_error"
    WRONG_SYNTHESIS = "wrong_synthesis"
    EVIDENCE_MISS = "evidence_miss"
    NULL_ANSWER = "null_answer"
    CONNECTION_ERROR = "connection_error"
    PARSE_ERROR = "parse_error"
    TIMEOUT = "timeout"
    OTHER = "other"
```

위 코드 그대로 추가. 기존 import / dataclass 변경 0.

### Step 3 — Stage 2A `TrialError` 와의 관계 명시 (docstring 만)

`schema.py` 의 `FailureLabel` docstring 에 다음 disclosure 추가 (Step 2 의 docstring 그대로 — `Stage 2A TrialError 와 동기`).

`run_helpers.py` (Stage 2A 영역) 의 `TrialError` 변경 금지 — 본 plan 영역 외.

### Step 4 — `__all__` 또는 module-level export

`schema.py` 의 `__all__` 가 정의되어 있으면 `FailureLabel` 추가:

```python
__all__ = [..., "FailureLabel"]
```

`__all__` 미정의 시 추가 의무 0 (Python convention, public 자동 export).

## Dependencies

- 패키지: 표준만 (`enum`)
- 다른 subtask: 없음 (parallel_group B, 첫 노드)
- 기존 `experiments/run_helpers.py:TrialError` 와 의미적 정합 — 단 import 의존성 0 (각각 독립 정의)

## Verification

```bash
# 1) syntax + import
.venv/Scripts/python -c "
from experiments.schema import FailureLabel
assert FailureLabel.NONE.value == 'none'
assert FailureLabel.FORMAT_ERROR.value == 'format_error'
assert FailureLabel.CONNECTION_ERROR.value == 'connection_error'
print('verification 1 ok: FailureLabel enum')
"

# 2) 기존 Tattoo / Assertion import 영향 0
.venv/Scripts/python -c "
from experiments.schema import Tattoo, Assertion
print('verification 2 ok: 기존 dataclass 보존')
"

# 3) Stage 2A 의 TrialError 도 import 가능 (충돌 0)
.venv/Scripts/python -c "
from experiments.schema import FailureLabel
from experiments.run_helpers import TrialError
# 의미 매핑 (수동 검증)
mapping = {
    TrialError.CONNECTION_ERROR: FailureLabel.CONNECTION_ERROR,
    TrialError.TIMEOUT: FailureLabel.TIMEOUT,
    TrialError.PARSE_ERROR: FailureLabel.PARSE_ERROR,
    TrialError.MODEL_ERROR: FailureLabel.OTHER,
    TrialError.OTHER: FailureLabel.OTHER,
}
assert all(mapping[k].value in ('connection_error', 'timeout', 'parse_error', 'other') for k in mapping)
print('verification 3 ok: TrialError ↔ FailureLabel 의미 매핑')
"
```

3 명령 모두 정상.

## Risks

- **Risk 1 — `schema.py` 의 import side-effect**: 기존 dataclass 의 `__post_init__` 등에서 enum 사용 시 영향. 정찰 필요. 본 task 는 신규 추가만이라 영향 0 예상.
- **Risk 2 — Stage 2A `TrialError` 와의 중복**: 두 enum 이 비슷한 분류. 의미적 alias 관계 — Stage 2A `TrialError` 는 *trial 단위 error 분류* (run_helpers.py 의 fatal abort 결정용), 본 plan `FailureLabel` 은 *분석 단위 분류* (analyze 측 + 보고서 라벨링). 사용 영역 다름 — 통합하지 않고 의미 매핑만 docstring 명시.
- **Risk 3 — Sonnet 이 `TrialError` 와 통합 시도**: 본 plan 영역 외 (Stage 2A 영역). Scope boundary 엄수.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/run_helpers.py` (Stage 2A 영역) — `TrialError` 변경 / 통합 금지
- `experiments/measure.py` — 본 plan 영역 외
- `experiments/orchestrator.py` — 변경 금지
- 모든 `experiments/exp**/run.py` — 변경 금지
- 모든 결과 JSON / 분석 helper — 변경 금지
- README / researchNotebook / 다른 reference 문서
