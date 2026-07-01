"""Exp23 — FAILED_UNITS 도구 A/B: control vs fu_offered vs fu_mandatory.

Task 01(완료)에서 추가된 `list_failed_units`(FAILED_UNITS_TOOL_SCHEMAS/FUNCTIONS)가
per-attempt retrieval_gap(모델이 넓은 grep 후 포기)을 줄이는지 검증. 3 arm 의 차이는
오직 (a) caller 에 넘기는 extra_tool_schemas/fns 주입 여부, (b) fu_mandatory 만
"list_failed_units 를 먼저 호출하라" constraint 를 추가 주입.

run_v21_facet_ab.py 인프라(BASE_URL/MODEL/NUM_CTX/REDIS_KEY/TASKS/_healthcheck/
_load_megalog_to_redis) 를 그대로 재사용(모듈 import, 무변경). retrieval_gap 측정이
목적이므로 **single-attempt**(retry 없음), task = exp21a_crashloop 만, n=15/arm.

arm:
  - control:      schemas=None,                     fns=None                        (도구 미제공)
  - fu_offered:    FAILED_UNITS_TOOL_SCHEMAS/FUNCTIONS 제공, constraint 힌트 없음
  - fu_mandatory: 위 도구 제공 + FU_MANDATORY_HINT(먼저 list_failed_units 호출 지시)

측정(trial 별): finalized(ans is not None), correct("gohttpserver" in ans.lower()),
n_assertions, used_fu(해당 체인에서 list_failed_units 실제 호출 여부 — 도구 함수를
카운팅 래퍼로 감싸서 계측; control 은 도구 자체가 없으므로 항상 False).

사용자/에이전트 실행 (boxie e4b 터널(11435) + Redis 메가로그 키 필요):
  python -u experiments/exp15_context_router/run_v23_failed_units_ab.py
  환경변수 EXP20_LOG_PATH 로 메가로그 파일 경로 오버라이드 가능(run_v21_facet_ab.py 참조).
  진척: diagnostics/v23_failed_units_result.json 의 arms.*.{finalized_rate,correct_rate,
  used_fu_rate} 확인. trial 마다 증분 write(중단 내성).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # experiments/ (tools 패키지용)

from tools import FAILED_UNITS_TOOL_SCHEMAS, FAILED_UNITS_TOOL_FUNCTIONS
from orchestrator import run_abc_chain
from native_ollama_caller import make_ollama_native_caller

import run_v21_facet_ab as drv  # BASE_URL/MODEL/NUM_CTX/REDIS_KEY/TASKS/_healthcheck/_load_megalog_to_redis 재사용

BASE_URL, MODEL, NUM_CTX, REDIS_KEY = drv.BASE_URL, drv.MODEL, drv.NUM_CTX, drv.REDIS_KEY
MAX_CYCLES = 8
N_TRIALS = 15
TASK_ID = "exp21a_crashloop"
CORRECT_KW = "gohttpserver"

TASK = next(t for t in drv.TASKS if t["id"] == TASK_ID)

_DIR = Path(__file__).resolve().parent
OUT_PATH = _DIR / "diagnostics" / "v23_failed_units_result.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

FU_MANDATORY_HINT = (
    "For a service crash/failure diagnosis, FIRST call `list_failed_units` on the handle "
    "to get the failing systemd units directly — do NOT start by grepping for 'error'. "
    "Then confirm the top unit with grep_context and record it as a new_assertion."
)

# ── arm 정의 (FAILED_UNITS 도구 주입 여부 + fu_mandatory 만 constraint 힌트) ──────
ARMS = [
    {"id": "control",      "schemas": None,                      "fns": None,                        "hint": None},
    {"id": "fu_offered",   "schemas": FAILED_UNITS_TOOL_SCHEMAS,  "fns": FAILED_UNITS_TOOL_FUNCTIONS,  "hint": None},
    {"id": "fu_mandatory", "schemas": FAILED_UNITS_TOOL_SCHEMAS,  "fns": FAILED_UNITS_TOOL_FUNCTIONS,  "hint": FU_MANDATORY_HINT},
]


def _make_fu_extra_fns(arm: dict, used_flag: list):
    """arm['fns'] 의 list_failed_units 를 카운팅 래퍼로 교체(있으면).

    used_flag[0] 은 이 체인(단일 trial) 동안 list_failed_units 가 한 번이라도
    호출되면 True 로 세팅된다. control 은 fns 가 None 이므로 항상 그대로 None 반환
    → used_fu 는 항상 False.
    """
    fns = arm["fns"]
    if fns is None:
        return None
    orig = fns.get("list_failed_units")
    if orig is None:
        return dict(fns)

    def _counting_wrapper(*a, _orig=orig, **kw):
        used_flag[0] = True
        return _orig(*a, **kw)

    return {**fns, "list_failed_units": _counting_wrapper}


def _run_one(arm: dict) -> dict:
    """task 를 주어진 arm 으로 single-attempt 실행. trial 별 metric dict 반환."""
    prompt = (
        f"A diagnostic request for server test9ng. The full systemd journal (30-day window, "
        f"very large) is cached in Redis.\nContext Handle: {REDIS_KEY}\n\n"
        + TASK["objective"]
    )
    constraints = list(TASK["constraints"])
    if arm["hint"]:
        constraints = constraints + [arm["hint"]]

    used_flag = [False]
    extra_fns = _make_fu_extra_fns(arm, used_flag)

    caller = make_ollama_native_caller(
        BASE_URL, MODEL, num_ctx=NUM_CTX,
        extra_tool_schemas=arm["schemas"],
        extra_tool_fns=extra_fns,
    )
    tt, logs, ans = run_abc_chain(
        task_id=TASK["id"], objective=TASK["objective"], prompt=prompt,
        constraints=constraints, max_cycles=MAX_CYCLES, model_caller=caller,
        context_router=True, error_blocks=False, context_handles=[REDIS_KEY],
        mandatory_tool_prompt=True,
    )

    finalized = ans is not None
    correct = (CORRECT_KW in str(ans).lower()) if ans else False
    return {
        "finalized": finalized,
        "correct": correct,
        "n_assertions": len(tt.active_assertions),
        "used_fu": used_flag[0],
        "n_cycles": len(logs),
        "ans": (ans if not isinstance(ans, str) else ans[:200]),
    }


def main():
    print("=" * 80, flush=True)
    print(
        f"Exp23 FAILED_UNITS A/B — test9ng crashloop task → boxie {MODEL} | "
        f"n={N_TRIALS}/arm, max_cycles={MAX_CYCLES}, single-attempt",
        flush=True,
    )
    print("  arms: control vs fu_offered vs fu_mandatory | 지표: finalized/correct/used_fu rate", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    out = {
        "experiment": "exp23_failed_units_ab",
        "model": MODEL,
        "task": TASK_ID,
        "n_trials": N_TRIALS,
        "max_cycles": MAX_CYCLES,
        "arms": {},
    }
    t0 = time.time()
    for arm in ARMS:
        aid = arm["id"]
        print(f"\n  ── Arm={aid} ──", flush=True)
        samples = []
        for i in range(1, N_TRIALS + 1):
            r = _run_one(arm)
            samples.append(r)

            n = len(samples)
            fin = sum(1 for x in samples if x["finalized"])
            corr = sum(1 for x in samples if x["correct"])
            used = sum(1 for x in samples if x["used_fu"])
            out["arms"][aid] = {
                "n": n,
                "finalized_rate": round(fin / n, 3),
                "correct_rate": round(corr / n, 3),
                "used_fu_rate": round(used / n, 3),
                "samples": samples,
            }
            out["elapsed_sec"] = round(time.time() - t0, 1)
            with open(OUT_PATH, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)

            print(
                f"  [{aid} {i}/{N_TRIALS}] finalized={r['finalized']} correct={r['correct']} "
                f"used_fu={r['used_fu']} asrt={r['n_assertions']} cyc={r['n_cycles']} "
                f"| ans={str(r['ans'])[:100]}",
                flush=True,
            )

    print("\n" + "=" * 80, flush=True)
    print("Exp23 FAILED_UNITS A/B 결과:", flush=True)
    for aid, a in out["arms"].items():
        print(
            f"  [{aid}] finalized={a['finalized_rate']:.0%} correct={a['correct_rate']:.0%} "
            f"used_fu={a['used_fu_rate']:.0%} (n={a['n']})",
            flush=True,
        )
    print(f"  → {OUT_PATH}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
