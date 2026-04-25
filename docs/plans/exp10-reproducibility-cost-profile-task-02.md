---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: exp10-reproducibility-cost-profile
parallel_group: A
depends_on: []
---

# Task 02 — 9 핵심 task subset 확정 + 채점 spec

## Changed files

- `experiments/exp10_reproducibility_cost/__init__.py` — **신규** (빈 파일, 패키지 표지)
- `experiments/exp10_reproducibility_cost/tasks.py` — **신규**. `EXP10_TASK_IDS` 상수 + 채점 함수 위임

신규 외 다른 파일 수정 금지. `experiments/tasks/taskset.json` 은 import 만.

## Change description

### 배경

Exp10 의 9 task subset 을 plan 에 명시 결정 후 실제 검증 가능한 코드 상수로 확정한다. 본 task 는 LLM 호출 0 — taskset 검증·채점 함수 정의만.

### 9 task 확정 (verified against `experiments/tasks/taskset.json`)

`taskset.json` 12 task 중 9 개 선정:

| Task | 카테고리 | 선정 사유 |
|------|---------|----------|
| math-01 | Math | Exp08/08b 검증 |
| math-02 | Math | Exp08/08b 검증 |
| math-03 | Math | Exp08/08b 검증 |
| math-04 | Math | Exp08b 100% 도달 — 핵심 비교 case |
| synthesis-01 | Synthesis | Exp04~06 검증, 안정 |
| synthesis-03 | Synthesis | Exp04~06 검증, 안정 |
| synthesis-04 | Synthesis | Exp04~06 검증 |
| logic-03 | Logic | Exp08b 검증 (logic-01·02 와 다름) |
| logic-04 | Logic | Exp08b 검증 |

**제외 사유**:
- `logic-01`, `logic-02`: Exp03 부터 "JSON 파싱 불안정" 으로 skip 처리되어 옴 (`run_error_propagation`, `run_cross_validation`, `run_abc_pipeline`, `run_prompt_enhance` 모두 skip_tasks 에 포함). 본 plan 도 동일 정책.
- `synthesis-02`: Exp05a 에서 trial 2,3 `final_answer=None` 실패 이력. Reproducibility 측정 시 outlier 가 너무 많아 Q1 (분산) 측정에 노이즈. 본 plan 의 Q1 신뢰성을 위해 제외.

### Step 1 — `experiments/exp10_reproducibility_cost/__init__.py` 생성

빈 파일.

### Step 2 — `experiments/exp10_reproducibility_cost/tasks.py` 작성

```python
"""Exp10 9 task subset + 채점 함수.

3 condition (gemma_8loop, gemma_1loop, gemini_flash_1call) 비교 실험에서
공통으로 사용할 task ID 와 채점 helper.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# experiments/ 를 import 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from measure import score_answer_v2  # 기존 채점 함수


EXP10_TASK_IDS = (
    # math (4)
    "math-01",
    "math-02",
    "math-03",
    "math-04",
    # synthesis (3) — synthesis-02 제외 (Exp05a final_answer=None 이력)
    "synthesis-01",
    "synthesis-03",
    "synthesis-04",
    # logic (2) — logic-01·02 제외 (JSON 파싱 불안정 이력)
    "logic-03",
    "logic-04",
)


def load_exp10_tasks() -> list[dict]:
    """Exp10 9 task 만 로드. order 보존."""
    tasks_path = Path(__file__).resolve().parent.parent / "tasks" / "taskset.json"
    with open(tasks_path, encoding="utf-8") as f:
        all_tasks = json.load(f)["tasks"]
    by_id = {t["id"]: t for t in all_tasks}
    missing = [tid for tid in EXP10_TASK_IDS if tid not in by_id]
    if missing:
        raise RuntimeError(f"Exp10 tasks missing in taskset.json: {missing}")
    return [by_id[tid] for tid in EXP10_TASK_IDS]


def score_trial(final_answer: str | None, task: dict) -> float:
    """단일 trial 채점. measure.score_answer_v2 로 위임."""
    return score_answer_v2(str(final_answer or ""), task)
```

### Step 3 — 검증 패턴

본 task 의 verification 은 4 가지:
- 9 task 모두 `taskset.json` 에 존재
- 9 task 모두 `expected_answer` + `scoring_keywords` 보유 (이미 위 grep 으로 확인됨)
- `EXP10_TASK_IDS` tuple 길이 == 9
- `load_exp10_tasks()` 결과 length == 9, 순서 보존
- `score_trial` 이 callable

LLM 호출 일체 없음. 정적 검증만.

## Dependencies

