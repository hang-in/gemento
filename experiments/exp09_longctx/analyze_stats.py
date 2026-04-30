"""Exp09 통계 검정 스크립트 — 5-trial 데이터 기반 H9b 유의성 검증.

- Paired t-test / Wilcoxon signed-rank (abc_tattoo vs rag_baseline)
- Bootstrap 95% CI
- size_class / hop_type 분해
- Small Paradox 하위 분석

사용:
    python -m experiments.exp09_longctx.analyze_stats
    python -m experiments.exp09_longctx.analyze_stats --result <path>
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from measure import score_answer_v2

RESULTS_DIR = Path(__file__).resolve().parent / "results"
_TASKS_DIR = Path(__file__).resolve().parent.parent / "tasks"


# ── 결과 파일 탐색 ──

def _find_result(path: str | None) -> Path:
    if path:
        p = Path(path)
        if p.exists():
            return p
        raise FileNotFoundError(f"Specified result file not found: {path}")

    # --result 미지정 시 5-trial 파일만 허용 (3-trial 폴백 제거)
    candidates = sorted(RESULTS_DIR.glob("exp09_longctx_5trial_*.json"))
    if candidates:
        return candidates[-1]
    raise FileNotFoundError(
        "5-trial result file not found in " + str(RESULTS_DIR) + "\n"
        "  Run first: python -m experiments.exp09_longctx.run_append_trials\n"
        "  To analyze a specific file (e.g. 3-trial): pass --result <path>"
    )


# ── 채점 ──

def _load_taskset() -> dict[str, dict]:
    return {t["id"]: t for t in json.load(open(_TASKS_DIR / "longctx_taskset.json"))["tasks"]}


def _score_trials(results_by_arm: dict, task_map: dict) -> dict[str, dict[str, list[float]]]:
    """arm → task_id → trial scores (v2)."""
    scored: dict[str, dict[str, list[float]]] = {}
    for arm_label, task_list in results_by_arm.items():
        scored[arm_label] = {}
        for task_entry in task_list:
            tid = task_entry["task_id"]
            te = task_map.get(tid, task_entry)
            scores = [
                score_answer_v2(str(t.get("final_answer") or ""), te)
                for t in task_entry["trials"]
            ]
            scored[arm_label][tid] = scores
    return scored


def _task_mean(scores: list[float]) -> float:
    return sum(scores) / len(scores) if scores else 0.0


# ── 통계 검정 ──

def _paired_ttest(a: list[float], b: list[float]) -> dict:
    """Paired t-test: H0: mean(a-b)=0."""
    try:
        from scipy import stats
        t_stat, p_val = stats.ttest_rel(a, b)
        n = len(a)
        diff = [x - y for x, y in zip(a, b)]
        mean_diff = sum(diff) / n
        std_diff = (sum((d - mean_diff) ** 2 for d in diff) / (n - 1)) ** 0.5
        cohens_d = mean_diff / std_diff if std_diff > 0 else 0.0
        return {"t": float(t_stat), "p_value": float(p_val), "cohens_d": cohens_d,
                "n": n, "mean_diff": mean_diff}
    except ImportError:
        return {"error": "scipy not installed", "n": len(a)}


def _wilcoxon(a: list[float], b: list[float]) -> dict:
    """Wilcoxon signed-rank test."""
    try:
        from scipy import stats
        diff = [x - y for x, y in zip(a, b)]
        if all(d == 0 for d in diff):
            return {"W": 0.0, "p_value": 1.0, "note": "all differences zero"}
        stat, p_val = stats.wilcoxon(diff)
        return {"W": float(stat), "p_value": float(p_val)}
    except ImportError:
        return {"error": "scipy not installed"}


def _bootstrap_ci(a: list[float], b: list[float],
                  n: int = 10_000, seed: int = 42) -> dict:
    """Bootstrap 95% CI for mean(a) - mean(b), trial-level."""
    rng = random.Random(seed)
    diffs = []
    for _ in range(n):
        sa = rng.choices(a, k=len(a))
        sb = rng.choices(b, k=len(b))
        diffs.append(sum(sa) / len(sa) - sum(sb) / len(sb))
    diffs.sort()
    lo = diffs[int(n * 0.025)]
    hi = diffs[int(n * 0.975)]
    obs = sum(a) / len(a) - sum(b) / len(b)
    return {"observed_delta": obs, "ci_95": [lo, hi], "includes_zero": lo <= 0 <= hi}


def _verdict(ttest: dict, wilcoxon: dict, ci: dict, alpha: float = 0.05) -> str:
    if "error" in ttest or "error" in wilcoxon:
        return "UNDETERMINED (scipy not installed)"
    tp = ttest.get("p_value", 1.0)
    wp = wilcoxon.get("p_value", 1.0)
    excludes_zero = not ci.get("includes_zero", True)
    if tp < alpha and wp < alpha and excludes_zero:
        return "SIGNIFICANT — 채택 권고"
    if tp < alpha or wp < alpha:
        return "MARGINAL — 조건부 채택 유지"
    return "NOT SIGNIFICANT — 미결 (검정력 부족 가능성)"


# ── 메인 ──

def main(result_path: str | None = None) -> None:
    result_file = _find_result(result_path)
    print(f"  Result file: {result_file.name}")

    with open(result_file) as f:
        data = json.load(f)

    n_trials = data.get("trials_per_task", "?")
    task_map = _load_taskset()
    scored = _score_trials(data["results_by_arm"], task_map)

    # task 목록 (abc_tattoo 기준)
    task_ids = list(scored.get("abc_tattoo", {}).keys())
    n_tasks = len(task_ids)

    # per-task means
    abc_means = [_task_mean(scored["abc_tattoo"].get(tid, [])) for tid in task_ids]
    rag_means = [_task_mean(scored["rag_baseline"].get(tid, [])) for tid in task_ids]

    # trial-level flat lists
    abc_all = [s for tid in task_ids for s in scored["abc_tattoo"].get(tid, [])]
    rag_all = [s for tid in task_ids for s in scored["rag_baseline"].get(tid, [])]

    print("\n" + "═" * 88)
    print(f"  Exp09 Statistical Analysis  ({n_trials} trials/task, {n_tasks} tasks)")
    print("═" * 88)

    # ── H9b 주 검정 ──
    ttest = _paired_ttest(abc_means, rag_means)
    wilc = _wilcoxon(abc_means, rag_means)
    ci = _bootstrap_ci(abc_all, rag_all)
    verd = _verdict(ttest, wilc, ci)

    abc_mean_overall = sum(abc_means) / n_tasks
    rag_mean_overall = sum(rag_means) / n_tasks
    delta_overall = abc_mean_overall - rag_mean_overall

    print(f"\n  H9b: abc_tattoo vs rag_baseline")
    print(f"  {'─' * 60}")
    print(f"  Overall mean:   abc={abc_mean_overall:.4f}  rag={rag_mean_overall:.4f}  Δ={delta_overall:+.4f}")
    if "error" not in ttest:
        print(f"  Paired t-test:  t={ttest['t']:.3f},  p={ttest['p_value']:.4f},  Cohen's d={ttest['cohens_d']:.3f}")
    else:
        print(f"  Paired t-test:  {ttest['error']}")
    if "error" not in wilc:
        print(f"  Wilcoxon:       W={wilc['W']:.1f},  p={wilc['p_value']:.4f}")
    else:
        print(f"  Wilcoxon:       {wilc['error']}")
    print(f"  Bootstrap 95% CI for Δ: [{ci['ci_95'][0]:.4f}, {ci['ci_95'][1]:.4f}]"
          f"  ({'excludes' if not ci['includes_zero'] else 'includes'} zero)")
    print(f"  → Verdict: {verd}")

    # ── size_class / hop_type 분해 ──
    groups: dict[str, list[str]] = {"size_class": {}, "hop_type": {}}  # type: ignore
    for tid in task_ids:
        t = task_map.get(tid, {})
        for key in ("size_class", "hop_type"):
            val = t.get(key, "unknown")
            groups[key].setdefault(val, []).append(tid)  # type: ignore

    group_results: dict = {}
    for group_key, group_map in groups.items():
        print(f"\n  {group_key} breakdown:")
        print(f"  {'─' * 60}")
        group_results[group_key] = {}
        for gval, tids in sorted(group_map.items()):
            ga = [_task_mean(scored["abc_tattoo"].get(t, [])) for t in tids]
            gr = [_task_mean(scored["rag_baseline"].get(t, [])) for t in tids]
            gm_abc = sum(ga) / len(ga) if ga else 0
            gm_rag = sum(gr) / gr.__len__() if gr else 0
            delta_g = gm_abc - gm_rag
            note = " ◄ Small Paradox?" if group_key == "size_class" and gval == "small" and delta_g < 0 else ""
            print(f"    {gval:<12} (n={len(tids)}):  abc={gm_abc:.3f}  rag={gm_rag:.3f}  Δ={delta_g:+.3f}{note}")
            group_results[group_key][gval] = {
                "n_tasks": len(tids),
                "abc_mean": gm_abc, "rag_mean": gm_rag, "delta": delta_g,
            }

    # ── Small Paradox 상세 ──
    small_ids = [tid for tid in task_ids if task_map.get(tid, {}).get("size_class") == "small"]
    print(f"\n  Small Paradox 하위 분석  (n={len(small_ids)} small tasks)")
    print(f"  {'─' * 60}")
    small_detail = []
    for tid in small_ids:
        abc_s = scored["abc_tattoo"].get(tid, [])
        rag_s = scored["rag_baseline"].get(tid, [])
        abc_m = _task_mean(abc_s)
        rag_m = _task_mean(rag_s)
        flag = " ◄ ABC < RAG" if abc_m < rag_m - 0.01 else ""
        print(f"    {tid:<35}  abc={abc_m:.3f}  rag={rag_m:.3f}  Δ={abc_m-rag_m:+.3f}  trials_abc={abc_s}{flag}")
        small_detail.append({"task_id": tid, "abc_mean": abc_m, "rag_mean": rag_m,
                              "delta": abc_m - rag_m, "abc_trials": abc_s, "rag_trials": rag_s})

    # ── JSON 저장 ──
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"exp09_stats_{ts}.json"
    summary = {
        "generated_at": ts,
        "result_file": str(result_file),
        "n_tasks": n_tasks,
        "n_trials_per_task": n_trials,
        "h9b_overall": {
            "abc_mean": abc_mean_overall, "rag_mean": rag_mean_overall, "delta": delta_overall,
        },
        "h9b_paired_ttest": ttest,
        "h9b_wilcoxon": wilc,
        "bootstrap_ci": ci,
        "verdict": verd,
        "size_class_breakdown": group_results.get("size_class", {}),
        "hop_type_breakdown": group_results.get("hop_type", {}),
        "small_paradox": small_detail,
    }
    out_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n  → JSON saved: {out_path}")
    print("\nANALYSIS COMPLETE")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", default=None, help="Path to result JSON")
    args = parser.parse_args()
    main(args.result)
