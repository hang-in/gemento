"""H4 재검증 — Solo-1call / Solo-budget / ABC 3 condition 비교.

15 task × 3 condition × 5 trial = 225 trial.
dispatcher key: `h4-recheck`
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments.run_helpers import (
    classify_trial_error,
    is_fatal_error,
    check_error_rate,
    build_result_meta,
    get_taskset_version,
    normalize_sampling_params,
)
from experiments.config import SAMPLING_PARAMS, MODEL_NAME, API_BASE_URL
from experiments.measure import score_answer_v3
from experiments.orchestrator import run_chain, run_abc_chain, call_model, extract_json_from_response

RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_TRIALS = 5
DEFAULT_MAX_CYCLES = 8  # 결정 5


def _solo_messages(task: dict) -> list[dict]:
    return [
        {"role": "system", "content": "You are a helpful reasoning assistant. Think step by step and provide your final answer as JSON: {\"final_answer\": \"...\"}."},
        {"role": "user", "content": task["prompt"]},
    ]


def run_solo_1call(task: dict, trial_idx: int) -> dict:
    """Solo-1call: 단발 호출, loop=1. exp00_baseline 패턴."""
    start = time.time()
    final_answer = None
    error = None
    tattoo_history = None
    try:
        raw, _ = call_model(_solo_messages(task))
        parsed = extract_json_from_response(raw)
        if isinstance(parsed, dict):
            final_answer = parsed.get("final_answer")
        if final_answer is None and raw:
            final_answer = raw.strip()[:500]
    except Exception as e:
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    return {
        "final_answer": final_answer,
        "error": error,
        "cycles": 1,
        "duration_ms": duration_ms,
        "tattoo_history": tattoo_history,
    }


def run_solo_budget(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """Solo-budget: 단일 모델 자기 반복, max_loops=max_cycles. exp06 run_chain 패턴."""
    start = time.time()
    final_answer = None
    error = None
    tattoo_history = None
    actual_cycles = 0
    try:
        final_tattoo, logs, final_answer = run_chain(
            task_id=f"{task['id']}_solo_budget_t{trial_idx}",
            objective=f"{task['objective']}\n\nProblem:\n{task['prompt']}",
            constraints=task.get("constraints", []),
            max_loops=max_cycles,
        )
        actual_cycles = len(logs)
        tattoo_history = [l.tattoo_out for l in logs] if logs else None
        if not final_answer:
            error = f"solo_budget: no final_answer after {actual_cycles} loops"
    except Exception as e:
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": duration_ms,
        "tattoo_history": tattoo_history,
    }


def run_abc(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """ABC: A→B→C 직렬, max_cycles=max_cycles (결정 5 = 8)."""
    start = time.time()
    final_answer = None
    error = None
    tattoo_history = None
    actual_cycles = 0
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_abc_t{trial_idx}",
            objective=task["objective"],
            prompt=task["prompt"],
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
        )
        actual_cycles = len(abc_logs)
        tattoo_history = [tattoo.to_dict()] if tattoo else None
        if not final_answer:
            error = f"abc: no final_answer after {actual_cycles} cycles"
    except Exception as e:
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": duration_ms,
        "tattoo_history": tattoo_history,
    }


CONDITION_DISPATCH = {
    "solo_1call": run_solo_1call,
    "solo_budget": run_solo_budget,
    "abc": run_abc,
}


def run_experiment(
    *,
    taskset_path: Path,
    trials_per_condition: int = DEFAULT_TRIALS,
    conditions: tuple[str, ...] = ("solo_1call", "solo_budget", "abc"),
    max_cycles: int = DEFAULT_MAX_CYCLES,
) -> dict:
    """전체 실험 실행 — 사용자 직접 호출 (Task 04)."""
    started = _dt.datetime.now().astimezone().isoformat()

    with open(taskset_path, encoding="utf-8") as f:
        taskset = json.load(f)
    tasks = taskset["tasks"]

    partial_path = RESULTS_DIR / "partial_exp_h4_recheck.json"
    trials_data: list[dict] = []
    finished: set[tuple[str, str, int]] = set()

    if partial_path.exists():
        try:
            with open(partial_path, encoding="utf-8") as f:
                partial = json.load(f)
                trials_data = partial.get("trials", [])
                for t in trials_data:
                    finished.add((t["condition"], t["task_id"], t["trial_idx"]))
            print(f"  → Resuming: {len(finished)} trials done.")
        except Exception:
            print("  ⚠ Checkpoint load failed; starting fresh.")
            trials_data = []

    total = len(conditions) * len(tasks) * trials_per_condition
    counter = len(finished)
    aborted = False

    for cond in conditions:
        if aborted:
            break
        dispatch = CONDITION_DISPATCH[cond]
        print()
        print("=" * 80)
        print(f"  CONDITION: {cond}  (max_cycles={max_cycles}, trials_per_task={trials_per_condition})")
        print("=" * 80)
        for task in tasks:
            if aborted:
                break
            for trial_idx in range(trials_per_condition):
                key = (cond, task["id"], trial_idx)
                if key in finished:
                    continue
                counter += 1
                prompt_preview = str(task.get("prompt", ""))[:120].replace("\n", " ")
                print()
                print(f"  [{counter}/{total}] {cond} | {task['id']} ({task.get('category','?')}/{task.get('difficulty','?')}) | trial {trial_idx}")
                print(f"      prompt: {prompt_preview}{'...' if len(str(task.get('prompt',''))) > 120 else ''}")

                result = dispatch(task, trial_idx, max_cycles) if cond != "solo_1call" else dispatch(task, trial_idx)
                final = result.get("final_answer") or ""
                acc = score_answer_v3(str(final), task)
                ans_preview = str(final)[:120].replace("\n", " ") if final else "(null)"
                dur = result.get("duration_ms")
                cyc = result.get("cycles")
                err = result.get("error")
                verdict = "✓" if acc >= 0.5 else ("✗" if acc == 0 else "△")
                print(
                    f"      → {verdict} acc={acc:.2f}"
                    + (f"  cycles={cyc}" if cyc is not None else "")
                    + (f"  dur={dur}ms" if dur is not None else "")
                    + (f"  err={str(err)[:60]}" if err else "")
                )
                print(f"      answer: {ans_preview}{'...' if len(str(final)) > 120 else ''}")

                trial = {
                    "condition": cond,
                    "task_id": task["id"],
                    "trial_idx": trial_idx,
                    "final_answer": str(final)[:500] if final else None,
                    "duration_ms": result.get("duration_ms"),
                    "error": result.get("error"),
                    "cycles": result.get("cycles"),
                    "tattoo_history": result.get("tattoo_history"),
                    "accuracy_v3": acc,
                }
                trials_data.append(trial)

                err = classify_trial_error(result.get("error"))
                if is_fatal_error(err):
                    print(f"[ABORT] cond={cond} task={task['id']} trial={trial_idx} fatal={err.value}: {str(result.get('error'))[:200]}")
                    print("[ABORT] 부분 결과는 보존. 저장 직전 error 비율 검사 진행.")
                    aborted = True
                    break

                RESULTS_DIR.mkdir(parents=True, exist_ok=True)
                with open(partial_path, "w", encoding="utf-8") as f:
                    json.dump({"trials": trials_data}, f, ensure_ascii=False, indent=2)

    ok, rate = check_error_rate(trials_data, threshold=0.30)
    if not ok:
        print(f"[REJECT] error rate {rate:.1%} ≥ 30%. 저장 거부 + warning")
        print("[REJECT] 부분 결과는 메모리에 유지 — 사용자가 별도 처리 권고")
        raise SystemExit(1)

    ended = _dt.datetime.now().astimezone().isoformat()

    meta = build_result_meta(
        experiment="exp_h4_recheck",
        model_name=MODEL_NAME,
        model_engine="lm_studio",
        model_endpoint=API_BASE_URL,
        sampling_params=normalize_sampling_params(SAMPLING_PARAMS),
        scorer_version="v3",
        taskset_version=get_taskset_version(),
        started_at=started,
        ended_at=ended,
    )

    out = {
        **meta,
        "conditions": list(conditions),
        "trials_per_condition": trials_per_condition,
        "max_cycles": max_cycles,
        "trials": trials_data,
    }

    if partial_path.exists():
        partial_path.unlink()
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="H4 재검증 — Solo-1call / Solo-budget / ABC")
    parser.add_argument("--taskset", default="experiments/tasks/taskset.json")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--max-cycles", type=int, default=DEFAULT_MAX_CYCLES)
    parser.add_argument("--conditions", nargs="+", default=["solo_1call", "solo_budget", "abc"])
    parser.add_argument("--out-name", default=None)
    args = parser.parse_args()

    out = run_experiment(
        taskset_path=Path(args.taskset),
        trials_per_condition=args.trials,
        conditions=tuple(args.conditions),
        max_cycles=args.max_cycles,
    )

    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = args.out_name or f"exp_h4_recheck_{ts}.json"
    out_path = RESULTS_DIR / name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"  → Result saved: {out_path}")

    agg: dict = defaultdict(lambda: {"n": 0, "v3": 0.0})
    for t in out["trials"]:
        agg[t["condition"]]["n"] += 1
        agg[t["condition"]]["v3"] += t.get("accuracy_v3", 0)
    print()
    print("=== condition aggregate (v3) ===")
    for cond in args.conditions:
        if cond in agg:
            stat = agg[cond]
            mean = stat["v3"] / stat["n"] if stat["n"] else 0
            print(f"  {cond:20} n={stat['n']:4} mean_acc={mean:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
