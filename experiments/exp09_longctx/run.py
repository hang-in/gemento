"""실험 9: Long-Context Stress Test (ABC vs Solo-dump vs RAG).

3 arm × 10 tasks × 3 trials = 90 runs. 체크포인트 지원.

dispatcher key: `longctx`
원본 함수: experiments/run_experiment.py:run_longctx (line 1365 in v1)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import MODEL_NAME

# experiments-task-07 rev — 자체 디렉토리의 results/ 사용
RESULTS_DIR = Path(__file__).resolve().parent / "results"
from experiments.run_helpers import classify_trial_error, is_fatal_error, check_error_rate


_TASKS_DIR = Path(__file__).resolve().parent.parent / "tasks"

LONGCTX_TRIALS = 3  # MVP
LONGCTX_TASKSET_PATH = _TASKS_DIR / "longctx_taskset.json"
LONGCTX_ARMS = [
    {"label": "solo_dump",    "description": "document 전체를 A에 단일 투입"},
    {"label": "rag_baseline", "description": "BM25 top-K chunks만 A에 투입"},
    {"label": "abc_tattoo",   "description": "ABC + Tattoo + chunk iteration"},
]
LONGCTX_CHUNK_SIZE = 500
LONGCTX_CHUNK_OVERLAP = 50
LONGCTX_RAG_TOP_K = 5
LONGCTX_MAX_FINAL_CYCLES = 5


def save_result(experiment_name: str, result: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{experiment_name}_{timestamp}.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"  → Result saved: {path}")
    return path


def _extract_answer(raw: str) -> str | None:
    """solo_dump / rag_baseline 용 final_answer 파싱."""
    from orchestrator import extract_json_from_response
    parsed = extract_json_from_response(raw)
    if parsed and isinstance(parsed, dict):
        return parsed.get("final_answer")
    return raw.strip() if raw else None


def _run_longctx_trial(arm: dict, task: dict, trial_idx: int) -> dict:
    """단일 arm × task × trial 실행. arm label에 따라 분기."""
    from tools.chunker import chunk_document
    from tools.bm25_tool import bm25_retrieve
    from orchestrator import run_abc_chunked, call_model, log_detail, extract_json_from_response

    label = arm["label"]
    question = task["question"]
    document = task["_document"]

    log_detail(f"  > Trial {trial_idx + 1} START | Arm: {label}")

    if label == "solo_dump":
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Answer based on the provided document."},
            {"role": "user", "content": f"## Document\n\n{document}\n\n## Question\n\n{question}\n\nProvide the answer as a JSON object: {{\"final_answer\": \"...\"}}."},
        ]
        final_answer = None
        error = None
        try:
            raw, _ = call_model(messages)
            parsed = extract_json_from_response(raw)
            final_answer = _extract_answer(raw)
            log_detail(f"    Solo-dump Response: {raw[:500]}...")
        except Exception as e:
            error = str(e)
            log_detail(f"    ⚠ Solo-dump Error: {error}")
        return {
            "trial": trial_idx + 1,
            "arm": label,
            "final_answer": final_answer,
            "error": error,
            "doc_word_count": len(document.split()),
        }

    elif label == "rag_baseline":
        chunks = [c.to_dict() for c in chunk_document(document, size=LONGCTX_CHUNK_SIZE, overlap=LONGCTX_CHUNK_OVERLAP)]
        top = bm25_retrieve(question, chunks, top_k=LONGCTX_RAG_TOP_K)
        top_text = "\n\n---\n\n".join(f"[chunk {c['chunk_id']}]\n{c['content']}" for c in top)
        log_detail(f"    RAG retrieved chunk IDs: {[c['chunk_id'] for c in top]}")

        messages = [
            {"role": "system", "content": "You are a helpful assistant. Answer based on the retrieved chunks."},
            {"role": "user", "content": f"## Retrieved Chunks\n\n{top_text}\n\n## Question\n\n{question}\n\nProvide the answer as a JSON object: {{\"final_answer\": \"...\"}}."},
        ]
        final_answer = None
        error = None
        try:
            raw, _ = call_model(messages)
            final_answer = _extract_answer(raw)
            log_detail(f"    RAG Response: {raw[:500]}...")
        except Exception as e:
            error = str(e)
            log_detail(f"    ⚠ RAG Error: {error}")
        return {
            "trial": trial_idx + 1,
            "arm": label,
            "final_answer": final_answer,
            "error": error,
            "retrieved_chunk_ids": [c["chunk_id"] for c in top],
            "top_k": LONGCTX_RAG_TOP_K,
        }

    elif label == "abc_tattoo":
        chunks = [c.to_dict() for c in chunk_document(document, size=LONGCTX_CHUNK_SIZE, overlap=LONGCTX_CHUNK_OVERLAP)]
        tattoo = None
        logs = []
        final_answer = None
        evidence_refs_used = []
        error = None
        try:
            tattoo, logs, final_answer = run_abc_chunked(
                task_id=f"{task['id']}_t{trial_idx}",
                question=question,
                chunks=chunks,
                max_final_cycles=LONGCTX_MAX_FINAL_CYCLES,
            )
            evidence_refs_used = [
                a.evidence_ref for a in tattoo.active_assertions if a.evidence_ref
            ]
        except Exception as e:
            error = str(e)
            log_detail(f"    ⚠ ABC Error: {error}")

        log_detail(f"    ABC Result: Answer={str(final_answer)[:100]}..., Evidence Count={len(evidence_refs_used)}")
        return {
            "trial": trial_idx + 1,
            "arm": label,
            "final_answer": final_answer,
            "error": error,
            "num_chunks": len(chunks),
            "num_assertions": len(tattoo.active_assertions) if tattoo else 0,
            "evidence_refs_used": evidence_refs_used,
        }

    raise ValueError(f"unknown arm label: {label}")


def run():
    """실험 9: Long-Context Stress Test (ABC vs Solo-dump vs RAG).

    3 arm × 10 tasks × 3 trials = 90 runs. 체크포인트 지원.
    """
    print(f"Taskset: {LONGCTX_TASKSET_PATH}")

    with open(LONGCTX_TASKSET_PATH) as f:
        d = json.load(f)
    tasks = d["tasks"]

    # document 본문 로드 (_document 키에 저장, 결과 JSON에는 저장 안 함)
    for t in tasks:
        doc_path = _TASKS_DIR / t["document_path"]
        with open(doc_path) as f:
            t["_document"] = f.read()

    partial_path = RESULTS_DIR / "partial_longctx.json"
    results: dict = {"solo_dump": [], "rag_baseline": [], "abc_tattoo": []}
    finished: set[tuple[str, str]] = set()
    if partial_path.exists():
        try:
            with open(partial_path) as f:
                partial = json.load(f)
                results = partial.get("results_by_arm", results)
                for arm_label, task_list in results.items():
                    for tr in task_list:
                        finished.add((arm_label, tr["task_id"]))
            print(f"  → Resuming: {len(finished)} (arm, task) pairs done.")
        except Exception:
            print("  ⚠ Checkpoint load failed; starting fresh.")

    aborted = False
    for arm in LONGCTX_ARMS:
        if aborted:
            break
        label = arm["label"]
        for task in tasks:
            if aborted:
                break
            if (label, task["id"]) in finished:
                print(f"  [skip] arm={label} task={task['id']}")
                continue
            print(f"\n[LongCtx] arm={label} | task={task['id']} ({task['size_class']}, {task['hop_type']})")
            task_results = []
            for trial in range(LONGCTX_TRIALS):
                print(f"  Trial {trial + 1}/{LONGCTX_TRIALS}...")
                trial_result = _run_longctx_trial(arm, task, trial)
                task_results.append(trial_result)

                err_class = classify_trial_error(trial_result.get("error"))
                if is_fatal_error(err_class):
                    print(
                        f"[ABORT] arm={label} task={task['id']} trial={trial} "
                        f"fatal={err_class.value}: {str(trial_result.get('error'))[:200]}"
                    )
                    print("[ABORT] 부분 결과는 보존. 저장 직전 error 비율 검사 진행.")
                    aborted = True
                    break

            results.setdefault(label, []).append({
                "task_id": task["id"],
                "size_class": task["size_class"],
                "hop_type": task["hop_type"],
                "expected_answer": task["expected_answer"],
                "scoring_keywords": task.get("scoring_keywords", []),
                "gold_evidence_chunks": task.get("gold_evidence_chunks", []),
                "trials": task_results,
            })
            with open(partial_path, "w", encoding="utf-8") as f:
                json.dump({
                    "experiment": "longctx",
                    "model": MODEL_NAME,
                    "arms": LONGCTX_ARMS,
                    "results_by_arm": results,
                }, f, ensure_ascii=False, indent=2)

    final = {
        "experiment": "longctx",
        "model": MODEL_NAME,
        "arms": LONGCTX_ARMS,
        "trials_per_task": LONGCTX_TRIALS,
        "chunk_size": LONGCTX_CHUNK_SIZE,
        "chunk_overlap": LONGCTX_CHUNK_OVERLAP,
        "rag_top_k": LONGCTX_RAG_TOP_K,
        "results_by_arm": results,
    }

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

    save_result("exp09_longctx", final)
    if partial_path.exists():
        partial_path.unlink()