- 선행 Task 없음 (`depends_on: []`)
- 외부 패키지: 없음
- import 경로: `measure.score_answer_v2` (기존), `taskset.json` (기존)

## Verification

```bash
# 1. 신규 2 파일 존재
test -f /Users/d9ng/privateProject/gemento/experiments/exp10_reproducibility_cost/__init__.py && \
test -f /Users/d9ng/privateProject/gemento/experiments/exp10_reproducibility_cost/tasks.py && \
echo "OK 2 files exist"

# 2. EXP10_TASK_IDS 9 개 + 모두 taskset.json 에 존재
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.tasks import EXP10_TASK_IDS, load_exp10_tasks
assert len(EXP10_TASK_IDS) == 9, f'expected 9 task ids, got {len(EXP10_TASK_IDS)}'
tasks = load_exp10_tasks()
assert len(tasks) == 9
# 순서 보존
assert tuple(t['id'] for t in tasks) == EXP10_TASK_IDS
print('OK 9 tasks loaded, order preserved')
"

# 3. 9 task 모두 expected_answer + scoring_keywords 보유
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.tasks import load_exp10_tasks
for t in load_exp10_tasks():
    assert t.get('expected_answer'), f\"{t['id']}: no expected_answer\"
    assert t.get('scoring_keywords'), f\"{t['id']}: no scoring_keywords\"
print('OK 9 tasks have expected_answer + scoring_keywords')
"

# 4. score_trial callable + measure.score_answer_v2 와 1:1 위임
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.tasks import score_trial, load_exp10_tasks
tasks = load_exp10_tasks()
math04 = next(t for t in tasks if t['id'] == 'math-04')
score = score_trial(str(math04['expected_answer']), math04)
assert 0.0 <= score <= 1.0, f'score out of range: {score}'
print(f'OK score_trial returns {score} for math-04 expected_answer')
"

# 5. 제외된 task (logic-01·02, synthesis-02) 가 EXP10_TASK_IDS 에 없음
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.tasks import EXP10_TASK_IDS
excluded = {'logic-01', 'logic-02', 'synthesis-02'}
overlap = excluded & set(EXP10_TASK_IDS)
assert not overlap, f'excluded tasks should not be in EXP10_TASK_IDS: {overlap}'
print('OK excluded tasks not in EXP10_TASK_IDS')
"

# 6. taskset.json 변경 없음 (Task 02 범위 검증)
cd /Users/d9ng/privateProject/gemento && git diff HEAD experiments/tasks/taskset.json | wc -l
# 기대: 0
```

## Risks

- **task 정의 변경**: 본 plan 이후 누군가 `taskset.json` 의 task 내용을 수정하면 결과 비교 무의미. plan Constraints 에 "taskset 수정 금지" 명시되어 있지만 외부 작업 시 주의.
- **synthesis-02 제외의 외부 비판**: 외부 평가자가 "왜 이 task 만 빼냐" 질문할 수 있음. report 작성 (task-06) 시 명확히 사유 기록 — Exp05a 에서 final_answer=None 이력으로 분산 측정 노이즈 제거 목적.
- **logic-01·02 제외**: `experiments/exp03_error_propagation/run.py:48` 부터 일관된 정책. 본 plan 도 따름. 외부 비판 시 동일 사유 인용.
- **measure.py 의 score_answer_v2 변경**: 채점 로직이 plan 진행 중 변경되면 결과 비교 깨짐. 본 plan 시작 시점 hash 를 report 에 기록하여 재현 가능하게.
- **EXP10_TASK_IDS 순서 의존성**: tuple 로 정의해 immutable. score 계산은 task_id key 로 이루어지므로 순서 변경에 강건. 단 report.md 출력 순서가 EXP10_TASK_IDS 따름 — 일관성 유지.

## Scope boundary

**Task 02 에서 절대 수정 금지**:

- `experiments/tasks/taskset.json` — 12 task 정의 그대로.
- `experiments/measure.py` — `score_answer_v2` 함수 import 만, 수정 금지.
- `experiments/_external/` — task-01 영역.
- `experiments/exp10_reproducibility_cost/run.py`, `analyze.py`, `INDEX.md` — task-03·04·05 영역.
- `experiments/run_experiment.py` — task-05 영역.
- `experiments/orchestrator.py`, `config.py`, `schema.py`, `system_prompt.py`.
- 다른 expXX/ 디렉토리.

**허용 범위**:

- `experiments/exp10_reproducibility_cost/__init__.py` 신규.
- `experiments/exp10_reproducibility_cost/tasks.py` 신규 — `EXP10_TASK_IDS`, `load_exp10_tasks`, `score_trial` 정의.
