"""Exp26 v1 — 추출기·실패모드 일반화 (게이트 ON, 기존 추출기 재사용, 공유코드 무변경).

로그분석가 아키텍처의 최상위 미검증 가정: fail-safe(wrong 0)+처리량이
(list_failed_units × crashloop) 하나를 넘어 **다른 추출기·다른 실패모드**로 일반화되나?

v1(값쌈, 새 도구 없음): 이미 검증된 결정론 추출기 2개 × Exp21 태스크 2개를 게이트 ON 교차.
  Cell 1 (control): list_failed_units → crashloop(task A, gohttpserver.service)  ← Exp25c 재현
  Cell 2 (신규)    : aggregate_context → brute-force(task B, 45.144.212.75)      ← 신규 추출기+모드

각 cell: 결정론 finding → clean 주입 → 게이트 ON full ABC(도구 없음) → finalized/correct/wrong.
핵심 질문: Cell 2 도 wrong 0(fail-safe) + 합리적 처리량 유지 → 일반화 증거(2추출기×2모드).
          Cell 2 wrong>0 → fail-safe 미일반화(중요한 반증).

실행 (boxie 터널 + Redis 메가로그):
  python -u experiments/exp15_context_router/diagnostics/exp26_extractor_generalize.py
"""
import json
import math
import re
import sys
import time
from pathlib import Path

_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_DIR.parent.parent))                 # experiments/
sys.path.insert(0, str(_DIR.parent))                        # exp15_context_router/

import run_v21_facet_ab as drv
from tools import list_failed_units, aggregate_context
from orchestrator import run_abc_chain
from native_ollama_caller import make_ollama_native_caller

N = 12                                                      # cell 당 (경합 고려)
MAX_CYCLES = 8
OUT = _DIR / "exp26_extractor_generalize_result.json"
PRODUCTIVE = {"SYNTHESIZE", "VERIFY"}

TASK_A = next(t for t in drv.TASKS if t["id"] == "exp21a_crashloop")
TASK_B = next(t for t in drv.TASKS if t["id"] == "exp21b_bruteforce")


def _wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (round(c - h, 3), round(c + h, 3))


def _finding_crashloop() -> str:
    """추출기 1: list_failed_units → top 실패 unit (결정론)."""
    out = list_failed_units(drv.REDIS_KEY, top_n=3)
    if out.get("error") or not out.get("top"):
        return ""
    t = out["top"][0]
    return f"{t['unit']} (top failing systemd unit, {t['failure_signals']} failure signals)"


def _finding_bruteforce() -> str:
    """추출기 2: aggregate_context → 최다 실패 로그인 source IP (결정론)."""
    out = aggregate_context(drv.REDIS_KEY, "Failed password",
                            group_by=r"from (\d+\.\d+\.\d+\.\d+)", top_n=3)
    if out.get("error") or not out.get("top"):
        return ""
    t = out["top"][0]
    return f"{t['value']} (source IP with the most failed SSH logins, {t['count']} attempts)"


CELLS = [
    {"id": "crashloop_list_failed_units", "task": TASK_A, "correct_kw": "gohttpserver",
     "extractor": "list_failed_units", "finding_fn": _finding_crashloop},
    {"id": "bruteforce_aggregate_context", "task": TASK_B, "correct_kw": "45.144.212.75",
     "extractor": "aggregate_context", "finding_fn": _finding_bruteforce},
]


def one(task, finding: str, correct_kw: str) -> dict:
    prompt = (
        f"This is a diagnostic request for server test9ng.\n\n"
        f"DETERMINISTIC EVIDENCE (from an automated exhaustive scan of the full journal): "
        f"{finding}. This evidence is reliable and already gathered — no further searching is "
        f"needed.\n\n" + task["objective"]
    )
    caller = make_ollama_native_caller(drv.BASE_URL, drv.MODEL, num_ctx=drv.NUM_CTX)
    tt, logs, ans = run_abc_chain(
        task_id=task["id"], objective=task["objective"], prompt=prompt,
        constraints=task["constraints"], max_cycles=MAX_CYCLES, model_caller=caller,
        context_router=False, error_blocks=False, context_handles=None,
        mandatory_tool_prompt=False,
        converged_requires_answer=True,                     # ★ 게이트 ON (Exp25c 기본)
    )
    finalized = ans is not None
    correct = (correct_kw.lower() in str(ans).lower()) if ans else False
    reached_productive = any(lg.phase in PRODUCTIVE for lg in logs)
    return {"finalized": finalized, "correct": correct,
            "wrong": bool(finalized and not correct),        # fail-safe → 0 기대
            "reached_productive": reached_productive, "n_cycles": len(logs),
            "ans": (str(ans)[:160] if ans else None)}


def _agg(samples):
    n = len(samples)
    if n == 0:
        return {}
    corr = sum(1 for s in samples if s["correct"])
    return {
        "n": n,
        "finalized_rate": round(sum(1 for s in samples if s["finalized"]) / n, 3),
        "correct_rate": round(corr / n, 3),
        "correct_wilson95": _wilson(corr, n),
        "wrong_rate": round(sum(1 for s in samples if s["wrong"]) / n, 3),
        "reached_productive_rate": round(sum(1 for s in samples if s["reached_productive"]) / n, 3),
    }


def main():
    print("=" * 80, flush=True)
    print(f"Exp26 v1 — 추출기·실패모드 일반화 | 게이트 ON, 2 cell × n={N}", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    out = {"experiment": "exp26_extractor_generalize", "model": drv.MODEL,
           "n_per_cell": N, "max_cycles": MAX_CYCLES, "gate": "converged_requires_answer=True",
           "cells": {}}
    t0 = time.time()
    for cell in CELLS:
        finding = cell["finding_fn"]()
        if not finding:
            print(f"  [ABORT] {cell['id']} finding 못 뽑음"); sys.exit(1)
        print(f"\n  [{cell['id']}] 추출기={cell['extractor']} finding={finding}", flush=True)
        samples = []
        for i in range(1, N + 1):
            r = one(cell["task"], finding, cell["correct_kw"])
            samples.append(r)
            out["cells"][cell["id"]] = {
                "extractor": cell["extractor"], "task": cell["task"]["id"],
                "correct_kw": cell["correct_kw"], "finding": finding,
                "samples": samples, "agg": _agg(samples),
            }
            out["elapsed_sec"] = round(time.time() - t0, 1)
            OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"    [{cell['id']} {i}/{N}] final={r['finalized']} corr={r['correct']} "
                  f"wrong={r['wrong']} prod={r['reached_productive']} cyc={r['n_cycles']}", flush=True)

    print("\n" + "=" * 80, flush=True)
    print("Exp26 v1 결과:", flush=True)
    for cid, c in out["cells"].items():
        a = c["agg"]
        print(f"  {cid}: finalized={a['finalized_rate']:.0%} correct={a['correct_rate']:.0%} "
              f"wrong={a['wrong_rate']:.0%} prod={a['reached_productive_rate']:.0%} "
              f"(correct Wilson95={a['correct_wilson95']})", flush=True)
    print(f"  판정: 양 cell wrong 0 & correct 합리적 → fail-safe·처리량 일반화(2추출기×2모드).", flush=True)
    print(f"        Cell 2 wrong>0 → fail-safe 미일반화(반증).", flush=True)
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
