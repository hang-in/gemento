---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: exp06-h4-recheck-expanded-taskset-pre-exp11
parallel_group: B
depends_on: []
---

# Task 02 — 3 condition 정의 (Solo-1call / Solo-budget / ABC) + run 진입점

## Changed files

- `experiments/exp_h4_recheck/__init__.py` — **신규**
- `experiments/exp_h4_recheck/run.py` — **신규**. 3 condition 의 trial loop + 결과 저장
- `experiments/exp_h4_recheck/results/.gitkeep` — **신규**

신규 3 파일. 기존 코드 수정 0.

## Change description

### 배경

H4 재검증의 ablation 핵심 = 3 condition 분리:
- **Solo-1call**: 단발 호출, loop=1
- **Solo-budget**: 같은 모델 자기 반복, max_cycles=8 (결정 5)
- **ABC**: A→B→C 직렬, max_cycles=8

본 task 는 3 condition 의 정의 + run 진입점만. 실제 실행은 Task 04 (사용자 직접).

### Step 1 — 디렉토리 신규

```bash
mkdir -p experiments/exp_h4_recheck/results
touch experiments/exp_h4_recheck/__init__.py
touch experiments/exp_h4_recheck/results/.gitkeep
```

### Step 2 — `experiments/exp_h4_recheck/run.py` 신규

기존 `experiments/exp10_reproducibility_cost/run.py` 패턴 참조 (3 condition 의 비교 실험). 본 task 의 run.py 는 다음 구조:

```python
"""H4 재검증 — Solo-1call / Solo-budget / ABC 3 condition 비교.

15 task × 3 condition × 5 trial = 225 trial.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments.run_helpers import (  # Stage 2A 의 helper
    classify_trial_error,
    is_fatal_error,
    check_error_rate,
    build_result_meta,
    get_taskset_version,
    normalize_sampling_params,
)
from experiments.config import SAMPLING_PARAMS, MODEL_NAME, API_BASE_URL  # 또는 도구별 import
from experiments.measure import score_answer_v3
from experiments.orchestrator import run_abc_chain  # ABC condition
# Solo 호출은 도구 client 직접 — lmstudio_client.call_model 등

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def run_solo_1call(task: dict, trial_idx: int) -> dict:
    """Solo-1call: 단발 호출, loop=1.

    A 의 SYSTEM_PROMPT 만 사용 (B/C 호출 없음). max_cycles=1.
    """
    # client.call_model(messages=[{"role":"system",...}, {"role":"user", "content": task["prompt"]}])
    # 결과: {"final_answer": str, "raw_response": str, "duration_ms": ..., "error": ..., "cycles": 1}
    raise NotImplementedError("Architect 가 Step 2의 client 호출 패턴 명시 — 기존 exp00_baseline 또는 exp10 의 Solo 호출 참조")


def run_solo_budget(task: dict, trial_idx: int, max_cycles: int = 8) -> dict:
    """Solo-budget: 같은 모델 자기 반복, max_cycles=8.

    한 모델이 자신의 출력을 자신의 입력으로 받음. ABC 의 A→B→C 분기 없이 A 만 반복.
    Tattoo 도 ABC 와 동일 구조 — 단 단일 모델이 propose/critic/judge 모두 수행.
    """
    raise NotImplementedError("Architect 가 Step 2 의 Solo-budget loop 패턴 명시 — Exp06 의 Solo 패턴 참조 (experiments/exp06_solo_budget/run.py)")


def run_abc(task: dict, trial_idx: int, max_cycles: int = 8) -> dict:
    """ABC: A→B→C 직렬, max_cycles=8.

    기존 run_abc_chain 호출. 결과 schema 동일.
    """
    return run_abc_chain(task, max_cycles=max_cycles, trial_idx=trial_idx)


def run_experiment(
    *,
    taskset_path: Path,
    trials_per_condition: int = 5,
    conditions: tuple[str, ...] = ("solo_1call", "solo_budget", "abc"),
    max_cycles: int = 8,
) -> dict:
    """전체 실험 실행 — 사용자 직접 호출 (Task 04)."""
    started = _dt.datetime.now().astimezone().isoformat()

    with open(taskset_path, encoding='utf-8') as f:
        taskset = json.load(f)
    tasks = taskset['tasks']

    runner_map = {
        "solo_1call": lambda t, i: run_solo_1call(t, i),
        "solo_budget": lambda t, i: run_solo_budget(t, i, max_cycles=max_cycles),
        "abc": lambda t, i: run_abc(t, i, max_cycles=max_cycles),
    }

    trials_data = []
    aborted = False
    for cond in conditions:
        if aborted:
            break
        for task in tasks:
            if aborted:
                break
            for trial_idx in range(trials_per_condition):
                result = runner_map[cond](task, trial_idx)
                final = str(result.get("final_answer") or "")
                acc = score_answer_v3(final, task)
                trial = {
                    "condition": cond,
                    "task_id": task["id"],
                    "trial_idx": trial_idx,
                    "final_answer": final[:500],
                    "duration_ms": result.get("duration_ms"),
                    "error": result.get("error"),
                    "cycles": result.get("cycles"),
                    "tattoo_history": result.get("tattoo_history"),  # assertion turnover 분석용
                    "accuracy_v3": acc,
                }
                trials_data.append(trial)

                # Stage 2A healthcheck/abort
                err = classify_trial_error(result.get("error"))
                if is_fatal_error(err):
                    print(f"[ABORT] cond={cond} task={task['id']} trial={trial_idx} fatal={err.value}")
                    aborted = True
                    break

    # 저장 직전 error 비율 검사
    ok, rate = check_error_rate(trials_data, threshold=0.30)
    if not ok:
        print(f"[REJECT] error rate {rate:.1%} ≥ 30%")
        raise SystemExit(1)

    ended = _dt.datetime.now().astimezone().isoformat()

    # Stage 2A meta v1.0
    meta = build_result_meta(
        experiment="exp_h4_recheck",
        model_name=MODEL_NAME,
        model_engine="lm_studio",
        model_endpoint=API_BASE_URL,  # 또는 환경변수
        sampling_params=normalize_sampling_params(SAMPLING_PARAMS),
        scorer_version="v3",
        taskset_version=get_taskset_version(),
        started_at=started,
        ended_at=ended,
    )

    out = {
        **meta,
        "conditions": list(conditions),
        "trials_per_condition": trials_per_condition,
        "max_cycles": max_cycles,
        "trials": trials_data,
    }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="H4 재검증 — Solo-1call / Solo-budget / ABC")
    parser.add_argument("--taskset", default="experiments/tasks/taskset.json")
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--max-cycles", type=int, default=8)
    parser.add_argument("--conditions", nargs="+",
                        default=["solo_1call", "solo_budget", "abc"])
    parser.add_argument("--out-name", default=None)
    args = parser.parse_args()

    out = run_experiment(
        taskset_path=Path(args.taskset),
        trials_per_condition=args.trials,
        conditions=tuple(args.conditions),
        max_cycles=args.max_cycles,
    )

    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = args.out_name or f"exp_h4_recheck_{ts}.json"
    out_path = RESULTS_DIR / name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"  → Result saved: {out_path}")

    # condition aggregate 출력
    from collections import defaultdict
    agg = defaultdict(lambda: {"n": 0, "v3": 0.0})
    for t in out["trials"]:
        agg[t["condition"]]["n"] += 1
        agg[t["condition"]]["v3"] += t.get("accuracy_v3", 0)
    print()
    print("=== condition aggregate (v3) ===")
    for cond in args.conditions:
        if cond in agg:
            stat = agg[cond]
            mean = stat["v3"] / stat["n"] if stat["n"] else 0
            print(f"  {cond:20} n={stat['n']:4} mean_acc={mean:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**중요**: 위 코드의 `run_solo_1call` / `run_solo_budget` 의 client 호출 패턴은 `NotImplementedError`. Developer 가 정찰 후 채워야 함:
- `run_solo_1call`: `experiments/exp00_baseline/run.py` 의 단발 호출 패턴 참조
- `run_solo_budget`: `experiments/exp06_solo_budget/run.py` 의 Solo 반복 패턴 참조

두 정찰 후 stub 채우기 — 각 도구별 client 호출 정확한 시그니처 확인 후 inline.

### Step 3 — Stage 2A healthcheck/abort + meta v1.0 통합

위 코드의 `classify_trial_error` / `is_fatal_error` / `check_error_rate` / `build_result_meta` / `get_taskset_version` / `normalize_sampling_params` 는 모두 Stage 2A 의 helper. Stage 2A 마감 후 import 가능.

본 task (Task 02) 의 코드 작성은 Stage 2A 마감 전에 해도 OK — 단순 syntax 만 검증. 실제 실행 (Task 04) 은 Stage 2A 마감 후.

### Step 4 — sample dry-run (작은 입력)

```bash
.venv/Scripts/python -c "
from experiments.exp_h4_recheck.run import run_experiment
# 작은 입력 — 1 task × 1 trial × 1 condition
# (실제 실행은 client 호출 — 사용자 직접)
"
```

위는 import 검증만. 실제 실행은 Task 04.

## Dependencies

- Stage 2A 의 `experiments/run_helpers.py` 마감 (Stage 2A 의 task-01) — import 의존
- `experiments/orchestrator.py:run_abc_chain` — read-only 호출
- `experiments/measure.py:score_answer_v3` — read-only 호출
- 기존 client (`lmstudio_client.py` 또는 도구별) — read-only 호출
- 패키지: 표준만 (`argparse`, `json`, `datetime`)

## Verification

```bash
# 1) syntax + import path
.venv/Scripts/python -m py_compile experiments/exp_h4_recheck/run.py
echo "verification 1 ok: syntax"

