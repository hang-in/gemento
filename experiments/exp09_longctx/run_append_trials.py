"""Exp09 추가 trial 실행 — 기존 3-trial 결과에 trial 4, 5를 append.

기존 결과 JSON을 로드하고 각 (arm, task) 조합에 대해 2개 추가 trial을 실행한다.
최종적으로 5-trial 결과를 exp09_longctx_5trial_<timestamp>.json으로 저장한다.

전제: Ollama 또는 LM Studio에 gemma4:e4b 모델이 구동 중이어야 한다.

사용:
    python -m experiments.exp09_longctx.run_append_trials
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# experiments/ 및 exp09_longctx/ 를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run import (  # noqa: E402  (same directory import after path setup)
    _run_longctx_trial,
    LONGCTX_ARMS,
    LONGCTX_CHUNK_SIZE,
    LONGCTX_CHUNK_OVERLAP,
    LONGCTX_RAG_TOP_K,
    LONGCTX_MAX_FINAL_CYCLES,
    LONGCTX_TASKSET_PATH,
    RESULTS_DIR,
    save_result,
)
from experiments.run_helpers import (
    TrialError,
    classify_trial_error,
    is_fatal_error,
    check_error_rate,
)

# ── 설정 ──
TARGET_TRIALS = 5                  # 최종 목표 trial 수
EXISTING_RESULT = RESULTS_DIR / "exp09_longctx_20260425_144412.json"
PARTIAL_PATH = RESULTS_DIR / "partial_append.json"

_TASKS_DIR = Path(__file__).resolve().parent.parent / "tasks"


def _load_tasks_with_documents() -> dict[str, dict]:
    """longctx_taskset.json 로드 + 각 task에 document 본문 추가."""
    with open(LONGCTX_TASKSET_PATH) as f:
        d = json.load(f)
    task_map: dict[str, dict] = {}
    for t in d["tasks"]:
        doc_path = _TASKS_DIR / t["document_path"]
        with open(doc_path) as f:
            t["_document"] = f.read()
        task_map[t["id"]] = t
    return task_map


def _save_partial(data: dict) -> None:
    with open(PARTIAL_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run() -> None:
    """기존 3-trial 결과에 2 trial을 추가해 5-trial JSON을 생성한다."""
    if not EXISTING_RESULT.exists():
        print(f"[ERROR] Existing result not found: {EXISTING_RESULT}")
        sys.exit(1)

    print(f"Loading existing result: {EXISTING_RESULT}")
    with open(EXISTING_RESULT) as f:
        base = json.load(f)

    # Deep copy results_by_arm (원본 보존)
    results_by_arm: dict = {
        arm_label: [dict(task_entry, trials=list(task_entry["trials"]))
                    for task_entry in task_list]
        for arm_label, task_list in base["results_by_arm"].items()
    }

    # 이미 append 중이던 체크포인트 복원
    if PARTIAL_PATH.exists():
        try:
            with open(PARTIAL_PATH) as f:
                partial = json.load(f)
            results_by_arm = partial.get("results_by_arm", results_by_arm)
            print(f"  → Resumed from checkpoint: {PARTIAL_PATH}")
        except Exception:
            print("  ⚠ Checkpoint load failed; starting from existing 3-trial base.")

    # task_map (document 포함)
    task_map = _load_tasks_with_documents()

    total_added = 0
    aborted = False
    for arm in LONGCTX_ARMS:
        if aborted:
            break
        label = arm["label"]
        for task_entry in results_by_arm[label]:
            if aborted:
                break
            tid = task_entry["task_id"]
            current_trials = len(task_entry["trials"])

            if current_trials >= TARGET_TRIALS:
                print(f"  [skip] arm={label} task={tid} (already {current_trials} trials)")
                continue

            task_obj = task_map.get(tid)
            if task_obj is None:
                print(f"  [warn] task {tid} not found in taskset; skipping")
                continue

            print(f"\n[Append] arm={label} | task={tid} ({task_entry.get('size_class')}, {task_entry.get('hop_type')})")
            for trial_idx in range(current_trials, TARGET_TRIALS):
                print(f"  Trial {trial_idx + 1}/{TARGET_TRIALS}...")
                result = _run_longctx_trial(arm, task_obj, trial_idx)
                task_entry["trials"].append(result)
                total_added += 1

                # 신규: fatal classify + abort
                err_class = classify_trial_error(result.get("error"))
                if is_fatal_error(err_class):
                    print(
                        f"[ABORT] arm={label} task={tid} trial={trial_idx} "
                        f"fatal error={err_class.value}: {str(result.get('error'))[:200]}"
                    )
                    print("[ABORT] 부분 결과는 보존. 저장 직전 error 비율 검사 진행.")
                    aborted = True
                    break

            _save_partial({
                "experiment": "longctx",
                "model": base.get("model"),
                "arms": LONGCTX_ARMS,
                "results_by_arm": results_by_arm,
            })

    # 최종 저장
    final = {
        "experiment": "longctx",
        "model": base.get("model"),
        "arms": LONGCTX_ARMS,
        "trials_per_task": TARGET_TRIALS,
        "chunk_size": LONGCTX_CHUNK_SIZE,
        "chunk_overlap": LONGCTX_CHUNK_OVERLAP,
        "rag_top_k": LONGCTX_RAG_TOP_K,
        "results_by_arm": results_by_arm,
    }

    # 저장 직전 error 비율 검사
    all_trials = [
        t
        for arm_data in final["results_by_arm"].values()
        for task_entry in arm_data
        for t in task_entry.get("trials", [])
    ]
    ok, rate = check_error_rate(all_trials, threshold=0.30)
    if not ok:
        print(f"[REJECT] error 비율 {rate:.1%} ≥ 30%. 저장 거부 + warning")
        print("[REJECT] 부분 결과는 메모리에 유지 — 사용자가 별도 처리 권고")
        raise SystemExit(1)

    out_path = save_result("exp09_longctx_5trial", final)
    print(f"\n  → 5-trial result saved: {out_path}")

    if PARTIAL_PATH.exists():
        PARTIAL_PATH.unlink()

    print(f"\n  총 추가 trial: {total_added}")
    print("APPEND COMPLETE")


if __name__ == "__main__":
    run()
