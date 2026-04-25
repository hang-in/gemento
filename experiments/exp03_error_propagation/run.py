"""실험 3: 오류 전파와 자기 교정.

가설 H2를 검증한다 — 결함 주입 시 후속 루프가 오류를 감지·교정할 수 있는가.

dispatcher key: `error-propagation`
원본 함수: experiments/run_experiment.py:run_error_propagation (line 214 in v1)
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
from orchestrator import run_chain, LoopLog


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
    """결함 주입 후 오류 전파를 측정한다."""
    tasks = load_tasks()
    results = []

    # logic 태스크 제외 (JSON 파싱 불안정)
    skip_tasks = {"logic-01", "logic-02"}
    for task in tasks:
        if task["id"] in skip_tasks:
            print(f"\n[Error Propagation] Task: {task['id']} — SKIPPED (unstable JSON)")
            continue
        print(f"\n[Error Propagation] Task: {task['id']}")
        fault_types = task.get("fault_injections", [])
        if not fault_types:
            continue

        for fault in fault_types:
            task_results = []
            for trial in range(DEFAULT_REPEAT):
                # 정상 체인 2루프 실행
                tattoo, pre_logs, _ = run_chain(
                    task_id=f"{task['id']}_fault_{fault['type']}_t{trial}",
                    objective=f"{task['objective']}\n\nProblem:\n{task['prompt']}",
                    max_loops=fault.get("inject_at_loop", 2),
                )

                # 결함 주입
                if fault["type"] == "corrupt_content" and tattoo.active_assertions:
                    target = tattoo.active_assertions[0]
                    target.content = fault.get("corrupted_value", "CORRUPTED: incorrect fact")
                elif fault["type"] == "inflate_confidence" and tattoo.active_assertions:
                    target = tattoo.active_assertions[0]
                    target.confidence = 0.95
                elif fault["type"] == "contradiction":
                    tattoo.add_assertion(
                        content=fault.get("contradicting_assertion", "This contradicts everything."),
                        confidence=0.85,
                        source_loop=tattoo.loop_index,
                    )

                tattoo.finalize_integrity(parent_chain_hash=tattoo.chain_hash)

                # 결함 주입 후 추가 루프 실행 (run_chain과 동일한 로직)
                from orchestrator import run_loop, decide_phase_transition, PHASE_DIRECTIVES
                post_logs: list[LoopLog] = []
                loops_in_current_phase = 0
                current_phase = tattoo.phase
                for i in range(tattoo.loop_index + 1, tattoo.loop_index + 7):
                    tattoo.next_directive = PHASE_DIRECTIVES.get(tattoo.phase, "Continue reasoning.")
                    tattoo, log, _ = run_loop(tattoo, i)
                    post_logs.append(log)

                    if tattoo.phase == current_phase:
                        loops_in_current_phase += 1
                    else:
                        current_phase = tattoo.phase
                        loops_in_current_phase = 1

                    if tattoo.phase == Phase.CONVERGED:
                        break

                    new_phase = decide_phase_transition(tattoo, loops_in_current_phase)
                    if new_phase and new_phase != tattoo.phase:
                        tattoo.phase = new_phase
                        loops_in_current_phase = 0
                        current_phase = new_phase
                        if new_phase == Phase.CONVERGED:
                            break

                task_results.append({
                    "trial": trial + 1,
                    "fault_type": fault["type"],
                    "inject_at_loop": fault.get("inject_at_loop", 2),
                    "post_injection_loops": len(post_logs),
                    "final_confidence": tattoo.confidence,
                    "final_phase": tattoo.phase.value,
                    "confidence_trajectory": [
                        l.tattoo_out["integrity"]["confidence"] for l in post_logs
                    ],
                })

            results.append({
                "task_id": task["id"],
                "fault": fault,
                "trials": task_results,
            })

    save_result("exp03_error_propagation", {"experiment": "error_propagation", "model": MODEL_NAME, "results": results})
