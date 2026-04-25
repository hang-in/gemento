---
type: task
status: abandoned
plan: exp07-loop-saturation
task: 4
parallel_group: B
depends_on: [1, 2, 3]
updated_at: 2026-04-25---

# Task 4: 실험 실행 함수 작성

## Changed files

- `experiments/run_experiment.py` — `run_loop_saturation()` 함수 추가 + CLI 등록

## Change description

2×4 요인 설계를 실행하는 `run_loop_saturation()` 함수를 추가한다.

### 조건 매트릭스

```python
CONDITIONS = [
    {"max_cycles": 8,  "use_phase_prompt": False, "label": "baseline_8"},
    {"max_cycles": 11, "use_phase_prompt": False, "label": "baseline_11"},
    {"max_cycles": 15, "use_phase_prompt": False, "label": "baseline_15"},
    {"max_cycles": 20, "use_phase_prompt": False, "label": "baseline_20"},
    {"max_cycles": 8,  "use_phase_prompt": True,  "label": "phase_8"},
    {"max_cycles": 11, "use_phase_prompt": True,  "label": "phase_11"},
    {"max_cycles": 15, "use_phase_prompt": True,  "label": "phase_15"},
    {"max_cycles": 20, "use_phase_prompt": True,  "label": "phase_20"},
]
```

### 함수 구조

```python
LOOP_SAT_REPEAT = 3  # 288 runs 총량 제어

def run_loop_saturation():
    """실험 7: Loop Saturation + Loop-Phase 프롬프트.
    
    2×4 요인 설계: 프롬프트(baseline/phase) × MAX_CYCLES(8/11/15/20).
    12 태스크 × 3 trials × 8 조건 = 288 runs.
    """
    tasks = load_tasks()
    partial_path = RESULTS_DIR / "partial_loop_saturation.json"
    
    # 체크포인트 로드 (기존 패턴 동일)
    results = {}  # key: condition label → list of task results
    finished = set()  # (label, task_id) 튜플
    # ... checkpoint loading ...
    
    for cond in CONDITIONS:
        label = cond["label"]
        
        for task in tasks:
            if (label, task["id"]) in finished:
                continue
            
            task_results = []
            for trial_idx in range(LOOP_SAT_REPEAT):
                tattoo, abc_logs, final_answer = run_abc_chain(
                    task_id=f"{task['id']}_{label}_t{trial_idx}",
                    objective=task["objective"],
                    prompt=task["prompt"],
                    constraints=task.get("constraints"),
                    max_cycles=cond["max_cycles"],
                    use_phase_prompt=cond["use_phase_prompt"],
                )
                
                task_results.append({
                    "trial": trial_idx + 1,
                    "max_cycles": cond["max_cycles"],
                    "use_phase_prompt": cond["use_phase_prompt"],
                    "actual_cycles": len(abc_logs),
                    "final_phase": tattoo.phase.value,
                    "final_confidence": tattoo.confidence,
                    "total_assertions": len(tattoo.assertions),
                    "final_answer": str(final_answer) if final_answer else None,
                    "cycle_details": [...]  # 기존 handoff_protocol 패턴 동일
                })
            
            results.setdefault(label, []).append({
                "task_id": task["id"],
                "objective": task["objective"],
                "expected_answer": task.get("expected_answer"),
                "trials": task_results,
            })
            
            # 체크포인트 저장
            ...
    
    # 최종 결과 저장
    save_result("exp07_loop_saturation", {
        "experiment": "loop_saturation",
        "model": MODEL_NAME,
        "conditions": CONDITIONS,
        "results_by_condition": results,
    })
```

### 결과 JSON 구조

```json
{
  "experiment": "loop_saturation",
  "model": "gemma4:e4b",
  "conditions": [...],
  "results_by_condition": {
    "baseline_8": [
      {
        "task_id": "math-01",
        "objective": "...",
        "expected_answer": "...",
        "trials": [
          {
            "trial": 1,
            "max_cycles": 8,
            "use_phase_prompt": false,
            "actual_cycles": 7,
            "final_phase": "CONVERGED",
            "final_answer": "...",
            "cycle_details": [...]
          }
        ]
      }
    ],
    "phase_20": [...]
  }
}
```

### CLI 등록

```python
EXPERIMENTS = {
    ...
    "loop-saturation": run_loop_saturation,  # 추가
}
```

### 구현 순서

1. `CONDITIONS` 상수와 `LOOP_SAT_REPEAT = 3` 정의
2. `run_loop_saturation()` 함수 작성 (체크포인트 패턴은 `run_handoff_protocol()` 복사 후 수정)
3. `EXPERIMENTS` 딕셔너리에 `"loop-saturation"` 키 등록
4. CLI docstring 업데이트

### 체크포인트 구조

중단/재시작을 위해 `(condition_label, task_id)` 쌍으로 완료 추적.
`partial_loop_saturation.json`에 현재까지의 `results_by_condition`을 저장.

## Dependencies

- Task 1 (태스크 12개 필요)
- Task 2 (phase prompt 함수 필요)
- Task 3 (run_abc_chain 파라미터 필요)

## Verification

```bash
cd /Users/d9ng/privateProject/gemento/experiments
python -c "
from run_experiment import EXPERIMENTS
assert 'loop-saturation' in EXPERIMENTS, 'loop-saturation not registered'
print('CLI registration OK')
"
```

```bash
cd /Users/d9ng/privateProject/gemento/experiments
python run_experiment.py --help 2>&1 | grep loop-saturation
# 'loop-saturation'이 choices에 나타나야 함
```

## Risks

- 288 runs × ~10분/run = 최대 48시간 소요 → 체크포인트 필수
- 메모리: 12태스크 × 8조건 × 3trial의 cycle_details가 크면 partial JSON이 거대해짐 → cycle_details에서 tattoo_in/out을 생략하고 필수 메트릭만 기록
- 조건 순회 순서: baseline 먼저 → phase 나중 (비교 기준선 확보 우선)

## Scope boundary

수정 금지:
- `run_handoff_protocol()`, `run_solo_budget()` 등 기존 실험 함수
- `experiments/tasks/taskset.json` (Task 1 영역)
- `experiments/system_prompt.py` (Task 2 영역)
- `experiments/orchestrator.py` (Task 3 영역)
- `experiments/measure.py` (Task 5 영역)
