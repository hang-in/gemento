---
type: plan-task
status: todo
updated_at: 2026-05-04
parent_plan: exp13-reducer-role
parallel_group: C
depends_on: [01, 02]
---

# Task 03 — `exp13_reducer_role/run.py` + 2 condition + tattoo_history 저장

## Changed files

- `experiments/exp13_reducer_role/__init__.py` — **신규**
- `experiments/exp13_reducer_role/run.py` — **신규**. 2 condition (baseline_abc + reducer_abc) + cycle-by-cycle tattoo_history (Stage 2C 결함 fix 보존, Exp12 패턴)
- `experiments/exp13_reducer_role/results/.gitkeep` — **신규**

신규 3.

## Change description

### 배경

task-01 의 REDUCER_PROMPT + task-02 의 reducer_post_stage hook 위에서 Reducer Role 실험 도구. **Exp12 `exp12_extractor_role/run.py` 패턴 그대로** — `run_baseline_abc` (extractor_pre_stage=False, reducer_post_stage=False) + `run_reducer_abc` (reducer_post_stage=True) 만 추가.

### Step 1 — 디렉토리 신규

```bash
mkdir -p experiments/exp13_reducer_role/results
touch experiments/exp13_reducer_role/__init__.py
touch experiments/exp13_reducer_role/results/.gitkeep
```

### Step 2 — `experiments/exp13_reducer_role/run.py` 신규

Exp12 `exp12_extractor_role/run.py` 의 패턴 그대로:

```python
"""Exp13 Reducer Role — post-stage 결과 통합 효과 측정.

H12 후보 가설: 신규 Role (Reducer) 가 ABC chain 의 final tattoo + final_answer
를 받아 정리하면 keyword 매칭 정확도 + final answer 명료성 향상.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments.run_helpers import (
    classify_trial_error, is_fatal_error, check_error_rate,
    build_result_meta, get_taskset_version, normalize_sampling_params,
)
from experiments.config import SAMPLING_PARAMS, MODEL_NAME, API_BASE_URL
from experiments.measure import score_answer_v3
from experiments.orchestrator import run_abc_chain


RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_TRIALS = 5
DEFAULT_MAX_CYCLES = 8


def _extract_tattoo_history(abc_logs, fallback_tattoo) -> list:
    """Stage 2C 결함 fix — cycle-by-cycle 저장 추출 (Exp12 패턴 재사용)."""
    history = []
    for log_entry in abc_logs:
        if hasattr(log_entry, "tattoo_snapshot"):
            history.append(log_entry.tattoo_snapshot.to_dict() if hasattr(log_entry.tattoo_snapshot, "to_dict") else log_entry.tattoo_snapshot)
        elif hasattr(log_entry, "tattoo_out"):
            history.append(log_entry.tattoo_out.to_dict() if hasattr(log_entry.tattoo_out, "to_dict") else log_entry.tattoo_out)
        elif isinstance(log_entry, dict) and "tattoo" in log_entry:
            history.append(log_entry["tattoo"])
    if not history and fallback_tattoo:
        history = [fallback_tattoo.to_dict()]
    return history


def run_baseline_abc(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """A/B/C 모두 Gemma — Stage 2C / Exp11 / Exp12 baseline 정합."""
    start = time.time()
    final_answer = None; error = None; actual_cycles = 0
    tattoo_history = []
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_baseline_abc_t{trial_idx}",
            objective=task["objective"],
            prompt=task["prompt"],
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            extractor_pre_stage=False,
            reducer_post_stage=False,  # ⭐ baseline = Reducer 미주입
        )
        actual_cycles = len(abc_logs)
        tattoo_history = _extract_tattoo_history(abc_logs, tattoo)
        if not final_answer:
            error = f"baseline_abc: no final_answer after {actual_cycles} cycles"
    except Exception as e:
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": duration_ms,
        "tattoo_history": tattoo_history if tattoo_history else None,
    }


def run_reducer_abc(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """A→B→C → Reducer (Gemma) post-stage. 동일 모델 Role 분리/추가."""
    start = time.time()
    final_answer = None; error = None; actual_cycles = 0
    tattoo_history = []
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_reducer_abc_t{trial_idx}",
            objective=task["objective"],
            prompt=task["prompt"],
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            extractor_pre_stage=False,
            reducer_post_stage=True,  # ⭐ Reducer 추가
        )
        actual_cycles = len(abc_logs)
        tattoo_history = _extract_tattoo_history(abc_logs, tattoo)
        if not final_answer:
            error = f"reducer_abc: no final_answer after {actual_cycles} cycles"
    except Exception as e:
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": duration_ms,
        "tattoo_history": tattoo_history if tattoo_history else None,
    }


CONDITION_DISPATCH = {
    "baseline_abc": run_baseline_abc,
    "reducer_abc": run_reducer_abc,
}


# run_experiment / main = Exp12 패턴 그대로 (NotImplementedError stub)
# Sonnet 이 Exp12 exp12_extractor_role/run.py 를 read 후 패턴 적용 + CONDITION_DISPATCH 만 변경

def run_experiment(*, taskset_path, trials_per_condition=DEFAULT_TRIALS,
                   conditions=("baseline_abc", "reducer_abc"),
                   max_cycles=DEFAULT_MAX_CYCLES, out_name=None):
    """Stage 2C / Exp11 / Exp12 의 run_experiment 패턴 그대로."""
    raise NotImplementedError(
        "Step 2 의 run_experiment 본체는 Exp12 exp12_extractor_role/run.py 의 "
        "run_experiment 그대로 패턴 재사용. CONDITION_DISPATCH 만 변경."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Exp13 Reducer Role")
    parser.add_argument("--taskset", default="experiments/tasks/taskset.json")
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--max-cycles", type=int, default=8)
    parser.add_argument("--conditions", nargs="+",
                        default=["baseline_abc", "reducer_abc"])
    parser.add_argument("--out-name", default=None)
    args = parser.parse_args()
    raise NotImplementedError("main 도 Exp12 패턴 그대로")


if __name__ == "__main__":
    raise SystemExit(main())
```

