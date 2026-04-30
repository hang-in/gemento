"""taskset expected_answer 전수 검증.

12개 기본 태스크 + 10개 longctx 태스크:
- Math: sympy/scipy 수학 검증 (미설치 시 arithmetic fallback)
- Logic/Synthesis/Longctx: keyword 일관성 검증

사용:
    python -m experiments.validate_taskset
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
TASKSET_JSON = _ROOT / "experiments/tasks/taskset.json"
LONGCTX_JSON = _ROOT / "experiments/tasks/longctx_taskset.json"
RESULTS_DIR = Path(__file__).resolve().parent / "validate_taskset_results"


# ── 공통 검증 헬퍼 ──

def _keywords_in_expected(task: dict) -> dict:
    """scoring_keywords의 모든 토큰이 expected_answer에 포함되는지 확인."""
    expected = (task.get("expected_answer") or "").lower()
    keywords = task.get("scoring_keywords") or []
    issues = []
    for group in keywords:
        for token in group:
            if token.lower() not in expected:
                issues.append(f"token '{token}' not found in expected_answer")
    if issues:
        return {"result": "INCONSISTENT", "detail": "; ".join(issues)}
    return {"result": "CONSISTENT", "detail": "all keyword tokens found in expected_answer"}


def _no_negative_self_match(task: dict) -> dict:
    """negative_patterns가 expected_answer 자체에 매칭되지 않는지 확인."""
    expected = task.get("expected_answer") or ""
    for pat in (task.get("negative_patterns") or []):
        if re.search(pat, expected, re.IGNORECASE):
            return {"result": "INCONSISTENT",
                    "detail": f"negative_pattern '{pat}' matches expected_answer (self-contradiction)"}
    return {"result": "CONSISTENT", "detail": "no negative_patterns match expected_answer"}


def _conclusion_matches_expected(task: dict) -> dict:
    """conclusion_required가 expected_answer 끝 200자에 매칭되는지 확인."""
    patterns = task.get("conclusion_required") or []
    if not patterns:
        return {"result": "SKIP", "detail": "no conclusion_required field"}
    expected = task.get("expected_answer") or ""
    tail = expected[-200:] if len(expected) > 200 else expected
    for pat in patterns:
        if re.search(pat, tail, re.IGNORECASE):
            return {"result": "CONSISTENT", "detail": f"conclusion_required matched: '{pat}'"}
    return {"result": "INCONSISTENT",
            "detail": "conclusion_required patterns do not match expected_answer tail"}


# ── Math 검증 함수 ──

def _validate_math_01() -> dict:
    """x + y = 20, 2x + 3y = 47  →  x=13, y=7."""
    try:
        from sympy import symbols, Eq, solve
        x, y = symbols("x y", positive=True)
        sol = solve([Eq(x + y, 20), Eq(2 * x + 3 * y, 47)], [x, y])
        if int(sol[x]) == 13 and int(sol[y]) == 7:
            return {"result": "PASS", "detail": f"sympy: apples={int(sol[x])}, oranges={int(sol[y])}"}
        return {"result": "FAIL", "detail": f"sympy got {sol}, expected x=13,y=7"}
    except ImportError:
        a, o = 13, 7
        ok = (a + o == 20) and (2 * a + 3 * o == 47) and (a > o)
        return {"result": "PASS" if ok else "FAIL",
                "detail": f"arithmetic fallback: a={a},o={o}, checks={ok}"}


def _validate_math_02() -> dict:
    """2(l+w)=56, l²+w²=400  →  area=lw=192."""
    # (l+w)²=784, l²+w²=400 → 2lw=384 → lw=192
    area = (28 ** 2 - 400) // 2
    if area == 192:
        return {"result": "PASS", "detail": f"arithmetic: area={area} sq meters (l+w=28, l²+w²=400)"}
    return {"result": "FAIL", "detail": f"computed area={area}, expected 192"}


def _validate_math_03() -> dict:
    """r+s+rect=15, 4r+6s+8rect=88, rect=r-1, r=s+2  →  r=6,s=4,rect=5.

    Phase 1 후속 (rev.1, 2026-04-30): seats 96→88 + r=s+2 constraint 추가로
    선형 종속 해소, unique solution.
    """
    try:
        from sympy import symbols, Eq, solve
        r, s, rec = symbols("r s rec", positive=True)
        sol = solve([
            Eq(r + s + rec, 15),
            Eq(4 * r + 6 * s + 8 * rec, 88),
            Eq(rec, r - 1),
            Eq(r, s + 2),
        ], [r, s, rec])
        if int(sol[r]) == 6 and int(sol[s]) == 4 and int(sol[rec]) == 5:
            return {"result": "PASS",
                    "detail": f"sympy: round={int(sol[r])},square={int(sol[s])},rect={int(sol[rec])}"}
        return {"result": "FAIL", "detail": f"sympy got {sol}, expected r=6,s=4,rec=5"}
    except ImportError:
        r, s, rec = 6, 4, 5
        ok = (r + s + rec == 15) and (4*r + 6*s + 8*rec == 88) and (rec == r - 1) and (r == s + 2)
        return {"result": "PASS" if ok else "FAIL",
                "detail": f"arithmetic fallback: r={r},s={s},rec={rec}, checks={ok}"}


def _validate_math_04() -> dict:
    """LP: max 50X+40Y+30Z, s.t. 2X+3Y+4Z≤240, 3X+2Y+Z≤150, X/Y/Z≥10  →  X=31,Y=10,Z=37,profit=3060."""
    try:
        from scipy.optimize import linprog
        res = linprog(
            [-50, -40, -30],
            A_ub=[[2, 3, 4], [3, 2, 1]],
            b_ub=[240, 150],
            bounds=[(10, None), (10, None), (10, None)],
            method="highs",
        )
        if res.success:
            x, y, z = [round(v) for v in res.x]
            profit = round(-res.fun)
            if x == 31 and y == 10 and z == 37 and profit == 3060:
                return {"result": "PASS",
                        "detail": f"scipy: X={x},Y={y},Z={z},profit=${profit}"}
            return {"result": "FAIL",
                    "detail": f"scipy: X={x},Y={y},Z={z},profit=${profit}, expected X=31,Y=10,Z=37,3060"}
        return {"result": "FAIL", "detail": f"scipy failed: {res.message}"}
    except ImportError:
        x, y, z = 31, 10, 37
        labor = 2*x + 3*y + 4*z
        material = 3*x + 2*y + z
        profit = 50*x + 40*y + 30*z
        ok = x >= 10 and y >= 10 and z >= 10 and labor <= 240 and material <= 150 and profit == 3060
        return {"result": "PASS" if ok else "FAIL",
                "detail": f"arithmetic fallback: labor={labor}≤240, material={material}≤150, profit={profit}"}


MATH_VALIDATORS = {
    "math-01": _validate_math_01,
    "math-02": _validate_math_02,
    "math-03": _validate_math_03,
    "math-04": _validate_math_04,
}


# ── 태스크별 검증 ──

def _validate_task(task: dict) -> dict:
    tid = task["id"]

    if tid in MATH_VALIDATORS:
        r = MATH_VALIDATORS[tid]()
        kw = _keywords_in_expected(task)
        r["keyword_consistency"] = kw["result"]
        if kw["result"] == "INCONSISTENT" and r["result"] == "PASS":
            r["result"] = "WARN"
            r["detail"] += f" | keyword issue: {kw['detail']}"
        return r

    issues = []
    for check_fn in [_keywords_in_expected, _no_negative_self_match, _conclusion_matches_expected]:
        res = check_fn(task)
        if res["result"] == "INCONSISTENT":
            issues.append(res["detail"])

    if issues:
        return {"result": "FAIL", "detail": "; ".join(issues)}
    return {"result": "PASS", "detail": f"consistency OK. {_conclusion_matches_expected(task)['detail']}"}


def _validate_longctx_task(task: dict) -> dict:
    kw = _keywords_in_expected(task)
    result = "PASS" if kw["result"] == "CONSISTENT" else "FAIL"
    detail = kw["detail"]

    # gold_evidence_text에 expected 핵심 토큰 존재 여부 (WARN)
    gold_text = (task.get("gold_evidence_text") or "").lower()
    expected = (task.get("expected_answer") or "").lower()
    if gold_text and expected:
        stop = {"the", "a", "an", "is", "of", "in", "on", "at", "and", "or", "to"}
        exp_tokens = set(re.findall(r"\b\w+\b", expected)) - stop
        gold_tokens = set(re.findall(r"\b\w+\b", gold_text))
        missing = exp_tokens - gold_tokens
        if missing:
            detail += f" | WARN: expected tokens not in gold_evidence: {missing}"

    return {"result": result, "detail": detail}


def main() -> None:
    tasks = json.loads(TASKSET_JSON.read_text())["tasks"]
    longctx_tasks = json.loads(LONGCTX_JSON.read_text())["tasks"]

    all_results: list[dict] = []

    print("\n" + "═" * 88)
    print("  Taskset Validation Report")
    print("═" * 88)
    print(f"  {'task_id':<32} {'category':<22} {'method':<18} result")
    print("  " + "-" * 84)

    def _print_row(tid, cat, method, r, detail):
        flag = " ◄" if r in ("FAIL", "INCONSISTENT", "WARN") else ""
        print(f"  {tid:<32} {cat:<22} {method:<18} {r}{flag}")
        if r not in ("PASS", "SKIP", "CONSISTENT") or "WARN" in detail:
            print(f"  {'':32} → {detail}")

    for task in tasks:
        tid = task["id"]
        cat = task.get("category", "")
        method = "sympy/scipy" if tid in MATH_VALIDATORS else "consistency"
        r = _validate_task(task)
        _print_row(tid, cat, method, r["result"], r.get("detail", ""))
        all_results.append({"task_id": tid, "category": cat, "source": "taskset.json", **r})

    print("  " + "-" * 84)

    for task in longctx_tasks:
        tid = task["id"]
        r = _validate_longctx_task(task)
        _print_row(tid, "longctx", "consistency", r["result"], r.get("detail", ""))
        all_results.append({"task_id": tid, "category": "longctx", "source": "longctx_taskset.json", **r})

    total = len(all_results)
    passed = sum(1 for r in all_results if r["result"] in ("PASS", "CONSISTENT"))
    failed = sum(1 for r in all_results if r["result"] in ("FAIL", "INCONSISTENT"))
    warned = sum(1 for r in all_results if r["result"] == "WARN")
    skipped = sum(1 for r in all_results if r["result"] == "SKIP")

    print("\n" + "═" * 88)
    print(f"  Summary: {passed} PASS / {failed} FAIL / {warned} WARN / {skipped} SKIP  (total: {total})")
    print("═" * 88)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"validation_{ts}.json"
    out_path.write_text(
        json.dumps({
            "generated_at": ts,
            "results": all_results,
            "summary": {"total": total, "pass": passed, "fail": failed, "warn": warned, "skip": skipped},
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n  → JSON saved: {out_path}")
    print("\nVALIDATION COMPLETE")


if __name__ == "__main__":
    main()
