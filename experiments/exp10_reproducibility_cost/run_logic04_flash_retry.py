"""Exp10 targeted retry: gemini_flash_1call on logic-04 timeout failures only.

The Exp10 v2 main run hit 4 ReadTimeouts (~120s default) on
(gemini_flash_1call, logic-04, trials 2/11/17/20).
This runner reads the v2 result JSON, picks only the trials whose error is not
None, and reruns them with a longer timeout.

Trial numbers are preserved so the retried records can be merged back into the
v2 result by (condition, task_id, trial) key.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import MODEL_NAME
from orchestrator import extract_json_from_response
from _external.gemini_client import call_with_meter as gemini_call

from exp10_reproducibility_cost.run import (
    GEMINI_CALL_SLEEP_SEC,
    RESULTS_DIR,
    save_result,
)
from exp10_reproducibility_cost.tasks import load_exp10_tasks, score_trial


CONDITION = "gemini_flash_1call"
TASK_ID = "logic-04"
DEFAULT_TIMEOUT_SEC = 300
DEFAULT_SOURCE = (
    RESULTS_DIR / "exp10_reproducibility_cost_20260428_175247.json"
)


def _trial_with_timeout(task: dict, trial_no: int, timeout_sec: int) -> dict:
    """Mirror of run.trial_gemini_flash but with explicit timeout and trial number."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful reasoning assistant. Think step by step and "
                'provide your final answer as JSON: {"final_answer": "..."}.'
            ),
        },
        {"role": "user", "content": task["prompt"]},
    ]
    meter = gemini_call(
        messages,
        timeout=timeout_sec,
        response_mime_type="application/json",
    )
    final_answer = None
    if meter.raw_response and not meter.error:
        parsed = extract_json_from_response(meter.raw_response)
        if isinstance(parsed, dict):
            final_answer = parsed.get("final_answer")
        if final_answer is None:
            final_answer = meter.raw_response.strip()[:200]
    accuracy = score_trial(final_answer, task)
    time.sleep(GEMINI_CALL_SLEEP_SEC)
    return {
        "trial": trial_no,
        "condition": CONDITION,
        "task_id": TASK_ID,
        "final_answer": str(final_answer) if final_answer else None,
        "accuracy": accuracy,
        "actual_cycles": 1,
        "duration_ms": meter.duration_ms,
        "input_tokens": meter.input_tokens,
        "output_tokens": meter.output_tokens,
        "cost_usd": meter.cost_usd,
        "error": meter.error,
        "_retry": {
            "source_v2_result": str(DEFAULT_SOURCE.name),
            "timeout_sec": timeout_sec,
            "reason": "v2 ReadTimeout retry",
        },
    }


def _select_failed_trial_numbers(source: Path) -> list[int]:
    with open(source, encoding="utf-8") as f:
        data = json.load(f)
    fails = [
        t for t in data.get("trials", [])
        if t.get("condition") == CONDITION
        and t.get("task_id") == TASK_ID
        and t.get("error") is not None
    ]
    nums = sorted(int(t["trial"]) for t in fails)
    return nums


def run(source: Path, timeout_sec: int) -> Path:
    if not source.exists():
        raise FileNotFoundError(f"Source v2 result not found: {source}")

    task = next(t for t in load_exp10_tasks() if t["id"] == TASK_ID)
    trial_nums = _select_failed_trial_numbers(source)
    print(f"  -> retry targets in {source.name}: trials={trial_nums}")
    if not trial_nums:
        print("  -> no failures detected; nothing to retry.")
        return source

    results: list[dict] = []
    for n in trial_nums:
        print(
            f"  [{n}/{trial_nums[-1]}] {CONDITION} | {TASK_ID} | "
            f"trial {n} (timeout={timeout_sec}s)"
        )
        result = _trial_with_timeout(task, n, timeout_sec)
        err = result.get("error")
        print(
            f"    -> error={err!r}  acc={result['accuracy']}  "
            f"final={str(result.get('final_answer'))[:80]!r}"
        )
        results.append(result)

    out = save_result(
        "exp10_logic04_flash_retry",
        {
            "experiment": "exp10_logic04_flash_retry",
            "model": MODEL_NAME,
            "source_v2_result": source.name,
            "retry_timeout_sec": timeout_sec,
            "conditions": [CONDITION],
            "task_ids": [TASK_ID],
            "trials": results,
        },
    )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Exp10 targeted retry of gemini_flash logic-04 timeouts"
    )
    parser.add_argument(
        "--source",
        default=str(DEFAULT_SOURCE),
        help="Path to the v2 result JSON containing the failed trials",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SEC,
        help=f"HTTP timeout in seconds for retried calls (default: {DEFAULT_TIMEOUT_SEC})",
    )
    args = parser.parse_args()
    run(Path(args.source), args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
