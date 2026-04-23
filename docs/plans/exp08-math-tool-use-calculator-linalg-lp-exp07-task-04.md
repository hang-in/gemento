---
type: plan-task
status: todo
updated_at: 2026-04-24
parent_plan: exp08-math-tool-use-calculator-linalg-lp-exp07
parallel_group: C
depends_on: [03]
---

# Task 04 — Exp08 실행 분기 (run_tool_use + tool-use 커맨드)

## Changed files

- `experiments/run_experiment.py`
  - 파일 하단에 `TOOL_USE_REPEAT`, `TOOL_USE_CONDITIONS`, `run_tool_use()` 추가 (line 1006 근처 `EXPERIMENTS = {...}` 앞)
  - `EXPERIMENTS` 딕셔너리(line 994~1006)에 `"tool-use": run_tool_use` 항목 추가

## Change description

### 1. 실험 상수 및 조건 정의

```python
TOOL_USE_REPEAT = 5  # trial per (arm × task)
TOOL_USE_MAX_CYCLES = 15
TOOL_USE_PHASE_PROMPT = True
TOOL_USE_CONDITIONS = [
    {"label": "baseline_phase15", "use_tools": False},
    {"label": "tooluse_phase15", "use_tools": True},
]
TOOL_USE_TASK_IDS = ["math-01", "math-02", "math-03", "math-04"]
# 회귀 감시용으로 logic-04, synthesis-04도 tooluse arm에만 추가 포함하려면
# 아래 리스트로 확장. 이번 v1은 math 집중이므로 비활성.
# TOOL_USE_EXTRA_MONITOR = ["logic-04", "synthesis-04"]
```

**근거**:
- arm별 5 trial × 4 math 태스크 × 2 arm = 40 runs. 서버 1 slot 기준 ~수 시간.
- MAX_CYCLES=15, use_phase_prompt=True는 Exp07에서 가장 안정적인 조건.
- 회귀 감시(logic-04/synthesis-04)는 v1에서는 제외 — 실행 시간 최소화. 별도 실험으로 확장 가능.

### 2. `run_tool_use()` 함수

구조는 `run_loop_saturation()`(line 889~992)를 템플릿으로 재사용.

```python
def run_tool_use():
    """실험 8: Math Tool-Use.

    A(제안자)에게 calculator/solve_linear_system/linprog 도구를 제공하고
    math 태스크의 정답률 향상을 측정한다. B·C는 도구 없음.
    2 arm(baseline/tooluse) × 4 math 태스크 × 5 trial = 40 runs.
    체크포인트 기능(partial_tool_use.json)으로 중단 후 재실행 가능.
    """
    all_tasks = load_tasks()
    tasks = [t for t in all_tasks if t["id"] in TOOL_USE_TASK_IDS]
    assert len(tasks) == len(TOOL_USE_TASK_IDS), f"missing tasks: expected {TOOL_USE_TASK_IDS}"

    partial_path = RESULTS_DIR / "partial_tool_use.json"
    results_by_condition: dict[str, list] = {}
    finished: set[tuple[str, str]] = set()

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

    for cond in TOOL_USE_CONDITIONS:
        label = cond["label"]
        use_tools = cond["use_tools"]

        for task in tasks:
            if (label, task["id"]) in finished:
                continue

            print(f"\n[Tool Use] arm={label} | task={task['id']}")
            task_results = []

            for trial_idx in range(TOOL_USE_REPEAT):
                print(f"  Trial {trial_idx + 1}/{TOOL_USE_REPEAT}...")

                tattoo, abc_logs, final_answer = run_abc_chain(
                    task_id=f"{task['id']}_{label}_t{trial_idx}",
                    objective=task["objective"],
                    prompt=task["prompt"],
                    constraints=task.get("constraints"),
                    termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
                    max_cycles=TOOL_USE_MAX_CYCLES,
                    use_phase_prompt=TOOL_USE_PHASE_PROMPT,
                    use_tools=use_tools,
                )

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
                    # Task 03에서 ABCCycleLog에 tool_calls 필드를 추가했을 때만 집계
                    tc_list = getattr(cl, "tool_calls", []) or []
                    total_tool_calls += len(tc_list)
                    tool_errors += sum(1 for tc in tc_list if tc.get("error"))
                    cd["tool_calls"] = tc_list
                    cycle_details.append(cd)

                task_results.append({
                    "trial": trial_idx + 1,
                    "max_cycles": TOOL_USE_MAX_CYCLES,
                    "use_phase_prompt": TOOL_USE_PHASE_PROMPT,
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

            # checkpoint 저장 (partial)
            with open(partial_path, "w", encoding="utf-8") as f:
                json.dump({
                    "experiment": "tool_use",
                    "model": MODEL_NAME,
                    "conditions": TOOL_USE_CONDITIONS,
                    "results_by_condition": results_by_condition,
                }, f, ensure_ascii=False, indent=2)

    # 최종 저장
    result = {
        "experiment": "tool_use",
        "model": MODEL_NAME,
        "conditions": TOOL_USE_CONDITIONS,
        "task_ids": TOOL_USE_TASK_IDS,
        "repeat": TOOL_USE_REPEAT,
        "results_by_condition": results_by_condition,
    }
    save_result("exp08_tool_use", result)

    # partial 제거
    if partial_path.exists():
        partial_path.unlink()
```

