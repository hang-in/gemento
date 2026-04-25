"""math-04 격리 회귀 실행 — Role Adapter 리팩토링 동치 검증용.

`run_experiment.py:run_tool_use_refined`의 trial 루프를 math-04 한 task만 실행하도록
간소화한 entry point. 출력은 `regression_check.py:compare()`가 직접 읽을 수 있는
형식이며 `experiments/results/role_adapter_regression_pre.json` 과 동일 구조이다.

usage:
    python run_regression_gate.py [--trials N] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from orchestrator import run_abc_chain
from run_experiment import (
    TOOL_USE_REFINED_REPEAT,
    TOOL_USE_REFINED_MAX_CYCLES,
    TOOL_USE_REFINED_PHASE_PROMPT,
    TOOL_USE_REFINED_CONDITIONS,
    load_tasks,
)


TARGET_TASK_ID = "math-04"
DEFAULT_OUT = Path(__file__).parent / "results" / "role_adapter_regression_post.json"


def run_one_trial(task: dict, label: str, use_tools: bool, trial_idx: int) -> dict:
    """run_tool_use_refined 의 1 trial 실행 로직을 그대로 호출."""
    tattoo, abc_logs, final_answer = run_abc_chain(
        task_id=f"{task['id']}_{label}_t{trial_idx}",
        objective=task["objective"],
        prompt=task["prompt"],
        constraints=task.get("constraints"),
        termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
        max_cycles=TOOL_USE_REFINED_MAX_CYCLES,
        use_phase_prompt=TOOL_USE_REFINED_PHASE_PROMPT,
        use_tools=use_tools,
    )
    total_tool_calls = 0
    tool_errors = 0
    for cl in abc_logs:
        tc_list = getattr(cl, "tool_calls", []) or []
        total_tool_calls += len(tc_list)
        tool_errors += sum(1 for tc in tc_list if tc.get("error"))
    return {
        "trial": trial_idx + 1,
        "final_answer": final_answer,
        "actual_cycles": len(abc_logs),
        "num_assertions": len(tattoo.assertions),
        "total_tool_calls": total_tool_calls,
        "tool_errors": tool_errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Role Adapter 회귀 게이트 — math-04 격리 실행")
    parser.add_argument("--trials", type=int, default=TOOL_USE_REFINED_REPEAT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    all_tasks = load_tasks()
    task = next((t for t in all_tasks if t["id"] == TARGET_TASK_ID), None)
    if task is None:
        print(f"task {TARGET_TASK_ID} not found in taskset")
        return 2

    output: dict[str, dict] = {}
    for cond in TOOL_USE_REFINED_CONDITIONS:
        label = cond["label"]
        use_tools = cond["use_tools"]
        print(f"\n[regression-gate] arm={label} | task={TARGET_TASK_ID}")
        trials: list[dict] = []
        for i in range(args.trials):
            print(f"  Trial {i + 1}/{args.trials}...")
            trials.append(run_one_trial(task, label, use_tools, i))
        output[label] = {
            "task_id": TARGET_TASK_ID,
            "expected_answer": task.get("expected_answer"),
            "trials": trials,
        }
        # incremental save — 중간에 끊겨도 부분 결과 보존
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"  saved partial -> {args.out}")

    print(f"\nDone. wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
