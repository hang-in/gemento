"""Exp25b — C(판정자) 수렴 병목 진단 (공유코드 무변경, 순수 계측).

배경: det_planner_probe/Exp25 는 결정론 finding 을 clean 주입해도 first-attempt finalized
~20-33% 임을 확인. Exp25 는 이를 retry(K=5→67%)로 매입했으나 처리량 병목이
A-stage(emit)에서 C-stage(수렴)로 이동. 이 진단은 '어디서 멈추나' 를 국소화한다.

중요(코드 리딩 결과): run_abc_chain 의 C 처리에는 confidence 게이트가 없다. C 출력은
converged(bool)/next_phase/reasoning 뿐. 실제 phase 전진 메커니즘 =
  (a) C 가 converged=true + 유효 next_phase 를 내면 전진, 또는
  (b) safety-limit (MAX_CYCLES_PER_PHASE=3 cyc/phase) 로만 전진.
final_answer 는 A 가 SYNTHESIZE/VERIFY phase 에서 emit(PHASE_DIRECTIVES). 따라서
finalized 되려면 chain 이 SYNTHESIZE/VERIFY(=productive) 로 전진 + 거기서 A 가 emit 해야.

두 stall point 후보:
  (1) C 가 converged 를 안 내서 phase 가 safety(3 cyc/phase)로만 기어감
      → max_cycles=8 안에 productive 미도달.  → 레버 = C 프롬프트/termination.
  (2) productive 도달했으나 A 가 final_answer emit 안 함.  → 레버 = SYNTHESIZE 지시.

수집(chain별): cycle 궤적(phase / c_converged / c_next_phase / transition(C vs safety) /
a_final / c_reasoning). 집계: 비-finalized chain 중 productive 미도달 vs 도달-emit실패 비율.

실행 (boxie 터널 + Redis 메가로그):
  python -u experiments/exp15_context_router/diagnostics/exp25b_c_convergence_probe.py
"""
import json
import sys
import time
from collections import Counter
from pathlib import Path

_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_DIR.parent.parent))                 # experiments/
sys.path.insert(0, str(_DIR.parent))                        # exp15_context_router/

import run_v21_facet_ab as drv
import det_planner_probe as probe                            # _det_finding / TASK / CORRECT_KW 재사용
from orchestrator import run_abc_chain
from native_ollama_caller import make_ollama_native_caller

N = 15
OUT = _DIR / "exp25b_c_convergence_result.json"

PHASE_RANK = {"DECOMPOSE": 0, "INVESTIGATE": 1, "SYNTHESIZE": 2, "VERIFY": 3, "CONVERGED": 4}
PRODUCTIVE = {"SYNTHESIZE", "VERIFY"}


def one_trace(finding: str) -> dict:
    """probe.one 과 동일 체인(결정론 finding 주입, 도구 없음)을 돌리되 cycle logs 를 계측한다."""
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
    )

    # ── cycle 궤적 재구성 ──
    traj = []
    for i, lg in enumerate(logs):
        cd = lg.c_decision or {}
        a_parsed = lg.a_log.parsed_response if lg.a_log else None
        a_final = bool(a_parsed.get("final_answer")) if isinstance(a_parsed, dict) else False
        # transition 유형: phase_transition 필드가 있으면 C-driven. 아니면 다음 cycle 과 phase
        # 비교로 safety-driven 추정(마지막 cycle 은 next 없음).
        next_phase_actual = logs[i + 1].phase if i + 1 < len(logs) else None
        c_driven = bool(lg.phase_transition)
        safety_driven = (
            not c_driven and next_phase_actual is not None and next_phase_actual != lg.phase
        )
        traj.append({
            "cycle": lg.cycle,
            "phase": lg.phase,
            "c_converged": cd.get("converged") if lg.c_decision is not None else None,
            "c_next_phase": cd.get("next_phase") if lg.c_decision is not None else None,
            "c_error": lg.c_error,
            "transition": lg.phase_transition,             # C-driven 이면 "OLD→NEW"
            "c_driven_transition": c_driven,
            "safety_driven_transition": safety_driven,
            "a_final": a_final,
            "c_reasoning": (str(cd.get("reasoning") or ""))[:220],
        })

    phases_seen = [t["phase"] for t in traj]
    max_rank = max((PHASE_RANK.get(p, -1) for p in phases_seen), default=-1)
    reached_productive = any(p in PRODUCTIVE for p in phases_seen)
    emitted_final_in_productive = any(t["a_final"] and t["phase"] in PRODUCTIVE for t in traj)
    converge_events = sum(1 for t in traj if t["c_converged"] is True)
    safety_events = sum(1 for t in traj if t["safety_driven_transition"])
    c_parse_fail = sum(1 for t in traj if t["c_converged"] is None)

    finalized = ans is not None
    correct = (probe.CORRECT_KW in str(ans).lower()) if ans else False

    return {
        "finalized": finalized,
        "correct": correct,
        "final_phase": tt.phase.value,
        "n_cycles": len(logs),
        "max_phase_reached": max((p for p in phases_seen), key=lambda x: PHASE_RANK.get(x, -1),
                                 default=None),
        "max_rank": max_rank,
        "reached_productive": reached_productive,
        "emitted_final_in_productive": emitted_final_in_productive,
        "converge_events": converge_events,       # C 가 converged=true 낸 횟수
        "safety_events": safety_events,            # safety-limit 로 강제전이된 횟수
        "c_parse_fail_cycles": c_parse_fail,       # C 응답 파싱 실패 cycle 수
        "trajectory": traj,
    }


