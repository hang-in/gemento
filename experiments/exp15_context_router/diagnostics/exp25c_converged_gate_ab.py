"""Exp25c — CONVERGED 게이팅 A/B (converged_requires_answer off vs on).

Exp25b 진단: 비-finalized 의 89% = premature CONVERGED(C 가 답 없이 DECOMPOSE/INVESTIGATE
에서 CONVERGED 월반 → 답 쓰는 phase 스킵 → null). 레버 = CONVERGED 를 final_answer 존재로
게이팅(orchestrator opt-in `converged_requires_answer`), 답 없으면 SYNTHESIZE 로 유도.

이 A/B: 동일 det_planner 셋업(결정론 finding 주입, 도구 없음)에서
  arm OFF  = converged_requires_answer=False (baseline, Exp25b 재현 ~40%)
  arm ON   = converged_requires_answer=True  (게이트, 예측 ~85-90%)
1차 지표 = finalized/correct rate. 안전 지표 = wrong_rate(fail-safe → 0 유지 필수).

판정:
  ON correct >> OFF & wrong 0   → 게이트가 처리량 레버 확증(fail-safe 보존) → Stage 13 채택.
  ON wrong > 0                  → 게이트가 confident-wrong 유입 → 재검토(SYNTHESIZE emit 오답).
  ON ≈ OFF                      → 게이트 무효(월반이 병목 아니었거나 SYNTHESIZE 서도 emit 실패).

실행 (boxie 터널 + Redis 메가로그):
  python -u experiments/exp15_context_router/diagnostics/exp25c_converged_gate_ab.py
"""
import json
import math
import sys
import time
from pathlib import Path

_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_DIR.parent.parent))                 # experiments/
sys.path.insert(0, str(_DIR.parent))                        # exp15_context_router/

import run_v21_facet_ab as drv
import det_planner_probe as probe
from orchestrator import run_abc_chain
from native_ollama_caller import make_ollama_native_caller

N = 15
OUT = _DIR / "exp25c_converged_gate_ab_result.json"


def _wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (round(c - h, 3), round(c + h, 3))


def one(finding: str, gate: bool) -> dict:
    prompt = (
        f"A diagnostic request for server test9ng.\n\n"
        f"DETERMINISTIC EVIDENCE (from an automated systemd failure-signal scan of the full "
        f"journal): the top failing unit is {finding}. This evidence is reliable and already "
        f"gathered — no further searching is needed.\n\n" + probe.TASK["objective"]
    )
    caller = make_ollama_native_caller(probe.BASE_URL, probe.MODEL, num_ctx=probe.NUM_CTX)
    tt, logs, ans = run_abc_chain(
        task_id=probe.TASK["id"], objective=probe.TASK["objective"], prompt=prompt,
        constraints=probe.TASK["constraints"], max_cycles=probe.MAX_CYCLES, model_caller=caller,
        context_router=False, error_blocks=False, context_handles=None,
        mandatory_tool_prompt=False,
        converged_requires_answer=gate,
    )
    reached_productive = any(lg.phase in ("SYNTHESIZE", "VERIFY") for lg in logs)
    return {
        "finalized": ans is not None,
        "correct": (probe.CORRECT_KW in str(ans).lower()) if ans else False,
        "final_phase": tt.phase.value,
        "n_cycles": len(logs),
        "reached_productive": reached_productive,
    }


def _agg(samples):
    n = len(samples)
    if n == 0:
        return {}
    fin = sum(1 for s in samples if s["finalized"])
    corr = sum(1 for s in samples if s["correct"])
    wrong = sum(1 for s in samples if s["finalized"] and not s["correct"])
    prod = sum(1 for s in samples if s["reached_productive"])
    return {
        "n": n,
        "finalized_rate": round(fin / n, 3),
        "correct_rate": round(corr / n, 3),
        "correct_wilson95": _wilson(corr, n),
        "wrong_rate": round(wrong / n, 3),
        "reached_productive_rate": round(prod / n, 3),
        "avg_cycles": round(sum(s["n_cycles"] for s in samples) / n, 2),
    }


def main():
    print("=" * 80, flush=True)
    print(f"Exp25c — CONVERGED 게이팅 A/B (off vs on) | 결정론 finding, 도구 없음, n={N}/arm", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    finding = probe._det_finding()
    if not finding:
        print("  [ABORT] 결정론 finding 못 뽑음"); sys.exit(1)
    print(f"  [결정론 finding] {finding}", flush=True)

    out = {"experiment": "exp25c_converged_gate_ab", "model": drv.MODEL, "task": probe.TASK_ID,
           "n_per_arm": N, "max_cycles": probe.MAX_CYCLES, "finding": finding,
           "arms": {"off": {"samples": []}, "on": {"samples": []}}}
    t0 = time.time()
    # arm 순차: OFF 전체 → ON 전체 (boxie kill 시 부분 저장으로 재개 판단 용이)
    for gate, key in ((False, "off"), (True, "on")):
        for i in range(1, N + 1):
            r = one(finding, gate)
            out["arms"][key]["samples"].append(r)
            out["arms"][key]["agg"] = _agg(out["arms"][key]["samples"])
            out["elapsed_sec"] = round(time.time() - t0, 1)
            OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  [{key} {i}/{N}] final={r['finalized']} corr={r['correct']} "
                  f"prod={r['reached_productive']} cyc={r['n_cycles']} phase={r['final_phase']}",
                  flush=True)

    off, on = out["arms"]["off"]["agg"], out["arms"]["on"]["agg"]
    print("\n" + "=" * 80, flush=True)
    print("Exp25c A/B 결과:", flush=True)
    print(f"  OFF: finalized={off['finalized_rate']:.0%} correct={off['correct_rate']:.0%} "
          f"wrong={off['wrong_rate']:.0%} prod={off['reached_productive_rate']:.0%}", flush=True)
    print(f"  ON : finalized={on['finalized_rate']:.0%} correct={on['correct_rate']:.0%} "
          f"wrong={on['wrong_rate']:.0%} prod={on['reached_productive_rate']:.0%} "
          f"(correct Wilson95={on['correct_wilson95']})", flush=True)
    print(f"  판정: ON correct >> OFF & ON wrong 0 → 게이트가 처리량 레버(fail-safe 보존).", flush=True)
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
