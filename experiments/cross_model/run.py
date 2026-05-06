"""Stage 6 cross-model replication driver.

4 가설 (H10/H11/H12/H13) × 3 모델 (Local Qwen 2.5 7B / Groq Llama 3.1 8B / Groq Llama 3.3 70B)
재현. model_caller hook 으로 외부 모델 주입. LLM-as-judge 보조 채점 옵션 지원.

Usage:
  .venv/Scripts/python -m experiments.cross_model.run --model llama_3_1_8b_groq --hypothesis h11 h12
  .venv/Scripts/python -m experiments.cross_model.run --model llama_3_3_70b_groq --hypothesis h13 --judge
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Callable

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments._external.groq_client import (
    call_with_meter_retry,
    LLAMA_3_1_8B,
    LLAMA_3_3_70B,
)
from experiments._external.llm_judge import compare_answers
from experiments.measure import score_answer_v3
from experiments.orchestrator import run_abc_chain
from experiments.run_helpers import (
    classify_trial_error,
    is_fatal_error,
    check_error_rate,
    build_result_meta,
    get_taskset_version,
    normalize_sampling_params,
)
from experiments.config import SAMPLING_PARAMS

RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_TRIALS = 5
DEFAULT_MAX_CYCLES = 8
STANDARD_TASKSET_PATH = "experiments/tasks/taskset.json"
LONGCTX_TASKSET_PATH = "experiments/tasks/longctx_taskset.json"

LOCAL_QWEN_ENDPOINT = "http://localhost:1235"
LOCAL_QWEN_MODEL_ID = "qwen-2.5-7b-q4"

MODELS: dict[str, dict] = {
    "qwen_25_7b_local": {
        "provider": "lm_studio_local",
        "endpoint": LOCAL_QWEN_ENDPOINT,
        "model_id": LOCAL_QWEN_MODEL_ID,
        "context": 32768,
        "supports_longctx": True,
    },
    "llama_3_1_8b_groq": {
        "provider": "groq",
        "model_id": LLAMA_3_1_8B,
        "context": 8192,
        "supports_longctx": False,
    },
    "llama_3_3_70b_groq": {
        "provider": "groq",
        "model_id": LLAMA_3_3_70B,
        "context": 131072,
        "supports_longctx": True,
    },
}

HYPOTHESIS_META: dict[str, dict] = {
    "h10": {
        "taskset": "standard",
        "conditions": ["baseline_abc", "cross_c_judge"],
        "judge_eligible": False,
    },
    "h11": {
        "taskset": "standard",
        "conditions": ["baseline_abc", "extractor_abc"],
        "judge_eligible": False,
    },
    "h12": {
        "taskset": "standard",
        "conditions": ["baseline_abc", "reducer_abc"],
        "judge_eligible": True,
    },
    "h13": {
        "taskset": "longctx",
        "conditions": ["baseline_abc_chunked", "abc_search_tool"],
        "judge_eligible": True,
    },
}


# ── Model caller factories ────────────────────────────────────────────────────

# Groq free tier: 30 RPM = 1 call / 2sec. ABC chain bursts (A→B→C in same cycle)
# 즉시 429 storm → exponential backoff 로 인한 대기 시간 폭증. Preventive throttle:
# 매 호출 *전* 에 min interval 보장.
# 2026-05-06 v1: 2.5s 시도 → cycle 2 에서 rate limit 재발. Extractor pre-stage 의
# A 호출이 cycle 시작 직후 burst → 5.0s (= 12 RPM) 로 상향, 30 RPM 한도 안전 마진 큼.
GROQ_MIN_CALL_INTERVAL_SEC = 5.0
_groq_last_call_ts: dict[str, float] = {}  # per-model 마지막 호출 시각


def make_groq_caller(model_id: str) -> Callable:
    """Groq API → model_caller signature: (messages, tools=None, **kwargs) → (str, dict).

    Preventive throttle: 직전 호출 후 GROQ_MIN_CALL_INTERVAL_SEC 미경과 시 sleep.
    per-model 별도 추적 (다른 모델 동시 호출 가능).
    """
    def _caller(messages: list[dict], tools=None, **kwargs) -> tuple[str, dict]:
        # Preventive throttle — 호출 전 minimum interval 보장
        now = time.time()
        last = _groq_last_call_ts.get(model_id, 0.0)
        elapsed = now - last
        if elapsed < GROQ_MIN_CALL_INTERVAL_SEC:
            time.sleep(GROQ_MIN_CALL_INTERVAL_SEC - elapsed)
        _groq_last_call_ts[model_id] = time.time()

        result = call_with_meter_retry(messages, model=model_id, tools=tools, **kwargs)
        meta = {
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "duration_ms": result.duration_ms,
            "cost_usd": result.cost_usd,
            "error": result.error,
            "reasoning_tokens": result.reasoning_tokens,
        }
        return result.raw_response, meta
    return _caller


def make_local_caller(endpoint: str, model_id: str) -> Callable:
    """LM Studio OpenAI-compatible local endpoint caller (no API key needed).

    endpoint: e.g. "http://localhost:1235" (no trailing slash, no /v1 suffix)
    model_id: model identifier as returned by /v1/models
    """
    url = endpoint.rstrip("/") + "/v1/chat/completions"

    def _caller(messages: list[dict], tools=None, temperature: float = 0.1,
                max_tokens: int = 4096, **kwargs) -> tuple[str, dict]:
        payload: dict = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
        headers = {"Content-Type": "application/json"}
        start = time.time()
        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            duration_ms = int((time.time() - start) * 1000)
            return "", {"error": str(exc), "duration_ms": duration_ms,
                        "input_tokens": 0, "output_tokens": 0,
                        "cost_usd": 0.0, "reasoning_tokens": 0}
        duration_ms = int((time.time() - start) * 1000)
        content = ""
        choices = data.get("choices") or []
        if choices:
            content = (choices[0].get("message") or {}).get("content") or ""
        usage = data.get("usage") or {}
        meta = {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "duration_ms": duration_ms,
            "cost_usd": 0.0,
            "error": None,
            "reasoning_tokens": 0,
        }
        return content, meta

    return _caller


def _get_model_caller(model_key: str) -> Callable:
    cfg = MODELS[model_key]
    if cfg["provider"] == "groq":
        return make_groq_caller(cfg["model_id"])
    return make_local_caller(cfg["endpoint"], cfg["model_id"])


# ── Shared helpers ────────────────────────────────────────────────────────────

def _extract_tattoo_history(abc_logs: list, fallback_tattoo) -> list:
    history = []
    for entry in abc_logs:
        if hasattr(entry, "tattoo_snapshot"):
            snap = entry.tattoo_snapshot
            history.append(snap.to_dict() if hasattr(snap, "to_dict") else snap)
        elif hasattr(entry, "a_log") and hasattr(entry.a_log, "tattoo_out"):
            out = entry.a_log.tattoo_out
            history.append(out if isinstance(out, dict) else out.to_dict())
        elif hasattr(entry, "tattoo_out"):
            out = entry.tattoo_out
            history.append(out if isinstance(out, dict) else out.to_dict())
        elif isinstance(entry, dict) and "tattoo" in entry:
            history.append(entry["tattoo"])
    if not history and fallback_tattoo:
        history = [fallback_tattoo.to_dict()]
    return history


def _load_longctx_tasks(taskset_path: str) -> list[dict]:
    from experiments.tools import chunk_document
    with open(taskset_path, encoding="utf-8") as f:
        ts = json.load(f)
    tasks = ts["tasks"]
    base_dir = Path(taskset_path).parent
    for task in tasks:
        doc_path = base_dir / task["document_path"]
        with open(doc_path, encoding="utf-8") as f:
            doc_text = f.read()
        chunks = chunk_document(doc_text, size=500, overlap=50)
        task["_chunks"] = [c.to_dict() for c in chunks]
    return tasks


# ── Condition-level run functions ─────────────────────────────────────────────

def _run_baseline_abc(task: dict, trial_idx: int, max_cycles: int,
                      task_id_suffix: str = "baseline_abc") -> dict:
    """All-Gemma baseline — no model_caller, no pre/post stage hooks."""
    start = time.time()
    final_answer = error = None
    actual_cycles = 0
    tattoo = abc_logs = None
    abc_logs = []
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_{task_id_suffix}_t{trial_idx}",
            objective=task.get("objective", task.get("question", "")),
            prompt=task.get("prompt", task.get("question", "")),
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            extractor_pre_stage=False,
            reducer_post_stage=False,
        )
        actual_cycles = len(abc_logs)
        if not final_answer:
            error = f"{task_id_suffix}: no final_answer after {actual_cycles} cycles"
    except Exception as exc:
        error = str(exc)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": int((time.time() - start) * 1000),
        "tattoo_history": _extract_tattoo_history(abc_logs, tattoo) or None,
    }


def _run_cross_c_judge(task: dict, trial_idx: int, max_cycles: int,
                       c_caller: Callable) -> dict:
    """H10: Gemma A/B + external model as C-judge (c_caller). A/B stay on local Gemma."""
    start = time.time()
    final_answer = error = None
    actual_cycles = 0
    tattoo = None
    abc_logs = []
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_cross_c_judge_t{trial_idx}",
            objective=task.get("objective", task.get("question", "")),
            prompt=task.get("prompt", task.get("question", "")),
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            c_caller=c_caller,
        )
        actual_cycles = len(abc_logs)
        if not final_answer:
            error = f"cross_c_judge: no final_answer after {actual_cycles} cycles"
    except Exception as exc:
        error = str(exc)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": int((time.time() - start) * 1000),
        "tattoo_history": _extract_tattoo_history(abc_logs, tattoo) or None,
    }


def _run_cm_baseline(task: dict, trial_idx: int, max_cycles: int,
                     model_caller: Callable, task_id_suffix: str = "cm_baseline") -> dict:
    """Cross-model baseline: all A/B/C via model_caller, no hooks."""
    start = time.time()
    final_answer = error = None
    actual_cycles = 0
    tattoo = None
    abc_logs = []
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_{task_id_suffix}_t{trial_idx}",
            objective=task.get("objective", task.get("question", "")),
            prompt=task.get("prompt", task.get("question", "")),
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            extractor_pre_stage=False,
            reducer_post_stage=False,
            model_caller=model_caller,
        )
        actual_cycles = len(abc_logs)
        if not final_answer:
            error = f"{task_id_suffix}: no final_answer after {actual_cycles} cycles"
    except Exception as exc:
        error = str(exc)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": int((time.time() - start) * 1000),
        "tattoo_history": _extract_tattoo_history(abc_logs, tattoo) or None,
    }


def _run_cm_extractor(task: dict, trial_idx: int, max_cycles: int,
                      model_caller: Callable) -> dict:
    """H11 treatment: external model_caller + extractor_pre_stage=True."""
    start = time.time()
    final_answer = error = None
    actual_cycles = 0
    tattoo = None
    abc_logs = []
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_cm_extractor_t{trial_idx}",
            objective=task.get("objective", task.get("question", "")),
            prompt=task.get("prompt", task.get("question", "")),
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            extractor_pre_stage=True,
            reducer_post_stage=False,
            model_caller=model_caller,
        )
        actual_cycles = len(abc_logs)
        if not final_answer:
            error = f"cm_extractor: no final_answer after {actual_cycles} cycles"
    except Exception as exc:
        error = str(exc)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": int((time.time() - start) * 1000),
        "tattoo_history": _extract_tattoo_history(abc_logs, tattoo) or None,
    }


def _run_cm_reducer(task: dict, trial_idx: int, max_cycles: int,
                    model_caller: Callable) -> dict:
    """H12 treatment: external model_caller + reducer_post_stage=True."""
    start = time.time()
    final_answer = error = None
    actual_cycles = 0
    tattoo = None
    abc_logs = []
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_cm_reducer_t{trial_idx}",
            objective=task.get("objective", task.get("question", "")),
            prompt=task.get("prompt", task.get("question", "")),
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            extractor_pre_stage=False,
            reducer_post_stage=True,
            model_caller=model_caller,
        )
        actual_cycles = len(abc_logs)
        if not final_answer:
            error = f"cm_reducer: no final_answer after {actual_cycles} cycles"
    except Exception as exc:
        error = str(exc)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": int((time.time() - start) * 1000),
        "tattoo_history": _extract_tattoo_history(abc_logs, tattoo) or None,
    }


def _run_cm_baseline_chunked(task: dict, trial_idx: int, max_cycles: int,
                              model_caller: Callable) -> dict:
    """H13 baseline: external model_caller + full document text in prompt."""
    corpus_text = "\n\n".join(c["content"] for c in task["_chunks"])
    full_prompt = f"{task['question']}\n\nDocument:\n{corpus_text}"
    start = time.time()
    final_answer = error = None
    actual_cycles = 0
    tattoo = None
    abc_logs = []
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_cm_baseline_chunked_t{trial_idx}",
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
            model_caller=model_caller,
        )
        actual_cycles = len(abc_logs)
        if not final_answer:
            error = f"cm_baseline_chunked: no final_answer after {actual_cycles} cycles"
    except Exception as exc:
        error = str(exc)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": int((time.time() - start) * 1000),
        "tattoo_history": _extract_tattoo_history(abc_logs, tattoo) or None,
    }


def _run_cm_search_tool(task: dict, trial_idx: int, max_cycles: int,
                        model_caller: Callable) -> dict:
    """H13 treatment: external model_caller + BM25 search_tool=True."""
    full_prompt = (
        f"{task['question']}\n\n"
        f"## Document context\n"
        f"A long document containing the answer is available but NOT included in this prompt. "
        f"You have access to a `search_chunks(query, top_k)` tool that performs BM25 lexical "
        f"search over this document and returns relevant chunks. Use it whenever you need "
        f"information from the document to answer the question. You may call it multiple "
        f"times with different queries to refine your search."
    )
    start = time.time()
    final_answer = error = None
    actual_cycles = 0
    tattoo = None
    abc_logs = []
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_cm_search_tool_t{trial_idx}",
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
            model_caller=model_caller,
        )
        actual_cycles = len(abc_logs)
        if not final_answer:
            error = f"cm_search_tool: no final_answer after {actual_cycles} cycles"
    except Exception as exc:
        error = str(exc)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": int((time.time() - start) * 1000),
        "tattoo_history": _extract_tattoo_history(abc_logs, tattoo) or None,
    }


# ── Top-level reproduce functions (plan verification targets) ─────────────────

def reproduce_h10_mixed(model_key: str, task: dict, trial_idx: int,
                        max_cycles: int, condition: str) -> dict:
    """H10 cross-model: baseline_abc (all Gemma) vs cross_c_judge (Gemma A/B + external C).

    c_caller carries external model as C-judge; A/B stay on local Gemma.
    model_caller not used (mutually exclusive with c_caller).
    """
    if condition == "baseline_abc":
        return _run_baseline_abc(task, trial_idx, max_cycles, "h10_baseline_abc")
    elif condition == "cross_c_judge":
        c_caller = _get_model_caller(model_key)
        return _run_cross_c_judge(task, trial_idx, max_cycles, c_caller)
    raise ValueError(f"Unknown h10 condition: {condition}")


def reproduce_h11_extractor(model_key: str, task: dict, trial_idx: int,
                             max_cycles: int, condition: str) -> dict:
    """H11 cross-model: baseline_abc vs extractor_abc — both with model_caller."""
    model_caller = _get_model_caller(model_key)
    if condition == "baseline_abc":
        return _run_cm_baseline(task, trial_idx, max_cycles, model_caller, "h11_cm_baseline")
    elif condition == "extractor_abc":
        return _run_cm_extractor(task, trial_idx, max_cycles, model_caller)
    raise ValueError(f"Unknown h11 condition: {condition}")


def reproduce_h12_reducer(model_key: str, task: dict, trial_idx: int,
                           max_cycles: int, condition: str) -> dict:
    """H12 cross-model: baseline_abc vs reducer_abc — both with model_caller + reducer_post_stage."""
    model_caller = _get_model_caller(model_key)
    if condition == "baseline_abc":
        return _run_cm_baseline(task, trial_idx, max_cycles, model_caller, "h12_cm_baseline")
    elif condition == "reducer_abc":
        return _run_cm_reducer(task, trial_idx, max_cycles, model_caller)
    raise ValueError(f"Unknown h12 condition: {condition}")


def reproduce_h13_search(model_key: str, task: dict, trial_idx: int,
                          max_cycles: int, condition: str) -> dict:
    """H13 cross-model: baseline_abc_chunked vs abc_search_tool — both with model_caller.

    corpus loaded via task['_chunks'] (injected by _load_longctx_tasks).
    search_tool=True injects BM25 SEARCH_TOOL_SCHEMA into A-agent.
    """
    model_caller = _get_model_caller(model_key)
    if condition == "baseline_abc_chunked":
        return _run_cm_baseline_chunked(task, trial_idx, max_cycles, model_caller)
    elif condition == "abc_search_tool":
        return _run_cm_search_tool(task, trial_idx, max_cycles, model_caller)
    raise ValueError(f"Unknown h13 condition: {condition}")


_REPRODUCE_DISPATCH = {
    "h10": reproduce_h10_mixed,
    "h11": reproduce_h11_extractor,
    "h12": reproduce_h12_reducer,
    "h13": reproduce_h13_search,
}


# ── LLM-as-judge pass ─────────────────────────────────────────────────────────

def _run_judge_pass(trials_data: list[dict], hypothesis: str, seed: int = 42) -> None:
    """Compare baseline vs treatment answers via GPT-OSS 120B judge (in-place update).

    Only for hypotheses with judge_eligible=True (H12/H13).
    order randomization seeded for reproducibility.
    """
    meta = HYPOTHESIS_META[hypothesis]
    if not meta["judge_eligible"]:
        return
    baseline_cond, treatment_cond = meta["conditions"]
    rng = random.Random(seed)

    baseline_map = {
        (t["task_id"], t["trial_idx"]): t
        for t in trials_data if t["condition"] == baseline_cond
    }
    treatment_map = {
        (t["task_id"], t["trial_idx"]): t
        for t in trials_data if t["condition"] == treatment_cond
    }

    pairs = sorted(set(baseline_map) & set(treatment_map))
    print(f"\n  [judge] Running LLM-as-judge on {len(pairs)} pairs (H={hypothesis.upper()}) ...")
    for key in pairs:
        base_t = baseline_map[key]
        treat_t = treatment_map[key]
        q = base_t.get("task_question", "")
        exp = base_t.get("task_expected_answer", "")
        base_ans = base_t.get("final_answer", "") or ""
        treat_ans = treat_t.get("final_answer", "") or ""

        if rng.random() < 0.5:
            answer_A, answer_B = base_ans, treat_ans
            order = "baseline_A_treatment_B"
        else:
            answer_A, answer_B = treat_ans, base_ans
            order = "treatment_A_baseline_B"

        verdict = compare_answers(q, exp, answer_A, answer_B)
        shared = {**verdict, "judge_order": order, "judge_seed": seed}
        base_t["judge_verdict"] = {**shared, "role": "baseline"}
        treat_t["judge_verdict"] = {**shared, "role": "treatment"}
        time.sleep(1.5)


# ── Main orchestrator ─────────────────────────────────────────────────────────

def run_experiment(
    *,
    model_key: str,
    hypotheses: list[str],
    trials_per_condition: int = DEFAULT_TRIALS,
    max_cycles: int = DEFAULT_MAX_CYCLES,
    task_filter: list[str] | None = None,
    out_name: str | None = None,
    run_judge: bool = False,
    standard_taskset_path: str = STANDARD_TASKSET_PATH,
    longctx_taskset_path: str = LONGCTX_TASKSET_PATH,
) -> dict:
    """Run cross-model replication experiment for given model and hypotheses.

    Supports checkpoint/resume via partial JSON. Error rate gate (30% abort).
    """
    started = _dt.datetime.now().astimezone().isoformat()
    model_cfg = MODELS[model_key]

    # Load tasksets
    with open(standard_taskset_path, encoding="utf-8") as f:
        std_tasks = json.load(f)["tasks"]
    longctx_tasks: list[dict] | None = None

    partial_name = f"partial_stage6_{model_key}.json"
    partial_path = RESULTS_DIR / partial_name
    trials_data: list[dict] = []
    finished: set[tuple[str, str, str, int]] = set()

    if partial_path.exists():
        try:
            with open(partial_path, encoding="utf-8") as f:
                partial = json.load(f)
                trials_data = partial.get("trials", [])
                for t in trials_data:
                    finished.add((t["hypothesis"], t["condition"], t["task_id"], t["trial_idx"]))
            print(f"  → Resuming: {len(finished)} trials done.")
        except Exception:
            print("  ⚠ Checkpoint load failed; starting fresh.")
            trials_data = []

    aborted = False

    for hyp in hypotheses:
        if aborted:
            break
        meta = HYPOTHESIS_META[hyp]
        conditions = meta["conditions"]
        taskset_type = meta["taskset"]

        # Llama 3.1 8B longctx skip
        if taskset_type == "longctx" and not model_cfg["supports_longctx"]:
            print(f"\n  [SKIP] {hyp.upper()}: model {model_key} does not support longctx (context={model_cfg['context']})")
            continue

        if taskset_type == "longctx":
            if longctx_tasks is None:
                longctx_tasks = _load_longctx_tasks(longctx_taskset_path)
            tasks = longctx_tasks
        else:
            tasks = std_tasks

        if task_filter:
            tasks = [t for t in tasks if t["id"] in task_filter]
            if not tasks:
                print(f"  [WARN] task_filter yielded 0 tasks for {hyp} — skipping")
                continue

        reproduce_fn = _REPRODUCE_DISPATCH[hyp]
        total = len(conditions) * len(tasks) * trials_per_condition
        counter = sum(
            1 for t in trials_data
            if t["hypothesis"] == hyp
        )

        print()
        print("=" * 80)
        print(f"  HYPOTHESIS: {hyp.upper()}  model={model_key}  (max_cycles={max_cycles}, trials_per_task={trials_per_condition})")
        print("=" * 80)

        for cond in conditions:
            if aborted:
                break
            for task in tasks:
                if aborted:
                    break
                for trial_idx in range(trials_per_condition):
                    key = (hyp, cond, task["id"], trial_idx)
                    if key in finished:
                        continue
                    counter += 1
                    q_preview = str(task.get("prompt", task.get("question", "")))[:100].replace("\n", " ")
                    print(f"\n  [{counter}/{total}] {hyp.upper()} | {cond} | {task['id']} | trial {trial_idx}")
                    print(f"      q: {q_preview}{'...' if len(q_preview) == 100 else ''}")

                    result = reproduce_fn(model_key, task, trial_idx, max_cycles, cond)
                    final = result.get("final_answer") or ""
                    acc = score_answer_v3(str(final), task)
                    err = result.get("error")
                    verdict = "✓" if acc >= 0.5 else ("✗" if acc == 0 else "△")
                    print(
                        f"      → {verdict} acc={acc:.2f}"
                        + (f"  cycles={result.get('cycles')}" if result.get("cycles") is not None else "")
                        + (f"  dur={result.get('duration_ms')}ms" if result.get("duration_ms") else "")
                        + (f"  err={str(err)[:60]}" if err else "")
                    )

                    trial_row: dict = {
                        "hypothesis": hyp,
                        "condition": cond,
                        "model_key": model_key,
                        "task_id": task["id"],
                        "trial_idx": trial_idx,
                        "task_question": task.get("prompt", task.get("question", "")),
                        "task_expected_answer": task.get("expected_answer", ""),
                        "final_answer": str(final)[:500] if final else None,
                        "accuracy_v3": acc,
                        "cycles": result.get("cycles"),
                        "duration_ms": result.get("duration_ms"),
                        "error": err,
                        "tattoo_history": result.get("tattoo_history"),
                    }
                    trials_data.append(trial_row)
                    finished.add(key)

                    err_cls = classify_trial_error(err)
                    if is_fatal_error(err_cls):
                        print(f"[ABORT] fatal={err_cls.value}: {str(err)[:200]}")
                        aborted = True
                        break

                    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
                    with open(partial_path, "w", encoding="utf-8") as f:
                        json.dump({"trials": trials_data}, f, ensure_ascii=False, indent=2)

    ok, rate = check_error_rate(trials_data, threshold=0.30)
    if not ok:
        print(f"[REJECT] error rate {rate:.1%} ≥ 30%. 저장 거부.")
        raise SystemExit(1)

    if run_judge:
        for hyp in hypotheses:
            _run_judge_pass(trials_data, hyp)

    ended = _dt.datetime.now().astimezone().isoformat()

    meta_out = build_result_meta(
        experiment="stage6_cross_model",
        model_name=model_cfg["model_id"],
        model_engine=model_cfg["provider"],
        model_endpoint=model_cfg.get("endpoint", "groq"),
        sampling_params=normalize_sampling_params(SAMPLING_PARAMS),
        scorer_version="v3",
        taskset_version=get_taskset_version(),
        started_at=started,
        ended_at=ended,
    )

    out = {
        **meta_out,
        "model_key": model_key,
        "hypotheses": hypotheses,
        "trials_per_condition": trials_per_condition,
        "max_cycles": max_cycles,
        "run_judge": run_judge,
        "trials": trials_data,
    }

    if partial_path.exists():
        partial_path.unlink()

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 6 cross-model replication")
    parser.add_argument("--model", required=True, choices=list(MODELS.keys()),
                        help="대상 모델 (qwen_25_7b_local / llama_3_1_8b_groq / llama_3_3_70b_groq)")
    parser.add_argument("--hypothesis", nargs="+", required=True,
                        choices=["h10", "h11", "h12", "h13"],
                        help="재현할 Stage 5 가설 (복수 지정 가능)")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--max-cycles", type=int, default=DEFAULT_MAX_CYCLES)
    parser.add_argument("--tasks", nargs="+", default=None,
                        help="task_id filter (None = 전체)")
    parser.add_argument("--out-name", default=None,
                        help="출력 파일명 (없으면 자동 생성)")
    parser.add_argument("--judge", action="store_true",
                        help="LLM-as-judge 보조 채점 활성 (H12/H13 권장)")
    parser.add_argument("--standard-taskset", default=STANDARD_TASKSET_PATH)
    parser.add_argument("--longctx-taskset", default=LONGCTX_TASKSET_PATH)
    args = parser.parse_args()

    out = run_experiment(
        model_key=args.model,
        hypotheses=args.hypothesis,
        trials_per_condition=args.trials,
        max_cycles=args.max_cycles,
        task_filter=args.tasks,
        out_name=args.out_name,
        run_judge=args.judge,
        standard_taskset_path=args.standard_taskset,
        longctx_taskset_path=args.longctx_taskset,
    )

    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    hyp_tag = "_".join(args.hypothesis)
    name = args.out_name or f"stage6_{args.model}_{hyp_tag}_{ts}.json"
    if not name.endswith(".json"):
        name += ".json"
    out_path = RESULTS_DIR / name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n  → Result saved: {out_path}")

    agg: dict = defaultdict(lambda: {"n": 0, "v3": 0.0})
    for t in out["trials"]:
        k = f"{t['hypothesis']}|{t['condition']}"
        agg[k]["n"] += 1
        agg[k]["v3"] += t.get("accuracy_v3", 0)

    print()
    print("=== condition aggregate (v3) ===")
    for k, stat in sorted(agg.items()):
        mean = stat["v3"] / stat["n"] if stat["n"] else 0
        print(f"  {k:40} n={stat['n']:4} mean_acc={mean:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
