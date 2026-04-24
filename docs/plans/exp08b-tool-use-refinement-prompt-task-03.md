---
type: plan-task
status: todo
updated_at: 2026-04-24
parent_plan: exp08b-tool-use-refinement-prompt
parallel_group: B
depends_on: [01, 02]
---

# Task 03 — Exp08b 실행 분기 (`tool-use-refined`)

## Changed files

- `experiments/run_experiment.py`
  - 기존 `TOOL_USE_*` 상수 블록(line 992~999) 뒤에 `TOOL_USE_REFINED_*` 상수 추가.
  - 기존 `run_tool_use()` (line 1002~) 뒤에 `run_tool_use_refined()` 함수 신규 추가.
  - `EXPERIMENTS` 딕셔너리(line 1130 근처)에 `"tool-use-refined": run_tool_use_refined` 항목 추가.

## Change description

### Step 1 — 신규 상수 추가

기존 `TOOL_USE_*` 상수 블록 바로 다음에 병행 상수 추가:

```python
# ── Exp08b (tool-use refined) ──
TOOL_USE_REFINED_REPEAT = TOOL_USE_REPEAT
TOOL_USE_REFINED_MAX_CYCLES = TOOL_USE_MAX_CYCLES
TOOL_USE_REFINED_PHASE_PROMPT = TOOL_USE_PHASE_PROMPT
TOOL_USE_REFINED_CONDITIONS = [
    {"label": "baseline_refined", "use_tools": False},
    {"label": "tooluse_refined", "use_tools": True},
]
TOOL_USE_REFINED_TASK_IDS = TOOL_USE_TASK_IDS
```

**근거**: 모든 실행 파라미터를 Exp08과 동일하게 유지 — Task 01/02의 2가지 개선만 차이가 되도록. 상수 재사용으로 drift 방지.

### Step 2 — `run_tool_use_refined()` 함수 추가

기존 `run_tool_use()` 구조를 템플릿으로 복제하되 다음만 변경:
- 함수명: `run_tool_use_refined`
- 체크포인트 파일: `partial_tool_use_refined.json`
- 결과 저장 파일명 접두사: `exp08b_tool_use_refined`
- `experiment` 필드: `"tool_use"` 유지 (analyzer 공유)
- 조건 리스트: `TOOL_USE_REFINED_CONDITIONS`
- arm label: `baseline_refined`, `tooluse_refined`
- 나머지는 동일

**중요**: `experiment: "tool_use"`를 그대로 둬야 `measure.py`의 `ANALYZERS["tool_use"]`가 Exp08b 결과도 분석할 수 있다 (Task 04가 이 경로에 tool_neglect_rate 추가).

대략의 구조:

