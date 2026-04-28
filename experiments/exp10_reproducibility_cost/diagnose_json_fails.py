"""v2 final 의 ABC JSON parse 4 fail 진단.

각 fail trial 의 마지막 cycle 의 a_raw/b_raw/c_raw 중 error 가 발생한 항목을
분석하여 원인을 분류한다.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from exp10_reproducibility_cost.run import RESULTS_DIR


DEFAULT_INPUT = RESULTS_DIR / "exp10_v2_final_20260429_033922.json"

TRUNCATE_TAIL = re.compile(r"\.\.\. \(truncated, original_len=(\d+)\)\s*$")


def classify(raw: str) -> dict:
    """Raw 를 분류. 반환 키: kind, original_len, has_open_fence, has_close_fence,
    brace_open, brace_close, tail50."""
    if not raw:
        return {"kind": "empty"}
    m = TRUNCATE_TAIL.search(raw)
    truncated = bool(m)
    original_len = int(m.group(1)) if m else len(raw)
    body = raw[: m.start()] if truncated else raw
    has_open = bool(re.search(r"```(?:json)?", body, re.IGNORECASE))
    has_close = False
    if has_open:
        first = re.search(r"```(?:json)?", body, re.IGNORECASE)
        rest = body[first.end():] if first else ""
        has_close = "```" in rest
    brace_open = body.count("{")
    brace_close = body.count("}")
    tail50 = body[-50:] if len(body) > 50 else body

    if truncated:
        kind = "truncate"
    elif has_open and not has_close:
        kind = "fence_unclosed"
    elif brace_open != brace_close:
        kind = "brace_mismatch"
    else:
        kind = "other"

    return {
        "kind": kind,
        "truncated": truncated,
        "original_len": original_len,
        "stored_len": len(body),
        "has_open_fence": has_open,
        "has_close_fence": has_close,
        "brace_open": brace_open,
        "brace_close": brace_close,
        "tail50": tail50,
    }


TARGETS = [
    ("gemma_8loop", "math-03", 13),
    ("gemma_8loop", "synthesis-01", 14),
    ("gemma_8loop", "logic-04", 2),
    ("gemma_8loop", "logic-04", 6),
]


def diagnose(input_path: Path) -> list[dict]:
    with open(input_path, encoding="utf-8") as f:
        d = json.load(f)
    by_key = {(t["condition"], t["task_id"], t["trial"]): t for t in d["trials"]}
    rows = []
    for key in TARGETS:
        t = by_key.get(key)
        if t is None:
            rows.append({"key": list(key), "missing": True})
            continue
        debug = t.get("_debug") or {}
        logs = debug.get("abc_logs") or []
        if not logs:
            rows.append({"key": list(key), "no_debug_logs": True})
            continue
        last = logs[-1]
        if last.get("a_error"):
            phase = "A"
            raw = last.get("a_raw", "")
        elif last.get("b_error"):
            phase = "B"
            raw = last.get("b_raw", "")
        elif last.get("c_error"):
            phase = "C"
            raw = last.get("c_raw", "")
        else:
            phase = "?"
            raw = ""
        cls = classify(raw)
        rows.append({
            "key": list(key),
            "trial_error": t.get("error"),
            "fail_phase": phase,
            "last_cycle": last.get("cycle"),
            "last_phase_name": last.get("phase"),
            **cls,
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose ABC JSON parse 4 fail")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    args = parser.parse_args()
    rows = diagnose(Path(args.input))
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    kinds: dict = {}
    for r in rows:
        k = r.get("kind", "unknown")
        kinds[k] = kinds.get(k, 0) + 1
    print("\n--- summary ---")
    for k, v in sorted(kinds.items()):
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
