"""v2 역행 진단 — Exp04/05a trial별 v1/v2/v3 재채점 및 역행 패턴 분류.

사용:
    python -m experiments.scoring_diagnostic
"""

from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from measure import score_answer_v2, score_answer_v3

_ROOT = Path(__file__).resolve().parent.parent

EXP04_JSON = _ROOT / "experiments/exp04_abc_pipeline/results/exp04_abc_pipeline_20260409_182751.json"
EXP05A_JSON = _ROOT / "experiments/exp05a_prompt_enhance/results/exp05a_prompt_enhance_20260410_145033.json"
TASKS_JSON = _ROOT / "experiments/tasks/taskset.json"
RESULTS_DIR = Path(__file__).resolve().parent / "scoring_diagnostic_results"

EXP_TASK_IDS = {
    "math-01", "math-02", "math-03",
    "logic-01", "logic-02", "logic-03",
    "synthesis-01", "synthesis-02", "synthesis-03",
}


def _score_answer_with_path(response: str, expected: str) -> tuple[float, str]:
    """v1 채점 + 분기 경로 반환. measure.py:score_answer와 동일 로직."""
    if not response or not expected:
        return 0.0, "zero"
    resp_lower = response.lower().strip()
    exp_lower = expected.lower().strip()

    if exp_lower in resp_lower:
        return 1.0, "substring"

    expected_tokens = set(re.findall(r"\b\w+\b", exp_lower))
    response_tokens = set(re.findall(r"\b\w+\b", resp_lower))
    if expected_tokens and expected_tokens.issubset(response_tokens):
        return 0.8, "token_subset"

    overlap = expected_tokens & response_tokens
    if expected_tokens:
        return len(overlap) / len(expected_tokens) * 0.6, "partial_overlap"

    return 0.0, "zero"


def _classify_regression(v1_score: float, v2_score: float, v1_path: str) -> str:
    """v2 역행 패턴 분류."""
    if v1_score <= v2_score + 1e-9:
        return "NONE"
    if v1_path == "substring":
        return "TYPE_A"  # substring match이지만 keyword group 일부 실패
    if v1_path == "token_subset":
        return "TYPE_B"  # token subset이지만 keyword group 미매칭
    if v1_path == "partial_overlap":
        return "TYPE_C"  # partial overlap이지만 keyword groups 모두 실패
    return "TYPE_D"


def _keyword_group_detail(response: str, keywords: list) -> list[dict]:
    """각 keyword group의 매칭 여부 반환."""
    resp_lower = (response or "").lower()
    detail = []
    for group in keywords:
        matched_tokens = [t for t in group if t.lower() in resp_lower]
        detail.append({
            "group": group,
            "matched": len(matched_tokens) == len(group),
            "missing_tokens": [t for t in group if t.lower() not in resp_lower],
        })
    return detail


def _load_experiment(json_path: Path) -> list[dict]:
    return json.loads(json_path.read_text(encoding="utf-8")).get("results", [])


