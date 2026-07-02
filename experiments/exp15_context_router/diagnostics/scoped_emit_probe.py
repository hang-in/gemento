"""a2a 싼 falsification — scoped-emit 신뢰성 probe (공유 코드 무변경).

질문(§21 후속): per-attempt 실패의 핵심은 A 가 답을 알아도 assertion 0개 emit
(Exp23 fu_mandatory 샘플 used_fu=True asrt=0). a2a(planner-executor)의 베팅 =
"좁게 스코프된 executor 호출이 broad A stage 보다 emit 이 안정적이다".

probe: A-stage(run_loop) 를 **답을 objective 에 handed 한 trivial 태스크**로 1회 호출.
tool/megalog 없음 — 순수 structured-output emit 신뢰성만 격리. 짧은 단일 호출이라
GPU 간헐 부하 kill 도 회피.

판정:
  emit 성공 ~90%+  → 모델은 좁으면 안정 emit → 실패는 broad-context overload → a2a 가치 O
  emit 성공 ~50%   → handed 답조차 emit 불안정 = structural → a2a 무효, retry 수용

control 대조(broad A stage 의 finalization ~49%)는 Exp23/§20. 여기선 scoped emit rate.

실행 (boxie 터널만 필요, Redis/megalog 불필요):
  python -u experiments/exp15_context_router/diagnostics/scoped_emit_probe.py
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
from schema import create_initial_tattoo
from orchestrator import run_loop
from native_ollama_caller import make_ollama_native_caller

BASE_URL, MODEL, NUM_CTX = drv.BASE_URL, drv.MODEL, drv.NUM_CTX
N = 20
CORRECT_KW = "gohttpserver"
OUT = _DIR / "scoped_emit_probe_result.json"

# 답을 objective 에 handed — 검색/분해 복잡도 제거, 순수 emit 만 요구.
SCOPED_OBJECTIVE = (
    "FACT (already established): the systemd unit that is crash-looping on server test9ng "
    "is `gohttpserver.service`. Your ONLY task this cycle is to record this established fact "
    "as a new_assertion (content: which unit is crash-looping and that it is failing), with "
    "confidence >= 0.8. Do NOT call any tools; the fact is already known. Emit at least one "
    "new_assertion."
)


def _wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (round(c - h, 3), round(c + h, 3))


def one():
    tt = create_initial_tattoo(task_id="scoped_emit_probe", objective=SCOPED_OBJECTIVE,
                               constraints=[], termination="")
    caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX)
    new_tt, log, ans, _ = run_loop(tt, 1, model_caller=caller)   # tools 없음 = 순수 emit
    parsed = log.parsed_response
    new_asns = (parsed or {}).get("new_assertions", []) if parsed else []
    contents = " ".join(str(a.get("content", "")) for a in new_asns).lower()
    # tattoo 에 실제 적용된 assertion 도 확인 (apply_llm_response 경유)
    applied = " ".join(str(getattr(a, "content", "")) for a in new_tt.active_assertions).lower()
    return {
        "parseable": parsed is not None,
        "emitted": len(new_asns) > 0,
        "emitted_correct": CORRECT_KW in contents,
        "applied_nonempty": len(new_tt.active_assertions) > 0,
        "applied_correct": CORRECT_KW in applied,
        "n_new_assertions": len(new_asns),
        "error": log.error,
    }


def main():
    print("=" * 80, flush=True)
    print(f"scoped-emit probe — handed 답으로 A-stage emit 신뢰성 | n={N}, tool 없음", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)

    out = {"experiment": "scoped_emit_probe", "model": MODEL, "n": N, "samples": []}
    t0 = time.time()
    samples = []
    for i in range(1, N + 1):
        r = one()
        samples.append(r)
        n = len(samples)
        emit = sum(1 for x in samples if x["emitted"])
        emit_c = sum(1 for x in samples if x["emitted_correct"])
        appl = sum(1 for x in samples if x["applied_nonempty"])
        parse = sum(1 for x in samples if x["parseable"])
        out["samples"] = samples
        out["agg"] = {
            "n": n,
            "parseable_rate": round(parse / n, 3),
            "emit_rate": round(emit / n, 3),
            "emit_wilson95": _wilson_ci(emit, n),
            "emit_correct_rate": round(emit_c / n, 3),
            "applied_nonempty_rate": round(appl / n, 3),
        }
        out["elapsed_sec"] = round(time.time() - t0, 1)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [{i}/{N}] emitted={r['emitted']} correct={r['emitted_correct']} "
              f"applied={r['applied_nonempty']} n_asn={r['n_new_assertions']} "
              f"parse={r['parseable']} err={r['error']}", flush=True)

    a = out["agg"]
    print("\n" + "=" * 80, flush=True)
    print("scoped-emit probe 결과:", flush=True)
    print(f"  emit_rate = {a['emit_rate']:.0%} (n={a['n']}, Wilson95={a['emit_wilson95']})", flush=True)
    print(f"  emit_correct = {a['emit_correct_rate']:.0%} | applied_nonempty = {a['applied_nonempty_rate']:.0%} "
          f"| parseable = {a['parseable_rate']:.0%}", flush=True)
    print(f"  판정: emit ~90%+ → a2a executor 가치 / ~50% → structural, a2a 무효(retry 수용)", flush=True)
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
