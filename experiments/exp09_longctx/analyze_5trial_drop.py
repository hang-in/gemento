"""Exp09 5-trial 점수 하락 원인 분석.

3-trial 결과 (exp09_longctx_20260425_144412.json) vs 5-trial 결과
(exp09_longctx_5trial_20260430_111330.json) 의 trial 1-3 vs 4-5 답변 / 채점 분포 비교.

분석 차원:
  (a) 환경 차이  — 두 JSON 의 model / arms / chunk 등 메타 비교
  (b) 모델 비결정성 — 같은 task 의 trial 별 답변 unique 개수, early/late overlap
  (c) 시스템 결함 — error / null final_answer 분포
  (d) 채점 변동 — 동일 답변에 다른 score 발생 여부

사용:
    python -m experiments.exp09_longctx.analyze_5trial_drop --arm abc_tattoo
    python -m experiments.exp09_longctx.analyze_5trial_drop --arm rag_baseline
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from measure import score_answer_v2  # noqa: E402

_ROOT = Path(__file__).resolve().parent
_TASKS_DIR = Path(__file__).resolve().parent.parent / "tasks"

DEFAULT_3TRIAL = _ROOT / "results/exp09_longctx_20260425_144412.json"
DEFAULT_5TRIAL = _ROOT / "results/exp09_longctx_5trial_20260430_111330.json"


def _load(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_taskset() -> dict[str, dict]:
    return {t["id"]: t for t in json.load(open(_TASKS_DIR / "longctx_taskset.json"))["tasks"]}


def _meta_diff(d3: dict, d5: dict) -> list[str]:
    """top-level meta 비교 (model, arms 라벨, chunk, top_k 등)."""
    keys = ("model", "trials_per_task", "chunk_size", "chunk_overlap", "rag_top_k")
    diffs: list[str] = []
    for k in keys:
        v3, v5 = d3.get(k), d5.get(k)
        if v3 != v5 and not (k == "trials_per_task"):  # trials_per_task 차이는 정상
            diffs.append(f"{k}: 3-trial={v3!r}  5-trial={v5!r}")
    a3 = [a.get("label") for a in (d3.get("arms") or [])]
    a5 = [a.get("label") for a in (d5.get("arms") or [])]
    if a3 != a5:
        diffs.append(f"arms label: 3-trial={a3}  5-trial={a5}")
    return diffs


def _arm_entries(d: dict, arm: str) -> list[dict]:
    return (d.get("results_by_arm") or {}).get(arm, [])


def _score_trial(trial: dict, task_meta: dict) -> float:
    return score_answer_v2(str(trial.get("final_answer") or ""), task_meta)


def analyze(d3: dict, d5: dict, arm: str, task_map: dict[str, dict]) -> dict:
    entries_3 = {e["task_id"]: e for e in _arm_entries(d3, arm)}
    entries_5 = {e["task_id"]: e for e in _arm_entries(d5, arm)}

    early_acc: list[float] = []   # 5-trial 의 trial 0,1,2
    late_acc: list[float] = []    # 5-trial 의 trial 3,4
    three_acc: list[float] = []   # 3-trial JSON 의 모든 trial
    early_errors = 0
    late_errors = 0
    early_null_answers = 0
    late_null_answers = 0
    answer_diversity_early: list[int] = []
    answer_diversity_late: list[int] = []
    answer_overlap_count: list[int] = []
    early_vs_3trial_consistency: list[bool] = []  # trial 1-3 정합성

    per_task: list[dict] = []

    for tid, entry5 in entries_5.items():
        task_meta = task_map.get(tid, entry5)
        trials5 = entry5.get("trials") or []
        if len(trials5) < 5:
            continue
        early = trials5[:3]
        late = trials5[3:5]
        es = [_score_trial(t, task_meta) for t in early]
        ls = [_score_trial(t, task_meta) for t in late]
        early_acc.extend(es)
        late_acc.extend(ls)

        for t in early:
            if t.get("error"):
                early_errors += 1
            if not str(t.get("final_answer") or "").strip():
                early_null_answers += 1
        for t in late:
            if t.get("error"):
                late_errors += 1
            if not str(t.get("final_answer") or "").strip():
                late_null_answers += 1

        early_answers = [str(t.get("final_answer") or "").strip()[:120] for t in early]
        late_answers = [str(t.get("final_answer") or "").strip()[:120] for t in late]
        answer_diversity_early.append(len(set(early_answers)))
        answer_diversity_late.append(len(set(late_answers)))
        answer_overlap_count.append(len(set(early_answers) & set(late_answers)))

        # 3-trial JSON 의 trial 0-2 가 5-trial 의 trial 0-2 와 동일한지 (append 정합)
        entry3 = entries_3.get(tid)
        if entry3:
            t3 = entry3.get("trials") or []
            three_s = [_score_trial(t, task_meta) for t in t3]
            three_acc.extend(three_s)
            if len(t3) >= 3:
                consistent = (
                    [str(t.get("final_answer") or "").strip()[:120] for t in t3[:3]]
                    == early_answers
                )
                early_vs_3trial_consistency.append(consistent)

        per_task.append({
            "task_id": tid,
            "early_mean": statistics.mean(es) if es else 0.0,
            "late_mean": statistics.mean(ls) if ls else 0.0,
            "delta": (statistics.mean(ls) if ls else 0.0) - (statistics.mean(es) if es else 0.0),
            "early_answers_unique": len(set(early_answers)),
            "late_answers_unique": len(set(late_answers)),
            "overlap": len(set(early_answers) & set(late_answers)),
        })

    def _mean_std(xs: list[float]) -> tuple[float, float]:
        if not xs:
            return 0.0, 0.0
        m = statistics.mean(xs)
        s = statistics.stdev(xs) if len(xs) > 1 else 0.0
        return m, s

    em, esd = _mean_std(early_acc)
    lm, lsd = _mean_std(late_acc)
    tm, tsd = _mean_std(three_acc)

    return {
        "arm": arm,
        "n_tasks": len(per_task),
        "early_mean": em, "early_std": esd, "early_n": len(early_acc),
        "late_mean": lm, "late_std": lsd, "late_n": len(late_acc),
        "three_mean": tm, "three_std": tsd, "three_n": len(three_acc),
        "delta_late_minus_early": lm - em,
        "early_errors": early_errors, "late_errors": late_errors,
        "early_null_answers": early_null_answers, "late_null_answers": late_null_answers,
        "answer_diversity_early_mean": (
            statistics.mean(answer_diversity_early) if answer_diversity_early else 0.0
        ),
        "answer_diversity_late_mean": (
            statistics.mean(answer_diversity_late) if answer_diversity_late else 0.0
        ),
        "answer_overlap_mean": (
            statistics.mean(answer_overlap_count) if answer_overlap_count else 0.0
        ),
        "append_consistency_3vs5": (
            sum(1 for c in early_vs_3trial_consistency if c),
            len(early_vs_3trial_consistency),
        ),
        "per_task": per_task,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Exp09 5-trial 점수 하락 원인 분석")
    parser.add_argument("--3trial", dest="three", default=str(DEFAULT_3TRIAL))
    parser.add_argument("--5trial", dest="five", default=str(DEFAULT_5TRIAL))
    parser.add_argument(
        "--arm",
        default="abc_tattoo",
        help="abc_tattoo | rag_baseline | solo_dump",
    )
    args = parser.parse_args()

    d3 = _load(Path(args.three))
    d5 = _load(Path(args.five))
    task_map = _load_taskset()

    print("═" * 88)
    print(f"  Exp09 5-trial drop analysis  arm={args.arm}")
    print("═" * 88)

    diffs = _meta_diff(d3, d5)
    print("\n[a] 환경 차이 (top-level meta)")
    if not diffs:
        print("    동일 (model / arms / chunk / top_k 모두 일치)")
    else:
        for d in diffs:
            print(f"    {d}")

    res = analyze(d3, d5, args.arm, task_map)

    print("\n[b/c] trial 1-3 vs 4-5 채점·답변 분포")
    print(f"    n_tasks                      {res['n_tasks']}")
    print(
        f"    early (trial 1-3) mean       {res['early_mean']:.4f}  "
        f"std={res['early_std']:.4f}  n={res['early_n']}"
    )
    print(
        f"    late  (trial 4-5) mean       {res['late_mean']:.4f}  "
        f"std={res['late_std']:.4f}  n={res['late_n']}"
    )
    print(f"    Δ(late−early)                {res['delta_late_minus_early']:+.4f}")
    print(
        f"    3-trial JSON 전체 mean        {res['three_mean']:.4f}  "
        f"std={res['three_std']:.4f}  n={res['three_n']}"
    )
    print(f"    early errors / null_answer   {res['early_errors']} / {res['early_null_answers']}")
    print(f"    late  errors / null_answer   {res['late_errors']} / {res['late_null_answers']}")
    print(
        f"    answer unique mean (early)   {res['answer_diversity_early_mean']:.2f}  "
        f"(of 3 trials)"
    )
    print(
        f"    answer unique mean (late)    {res['answer_diversity_late_mean']:.2f}  "
        f"(of 2 trials)"
    )
    print(
        f"    early/late answer overlap    {res['answer_overlap_mean']:.2f}  "
        f"(answers shared between trial 1-3 and 4-5)"
    )
    consistent, total = res["append_consistency_3vs5"]
    print(
        f"    append consistency           {consistent}/{total} task 의 3-trial JSON 답변과 "
        f"5-trial JSON 의 trial 1-3 일치"
    )

    print("\n[per-task] late mean − early mean (Δ ≠ 0 만 출력)")
    for pt in sorted(res["per_task"], key=lambda x: x["delta"]):
        if abs(pt["delta"]) >= 0.001:
            print(
                f"    {pt['task_id']:<32}  early={pt['early_mean']:.3f}  "
                f"late={pt['late_mean']:.3f}  Δ={pt['delta']:+.3f}  "
                f"unique(e/l)={pt['early_answers_unique']}/{pt['late_answers_unique']}  "
                f"overlap={pt['overlap']}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
