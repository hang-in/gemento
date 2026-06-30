"""Exp16b — per-attempt 신뢰도 향상 (mandatory-tool prompting).

H16b: 라우터 task prompt 에 mandatory-tool 지시(반드시 grep 먼저 / "not found" 조기 단정 금지 /
매치 라인을 그대로 전사)를 주면, e4b router 의 *per-attempt* 성공률이 큰 로그에서 오른다.
Exp08b 가 tool_neglect 0% 를 만든 패턴을 컨텍스트 라우터에 적용.

배경: Exp16 에서 retry 만으론 ~50~70% 정체 — 큰 로그 per-attempt 성공률 ~10~30% 가 병목.
retry(증상) 대신 per-attempt(원인) 를 올린다.

설계: gemma4:e4b, router_basic, size{12K,25K,50K}, num_ctx=32768,
  baseline-prompt vs mandatory-tool-prompt × n=10 (1 시도, retry 없음 — per-attempt 깨끗이 측정).
구현: mandatory 지시는 driver task prompt prefix 에만. 공유 system_prompt.py 불변 (side 브랜치).
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

_DIR = Path(__file__).resolve().parent
RESULTS_DIR = _DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULTS_DIR / "exp16b_mandatory_gemma4_e4b.json"

OBJECTIVE = "Find the exact file name, line number, and unresolved import module that caused the Rust compilation failure."
KEYWORDS = [["src/main.rs"], ["342"], ["SemanticRouter"]]

# mandatory-tool 지시 — Stage 8 에서 source-of-truth 를 system_prompt.MANDATORY_TOOL_RULES 로 통일.
# (Exp16b 작성 시점의 로컬 블록과 byte-identical — Task 01 검증 통과.)
from system_prompt import MANDATORY_TOOL_RULES as MANDATORY_BLOCK


def _build_log(n_lines: int) -> str:
    needle_at = n_lines // 2
    lines = []
    for i in range(1, n_lines + 1):
        if i == needle_at:
            lines.append("error[E0432]: unresolved import `crate::router::SemanticRouter` in src/main.rs:342")
        else:
            lines.append(f"[INFO] 2026-06-29 10:15:{i % 60:02d} - Building crate gemento v1.0.0 (step {i}/{n_lines})... ok")
    return "\n".join(lines)


def _score(ans, tattoo) -> float:
    parts = []
    if ans:
        parts.append(ans if isinstance(ans, str) else json.dumps(ans, ensure_ascii=False))
    try:
        for a in tattoo.active_assertions:
            c = getattr(a, "content", None)
            if c:
                parts.append(str(c))
    except Exception:
        pass
    if not parts:
        return 0.0
    low = " \n ".join(parts).lower()
    return sum(1 for grp in KEYWORDS if all(t.lower() in low for t in grp)) / len(KEYWORDS)


def _healthcheck():
    try:
        with httpx.Client(timeout=30) as c:
            names = [m.get("name") for m in c.get(BASE_URL.rstrip("/") + "/api/tags").json().get("models", [])]
        if MODEL not in names:
            print(f"  [ABORT] {MODEL} missing. {names}"); return False
        print(f"  [Healthcheck] OK {names}"); return True
    except Exception as e:
        print(f"  [ABORT] {e}"); return False


def main():
    print("=" * 80)
    print(f"Exp16b mandatory-tool prompting — {MODEL} router, sizes {[s[0] for s in SIZES]}, "
          f"baseline vs mandatory × n={N_TRIALS} (1 attempt)")
    print("=" * 80)
    if not _healthcheck():
        sys.exit(1)

    r = get_redis_client()
    results = {"experiment": "exp16b_mandatory_tool", "model": MODEL, "num_ctx": NUM_CTX,
               "n_trials": N_TRIALS, "max_cycles": MAX_CYCLES, "results": {}}
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
            if prev.get("results"):
                results["results"] = prev["results"]; print(f"  [Resume] {OUT_PATH.name}")
        except Exception as e:
            print(f"  [Resume] fresh ({e})")

    def _done(size_label, arm):
        c = results["results"].get(size_label, {}).get(arm)
        return bool(c and len(c.get("scores", [])) == N_TRIALS)

    t0 = time.time()
    for size_label, n_lines in SIZES:
        log_content = _build_log(n_lines)
        redis_key = f"ctx:exp16b_{size_label}:stdout"
        r.set(redis_key, log_content)
        print(f"\n{'#'*60}\n# SIZE {size_label} (~{len(log_content)//4} tok)\n{'#'*60}")
        cell = results["results"].setdefault(size_label, {"approx_tokens": len(log_content) // 4})

        base_prompt = (f"A build failure occurred. The raw log is cached in Redis.\nContext Handle: {redis_key}\n\n" + OBJECTIVE)
        prompts = {
            "baseline": base_prompt,
            "mandatory": base_prompt + MANDATORY_BLOCK,
        }
        for arm, prompt in prompts.items():
            if _done(size_label, arm):
                print(f"  [skip] {size_label} {arm} mean={results['results'][size_label][arm]['mean_score']:.0%}")
                continue
            scores, durs, cyc, trounds = [], [], [], []
            for trial in range(1, N_TRIALS + 1):
                stats = {}
                caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX, stats=stats)
                start = time.time()
                try:
                    _t, logs, ans = run_abc_chain(
                        task_id=f"exp16b_{size_label}_{arm}_{trial}", objective=OBJECTIVE, prompt=prompt,
                        constraints=["정확한 파일/라인/모듈명을 그대로 기재하라"],
                        max_cycles=MAX_CYCLES, model_caller=caller,
                        context_router=True, error_blocks=False, context_handles=[redis_key],
                    )
                    scores.append(_score(ans, _t)); durs.append(time.time() - start)
                    cyc.append(len(logs)); trounds.append(stats.get("tool_rounds", 0))
                except Exception as e:
                    scores.append(0.0); durs.append(time.time() - start); cyc.append(0); trounds.append(stats.get("tool_rounds", 0))
                    print(f"    ERR {e}")
                print(f"  [{size_label} {arm} t{trial}] score={scores[-1]:.0%} dur={durs[-1]:.0f}s tr={trounds[-1]}")
            cell[arm] = {"scores": scores, "mean_score": round(statistics.mean(scores), 3),
                         "mean_dur": round(statistics.mean(durs), 1), "mean_cycles": round(statistics.mean(cyc), 1),
                         "mean_tool_rounds": round(statistics.mean(trounds), 2)}
            with open(OUT_PATH, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"  → [{size_label} {arm}] per-attempt mean={cell[arm]['mean_score']:.0%} tr={cell[arm]['mean_tool_rounds']} (saved)")

    results["total_elapsed_sec"] = round(time.time() - t0, 1)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80 + "\nSUMMARY — per-attempt success: baseline → mandatory (tool_rounds)\n" + "=" * 80)
    for size_label, _ in SIZES:
        c = results["results"].get(size_label, {})
        b = c.get("baseline", {}); m = c.get("mandatory", {})
        if b and m:
            print(f"  {size_label:>4} (~{c['approx_tokens']}tok): baseline {b['mean_score']:.0%} (tr{b['mean_tool_rounds']}) "
                  f"→ mandatory {m['mean_score']:.0%} (tr{m['mean_tool_rounds']})  [{(m['mean_score']-b['mean_score'])*100:+.0f}pp]")
    print(f"\ntotal elapsed: {results['total_elapsed_sec']}s → {OUT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
