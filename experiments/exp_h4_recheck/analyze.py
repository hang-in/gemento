"""H4 재검증 분석 — assertion turnover + error mode + 정확도 종합.

Task 04 의 결과 JSON 을 입력으로 받아 condition × task 별 3 축 metric 산출.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ============================================================
# (ii) assertion turnover
# ============================================================

def count_assertion_turnover(tattoo_history: list[dict] | None) -> dict:
    """Tattoo history 에서 cycle 별 assertion 추가/수정/삭제 카운트.

    Args:
        tattoo_history: cycle 별 Tattoo dict 의 list. 각 dict 의 'assertions' 필드 비교.

    Returns:
        {added: int, modified: int, deleted: int, total_cycles: int, final_count: int}
    """
    if not tattoo_history or len(tattoo_history) < 2:
        return {"added": 0, "modified": 0, "deleted": 0, "total_cycles": len(tattoo_history or []), "final_count": 0}

    added = 0
    modified = 0
    deleted = 0
    prev_assertions = []
    for cycle_idx, t in enumerate(tattoo_history):
        curr_assertions = t.get("assertions") or (t.get("state") or {}).get("assertions") or []
        if cycle_idx == 0:
            added += len(curr_assertions)
        else:
            prev_ids = {a.get("id") or i: a for i, a in enumerate(prev_assertions)}
            curr_ids = {a.get("id") or i: a for i, a in enumerate(curr_assertions)}
            added += len(set(curr_ids) - set(prev_ids))
            deleted += len(set(prev_ids) - set(curr_ids))
            for k in set(curr_ids) & set(prev_ids):
                if json.dumps(curr_ids[k], sort_keys=True) != json.dumps(prev_ids[k], sort_keys=True):
                    modified += 1
        prev_assertions = curr_assertions

    return {
        "added": added,
        "modified": modified,
        "deleted": deleted,
        "total_cycles": len(tattoo_history),
        "final_count": len(prev_assertions),
    }


# ============================================================
# (iii) error mode classifier
# ============================================================

# Stage 2B (`scorer-failure-label-reference`) 통합:
# `experiments/schema.py:FailureLabel` 이 표준 enum.
# 본 모듈의 ErrorMode 는 그 alias — 두 이름 모두 사용 가능.
from experiments.schema import FailureLabel as ErrorMode


def classify_error_mode(trial: dict, task: dict | None = None) -> ErrorMode:
    """trial 결과 + task 정보로 error mode 분류.

    Args:
        trial: {final_answer, error, accuracy_v3, ...}
        task: 정답 검증용 (optional)

    Returns:
        ErrorMode enum 값
    """
    if trial.get("error"):
        from experiments.run_helpers import classify_trial_error, TrialError
        te = classify_trial_error(trial["error"])
        return {
            TrialError.CONNECTION_ERROR: ErrorMode.CONNECTION_ERROR,
            TrialError.TIMEOUT: ErrorMode.TIMEOUT,
            TrialError.PARSE_ERROR: ErrorMode.PARSE_ERROR,
            TrialError.MODEL_ERROR: ErrorMode.OTHER,
            TrialError.OTHER: ErrorMode.OTHER,
        }.get(te, ErrorMode.OTHER)

    final = trial.get("final_answer")
    if final is None or (isinstance(final, str) and not final.strip()):
        return ErrorMode.NULL_ANSWER

    acc = trial.get("accuracy_v3", 0)
    if acc >= 0.5:
        return ErrorMode.NONE

    if isinstance(final, str) and len(final) > 10:
        return ErrorMode.WRONG_SYNTHESIS

    return ErrorMode.FORMAT_ERROR


# ============================================================
# main
# ============================================================

def analyze(result_path: Path, taskset_path: Path | None = None) -> dict:
    with open(result_path, encoding="utf-8") as f:
        d = json.load(f)

    tasks = {}
    if taskset_path:
        with open(taskset_path, encoding="utf-8") as f:
            ts = json.load(f)
        tasks = {t["id"]: t for t in ts["tasks"]}

    by_cond_task: dict = defaultdict(lambda: {
        "n": 0,
        "acc_v3_sum": 0.0,
        "turnover_added_sum": 0,
        "turnover_modified_sum": 0,
        "turnover_deleted_sum": 0,
        "turnover_final_count_sum": 0,
        "error_modes": defaultdict(int),
    })

    for trial in d["trials"]:
        key = (trial["condition"], trial["task_id"])
        agg = by_cond_task[key]
        agg["n"] += 1
        agg["acc_v3_sum"] += trial.get("accuracy_v3", 0)
        turn = count_assertion_turnover(trial.get("tattoo_history"))
        agg["turnover_added_sum"] += turn["added"]
        agg["turnover_modified_sum"] += turn["modified"]
        agg["turnover_deleted_sum"] += turn["deleted"]
        agg["turnover_final_count_sum"] += turn["final_count"]
        em = classify_error_mode(trial, tasks.get(trial["task_id"]))
        agg["error_modes"][em.value] += 1

    summary = {}
    for (cond, task_id), agg in by_cond_task.items():
        n = agg["n"]
        summary[(cond, task_id)] = {
            "n": n,
            "acc_v3_mean": agg["acc_v3_sum"] / n if n else 0,
            "turnover": {
                "added_mean": agg["turnover_added_sum"] / n if n else 0,
                "modified_mean": agg["turnover_modified_sum"] / n if n else 0,
                "deleted_mean": agg["turnover_deleted_sum"] / n if n else 0,
                "final_count_mean": agg["turnover_final_count_sum"] / n if n else 0,
            },
            "error_modes": dict(agg["error_modes"]),
        }

    by_cond: dict = defaultdict(lambda: {"n": 0, "acc": 0.0, "turn_added": 0, "turn_modified": 0})
    for (cond, _), s in summary.items():
        by_cond[cond]["n"] += s["n"]
        by_cond[cond]["acc"] += s["acc_v3_mean"] * s["n"]
        by_cond[cond]["turn_added"] += s["turnover"]["added_mean"] * s["n"]
        by_cond[cond]["turn_modified"] += s["turnover"]["modified_mean"] * s["n"]

    return {"by_cond_task": summary, "by_cond": dict(by_cond)}


def main() -> int:
    parser = argparse.ArgumentParser(description="H4 재검증 분석")
    parser.add_argument("--result", required=True, help="exp_h4_recheck_*.json 경로")
    parser.add_argument("--taskset", default="experiments/tasks/taskset.json")
    args = parser.parse_args()

    out = analyze(Path(args.result), Path(args.taskset))

    print("=== condition aggregate ===")
    for cond, stat in out["by_cond"].items():
        n = stat["n"]
        print(f"  {cond:15} n={n:4} acc={stat['acc']/n:.4f} turn_added={stat['turn_added']/n:.2f} turn_modified={stat['turn_modified']/n:.2f}")

    print()
    print("=== ablation ===")
    bc = out["by_cond"]
    if "solo_1call" in bc and "solo_budget" in bc and "abc" in bc:
        s1_acc = bc["solo_1call"]["acc"] / bc["solo_1call"]["n"]
        sb_acc = bc["solo_budget"]["acc"] / bc["solo_budget"]["n"]
        ab_acc = bc["abc"]["acc"] / bc["abc"]["n"]
        print(f"  다단계 효과 (solo_budget − solo_1call) = {sb_acc - s1_acc:+.4f}")
        print(f"  역할 분리 효과 (abc − solo_budget)    = {ab_acc - sb_acc:+.4f}")
        print(f"  합산 효과 (abc − solo_1call)         = {ab_acc - s1_acc:+.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
