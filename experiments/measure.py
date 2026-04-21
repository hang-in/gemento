"""제멘토 실험 측정/채점 스크립트.

실험 결과 JSON을 읽어 메트릭을 계산하고 요약 보고서를 생성한다.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from collections import defaultdict


def load_result(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


# ── 정확도 채점 ──

def score_answer(response: str, expected: str) -> float:
    if not response or not expected:
        return 0.0
    response_lower = response.lower().strip()
    expected_lower = expected.lower().strip()

    if expected_lower in response_lower:
        return 1.0

    expected_tokens = set(re.findall(r'\b\w+\b', expected_lower))
    response_tokens = set(re.findall(r'\b\w+\b', response_lower))
    if expected_tokens and expected_tokens.issubset(response_tokens):
        return 0.8

    overlap = expected_tokens & response_tokens
    if expected_tokens:
        return len(overlap) / len(expected_tokens) * 0.6

    return 0.0


def score_answer_v2(response: str, task_entry: dict) -> float:
    """
    keyword-group 기반 채점.
    scoring_keywords: [[token, ...], ...]
    각 그룹의 모든 토큰이 response에 포함되면 해당 그룹 매칭.
    점수 = 매칭된 그룹 수 / 전체 그룹 수
    scoring_keywords 없으면 score_answer(v1) fallback.
    """
    keywords = task_entry.get("scoring_keywords")
    if not keywords:
        return score_answer(response, task_entry.get("expected_answer", ""))

    response_lower = response.lower()
    matched = sum(
        1 for group in keywords
        if all(token.lower() in response_lower for token in group)
    )
    return matched / len(keywords)


# ── 실험별 분석 로직 ──

def analyze_baseline(data: dict, task_map: dict = None) -> dict:
    summary = {"experiment": "baseline", "tasks": []}
    task_map = task_map or {}
    for tr in data["results"]:
        task_entry = task_map.get(tr["task_id"], tr)
        scores = [score_answer_v2(t["response"], task_entry) for t in tr["trials"] if not t.get("error")]
        summary["tasks"].append({
            "task_id": tr["task_id"],
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "trials": len(scores),
        })
    all_scores = [t["avg_score"] for t in summary["tasks"]]
    summary["overall_avg_score"] = sum(all_scores) / len(all_scores) if all_scores else 0
    return summary

def analyze_multiloop(data: dict, task_map: dict = None) -> dict:
    summary = {"experiment": "multiloop", "by_loops": defaultdict(list)}
    task_map = task_map or {}
    for tr in data["results"]:
        max_loops = tr["max_loops"]
        task_entry = task_map.get(tr["task_id"], tr)
        for trial in tr["trials"]:
            score = score_answer_v2(str(trial.get("final_answer", "")), task_entry)
            summary["by_loops"][max_loops].append({"score": score, "converged": trial["final_phase"] == "CONVERGED"})
    
    loop_summary = []
    for loops in sorted(summary["by_loops"].keys()):
        entries = summary["by_loops"][loops]
        loop_summary.append({
            "max_loops": loops,
            "avg_score": sum(e["score"] for e in entries) / len(entries),
            "converged_rate": sum(1 for e in entries if e["converged"]) / len(entries),
        })
    return {"experiment": "multiloop", "loop_analysis": loop_summary}

def analyze_abc_pipeline(data: dict, task_map: dict = None) -> dict:
    summary = {"experiment": "abc_pipeline", "tasks": []}
    task_map = task_map or {}
    for tr in data["results"]:
        task_entry = task_map.get(tr["task_id"], tr)
        for trial in tr["trials"]:
            score = score_answer_v2(str(trial.get("final_answer", "")), task_entry)
            summary["tasks"].append({
                "task_id": tr["task_id"],
                "trial": trial["trial"],
                "score": score,
                "converged": trial["final_phase"] == "CONVERGED",
                "total_cycles": trial["total_cycles"],
            })
    tasks = summary["tasks"]
    summary["overall"] = {
        "convergence_rate": sum(1 for t in tasks if t["converged"]) / len(tasks) if tasks else 0,
        "avg_score": sum(t["score"] for t in tasks) / len(tasks) if tasks else 0,
        "avg_cycles": sum(t["total_cycles"] for t in tasks) / len(tasks) if tasks else 0,
    }
    return summary

def analyze_handoff_protocol(data: dict) -> dict:
    summary = {"experiment": "handoff_protocol", "tasks": []}
    task_handoff_scores = []
    task_backprop_scores = []

    for tr in data.get("results", []):
        h_scores = []
        b_scores = []
        for trial in tr.get("trials", []):
            cycles = trial.get("cycle_details", [])
            for i in range(len(cycles)):
                c = cycles[i]
                h_in = c.get("tattoo_in", {}).get("handoff", {}).get("a2b", {})
                h_out = c.get("tattoo_out", {}).get("handoff", {}).get("b2c", {})
                constraints = h_in.get("constraints", [])
                if constraints:
                    b_content = str(h_out.get("implementation_summary", "")) + str(h_out.get("self_test_results", ""))
                    matched = sum(1 for con in constraints if con.lower() in b_content.lower())
                    h_scores.append(1.0 - (matched / len(constraints)))
                
                rej = c.get("tattoo_out", {}).get("handoff", {}).get("reject_memo")
                if rej and rej.get("target_phase") == "A" and i + 1 < len(cycles):
                    prev_bp = h_in.get("blueprint", "")
                    next_bp = cycles[i+1].get("tattoo_out", {}).get("handoff", {}).get("a2b", {}).get("blueprint", "")
                    b_scores.append(1.0 if prev_bp != next_bp else 0.0)

        summary["tasks"].append({
            "task_id": tr["task_id"],
            "avg_handoff_loss": sum(h_scores) / len(h_scores) if h_scores else 0,
            "avg_backprop_accuracy": sum(b_scores) / len(b_scores) if b_scores else 0,
            "sample_cycles": len(h_scores),
        })
        task_handoff_scores.extend(h_scores)
        task_backprop_scores.extend(b_scores)

    summary["overall_avg_loss_rate"] = sum(task_handoff_scores) / len(task_handoff_scores) if task_handoff_scores else 0
    summary["overall_avg_backprop_accuracy"] = sum(task_backprop_scores) / len(task_backprop_scores) if task_backprop_scores else 0
    return summary

def analyze_solo_budget(data: dict, task_map: dict = None) -> dict:
    summary = {"experiment": "solo_budget", "tasks": []}
    task_map = task_map or {}
    for tr in data["results"]:
        task_entry = task_map.get(tr["task_id"], tr)
        for trial in tr["trials"]:
            score = score_answer_v2(str(trial.get("final_answer", "")), task_entry)
            summary["tasks"].append({
                "task_id": tr["task_id"],
                "trial": trial["trial"],
                "score": score,
                "converged": trial["final_phase"] == "CONVERGED",
                "total_cycles": trial["actual_loops"],
            })
    tasks = summary["tasks"]
    summary["overall"] = {
        "convergence_rate": sum(1 for t in tasks if t["converged"]) / len(tasks) if tasks else 0,
        "avg_score": sum(t["score"] for t in tasks) / len(tasks) if tasks else 0,
        "avg_loops": sum(t["total_cycles"] for t in tasks) / len(tasks) if tasks else 0,
    }
    return summary


# ── 보고서 출력 ──

def print_report(analysis: dict):
    exp = analysis["experiment"]
    print(f"\n{'═' * 60}\n  실험 분석: {exp}\n{'═' * 60}")

    if exp == "solo_budget":
        o = analysis["overall"]
        print(f"\n  수렴률: {o['convergence_rate']:.1%}\n  평균 점수: {o['avg_score']:.3f}\n  평균 루프: {o['avg_loops']:.1f}")
        print(f"\n  {'태스크':<15} {'Trial':>6} {'수렴':>6} {'점수':>6} {'루프':>8}\n  {'-' * 45}")
        for t in analysis["tasks"]:
            conv = "✓" if t["converged"] else "✗"
            print(f"  {t['task_id']:<15} {t['trial']:>6} {conv:>6} {t['score']:>6.2f} {t['total_cycles']:>8}")
    
    elif exp == "handoff_protocol":
        print(f"\n  전체 Loss Rate: {analysis['overall_avg_loss_rate']:.1%}\n  전체 Backprop Acc: {analysis['overall_avg_backprop_accuracy']:.1%}")
        for t in analysis["tasks"]:
            print(f"  {t['task_id']:<20} {t['avg_handoff_loss']:>10.1%} {t['avg_backprop_accuracy']:>12.1%}")

def generate_markdown_report(analysis: dict) -> str:
    exp = analysis["experiment"]
    lines = [f"# 실험 결과: {exp}", ""]
    if exp == "solo_budget":
        o = analysis["overall"]
        lines.extend([f"**수렴률:** {o['convergence_rate']:.1%}", f"**평균 점수:** {o['avg_score']:.3f}", ""])
        lines.extend(["| 태스크 | 수렴 | 점수 | 루프 |", "|---|---|---|---|"])
        for t in analysis["tasks"]:
            conv = "✓" if t["converged"] else "✗"
            lines.append(f"| {t['task_id']} | {conv} | {t['score']:.2f} | {t['total_cycles']} |")
    elif exp == "loop_saturation":
        lines.append(f"> {analysis.get('note', '')}")
        lines.append("")

        # 포화 곡선 테이블
        lines.append("## Loop Saturation Curve")
        lines.append("")
        lines.append("| MAX_CYCLES | Baseline 정답률 | Phase 정답률 | Delta | Baseline 수렴률 | Phase 수렴률 |")
        lines.append("|------------|----------------|-------------|-------|-----------------|-------------|")
        curve = analysis.get("saturation_curve", {})
        baseline_curve = curve.get("baseline", {})
        phase_curve = curve.get("phase", {})
        delta_map = analysis.get("phase_prompt_delta", {})
        for mc in sorted(set(list(baseline_curve.keys()) + list(phase_curve.keys()))):
            b = baseline_curve.get(mc, {})
            p = phase_curve.get(mc, {})
            b_acc = f"{b.get('accuracy', 0):.1%}" if b else "N/A"
            p_acc = f"{p.get('accuracy', 0):.1%}" if p else "N/A"
            delta = delta_map.get(mc)
            delta_str = f"{delta:+.1%}" if delta is not None else "N/A"
            b_conv = f"{b.get('convergence', 0):.1%}" if b else "N/A"
            p_conv = f"{p.get('convergence', 0):.1%}" if p else "N/A"
            lines.append(f"| {mc} | {b_acc} | {p_acc} | {delta_str} | {b_conv} | {p_conv} |")

        lines.append("")

        # 고난도 태스크 테이블
        new_results = analysis.get("new_task_results", {})
        if new_results:
            lines.append("## High-Difficulty Tasks (04)")
            lines.append("")
            lines.append("| Task | Best Accuracy | Best Condition |")
            lines.append("|------|--------------|---------------|")
            for tid in sorted(new_results.keys()):
                r = new_results[tid]
                lines.append(f"| {tid} | {r['best_accuracy']:.1%} | {r['best_condition']} |")

    return "\n".join(lines)

def analyze_loop_saturation(data: dict, task_map: dict = None) -> dict:
    """실험 7: Loop Saturation + Loop-Phase 분석."""
    task_map = task_map or {}
    results_by_condition = data.get("results_by_condition", {})

    # 조건별 집계: {label: {max_cycles, use_phase_prompt, accuracy, convergence, avg_cycles}}
    condition_stats: dict[str, dict] = {}
    per_task: dict[str, dict[str, dict]] = {}

    for label, task_list in results_by_condition.items():
        scores, converged_flags, cycle_counts = [], [], []

        for tr in task_list:
            task_entry = task_map.get(tr["task_id"], tr)
            task_id = tr["task_id"]
            if task_id not in per_task:
                per_task[task_id] = {}

            t_scores, t_cycles, t_conv = [], [], []
            for trial in tr.get("trials", []):
                s = score_answer_v2(str(trial.get("final_answer", "")), task_entry)
                conv = trial.get("final_phase") == "CONVERGED"
                cyc = trial.get("actual_cycles", 0)
                scores.append(s)
                converged_flags.append(conv)
                cycle_counts.append(cyc)
                t_scores.append(s)
                t_conv.append(conv)
                t_cycles.append(cyc)

            per_task[task_id][label] = {
                "accuracy": sum(t_scores) / len(t_scores) if t_scores else 0.0,
                "convergence": sum(t_conv) / len(t_conv) if t_conv else 0.0,
                "avg_cycles": sum(t_cycles) / len(t_cycles) if t_cycles else 0.0,
            }

        # 조건 메타 파싱 (label 형식: baseline_8 / phase_20)
        parts = label.split("_")
        use_phase = parts[0] == "phase"
        max_cyc = int(parts[-1])

        condition_stats[label] = {
            "max_cycles": max_cyc,
            "use_phase_prompt": use_phase,
            "accuracy": sum(scores) / len(scores) if scores else 0.0,
            "convergence": sum(converged_flags) / len(converged_flags) if converged_flags else 0.0,
            "avg_cycles": sum(cycle_counts) / len(cycle_counts) if cycle_counts else 0.0,
        }

    # 포화 곡선: baseline vs phase 각 max_cycles별 집계
    max_cycles_values = sorted({v["max_cycles"] for v in condition_stats.values()})
    saturation_curve: dict[str, dict] = {"baseline": {}, "phase": {}}
    for mc in max_cycles_values:
        for prompt_type in ("baseline", "phase"):
            lbl = f"{prompt_type}_{mc}"
            if lbl in condition_stats:
                saturation_curve[prompt_type][mc] = {
                    "accuracy": condition_stats[lbl]["accuracy"],
                    "convergence": condition_stats[lbl]["convergence"],
                    "avg_cycles": condition_stats[lbl]["avg_cycles"],
                }

    # phase - baseline 정답률 델타
    phase_delta: dict[int, float] = {}
    for mc in max_cycles_values:
        b = saturation_curve["baseline"].get(mc, {}).get("accuracy", 0.0)
        p = saturation_curve["phase"].get(mc, {}).get("accuracy", 0.0)
        if f"baseline_{mc}" in condition_stats and f"phase_{mc}" in condition_stats:
            phase_delta[mc] = round(p - b, 4)

    # 신규 04급 태스크 결과
    new_task_ids = {"math-04", "logic-04", "synthesis-04"}
    new_task_results: dict[str, dict] = {}
    for tid in new_task_ids:
        if tid not in per_task:
            continue
        best_acc = 0.0
        best_cond = ""
        for lbl, stats in per_task[tid].items():
            if stats["accuracy"] > best_acc:
                best_acc = stats["accuracy"]
                best_cond = lbl
        new_task_results[tid] = {
            "best_accuracy": best_acc,
            "best_condition": best_cond,
        }

    return {
        "experiment": "loop_saturation",
        "note": "n=3 per condition per task — interpret with caution",
        "saturation_curve": saturation_curve,
        "condition_stats": condition_stats,
        "per_task": per_task,
        "phase_prompt_delta": phase_delta,
        "new_task_results": new_task_results,
    }


ANALYZERS = {
    "baseline": analyze_baseline,
    "multiloop": analyze_multiloop,
    "abc_pipeline": analyze_abc_pipeline,
    "handoff_protocol": analyze_handoff_protocol,
    "solo_budget": analyze_solo_budget,
    "loop_saturation": analyze_loop_saturation,
}


def rescore_all(results_dir: Path, task_map: dict):
    """
    results/ 디렉토리의 모든 JSON을 v1/v2로 재채점하여 비교표 출력.
    결과 JSON은 수정하지 않는다 (읽기 전용).
    """
    import glob as _glob

    # 실험 타입별 최신 파일 결정
    type_to_files: dict[str, list] = {}
    for path in sorted(results_dir.glob("*.json")):
        try:
            data = load_result(str(path))
        except Exception as e:
            print(f"[warn] skip {path.name}: {e}", file=sys.stderr)
            continue
        exp_type = data.get("experiment", "unknown")
        type_to_files.setdefault(exp_type, []).append((path, data))

    # 모든 실험 타입을 v1/v2로 재채점한다.
    SKIP_TYPES: set[str] = set()

    print(f"\n{'═' * 51}")
    print("  Rescore 결과 비교 (v1 substring vs v2 keyword)")
    print(f"{'═' * 51}")
    print(f"  {'파일명':<35} {'v1 avg':>7} {'v2 avg':>7} {'diff':>8}")
    print(f"  {'-' * 49}")

    for exp_type, entries in sorted(type_to_files.items()):
        if exp_type in SKIP_TYPES:
            path = entries[-1][0]
            print(f"  {path.name:<35} {'N/A':>7} {'N/A':>7} {'(skip)':>8}")
            continue

        path, data = entries[-1]  # 가장 최신

        def _score_trials(score_fn):
            scores = []
            for tr in data.get("results", []):
                task_entry_v2 = task_map.get(tr["task_id"], tr)
                for trial in tr.get("trials", []):
                    if exp_type == "baseline":
                        resp = trial.get("response", "")
                    else:
                        resp = str(trial.get("final_answer", ""))
                    scores.append(score_fn(resp, tr, task_entry_v2))
            return sum(scores) / len(scores) if scores else 0.0

        v1_avg = _score_trials(lambda r, tr, _: score_answer(r, tr.get("expected_answer", "")))
        v2_avg = _score_trials(lambda r, _, te: score_answer_v2(r, te))
        diff = v2_avg - v1_avg
        sign = "+" if diff >= 0 else ""
        print(f"  {path.name:<35} {v1_avg:>7.3f} {v2_avg:>7.3f} {sign}{diff*100:>6.1f}%")

    print()


def load_task_map() -> dict:
    taskset_path = Path(__file__).parent / "tasks" / "taskset.json"
    if not taskset_path.exists():
        print(f"[warn] taskset.json not found at {taskset_path}, falling back to v1 scoring", file=sys.stderr)
        return {}
    with open(taskset_path) as f:
        ts = json.load(f)
    return {t["id"]: t for t in ts.get("tasks", [])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_file", nargs="?", help="단일 파일 분석")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--rescore", action="store_true", help="전체 결과 재채점 비교")
    args = parser.parse_args()

    task_map = load_task_map()

    if args.rescore:
        rescore_all(Path(__file__).parent / "results", task_map)
    elif args.result_file:
        import glob
        matches = sorted(glob.glob(args.result_file))
        if not matches:
            return

        data = load_result(matches[-1])
        exp_type = data["experiment"]
        if exp_type in ANALYZERS:
            analyzer = ANALYZERS[exp_type]
            if exp_type == "handoff_protocol":
                analysis = analyzer(data)
            else:
                analysis = analyzer(data, task_map)
            print_report(analysis)
            if args.markdown:
                print("\n" + generate_markdown_report(analysis))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
