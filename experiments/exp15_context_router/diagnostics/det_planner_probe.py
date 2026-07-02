"""로그 분석가 척추 probe — 결정론적 finding → full ABC 체인이 정답 수렴하나 (공유코드 무변경).

배경: per-attempt 트랙(§20~22) 종결 후 방향을 '로그 분석 어시스턴트'로 재정의.
핵심 아키텍처 후보 = 결정론적 추출기(list_failed_units, judgment 불필요)로 finding 을
뽑고, e4b 는 언어화만. Exp24 a2a 는 LLM planner 가 finding 을 87% 틀렸으나, 결정론
추출기는 gohttpserver.service 를 항상 정답 반환(505,848 신호 #1).

미검증 링크: finding 을 결정론적으로 뽑아 **깨끗이 주입**하면 full ABC(A emit→B→C→finalize)가
정답으로 수렴하는가? (scoped_emit_probe 는 A emit 만 100% 확인. B/C 수렴은 미검증 —
Exp23 fu_mandatory 는 도구 결과를 reasoning 내서 받고 53%. 여기선 clean prompt 주입.)

설계: finding = list_failed_units(handle)[0] (결정론). prompt 에 clean 주입, 도구 없음
(context_router=False, mandatory=False), full run_abc_chain, task A, n=15.
판정: finalized/correct ~90%+ → 척추 작동, 로그분석가 아키텍처 plan. ~50% → B/C ceiling.

실행 (boxie 터널 + Redis 메가로그):
  python -u experiments/exp15_context_router/diagnostics/det_planner_probe.py
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
from tools import list_failed_units
from orchestrator import run_abc_chain
from native_ollama_caller import make_ollama_native_caller

BASE_URL, MODEL, NUM_CTX, REDIS_KEY = drv.BASE_URL, drv.MODEL, drv.NUM_CTX, drv.REDIS_KEY
MAX_CYCLES = 8
N = 15
TASK_ID = "exp21a_crashloop"
CORRECT_KW = "gohttpserver"
OUT = _DIR / "det_planner_probe_result.json"

TASK = next(t for t in drv.TASKS if t["id"] == TASK_ID)


def _wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (round(c - h, 3), round(c + h, 3))


def _det_finding() -> str:
    """결정론적 추출기 — list_failed_units 로 top 실패 unit (judgment 없음)."""
    out = list_failed_units(REDIS_KEY, top_n=3)
    if out.get("error") or not out.get("top"):
        return ""
    top = out["top"][0]
    return f"{top['unit']} (top failing systemd unit, {top['failure_signals']} failure signals)"


def one(finding: str) -> dict:
    prompt = (
        f"A diagnostic request for server test9ng.\n\n"
        f"DETERMINISTIC EVIDENCE (from an automated systemd failure-signal scan of the full "
        f"journal): the top failing unit is {finding}. This evidence is reliable and already "
        f"gathered — no further searching is needed.\n\n" + TASK["objective"]
    )
    caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX)
    # 도구 없음(context_router=False) + finding clean 주입 = '결정론 추출 → e4b 언어화' 척추
    tt, logs, ans = run_abc_chain(
        task_id=TASK["id"], objective=TASK["objective"], prompt=prompt,
        constraints=TASK["constraints"], max_cycles=MAX_CYCLES, model_caller=caller,
        context_router=False, error_blocks=False, context_handles=None,
        mandatory_tool_prompt=False,
    )
    return {
        "finalized": ans is not None,
        "correct": (CORRECT_KW in str(ans).lower()) if ans else False,
        "n_assertions": len(tt.active_assertions),
        "n_cycles": len(logs),
        "ans": (ans if not isinstance(ans, str) else ans[:160]),
    }


def main():
    print("=" * 80, flush=True)
    print(f"det-planner probe — 결정론 finding → full ABC 수렴 | task A, n={N}, 도구 없음", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    finding = _det_finding()
    if not finding:
        print("  [ABORT] list_failed_units 가 finding 못 뽑음"); sys.exit(1)
    print(f"  [결정론 finding] {finding}", flush=True)

    out = {"experiment": "det_planner_probe", "model": MODEL, "task": TASK_ID,
           "n": N, "finding": finding, "samples": []}
    t0 = time.time()
    samples = []
    for i in range(1, N + 1):
        r = one(finding)
        samples.append(r)
        n = len(samples)
        fin = sum(1 for x in samples if x["finalized"])
        corr = sum(1 for x in samples if x["correct"])
        out["samples"] = samples
        out["agg"] = {
            "n": n,
            "finalized_rate": round(fin / n, 3),
            "correct_rate": round(corr / n, 3),
            "correct_wilson95": _wilson(corr, n),
        }
        out["elapsed_sec"] = round(time.time() - t0, 1)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [{i}/{N}] finalized={r['finalized']} correct={r['correct']} "
              f"asrt={r['n_assertions']} cyc={r['n_cycles']}", flush=True)

    a = out["agg"]
    print("\n" + "=" * 80, flush=True)
    print("det-planner probe 결과:", flush=True)
    print(f"  finalized={a['finalized_rate']:.0%} correct={a['correct_rate']:.0%} "
          f"(n={a['n']}, correct Wilson95={a['correct_wilson95']})", flush=True)
    print(f"  판정: correct ~90%+ → 척추 작동(로그분석가 아키텍처) / ~50% → B/C ceiling", flush=True)
    print(f"  대조: Exp24 control 47% / Exp23 fu_mandatory 53%(도구 reasoning 내)", flush=True)
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
