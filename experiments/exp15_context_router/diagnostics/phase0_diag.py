"""Phase 0 — orchestrator finalization 실패 특성화 (공유 코드 무변경).

run_abc_chain 반환값(tattoo/logs/final_answer)만 계측해 None-finalization 을 분해:
  - finalized?           : final_answer is not None
  - answer_in_tattoo?    : 정답 키워드가 active_assertions 에 존재 (= "추출 가능한 None")
  - death_phase          : 종료 시 phase (SYNTHESIZE 도달 못 하면 final_answer set 불가)
  - judge_ever_converged : C 가 한 번이라도 converged=true (= judge-stuck 여부)
  - n_cycles / n_assertions

단일 attempt(retry 없음)로 raw per-attempt 거동 관찰. grep_only(facet 무) + router +
mandatory, max_cycles=8 (Exp21 동일 설정). megalog task A(finalization-fragile) 주력
+ task B(finalizes 잘 됨) 대조.
"""
import json, statistics, sys, time
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(r"D:\privateProject\gemento\experiments")))
sys.path.insert(0, str(Path(r"D:\privateProject\gemento\experiments\exp15_context_router")))

import run_v21_facet_ab as drv
from orchestrator import run_abc_chain
from native_ollama_caller import make_ollama_native_caller

BASE_URL, MODEL, NUM_CTX, REDIS_KEY = drv.BASE_URL, drv.MODEL, drv.NUM_CTX, drv.REDIS_KEY
MAX_CYCLES = 8
OUT = Path(r"C:\Users\사자\AppData\Local\Temp\claude\D--privateProject-gemento\e0e17d5d-1940-4371-902a-107212495699\scratchpad\phase0_diag_result.json")

CORRECT = {"exp21a_crashloop": "gohttpserver", "exp21b_bruteforce": "45.144.212.75"}
PLAN = {"exp21a_crashloop": 8, "exp21b_bruteforce": 3}   # n per task


def _synth(tt):
    try:
        return " \n ".join(str(getattr(a, "content", "")) for a in tt.active_assertions
                           if getattr(a, "content", None))
    except Exception:
        return ""


def one_chain(task):
    prompt = (f"A diagnostic request for server test9ng. The full systemd journal (30-day window, "
              f"very large) is cached in Redis.\nContext Handle: {REDIS_KEY}\n\n" + task["objective"])
    caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX)   # grep_only
    tt, logs, ans = run_abc_chain(
        task_id=task["id"], objective=task["objective"], prompt=prompt,
        constraints=task["constraints"], max_cycles=MAX_CYCLES, model_caller=caller,
        context_router=True, error_blocks=False, context_handles=[REDIS_KEY],
        mandatory_tool_prompt=True,
    )
    s = _synth(tt).lower()
    kw = CORRECT[task["id"]].lower()
    judge_conv = any((getattr(l, "c_decision", None) or {}).get("converged") for l in logs)
    phases = [getattr(l, "phase", "?") for l in logs]
    return {
        "finalized": ans is not None,
        "answer_in_tattoo": kw in s,
        "death_phase": tt.phase.value,
        "judge_ever_converged": bool(judge_conv),
        "n_cycles": len(logs),
        "n_assertions": len(tt.active_assertions),
        "phases": phases,
        "ans": (ans if not isinstance(ans, str) else ans[:160]),
        "assert_snip": s[:200],
    }


def main():
    print("=" * 80, flush=True)
    print("Phase 0 — finalization 실패 특성화 (grep_only, router+mandatory, max_cycles=8)", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    results = {"experiment": "phase0_finalization_diag", "model": MODEL,
               "max_cycles": MAX_CYCLES, "stack": "grep_only+router+mandatory, single-attempt",
               "by_task": {}}
    t0 = time.time()
    for task in drv.TASKS:
        tid = task["id"]
        n = PLAN[tid]
        print(f"\n  ── Task {tid} (n={n}, correct-kw='{CORRECT[tid]}') ──", flush=True)
        samples = []
        for i in range(1, n + 1):
            r = one_chain(task)
            samples.append(r)
            print(f"  [{tid} {i}/{n}] finalized={r['finalized']} "
                  f"ans_in_tattoo={r['answer_in_tattoo']} death={r['death_phase']} "
                  f"judge_conv={r['judge_ever_converged']} cyc={r['n_cycles']} "
                  f"asrt={r['n_assertions']}", flush=True)
            # 집계
            fin = [x for x in samples if x["finalized"]]
            none = [x for x in samples if not x["finalized"]]
            agg = {
                "n": len(samples),
                "finalized_rate": round(len(fin) / len(samples), 3),
                "none_count": len(none),
                "none_with_answer_in_tattoo": sum(1 for x in none if x["answer_in_tattoo"]),
                "none_without_answer": sum(1 for x in none if not x["answer_in_tattoo"]),
                "judge_ever_converged_rate": round(sum(1 for x in samples if x["judge_ever_converged"]) / len(samples), 3),
                "death_phase_dist": dict(Counter(x["death_phase"] for x in samples)),
                "samples": samples,
            }
            results["by_task"][tid] = agg
            results["elapsed_sec"] = round(time.time() - t0, 1)
            OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 80, flush=True)
    print("Phase 0 분해 결과:", flush=True)
    for tid, a in results["by_task"].items():
        print(f"  [{tid}] finalized={a['finalized_rate']:.0%} | None={a['none_count']} "
              f"(answer_in_tattoo={a['none_with_answer_in_tattoo']} / no_answer={a['none_without_answer']}) "
              f"| judge_conv={a['judge_ever_converged_rate']:.0%} | death={a['death_phase_dist']}", flush=True)
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
