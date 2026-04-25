---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: exp08-math-tool-use-calculator-linalg-lp-exp07
parallel_group: D
depends_on: [04]
---

# Task 05 — Measure 분석기 (analyze_tool_use)

## Changed files

- `experiments/measure.py`
  - `analyze_loop_saturation()` 정의부(line 255~) 아래에 `analyze_tool_use()` 신규 함수 추가
  - `ANALYZERS` 딕셔너리(line 362 근처)에 `"tool_use": analyze_tool_use` 항목 추가
  - `generate_markdown_report()`(line 205~) 에 `analysis["experiment"] == "tool_use"` 분기 추가

## Change description

### 1. `analyze_tool_use(data: dict, task_map: dict = None) -> dict`

**입력**: Task 04가 저장한 JSON (`data["experiment"] == "tool_use"`, `data["results_by_condition"]`).

**반환 구조**:
```python
{
    "experiment": "tool_use",
    "arm_summary": {
        "baseline_phase15": {
            "accuracy_v2": float,       # 0~1
            "accuracy_v1": float,
            "total_trials": int,
            "converged": int,
            "avg_actual_cycles": float,
            "total_tool_calls": int,    # always 0 for baseline
            "tool_errors": int,
        },
        "tooluse_phase15": { ... },
    },
    "task_summary": [
        {
            "task_id": "math-04",
            "baseline": {"accuracy_v2": ..., "n": ...},
            "tooluse":  {"accuracy_v2": ..., "n": ...},
            "delta_v2": float,
            "avg_tool_calls_tooluse": float,
        },
        ...
    ],
    "overall_delta_v2": float,     # arm 평균 차이 (tooluse - baseline)
    "tool_usage": {
        "calls_by_function": {"calculator": int, "solve_linear_system": int, "linprog": int},
        "errors_by_function": {"calculator": int, ...},
    },
    "math04_breakthrough": bool,   # tooluse.math-04 >= 0.8 여부
}
```

**구현 주요 스텝**:
1. `data["results_by_condition"]` iterate. arm별·task별로 `trials` 순회.
2. 각 trial의 `final_answer`를 `score_v1()`, `score_v2()`(기존 함수)에 통과 — `task_map`에서 태스크의 `scoring_keywords` 조회.
3. arm별 평균, task별 비교, overall delta 계산.
4. `trial["cycle_details"][*]["tool_calls"]` 순회하여 함수별 호출/에러 집계.
5. math-04 tooluse arm 정답률 ≥ 0.8 → `math04_breakthrough = True`.

**함수 재사용**: 기존 `score_v1`, `score_v2`, `load_taskmap` 등이 `analyze_loop_saturation`에서 이미 쓰이므로 같은 패턴 follow. 기존 함수 본문 수정 금지 — 호출만.

### 2. `ANALYZERS` 등록

```python
ANALYZERS = {
    # ... 기존
    "loop_saturation": analyze_loop_saturation,
    "tool_use": analyze_tool_use,  # ← 추가
}
```

### 3. `generate_markdown_report()` 확장

기존 `loop_saturation` 분기(line 243 근처)와 같은 패턴으로 `tool_use` 분기 추가. 보고서 형식:

```markdown
# 실험 결과: tool_use

> N = {repeat} per (arm × task); arms = baseline_phase15, tooluse_phase15

## Arm Summary

| Arm | Accuracy (v2) | Accuracy (v1) | Trials | Avg Cycles | Tool Calls | Tool Errors |
|-----|---------------|---------------|--------|------------|-----------|-------------|
| baseline_phase15 | X.XX | X.XX | 20 | 7.0 | 0 | 0 |
| tooluse_phase15  | X.XX | X.XX | 20 | 7.2 | NN | M |

**Overall Δ (v2): +X.XX%p** (tooluse − baseline)

## Per-task Accuracy (v2)

| Task | Baseline | Tool-use | Δ | Avg Tool Calls (tooluse) |
|------|---------|----------|---|--------------------------|
| math-01 | ... |
| math-04 | 0.50 | **0.80** | **+0.30** | 1.4 |

## Tool Usage Breakdown

| Function | Calls | Errors | Success rate |
|----------|-------|--------|--------------|
| calculator          | NN | M | X.XX |
| solve_linear_system | NN | M | X.XX |
| linprog             | NN | M | X.XX |

**math-04 breakthrough**: ✅ / ❌  (target: tooluse accuracy ≥ 0.80)
```

