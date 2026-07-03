"""Exp25 척추 확인 — 결정론 finding + retry-on-None (fail-safe + throughput, 공유코드 무변경).

det_planner_probe 발견: 결정론 finding 주입 시 correct==finalized(단발 33%, n=15) =
finalized-but-wrong 0 = fail-safe(정답 아니면 침묵). 단발 33% 는 C 수렴 ceiling.
로그분석가 아키텍처(logAnalystDesign §1) = 결정론 추출기 + clean executor + **retry**.

이 실험: det_planner_probe.one() 을 retry-on-None(최대 K회)으로 감싸 safe None 을
정답으로 매입 → correct_after_retry ~87%+/wrong 0 실측(fail-safe n↑ 재확인, §20 retry
binomial 스케일이 이 경로에도 성립하나).

판정:
  correct ~87%+ & wrong 0  → 아키텍처 척추 확증(결정론+retry=안전·결국정답) → 로그분석가 plan.
  wrong > 0                → fail-safe 깨짐(det_planner_probe 소표본 착시) → 재검토.
  correct 낮음             → retry 로도 C 수렴 부족 → K↑ 또는 C-stage 손봐야.

실행 (boxie 터널 + Redis 메가로그):
  python -u experiments/exp15_context_router/diagnostics/det_planner_retry.py
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_DIR.parent.parent))                 # experiments/
sys.path.insert(0, str(_DIR.parent))                        # exp15_context_router/

import time
import run_v21_facet_ab as drv
import det_planner_probe as probe                            # one(finding) / _det_finding 재사용

N = 15
K = 5                                                        # retry-on-None 최대 시도
OUT = _DIR / "det_planner_retry_result.json"


def _wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (round(c - h, 3), round(c + h, 3))


def one_trial(finding: str) -> dict:
    """retry-on-None: finalized 될 때까지 최대 K회. 각 시도 correct 도 기록(wrong 감지)."""
    first_finalized = None
    any_wrong = False
    for attempt in range(1, K + 1):
        r = probe.one(finding)                               # 결정론 finding 주입 + 도구없는 full 체인
        if attempt == 1:
            first_finalized = r["finalized"]
        if r["finalized"]:
            # 결정론 finding 이라 correct 여야 함. wrong 이면 fail-safe 파손.
            return {"finalized": True, "attempts": attempt, "correct": r["correct"],
                    "any_wrong_before_final": any_wrong, "first_attempt_finalized": first_finalized}
        # finalized 아니면 None(안전) — 다음 시도
    return {"finalized": False, "attempts": K, "correct": False,
            "any_wrong_before_final": any_wrong, "first_attempt_finalized": first_finalized}


def main():
    print("=" * 80, flush=True)
    print(f"Exp25 척추 — 결정론 finding + retry-on-None K={K} | task A, n={N}", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    finding = probe._det_finding()
    if not finding:
        print("  [ABORT] finding 못 뽑음"); sys.exit(1)
    print(f"  [결정론 finding] {finding}", flush=True)

    out = {"experiment": "det_planner_retry", "model": drv.MODEL, "task": probe.TASK_ID,
           "n": N, "K": K, "finding": finding, "samples": []}
    t0 = time.time()
    samples = []
    for i in range(1, N + 1):
        r = one_trial(finding)
        samples.append(r)
        n = len(samples)
        fin = sum(1 for x in samples if x["finalized"])
        corr = sum(1 for x in samples if x["correct"])
        wrong = sum(1 for x in samples if x["finalized"] and not x["correct"])
        first = sum(1 for x in samples if x["first_attempt_finalized"])
        out["samples"] = samples
        out["agg"] = {
            "n": n,
            "finalized_after_retry": round(fin / n, 3),
            "correct_after_retry": round(corr / n, 3),
            "correct_wilson95": _wilson(corr, n),
            "wrong_rate": round(wrong / n, 3),                # fail-safe → 0 기대
            "first_attempt_finalized": round(first / n, 3),   # det_planner_probe ~33% 재확인
            "avg_attempts": round(sum(x["attempts"] for x in samples) / n, 2),
            "attempts_dist": dict(Counter(x["attempts"] for x in samples)),
        }
        out["elapsed_sec"] = round(time.time() - t0, 1)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [{i}/{N}] finalized={r['finalized']} correct={r['correct']} "
              f"attempts={r['attempts']} first_ok={r['first_attempt_finalized']}", flush=True)

    a = out["agg"]
    print("\n" + "=" * 80, flush=True)
    print("Exp25 척추 결과:", flush=True)
    print(f"  correct_after_retry = {a['correct_after_retry']:.0%} "
          f"(n={a['n']}, Wilson95={a['correct_wilson95']})", flush=True)
    print(f"  wrong_rate = {a['wrong_rate']:.0%}  (fail-safe → 0 기대)", flush=True)
    print(f"  first-attempt finalized = {a['first_attempt_finalized']:.0%} "
          f"(det_planner_probe 33% 재확인)", flush=True)
    print(f"  avg attempts = {a['avg_attempts']}  dist = {a['attempts_dist']}", flush=True)
    print(f"  판정: correct ~87%+ & wrong 0 → 척추 확증(로그분석가 아키텍처)", flush=True)
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
