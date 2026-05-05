"""Exp14 Search Tool — agent-active BM25 retrieval 효과 측정.

H13 후보 가설: agent가 BM25 Search Tool을 자율 호출하면 long-context retrieval
정확도가 baseline (document 통째 포함) 대비 향상.
2 condition: baseline_abc_chunked (document 전체 prompt 포함) vs abc_search_tool (Search Tool 활성).
10 task × 2 condition × 5 trial = 100 trial.
dispatcher key: `exp14-search-tool`
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
    """Stage 2C 결함 fix — cycle-by-cycle tattoo snapshot 추출 (Exp12/Exp13/Exp14 공통 패턴)."""
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


def _extract_tool_calls(abc_logs) -> list[list[dict]]:
    """ABCCycleLog.tool_calls 를 cycle 별로 추출. mechanism 분석용 (Exp14 H13).

    Returns:
        list of cycle's tool_call_log. 각 cycle 의 tool_calls 는
        [{"name": "search_chunks", "arguments": {...}, "result": ..., "error": ...}, ...]
        호출 0회 cycle 은 빈 list.
    """
    out = []
    for entry in abc_logs:
        tc = getattr(entry, "tool_calls", None)
        if tc is None:
            out.append([])
            continue
        # result 가 dict/list 등 직렬화 가능 형식인지 확인 + truncate (chunk content 가 너무 길 수 있음)
        sanitized = []
        for call in tc:
            try:
                name = call.get("name", "?")
                args = call.get("arguments", {})
                result = call.get("result")
                err = call.get("error")
                # search_chunks 의 result 는 chunk list — content 만 truncate
                if isinstance(result, list):
                    result = [
                        {**r, "content": (r.get("content", "")[:300] + "...") if len(r.get("content", "")) > 300 else r.get("content", "")}
                        if isinstance(r, dict) else r
                        for r in result
                    ]
                sanitized.append({"name": name, "arguments": args, "result": result, "error": err})
            except Exception:
                sanitized.append({"name": str(call)[:200]})
        out.append(sanitized)
    return out


def _load_longctx_taskset(taskset_path: str) -> list[dict]:
    """longctx_taskset.json 로드. 각 task에 chunked corpus 주입."""
    from tools import chunk_document
    with open(taskset_path, "r", encoding="utf-8") as f:
        ts = json.load(f)
    tasks = ts["tasks"]
    base_dir = Path(taskset_path).parent
    for task in tasks:
        doc_path = base_dir / task["document_path"]
        with open(doc_path, "r", encoding="utf-8") as f:
            doc_text = f.read()
        chunks = chunk_document(doc_text, size=500, overlap=50)
        task["_chunks"] = [c.to_dict() for c in chunks]
    return tasks


def run_baseline_abc_chunked(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """A/B/C 모두 Gemma + Search Tool 없음. corpus는 prompt에 직접 포함."""
    start = time.time()
    final_answer = None
    error = None
    actual_cycles = 0
    tattoo = None
    abc_logs = []
    try:
        corpus_text = "\n\n".join(c["content"] for c in task["_chunks"])
        full_prompt = f"{task['question']}\n\nDocument:\n{corpus_text}"
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_baseline_chunked_t{trial_idx}",
            objective=task.get("question", ""),
            prompt=full_prompt,
            constraints=None,
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            extractor_pre_stage=False,
            reducer_post_stage=False,
            search_tool=False,
            corpus=None,
        )
        actual_cycles = len(abc_logs)
        if not final_answer:
            error = f"baseline_abc_chunked: no final_answer after {actual_cycles} cycles"
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


def run_abc_search_tool(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """A/B/C 모두 Gemma + A가 search_chunks 호출 가능."""
    start = time.time()
    final_answer = None
    error = None
    actual_cycles = 0
    tattoo = None
    abc_logs = []
    try:
        # Agent 는 document 의 존재 자체를 prompt 에서 알아야 search_chunks tool 의
        # 의미를 인식. dry-run (2026-05-05) 에서 prompt=question 만 시 외부 지식
        # 검색으로 오인 → needle task 6/6 fail. Document availability + tool 사용
        # 가이드를 prompt 에 명시.
        full_prompt = (
            f"{task['question']}\n\n"
            f"## Document context\n"
            f"A long document containing the answer is available but NOT included in this prompt. "
            f"You have access to a `search_chunks(query, top_k)` tool that performs BM25 lexical "
            f"search over this document and returns relevant chunks. Use it whenever you need "
            f"information from the document to answer the question. You may call it multiple "
            f"times with different queries to refine your search."
        )
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_search_tool_t{trial_idx}",
            objective=task.get("question", ""),
            prompt=full_prompt,
            constraints=None,
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            extractor_pre_stage=False,
            reducer_post_stage=False,
            search_tool=True,
            corpus=task["_chunks"],
        )
        actual_cycles = len(abc_logs)
        if not final_answer:
            error = f"abc_search_tool: no final_answer after {actual_cycles} cycles"
    except Exception as e:
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    tattoo_history = _extract_tattoo_history(abc_logs, tattoo)
    tool_calls_per_cycle = _extract_tool_calls(abc_logs)
    total_tool_calls = sum(len(c) for c in tool_calls_per_cycle)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": duration_ms,
        "tattoo_history": tattoo_history if tattoo_history else None,
        "tool_calls_per_cycle": tool_calls_per_cycle,
        "total_tool_calls": total_tool_calls,
    }


CONDITION_DISPATCH = {
    "baseline_abc_chunked": run_baseline_abc_chunked,
    "abc_search_tool": run_abc_search_tool,
}


def run_experiment(
    *,
    taskset_path: Path,
    trials_per_condition: int = DEFAULT_TRIALS,
    conditions: tuple[str, ...] = ("baseline_abc_chunked", "abc_search_tool"),
    max_cycles: int = DEFAULT_MAX_CYCLES,
    task_filter: tuple[str, ...] | None = None,
) -> dict:
    """전체 실험 실행 — 사용자 직접 호출 (Task 04).

    task_filter: 특정 task_id 만 실행 (None = 전체). 진단/dry-run 용.
    """
    started = _dt.datetime.now().astimezone().isoformat()

    tasks = _load_longctx_taskset(str(taskset_path))
    if task_filter:
        tasks = [t for t in tasks if t["id"] in task_filter]
        if not tasks:
            raise ValueError(f"task_filter 가 매칭되는 task 없음: {task_filter}")

    partial_path = RESULTS_DIR / "partial_exp14_search_tool.json"
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
                question_preview = str(task.get("question", ""))[:120].replace("\n", " ")
                print()
                print(f"  [{counter}/{total}] {cond} | {task['id']} ({task.get('hop_type','?')}/{task.get('size_class','?')}) | trial {trial_idx}")
                print(f"      question: {question_preview}{'...' if len(str(task.get('question',''))) > 120 else ''}")

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
                    # Exp14 mechanism 진단 — search_tool 호출 추적 (Search Tool condition 만 채워짐)
                    "tool_calls_per_cycle": result.get("tool_calls_per_cycle"),
                    "total_tool_calls": result.get("total_tool_calls"),
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
        experiment="exp14_search_tool",
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
    parser = argparse.ArgumentParser(description="Exp14 Search Tool — agent-active BM25 retrieval")
    parser.add_argument("--taskset", default="experiments/tasks/longctx_taskset.json")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--max-cycles", type=int, default=DEFAULT_MAX_CYCLES)
    parser.add_argument("--conditions", nargs="+", default=["baseline_abc_chunked", "abc_search_tool"])
    parser.add_argument("--out-name", default=None)
    parser.add_argument("--tasks", nargs="+", default=None,
                        help="특정 task_id 만 실행 (예: longctx-medium-needle-01). None = 전체")
    args = parser.parse_args()

    out = run_experiment(
        taskset_path=Path(args.taskset),
        trials_per_condition=args.trials,
        conditions=tuple(args.conditions),
        max_cycles=args.max_cycles,
        task_filter=tuple(args.tasks) if args.tasks else None,
    )

    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = args.out_name or f"exp14_search_tool_{ts}.json"
    # Auto-append .json 확장자 — --out-name 사용자가 .json 누락 시 (Exp12/13/14 패턴)
    if not name.endswith(".json"):
        name = name + ".json"
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
