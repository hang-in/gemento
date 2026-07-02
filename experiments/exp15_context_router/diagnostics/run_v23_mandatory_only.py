"""Exp23 fu_mandatory arm 단독 완주 러너 (control/offered 는 이미 pooled n~30 견고).

배경: run_v23_failed_units_ab.py 는 arm 을 순차 실행 → 마지막 arm(fu_mandatory)이
GPU 간헐 부하로 매번 preempt(2회 run 다 control+offered 만 완주). 이 arm 만 단독으로
n=15 완주시켜 3-arm 판정을 완성한다. 드라이버 함수(`_run_one`, `ARMS`) 재사용 — 무변경.

결과 별도 저장: diagnostics/v23_mandatory_only_result.json (기존 v23 JSON 무건드림).
kill 시 이 arm 만 재실행하면 됨(control/offered 재실행 불필요).

실행 (boxie 터널 필요):
  python -u experiments/exp15_context_router/diagnostics/run_v23_mandatory_only.py
"""
import json
import sys
import time
from pathlib import Path

_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_DIR.parent))                        # exp15_context_router/
sys.path.insert(0, str(_DIR.parent.parent))                # experiments/

import run_v23_failed_units_ab as drv23
from run_v23_failed_units_ab import _run_one, ARMS, N_TRIALS, MAX_CYCLES, TASK_ID, MODEL

ARM = next(a for a in ARMS if a["id"] == "fu_mandatory")
OUT = _DIR / "v23_mandatory_only_result.json"


def main():
    print("=" * 80, flush=True)
    print(f"Exp23 fu_mandatory 단독 완주 — task A, n={N_TRIALS}, single-attempt", flush=True)
    print("=" * 80, flush=True)
    if not drv23.drv._healthcheck():
        sys.exit(1)
    drv23.drv._load_megalog_to_redis()

    out = {"experiment": "exp23_fu_mandatory_only", "model": MODEL, "task": TASK_ID,
           "n_trials": N_TRIALS, "max_cycles": MAX_CYCLES, "arm": "fu_mandatory", "samples": []}
    t0 = time.time()
    samples = []
    for i in range(1, N_TRIALS + 1):
        r = _run_one(ARM)
        samples.append(r)
        n = len(samples)
        fin = sum(1 for x in samples if x["finalized"])
        corr = sum(1 for x in samples if x["correct"])
        used = sum(1 for x in samples if x["used_fu"])
        out["samples"] = samples
        out["agg"] = {"n": n, "finalized_rate": round(fin / n, 3),
                      "correct_rate": round(corr / n, 3), "used_fu_rate": round(used / n, 3)}
        out["elapsed_sec"] = round(time.time() - t0, 1)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [fu_mandatory {i}/{N_TRIALS}] finalized={r['finalized']} correct={r['correct']} "
              f"used_fu={r['used_fu']} asrt={r['n_assertions']} cyc={r['n_cycles']}", flush=True)

    a = out["agg"]
    print("\n" + "=" * 80, flush=True)
    print(f"fu_mandatory: finalized={a['finalized_rate']:.0%} correct={a['correct_rate']:.0%} "
          f"used_fu={a['used_fu_rate']:.0%} (n={a['n']})", flush=True)
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