# 2) help 출력
.venv/Scripts/python -m experiments.exp_h4_recheck.run --help
# 기대: --taskset / --trials / --max-cycles / --conditions / --out-name

# 3) 디렉토리 + .gitkeep
ls experiments/exp_h4_recheck/results/.gitkeep
echo "verification 3 ok: 디렉토리 신규"

# 4) NotImplementedError 의 raise 확인 (실제 실행 시 client 호출 stub 미구현 알림)
.venv/Scripts/python -c "
import importlib
m = importlib.import_module('experiments.exp_h4_recheck.run')
assert callable(m.run_solo_1call) and callable(m.run_solo_budget) and callable(m.run_abc)
print('verification 4 ok: 3 condition runner 정의')
"
```

4 명령 모두 정상.

## Risks

- **Risk 1 — Stage 2A 마감 의존**: 본 task 의 helper import 가 Stage 2A 의 `run_helpers.py` 부재 시 실패. 대응: 본 task 가 Stage 2A task-01 직후 진행되도록 순서 조정. 또는 본 task 가 helper 없이 `pass` 형태로 작성 후 Stage 2A 완료 후 통합 — Architect 추천: **Stage 2A task-01 마감 후 본 task 진행**
- **Risk 2 — Solo-budget 의 자기 반복 정확한 정의 모호성**: ABC 의 A 만 N 회 호출하는 패턴인지, A 가 자신의 결과를 입력으로 받는 패턴인지 명세 필요. **Architect 정의**: A 가 자신의 prev cycle Tattoo 를 다음 cycle 의 input 으로 받음. C/B 호출 없음. ABC 의 A 만 반복.
- **Risk 3 — `run_abc_chain` 의 시그니처 차이**: `experiments/orchestrator.py:run_abc_chain` 의 정확한 시그니처가 (task, max_cycles, trial_idx) 와 다를 가능성. 정찰 필수
- **Risk 4 — `tattoo_history` 필드의 schema**: assertion turnover 분석에 필요한 raw Tattoo history 가 결과에 포함되어야 함. 기존 ABC chain 이 어떻게 history 를 반환하는지 정찰. 부재 시 추가 — 단 `experiments/orchestrator.py` 변경 0 (Constraint) 이라 결과만 후처리 추출
- **Risk 5 — config.py 의 변수**: `MODEL_NAME` / `API_BASE_URL` / `SAMPLING_PARAMS` 의 정확한 이름 차이. 정찰 후 import 패턴 조정

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/orchestrator.py` — read-only 호출만
- `experiments/measure.py` — read-only 호출만
- `experiments/schema.py` — read-only
- `experiments/run_helpers.py` — Stage 2A 영역
- 기존 client (`lmstudio_client.py` / `gemini_client.py` 등) — read-only
- 기존 모든 `experiments/exp**/run.py` — read-only (참조만)
- `experiments/tasks/*` — Task 01 영역
- 분석 helper — Task 03 영역
- README / 노트북 — Task 05 영역

## 사용자 호출 시점

- Risk 2 (Solo-budget 정의) 의 Architect 정의가 사용자 의도와 다를 때
- 결정 5 (max_cycles=8 vs 15) 변경 선호 시
- run_abc_chain 의 시그니처가 본 task 코드와 호환 안 될 때
