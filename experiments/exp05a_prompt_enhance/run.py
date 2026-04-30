"""실험 5a: Prompt Enhancement.

A의 프롬프트 강화 후 A-B-C 파이프라인을 재실행한다.
변경점: SYNTHESIZE/VERIFY의 next_directive에서 final_answer 필수 제출 강조.

dispatcher key: `prompt-enhance`
원본 함수: experiments/run_experiment.py:run_prompt_enhance (line 545 in v1)
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
    """A의 프롬프트 강화 후 A-B-C 파이프라인을 재실행한다.

    변경점: SYNTHESIZE/VERIFY의 next_directive에서 final_answer 필수 제출 강조.
    비교군: 실험 4 (동일 태스크, 동일 구조, 프롬프트만 변경).
    통과 기준: synthesis-02 정답률 33%→66%+, 전체 정답률 ≥ 90%, 퇴행 없음.
    """
    from experiment_logger import ExperimentLogger

    logger = ExperimentLogger("exp05a_prompt_enhance")
    tasks = load_tasks()
    skip_tasks = {"logic-01", "logic-02"}
    results = []

    aborted = False
    for task in tasks:
        if aborted:
            break
        if task["id"] in skip_tasks:
            logger._write(f"\n[Prompt Enhance] Task: {task['id']} — SKIPPED")
            continue

        task_results = []
        for trial in range(DEFAULT_REPEAT):
            logger.task_start(task["id"], trial + 1, task["objective"])

            final_tattoo, cycle_logs, final_answer = run_abc_chain(
                task_id=f"{task['id']}_5a_t{trial}",
                objective=task["objective"],
                prompt=task["prompt"],
                constraints=task.get("constraints", []),
                logger=logger,
            )

            # 사이클별 상세 기록
            cycle_details = []
            for cl in cycle_logs:
                detail = {
                    "cycle": cl.cycle,
                    "phase": cl.phase,
                    "a_duration_ms": cl.a_log.duration_ms,
                    "a_error": cl.a_log.error,
                    "b_duration_ms": cl.b_duration_ms,
                    "b_error": cl.b_error,
                    "b_invalid_count": 0,
                    "b_suspect_count": 0,
                    "c_duration_ms": cl.c_duration_ms,
                    "c_error": cl.c_error,
                    "c_converged": None,
                    "phase_transition": cl.phase_transition,
                }
                if cl.b_judgments and "judgments" in cl.b_judgments:
                    detail["b_invalid_count"] = sum(
                        1 for j in cl.b_judgments["judgments"]
                        if j.get("status") == "invalid"
                    )
                    detail["b_suspect_count"] = sum(
                        1 for j in cl.b_judgments["judgments"]
                        if j.get("status") == "suspect"
                    )
                if cl.c_decision:
                    detail["c_converged"] = cl.c_decision.get("converged")
                cycle_details.append(detail)

            task_results.append({
                "trial": trial + 1,
                "total_cycles": len(cycle_logs),
                "final_phase": final_tattoo.phase.value,
                "final_confidence": final_tattoo.confidence,
                "total_assertions": len(final_tattoo.active_assertions),
                "final_answer": str(final_answer) if final_answer else None,
                "phase_transitions": [
                    cl.phase_transition for cl in cycle_logs
                    if cl.phase_transition
                ],
                "c_decisions": [
                    cl.c_decision.get("converged") if cl.c_decision else None
                    for cl in cycle_logs
                ],
                "cycle_details": cycle_details,
            })

            logger.trial_result(
                task["id"], trial + 1,
                final_tattoo.phase == Phase.CONVERGED,
                str(final_answer) if final_answer else None,
                len(cycle_logs),
            )

            err_class = classify_trial_error(task_results[-1].get("error"))
            if is_fatal_error(err_class):
                print(f"[ABORT] task={task['id']} trial={trial} fatal={err_class.value}")
                print("[ABORT] 부분 결과는 보존. 저장 직전 error 비율 검사 진행.")
                aborted = True
                break

        results.append({
            "task_id": task["id"],
            "expected_answer": task.get("expected_answer"),
            "trials": task_results,
        })

    # 요약
    total = sum(len(r["trials"]) for r in results)
    converged = sum(
        1 for r in results for t in r["trials"]
        if t["final_phase"] == "CONVERGED"
    )
    with_answer = sum(
        1 for r in results for t in r["trials"]
        if t["final_answer"] is not None
    )
    logger.summary(total, converged, with_answer)
    logger.close()

    all_trials = [t for r in results for t in r.get("trials", [])]
    ok, rate = check_error_rate(all_trials, threshold=0.30)
    if not ok:
        print(f"[REJECT] error 비율 {rate:.1%} ≥ 30%. 저장 거부 + warning")
        print("[REJECT] 부분 결과는 메모리에 유지 — 사용자가 별도 처리 권고")
        raise SystemExit(1)

    save_result("exp05a_prompt_enhance", {
        "experiment": "prompt_enhance",
        "model": MODEL_NAME,
        "change": "SYNTHESIZE/VERIFY directive에 final_answer 필수 제출 강조",
        "baseline": "exp04_abc_pipeline (정답률 83.3%, synthesis-02 1/3)",
        "results": results,
    })
