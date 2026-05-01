"""Exp11 Mixed Intelligence — Gemini 2.5 Flash Judge C + Gemma A/B.

H10 가설: 강한 외부 Judge C(Flash)가 약한 Proposer/Critic(Gemma)의 한계를 보완.
2 condition: baseline_abc (Gemma A/B/C) vs mixed_flash_judge (Gemma A/B + Flash C).
15 task × 2 condition × 5 trial = 150 trial.
dispatcher key: `exp11-mixed-intelligence`
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
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
from experiments._external.gemini_client import (
    call_with_meter as call_gemini,
    DEFAULT_MODEL as GEMINI_FLASH_MODEL,
)

RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_TRIALS = 5
DEFAULT_MAX_CYCLES = 8


@dataclass
class FlashCostAccumulator:
    """trial 단위 Gemini Flash 비용 누적."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    call_count: int = 0
    errors: list[str] = field(default_factory=list)

    def add_meter(self, meter) -> None:
        self.total_input_tokens += meter.input_tokens
        self.total_output_tokens += meter.output_tokens
        self.total_cost_usd += meter.cost_usd
        self.call_count += 1
        if meter.error:
            self.errors.append(meter.error)

    def to_dict(self) -> dict:
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "call_count": self.call_count,
            "errors": self.errors,
        }


def _flash_c_caller(cost_acc: FlashCostAccumulator):
    """Gemini Flash 호출 wrapper — run_abc_chain 의 c_caller 시그니처 호환.

    c_caller: (messages: list[dict]) -> tuple[str, dict]
    gemini_client.call_with_meter 가 OpenAI 스타일 messages 자동 변환 + system 분리.
    response_mime_type=None: Judge 응답은 자유 형식(text), JSON 강제 안 함.
    """
    def _caller(messages: list[dict]) -> tuple[str, dict]:
        meter = call_gemini(
            messages,
            model=GEMINI_FLASH_MODEL,
            response_mime_type=None,
        )
        cost_acc.add_meter(meter)
        meta = {
            "model": meter.model,
            "duration_ms": meter.duration_ms,
            "input_tokens": meter.input_tokens,
            "output_tokens": meter.output_tokens,
            "cost_usd": meter.cost_usd,
            "error": meter.error,
        }
        return meter.raw_response, meta
    return _caller


def _extract_tattoo_history(abc_logs: list, tattoo) -> list:
    """abc_logs 에서 cycle-by-cycle tattoo snapshot 추출.

    ABCCycleLog.a_log.tattoo_out 이 각 사이클 A 처리 후 tattoo dict.
    추출 실패 시 final tattoo 1 개 fallback (Stage 2C 결함 패턴 유지).
    """
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
    if not history and tattoo:
        history = [tattoo.to_dict()]
    return history


def run_baseline_abc(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """A/B/C 모두 Gemma — Stage 2C abc condition 과 정합 + cycle-by-cycle tattoo_history."""
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


def run_mixed_flash_judge(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """A/B = Gemma, C = Gemini 2.5 Flash. Mixed Intelligence."""
    start = time.time()
    final_answer = None
    error = None
    actual_cycles = 0
    tattoo = None
    abc_logs = []
    cost_acc = FlashCostAccumulator()
    try:
        flash_c = _flash_c_caller(cost_acc)
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_mixed_t{trial_idx}",
            objective=task["objective"],
            prompt=task["prompt"],
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            c_caller=flash_c,
        )
        actual_cycles = len(abc_logs)
        if not final_answer:
            error = f"mixed_flash_judge: no final_answer after {actual_cycles} cycles"
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
        "flash_cost": cost_acc.to_dict(),
    }


CONDITION_DISPATCH = {
    "baseline_abc": run_baseline_abc,
    "mixed_flash_judge": run_mixed_flash_judge,
}


def run_experiment(
    *,
    taskset_path: Path,
    trials_per_condition: int = DEFAULT_TRIALS,
    conditions: tuple[str, ...] = ("baseline_abc", "mixed_flash_judge"),
    max_cycles: int = DEFAULT_MAX_CYCLES,
) -> dict:
    """전체 실험 실행 — 사용자 직접 호출 (Task 04)."""
    started = _dt.datetime.now().astimezone().isoformat()

    with open(taskset_path, encoding="utf-8") as f:
        taskset = json.load(f)
    tasks = taskset["tasks"]

    partial_path = RESULTS_DIR / "partial_exp11_mixed_intelligence.json"
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
                flash_cost = result.get("flash_cost")
                verdict = "✓" if acc >= 0.5 else ("✗" if acc == 0 else "△")
                cost_str = f"  flash_cost=${flash_cost['total_cost_usd']:.6f}" if flash_cost else ""
                print(
                    f"      → {verdict} acc={acc:.2f}"
                    + (f"  cycles={cyc}" if cyc is not None else "")
                    + (f"  dur={dur}ms" if dur is not None else "")
                    + cost_str
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
                if flash_cost is not None:
                    trial["flash_cost"] = flash_cost
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
        experiment="exp11_mixed_intelligence",
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
    parser = argparse.ArgumentParser(description="Exp11 Mixed Intelligence — Flash Judge C")
    parser.add_argument("--taskset", default="experiments/tasks/taskset.json")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--max-cycles", type=int, default=DEFAULT_MAX_CYCLES)
    parser.add_argument("--conditions", nargs="+", default=["baseline_abc", "mixed_flash_judge"])
    parser.add_argument("--out-name", default=None)
    args = parser.parse_args()

    out = run_experiment(
        taskset_path=Path(args.taskset),
        trials_per_condition=args.trials,
        conditions=tuple(args.conditions),
        max_cycles=args.max_cycles,
    )

    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = args.out_name or f"exp11_mixed_intelligence_{ts}.json"
    out_path = RESULTS_DIR / name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"  → Result saved: {out_path}")

    agg: dict = defaultdict(lambda: {"n": 0, "v3": 0.0, "flash_cost_usd": 0.0})
    for t in out["trials"]:
        agg[t["condition"]]["n"] += 1
        agg[t["condition"]]["v3"] += t.get("accuracy_v3", 0)
        if t.get("flash_cost"):
            agg[t["condition"]]["flash_cost_usd"] += t["flash_cost"].get("total_cost_usd", 0)

    print()
    print("=== condition aggregate (v3) ===")
    for cond in args.conditions:
        if cond in agg:
            stat = agg[cond]
            mean = stat["v3"] / stat["n"] if stat["n"] else 0
            cost_str = f"  total_flash_cost=${stat['flash_cost_usd']:.4f}" if stat["flash_cost_usd"] else ""
            print(f"  {cond:25} n={stat['n']:4} mean_acc={mean:.4f}{cost_str}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
