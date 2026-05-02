---
type: plan-task
status: todo
updated_at: 2026-05-03
parent_plan: exp12-extractor-role-pre-search
parallel_group: C
depends_on: [01, 02]
---

# Task 03 — `exp12_extractor_role/run.py` + 2 condition + tattoo_history 저장

## Changed files

- `experiments/exp12_extractor_role/__init__.py` — **신규**
- `experiments/exp12_extractor_role/run.py` — **신규**. 2 condition (baseline_abc + extractor_abc) + cycle-by-cycle tattoo_history 저장 (Stage 2C 결함 fix 적용)
- `experiments/exp12_extractor_role/results/.gitkeep` — **신규**

신규 3.

## Change description

### 배경

task-01 의 EXTRACTOR_PROMPT + task-02 의 orchestrator hook 위에서 Extractor Role 실험 도구. Stage 2C `exp_h4_recheck/run.py` + Exp11 `exp11_mixed_intelligence/run.py` 패턴 그대로.

### Step 1 — 디렉토리 신규

```bash
mkdir -p experiments/exp12_extractor_role/results
touch experiments/exp12_extractor_role/__init__.py
touch experiments/exp12_extractor_role/results/.gitkeep
```

### Step 2 — `experiments/exp12_extractor_role/run.py` 신규

Exp11 `exp11_mixed_intelligence/run.py` 의 `run_baseline_abc` 패턴 + 신규 `run_extractor_abc` (task-02 의 `extractor_pre_stage=True` 호출) 만 추가.

```python
"""Exp12 Extractor Role — Extractor 추가 효과 측정.

H11 후보 가설: Extractor 가 task prompt 의 claims/entities 를 사전 추출하여
A→B→C chain 의 input 에 prefix 주입하면, A 의 부담 감소 + 정확도 향상.
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
    """Stage 2C 결함 fix — cycle-by-cycle 저장 추출."""
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
    """A/B/C 모두 Gemma — Stage 2C abc + Exp11 baseline 와 정합."""
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
            extractor_pre_stage=False,  # ⭐ baseline = Extractor 미주입
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


def run_extractor_abc(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """Extractor (Gemma) → A → B → C — Extractor 가 trial 시작 시 1회 claims/entities 추출."""
    start = time.time()
    final_answer = None; error = None; actual_cycles = 0
    tattoo_history = []
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_extractor_abc_t{trial_idx}",
            objective=task["objective"],
            prompt=task["prompt"],
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            extractor_pre_stage=True,  # ⭐ Extractor 추가
        )
        actual_cycles = len(abc_logs)
        tattoo_history = _extract_tattoo_history(abc_logs, tattoo)
        if not final_answer:
            error = f"extractor_abc: no final_answer after {actual_cycles} cycles"
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
    "extractor_abc": run_extractor_abc,
}


def run_experiment(*, taskset_path, trials_per_condition=DEFAULT_TRIALS,
                   conditions=("baseline_abc", "extractor_abc"),
                   max_cycles=DEFAULT_MAX_CYCLES, out_name=None):
    """Stage 2C / Exp11 의 run_experiment 패턴 그대로.
    
    CONDITION_DISPATCH 만 본 plan 의 baseline_abc / extractor_abc 로 변경.
    Stage 2A healthcheck/abort + Stage 2B FailureLabel + Stage 2A meta v1.0 모두 적용.
    """
    raise NotImplementedError(
        "Step 2 의 run_experiment 본체는 Exp11 exp11_mixed_intelligence/run.py 의 "
        "run_experiment 그대로 패턴 재사용. CONDITION_DISPATCH 만 변경."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Exp12 Extractor Role")
    parser.add_argument("--taskset", default="experiments/tasks/taskset.json")
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--max-cycles", type=int, default=8)
    parser.add_argument("--conditions", nargs="+",
                        default=["baseline_abc", "extractor_abc"])
    parser.add_argument("--out-name", default=None)
    args = parser.parse_args()
    raise NotImplementedError("main 도 Exp11 패턴 그대로 — out_name 별 저장 + condition aggregate stdout")


if __name__ == "__main__":
    raise SystemExit(main())
```

