"""Exp24 — A2A Planner→Executor A/B: control(monolithic A) vs a2a(Planner→Executor).

Task 01(완료)에서 `run_abc_chain(..., a2a_proposer=...)` 플래그가 추가됨. 이 플래그가
per-attempt 결과(finalized/correct/assertion 수/cycle 수)에 미치는 영향을 검증. 2 arm 의
유일한 차이는 `run_abc_chain` 에 넘기는 `a2a_proposer` 값 (control=False, a2a=True) 뿐이다.

run_v21_facet_ab.py 인프라(BASE_URL/MODEL/NUM_CTX/REDIS_KEY/TASKS/_healthcheck/
_load_megalog_to_redis) 를 그대로 재사용(모듈 import, 무변경). run_v23_failed_units_ab.py
의 드라이버 패턴(단일 task, single-attempt, 증분 durable JSON)을 그대로 복제.
**single-attempt**(retry 없음), task = exp21a_crashloop 만, n=15/arm.

arm:
  - control: a2a_proposer=False (기존 monolithic A/제안자)
  - a2a:     a2a_proposer=True  (Planner→Executor 분리)

측정(trial 별): finalized(ans is not None), correct("gohttpserver" in ans.lower()),
n_assertions(len(tt.active_assertions)), n_cycles(len(logs)).

사용자/에이전트 실행 (boxie e4b 터널(11435) + Redis 메가로그 키 필요):
  python -u experiments/exp15_context_router/run_v24_a2a_ab.py
  환경변수 EXP20_LOG_PATH 로 메가로그 파일 경로 오버라이드 가능(run_v21_facet_ab.py 참조).
  진척: diagnostics/v24_a2a_result.json 의 arms.*.{finalized_rate,correct_rate} 확인.
  trial 마다 증분 write(중단 내성).

  **GPU 부하 대비**: a2a arm 은 Planner+Executor 2단계 호출 → control 대비 비용/시간이
  더 든다. §21 교훈대로 arm 순차 preempt(선점) 가능성이 있음 — 드라이버는 arm 별로
  완주 후 다음 arm 으로 진행하되, 매 trial 증분 저장이므로 중단되어도 그때까지의
  결과는 diagnostics/v24_a2a_result.json 에 보존된다.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # experiments/ (tools 패키지용)

from orchestrator import run_abc_chain
from native_ollama_caller import make_ollama_native_caller

import run_v21_facet_ab as drv  # BASE_URL/MODEL/NUM_CTX/REDIS_KEY/TASKS/_healthcheck/_load_megalog_to_redis 재사용

BASE_URL, MODEL, NUM_CTX, REDIS_KEY = drv.BASE_URL, drv.MODEL, drv.NUM_CTX, drv.REDIS_KEY
MAX_CYCLES = 8
N_TRIALS = 15
TASK_ID = "exp21a_crashloop"
CORRECT_KW = "gohttpserver"

TASK = next(t for t in drv.TASKS if t["id"] == TASK_ID)

_DIR = Path(__file__).resolve().parent
OUT_PATH = _DIR / "diagnostics" / "v24_a2a_result.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── arm 정의 (a2a_proposer 플래그만 다름) ────────────────────────────────────
ARMS = [
    {"id": 'control', "a2a": False},
    {"id": 'a2a',     "a2a": True},
]


def _run_one(arm: dict) -> dict:
    """task 를 주어진 arm 으로 single-attempt 실행. trial 별 metric dict 반환."""
    prompt = (
        f"A diagnostic request for server test9ng. The full systemd journal (30-day window, "
        f"very large) is cached in Redis.\nContext Handle: {REDIS_KEY}\n\n"
        + TASK["objective"]
    )
    constraints = list(TASK["constraints"])

    caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX)
    tt, logs, ans = run_abc_chain(
        task_id=TASK["id"], objective=TASK["objective"], prompt=prompt,
        constraints=constraints, max_cycles=MAX_CYCLES, model_caller=caller,
        context_router=True, error_blocks=False, context_handles=[REDIS_KEY],
        mandatory_tool_prompt=True, a2a_proposer=arm["a2a"],
    )

    finalized = ans is not None
    correct = (CORRECT_KW in str(ans).lower()) if ans else False
    return {
        "finalized": finalized,
        "correct": correct,
        "n_assertions": len(tt.active_assertions),
        "n_cycles": len(logs),
        "ans": (ans if not isinstance(ans, str) else ans[:200]),
    }


def main():
    print("=" * 80, flush=True)
    print(
        f"Exp24 A2A Planner-Executor A/B — test9ng crashloop task → boxie {MODEL} | "
        f"n={N_TRIALS}/arm, max_cycles={MAX_CYCLES}, single-attempt",
        flush=True,
    )
    print("  arms: control(a2a_proposer=False) vs a2a(a2a_proposer=True) | 지표: finalized/correct rate", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    out = {
        "experiment": "exp24_a2a_ab",
        "model": MODEL,
        "task": TASK_ID,
        "n_trials": N_TRIALS,
        "max_cycles": MAX_CYCLES,
        "arms": {},
    }
    t0 = time.time()
    for arm in ARMS:
        aid = arm["id"]
        print(f"\n  ── Arm={aid} ──", flush=True)
        samples = []
        for i in range(1, N_TRIALS + 1):
            r = _run_one(arm)
            samples.append(r)

            n = len(samples)
            fin = sum(1 for x in samples if x["finalized"])
            corr = sum(1 for x in samples if x["correct"])
            out["arms"][aid] = {
                "n": n,
                "finalized_rate": round(fin / n, 3),
                "correct_rate": round(corr / n, 3),
                "samples": samples,
            }
            out["elapsed_sec"] = round(time.time() - t0, 1)
            with open(OUT_PATH, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)

            print(
                f"  [{aid} {i}/{N_TRIALS}] finalized={r['finalized']} correct={r['correct']} "
                f"asrt={r['n_assertions']} cyc={r['n_cycles']} "
                f"| ans={str(r['ans'])[:100]}",
                flush=True,
            )

    print("\n" + "=" * 80, flush=True)
    print("Exp24 A2A Planner-Executor A/B 결과:", flush=True)
    for aid, a in out["arms"].items():
        print(
            f"  [{aid}] finalized={a['finalized_rate']:.0%} correct={a['correct_rate']:.0%} (n={a['n']})",
            flush=True,
        )
    print(f"  → {OUT_PATH}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