```python
def run_tool_use_refined():
    """실험 8b: Tool-Use Refinement.

    Exp08의 2개 부작용(calculator ^ 혼동, tool neglect)을 프롬프트·에러
    메시지 개선으로 보완한 재측정. 태스크·파라미터는 Exp08과 동일.
    """
    all_tasks = load_tasks()
    tasks = [t for t in all_tasks if t["id"] in TOOL_USE_REFINED_TASK_IDS]
    assert len(tasks) == len(TOOL_USE_REFINED_TASK_IDS), \
        f"missing tasks: expected {TOOL_USE_REFINED_TASK_IDS}"

    partial_path = RESULTS_DIR / "partial_tool_use_refined.json"
    results_by_condition: dict[str, list] = {}
    finished: set[tuple[str, str]] = set()

    # checkpoint resume 로직 — run_tool_use와 동일 패턴
    if partial_path.exists():
        try:
            with open(partial_path) as f:
                partial_data = json.load(f)
                results_by_condition = partial_data.get("results_by_condition", {})
                for label, task_list in results_by_condition.items():
                    for tr in task_list:
                        finished.add((label, tr["task_id"]))
            print(f"  → Resuming from checkpoint: {len(finished)} (condition, task) pairs done.")
        except Exception:
            print("  ⚠ Checkpoint load failed, starting from scratch.")

    for cond in TOOL_USE_REFINED_CONDITIONS:
        label = cond["label"]
        use_tools = cond["use_tools"]
        for task in tasks:
            if (label, task["id"]) in finished:
                continue
            print(f"\n[Tool Use Refined] arm={label} | task={task['id']}")
            task_results = []
            for trial_idx in range(TOOL_USE_REFINED_REPEAT):
                print(f"  Trial {trial_idx + 1}/{TOOL_USE_REFINED_REPEAT}...")
                # run_abc_chain 호출 — run_tool_use와 동일 시그니처
                tattoo, abc_logs, final_answer = run_abc_chain(
                    task_id=f"{task['id']}_{label}_t{trial_idx}",
                    objective=task["objective"],
                    prompt=task["prompt"],
                    constraints=task.get("constraints"),
                    termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
                    max_cycles=TOOL_USE_REFINED_MAX_CYCLES,
                    use_phase_prompt=TOOL_USE_REFINED_PHASE_PROMPT,
                    use_tools=use_tools,
                )
                # trial 결과 집계 — run_tool_use의 cycle_details/tool_calls 집계 로직 그대로
                cycle_details = []
                total_tool_calls = 0
                tool_errors = 0
                for cl in abc_logs:
                    cd = {
                        "cycle": cl.cycle,
                        "phase": cl.phase,
                        "a_error": cl.a_error,
                        "b_error": cl.b_error,
                        "c_error": cl.c_error,
                    }
                    tc_list = getattr(cl, "tool_calls", []) or []
                    total_tool_calls += len(tc_list)
                    tool_errors += sum(1 for tc in tc_list if tc.get("error"))
                    cd["tool_calls"] = tc_list
                    cycle_details.append(cd)
                task_results.append({
                    "trial": trial_idx + 1,
                    "max_cycles": TOOL_USE_REFINED_MAX_CYCLES,
                    "use_phase_prompt": TOOL_USE_REFINED_PHASE_PROMPT,
                    "use_tools": use_tools,
                    "actual_cycles": len(abc_logs),
                    "final_phase": tattoo.phase.value,
                    "final_confidence": tattoo.confidence,
                    "total_assertions": len(tattoo.assertions),
                    "final_answer": final_answer,
                    "total_tool_calls": total_tool_calls,
                    "tool_errors": tool_errors,
                    "cycle_details": cycle_details,
                })
            results_by_condition.setdefault(label, []).append({
                "task_id": task["id"],
                "objective": task["objective"],
                "expected_answer": task.get("expected_answer"),
                "trials": task_results,
            })
            # checkpoint 저장
            with open(partial_path, "w", encoding="utf-8") as f:
                json.dump({
                    "experiment": "tool_use",
                    "model": MODEL_NAME,
                    "conditions": TOOL_USE_REFINED_CONDITIONS,
                    "results_by_condition": results_by_condition,
                }, f, ensure_ascii=False, indent=2)

    result = {
        "experiment": "tool_use",
        "variant": "refined",
        "model": MODEL_NAME,
        "conditions": TOOL_USE_REFINED_CONDITIONS,
        "task_ids": TOOL_USE_REFINED_TASK_IDS,
        "repeat": TOOL_USE_REFINED_REPEAT,
        "results_by_condition": results_by_condition,
    }
    save_result("exp08b_tool_use_refined", result)

    if partial_path.exists():
        partial_path.unlink()
```

**핵심**:
- `"variant": "refined"` 필드로 Exp08과 구분 가능 (analyzer 호환은 유지).
- `"experiment": "tool_use"`로 `ANALYZERS["tool_use"]` 호환.

### Step 3 — EXPERIMENTS 딕셔너리 등록

기존 `"tool-use": run_tool_use` 아래에 1줄 추가:

```python
EXPERIMENTS = {
    # ... 기존 ...
    "tool-use": run_tool_use,
    "tool-use-refined": run_tool_use_refined,  # ← 추가
}
```

