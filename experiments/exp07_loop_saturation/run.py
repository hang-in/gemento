"""실험 7: Loop Saturation + Loop-Phase 프롬프트.

2×4 요인 설계: 프롬프트(baseline/phase) × MAX_CYCLES(8/11/15/20).
12 태스크 × 3 trials × 8 조건 = 288 runs.

dispatcher key: `loop-saturation`
원본 함수: experiments/run_experiment.py:run_loop_saturation (line 889 in v1)
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


LOOP_SAT_REPEAT = 3

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
    """실험 7: Loop Saturation + Loop-Phase 프롬프트.

    2×4 요인 설계: 프롬프트(baseline/phase) × MAX_CYCLES(8/11/15/20).
    12 태스크 × 3 trials × 8 조건 = 288 runs.
    체크포인트 기능 포함: 중단 후 재실행 시 자동으로 이어서 시작.
    """
    tasks = load_tasks()
    partial_path = RESULTS_DIR / "partial_loop_saturation.json"

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
    for cond in CONDITIONS:
        if aborted:
            break
        label = cond["label"]

        for task in tasks:
            if aborted:
                break
            if (label, task["id"]) in finished:
                continue

            print(f"\n[Loop Saturation] Condition={label} | Task={task['id']}")
            task_results = []

            for trial_idx in range(LOOP_SAT_REPEAT):
                print(f"  Trial {trial_idx + 1}/{LOOP_SAT_REPEAT}...")

                tattoo, abc_logs, final_answer = run_abc_chain(
                    task_id=f"{task['id']}_{label}_t{trial_idx}",
                    objective=task["objective"],
                    prompt=task["prompt"],
                    constraints=task.get("constraints"),
                    termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
                    max_cycles=cond["max_cycles"],
                    use_phase_prompt=cond["use_phase_prompt"],
                )

                cycle_details = []
                for cl in abc_logs:
                    cycle_details.append({
                        "cycle": cl.cycle,
                        "phase": cl.phase,
                        "phase_transition": cl.phase_transition,
                        "b_error": cl.b_error,
                        "c_error": cl.c_error,
                    })

                task_results.append({
                    "trial": trial_idx + 1,
                    "max_cycles": cond["max_cycles"],
                    "use_phase_prompt": cond["use_phase_prompt"],
                    "actual_cycles": len(abc_logs),
                    "final_phase": tattoo.phase.value,
                    "final_confidence": tattoo.confidence,
                    "total_assertions": len(tattoo.assertions),
                    "final_answer": str(final_answer) if final_answer else None,
                    "cycle_details": cycle_details,
                })

                status = "✓" if tattoo.phase.value == "CONVERGED" else "✗"
                print(f"    {status} cycles={len(abc_logs)} phase={tattoo.phase.value} "
                      f"answer={'yes' if final_answer else 'no'}")

                err_class = classify_trial_error(task_results[-1].get("error"))
                if is_fatal_error(err_class):
                    print(f"[ABORT] cond={label} task={task['id']} trial={trial_idx} fatal={err_class.value}")
                    print("[ABORT] 부분 결과는 보존. 저장 직전 error 비율 검사 진행.")
                    aborted = True
                    break

            results_by_condition.setdefault(label, []).append({
                "task_id": task["id"],
                "objective": task["objective"],
                "expected_answer": task.get("expected_answer"),
                "trials": task_results,
            })

            # 태스크 완료 시마다 체크포인트 저장
            with open(partial_path, "w") as f:
                json.dump({
                    "experiment": "loop_saturation",
                    "model": MODEL_NAME,
                    "conditions": CONDITIONS,
                    "results_by_condition": results_by_condition,
                }, f, indent=2, ensure_ascii=False)
            print(f"  ✓ Saved checkpoint: {label}/{task['id']}")

    all_trials = [t for tl in results_by_condition.values() for r in tl for t in r.get("trials", [])]
    ok, rate = check_error_rate(all_trials, threshold=0.30)
    if not ok:
        print(f"[REJECT] error 비율 {rate:.1%} ≥ 30%. 저장 거부 + warning")
        print("[REJECT] 부분 결과는 메모리에 유지 — 사용자가 별도 처리 권고")
        raise SystemExit(1)

    save_result("exp07_loop_saturation", {
        "experiment": "loop_saturation",
        "model": MODEL_NAME,
        "conditions": CONDITIONS,
        "results_by_condition": results_by_condition,
    })

    if partial_path.exists():
        partial_path.unlink()
        print("  → Checkpoint cleared.")
