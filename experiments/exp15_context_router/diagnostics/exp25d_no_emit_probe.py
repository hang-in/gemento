"""Exp25d — productive-no-emit 진단 (게이트 ON, 공유코드 무변경, 순수 계측).

Exp25c 잔여 천장: converged_requires_answer=True 로 reached_productive 100% 인데도
finalized 87% — 차이 13%는 SYNTHESIZE/VERIFY 도달 후 A 가 final_answer 를 emit 실패.
이 진단은 그 실패 chain 의 productive cycle A 응답을 뜯어 실패 유형을 분류한다.

목적(권장순서 Step 1): productive-no-emit 이
  (a) 단순 emit 노이즈(파싱 실패 / final_answer 필드 누락 / 빈 값) → **retry 가 값싸게 커버**
      (87% per-attempt + K=3 → ~99.8%). "더 영리한 단발 A-stage 레버" 불필요 = per-attempt 트랙 교훈 재확인.
  (b) 새로운 체계적 실패(예: A 가 특정 이유로 일관되게 emit 거부, 또는 wrong-content emit)
      → 재고 필요.
중 어느 것인지 판별. (a) 확인되면 Exp26(추출기 다종화)로 진행.

분류(비-finalized & reached_productive chain 의 productive cycle A 응답):
  - parse_fail       : A 응답 JSON 파싱 실패
  - no_final_field   : 파싱됐으나 final_answer 필드 없음(assertions/questions 만)
  - empty_final      : final_answer 있으나 falsy(빈 문자열/None)
  - wrong_content    : final_answer 있고 non-empty 인데 정답 키워드 불포함(confident-wrong 후보!)
                       — exp25c wrong 0% 였으니 없어야 정상. 있으면 중요.

실행 (boxie 터널 + Redis 메가로그):
  python -u experiments/exp15_context_router/diagnostics/exp25d_no_emit_probe.py
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
import det_planner_probe as probe
from orchestrator import run_abc_chain
from native_ollama_caller import make_ollama_native_caller

N = 25                                                      # 13% 실패율 → ~3 no-emit chain 기대
OUT = _DIR / "exp25d_no_emit_result.json"
PRODUCTIVE = {"SYNTHESIZE", "VERIFY"}


def _classify_a(a_parsed) -> tuple[str, str]:
    """productive cycle A 응답의 emit 상태 분류. 반환 (mode, final_val_trunc)."""
    if not isinstance(a_parsed, dict):
        return ("parse_fail", "")
    if "final_answer" not in a_parsed:
        return ("no_final_field", "")
    fa = a_parsed.get("final_answer")
    if not fa:
        return ("empty_final", "")
    fa_s = str(fa)
    if probe.CORRECT_KW in fa_s.lower():
        return ("correct_final", fa_s[:120])                # 이 cycle 은 사실 emit 성공(정답)
    return ("wrong_content", fa_s[:120])                     # non-empty but 오답 → confident-wrong 후보


def one(finding: str) -> dict:
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
        converged_requires_answer=True,                     # ★ 게이트 ON
    )
    finalized = ans is not None
    correct = (probe.CORRECT_KW in str(ans).lower()) if ans else False
    reached_productive = any(lg.phase in PRODUCTIVE for lg in logs)

    # productive cycle A 응답 수집
    prod_cycles = []
    for lg in logs:
        if lg.phase in PRODUCTIVE:
            a_parsed = lg.a_log.parsed_response if lg.a_log else None
            mode, fv = _classify_a(a_parsed)
            n_new = len(a_parsed.get("new_assertions", [])) if isinstance(a_parsed, dict) else 0
            reasoning = ""
            if isinstance(a_parsed, dict):
                reasoning = str(a_parsed.get("reasoning") or "")[:180]
            prod_cycles.append({
                "cycle": lg.cycle, "phase": lg.phase, "a_mode": mode,
                "final_val": fv, "n_new_assertions": n_new, "a_reasoning": reasoning,
            })

    # 이 chain 이 no-emit(비-finalized & productive 도달)이면 productive cycle 의 dominant mode
    no_emit = (not finalized) and reached_productive
    prod_modes = [c["a_mode"] for c in prod_cycles]
    return {
        "finalized": finalized, "correct": correct, "reached_productive": reached_productive,
        "no_emit": no_emit, "n_cycles": len(logs), "n_prod_cycles": len(prod_cycles),
        "prod_cycle_modes": prod_modes, "prod_cycles": prod_cycles,
    }


def main():
    print("=" * 80, flush=True)
    print(f"Exp25d — productive-no-emit 진단 | 게이트 ON, 결정론 finding, n={N}", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    finding = probe._det_finding()
    if not finding:
        print("  [ABORT] 결정론 finding 못 뽑음"); sys.exit(1)
    print(f"  [결정론 finding] {finding}", flush=True)

    out = {"experiment": "exp25d_no_emit", "model": drv.MODEL, "task": probe.TASK_ID,
           "n": N, "gate": "converged_requires_answer=True", "finding": finding, "samples": []}
    t0 = time.time()
    samples = []
    for i in range(1, N + 1):
        r = one(finding)
        samples.append(r)
        n = len(samples)
        no_emit = [s for s in samples if s["no_emit"]]
        # no-emit chain 들의 productive cycle mode 분포
        ne_modes = Counter(m for s in no_emit for m in s["prod_cycle_modes"])
        out["samples"] = samples
        out["agg"] = {
            "n": n,
            "finalized_rate": round(sum(1 for s in samples if s["finalized"]) / n, 3),
            "reached_productive_rate": round(sum(1 for s in samples if s["reached_productive"]) / n, 3),
            "no_emit_count": len(no_emit),
            "no_emit_rate": round(len(no_emit) / n, 3),
            "no_emit_prod_mode_dist": dict(ne_modes),        # ← 핵심: 실패 chain productive A 유형
            "wrong_content_count": ne_modes.get("wrong_content", 0),  # confident-wrong 후보(0 기대)
        }
        out["elapsed_sec"] = round(time.time() - t0, 1)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [{i}/{N}] final={r['finalized']} prod={r['reached_productive']} "
              f"no_emit={r['no_emit']} prod_modes={r['prod_cycle_modes']}", flush=True)

    a = out["agg"]
    print("\n" + "=" * 80, flush=True)
    print("Exp25d 결과:", flush=True)
    print(f"  finalized={a['finalized_rate']:.0%} reached_productive={a['reached_productive_rate']:.0%} "
          f"no_emit={a['no_emit_count']}/{a['n']} ({a['no_emit_rate']:.0%})", flush=True)
    print(f"  no-emit chain productive A 유형 분포: {a['no_emit_prod_mode_dist']}", flush=True)
    print(f"  wrong_content(confident-wrong 후보, 0 기대) = {a['wrong_content_count']}", flush=True)
    print(f"  판정: no_final_field/parse_fail/empty_final 우세 → 단순 emit 노이즈 = retry 커버 → Exp26 진행.", flush=True)
    print(f"        wrong_content>0 → 새 체계적 실패(fail-safe 위협) → 재고.", flush=True)
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
