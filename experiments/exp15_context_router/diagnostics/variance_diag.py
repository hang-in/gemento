"""Finalization run-to-run 분산 진단 (공유 코드 무변경).

동기: control finalized rate 가 레버 A/B(n=6) 17% → Exp22(n=10) 70% 로 요동.
질문 = (a) 순수 per-chain 샘플링 노이즈(단일 분포, 소표본 이항 변동) 인가,
      (b) 체계적 batch/시간 효과(bimodal, 서버 상태 의존) 인가.

설계: control-only(grep_only+router+mandatory, discipline off), task A(exp21a_crashloop,
finalization-fragile), 3 batch × n=10 = 30 chain. 각 chain 은 phase0_diag 필드 계측.
분석: pooled p̂ + Wilson 95% CI(진짜 control 신뢰도) + batch별 rate(시간 드리프트=over-dispersion).

결정 기준:
  pooled p̂ ~0.6-0.7 → "17% 문제"는 소표본 착시, finalization ~2/3 신뢰(retry-on-None 커버) → 트랙 축소.
  pooled p̂ ~0.3-0.4 → 진짜 신뢰성 갭 → 메커니즘 심화.
  batch간 분산 ≫ 이항 기대 → 시간/서버 상태 효과 → 별도 조사.

사용자/에이전트 실행 (boxie 터널 필요):
  python -u experiments/exp15_context_router/diagnostics/variance_diag.py
"""
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_DIR.parent.parent))                 # experiments/
sys.path.insert(0, str(_DIR.parent))                        # exp15_context_router/

import run_v21_facet_ab as drv
from orchestrator import run_abc_chain
from native_ollama_caller import make_ollama_native_caller

BASE_URL, MODEL, NUM_CTX, REDIS_KEY = drv.BASE_URL, drv.MODEL, drv.NUM_CTX, drv.REDIS_KEY
MAX_CYCLES = 8
N_BATCHES = 3
BATCH_N = 10
TASK_ID = "exp21a_crashloop"
CORRECT_KW = "gohttpserver"
OUT = _DIR / "variance_diag_result.json"

TASK = next(t for t in drv.TASKS if t["id"] == TASK_ID)


def _synth(tt):
    try:
        return " \n ".join(str(getattr(a, "content", "")) for a in tt.active_assertions
                           if getattr(a, "content", None))
    except Exception:
        return ""


def one_chain():
    prompt = (f"A diagnostic request for server test9ng. The full systemd journal (30-day window, "
              f"very large) is cached in Redis.\nContext Handle: {REDIS_KEY}\n\n" + TASK["objective"])
    caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX)   # grep_only, control
    tt, logs, ans = run_abc_chain(
        task_id=TASK["id"], objective=TASK["objective"], prompt=prompt,
        constraints=TASK["constraints"], max_cycles=MAX_CYCLES, model_caller=caller,
        context_router=True, error_blocks=False, context_handles=[REDIS_KEY],
        mandatory_tool_prompt=True,                          # discipline off = control
    )
    s = _synth(tt).lower()
    judge_conv = any((getattr(l, "c_decision", None) or {}).get("converged") for l in logs)
    return {
        "finalized": ans is not None,
        "answer_in_tattoo": CORRECT_KW in s,
        "correct": (CORRECT_KW in str(ans).lower()) if ans else False,
        "death_phase": tt.phase.value,
        "judge_ever_converged": bool(judge_conv),
        "n_cycles": len(logs),
        "n_assertions": len(tt.active_assertions),
    }


