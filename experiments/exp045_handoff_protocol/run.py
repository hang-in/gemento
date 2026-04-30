"""실험 4.5: A-B-C 직렬 파이프라인 + Handoff Protocol 메트릭 측정.

체크포인트 기능 포함: 중간 실패 시 이어서 시작 가능.

dispatcher key: `handoff-protocol`
원본 함수: experiments/run_experiment.py:run_handoff_protocol (line 684 in v1)
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
from orchestrator import run_abc_chain
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
    """실험 4.5: A-B-C 직렬 파이프라인 + Handoff Protocol 메트릭 측정.

    체크포인트 기능 포함: 중간 실패 시 이어서 시작 가능.
    """
    tasks = load_tasks()
    partial_path = RESULTS_DIR / "partial_handoff_protocol.json"

    # 이어하기 시도
    results = []
    finished_task_ids = set()
    if partial_path.exists():
        try:
            with open(partial_path) as f:
                partial_data = json.load(f)
                results = partial_data.get("results", [])
                finished_task_ids = {r["task_id"] for r in results}
                print(f"  → Resuming from checkpoint: {len(finished_task_ids)} tasks already finished.")
        except Exception:
            print("  ⚠ Failed to load checkpoint, starting from scratch.")

    aborted = False
    for task in tasks:
        if aborted:
            break
        if task["id"] in finished_task_ids:
            continue

        print(f"\n[Handoff Protocol] Task: {task['id']} — {task['objective']}")
        task_results = []

        for trial_idx in range(DEFAULT_REPEAT):
            print(f"  Trial {trial_idx + 1}/{DEFAULT_REPEAT}...")

            tattoo, abc_logs, final_answer = run_abc_chain(
                task_id=task["id"],
                objective=task["objective"],
                prompt=task["prompt"],
                constraints=task.get("constraints"),
                termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            )

            cycle_details = []
            for cl in abc_logs:
                detail = {
                    "cycle": cl.cycle,
                    "phase": cl.phase,
                    "tattoo_in": cl.a_log.tattoo_in,
                    "tattoo_out": cl.a_log.tattoo_out,
                    "b_handoff": cl.b_judgments.get("handoff_b2c") if cl.b_judgments else None,
                    "c_reject": cl.c_decision.get("reject_memo") if cl.c_decision else None,
                }
                cycle_details.append(detail)

            task_results.append({
                "trial": trial_idx + 1,
                "final_answer": str(final_answer) if final_answer else None,
                "total_cycles": len(abc_logs),
                "final_phase": tattoo.phase.value,
                "total_assertions": len(tattoo.assertions),
                "cycle_details": cycle_details,
            })

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

        # 태스크 완료 시마다 중간 저장
        with open(partial_path, "w") as f:
            json.dump({
                "experiment": "handoff_protocol",
                "model": MODEL_NAME,
                "results": results
            }, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Task {task['id']} saved to checkpoint.")

    all_trials = [t for r in results for t in r.get("trials", [])]
    ok, rate = check_error_rate(all_trials, threshold=0.30)
    if not ok:
        print(f"[REJECT] error 비율 {rate:.1%} ≥ 30%. 저장 거부 + warning")
        print("[REJECT] 부분 결과는 메모리에 유지 — 사용자가 별도 처리 권고")
        raise SystemExit(1)

    # 최종 결과 저장
    final_path = save_result("exp045_handoff_protocol", {
        "experiment": "handoff_protocol",
        "model": MODEL_NAME,
        "results": results
    })

    # 완료 후 체크포인트 파일 삭제 (깔끔하게 정리)
    if partial_path.exists():
        partial_path.unlink()
        print(f"  → Checkpoint cleared.")