**중요**: `run_experiment` / `main` 의 본체는 Exp11 `exp11_mixed_intelligence/run.py` 의 동일 함수 그대로 재사용. Sonnet 이 Exp11 run.py 를 read 하여 패턴 그대로 적용 + CONDITION_DISPATCH 만 본 plan 의 baseline_abc / extractor_abc 로 변경.

### Step 3 — Stage 2A healthcheck/abort + Stage 2B FailureLabel + Stage 2A meta v1.0 통합

Exp11 의 패턴 그대로 — `run_experiment` 안에서 trial 실행 후:
- `classify_trial_error(result.get('error'))` → fatal 시 abort
- 저장 직전 `check_error_rate(trials, threshold=0.30)` → reject 시 SystemExit(1)
- top-level meta = `build_result_meta(...)` 호출 + 결과 dict 에 unpack

### Step 4 — Extractor 결과 별도 저장 (선택)

Extractor 호출은 task-02 의 orchestrator 안에서 발생 — 단 결과 JSON 에 저장은 본 task 영역. 추가 옵션:
- run.py 가 trial 실행 시 Extractor 응답 별도 capture (orchestrator 의 print 기반)
- 또는 미보존 (분석 시 trial 의 첫 cycle assertions 로 간접 추정)

**Architect 결정**: 미보존 (over-engineering). 분석은 첫 cycle 의 assertion 추가 패턴으로 추론.

## Dependencies

- task-01 (EXTRACTOR_PROMPT)
- task-02 (orchestrator extractor_pre_stage hook)
- 기존 `experiments/run_helpers.py` (Stage 2A) — read-only
- 기존 `experiments/measure.py:score_answer_v3` — read-only

## Verification

```bash
# 1) syntax + import + help
.venv/Scripts/python -m py_compile experiments/exp12_extractor_role/run.py
.venv/Scripts/python -m experiments.exp12_extractor_role.run --help

# 2) condition dispatch
.venv/Scripts/python -c "
from experiments.exp12_extractor_role.run import CONDITION_DISPATCH
assert 'baseline_abc' in CONDITION_DISPATCH
assert 'extractor_abc' in CONDITION_DISPATCH
print('verification 2 ok: 2 condition dispatch')
"

# 3) extractor_abc 가 extractor_pre_stage=True 호출 패턴
.venv/Scripts/python -c "
import inspect
from experiments.exp12_extractor_role.run import run_extractor_abc
src = inspect.getsource(run_extractor_abc)
assert 'extractor_pre_stage=True' in src
print('verification 3 ok: extractor_pre_stage=True 호출')
"

# 4) (사용자 직접) dry-run 1 task × 1 trial × extractor — Step 5
```

## Risks

- **Risk 1 — Stage 2A/2B/Exp11 도구 import 의존**: Sonnet 이 import 체인 구성 시 Exp11 run.py 패턴 정확 따름. 임의 변경 금지
- **Risk 2 — Extractor 결과 미보존**: 분석 시 Extractor 효과 직접 측정 어려움. 단 첫 cycle assertion 패턴 + 정확도 차이로 간접 측정 가능
- **Risk 3 — extractor_abc 의 시간**: Extractor 호출 1회 추가 (~30s) × 75 trial = ~38분 추가. baseline_abc 12h vs extractor_abc 12.6h 정도. 큰 영향 0
- **Risk 4 — Stage 2C run.py 패턴 복사 실패**: Sonnet 이 Stage 2C / Exp11 run.py 를 정확히 read 후 변형. 임의 단순화 금지

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/system_prompt.py` (task-01 영역) — read-only import 만
- `experiments/orchestrator.py` (task-02 영역) — read-only 호출만
- `experiments/measure.py` / `score_answer_v*` — 본 plan 영역 외
- `experiments/run_helpers.py` (Stage 2A) — read-only
- `experiments/schema.py` — 변경 금지
- 모든 기존 `experiments/exp**/run.py` — 변경 금지 (Exp11 패턴 read-only 참조만)
- 결과 JSON