`argparse`의 `choices` 자동 업데이트 (이미 `choices=EXPERIMENTS.keys()` 패턴).

## Dependencies

- **Task 01 완료**: calculator BitXor 힌트가 실제 호출 경로에 반영되어야 실험 효과 유효.
- **Task 02 완료**: SYSTEM_PROMPT 강화가 A 프롬프트에 반영되어야 실험 효과 유효.
- 외부 패키지 추가 없음.

## Verification

```bash
# 1. tool-use-refined 커맨드 등록 확인
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from run_experiment import EXPERIMENTS
assert 'tool-use-refined' in EXPERIMENTS and 'tool-use' in EXPERIMENTS
print('OK both registered')
"
# 기대: "OK both registered"

# 2. argparse choices에 포함
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python run_experiment.py --help 2>&1 | grep -o 'tool-use-refined'
# 기대: "tool-use-refined"

# 3. run_tool_use_refined 함수 signature와 상수
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from run_experiment import (
    run_tool_use_refined,
    TOOL_USE_REFINED_TASK_IDS,
    TOOL_USE_REFINED_CONDITIONS,
    TOOL_USE_REFINED_REPEAT,
)
assert TOOL_USE_REFINED_TASK_IDS == ['math-01', 'math-02', 'math-03', 'math-04']
assert {c['label'] for c in TOOL_USE_REFINED_CONDITIONS} == {'baseline_refined', 'tooluse_refined'}
assert TOOL_USE_REFINED_REPEAT == 5
print('OK constants')
"
# 기대: "OK constants"

# 4. 기존 tool-use 함수 회귀 없음
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from run_experiment import run_tool_use, TOOL_USE_TASK_IDS, TOOL_USE_CONDITIONS
assert TOOL_USE_TASK_IDS == ['math-01', 'math-02', 'math-03', 'math-04']
assert {c['label'] for c in TOOL_USE_CONDITIONS} == {'baseline_phase15', 'tooluse_phase15'}
print('OK run_tool_use intact')
"
# 기대: "OK run_tool_use intact"

# 5. 전체 import 회귀 없음
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
import run_experiment, orchestrator, measure, schema, system_prompt
print('all imports OK')
"
# 기대: "all imports OK"
```

## Risks

- **partial 파일명 충돌**: `partial_tool_use_refined.json`은 신규이므로 기존 실험에 영향 없음. 단 동일 파일명이 실수로 재사용되지 않도록 Task 04의 분석기와 이름 일치 확인.
- **experiment 필드 값 결정**: `"tool_use"` 그대로 두면 analyzer 공유. `"tool_use_refined"`로 별도 두면 분석기 추가 필요 → 운영 복잡도 증가. 본 Task는 **공유 채택** — `variant` 필드로 구분.
- **코드 중복**: `run_tool_use`와 `run_tool_use_refined`의 본문이 90% 유사. 공통 함수 추출하는 리팩토링은 회귀 위험이 크므로 **이번 Task에서는 금지**. 필요 시 Exp08c 이후에 별도 리팩토링 Task로 처리.
- **실행 시간**: 40 runs × 평균 7 cycle ≈ 수 시간. Exp08과 동일 예상.

## Scope boundary

**Task 03에서 절대 수정 금지**:
- `experiments/tools/` 내부 (Task 01 영역)
- `experiments/system_prompt.py` (Task 02 영역)
- `experiments/measure.py` (Task 04 영역)
- `experiments/orchestrator.py` — 본 Task는 실행 래퍼만.
- 기존 `run_tool_use()` 본문 — 새 함수는 **복제**만, 원본은 절대 수정 금지.
- 기존 `TOOL_USE_*` 상수 값 — 재사용은 OK, 수정 금지.

**허용 범위**: `experiments/run_experiment.py`에 상수 5개 + 함수 1개 + 딕셔너리 1줄 추가.
