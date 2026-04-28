"""Exp10 v2 final 의 540 trial 을 v3 채점으로 재산정.

각 trial dict 에 `accuracy_v2` (원본 보존) + `accuracy_v3` (신규) 두 필드 보유.
출력 JSON 은 입력과 동일 schema + 위 두 필드 추가.
stdout 에 condition × task aggregate 비교 표 출력.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from measure import score_answer_v2, score_answer_v3
from exp10_reproducibility_cost.run import RESULTS_DIR, save_result


DEFAULT_INPUT = RESULTS_DIR / "exp10_v2_final_20260429_033922.json"
TASKSET_PATH = Path(__file__).resolve().parent.parent / "tasks" / "taskset.json"


def _load_task_map() -> dict[str, dict]:
    with open(TASKSET_PATH, encoding="utf-8") as f:
        d = json.load(f)
    return {t["id"]: t for t in d["tasks"]}


def rescore(input_path: Path) -> dict:
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)
    task_map = _load_task_map()

    new_trials = []
    for t in data["trials"]:
        task = task_map.get(t["task_id"])
        if task is None:
            raise RuntimeError(f"unknown task_id: {t['task_id']}")
        final = str(t.get("final_answer") or "")
        v2 = score_answer_v2(final, task)
        v3 = score_answer_v3(final, task)
        new_t = dict(t)
        new_t["accuracy_v2"] = v2
        new_t["accuracy_v3"] = v3
        new_trials.append(new_t)

    out = dict(data)
    out["trials"] = new_trials
    out["_v3_rescore"] = {
        "source": input_path.name,
        "scorer": "score_answer_v3",
        "scorer_changes": "logic-04 negative_patterns added in taskset.json",
    }
    return out


def aggregate_and_print(data: dict) -> None:
    cond_agg: dict = defaultdict(lambda: {"n": 0, "v2": 0.0, "v3": 0.0})
    task_agg: dict = defaultdict(lambda: {"n": 0, "v2": 0.0, "v3": 0.0})
    for t in data["trials"]:
        c = t["condition"]
        tid = t["task_id"]
        cond_agg[c]["n"] += 1
        cond_agg[c]["v2"] += t["accuracy_v2"]
        cond_agg[c]["v3"] += t["accuracy_v3"]
        task_agg[(c, tid)]["n"] += 1
        task_agg[(c, tid)]["v2"] += t["accuracy_v2"]
        task_agg[(c, tid)]["v3"] += t["accuracy_v3"]

    print("=== condition aggregate (v2 vs v3) ===")
    print(f'{"condition":24} {"n":>4} {"v2":>8} {"v3":>8} {"Δ":>9}')
    for c in ("gemma_8loop", "gemma_1loop", "gemini_flash_1call"):
        a = cond_agg[c]
        v2m = a["v2"] / a["n"]
        v3m = a["v3"] / a["n"]
        print(f'{c:24} {a["n"]:>4} {v2m:>8.4f} {v3m:>8.4f} {v3m-v2m:>+9.4f}')

    print()
    print("=== per-task v2 vs v3 (Δ != 0 만 표시) ===")
    print(f'{"condition":24} {"task":13} {"v2":>7} {"v3":>7} {"Δ":>8}')
    for (c, tid), a in sorted(task_agg.items()):
        v2m = a["v2"] / a["n"]
        v3m = a["v3"] / a["n"]
        if abs(v3m - v2m) > 1e-9:
            print(f'{c:24} {tid:13} {v2m:>7.3f} {v3m:>7.3f} {v3m-v2m:>+8.3f}')


def main() -> int:
    parser = argparse.ArgumentParser(description="Exp10 v2 final 의 v3 재산정")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--out-name", default="exp10_v3_rescored")
    args = parser.parse_args()
    data = rescore(Path(args.input))
    out_path = save_result(args.out_name, data)
    aggregate_and_print(data)
    print(f'\noutput: {out_path}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
