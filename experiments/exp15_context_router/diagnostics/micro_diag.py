"""Phase 1 step 0 — A-stage empty-tattoo 원인 micro-diagnosis (공유 코드 무변경).

run_abc_chain 반환 logs 의 a_log(LoopLog: raw_response / parsed_response / error) +
tool_calls 만 검사해, empty-tattoo chain 에서 A 가:
  - grep 을 호출했나 (n_tool_calls)            → investigation 여부
  - raw 출력에 'gohttpserver' 가 있나           → 답을 찾았나(recall)
  - parsed_response 가 None 인가 / error 인가   → parse/schema 실패 여부
를 cycle 별로 캡처. task A, n=6, single-attempt.

분류:
  (A) grep X            → investigation 실패
  (B) grep O + raw有 + parsed None/err → parse/schema 실패 (찾았으나 구조화 실패)
  (C) grep O + raw有 + parsed OK + assertion 0 → content mismatch (parse 됐으나 assertion 미emit)
  (D) grep O + raw無    → recall 실패 (못 찾음)
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
OUT = Path(r"C:\Users\사자\AppData\Local\Temp\claude\D--privateProject-gemento\e0e17d5d-1940-4371-902a-107212495699\scratchpad\micro_diag_result.json")
TASK = next(t for t in drv.TASKS if t["id"] == "exp21a_crashloop")


def _synth(tt):
    return " \n ".join(str(getattr(a, "content", "")) for a in tt.active_assertions
                       if getattr(a, "content", None))


def one(i):
    prompt = (f"A diagnostic request for server test9ng. The full systemd journal (30-day window, "
              f"very large) is cached in Redis.\nContext Handle: {REDIS_KEY}\n\n" + TASK["objective"])
    caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX)
    tt, logs, ans = run_abc_chain(
        task_id=TASK["id"], objective=TASK["objective"], prompt=prompt,
        constraints=TASK["constraints"], max_cycles=MAX_CYCLES, model_caller=caller,
        context_router=True, error_blocks=False, context_handles=[REDIS_KEY],
        mandatory_tool_prompt=True,
    )
    cycles = []
    for l in logs:
        al = getattr(l, "a_log", None)
        raw = (getattr(al, "raw_response", "") or "") if al else ""
        parsed = getattr(al, "parsed_response", None) if al else None
        cycles.append({
            "cycle": getattr(l, "cycle", "?"),
            "phase": getattr(l, "phase", "?"),
            "n_tool_calls": len(getattr(l, "tool_calls", None) or []),
            "raw_has_gohttp": "gohttpserver" in raw.lower(),
            "raw_len": len(raw),
            "parsed_ok": parsed is not None,
            "parsed_keys": list(parsed.keys()) if isinstance(parsed, dict) else None,
            "a_error": getattr(al, "error", None) if al else None,
            "raw_snip": raw[:200].replace("\n", " "),
        })
    finalized = ans is not None
    n_asrt = len(tt.active_assertions)
    # chain 분류 (empty-tattoo 기준)
    any_tool = any(c["n_tool_calls"] > 0 for c in cycles)
    any_raw_goh = any(c["raw_has_gohttp"] for c in cycles)
    any_parse_fail = any((not c["parsed_ok"]) or c["a_error"] for c in cycles)
    if n_asrt > 0:
        cls = "OK(populated)"
    elif not any_tool:
        cls = "A:investigation-fail (no grep)"
    elif any_raw_goh and any_parse_fail:
        cls = "B:parse/schema-fail (found, parse failed)"
    elif any_raw_goh:
        cls = "C:content-mismatch (found+parsed, no assertion)"
    else:
        cls = "D:recall-fail (grep but not found in raw)"
    return {"i": i, "finalized": finalized, "n_assertions": n_asrt,
            "any_tool": any_tool, "any_raw_gohttp": any_raw_goh,
            "any_parse_fail": any_parse_fail, "classification": cls, "cycles": cycles,
            "final_ans": (ans if not isinstance(ans, str) else ans[:120])}


def main():
    print("=" * 80, flush=True)
    print(f"Micro-diag — A-stage empty-tattoo 원인 (task A, n={N}, single-attempt)", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    out = {"experiment": "micro_diag_a_stage", "model": MODEL, "task": TASK["id"], "n": N, "samples": []}
    t0 = time.time()
    for i in range(1, N + 1):
        r = one(i)
        out["samples"].append(r)
        out["elapsed_sec"] = round(time.time() - t0, 1)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  [{i}/{N}] {r['classification']} | finalized={r['finalized']} asrt={r['n_assertions']} "
              f"any_grep={r['any_tool']} raw_gohttp={r['any_raw_gohttp']} parse_fail={r['any_parse_fail']}", flush=True)
        for c in r["cycles"]:
            print(f"      cyc{c['cycle']}/{c['phase'][:4]} grep={c['n_tool_calls']} "
                  f"raw_goh={c['raw_has_gohttp']} parsed={c['parsed_ok']} keys={c['parsed_keys']} "
                  f"err={c['a_error']}", flush=True)

    print("\n" + "=" * 80, flush=True)
    print("분류 집계:", flush=True)
    from collections import Counter
    print("  ", dict(Counter(s["classification"] for s in out["samples"])), flush=True)
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
