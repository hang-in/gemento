"""Phase 1 lever test — anti-give-up + narrow-query 지시가 finalization 을 회복하나.

관찰된 실패(Phase 0/micro-diag): A 가 넓게 grep('error')→노이즈→"pinpoint 불가"라며
좁히지 않고 포기→assertion 0→empty tattoo→None. 정답은 'Failed with result'/'.service'
로 좁히면 나옴.

레버(프롬프트 only, 공유코드 무변경): constraints 에 narrow-query + no-empty-cycle 지시 주입.
A/B: control(현행 constraints) vs nudge, task A, n=6 씩. finalized/empty-tattoo 율 비교.
"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(r"D:\privateProject\gemento\experiments")))
sys.path.insert(0, str(Path(r"D:\privateProject\gemento\experiments\exp15_context_router")))

import run_v21_facet_ab as drv
from orchestrator import run_abc_chain
from native_ollama_caller import make_ollama_native_caller

BASE_URL, MODEL, NUM_CTX, REDIS_KEY = drv.BASE_URL, drv.MODEL, drv.NUM_CTX, drv.REDIS_KEY
MAX_CYCLES = 8
N = 6
OUT = Path(r"C:\Users\사자\AppData\Local\Temp\claude\D--privateProject-gemento\e0e17d5d-1940-4371-902a-107212495699\scratchpad\lever_test_result.json")
TASK = next(t for t in drv.TASKS if t["id"] == "exp21a_crashloop")

NUDGE = (
    "RETRIEVAL DISCIPLINE (critical): A broad search term (e.g. 'error') returns mostly noise. "
    "Do NOT conclude that you 'cannot pinpoint the cause' — instead NARROW the search: try exact "
    "failure phrases such as 'Failed with result', 'Main process exited', or unit-name patterns "
    "like '.service'. Iterate with more specific patterns until you identify the failing unit. "
    "You MUST record at least one candidate service unit as a new_assertion before ending a cycle; "
    "never finish a cycle empty-handed while the failing unit is still unknown."
)

ARMS = [
    {"id": "control", "extra_constraint": None},
    {"id": "nudge",   "extra_constraint": NUDGE},
]


def one(arm):
    prompt = (f"A diagnostic request for server test9ng. The full systemd journal (30-day window, "
              f"very large) is cached in Redis.\nContext Handle: {REDIS_KEY}\n\n" + TASK["objective"])
    constraints = list(TASK["constraints"])
    if arm["extra_constraint"]:
        constraints = constraints + [arm["extra_constraint"]]
    caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX)
    tt, logs, ans = run_abc_chain(
        task_id=TASK["id"], objective=TASK["objective"], prompt=prompt,
        constraints=constraints, max_cycles=MAX_CYCLES, model_caller=caller,
        context_router=True, error_blocks=False, context_handles=[REDIS_KEY],
        mandatory_tool_prompt=True,
    )
    synth = " \n ".join(str(getattr(a, "content", "")) for a in tt.active_assertions
                        if getattr(a, "content", None)).lower()
    return {
        "finalized": ans is not None,
        "n_assertions": len(tt.active_assertions),
        "answer_in_tattoo": "gohttpserver" in synth,
        "n_cycles": len(logs),
        "death_phase": tt.phase.value,
        "correct": ("gohttpserver" in (str(ans).lower() if ans else "")) if ans else False,
        "ans": (ans if not isinstance(ans, str) else ans[:120]),
    }


def main():
    print("=" * 80, flush=True)
    print(f"Lever test — anti-give-up/narrow-query nudge | task A, n={N}/arm", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    out = {"experiment": "lever_test_narrow_query", "model": MODEL, "task": TASK["id"],
           "n_per_arm": N, "arms": {}}
    t0 = time.time()
    for arm in ARMS:
        aid = arm["id"]
        print(f"\n  ── Arm={aid} ──", flush=True)
        samples = []
        for i in range(1, N + 1):
            r = one(arm)
            samples.append(r)
            fin = sum(1 for x in samples if x["finalized"])
            empty = sum(1 for x in samples if x["n_assertions"] == 0)
            corr = sum(1 for x in samples if x["correct"])
            out["arms"][aid] = {
                "n": len(samples),
                "finalized_rate": round(fin / len(samples), 3),
                "empty_tattoo_rate": round(empty / len(samples), 3),
                "correct_rate": round(corr / len(samples), 3),
                "samples": samples,
            }
            out["elapsed_sec"] = round(time.time() - t0, 1)
            OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  [{aid} {i}/{N}] fin={r['finalized']} asrt={r['n_assertions']} "
                  f"correct={r['correct']} cyc={r['n_cycles']} death={r['death_phase']} "
                  f"| {str(r['ans'])[:80]}", flush=True)

    print("\n" + "=" * 80, flush=True)
    print("Lever test 결과:", flush=True)
    for aid, a in out["arms"].items():
        print(f"  [{aid}] finalized={a['finalized_rate']:.0%} empty_tattoo={a['empty_tattoo_rate']:.0%} "
              f"correct={a['correct_rate']:.0%} (n={a['n']})", flush=True)
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
