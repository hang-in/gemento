"""Exp16c — mandatory-tool 프롬프트 + retry-on-None 결합 (~99% 검증).

Exp16b: mandatory 프롬프트 → per-attempt 27%→83%.
Exp16:  retry-on-None 단독 → 50~70% 정체 (per-attempt 낮아서).
Exp16c: 둘을 결합 → per-attempt 83% + retry(K=2) 면 기대 ~99% 인지 실측.

설계: gemma4:e4b, router_basic + mandatory prompt, size{12K,25K,50K}, num_ctx=32768,
  stabilized(mandatory + retry-on-None, 최대 K=2, 총 ≤3 시도) × n=10.
구현: run_v16(retry) + run_v16b(mandatory block) 결합. 공유 코드 불변 (side 브랜치).
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
SIZES = [("12k", 950), ("25k", 1950), ("50k", 3900)]
N_TRIALS = 10
MAX_CYCLES = 5
MAX_RETRIES = 2

_DIR = Path(__file__).resolve().parent
RESULTS_DIR = _DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULTS_DIR / "exp16c_combined_gemma4_e4b.json"

OBJECTIVE = "Find the exact file name, line number, and unresolved import module that caused the Rust compilation failure."
KEYWORDS = [["src/main.rs"], ["342"], ["SemanticRouter"]]
MANDATORY_BLOCK = (
    "\n\n## MANDATORY TOOL-USE RULES (must follow):\n"
    "1. You MUST call `grep_context` on the given handle BEFORE answering. Do NOT answer from memory or assumption.\n"
    "2. Start by grepping for error markers, e.g. pattern \"error\" or \"E0432\". The raw log is NOT in your prompt — you can only see it via the tools.\n"
    "3. Do NOT conclude \"the log does not contain ...\" after a single query. If a grep returns no useful match, try another pattern (\"unresolved\", \"import\", a filename) before giving up.\n"
    "4. Once you find the matching line, transcribe the EXACT file path, line number, and module identifier verbatim from that line into your final_answer. Do not paraphrase or omit any of the three.\n"
)


def _build_log(n_lines: int) -> str:
    needle_at = n_lines // 2
    lines = []
    for i in range(1, n_lines + 1):
        if i == needle_at:
            lines.append("error[E0432]: unresolved import `crate::router::SemanticRouter` in src/main.rs:342")
        else:
            lines.append(f"[INFO] 2026-06-30 10:15:{i % 60:02d} - Building crate gemento v1.0.0 (step {i}/{n_lines})... ok")
    return "\n".join(lines)


def _synth(tattoo):
    try:
        parts = [str(getattr(a, "content", "")) for a in tattoo.active_assertions if getattr(a, "content", None)]
    except Exception:
        parts = []
    return " \n ".join(parts) if parts else None


def _score(text) -> float:
    if not text:
        return 0.0
    if not isinstance(text, str):
        text = json.dumps(text, ensure_ascii=False) if isinstance(text, dict) else str(text)
    low = text.lower()
    return sum(1 for grp in KEYWORDS if all(t.lower() in low for t in grp)) / len(KEYWORDS)


def _run_once(redis_key, prompt):
    stats = {}
    caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX, stats=stats)
    tattoo, logs, ans = run_abc_chain(
        task_id="exp16c", objective=OBJECTIVE, prompt=prompt,
        constraints=["정확한 파일/라인/모듈명을 그대로 기재하라"],
        max_cycles=MAX_CYCLES, model_caller=caller,
        context_router=True, error_blocks=False, context_handles=[redis_key],
    )
    synth = _synth(tattoo)
    scored = " \n ".join([p for p in [ans if isinstance(ans, str) else (json.dumps(ans, ensure_ascii=False) if ans else None), synth] if p])
    return ans, scored, len(logs), stats.get("tool_rounds", 0)


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
    print(f"Exp16c mandatory + retry — {MODEL} router, sizes {[s[0] for s in SIZES]}, "
          f"stabilized(mandatory + retry<= {MAX_RETRIES+1}) × n={N_TRIALS}")
    print("=" * 80)
    if not _healthcheck():
        sys.exit(1)

    r = get_redis_client()
    results = {"experiment": "exp16c_mandatory_plus_retry", "model": MODEL, "num_ctx": NUM_CTX,
               "n_trials": N_TRIALS, "max_retries": MAX_RETRIES, "results": {}}
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
            if prev.get("results"):
                results["results"] = prev["results"]; print(f"  [Resume] {OUT_PATH.name}")
        except Exception as e:
            print(f"  [Resume] fresh ({e})")

    t0 = time.time()
    for size_label, n_lines in SIZES:
        if size_label in results["results"] and len(results["results"][size_label].get("scores", [])) == N_TRIALS:
            print(f"  [skip] {size_label}"); continue
        log_content = _build_log(n_lines)
        redis_key = f"ctx:exp16c_{size_label}:stdout"
        r.set(redis_key, log_content)
        prompt = (f"A build failure occurred. The raw log is cached in Redis.\nContext Handle: {redis_key}\n\n"
                  + OBJECTIVE + MANDATORY_BLOCK)
        print(f"\n{'#'*60}\n# SIZE {size_label} (~{len(log_content)//4} tok)\n{'#'*60}")

        scores, attempts_list, first_scores = [], [], []
        for trial in range(1, N_TRIALS + 1):
            attempts = 0; final_scored = None; first_scored = None
            while attempts <= MAX_RETRIES:
                attempts += 1
                ans, scored, _ncyc, _tr = _run_once(redis_key, prompt)
                if attempts == 1:
                    first_scored = scored
                final_scored = scored
                if ans:
                    break
            s = _score(final_scored)
            scores.append(s); attempts_list.append(attempts)
            print(f"  [{size_label} t{trial}] eff={s:.0%} attempts={attempts}")

        cell = {"scores": scores, "mean_score": round(statistics.mean(scores), 3),
                "mean_attempts": round(statistics.mean(attempts_list), 2),
                "approx_tokens": len(log_content) // 4}
        results["results"][size_label] = cell
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"  → [{size_label}] mandatory+retry eff={cell['mean_score']:.0%} (mean_attempts={cell['mean_attempts']}) (saved)")

    results["total_elapsed_sec"] = round(time.time() - t0, 1)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80 + "\nSUMMARY — mandatory+retry effective accuracy\n" + "=" * 80)
    for size_label, _ in SIZES:
        c = results["results"].get(size_label)
        if c:
            print(f"  {size_label:>4} (~{c['approx_tokens']}tok): eff {c['mean_score']:.0%} (mean_attempts {c['mean_attempts']})")
    print(f"\ntotal elapsed: {results['total_elapsed_sec']}s → {OUT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