**중요**: `run_experiment` / `main` 의 본체는 Exp12 의 동일 함수 그대로 재사용. Sonnet 이 Exp12 run.py 를 read 후 변형.

### Step 3 — Stage 2A/2B/2C 인프라 보존

Exp12 패턴 그대로:
- Stage 2A healthcheck/abort + 결과 JSON meta v1.0
- Stage 2B FailureLabel
- Stage 2C tattoo_history cycle-by-cycle

## Dependencies

- task-01 (REDUCER_PROMPT)
- task-02 (orchestrator reducer_post_stage hook)
- 기존 `experiments/run_helpers.py` (Stage 2A) — read-only
- 기존 `experiments/measure.py:score_answer_v3` — read-only

## Verification

```bash
# 1) syntax + import + help
.venv/Scripts/python -m py_compile experiments/exp13_reducer_role/run.py
.venv/Scripts/python -m experiments.exp13_reducer_role.run --help

# 2) condition dispatch
.venv/Scripts/python -c "
from experiments.exp13_reducer_role.run import CONDITION_DISPATCH
assert 'baseline_abc' in CONDITION_DISPATCH
assert 'reducer_abc' in CONDITION_DISPATCH
print('verification 2 ok: 2 condition dispatch')
"

# 3) reducer_abc 가 reducer_post_stage=True 호출 패턴
.venv/Scripts/python -c "
import inspect
from experiments.exp13_reducer_role.run import run_reducer_abc
src = inspect.getsource(run_reducer_abc)
assert 'reducer_post_stage=True' in src
print('verification 3 ok: reducer_post_stage=True 호출')
"
```

3 명령 모두 정상 + (사용자 직접) dry-run 1 task × 1 trial × reducer 검증 (Step 4).

## Risks

- **Risk 1 — Stage 2A/2B/Exp12 패턴 복사 실패** — Sonnet 이 Exp12 run.py 를 정확히 read 후 변형. 임의 단순화 금지
- **Risk 2 — Reducer 호출 시간 추가** — ~30s/trial × 75 trial = ~38min. baseline 12h vs reducer 12.5h. 영향 작음
- **Risk 3 — Reducer 응답 후 final_answer 길이 변동** — final_answer 길이 차이 측정 (task-05 분석 입력)

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/system_prompt.py` (task-01 영역) — read-only import
- `experiments/orchestrator.py` (task-02 영역) — read-only 호출만
- `experiments/measure.py` / `score_answer_v*` — 본 plan 영역 외
- `experiments/run_helpers.py` (Stage 2A) — read-only
- `experiments/schema.py` — 변경 금지
- 모든 기존 `experiments/exp**/run.py` — 변경 금지 (Exp12 패턴 read-only 참조만)
- 결과 JSON