### 4. `--markdown --output` 경로 호환

Task 01에서 도입한 `--output` 옵션과 자동 호환 (generate_markdown_report 반환값을 그대로 쓰므로 추가 작업 없음).

## Dependencies

- **Task 04 완료**: `run_tool_use`가 `exp08_tool_use_*.json`을 생성해야 분석 대상 존재.
- **Task 01 완료**: `--output` 옵션이 있으면 보고서를 UTF-8로 파일에 기록 가능.
- 외부 패키지 추가 없음.

## Verification

```bash
# 1. analyze_tool_use 등록
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from measure import ANALYZERS
assert 'tool_use' in ANALYZERS
print('OK ANALYZERS')
"
# 기대: "OK ANALYZERS"

# 2. generate_markdown_report 분기 확인 (실제 실행 없이)
grep -n '"tool_use"\|== "tool_use"' experiments/measure.py
# 기대: generate_markdown_report 및 ANALYZERS 양쪽에 등장

# 3. Fixture 기반 분석 smoke — mock 결과로 분석기 단독 호출
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from measure import analyze_tool_use
mock = {
    'experiment': 'tool_use',
    'model': 'gemma4-e4b',
    'conditions': [{'label':'baseline_phase15','use_tools':False},
                   {'label':'tooluse_phase15','use_tools':True}],
    'results_by_condition': {
        'baseline_phase15': [{'task_id':'math-04','expected_answer':'X=30, Y=30, Z=10, profit=\$2800',
            'trials':[{'final_answer':'X=30 Y=30 Z=10 profit 2800','actual_cycles':7,'total_tool_calls':0,'tool_errors':0,'cycle_details':[]}]}],
        'tooluse_phase15': [{'task_id':'math-04','expected_answer':'X=30, Y=30, Z=10, profit=\$2800',
            'trials':[{'final_answer':'x=30 y=30 z=10 2800','actual_cycles':7,'total_tool_calls':2,'tool_errors':0,
                'cycle_details':[{'cycle':1,'tool_calls':[{'name':'linprog','arguments':{},'result':'ok','error':None}]},
                                 {'cycle':2,'tool_calls':[{'name':'calculator','arguments':{},'result':2800,'error':None}]}]}]}],
    }
}
r = analyze_tool_use(mock, task_map=None)
assert r['experiment'] == 'tool_use'
assert 'arm_summary' in r and 'tool_usage' in r
print('OK analyze_tool_use smoke')
"
# 기대: "OK analyze_tool_use smoke"
```

## Risks

- **score_v1/v2 API 차이**: `score_v2`는 `scoring_keywords` 그룹 매칭이 필요 — `task_map`이 없으면 v2 점수를 0으로 기록하거나 v1만 보고. `analyze_loop_saturation`의 패턴을 그대로 따를 것.
- **tool_calls 필드 부재 trial**: 체크포인트에서 이어받은 기존 실험 데이터에 `cycle_details[*].tool_calls`가 없을 수 있음 — `.get("tool_calls", [])` 폴백.
- **markdown 인코딩**: Task 01 `--output` 경로 사용 시 UTF-8 보장. stdout 경로는 터미널 로캘 따라 — Windows는 `chcp 65001` 설정 필요 (Task 06 핸드오프 문서에 언급).
- **기존 generate_markdown_report 회귀**: 기존 분기 로직은 변경 금지. tool_use 분기는 기존 분기 뒤에 추가.

## Scope boundary

**Task 05에서 절대 수정 금지**:
- `experiments/run_experiment.py` (Task 04 영역)
- `experiments/orchestrator.py`, `experiments/tools/`, `experiments/system_prompt.py`, `experiments/schema.py` (Task 02/03 영역)
- 기존 analyzer 함수(`analyze_loop_saturation`, `analyze_handoff_protocol`, 등) 본문 — 본 Task는 추가만.
- `docs/` (Task 06 영역)

**허용 범위**: `experiments/measure.py`만 수정.
