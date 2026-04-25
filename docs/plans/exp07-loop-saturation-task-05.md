---
type: task
status: abandoned
plan: exp07-loop-saturation
task: 5
parallel_group: B
depends_on: [4]
updated_at: 2026-04-25---

# Task 5: 분석 함수 작성

## Changed files

- `experiments/measure.py` — `analyze_loop_saturation()` 함수 추가 + ANALYZERS 등록

## Change description

`measure.py`에 실험 7 결과를 분석하는 함수를 추가한다.

### 1. `analyze_loop_saturation(data, task_map)`

입력: Task 4가 생성하는 JSON 구조 (`results_by_condition` 딕셔너리)

출력 구조:

```python
{
    "experiment": "loop_saturation",
    "saturation_curve": {
        "baseline": {
            8: {"accuracy": 0.72, "convergence": 0.85, "avg_cycles": 6.2},
            11: {"accuracy": 0.81, "convergence": 0.92, "avg_cycles": 8.1},
            15: {"accuracy": 0.85, "convergence": 0.95, "avg_cycles": 9.3},
            20: {"accuracy": 0.86, "convergence": 0.95, "avg_cycles": 9.5},
        },
        "phase": {
            8: {...},
            11: {...},
            15: {...},
            20: {...},
        }
    },
    "per_task": {
        "math-01": {
            "baseline_8": {"accuracy": ..., "avg_cycles": ...},
            ...
        },
        ...
    },
    "phase_prompt_delta": {
        8: +0.05,   # phase - baseline 정답률 차이
        11: +0.03,
        15: +0.01,
        20: +0.00,
    },
    "new_task_results": {
        "math-04": {"best_accuracy": ..., "best_condition": ...},
        "logic-04": {...},
        "synthesis-04": {...},
    }
}
```

### 2. Markdown 출력 (`format_markdown` 확장)

포화 곡선 테이블:

```
## Loop Saturation Curve

| MAX_CYCLES | Baseline 정답률 | Phase 정답률 | Delta | Baseline 수렴률 | Phase 수렴률 |
|------------|----------------|-------------|-------|-----------------|-------------|
| 8          | 72.2%          | 77.8%       | +5.6% | 85.0%           | 88.3%       |
| 11         | 81.1%          | 83.3%       | +2.2% | 91.7%           | 93.3%       |
| 15         | 85.0%          | 86.1%       | +1.1% | 95.0%           | 95.0%       |
| 20         | 85.6%          | 86.1%       | +0.5% | 95.0%           | 95.0%       |
```

고난도 태스크 상세:

```
## High-Difficulty Tasks (04)

| Task | Best Accuracy | Best Condition | Avg Cycles |
|------|--------------|---------------|------------|
| math-04 | 66.7% | phase_20 | 14.2 |
| logic-04 | 100% | baseline_15 | 8.7 |
| synthesis-04 | 33.3% | phase_20 | 18.5 |
```

### 3. ANALYZERS 등록

```python
ANALYZERS = {
    ...
    "loop_saturation": analyze_loop_saturation,  # 추가
}
```

### 채점 방식

기존 `score_answer_v2()` 사용. `task_map`에서 `scoring_keywords`를 조회하여 채점.
새 태스크 3종도 `scoring_keywords`가 있으므로 동일 로직으로 처리.

### 구현 순서

1. `analyze_loop_saturation(data, task_map)` 함수 작성
2. `format_markdown()` 내 `loop_saturation` 분기 추가
3. `ANALYZERS` 딕셔너리에 등록

## Dependencies

- Task 4 (결과 JSON 구조 정의)

## Verification

```bash
cd /Users/d9ng/privateProject/gemento/experiments
python -c "
from measure import ANALYZERS
assert 'loop_saturation' in ANALYZERS, 'loop_saturation not in ANALYZERS'
print('Analyzer registration OK')
"
```

```bash
cd /Users/d9ng/privateProject/gemento/experiments
python -c "
from measure import analyze_loop_saturation
import json

# 최소 구조 테스트 (실제 데이터 없이 구조 검증)
mock_data = {
    'experiment': 'loop_saturation',
    'results_by_condition': {
        'baseline_8': [{
            'task_id': 'math-01',
            'expected_answer': '13 apples and 7 oranges',
            'trials': [{
                'trial': 1,
                'max_cycles': 8,
                'use_phase_prompt': False,
                'actual_cycles': 7,
                'final_phase': 'CONVERGED',
                'final_answer': '13 apples and 7 oranges',
            }]
        }]
    }
}

# task_map 구성
with open('tasks/taskset.json') as f:
    ts = json.load(f)
task_map = {t['id']: t for t in ts['tasks']}

result = analyze_loop_saturation(mock_data, task_map)
assert 'saturation_curve' in result, 'missing saturation_curve'
print('Analyzer structure OK')
"
```

## Risks

- 결과 JSON 구조가 Task 4 구현과 불일치할 가능성 → Task 4의 결과 구조를 엄격히 따름
- 3 trial로는 통계적 유의성 부족 → 분석 출력에 "n=3, 해석 주의" 명시

## Scope boundary

수정 금지:
- `score_answer_v2()` 채점 로직
- `analyze_handoff_protocol()`, `analyze_solo_budget()` 등 기존 분석 함수
- `rescore_all()` 함수
- `experiments/run_experiment.py` (Task 4 영역)
- `experiments/orchestrator.py` (Task 3 영역)
