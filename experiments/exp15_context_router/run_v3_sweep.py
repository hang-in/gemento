"""Exp15 v3 — Load-Capacity 임계(S) 캘리브레이션 sweep.

질문: gemma4 의 각 크기(e2b ~2B / e4b ~4B)에서 로그가 얼마나 커지면 stuffing 이
무너지고(=임계 S) router 가 그걸 메우는가? → 동적 게이트 임계 실측 +
"똑똑한 소형 모델이 외재화로 키울 수 있는 작업 크기" 정량화.

설계: size 를 유일 변수로. 단일 1-needle 로그를 5 size 로 스케일.
  Model{gemma4:e2b, gemma4:e4b} × Arm{stuffing, router_basic} × size{~1K,5K,12K,25K,50K tok}
  × n=5 = 100 ABC chains. num_ctx=32768 고정 (≤32K = attention 한계 S 측정, 50K = hard overflow).

GEMENTO_API_BASE_URL 불필요 — native caller 가 직접 터널 base_url 로 /api/chat 호출.
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
MODELS = ["gemma4:e2b", "gemma4:e4b"]
ARMS = ["stuffing", "router_basic"]
NUM_CTX = 32768            # 고정 — size < 32K = attention(S) 측정, 50K = overflow
SIZES = [                  # (label, approx_tokens, n_lines) — 1-needle, needle at ~mid
    ("1k", 1000, 80),
    ("5k", 5000, 400),
    ("12k", 12000, 950),
    ("25k", 25000, 1950),
    ("50k", 50000, 3900),
]
N_TRIALS = 5
MAX_CYCLES = 5

_DIR = Path(__file__).resolve().parent
RESULTS_DIR = _DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULTS_DIR / "exp15_v3_sweep_gemma4_e2b_e4b.json"

OBJECTIVE = "Find the exact file name, line number, and unresolved import module that caused the Rust compilation failure."
KEYWORDS = [["src/main.rs"], ["342"], ["SemanticRouter"]]


def _build_log(n_lines: int) -> str:
    """1-needle Rust 빌드 로그. needle 은 항상 중앙(라인 n//2 부근)에 고정."""
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
        miss = [m for m in MODELS if m not in names]
        if miss:
            print(f"  [ABORT] missing models {miss}. available={names}")
            return False
        print(f"  [Healthcheck] tunnel OK, models present: {MODELS}")
        return True
    except Exception as e:
        print(f"  [ABORT] healthcheck failed: {e}")
        return False


def main():
    print("=" * 80)
    print(f"Exp15 v3 Load-Capacity sweep — {MODELS} × {ARMS} × {[s[0] for s in SIZES]} × n={N_TRIALS}")
    print(f"num_ctx={NUM_CTX} (fixed)")
    print("=" * 80)
    if not _healthcheck():
        sys.exit(1)

    r = get_redis_client()
    results = {"experiment": "exp15_v3_load_capacity_sweep", "models": MODELS, "arms": ARMS,
               "num_ctx": NUM_CTX, "sizes": [s[0] for s in SIZES], "n_trials": N_TRIALS,
               "max_cycles": MAX_CYCLES, "results": {}}
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
            if prev.get("results"):
                results["results"] = prev["results"]
                print(f"  [Resume] loaded {OUT_PATH.name}")
        except Exception as e:
            print(f"  [Resume] fresh ({e})")

    def _done(model, size_label, arm):
        cell = results["results"].get(model, {}).get(size_label, {}).get(arm)
        return bool(cell and len(cell.get("scores", [])) == N_TRIALS)

    t0 = time.time()
    # 로그는 size 별 1회 Redis 적재 (model/arm 무관 동일)
    for size_label, approx_tok, n_lines in SIZES:
        log_content = _build_log(n_lines)
        redis_key = f"ctx:exp15v3_{size_label}:stdout"
        r.set(redis_key, log_content)
        real_tok = len(log_content) // 4
        print(f"\n{'#'*70}\n# SIZE {size_label} | {n_lines} lines, ~{real_tok} tok (target {approx_tok}) | needle@mid\n{'#'*70}")

        for model in MODELS:
            results["results"].setdefault(model, {})
            results["results"][model].setdefault(size_label, {"approx_tokens": real_tok})
            for arm in ARMS:
                if _done(model, size_label, arm):
                    c = results["results"][model][size_label][arm]
                    print(f"  [skip] {model} {size_label} {arm} mean={c['mean_score']:.0%}")
                    continue
                scores, durs, cyc, trounds, intoks = [], [], [], [], []
                for trial in range(1, N_TRIALS + 1):
                    stats = {}
                    caller = make_ollama_native_caller(BASE_URL, model, num_ctx=NUM_CTX, stats=stats)
                    if arm == "stuffing":
                        prompt = ("Here is the raw log:\n\n```text\n" + log_content + "\n```\n\n" + OBJECTIVE)
                        kw = dict(context_router=False, error_blocks=False)
                    else:
                        prompt = (f"A build failure occurred. The raw log is cached in Redis.\nContext Handle: {redis_key}\n\n" + OBJECTIVE)
                        kw = dict(context_router=True, error_blocks=False, context_handles=[redis_key])
                    start = time.time()
                    try:
                        _t, logs, ans = run_abc_chain(
                            task_id=f"exp15v3_{model.replace(':','_')}_{size_label}_{arm}_{trial}",
                            objective=OBJECTIVE, prompt=prompt,
                            constraints=["정확한 파일/라인/모듈명을 기재하라"],
                            max_cycles=MAX_CYCLES, model_caller=caller, **kw,
                        )
                        scores.append(_score(ans, _t)); durs.append(time.time() - start)
                        cyc.append(len(logs)); trounds.append(stats.get("tool_rounds", 0)); intoks.append(stats.get("in_tok", 0))
                    except Exception as e:
                        scores.append(0.0); durs.append(time.time() - start)
                        cyc.append(0); trounds.append(stats.get("tool_rounds", 0)); intoks.append(stats.get("in_tok", 0))
                        print(f"    ERR {e}")
                    print(f"  [{model} {size_label} {arm} t{trial}] score={scores[-1]:.0%} dur={durs[-1]:.0f}s tr={trounds[-1]} in~{intoks[-1]}")
                cell = {"scores": scores, "mean_score": round(statistics.mean(scores), 3),
                        "mean_dur": round(statistics.mean(durs), 1), "mean_cycles": round(statistics.mean(cyc), 1),
                        "mean_tool_rounds": round(statistics.mean(trounds), 2), "mean_in_tok": int(statistics.mean(intoks))}
                results["results"][model][size_label][arm] = cell
                with open(OUT_PATH, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"  → [{model} {size_label} {arm}] mean={cell['mean_score']:.0%} dur={cell['mean_dur']}s tr={cell['mean_tool_rounds']} (saved)")

    results["total_elapsed_sec"] = round(time.time() - t0, 1)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80 + "\nSUMMARY — mean_score per model × size × arm (num_ctx=32768)\n" + "=" * 80)
    for model in MODELS:
        print(f"\n{model}")
        print(f"  {'size':>6} | {'stuffing':>9} | {'router':>9}")
        for size_label, _, _ in SIZES:
            cell = results["results"].get(model, {}).get(size_label, {})
            s = cell.get("stuffing", {}).get("mean_score")
            rt = cell.get("router_basic", {}).get("mean_score")
            print(f"  {size_label:>6} | {('%.0f%%'%(s*100)) if s is not None else '   -':>9} | {('%.0f%%'%(rt*100)) if rt is not None else '   -':>9}")
    print(f"\ntotal elapsed: {results['total_elapsed_sec']}s → {OUT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
