"""Retry capstone — per-attempt ≈57% + retry-on-None(K=3) → ~90% finalized 실측 확인.

분산 진단(variance_diag)이 밝힌 것: control task A per-attempt finalized ≈ 57%
(Wilson95 [39%,73%]), dispersion 0.63 = 순수 per-chain 노이즈(체계적 결함/시간효과 없음).
레버의 17%·Exp22 의 70%는 둘 다 이 분포의 꼬리 draw.

함의: retry-on-None(H16, 드라이버 레벨 루프 — run_abc_chain 을 finalized 될 때까지
최대 K회 재호출)이 이미 처방. p≈0.57 → 1-(0.43)^3 ≈ 92% 예측. 이걸 실측 확인하고
오케스트레이터 신뢰성 트랙을 '진짜 레버 = retry(기존)' 로 종결한다.

설계: control(grep_only+router+mandatory) task A, n=20, K=3 retry-on-None.
측정: retry 후 finalized_rate(~0.9 기대) / correct_rate / avg attempts /
     first-attempt finalized(≈0.57 재확인).

실행 (boxie 터널 필요):
  python -u experiments/exp15_context_router/diagnostics/retry_capstone.py
"""
import json
import math
import os
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
N = int(os.environ.get("CAPSTONE_N", "20"))
K = int(os.environ.get("CAPSTONE_K", "3"))                  # retry-on-None 최대 시도 (env override)
TASK_ID = "exp21a_crashloop"
CORRECT_KW = "gohttpserver"
OUT = _DIR / ("retry_capstone_result.json" if K == 3 else f"retry_capstone_k{K}_result.json")

TASK = next(t for t in drv.TASKS if t["id"] == TASK_ID)


def one_attempt():
    prompt = (f"A diagnostic request for server test9ng. The full systemd journal (30-day window, "
              f"very large) is cached in Redis.\nContext Handle: {REDIS_KEY}\n\n" + TASK["objective"])
    caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX)   # grep_only, control
    tt, logs, ans = run_abc_chain(
        task_id=TASK["id"], objective=TASK["objective"], prompt=prompt,
        constraints=TASK["constraints"], max_cycles=MAX_CYCLES, model_caller=caller,
        context_router=True, error_blocks=False, context_handles=[REDIS_KEY],
        mandatory_tool_prompt=True,
    )
    return ans


def one_trial():
    """retry-on-None: finalized 될 때까지 최대 K회 재호출 (H16 드라이버 레벨 루프)."""
    first_finalized = None
    for attempt in range(1, K + 1):
        ans = one_attempt()
        if attempt == 1:
            first_finalized = ans is not None
        if ans is not None:
            return {"finalized": True, "attempts": attempt,
                    "correct": CORRECT_KW in str(ans).lower(),
                    "first_attempt_finalized": first_finalized}
    return {"finalized": False, "attempts": K, "correct": False,
            "first_attempt_finalized": first_finalized}


def _wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (round(center - half, 3), round(center + half, 3))


def main():
    print("=" * 80, flush=True)
    print(f"Retry capstone — control task A | n={N}, retry-on-None K={K}, max_cycles={MAX_CYCLES}", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    out = {
        "experiment": "retry_capstone",
        "model": MODEL,
        "task": TASK_ID,
        "arm": "control (grep_only+router+mandatory) + retry-on-None",
        "n": N, "K": K, "max_cycles": MAX_CYCLES,
        "samples": [],
    }
    t0 = time.time()
    samples = []
    for i in range(1, N + 1):
        r = one_trial()
        samples.append(r)
        k_fin = sum(1 for x in samples if x["finalized"])
        k_first = sum(1 for x in samples if x["first_attempt_finalized"])
        k_corr = sum(1 for x in samples if x["correct"])
        out["samples"] = samples
        out["agg"] = {
            "n": len(samples),
            "finalized_rate_after_retry": round(k_fin / len(samples), 3),
            "finalized_wilson95": _wilson_ci(k_fin, len(samples)),
            "first_attempt_finalized_rate": round(k_first / len(samples), 3),
            "correct_rate": round(k_corr / len(samples), 3),
            "avg_attempts": round(sum(x["attempts"] for x in samples) / len(samples), 2),
            "attempts_dist": dict(Counter(x["attempts"] for x in samples)),
        }
        out["elapsed_sec"] = round(time.time() - t0, 1)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [{i}/{N}] finalized={r['finalized']} attempts={r['attempts']} "
              f"correct={r['correct']} first_ok={r['first_attempt_finalized']}", flush=True)

    a = out["agg"]
    print("\n" + "=" * 80, flush=True)
    print("Retry capstone 결과:", flush=True)
    print(f"  finalized after retry = {a['finalized_rate_after_retry']:.0%} "
          f"(n={a['n']}, Wilson95={a['finalized_wilson95']})", flush=True)
    print(f"  first-attempt finalized = {a['first_attempt_finalized_rate']:.0%}  (variance_diag ~57% 재확인용)", flush=True)
    print(f"  correct = {a['correct_rate']:.0%} | avg attempts = {a['avg_attempts']} | dist = {a['attempts_dist']}", flush=True)
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