def _bucket(samples):
    """비-finalized chain 을 병목 유형별로 분류."""
    non_final = [s for s in samples if not s["finalized"]]
    b = {
        "non_finalized": len(non_final),
        # 유형1: productive(SYNTHESIZE/VERIFY) 미도달 → C 수렴/phase advance 병목
        "stall_before_productive": sum(1 for s in non_final if not s["reached_productive"]),
        # 유형2: productive 도달했으나 emit 실패 → productive emit 병목
        "stall_productive_no_emit": sum(
            1 for s in non_final if s["reached_productive"] and not s["emitted_final_in_productive"]
        ),
        # 유형3: emit 했는데도 non-finalized (이론상 드묾 — 진단 sanity)
        "emitted_but_not_final": sum(
            1 for s in non_final if s["emitted_final_in_productive"]
        ),
    }
    return b


def main():
    print("=" * 80, flush=True)
    print(f"Exp25b — C 수렴 병목 진단 | 결정론 finding, 도구 없음, n={N}, max_cycles={probe.MAX_CYCLES}", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    finding = probe._det_finding()
    if not finding:
        print("  [ABORT] 결정론 finding 못 뽑음"); sys.exit(1)
    print(f"  [결정론 finding] {finding}", flush=True)

    out = {"experiment": "exp25b_c_convergence", "model": drv.MODEL, "task": probe.TASK_ID,
           "n": N, "max_cycles": probe.MAX_CYCLES, "finding": finding, "samples": []}
    t0 = time.time()
    samples = []
    for i in range(1, N + 1):
        r = one_trace(finding)
        samples.append(r)
        n = len(samples)
        out["samples"] = samples
        out["agg"] = {
            "n": n,
            "finalized_rate": round(sum(1 for s in samples if s["finalized"]) / n, 3),
            "correct_rate": round(sum(1 for s in samples if s["correct"]) / n, 3),
            "reached_productive_rate": round(sum(1 for s in samples if s["reached_productive"]) / n, 3),
            "avg_converge_events": round(sum(s["converge_events"] for s in samples) / n, 2),
            "avg_safety_events": round(sum(s["safety_events"] for s in samples) / n, 2),
            "avg_cycles": round(sum(s["n_cycles"] for s in samples) / n, 2),
            "avg_c_parse_fail_cycles": round(sum(s["c_parse_fail_cycles"] for s in samples) / n, 2),
            "max_phase_dist": dict(Counter(s["max_phase_reached"] for s in samples)),
            "final_phase_dist": dict(Counter(s["final_phase"] for s in samples)),
            "bottleneck_buckets": _bucket(samples),
        }
        out["elapsed_sec"] = round(time.time() - t0, 1)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [{i}/{N}] final={r['finalized']} corr={r['correct']} "
              f"maxphase={r['max_phase_reached']} prod={r['reached_productive']} "
              f"emit={r['emitted_final_in_productive']} Cconv={r['converge_events']} "
              f"safety={r['safety_events']} cyc={r['n_cycles']}", flush=True)

    a = out["agg"]
    bk = a["bottleneck_buckets"]
    print("\n" + "=" * 80, flush=True)
    print("Exp25b 결과:", flush=True)
    print(f"  finalized={a['finalized_rate']:.0%} correct={a['correct_rate']:.0%} "
          f"reached_productive={a['reached_productive_rate']:.0%}", flush=True)
    print(f"  avg converge_events(C가 converged 낸 횟수)={a['avg_converge_events']} "
          f"| avg safety_events={a['avg_safety_events']} | avg cycles={a['avg_cycles']}", flush=True)
    print(f"  max_phase 분포: {a['max_phase_dist']}", flush=True)
    print(f"  병목 분류(비-finalized {bk['non_finalized']}개 중): "
          f"productive 미도달={bk['stall_before_productive']} "
          f"| productive 도달-emit실패={bk['stall_productive_no_emit']} "
          f"| emit했으나 non-final={bk['emitted_but_not_final']}", flush=True)
    print(f"  판정: productive 미도달 우세 → 레버=C 수렴(phase advance). "
          f"emit실패 우세 → 레버=SYNTHESIZE 지시.", flush=True)
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