def _wilson_ci(k, n, z=1.96):
    """Wilson score 95% CI for a binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (round(center - half, 3), round(center + half, 3))


def main():
    print("=" * 80, flush=True)
    print(f"Finalization 분산 진단 — control-only task A | {N_BATCHES} batch × {BATCH_N} "
          f"= {N_BATCHES * BATCH_N} chain, max_cycles={MAX_CYCLES}", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    out = {
        "experiment": "finalization_variance_diag",
        "model": MODEL,
        "task": TASK_ID,
        "arm": "control (grep_only+router+mandatory, discipline off)",
        "n_batches": N_BATCHES,
        "batch_n": BATCH_N,
        "max_cycles": MAX_CYCLES,
        "batches": [],
    }
    t0 = time.time()
    all_samples = []

    for b in range(1, N_BATCHES + 1):
        print(f"\n  ══ Batch {b}/{N_BATCHES} ══", flush=True)
        bsamples = []
        for i in range(1, BATCH_N + 1):
            r = one_chain()
            bsamples.append(r)
            all_samples.append(r)
            fin = sum(1 for x in bsamples if x["finalized"])
            out["batches"] = out.get("batches", [])
            # 매 trial 증분 저장 (batch 진행분 반영)
            batch_rates = []
            done_batches = out["batches"][:b - 1]
            cur = {
                "batch": b, "n": len(bsamples),
                "finalized_rate": round(fin / len(bsamples), 3),
                "samples": bsamples,
            }
            snapshot = done_batches + [cur]
            k_all = sum(1 for x in all_samples if x["finalized"])
            n_all = len(all_samples)
            out_live = dict(out)
            out_live["batches"] = snapshot
            out_live["pooled"] = {
                "n": n_all,
                "finalized_rate": round(k_all / n_all, 3),
                "wilson95": _wilson_ci(k_all, n_all),
                "correct_rate": round(sum(1 for x in all_samples if x["correct"]) / n_all, 3),
                "empty_tattoo_rate": round(sum(1 for x in all_samples if x["n_assertions"] == 0) / n_all, 3),
                "judge_conv_rate": round(sum(1 for x in all_samples if x["judge_ever_converged"]) / n_all, 3),
                "death_phase_dist": dict(Counter(x["death_phase"] for x in all_samples)),
            }
            out_live["elapsed_sec"] = round(time.time() - t0, 1)
            OUT.write_text(json.dumps(out_live, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  [b{b} {i}/{BATCH_N}] finalized={r['finalized']} correct={r['correct']} "
                  f"death={r['death_phase']} judge_conv={r['judge_ever_converged']} "
                  f"cyc={r['n_cycles']} asrt={r['n_assertions']}", flush=True)
        out["batches"] = out_live["batches"]
        out["pooled"] = out_live["pooled"]

    # ── 최종 분산 분석 ──
    batch_rates = [b["finalized_rate"] for b in out["batches"]]
    p = out["pooled"]["finalized_rate"]
    # 이항 기대 batch-rate 분산 vs 관측 batch-rate 분산 (over-dispersion 지표)
    exp_var = p * (1 - p) / BATCH_N if 0 < p < 1 else 0.0
    obs_var = (sum((r - p) ** 2 for r in batch_rates) / len(batch_rates)) if batch_rates else 0.0
    dispersion = round(obs_var / exp_var, 2) if exp_var > 0 else None
    out["variance_analysis"] = {
        "batch_finalized_rates": batch_rates,
        "pooled_p": p,
        "wilson95": out["pooled"]["wilson95"],
        "expected_batch_var_binomial": round(exp_var, 4),
        "observed_batch_var": round(obs_var, 4),
        "dispersion_ratio_obs_over_exp": dispersion,
        "note": "dispersion ~1 → per-chain 노이즈(단일 분포); ≫1 → batch/시간 over-dispersion. (3 batch 는 coarse.)",
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 80, flush=True)
    print("분산 진단 결과:", flush=True)
    print(f"  pooled finalized = {p:.0%} (n={out['pooled']['n']}), Wilson95 = {out['pooled']['wilson95']}", flush=True)
    print(f"  batch rates = {batch_rates}", flush=True)
    print(f"  correct = {out['pooled']['correct_rate']:.0%} | empty_tattoo = {out['pooled']['empty_tattoo_rate']:.0%} "
          f"| judge_conv = {out['pooled']['judge_conv_rate']:.0%}", flush=True)
    print(f"  death_phase = {out['pooled']['death_phase_dist']}", flush=True)
    print(f"  dispersion(obs/exp) = {dispersion}  (~1 per-chain 노이즈 / ≫1 batch 효과)", flush=True)
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
