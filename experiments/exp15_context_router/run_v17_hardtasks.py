"""Exp17 — e4b + mandatory router 진짜 상한 (hard debugging tasks).

지금까지 needle 은 한 줄에 3요소가 다 있어 grep 한 방이면 끝. 실제 디버깅은 여러 줄 상관·
여러 발견 집계·distractor 판별이 필요. retrieval 은 풀렸으니 이제 e4b 의 *추론* 한계를 본다.

태스크 (난이도 상승, ~23K tok + distractor):
  1. multihop2  — config 라인 + 멀리 떨어진 error 라인 상관
  2. multihop3  — 3-hop 인과 사슬 (config→warning→fatal)
  3. multineedle— 흩어진 3개 실패 전부 나열 (조기종료 스트레스, 부분점수)
  4. distractor — 비슷한 import 줄 중 진짜 root cause 1개만 판별

조건: 각 task × {baseline(plain, 1시도), stack(mandatory + retry-on-None K=2)} × n=8.
고정: gemma4:e4b, router, num_ctx=32768. 공유 코드 불변 (side 브랜치).
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from tools.context_tools import get_redis_client
from orchestrator import run_abc_chain
from native_ollama_caller import make_ollama_native_caller

BASE_URL = "http://127.0.0.1:11435"
MODEL = "gemma4:e4b"
NUM_CTX = 32768
N_TRIALS = 8
MAX_CYCLES = 5
MAX_RETRIES = 2
N_LINES = 1800   # ~23K tok

_DIR = Path(__file__).resolve().parent
RESULTS_DIR = _DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULTS_DIR / "exp17_hardtasks_gemma4_e4b.json"

MANDATORY_BLOCK = (
    "\n\n## MANDATORY TOOL-USE RULES (must follow):\n"
    "1. You MUST call `grep_context` on the given handle BEFORE answering. Do NOT answer from memory.\n"
    "2. The raw log is NOT in your prompt — you can only see it via the tools. Grep for relevant markers (error, FAILED, WARN, config keys, filenames).\n"
    "3. Do NOT conclude after a single query. If the task needs multiple findings or correlation across lines, issue MULTIPLE greps and read the surrounding regions before answering. Do not stop at the first match.\n"
    "4. Transcribe exact identifiers (file paths, line numbers, names) verbatim from the matching lines into your final_answer. Report ALL required items.\n"
)


def _filler(i: int) -> str:
    return f"[INFO] 2026-06-30 10:15:{i % 60:02d} svc=api req={i} latency_ms={(i * 7) % 50} status=ok"


def _build_tasks():
    tasks = {}

    # 1. multihop2 — config@200 + error@1400 (distractors: other configs/errors)
    L = [_filler(i) for i in range(1, N_LINES + 1)]
    L[120] = "[CONFIG] http.timeout=30s (default)"
    L[160] = "[CONFIG] db.pool_size=10 (from env DB_POOL)"
    L[200] = "[CONFIG] cache.max_entries=0 (overridden by env CACHE_MAX)"
    L[900] = "[WARN] slow request 1200ms on /report (non-fatal)"
    L[1400] = "ERROR: cache insert failed: capacity is 0 at internal/cache/store.go:142"
    L[1600] = "[WARN] retry scheduled for /report"
    tasks["multihop2"] = dict(
        lines=L[:],
        objective="Find the ROOT-CAUSE config setting and the exact file:line where the resulting error surfaced. Correlate the config with the error.",
        keywords=[["max_entries"], ["store.go"], ["142"]],
    )

    # 2. multihop3 — config@150 → warn@900 → fatal@1700
    L = [_filler(i) for i in range(1, N_LINES + 1)]
    L[150] = "[CONFIG] tls.min_version=1.0 (deprecated)"
    L[500] = "[CONFIG] tls.cipher=AES256 (ok)"
    L[900] = "[WARN] handshake downgraded due to tls.min_version=1.0"
    L[1700] = "FATAL: peer rejected connection (insecure TLS) at net/tls_handshake.rs:88"
    tasks["multihop3"] = dict(
        lines=L[:],
        objective="Trace the causal chain: which config setting led, via a downgrade warning, to the fatal connection failure? Report the root config key and the file:line of the FATAL.",
        keywords=[["min_version"], ["tls_handshake.rs"], ["88"]],
    )

    # 3. multineedle — 3 scattered FAILED tests, must list all
    L = [_filler(i) for i in range(1, N_LINES + 1)]
    L[300] = "FAILED test_auth_login (AssertionError: expected 200 got 401)"
    L[800] = "FAILED test_payment_charge (KeyError: 'amount')"
    L[1500] = "FAILED test_cart_total (TypeError: NoneType has no len)"
    L[1750] = "Ran 312 tests, 3 failures"
    tasks["multineedle"] = dict(
        lines=L[:],
        objective="List the names of ALL failing tests in this log (there are several, scattered). Report every one.",
        keywords=[["test_auth_login"], ["test_payment_charge"], ["test_cart_total"]],
    )

    # 4. distractor — true error@1200 (E0432) vs warnings/notes (non-fatal)
    L = [_filler(i) for i in range(1, N_LINES + 1)]
    L[150] = "warning: unused import `std::fmt` in src/util.rs:3"
    L[600] = "note: unresolved import in tests/mock.rs:9 (cfg(test), non-fatal)"
    L[1200] = "error[E0432]: unresolved import `crate::auth::TokenStore` in src/server.rs:51"
    L[1400] = "warning: unresolved import `std::io` hint in src/util.rs:88 (auto-fixable)"
    L[1750] = "error: aborting due to previous error (src/server.rs)"
    tasks["distractor"] = dict(
        lines=L[:],
        objective="Several import-related messages appear, but only ONE is the fatal build error (E0432) that aborted the build. Find that one: its file, line, and the unresolved import name. Ignore warnings/notes.",
        keywords=[["src/server.rs"], ["51"], ["TokenStore"]],
    )
    return tasks


def _synth(tattoo):
    try:
        parts = [str(getattr(a, "content", "")) for a in tattoo.active_assertions if getattr(a, "content", None)]
    except Exception:
        parts = []
    return " \n ".join(parts) if parts else None


def _score(text, keyword_groups) -> float:
    """부분점수 = 만족 그룹 / 전체. multi-needle 은 items_found/N."""
    if not text:
        return 0.0
    if not isinstance(text, str):
        text = json.dumps(text, ensure_ascii=False) if isinstance(text, dict) else str(text)
    low = text.lower()
    return sum(1 for grp in keyword_groups if all(t.lower() in low for t in grp)) / len(keyword_groups)


def _run_once(redis_key, prompt):
    stats = {}
    caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX, stats=stats)
    tattoo, logs, ans = run_abc_chain(
        task_id="exp17", objective="(see prompt)", prompt=prompt,
        constraints=["요구된 모든 항목을 정확히 기재하라"],
        max_cycles=MAX_CYCLES, model_caller=caller,
        context_router=True, error_blocks=False, context_handles=[redis_key],
    )
    synth = _synth(tattoo)
    scored = " \n ".join([p for p in [ans if isinstance(ans, str) else (json.dumps(ans, ensure_ascii=False) if ans else None), synth] if p])
    return ans, scored, stats.get("tool_rounds", 0)


def _healthcheck():
    try:
        with httpx.Client(timeout=30) as c:
            names = [m.get("name") for m in c.get(BASE_URL.rstrip("/") + "/api/tags").json().get("models", [])]
        if MODEL not in names:
            print(f"  [ABORT] {MODEL} missing {names}"); return False
        print(f"  [Healthcheck] OK {names}"); return True
    except Exception as e:
        print(f"  [ABORT] {e}"); return False


def main():
    print("=" * 80)
    print(f"Exp17 hard tasks — {MODEL} router, baseline vs mandatory+retry × n={N_TRIALS}")
    print("=" * 80)
    if not _healthcheck():
        sys.exit(1)

    r = get_redis_client()
    tasks = _build_tasks()
    results = {"experiment": "exp17_hard_tasks", "model": MODEL, "num_ctx": NUM_CTX,
               "n_trials": N_TRIALS, "max_retries": MAX_RETRIES, "n_lines": N_LINES, "results": {}}
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
            if prev.get("results"):
                results["results"] = prev["results"]; print(f"  [Resume] {OUT_PATH.name}")
        except Exception as e:
            print(f"  [Resume] fresh ({e})")

    def _done(tid, arm):
        c = results["results"].get(tid, {}).get(arm)
        return bool(c and len(c.get("scores", [])) == N_TRIALS)

    t0 = time.time()
    for tid, spec in tasks.items():
        log_content = "\n".join(spec["lines"])
        redis_key = f"ctx:exp17_{tid}:stdout"
        r.set(redis_key, log_content)
        print(f"\n{'#'*60}\n# TASK {tid} (~{len(log_content)//4} tok)\n{'#'*60}")
        cell = results["results"].setdefault(tid, {"approx_tokens": len(log_content) // 4})
        base_prompt = (f"A failure occurred. The raw log is cached in Redis.\nContext Handle: {redis_key}\n\n" + spec["objective"])

        for arm in ("baseline", "stack"):
            if _done(tid, arm):
                print(f"  [skip] {tid} {arm} mean={cell[arm]['mean_score']:.0%}"); continue
            prompt = base_prompt + (MANDATORY_BLOCK if arm == "stack" else "")
            max_tries = (MAX_RETRIES + 1) if arm == "stack" else 1
            scores, attempts_list, tr_list = [], [], []
            for trial in range(1, N_TRIALS + 1):
                attempts = 0; final_scored = None; tr_total = 0
                while attempts < max_tries:
                    attempts += 1
                    ans, scored, tr = _run_once(redis_key, prompt)
                    tr_total += tr; final_scored = scored
                    if ans:   # stack: stop on non-None; baseline: max_tries=1 anyway
                        break
                s = _score(final_scored, spec["keywords"])
                scores.append(s); attempts_list.append(attempts); tr_list.append(tr_total)
                print(f"  [{tid} {arm} t{trial}] score={s:.0%} attempts={attempts} tr={tr_total}")
            cell[arm] = {"scores": scores, "mean_score": round(statistics.mean(scores), 3),
                         "mean_attempts": round(statistics.mean(attempts_list), 2),
                         "mean_tool_rounds": round(statistics.mean(tr_list), 1)}
            with open(OUT_PATH, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"  → [{tid} {arm}] mean={cell[arm]['mean_score']:.0%} attempts={cell[arm]['mean_attempts']} tr={cell[arm]['mean_tool_rounds']} (saved)")

    results["total_elapsed_sec"] = round(time.time() - t0, 1)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80 + "\nSUMMARY — hard tasks: baseline → stack(mandatory+retry)\n" + "=" * 80)
    for tid in tasks:
        c = results["results"].get(tid, {})
        b = c.get("baseline", {}); s = c.get("stack", {})
        if b and s:
            print(f"  {tid:>12} (~{c['approx_tokens']}tok): baseline {b['mean_score']:.0%} → stack {s['mean_score']:.0%} "
                  f"[{(s['mean_score']-b['mean_score'])*100:+.0f}pp, attempts {s['mean_attempts']}, tr {s['mean_tool_rounds']}]")
    print(f"\ntotal elapsed: {results['total_elapsed_sec']}s → {OUT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
