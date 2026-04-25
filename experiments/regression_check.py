"""Regression helpers for the role-adapter refactor gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from measure import score_answer_v2


TASKSET_PATH = Path(__file__).parent / "tasks" / "taskset.json"
TARGET_ARMS = ("baseline_refined", "tooluse_refined")
TARGET_TASK_ID = "math-04"


def load_json(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_task_map() -> dict[str, dict]:
    data = load_json(TASKSET_PATH)
    return {task["id"]: task for task in data["tasks"]}


def extract_math04(raw_result: dict) -> dict:
    extracted: dict[str, dict] = {}
    for arm in TARGET_ARMS:
        arm_data = raw_result.get("results_by_condition", {}).get(arm, [])
        match = next((tb for tb in arm_data if tb.get("task_id") == TARGET_TASK_ID), None)
        if match is None:
            continue
        extracted[arm] = {
            "task_id": TARGET_TASK_ID,
            "expected_answer": match.get("expected_answer"),
            "trials": [
                {
                    "trial": trial["trial"],
                    "final_answer": trial.get("final_answer"),
                    "actual_cycles": trial.get("actual_cycles", 0),
                    "num_assertions": trial.get("total_assertions", 0),
                    "total_tool_calls": trial.get("total_tool_calls", 0),
                    "tool_errors": trial.get("tool_errors", 0),
                }
                for trial in match.get("trials", [])
            ],
        }
    return extracted


def save_extracted(raw_result_path: str | Path, output_path: str | Path) -> None:
    raw = load_json(raw_result_path)
    extracted = extract_math04(raw)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(extracted, f, ensure_ascii=False, indent=2)
    print(f"saved {output_path}")


def accuracy_by_arm(data: dict, task_map: dict[str, dict]) -> dict[str, float]:
    task_entry = task_map[TARGET_TASK_ID]
    scores: dict[str, float] = {}
    for arm in TARGET_ARMS:
        trials = data.get(arm, {}).get("trials", [])
        values = [
            score_answer_v2(str(trial.get("final_answer") or ""), task_entry)
            for trial in trials
        ]
        scores[arm] = sum(values) / len(values) if values else 0.0
    return scores


def compare(pre: dict, post: dict) -> tuple[bool, list[str]]:
    violations: list[str] = []
    task_map = load_task_map()

    for arm in TARGET_ARMS:
        if arm not in pre or arm not in post:
            violations.append(f"arm missing: {arm}")
            continue
        pre_trials = {t["trial"]: t for t in pre[arm]["trials"]}
        post_trials = {t["trial"]: t for t in post[arm]["trials"]}
        for trial_id, pre_trial in pre_trials.items():
            post_trial = post_trials.get(trial_id)
            if post_trial is None:
                violations.append(f"{arm} trial {trial_id} missing in post")
                continue
            if str(pre_trial.get("final_answer")) != str(post_trial.get("final_answer")):
                violations.append(
                    f"{arm} trial {trial_id} final_answer mismatch: "
                    f"pre={str(pre_trial.get('final_answer'))[:80]!r} "
                    f"vs post={str(post_trial.get('final_answer'))[:80]!r}"
                )
            pre_assertions = pre_trial.get("num_assertions", 0)
            post_assertions = post_trial.get("num_assertions", 0)
            if abs(pre_assertions - post_assertions) > 1:
                violations.append(
                    f"{arm} trial {trial_id} num_assertions diff > 1: "
                    f"pre={pre_assertions} vs post={post_assertions}"
                )
            pre_tools = pre_trial.get("total_tool_calls", 0)
            post_tools = post_trial.get("total_tool_calls", 0)
            if abs(pre_tools - post_tools) > 2:
                violations.append(
                    f"{arm} trial {trial_id} tool_calls diff > 2: "
                    f"pre={pre_tools} vs post={post_tools}"
                )

    pre_acc = accuracy_by_arm(pre, task_map)
    post_acc = accuracy_by_arm(post, task_map)
    for arm in TARGET_ARMS:
        if pre_acc.get(arm, 0.0) != post_acc.get(arm, 0.0):
            violations.append(
                f"{arm} accuracy_v2 mismatch: pre={pre_acc.get(arm, 0.0):.3f} "
                f"vs post={post_acc.get(arm, 0.0):.3f}"
            )

    return (len(violations) == 0, violations)


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] == "extract":
        if len(argv) != 4:
            print("usage: regression_check.py extract <raw_result.json> <output.json>")
            return 2
        save_extracted(argv[2], argv[3])
        return 0

    if len(argv) != 3:
        print("usage: regression_check.py <pre.json> <post.json>")
        print("   or: regression_check.py extract <raw_result.json> <output.json>")
        return 2

    pre = load_json(argv[1])
    post = load_json(argv[2])
    ok, violations = compare(pre, post)
    if ok:
        print("PASS role-adapter regression gate")
        return 0

    print(f"FAIL role-adapter regression gate ({len(violations)} violations)")
    for violation in violations:
        print(f"- {violation}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
