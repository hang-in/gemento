"""실험 6: Solo Budget (ABC 시너지 비교군).

단일 E4B 에이전트가 ABC와 동일한 총 compute 예산을 받았을 때의 성능.
A-B-C 역할 분리가 단순히 반복 횟수 증가로 환원 가능한지 판별.

dispatcher key: `solo-budget`
원본 함수: experiments/run_experiment.py:run_solo_budget (line 777 in v1)
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
from schema import Phase
from orchestrator import run_chain
from experiments.run_helpers import classify_trial_error, is_fatal_error, check_error_rate


SOLO_MAX_LOOPS = 21  # ABC 평균 7.2 사이클 × 3 에이전트 ≈ 21 Ollama 호출


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
    """실험 6: 단일 E4B 에이전트가 ABC와 동일한 총 compute 예산을 받았을 때의 성능.

    비교군: exp 5b (handoff-protocol, 9 태스크 × 5 trials, 88.9%, 평균 21.6 Ollama calls)
    목적: A-B-C 역할 분리가 단순히 반복 횟수 증가로 환원 가능한지 판별.
    """
    tasks = load_tasks()
    partial_path = RESULTS_DIR / "partial_solo_budget.json"

    results = []
    finished_task_ids = set()
    if partial_path.exists():
        try:
            with open(partial_path) as f:
                partial_data = json.load(f)
                results = partial_data.get("results", [])
                finished_task_ids = {r["task_id"] for r in results}
                print(f"  → Resuming: {len(finished_task_ids)} tasks already finished.")
        except Exception:
            print("  ⚠ Checkpoint load failed, starting fresh.")

    aborted = False
    for task in tasks:
        if aborted:
            break
        if task["id"] in finished_task_ids:
            continue

        print(f"\n[Solo Budget] Task: {task['id']} — {task['objective']}")
        task_results = []

        for trial_idx in range(DEFAULT_REPEAT):
            print(f"  Trial {trial_idx + 1}/{DEFAULT_REPEAT}...")

            final_tattoo, logs, final_answer = run_chain(
                task_id=f"{task['id']}_solo_t{trial_idx}",
                objective=f"{task['objective']}\n\nProblem:\n{task['prompt']}",
                constraints=task.get("constraints", []),
                max_loops=SOLO_MAX_LOOPS,
            )

            loop_details = []
            for l in logs:
                loop_details.append({
                    "loop": l.loop_index,
                    "phase": l.tattoo_out["state"]["phase"],
                    "assertions": len([
                        a for a in l.tattoo_out["state"]["assertions"]
                        if a["status"] == "active"
                    ]),
                    "confidence": l.tattoo_out["integrity"]["confidence"],
                    "duration_ms": l.duration_ms,
                    "error": l.error,
                })

            task_results.append({
                "trial": trial_idx + 1,
                "max_loops": SOLO_MAX_LOOPS,
                "actual_loops": len(logs),
                "final_phase": final_tattoo.phase.value,
                "final_confidence": final_tattoo.confidence,
                "total_assertions": len(final_tattoo.active_assertions),
                "final_answer": str(final_answer) if final_answer else None,
                "loop_details": loop_details,
            })

            status = "✓" if final_tattoo.phase == Phase.CONVERGED else "✗"
            print(f"    {status} loops={len(logs)} phase={final_tattoo.phase.value} "
                  f"answer={'yes' if final_answer else 'no'}")

            err_class = classify_trial_error(task_results[-1].get("error"))
            if is_fatal_error(err_class):
                print(f"[ABORT] task={task['id']} trial={trial_idx} fatal={err_class.value}")
                print("[ABORT] 부분 결과는 보존. 저장 직전 error 비율 검사 진행.")
                aborted = True
                break

        results.append({
            "task_id": task["id"],
            "objective": task["objective"],
            "expected_answer": task.get("expected_answer"),
            "trials": task_results,
        })

        # 체크포인트 저장
        with open(partial_path, "w") as f:
            json.dump({
                "experiment": "solo_budget",
                "model": MODEL_NAME,
                "max_loops": SOLO_MAX_LOOPS,
                "results": results
            }, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Task {task['id']} saved to checkpoint.")

    all_trials = [t for r in results for t in r.get("trials", [])]
    ok, rate = check_error_rate(all_trials, threshold=0.30)
    if not ok:
        print(f"[REJECT] error 비율 {rate:.1%} ≥ 30%. 저장 거부 + warning")
        print("[REJECT] 부분 결과는 메모리에 유지 — 사용자가 별도 처리 권고")
        raise SystemExit(1)

    save_result("exp06_solo_budget", {
        "experiment": "solo_budget",
        "model": MODEL_NAME,
        "max_loops": SOLO_MAX_LOOPS,
        "baseline_comparison": "exp045_handoff_protocol (5b): 9 tasks × 5 trials, 88.9% accuracy, ~21.6 Ollama calls/trial",
        "results": results
    })

    if partial_path.exists():
        partial_path.unlink()