def main() -> None:
    task_map = {t["id"]: t for t in json.loads(TASKS_JSON.read_text())["tasks"]}

    experiments = [
        ("Exp04", EXP04_JSON),
        ("Exp05a", EXP05A_JSON),
    ]

    all_trials: list[dict] = []

    print("\n" + "═" * 104)
    print("  v2 역행 진단 — Exp04 + Exp05a trial별 재채점")
    print("═" * 104)

    for exp_name, json_path in experiments:
        records = _load_experiment(json_path)
        print(f"\n[{exp_name}]")
        print(f"  {'task':<15} {'trial':>5} {'v1':>6} {'path':<15} {'v2':>6} {'v3':>6} {'Δv1-v2':>8}  {'type':<8}  note")
        print("  " + "-" * 100)

        for record in records:
            tid = record["task_id"]
            if tid not in EXP_TASK_IDS:
                continue
            te = task_map.get(tid, record)
            expected = record.get("expected_answer", te.get("expected_answer", ""))

            for t in record.get("trials", []):
                ans = str(t.get("final_answer") or "")
                v1, v1_path = _score_answer_with_path(ans, expected)
                v2 = score_answer_v2(ans, te)
                v3 = score_answer_v3(ans, te)
                delta = v1 - v2
                rtype = _classify_regression(v1, v2, v1_path)

                note = ""
                if rtype != "NONE":
                    kw_detail = _keyword_group_detail(ans, te.get("scoring_keywords", []))
                    failed = [d["group"] for d in kw_detail if not d["matched"]]
                    note = f"failed_groups={failed}"

                flag = " ◄" if rtype != "NONE" else ""
                print(
                    f"  {tid:<15} {str(t.get('trial','?')):>5} {v1:>6.3f} {v1_path:<15}"
                    f" {v2:>6.3f} {v3:>6.3f} {delta:>+8.3f}  {rtype:<8}{flag}  {note}"
                )

                all_trials.append({
                    "experiment": exp_name,
                    "task_id": tid,
                    "trial": t.get("trial"),
                    "v1": v1,
                    "v1_path": v1_path,
                    "v2": v2,
                    "v3": v3,
                    "delta_v1_v2": delta,
                    "regression_type": rtype,
                    "final_answer_head": ans[:120],
                    "expected_answer": expected,
                })

    # ── 요약 ──
    regressed = [t for t in all_trials if t["regression_type"] != "NONE"]

    print("\n" + "═" * 104)
    print("  요약")
    print("═" * 104)
    print(f"  전체 trial  : {len(all_trials)}")
    print(f"  역행 trial  : {len(regressed)}  (v1 > v2)")

    type_counts = Counter(t["regression_type"] for t in regressed)
    for rtype, cnt in sorted(type_counts.items()):
        print(f"    {rtype}: {cnt}건")

    if regressed:
        print("\n  역행 task 분포:")
        for tid, cnt in Counter(t["task_id"] for t in regressed).most_common():
            print(f"    {tid}: {cnt}건")

        print("\n  v1 분기 경로별 역행:")
        for path, cnt in Counter(t["v1_path"] for t in regressed).most_common():
            print(f"    {path}: {cnt}건")

        max_delta = max(t["delta_v1_v2"] for t in regressed)
        mean_delta = sum(t["delta_v1_v2"] for t in regressed) / len(regressed)
        print(f"\n  최대 역행 폭: {max_delta:.3f}")
        print(f"  평균 역행 폭: {mean_delta:.3f}")

        all_type_a = all(t["regression_type"] == "TYPE_A" for t in regressed)
        print("\n  채점 정책 권고:")
        if all_type_a:
            print("  → TYPE_A 지배: expected_answer substring은 포함되지만 keyword group 요건이 더 엄격.")
            print("    v2 keyword 재설계 또는 그룹 축소 고려. v3 전면 전환은 역행 악화 없음.")
        else:
            print("  → 혼합 패턴: 각 역행 trial의 keyword group 실패 내역 확인 후 결정 필요.")
    else:
        print("\n  → 역행 없음: v2 채점이 v1 대비 일관되게 작동 중.")

    # ── 실험별 전체 평균 ──
    print("\n" + "═" * 104)
    print("  실험별 전체 평균")
    print("═" * 104)
    for exp_name in ["Exp04", "Exp05a"]:
        exp_t = [t for t in all_trials if t["experiment"] == exp_name]
        if exp_t:
            mv1 = sum(t["v1"] for t in exp_t) / len(exp_t)
            mv2 = sum(t["v2"] for t in exp_t) / len(exp_t)
            mv3 = sum(t["v3"] for t in exp_t) / len(exp_t)
            print(f"  {exp_name}: v1={mv1:.3f}  v2={mv2:.3f}  v3={mv3:.3f}  Δ(v1-v2)={mv1-mv2:+.3f}")

    # ── JSON 저장 ──
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"v2_regression_{ts}.json"
    out_path.write_text(
        json.dumps({
            "generated_at": ts,
            "exp04_json": str(EXP04_JSON),
            "exp05a_json": str(EXP05A_JSON),
            "trials": all_trials,
            "summary": {
                "total": len(all_trials),
                "regressed": len(regressed),
                "type_counts": dict(type_counts),
            },
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n  → JSON saved: {out_path}")
    print("\nDIAGNOSTIC COMPLETE")


if __name__ == "__main__":
    main()
