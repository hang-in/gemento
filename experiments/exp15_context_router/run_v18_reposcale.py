"""Exp18 — repo-규모 추론 상한 (e4b + router, size sweep).

질문: Exp17(~23K)에서 e4b+router 가 multi-hop/집계를 ~92% 처리. 컨텍스트(32K)를 초과하는
repo-규모(50K~200K tok) — router 가 *필수* 인 영역 — 에서도 추론이 유지되나, 아니면 e4b 추론
천장이 needle 분산에 따라 내려가나?

설계: 2 task(multihop3 / multineedle) × 3 size(~50K/100K/200K tok) × n=8.
  router + retry-on-None(K=2), mandatory OFF (Exp17: mandatory 는 추론 task 에 −).
  needle 을 거대 로그 전체에 분산(20%/55%/85%) → grep+상관 능력을 scale 에서 측정.
  로그는 Redis 에 보관, 모델은 grep 결과만 봄 → router 가 size-invariant 인지 직접 검증.
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
SIZES = [("50k", 3300), ("100k", 6700), ("200k", 13300)]   # (label, n_lines), ~15 tok/line
N_TRIALS = 8
MAX_CYCLES = 5
MAX_RETRIES = 2

_DIR = Path(__file__).resolve().parent
RESULTS_DIR = _DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULTS_DIR / "exp18_reposcale_gemma4_e4b.json"


def _filler(i: int, total: int) -> str:
    return f"[INFO] 2026-06-30 10:15:{i % 60:02d} svc=api req={i}/{total} latency_ms={(i * 7) % 50} status=ok"


def _positions(n_lines: int) -> tuple[int, int, int]:
    """needle 3개를 로그 전체에 분산 (20% / 55% / 85%)."""
    return int(n_lines * 0.20), int(n_lines * 0.55), int(n_lines * 0.85)


def _build(task: str, n_lines: int) -> str:
    a, b, c = _positions(n_lines)
    L = [_filler(i, n_lines) for i in range(1, n_lines + 1)]
    if task == "multihop3":
        L[a] = "[CONFIG] tls.min_version=1.0 (deprecated)"
        L[b] = "[WARN] handshake downgraded due to tls.min_version=1.0"
        L[c] = "FATAL: peer rejected connection (insecure TLS) at net/tls_handshake.rs:88"
    elif task == "multineedle":
        L[a] = "FAILED test_auth_login (AssertionError: expected 200 got 401)"
        L[b] = "FAILED test_payment_charge (KeyError: 'amount')"
        L[c] = "FAILED test_cart_total (TypeError: NoneType has no len)"
    return "\n".join(L)


TASKS = {
    "multihop3": dict(
        objective="Trace the causal chain: which config setting led, via a downgrade warning, to the fatal connection failure? Report the root config key and the file:line of the FATAL.",
        keywords=[["min_version"], ["tls_handshake.rs"], ["88"]],
    ),
    "multineedle": dict(
        objective="List the names of ALL failing tests in this log (there are several, scattered far apart). Report every one.",
        keywords=[["test_auth_login"], ["test_payment_charge"], ["test_cart_total"]],
    ),
}


def _synth(tattoo):
    try:
        return " \n ".join(str(getattr(a, "content", "")) for a in tattoo.active_assertions if getattr(a, "content", None))
    except Exception:
        return None


def _score(ans, tattoo, kw) -> float:
    parts = []
    if ans:
        parts.append(ans if isinstance(ans, str) else json.dumps(ans, ensure_ascii=False))
    s = _synth(tattoo)
    if s:
        parts.append(s)
    if not parts:
        return 0.0
    low = " \n ".join(parts).lower()
    return sum(1 for g in kw if all(t.lower() in low for t in g)) / len(kw)


def _run_with_retry(redis_key, objective, kw):
    """router + retry-on-None(K=2), mandatory OFF. 반환: (eff_score, attempts)."""
    prompt = (f"A failure occurred. The raw log is cached in Redis.\nContext Handle: {redis_key}\n\n" + objective)
    attempts = 0
    last_ans = last_tt = None
    while attempts <= MAX_RETRIES:
        attempts += 1
        caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX)
        tt, logs, ans = run_abc_chain(
            task_id="exp18", objective=objective, prompt=prompt,
            constraints=["요구된 모든 항목을 정확히 기재하라"],
            max_cycles=MAX_CYCLES, model_caller=caller,
            context_router=True, error_blocks=False, context_handles=[redis_key],
        )
        last_ans, last_tt = ans, tt
        if ans:
            break
    return _score(last_ans, last_tt, kw), attempts


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
    print(f"Exp18 repo-scale reasoning ceiling — {MODEL} router+retry, tasks {list(TASKS)}, sizes {[s[0] for s in SIZES]}, n={N_TRIALS}")
    print("=" * 80)
    if not _healthcheck():
        sys.exit(1)

    r = get_redis_client()
    results = {"experiment": "exp18_reposcale", "model": MODEL, "num_ctx": NUM_CTX,
               "n_trials": N_TRIALS, "max_retries": MAX_RETRIES, "results": {}}
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
            if prev.get("results"):
                results["results"] = prev["results"]; print(f"  [Resume] {OUT_PATH.name}")
        except Exception as e:
            print(f"  [Resume] fresh ({e})")

    def _done(task, size_label):
        c = results["results"].get(task, {}).get(size_label)
        return bool(c and len(c.get("scores", [])) == N_TRIALS)

    t0 = time.time()
    for task, spec in TASKS.items():
        results["results"].setdefault(task, {})
        for size_label, n_lines in SIZES:
            if _done(task, size_label):
                print(f"  [skip] {task} {size_label}"); continue
            log = _build(task, n_lines)
            redis_key = f"ctx:exp18_{task}_{size_label}:stdout"
            r.set(redis_key, log)
            approx_tok = len(log) // 4
            print(f"\n{'#'*60}\n# {task} {size_label} (~{approx_tok} tok, {n_lines} lines, needles@20/55/85%)\n{'#'*60}")
            scores, attempts_list = [], []
            for trial in range(1, N_TRIALS + 1):
                sc, att = _run_with_retry(redis_key, spec["objective"], spec["keywords"])
                scores.append(sc); attempts_list.append(att)
                print(f"  [{task} {size_label} t{trial}] score={sc:.0%} attempts={att}")
            cell = {"scores": scores, "mean_score": round(statistics.mean(scores), 3),
                    "mean_attempts": round(statistics.mean(attempts_list), 2), "approx_tokens": approx_tok}
            results["results"][task][size_label] = cell
            with open(OUT_PATH, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"  → [{task} {size_label}] mean={cell['mean_score']:.0%} attempts={cell['mean_attempts']} (saved)")

    results["total_elapsed_sec"] = round(time.time() - t0, 1)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80 + "\nSUMMARY — mean_score per task × size (router+retry, mandatory off)\n" + "=" * 80)
    for task in TASKS:
        row = " | ".join(f"{sl}={results['results'].get(task,{}).get(sl,{}).get('mean_score','-')}" for sl, _ in SIZES)
        print(f"  {task:>12}: {row}")
    print(f"\ntotal elapsed: {results['total_elapsed_sec']}s → {OUT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
