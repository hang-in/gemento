---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: exp08b-tool-use-refinement-prompt
parallel_group: B
depends_on: [03]
---

# Task 04 — Measure에 `tool_neglect_rate` 추가

## Changed files

- `experiments/measure.py`
  - `analyze_tool_use()` 함수 (line 408~): tool 주입 arm의 neglect 비율 집계 로직 추가, 반환 dict에 `tool_neglect_rate` 필드 포함.
  - `generate_markdown_report()` 내 `tool_use` 분기 (line 253 근처): 새 메트릭 1행 출력 추가.

## Change description

### Step 1 — `analyze_tool_use()`에 tool_neglect_rate 계산 추가

기존 `analyze_tool_use()`는 arm_summary, task_summary, tool_usage를 반환한다. 이 반환 dict에 새 필드 추가:

```python
# tool_neglect_rate 계산 (tool 주입 arm에서 total_tool_calls=0 AND answer empty/None)
tool_arm_label = None
for cond in data.get("conditions", []):
    if cond.get("use_tools"):
        tool_arm_label = cond["label"]
        break

neglect_count = 0
tool_arm_total = 0
if tool_arm_label and tool_arm_label in data.get("results_by_condition", {}):
    for task_block in data["results_by_condition"][tool_arm_label]:
        for trial in task_block.get("trials", []):
            tool_arm_total += 1
            tc = trial.get("total_tool_calls", 0)
            ans = trial.get("final_answer")
            ans_empty = (ans is None) or (isinstance(ans, str) and ans.strip() == "")
            if tc == 0 and ans_empty:
                neglect_count += 1

tool_neglect_rate = (neglect_count / tool_arm_total) if tool_arm_total > 0 else 0.0

# 반환 dict에 필드 추가
result["tool_neglect_rate"] = tool_neglect_rate
result["tool_neglect_count"] = neglect_count
result["tool_arm_total_trials"] = tool_arm_total
```

**배치 위치**: `analyze_tool_use` 함수 내, 최종 return 직전. 기존 arm_summary / task_summary / tool_usage / math04_breakthrough 집계 이후.

**근거**:
- 정의가 "tool 주입 arm에서 tool 미사용 + 실패" 이어야 함. 단순 "tool 미호출"만으로는 "모델이 암산으로 성공한 경우"도 포함되어 과대집계.
- `baseline` arm은 분모에서 제외 — 도구가 없는 환경의 tool_calls=0은 자명.

### Step 2 — `generate_markdown_report()`에 1행 추가

기존 `tool_use` 분기 내 Arm Summary 표 바로 아래에 다음 라인 추가:

```python
if analysis["experiment"] == "tool_use":
    # ... 기존 Arm Summary, Overall Δ, Per-task, Tool Usage 섹션들 ...
    # tool_neglect_rate 섹션 삽입 위치:
    neglect_rate = analysis.get("tool_neglect_rate", 0.0)
    neglect_count = analysis.get("tool_neglect_count", 0)
    neglect_total = analysis.get("tool_arm_total_trials", 0)
    lines.append(f"**Tool Neglect Rate (tool arm)**: {neglect_rate:.2%} "
                 f"({neglect_count}/{neglect_total} trials — tool 주입됐으나 호출 0회이면서 final_answer 부재)")
    lines.append("")
```

**배치 위치**: 기존 "Overall Δ (v2)" 라인 아래, 또는 Per-task Accuracy 표 위. 기존 구조를 깨지 않도록 한 줄만 삽입.

### Step 3 — `math04_breakthrough` 등 기존 필드 유지

기존 반환 필드(arm_summary, task_summary, overall_delta_v2, tool_usage, math04_breakthrough)는 모두 그대로. 새 3개 필드만 **추가**.

## Dependencies

- **Task 03 완료**: Exp08b 결과 JSON이 생성되어야 새 메트릭을 실제 데이터로 검증 가능. 단 본 Task 자체의 단위 동작은 mock 데이터로 검증 가능 (실행 순서상 Task 04 먼저 코드 변경 → Gemini가 Exp08b 실행 → 분석기가 호출되는 흐름).
- 외부 패키지 추가 없음.

## Verification

