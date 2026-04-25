"""실험 10: Reproducibility & Cost Profile.

3 condition × 9 task × N=20 trial = 540 호출.
- gemma_8loop        : Gemma 4 E4B + 8루프 (loop_saturation baseline_phase15 동등)
- gemma_1loop        : Gemma 4 E4B 단일 추론
- gemini_flash_1call : Gemini 2.5 Flash 1회 외부 API 호출 (rate limit 1초 sleep)

dispatcher key: `reproducibility-cost`
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import MODEL_NAME
from orchestrator import run_abc_chain
from _external.gemini_client import call_with_meter as gemini_call
from _external.lmstudio_client import call_with_meter as lmstudio_call

from exp10_reproducibility_cost.tasks import (
    EXP10_TASK_IDS, load_exp10_tasks, score_trial,
)


# Google AI Studio 무료 tier rate limit 안전 마진. paid tier 에서는 0 으로 줄여도 OK.
GEMINI_CALL_SLEEP_SEC = 1.0

# experiments-task-07 rev — 자체 디렉토리의 results/ 사용
RESULTS_DIR = Path(__file__).resolve().parent / "results"

DEFAULT_TRIALS = 20
GEMMA_8LOOP_MAX_CYCLES = 15  # loop_saturation baseline_phase15 와 동등
GEMMA_8LOOP_USE_PHASE_PROMPT = True

CONDITIONS = (
    "gemma_8loop",
    "gemma_1loop",
    "gemini_flash_1call",
)


def save_partial(path: Path, data: dict) -> None:
    """체크포인트 저장."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_result(experiment_name: str, result: dict) -> Path:
    """최종 결과 저장."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{experiment_name}_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  → Result saved: {path}")
    return path


def trial_gemma_8loop(task: dict, trial_idx: int) -> dict:
    """gemma_8loop condition: ABC + 8루프 (loop_saturation baseline_phase15 동등)."""
    start = time.time()
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_8loop_t{trial_idx}",
            objective=task["objective"],
            prompt=task["prompt"],
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=GEMMA_8LOOP_MAX_CYCLES,
            use_phase_prompt=GEMMA_8LOOP_USE_PHASE_PROMPT,
        )
        actual_cycles = len(abc_logs)
        error = None
    except Exception as e:
        final_answer = None
        actual_cycles = 0
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    accuracy = score_trial(final_answer, task)
    return {
        "trial": trial_idx + 1,
        "condition": "gemma_8loop",
        "task_id": task["id"],
        "final_answer": str(final_answer) if final_answer else None,
        "accuracy": accuracy,
        "actual_cycles": actual_cycles,
        "duration_ms": duration_ms,
        "input_tokens": 0,   # ABC 체인은 token 합계 미반환 — task-04 analyze 시 0 처리
        "output_tokens": 0,
        "cost_usd": 0.0,
        "error": error,
    }


def trial_gemma_1loop(task: dict, trial_idx: int) -> dict:
    """gemma_1loop condition: LM Studio 단일 호출."""
    messages = [
        {"role": "system", "content": "You are a helpful reasoning assistant. Think step by step and provide your final answer as JSON: {\"final_answer\": \"...\"}."},
        {"role": "user", "content": task["prompt"]},
    ]
    meter = lmstudio_call(messages, response_format={"type": "json_object"})
    # final_answer 파싱
    final_answer = None
    if meter.raw_response and not meter.error:
        try:
            parsed = json.loads(meter.raw_response)
            final_answer = parsed.get("final_answer") if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            final_answer = meter.raw_response.strip()[:200]
    accuracy = score_trial(final_answer, task)
    return {
        "trial": trial_idx + 1,
        "condition": "gemma_1loop",
        "task_id": task["id"],
        "final_answer": str(final_answer) if final_answer else None,
        "accuracy": accuracy,
        "actual_cycles": 1,
        "duration_ms": meter.duration_ms,
        "input_tokens": meter.input_tokens,
        "output_tokens": meter.output_tokens,
        "cost_usd": meter.cost_usd,
        "error": meter.error,
    }


def trial_gemini_flash(task: dict, trial_idx: int) -> dict:
    """gemini_flash_1call condition: Gemini 2.5 Flash API 1회 호출 + rate limit sleep."""
    messages = [
        {"role": "system", "content": "You are a helpful reasoning assistant. Think step by step and provide your final answer as JSON: {\"final_answer\": \"...\"}."},
        {"role": "user", "content": task["prompt"]},
    ]
    meter = gemini_call(messages, response_mime_type="application/json")
    final_answer = None
    if meter.raw_response and not meter.error:
        try:
            parsed = json.loads(meter.raw_response)
            final_answer = parsed.get("final_answer") if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            final_answer = meter.raw_response.strip()[:200]
    accuracy = score_trial(final_answer, task)
    # Rate limit 안전 마진 — Google AI Studio 무료 tier 보호
    time.sleep(GEMINI_CALL_SLEEP_SEC)
    return {
        "trial": trial_idx + 1,
        "condition": "gemini_flash_1call",
        "task_id": task["id"],
        "final_answer": str(final_answer) if final_answer else None,
        "accuracy": accuracy,
        "actual_cycles": 1,
        "duration_ms": meter.duration_ms,
        "input_tokens": meter.input_tokens,
        "output_tokens": meter.output_tokens,
        "cost_usd": meter.cost_usd,
        "error": meter.error,
    }


CONDITION_DISPATCH = {
    "gemma_8loop": trial_gemma_8loop,
    "gemma_1loop": trial_gemma_1loop,
    "gemini_flash_1call": trial_gemini_flash,
}


def run(trials: int = DEFAULT_TRIALS, dry_run: bool = False, conditions: tuple[str, ...] = CONDITIONS) -> Path | None:
    """본 실험. trials × 9 task × len(conditions) trial 실행."""
    tasks = load_exp10_tasks()
    partial_path = RESULTS_DIR / "partial_exp10_reproducibility_cost.json"

    # 이어하기 시도
    finished: set[tuple[str, str, int]] = set()  # (cond, task_id, trial)
    all_results: list[dict] = []
    if partial_path.exists() and not dry_run:
        try:
            with open(partial_path, encoding="utf-8") as f:
                partial = json.load(f)
                all_results = partial.get("trials", [])
                for r in all_results:
                    finished.add((r["condition"], r["task_id"], r["trial"]))
            print(f"  → Resuming from checkpoint: {len(finished)} trials done.")
        except Exception:
            print("  ⚠ Checkpoint load failed; starting fresh.")
            all_results = []

    total = len(conditions) * len(tasks) * trials
    counter = len(finished)
    for cond in conditions:
        dispatch = CONDITION_DISPATCH[cond]
        for task in tasks:
            for trial_idx in range(trials):
                key = (cond, task["id"], trial_idx + 1)
                if key in finished:
                    continue
                counter += 1
                print(f"  [{counter}/{total}] {cond} | {task['id']} | trial {trial_idx + 1}")
                if dry_run:
                    print(f"    (dry-run, skipping LLM call)")
                    return None
                result = dispatch(task, trial_idx)
                all_results.append(result)
                # 매 trial 후 체크포인트
                save_partial(partial_path, {
                    "experiment": "reproducibility_cost",
                    "model": MODEL_NAME,
                    "trials_per_condition": trials,
                    "conditions": list(conditions),
                    "task_ids": list(EXP10_TASK_IDS),
                    "trials": all_results,
                })

    # 최종 결과 저장
    final_path = save_result("exp10_reproducibility_cost", {
        "experiment": "reproducibility_cost",
        "model": MODEL_NAME,
        "trials_per_condition": trials,
        "conditions": list(conditions),
        "task_ids": list(EXP10_TASK_IDS),
        "trials": all_results,
    })
    if partial_path.exists():
        partial_path.unlink()
        print("  → Checkpoint cleared.")
    return final_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Exp10: Reproducibility & Cost Profile")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS, help=f"trials per condition×task (default: {DEFAULT_TRIALS})")
    parser.add_argument("--dry-run", action="store_true", help="첫 trial 만 보고 종료 (LLM 호출 0)")
    parser.add_argument("--conditions", nargs="*", default=list(CONDITIONS),
                        help=f"실행할 condition 목록 (default: {CONDITIONS})")
    args = parser.parse_args()
    run(trials=args.trials, dry_run=args.dry_run, conditions=tuple(args.conditions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
