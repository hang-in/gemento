"""실험 2: 다단계 루프 품질 누적.

제멘토의 핵심 가설(H1)을 검증한다 — 다단계 루프에서 품질이 누적되는지.

dispatcher key: `multiloop`
원본 함수: experiments/run_experiment.py:run_multiloop (line 154 in v1)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DEFAULT_REPEAT, MODEL_NAME

# experiments-task-07 rev — 자체 디렉토리의 results/ 사용
RESULTS_DIR = Path(__file__).resolve().parent / "results"
from orchestrator import run_chain
from experiments.run_helpers import classify_trial_error, is_fatal_error, check_error_rate


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
    """다단계 루프에서 품질이 누적되는지 검증한다."""
    tasks = load_tasks()
    loop_counts = [1, 2, 4, 8]
    results = []

    aborted = False
    for task in tasks:
        if aborted:
            break
        print(f"\n[Multiloop] Task: {task['id']}")

        for max_loops in loop_counts:
            if aborted:
                break
            task_results = []

            for trial in range(DEFAULT_REPEAT):
                final_tattoo, logs, final_answer = run_chain(
                    task_id=f"{task['id']}_loops{max_loops}_t{trial}",
                    objective=f"{task['objective']}\n\nProblem:\n{task['prompt']}",
                    constraints=task.get("constraints", []),
                    max_loops=max_loops,
                )

                task_results.append({
                    "trial": trial + 1,
                    "max_loops": max_loops,
                    "actual_loops": len(logs),
                    "final_phase": final_tattoo.phase.value,
                    "final_confidence": final_tattoo.confidence,
                    "total_assertions": len(final_tattoo.active_assertions),
                    "final_answer": final_answer,
                    "loop_details": [
                        {
                            "loop": l.loop_index,
                            "phase": l.tattoo_out["state"]["phase"],
                            "assertions": len([
                                a for a in l.tattoo_out["state"]["assertions"]
                                if a["status"] == "active"
                            ]),
                            "confidence": l.tattoo_out["integrity"]["confidence"],
                            "duration_ms": l.duration_ms,
                            "error": l.error,
                        }
                        for l in logs
                    ],
                })
                print(f"  Loops={max_loops}, Trial {trial + 1}: "
                      f"phase={final_tattoo.phase.value}, "
                      f"conf={final_tattoo.confidence:.2f}, "
                      f"assertions={len(final_tattoo.active_assertions)}")

                err_class = classify_trial_error(task_results[-1].get("error"))
                if is_fatal_error(err_class):
                    print(f"[ABORT] task={task['id']} loops={max_loops} trial={trial} fatal={err_class.value}")
                    print("[ABORT] 부분 결과는 보존. 저장 직전 error 비율 검사 진행.")
                    aborted = True
                    break

            results.append({
                "task_id": task["id"],
                "max_loops": max_loops,
                "expected_answer": task.get("expected_answer"),
                "trials": task_results,
            })

    all_trials = [t for r in results for t in r.get("trials", [])]
    ok, rate = check_error_rate(all_trials, threshold=0.30)
    if not ok:
        print(f"[REJECT] error 비율 {rate:.1%} ≥ 30%. 저장 거부 + warning")
        print("[REJECT] 부분 결과는 메모리에 유지 — 사용자가 별도 처리 권고")
        raise SystemExit(1)

    save_result("exp02_multiloop", {"experiment": "multiloop", "model": MODEL_NAME, "results": results})
