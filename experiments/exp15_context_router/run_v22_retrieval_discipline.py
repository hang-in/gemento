"""Exp22 — retrieval_discipline_prompt opt-in 재검증 A/B (Task 01 편입 후 정식 드라이버).

레버 A/B(`diagnostics/lever_test.py`)의 후속: 그 실험은 (1) n=6 소표본
(2) task A(crashloop) 만 (3) nudge 문자열을 `constraints` 에 **수동 주입**(실제
편입 경로 아님) (4) 결과가 scratchpad 에만 저장되어 소실됐다. Task 01
(`orchestrator.run_abc_chain(retrieval_discipline_prompt=...)`) 편입 이후,
이 드라이버는 실제 opt-in 플래그 경로로 재검증한다:
  - control  = run_abc_chain(..., mandatory_tool_prompt=True, retrieval_discipline_prompt=False)
  - discipline = run_abc_chain(..., mandatory_tool_prompt=True, retrieval_discipline_prompt=True)
  (mandatory_tool_prompt=True 는 양 arm 공통 — discipline 플래그만 토글)
  - n=10/arm, task A(exp21a_crashloop) + task B(exp21b_bruteforce) 둘 다
  - 결과 JSON 을 scratchpad 아닌 diagnostics/ 에 durable 저장 (매 trial 증분 write)

인프라(BASE_URL/MODEL/NUM_CTX/REDIS_KEY/TASKS/_healthcheck/_load_megalog_to_redis)는
`run_v21_facet_ab.py` 를 재사용한다(read-only import, 수정 없음).

사용자 실행 (터널 필요 — 에이전트는 실행 금지):
  ssh 터널(11435) 수립 + boxie ollama healthcheck 후:
    python -u experiments/exp15_context_router/run_v22_retrieval_discipline.py
  EXP20_LOG_PATH 환경변수로 메가로그 파일 경로 오버라이드 가능
  (run_v21_facet_ab.py 의 _load_megalog_to_redis 가 읽음).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_DIR))
sys.path.insert(0, str(_DIR.parent))

import run_v21_facet_ab as drv  # noqa: E402  (재사용: BASE_URL/MODEL/NUM_CTX/REDIS_KEY/TASKS/_healthcheck/_load_megalog_to_redis)
from orchestrator import run_abc_chain  # noqa: E402
from native_ollama_caller import make_ollama_native_caller  # noqa: E402

BASE_URL, MODEL, NUM_CTX, REDIS_KEY = drv.BASE_URL, drv.MODEL, drv.NUM_CTX, drv.REDIS_KEY
MAX_CYCLES = 8
N = 10  # arm 당 (레버 하네스 n=6 → 결정 3 에 따라 10 으로 증가)

DIAG_DIR = _DIR / "diagnostics"
DIAG_DIR.mkdir(parents=True, exist_ok=True)
OUT = DIAG_DIR / "v22_retrieval_discipline_result.json"

TASK_IDS = ["exp21a_crashloop", "exp21b_bruteforce"]
TASKS = [t for t in drv.TASKS if t["id"] in TASK_IDS]

# task 별 정답 판정 키워드 (run_v21_facet_ab.py TASKS["keywords"] 참조, task 별로 분리).
#   exp21a_crashloop: keywords=[["gohttpserver"], ["failed"]] → 1차 지표로 "gohttpserver" 사용
#     (lever_test.py 의 correct 판정과 동일 키워드).
#   exp21b_bruteforce: keywords=[["45.144.212.75"]] (최다 brute-force IP, ×286/총 5093건 —
#     run_v21_facet_ab.py TASKS 정의부 주석 그대로 인용).
CORRECT_KEYWORD = {
    "exp21a_crashloop": "gohttpserver",
    "exp21b_bruteforce": "45.144.212.75",
}

# arm 은 constraints 수동 주입이 아니라 run_abc_chain 플래그로만 분기.
# mandatory_tool_prompt=True 는 양 arm 공통(레버 하네스와 동일 조건) — discipline 만 토글.
ARMS = [
    {"id": "control", "retrieval_discipline_prompt": False},
    {"id": "discipline", "retrieval_discipline_prompt": True},
]


def one(task: dict, arm: dict) -> dict:
    prompt = (
        f"A diagnostic request for server test9ng. The full systemd journal (30-day window, "
        f"very large) is cached in Redis.\nContext Handle: {REDIS_KEY}\n\n" + task["objective"]
    )
    caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX)
    tt, logs, ans = run_abc_chain(
        task_id=task["id"], objective=task["objective"], prompt=prompt,
        constraints=task["constraints"], max_cycles=MAX_CYCLES, model_caller=caller,
        context_router=True, error_blocks=False, context_handles=[REDIS_KEY],
        mandatory_tool_prompt=True,
        retrieval_discipline_prompt=arm["retrieval_discipline_prompt"],
    )
    keyword = CORRECT_KEYWORD[task["id"]]
    ans_low = str(ans).lower() if ans else ""
    return {
        "finalized": ans is not None,
        "n_assertions": len(tt.active_assertions),
        "n_cycles": len(logs),
        "death_phase": tt.phase.value,
        "correct": (keyword in ans_low) if ans else False,
        "ans": (ans if not isinstance(ans, str) else ans[:120]),
    }


def main():
    print("=" * 80, flush=True)
    print(
        f"Exp22 retrieval_discipline_prompt 재검증 A/B — control vs discipline | "
        f"tasks={TASK_IDS} n={N}/arm max_cycles={MAX_CYCLES}",
        flush=True,
    )
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    out = {
        "experiment": "v22_retrieval_discipline",
        "model": MODEL,
        "n_per_arm": N,
        "max_cycles": MAX_CYCLES,
        "task_ids": TASK_IDS,
        "tasks": {},
    }
    t0 = time.time()

    for task in TASKS:
        tid = task["id"]
        out["tasks"][tid] = {}
        print(f"\n  ══ Task={tid} ══", flush=True)

        for arm in ARMS:
            aid = arm["id"]
            print(f"\n  ── Arm={aid} ──", flush=True)
            samples = []
            for i in range(1, N + 1):
                r = one(task, arm)
                samples.append(r)
                fin = sum(1 for x in samples if x["finalized"])
                empty = sum(1 for x in samples if x["n_assertions"] == 0)
                corr = sum(1 for x in samples if x["correct"])
                out["tasks"][tid][aid] = {
                    "n": len(samples),
                    "finalized_rate": round(fin / len(samples), 3),
                    "empty_tattoo_rate": round(empty / len(samples), 3),
                    "correct_rate": round(corr / len(samples), 3),
                    "samples": samples,
                }
                out["elapsed_sec"] = round(time.time() - t0, 1)
                OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
                print(
                    f"  [{tid}|{aid} {i}/{N}] fin={r['finalized']} asrt={r['n_assertions']} "
                    f"correct={r['correct']} cyc={r['n_cycles']} death={r['death_phase']} "
                    f"| {str(r['ans'])[:80]}",
                    flush=True,
                )

    print("\n" + "=" * 80, flush=True)
    print("Exp22 재검증 A/B 결과:", flush=True)
    for tid, arms_data in out["tasks"].items():
        for aid, a in arms_data.items():
            print(
                f"  [{tid}|{aid}] finalized={a['finalized_rate']:.0%} "
                f"empty_tattoo={a['empty_tattoo_rate']:.0%} correct={a['correct_rate']:.0%} "
                f"(n={a['n']})",
                flush=True,
            )
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
