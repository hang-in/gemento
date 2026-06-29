"""Exp16 — Orchestrator output-stabilization (None-fragility fix) on the Context Router.

H16: `final_answer=None` 시 체인을 재실행(최대 K회)하는 결정론적 안정화 층이, e4b router 의
큰 로그 실효 정답률을 ~60% → ~90%+ 로 올린다 (모델 무변경, Orchestrator/Python safety-net 축).

배경: Exp15 v2/v3 에서 e4b router 의 0점 trial 은 final_answer=None 이고 assertions 도 비어
(A 의 JSON 산출 실패/빈손 수렴). 답을 내면 3/3 완벽, 일부 trial 만 침묵 = 재현성 문제.
→ assertions 합성은 그 trial 을 못 구함(비어서). 진짜 레버는 retry.

안정화 메커니즘 (드라이버 래퍼, 공유 orchestrator 불변):
  (1) retry-on-None: final_answer is None 이면 체인 재실행, 최대 K=2 (총 ≤3 시도). 주력.
  (2) assertion-synthesis: 그래도 None 이고 assertions 가 있으면 합성. free 보조(기대 낮음).

배포 가능 신호: retry 트리거 = (final_answer is None) — gold 점수 불필요.

설계: gemma4:e4b, router_basic, size{12K,25K,50K tok}, num_ctx=32768,
  baseline(1 시도) vs stabilized(≤3 시도) × n=10.
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
SIZES = [("12k", 950), ("25k", 1950), ("50k", 3900)]   # (label, n_lines) — router-needed regime
N_TRIALS = 10
MAX_CYCLES = 5
MAX_RETRIES = 2          # stabilized: 총 ≤ MAX_RETRIES+1 시도

_DIR = Path(__file__).resolve().parent
RESULTS_DIR = _DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULTS_DIR / "exp16_stabilize_gemma4_e4b.json"

OBJECTIVE = "Find the exact file name, line number, and unresolved import module that caused the Rust compilation failure."
KEYWORDS = [["src/main.rs"], ["342"], ["SemanticRouter"]]


def _build_log(n_lines: int) -> str:
    needle_at = n_lines // 2
    lines = []
    for i in range(1, n_lines + 1):
        if i == needle_at:
            lines.append("error[E0432]: unresolved import `crate::router::SemanticRouter` in src/main.rs:342")
        else:
            lines.append(f"[INFO] 2026-06-29 10:15:{i % 60:02d} - Building crate gemento v1.0.0 (step {i}/{n_lines})... ok")
    return "\n".join(lines)


def _synth_from_assertions(tattoo) -> str | None:
    """final_answer=None 보조: 최종 assertions content 를 합쳐 답 후보 생성 (free)."""
    try:
        parts = [str(getattr(a, "content", "")) for a in tattoo.active_assertions if getattr(a, "content", None)]
    except Exception:
        parts = []
    return " \n ".join(parts) if parts else None


def _score(text) -> float:
    if not text:
        return 0.0
    if isinstance(text, dict):
        text = json.dumps(text, ensure_ascii=False)
    elif not isinstance(text, str):
        text = str(text)
    low = text.lower()
    return sum(1 for grp in KEYWORDS if all(t.lower() in low for t in grp)) / len(KEYWORDS)


def _run_once(redis_key):
    """단일 체인 실행 → (final_answer, scored_text(final∪assertions), tattoo, n_cycles)."""
    stats = {}
    caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX, stats=stats)
    prompt = (f"A build failure occurred. The raw log is cached in Redis.\nContext Handle: {redis_key}\n\n" + OBJECTIVE)
    tattoo, logs, ans = run_abc_chain(
        task_id="exp16", objective=OBJECTIVE, prompt=prompt,
        constraints=["정확한 파일/라인/모듈명을 기재하라"],
        max_cycles=MAX_CYCLES, model_caller=caller,
        context_router=True, error_blocks=False, context_handles=[redis_key],
    )
    # 채점용 텍스트 = final_answer ∪ assertions (v2/v3 와 동일 기준)
    synth = _synth_from_assertions(tattoo)
    scored = " \n ".join([p for p in [ans if isinstance(ans, str) else (json.dumps(ans, ensure_ascii=False) if ans else None), synth] if p])
    return ans, scored, tattoo, len(logs), stats.get("tool_rounds", 0)


def _healthcheck():
    try:
        with httpx.Client(timeout=30) as c:
            names = [m.get("name") for m in c.get(BASE_URL.rstrip("/") + "/api/tags").json().get("models", [])]
        if MODEL not in names:
            print(f"  [ABORT] {MODEL} not on server. {names}"); return False
        print(f"  [Healthcheck] OK {names}"); return True
    except Exception as e:
        print(f"  [ABORT] {e}"); return False


def main():
    print("=" * 80)
    print(f"Exp16 output-stabilization — {MODEL} router, sizes {[s[0] for s in SIZES]}, "
          f"baseline vs stabilized(<= {MAX_RETRIES+1} tries), n={N_TRIALS}")
    print("=" * 80)
    if not _healthcheck():
        sys.exit(1)

    r = get_redis_client()
    results = {"experiment": "exp16_output_stabilization", "model": MODEL, "num_ctx": NUM_CTX,
               "n_trials": N_TRIALS, "max_retries": MAX_RETRIES, "max_cycles": MAX_CYCLES, "results": {}}
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
            if prev.get("results"):
                results["results"] = prev["results"]; print(f"  [Resume] {OUT_PATH.name}")
        except Exception as e:
            print(f"  [Resume] fresh ({e})")

    t0 = time.time()
    for size_label, n_lines in SIZES:
        log_content = _build_log(n_lines)
        redis_key = f"ctx:exp16_{size_label}:stdout"
        r.set(redis_key, log_content)
        print(f"\n{'#'*60}\n# SIZE {size_label} (~{len(log_content)//4} tok)\n{'#'*60}")
        cell = results["results"].setdefault(size_label, {})

        # 각 logical trial 을 1회 실행하고, stabilized 는 None 이면 재실행.
        # baseline = 첫 시도 결과, stabilized = 재시도 포함 결과 (동일 trial 의 첫 시도를 공유).
        if "baseline" in cell and len(cell["baseline"]["scores"]) == N_TRIALS:
            print(f"  [skip done] {size_label}"); continue

        base_scores, stab_scores, attempts_list, cyc_list, tr_list = [], [], [], [], []
        for trial in range(1, N_TRIALS + 1):
            attempts = 0
            first_ans = first_scored = None
            stab_scored = None
            cyc_total = 0
            tr_total = 0
            while attempts <= MAX_RETRIES:
                attempts += 1
                ans, scored, tattoo, ncyc, tr = _run_once(redis_key)
                cyc_total += ncyc; tr_total += tr
                if attempts == 1:
                    first_ans, first_scored = ans, scored
                # stabilized 종료 조건: final_answer 가 비어있지 않으면 채택
                if ans:
                    stab_scored = scored
                    break
                stab_scored = scored  # None 이어도 마지막 scored(=assertion 합성 포함) 유지
            base_s = _score(first_scored)
            stab_s = _score(stab_scored)
            base_scores.append(base_s); stab_scores.append(stab_s)
            attempts_list.append(attempts); cyc_list.append(cyc_total); tr_list.append(tr_total)
            print(f"  [{size_label} t{trial}] base={base_s:.0%} stab={stab_s:.0%} attempts={attempts} cyc={cyc_total} tr={tr_total}")

        cell["baseline"] = {"scores": base_scores, "mean_score": round(statistics.mean(base_scores), 3)}
        cell["stabilized"] = {"scores": stab_scores, "mean_score": round(statistics.mean(stab_scores), 3),
                              "mean_attempts": round(statistics.mean(attempts_list), 2),
                              "mean_total_cycles": round(statistics.mean(cyc_list), 1),
                              "mean_total_tool_rounds": round(statistics.mean(tr_list), 1)}
        cell["approx_tokens"] = len(log_content) // 4
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"  → [{size_label}] baseline={cell['baseline']['mean_score']:.0%} → "
              f"stabilized={cell['stabilized']['mean_score']:.0%} "
              f"(mean_attempts={cell['stabilized']['mean_attempts']}) (saved)")

    results["total_elapsed_sec"] = round(time.time() - t0, 1)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80 + "\nSUMMARY — baseline → stabilized (lift) per size\n" + "=" * 80)
    for size_label, _ in SIZES:
        c = results["results"].get(size_label)
        if not c:
            continue
        b = c["baseline"]["mean_score"]; s = c["stabilized"]["mean_score"]
        print(f"  {size_label:>4} (~{c['approx_tokens']}tok): baseline {b:.0%} → stabilized {s:.0%} "
              f"(+{(s-b)*100:.0f}pp, mean_attempts={c['stabilized']['mean_attempts']})")
    print(f"\ntotal elapsed: {results['total_elapsed_sec']}s → {OUT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
