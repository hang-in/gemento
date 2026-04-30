---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: scorer-failure-label-reference
parallel_group: C
depends_on: [02]
---

# Task 04 — Stage 2C 의 `ErrorMode` 통합 (alias / rename)

## Changed files

- `experiments/exp_h4_recheck/analyze.py` — **수정**. `ErrorMode` 제거 후 `from experiments.schema import FailureLabel as ErrorMode` 로 alias

수정 1, 신규 0.

## Change description

### 배경

Stage 2C task-03 의 `experiments/exp_h4_recheck/analyze.py` 가 자체 `ErrorMode` enum 정의 (Stage 2B 보다 먼저 작성됨). Stage 2B (본 plan) 의 `FailureLabel` 이 표준이 되면 Stage 2C 의 `ErrorMode` 는 alias 로 통합. 단순 import 변경.

### Step 1 — 현 `analyze.py` 의 `ErrorMode` 정의 위치 정찰

```bash
.venv/Scripts/python -c "
import inspect
text = open('experiments/exp_h4_recheck/analyze.py', encoding='utf-8').read()
# 'class ErrorMode' 위치
import re
m = re.search(r'class\s+ErrorMode\s*\(.*?\):.*?(?=\nclass|\ndef|\Z)', text, re.DOTALL)
if m:
    print(text.count('ErrorMode'))
    print('block start: line', text[:m.start()].count('\\n') + 1)
"
```

기대: `ErrorMode` 정의 + 사용처 카운트.

### Step 2 — `ErrorMode` 정의 제거 + alias import 로 변경

`analyze.py` 의 변경:

```python
# Before:
from enum import Enum

class ErrorMode(Enum):
    NONE = "none"
    FORMAT_ERROR = "format_error"
    # ... (9 values)

# After:
from experiments.schema import FailureLabel as ErrorMode
```

기존 `ErrorMode.X` 사용처 (`classify_error_mode` 함수 내부 + 단위 테스트) 는 변경 0 — alias 라 동일.

**중요**: enum value 가 *완전히 일치* 해야 함:
- 기존 `ErrorMode`: NONE / FORMAT_ERROR / WRONG_SYNTHESIS / EVIDENCE_MISS / NULL_ANSWER / CONNECTION_ERROR / PARSE_ERROR / TIMEOUT / OTHER
- `FailureLabel`: 동일 9 value (task-02 정의)

→ alias 로 동작 보장.

### Step 3 — Stage 2C task-03 의 reference 문서 갱신

Stage 2C 의 plan 본문 (`exp06-h4-recheck-expanded-taskset-pre-exp11-task-03.md`) 의 `ErrorMode` 정의 코드 stub 도 갱신 — 단순 import 로 변경. 본 task 가 Stage 2C plan 의 Step 1 코드 stub 의 ErrorMode 정의 부분을 alias import 로 정정 권고 (Sonnet 이 Stage 2C task-03 진행 시 본 정정된 코드 stub 적용).

또는 Stage 2C task-03 의 Step 1 의 코드 stub 만 정정 + analyze.py 의 ErrorMode 정의 자체는 Sonnet 진행 시점에 alias 로 작성.

**결정**: Stage 2C task-03 의 Step 1 코드 stub 의 ErrorMode 부분을 alias import 로 정정. analyze.py 의 실제 변경은 Sonnet 의 Stage 2C task-03 진행 시 본 정정 stub 그대로 적용.

→ 본 task 의 핵심 = **Stage 2C plan 의 코드 stub 정정**. analyze.py 자체 변경은 Sonnet (Stage 2C task-03 진행 시).

### Step 4 — Stage 2C task-03 의 코드 stub 정정 (실제 진행)

`docs/plans/exp06-h4-recheck-expanded-taskset-pre-exp11-task-03.md` 의 Step 1 의 코드 stub:

```python
# Before:
from enum import Enum

class ErrorMode(Enum):
    NONE = "none"
    FORMAT_ERROR = "format_error"
    # ...

# After:
from experiments.schema import FailureLabel as ErrorMode  # Stage 2B 통합
```

이 정정을 본 task (Stage 2B task-04) 에서 Stage 2C plan 본문에 직접 반영.

## Dependencies

- task-02 마감 (`FailureLabel` enum 정의 + `schema.py` 에 추가)
- Stage 2C task-03 진행 *전* 본 task 마감 — Sonnet 이 Stage 2C task-03 진행 시 정정된 stub 사용

## Verification

```bash
# 1) Stage 2C task-03 의 코드 stub 정정 확인
.venv/Scripts/python -c "
text = open('docs/plans/exp06-h4-recheck-expanded-taskset-pre-exp11-task-03.md', encoding='utf-8').read()
# 'from experiments.schema import FailureLabel as ErrorMode' 가 코드 stub 안에 있어야
assert 'FailureLabel as ErrorMode' in text or 'FailureLabel' in text, 'Stage 2C task-03 stub 미정정'
# class ErrorMode 의 직접 정의 (9 value) 가 제거되어야
import re
direct_def = re.search(r'class\s+ErrorMode\s*\(\s*Enum\s*\)\s*:', text)
# direct_def 가 있어도 OK (heuristic) — 단 alias 가 우선 등장하면 통과
print('verification 1 ok: stub 정정')
"

# 2) Stage 2C analyze.py (Sonnet 진행 후) 의 alias 확인 — 본 task 시점에는 미진행 가능
# Sonnet 의 Stage 2C task-03 진행 후 별도 검증
```

## Risks

- **Risk 1 — Stage 2C task-03 진행 순서 의존**: 본 task 가 Stage 2C task-03 *전* 마감해야 Sonnet 의 Stage 2C task-03 진행 시 정정 stub 적용. 순서 보장 — Stage 2A 마감 → Stage 2B 진행 → Stage 2C 진행.
- **Risk 2 — `analyze.py` 의 ErrorMode 사용처 (Sonnet 작성 시) 와 alias 불일치**: 본 task 가 Stage 2C plan 의 stub 만 정정. 실제 analyze.py 는 Sonnet 작성. enum value 동일 보장 (task-02 의 9 value) 으로 alias 동작.
- **Risk 3 — Sonnet 이 Stage 2C task-03 의 정정된 stub 무시하고 자체 ErrorMode 정의**: Stage 2C plan 의 Step 1 disclosure 명시 — alias 의무. Sonnet 진행 가이드에서도 명시.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/schema.py` (task-02 영역) — `FailureLabel` 변경 금지
- `experiments/run_helpers.py` — 변경 금지
- `experiments/exp_h4_recheck/analyze.py` (Stage 2C 영역) — Sonnet 진행 시점에 작성됨. 본 task 시점에는 plan 의 stub 정정만
- 기존 reference 문서 — 변경 금지
- 다른 plan 파일 (Stage 2C task-03 외)
- 결과 JSON