```bash
# 1. analyze_tool_use 반환 dict에 tool_neglect_rate 필드 존재 — mock 데이터로 검증
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from measure import analyze_tool_use
mock = {
    'experiment': 'tool_use',
    'model': 'gemma4-e4b',
    'conditions': [
        {'label':'baseline_refined','use_tools':False},
        {'label':'tooluse_refined','use_tools':True},
    ],
    'results_by_condition': {
        'baseline_refined': [{'task_id':'math-04','expected_answer':'X=31','trials':[
            {'final_answer':None,'actual_cycles':10,'total_tool_calls':0,'tool_errors':0,'cycle_details':[]},
        ]}],
        'tooluse_refined': [{'task_id':'math-04','expected_answer':'X=31','trials':[
            {'final_answer':'X=31 Y=10 Z=37 profit 3060','actual_cycles':7,'total_tool_calls':1,'tool_errors':0,'cycle_details':[]},
            {'final_answer':None,'actual_cycles':10,'total_tool_calls':0,'tool_errors':0,'cycle_details':[]},
        ]}],
    },
}
r = analyze_tool_use(mock, task_map=None)
assert 'tool_neglect_rate' in r
assert r['tool_arm_total_trials'] == 2
assert r['tool_neglect_count'] == 1
assert abs(r['tool_neglect_rate'] - 0.5) < 1e-6
print(f'OK tool_neglect_rate={r[\"tool_neglect_rate\"]:.2f}')
"
# 기대: "OK tool_neglect_rate=0.50"

# 2. tool 주입 arm이 없는 실험에서는 neglect_rate=0
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from measure import analyze_tool_use
mock = {
    'experiment': 'tool_use',
    'conditions': [{'label':'baseline','use_tools':False}],
    'results_by_condition': {'baseline': [{'task_id':'math-01','expected_answer':'','trials':[
        {'final_answer':'foo','actual_cycles':5,'total_tool_calls':0,'tool_errors':0,'cycle_details':[]},
    ]}]},
}
r = analyze_tool_use(mock)
assert r['tool_neglect_rate'] == 0.0
assert r['tool_arm_total_trials'] == 0
print('OK no-tool-arm edge case')
"
# 기대: "OK no-tool-arm edge case"

# 3. generate_markdown_report 출력에 새 라인 포함
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from measure import analyze_tool_use, generate_markdown_report
mock = {
    'experiment': 'tool_use',
    'conditions': [
        {'label':'baseline_refined','use_tools':False},
        {'label':'tooluse_refined','use_tools':True},
    ],
    'results_by_condition': {
        'baseline_refined': [{'task_id':'math-04','expected_answer':'','trials':[
            {'final_answer':'foo','actual_cycles':7,'total_tool_calls':0,'tool_errors':0,'cycle_details':[]},
        ]}],
        'tooluse_refined': [{'task_id':'math-04','expected_answer':'','trials':[
            {'final_answer':None,'actual_cycles':10,'total_tool_calls':0,'tool_errors':0,'cycle_details':[]},
        ]}],
    },
}
r = analyze_tool_use(mock)
md = generate_markdown_report(r)
assert 'Tool Neglect Rate' in md
print('OK markdown contains Tool Neglect Rate')
"
# 기대: "OK markdown contains Tool Neglect Rate"

# 4. Exp08 기존 결과 파일로 회귀 없음 (tool_neglect_rate 필드 추가 후에도 분석 가능)
cd /Users/d9ng/privateProject/gemento && .venv/bin/python experiments/measure.py \
  "experiments/results/exp08_tool_use_20260424_125350.json" --markdown 2>&1 | grep -c "Tool Neglect Rate"
# 기대: 1 (Exp08 결과도 새 필드 표시 — 회귀 없음)
```

## Risks

- **arm label 하드코딩 회피**: 위 구현은 `conditions` 리스트에서 `use_tools=True`인 항목을 찾아 label을 추출하므로, Exp08(`tooluse_phase15`)와 Exp08b(`tooluse_refined`) 양쪽 모두 정상 작동. 라벨 문자열 변경에 강건.
- **빈 리스트 / None 필드**: `results_by_condition`에 해당 arm이 없거나 `trials`가 비어 있을 때 ZeroDivisionError 회피 — `if tool_arm_total > 0` 체크 필수.
- **final_answer 타입 다양성**: Exp04에서 dict 타입 `final_answer`도 있었음 (`{'production_plan': {...}}` 형식). 본 Task는 "None 또는 빈 문자열"만 neglect로 판정. dict는 정답 판정에서 별개로 처리되므로 여기서 다루지 않음.
- **graph 영향**: `generate_markdown_report`, `analyze_tool_use`는 code-review-graph에서 test gap으로 이미 보고됨. 본 Task로 해당 함수 본문이 수정되므로 단위 테스트로 커버 (위 Verification).

## Scope boundary

**Task 04에서 절대 수정 금지**:
- `experiments/tools/`, `experiments/system_prompt.py`, `experiments/orchestrator.py`, `experiments/run_experiment.py`
- `experiments/measure.py`의 다른 analyzer 함수 본문 (`analyze_baseline`, `analyze_loop_saturation`, `analyze_handoff_protocol` 등) — 터치 금지.
- `score_v1`, `score_v2`, `load_taskmap` 등 기존 helper — 호출만, 수정 금지.

**허용 범위**: `experiments/measure.py`의 `analyze_tool_use()` 함수 내부(return 전) + `generate_markdown_report()` 내 `tool_use` 분기 내부 1행 추가.
