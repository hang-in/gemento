"""실험 8b: Tool-Use Refinement.

Exp08의 2개 부작용(calculator ^ 혼동, tool neglect)을 프롬프트·에러
메시지 개선으로 보완한 재측정. 태스크·파라미터는 Exp08과 동일.

dispatcher key: `tool-use-refined`
원본 함수: experiments/run_experiment.py:run_tool_use_refined (line 1126 in v1)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import MODEL_NAME

# experiments-task-07 rev — 자체 디렉토리의 results/ 사용
RESULTS_DIR = Path(__file__).resolve().parent / "results"
from orchestrator import run_abc_chain
from experiments.run_helpers import classify_trial_error, is_fatal_error, check_error_rate


TOOL_USE_REFINED_REPEAT = 5
TOOL_USE_REFINED_MAX_CYCLES = 15
TOOL_USE_REFINED_PHASE_PROMPT = True
TOOL_USE_REFINED_CONDITIONS = [
    {"label": "baseline_refined", "use_tools": False},
    {"label": "tooluse_refined", "use_tools": True},
]
TOOL_USE_REFINED_TASK_IDS = ["math-01", "math-02", "math-03", "math-04"]


def load_tasks() -> list[dict]:
    tasks_path = Path(__file__).resolve().parent.parent / "tasks" / "taskset.json"
    with open(tasks_path) as f:
        return json.load(f)["tasks"]


def save_result(experiment_name: str, result: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{experiment_name}_{timestamp}.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"  → Result saved: {path}")
    return path


def run():
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

    aborted = False
    for cond in TOOL_USE_REFINED_CONDITIONS:
        if aborted:
            break
        label = cond["label"]
        use_tools = cond["use_tools"]

        for task in tasks:
            if aborted:
                break
            if (label, task["id"]) in finished:
                continue

            print(f"\n[Tool Use Refined] arm={label} | task={task['id']}")
            task_results = []

            for trial_idx in range(TOOL_USE_REFINED_REPEAT):
                print(f"  Trial {trial_idx + 1}/{TOOL_USE_REFINED_REPEAT}...")

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

                cycle_details = []
                total_tool_calls = 0
                tool_errors = 0
                for cl in abc_logs:
                    cd = {
                        "cycle": cl.cycle,
                        "phase": cl.phase,
                        "a_error": cl.a_log.error if cl.a_log else None,
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

                err_class = classify_trial_error(task_results[-1].get("error"))
                if is_fatal_error(err_class):
                    print(f"[ABORT] arm={label} task={task['id']} trial={trial_idx} fatal={err_class.value}")
                    print("[ABORT] 부분 결과는 보존. 저장 직전 error 비율 검사 진행.")
                    aborted = True
                    break

            results_by_condition.setdefault(label, []).append({
                "task_id": task["id"],
                "objective": task["objective"],
                "expected_answer": task.get("expected_answer"),
                "trials": task_results,
            })

            with open(partial_path, "w", encoding="utf-8") as f:
                json.dump({
                    "experiment": "tool_use",
                    "model": MODEL_NAME,
                    "conditions": TOOL_USE_REFINED_CONDITIONS,
                    "results_by_condition": results_by_condition,
                }, f, ensure_ascii=False, indent=2)

    all_trials = [t for tl in results_by_condition.values() for r in tl for t in r.get("trials", [])]
    ok, rate = check_error_rate(all_trials, threshold=0.30)
    if not ok:
        print(f"[REJECT] error 비율 {rate:.1%} ≥ 30%. 저장 거부 + warning")
        print("[REJECT] 부분 결과는 메모리에 유지 — 사용자가 별도 처리 권고")
        raise SystemExit(1)

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
