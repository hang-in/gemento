"""Exp13 Reducer Role — post-stage 결과 통합 효과 측정.

H12 후보 가설: Reducer 가 ABC chain 의 final tattoo + final_answer 를 받아
정리하면 keyword 매칭 정확도 + final answer 명료성 향상.
2 condition: baseline_abc (Reducer 미주입) vs reducer_abc (Reducer post-stage 주입).
15 task × 2 condition × 5 trial = 150 trial.
dispatcher key: `exp13-reducer-role`
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
from experiments.orchestrator import run_abc_chain

RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_TRIALS = 5
DEFAULT_MAX_CYCLES = 8


def _extract_tattoo_history(abc_logs: list, fallback_tattoo) -> list:
    """Stage 2C 결함 fix — cycle-by-cycle tattoo snapshot 추출 (Exp12/Exp13 공통 패턴)."""
    history = []
    for log_entry in abc_logs:
        if hasattr(log_entry, "tattoo_snapshot"):
            snap = log_entry.tattoo_snapshot
            history.append(snap.to_dict() if hasattr(snap, "to_dict") else snap)
        elif hasattr(log_entry, "a_log") and hasattr(log_entry.a_log, "tattoo_out"):
            out = log_entry.a_log.tattoo_out
            history.append(out if isinstance(out, dict) else out.to_dict())
        elif hasattr(log_entry, "tattoo_out"):
            out = log_entry.tattoo_out
            history.append(out if isinstance(out, dict) else out.to_dict())
        elif isinstance(log_entry, dict) and "tattoo" in log_entry:
            history.append(log_entry["tattoo"])
    if not history and fallback_tattoo:
        history = [fallback_tattoo.to_dict()]
    return history


def run_baseline_abc(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """A/B/C 모두 Gemma — Stage 2C / Exp11 / Exp12 baseline 정합. Reducer 미주입."""
    start = time.time()
    final_answer = None
    error = None
    actual_cycles = 0
    tattoo = None
    abc_logs = []
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_baseline_abc_t{trial_idx}",
            objective=task["objective"],
            prompt=task["prompt"],
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            extractor_pre_stage=False,
            reducer_post_stage=False,
        )
        actual_cycles = len(abc_logs)
        if not final_answer:
            error = f"baseline_abc: no final_answer after {actual_cycles} cycles"
    except Exception as e:
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    tattoo_history = _extract_tattoo_history(abc_logs, tattoo)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": duration_ms,
        "tattoo_history": tattoo_history if tattoo_history else None,
    }


def run_reducer_abc(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """A→B→C → Reducer (Gemma) post-stage. 동일 모델 Role 분리/추가."""
    start = time.time()
    final_answer = None
    error = None
    actual_cycles = 0
    tattoo = None
    abc_logs = []
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_reducer_abc_t{trial_idx}",
            objective=task["objective"],
            prompt=task["prompt"],
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            extractor_pre_stage=False,
            reducer_post_stage=True,
        )
        actual_cycles = len(abc_logs)
        if not final_answer:
            error = f"reducer_abc: no final_answer after {actual_cycles} cycles"
    except Exception as e:
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    tattoo_history = _extract_tattoo_history(abc_logs, tattoo)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": duration_ms,
        "tattoo_history": tattoo_history if tattoo_history else None,
    }


CONDITION_DISPATCH = {
    "baseline_abc": run_baseline_abc,
    "reducer_abc": run_reducer_abc,
}


def run_experiment(
    *,
    taskset_path: Path,
    trials_per_condition: int = DEFAULT_TRIALS,
    conditions: tuple[str, ...] = ("baseline_abc", "reducer_abc"),
    max_cycles: int = DEFAULT_MAX_CYCLES,
) -> dict:
    """전체 실험 실행 — 사용자 직접 호출 (Task 04)."""
    started = _dt.datetime.now().astimezone().isoformat()

    with open(taskset_path, encoding="utf-8") as f:
        taskset = json.load(f)
    tasks = taskset["tasks"]

    partial_path = RESULTS_DIR / "partial_exp13_reducer_role.json"
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

                result = dispatch(task, trial_idx, max_cycles)
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

                trial: dict = {
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

                err_cls = classify_trial_error(result.get("error"))
                if is_fatal_error(err_cls):
                    print(f"[ABORT] cond={cond} task={task['id']} trial={trial_idx} fatal={err_cls.value}: {str(result.get('error'))[:200]}")
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
        experiment="exp13_reducer_role",
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
    parser = argparse.ArgumentParser(description="Exp13 Reducer Role — post-stage hook")
    parser.add_argument("--taskset", default="experiments/tasks/taskset.json")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--max-cycles", type=int, default=DEFAULT_MAX_CYCLES)
    parser.add_argument("--conditions", nargs="+", default=["baseline_abc", "reducer_abc"])
    parser.add_argument("--out-name", default=None)
    args = parser.parse_args()

    out = run_experiment(
        taskset_path=Path(args.taskset),
        trials_per_condition=args.trials,
        conditions=tuple(args.conditions),
        max_cycles=args.max_cycles,
    )

    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = args.out_name or f"exp13_reducer_role_{ts}.json"
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
            print(f"  {cond:25} n={stat['n']:4} mean_acc={mean:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
