"""Merge Exp10 v2 main run + math-04 debug rerun + logic-04 flash retry.

Substitution policy:
  1. (gemma_8loop, math-04, all 20 trials) -> replaced by debug rerun
     (use_tools=True, augmented prompt). Disclosed in `_substitutions`.
  2. (gemini_flash_1call, logic-04, error != None) -> replaced by retry
     (timeout=300s). Successful 16 trials kept as-is.

Trial numbers are matched by (condition, task_id, trial). The merged JSON keeps
the original v2 schema and adds a `_substitutions` block for traceability.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from exp10_reproducibility_cost.run import RESULTS_DIR, save_result


DEFAULT_V2 = RESULTS_DIR / "exp10_reproducibility_cost_20260428_175247.json"
DEFAULT_MATH04 = RESULTS_DIR / "exp10_math04_8loop_debug_20260428_205650.json"
# logic-04 retry path is timestamped at runtime; pass --logic04 explicitly.

MATH04_KEY = ("gemma_8loop", "math-04")
LOGIC04_KEY = ("gemini_flash_1call", "logic-04")


def _load(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _trial_key(t: dict) -> tuple[str, str, int]:
    return (t["condition"], t["task_id"], int(t["trial"]))


def merge(
    v2_path: Path,
    math04_path: Path,
    logic04_path: Path | None,
) -> dict:
    v2 = _load(v2_path)
    math04 = _load(math04_path)
    logic04_retry = _load(logic04_path) if logic04_path else None

    v2_trials: list[dict] = list(v2.get("trials", []))
    by_key = {_trial_key(t): i for i, t in enumerate(v2_trials)}

    substitutions: list[dict] = []

    # 1. math-04 gemma_8loop: replace all 20 trials
    math04_trials = list(math04.get("trials", []))
    if len(math04_trials) != 20:
        raise RuntimeError(
            f"math-04 debug rerun expected 20 trials, got {len(math04_trials)}"
        )
    for t in math04_trials:
        if (t["condition"], t["task_id"]) != MATH04_KEY:
            raise RuntimeError(
                f"math-04 debug rerun has off-target trial: {t['condition']}/{t['task_id']}"
            )
        key = _trial_key(t)
        idx = by_key.get(key)
        if idx is None:
            raise RuntimeError(f"v2 has no trial slot for {key}")
        # Preserve provenance: mark substitution
        new_trial = dict(t)
        new_trial["_substituted_from"] = math04_path.name
        v2_trials[idx] = new_trial
        substitutions.append({
            "key": list(key),
            "source": math04_path.name,
            "reason": "use_tools=True debug rerun (augmented prompt) — original 20 trials had use_tools=False misconfiguration",
        })

    # 2. logic-04 gemini_flash retry: replace only the failed trial slots
    retried_count = 0
    if logic04_retry is not None:
        for t in logic04_retry.get("trials", []):
            if (t["condition"], t["task_id"]) != LOGIC04_KEY:
                raise RuntimeError(
                    f"logic-04 retry has off-target trial: {t['condition']}/{t['task_id']}"
                )
            key = _trial_key(t)
            idx = by_key.get(key)
            if idx is None:
                raise RuntimeError(f"v2 has no trial slot for {key}")
            original = v2_trials[idx]
            if original.get("error") is None:
                raise RuntimeError(
                    f"refusing to overwrite a non-failed v2 slot: {key}"
                )
            new_trial = dict(t)
            new_trial["_substituted_from"] = logic04_path.name
            v2_trials[idx] = new_trial
            substitutions.append({
                "key": list(key),
                "source": logic04_path.name,
                "reason": (
                    f"v2 ReadTimeout (~120s) -> retry with timeout="
                    f"{logic04_retry.get('retry_timeout_sec')}s"
                ),
            })
            retried_count += 1

    if len(v2_trials) != 540:
        raise RuntimeError(f"merged trial count drift: {len(v2_trials)} != 540")

    merged = dict(v2)
    merged["trials"] = v2_trials
    merged["_substitutions"] = {
        "math04_source": math04_path.name,
        "logic04_source": logic04_path.name if logic04_path else None,
        "math04_replaced": len(math04_trials),
        "logic04_replaced": retried_count,
        "details": substitutions,
        "merged_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge Exp10 v2 + patches into final result")
    parser.add_argument("--v2", default=str(DEFAULT_V2))
    parser.add_argument("--math04", default=str(DEFAULT_MATH04))
    parser.add_argument(
        "--logic04",
        default=None,
        help="Path to exp10_logic04_flash_retry_*.json (optional; omit to merge math-04 only)",
    )
    parser.add_argument(
        "--out-name",
        default="exp10_v2_final",
        help="save_result name (timestamped automatically)",
    )
    args = parser.parse_args()

    merged = merge(
        Path(args.v2),
        Path(args.math04),
        Path(args.logic04) if args.logic04 else None,
    )
    out_path = save_result(args.out_name, merged)
    subs = merged["_substitutions"]
    print(
        "  -> merge done: "
        f"math04_replaced={subs['math04_replaced']}  "
        f"logic04_replaced={subs['logic04_replaced']}"
    )
    print(f"  -> output: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