**주의**:
- `run_abc_chain`의 `use_tools` 인자는 Task 03에서 추가됨.
- `ABCCycleLog.tool_calls` 필드도 Task 03에서 추가됨. 없으면 `getattr(..., [])` 폴백.

### 3. EXPERIMENTS 딕셔너리 등록

```python
EXPERIMENTS = {
    # ... 기존 항목
    "loop-saturation": run_loop_saturation,
    "tool-use": run_tool_use,  # ← 추가
}
```

## Dependencies

- **Task 03 완료**: `run_abc_chain`에 `use_tools` 인자, `call_model`에 tools 루프, `ABCCycleLog.tool_calls` 필드 필요.
- 외부 패키지 추가 없음.

## Verification

```bash
# 1. tool-use 커맨드 등록 확인
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from run_experiment import EXPERIMENTS
assert 'tool-use' in EXPERIMENTS
print('OK tool-use registered')
"
# 기대: "OK tool-use registered"

# 2. argparse choices에도 포함되는지 (--help 출력 확인)
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python run_experiment.py --help | grep -o 'tool-use'
# 기대: "tool-use" 출력

# 3. run_tool_use 함수 signature 확인
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from run_experiment import run_tool_use, TOOL_USE_TASK_IDS, TOOL_USE_CONDITIONS, TOOL_USE_REPEAT
assert TOOL_USE_TASK_IDS == ['math-01', 'math-02', 'math-03', 'math-04']
assert {c['label'] for c in TOOL_USE_CONDITIONS} == {'baseline_phase15', 'tooluse_phase15'}
assert TOOL_USE_REPEAT == 5
print('OK constants')
"
# 기대: "OK constants"

# 4. Dry-run (tasks만 필터링, 실제 LLM 호출 없음)
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from run_experiment import load_tasks, TOOL_USE_TASK_IDS
tasks = [t for t in load_tasks() if t['id'] in TOOL_USE_TASK_IDS]
assert len(tasks) == 4, f'got {len(tasks)} tasks'
for t in tasks:
    print(f\"  - {t['id']}: {t['objective'][:40]}\")
print('OK task filtering')
"
# 기대: "math-01..math-04" 4개 + "OK task filtering"
```

## Risks

- **checkpoint 파일명 충돌**: `partial_tool_use.json`은 새 파일명이므로 기존 실험에 영향 없음.
- **오케스트레이터 회귀**: Task 03에서 `call_model` 반환값이 tuple로 바뀌었으므로 기존 `run_loop_saturation` 등 다른 분기가 이미 업데이트되었어야 함 (Task 03 Verification 4번 체크 항목).
- **tasks 개수 불일치**: `TOOL_USE_TASK_IDS`에 오타 있거나 taskset.json에 id가 없으면 assert로 즉시 실패 (의도).
- **실행 시간**: 40 runs × MAX_CYCLES=15 × 평균 cycle 7 ≈ 280 A-B-C cycle. tool 사용 시 tool round까지 포함 → 실제 ~수 시간 예상. 서버 slot=4 활용은 이번 범위 외(직렬 실행).

## Scope boundary

**Task 04에서 절대 수정 금지**:
- `experiments/orchestrator.py` (Task 03 영역)
- `experiments/tools/` (Task 02 영역)
- `experiments/measure.py` (Task 05 영역)
- `experiments/system_prompt.py`, `experiments/schema.py` (Task 03 영역)
- `docs/` (Task 06 영역)

**허용 범위**: `experiments/run_experiment.py`만 수정.
