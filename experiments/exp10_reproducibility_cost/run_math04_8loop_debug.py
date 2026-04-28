"""Exp10 targeted rerun: gemma_8loop on math-04 only.

This runner is intentionally separate from run.py so it never resumes from or
overwrites the main 540-trial checkpoint. It is for diagnosing the math-04
failure cluster observed in the Windows v2 rerun.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import MODEL_NAME
from orchestrator import run_abc_chain
from exp10_reproducibility_cost.run import (
    GEMMA_8LOOP_MAX_CYCLES,
    GEMMA_8LOOP_USE_PHASE_PROMPT,
    RESULTS_DIR,
    _serialize_abc_logs,
    _summarize_abc_failure,
    save_result,
    save_partial,
)
from exp10_reproducibility_cost.tasks import load_exp10_tasks
from exp10_reproducibility_cost.tasks import score_trial


TASK_ID = "math-04"
CONDITION = "gemma_8loop"
PARTIAL_PATH = RESULTS_DIR / "partial_exp10_math04_8loop_debug.json"

STRUCTURED_SUFFIX = """

For this diagnostic rerun, make the final answer explicit and machine-readable:
- Solve the linear programming problem by listing the binding constraints or checked vertices.
- The final_answer must include exactly these fields: X, Y, Z, profit.
- Prefer this final_answer shape: {"X": <int>, "Y": <int>, "Z": <int>, "profit": <int>}.
"""


def load_math04_task(augment_prompt: bool = True) -> dict:
    """Load math-04 and optionally add a structured final-answer instruction."""
    task = next(t for t in load_exp10_tasks() if t["id"] == TASK_ID)
    task = copy.deepcopy(task)
    if augment_prompt:
        task["prompt"] = task["prompt"].rstrip() + STRUCTURED_SUFFIX
        task["constraints"] = list(task.get("constraints") or []) + [
            "final_answer must include X, Y, Z, and profit as explicit fields",
        ]
    return task


def load_partial(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("trials", [])


def write_checkpoint(path: Path, trials: list[dict], trials_per_condition: int, augment_prompt: bool) -> None:
    save_partial(path, {
        "experiment": "exp10_math04_8loop_debug",
        "model": MODEL_NAME,
        "trials_per_condition": trials_per_condition,
        "conditions": [CONDITION],
        "task_ids": [TASK_ID],
        "augment_prompt": augment_prompt,
        "trials": trials,
    })


def trial_math04_8loop_with_tools(task: dict, trial_idx: int) -> dict:
    """Run the same ABC condition, but enable tools for the math-04 diagnostic."""
    start = time.time()
    abc_logs = []
    try:
        _tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_8loop_tool_debug_t{trial_idx}",
            objective=task["objective"],
            prompt=task["prompt"],
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=GEMMA_8LOOP_MAX_CYCLES,
            use_phase_prompt=GEMMA_8LOOP_USE_PHASE_PROMPT,
            use_tools=True,
        )
        actual_cycles = len(abc_logs)
        if final_answer:
            error = None
        else:
            error = _summarize_abc_failure(abc_logs) or "final_answer missing after ABC run"
    except Exception as exc:
        final_answer = None
        actual_cycles = 0
        error = str(exc)

    duration_ms = int((time.time() - start) * 1000)
    accuracy = score_trial(final_answer, task)
    return {
        "trial": trial_idx + 1,
        "condition": CONDITION,
        "task_id": task["id"],
        "final_answer": str(final_answer) if final_answer else None,
        "accuracy": accuracy,
        "actual_cycles": actual_cycles,
        "duration_ms": duration_ms,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "error": error,
        "_debug": {
            "abc_logs": _serialize_abc_logs(abc_logs),
            "tools_enabled": True,
        },
    }


def run(trials: int = 20, fresh: bool = False, augment_prompt: bool = True) -> Path:
    """Run gemma_8loop against math-04 only."""
    task = load_math04_task(augment_prompt=augment_prompt)
    all_results: list[dict] = []
    finished_trials: set[int] = set()

    if fresh and PARTIAL_PATH.exists():
        PARTIAL_PATH.unlink()

    if PARTIAL_PATH.exists():
        all_results = load_partial(PARTIAL_PATH)
        finished_trials = {
            int(r["trial"])
            for r in all_results
            if r.get("condition") == CONDITION and r.get("task_id") == TASK_ID
        }
        print(f"  -> Resuming math-04 debug checkpoint: {len(finished_trials)} trials done.")

    for trial_idx in range(trials):
        trial_no = trial_idx + 1
        if trial_no in finished_trials:
            continue

        print(f"  [{trial_no}/{trials}] {CONDITION} | {TASK_ID} | trial {trial_no}")
        result = trial_math04_8loop_with_tools(task, trial_idx)
        result["debug_rerun"] = {
            "name": "exp10_math04_8loop_debug",
            "augment_prompt": augment_prompt,
            "tools_enabled": True,
        }
        all_results.append(result)
        write_checkpoint(PARTIAL_PATH, all_results, trials, augment_prompt)

    final_path = save_result("exp10_math04_8loop_debug", {
        "experiment": "exp10_math04_8loop_debug",
        "model": MODEL_NAME,
        "trials_per_condition": trials,
        "conditions": [CONDITION],
        "task_ids": [TASK_ID],
        "augment_prompt": augment_prompt,
        "trials": all_results,
    })
    if PARTIAL_PATH.exists():
        PARTIAL_PATH.unlink()
        print("  -> Debug checkpoint cleared.")
    return final_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Exp10 targeted math-04 gemma_8loop debug rerun")
    parser.add_argument("--trials", type=int, default=20)
    parser.add_argument("--fresh", action="store_true", help="delete only the math-04 debug checkpoint before running")
    parser.add_argument("--raw-task", action="store_true", help="use the original math-04 prompt without the diagnostic suffix")
    args = parser.parse_args()
    run(trials=args.trials, fresh=args.fresh, augment_prompt=not args.raw_task)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
