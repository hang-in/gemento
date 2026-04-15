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


# ── 실험별 분석 로직 ──

def analyze_baseline(data: dict) -> dict:
    summary = {"experiment": "baseline", "tasks": []}
    for tr in data["results"]:
        scores = [score_answer(t["response"], tr.get("expected_answer", "")) for t in tr["trials"] if not t.get("error")]
        summary["tasks"].append({
            "task_id": tr["task_id"],
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "trials": len(scores),
        })
    all_scores = [t["avg_score"] for t in summary["tasks"]]
    summary["overall_avg_score"] = sum(all_scores) / len(all_scores) if all_scores else 0
    return summary

def analyze_multiloop(data: dict) -> dict:
    summary = {"experiment": "multiloop", "by_loops": defaultdict(list)}
    for tr in data["results"]:
        max_loops = tr["max_loops"]
        for trial in tr["trials"]:
            score = score_answer(str(trial.get("final_answer", "")), tr.get("expected_answer", ""))
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

def analyze_abc_pipeline(data: dict) -> dict:
    summary = {"experiment": "abc_pipeline", "tasks": []}
    for tr in data["results"]:
        for trial in tr["trials"]:
            score = score_answer(str(trial.get("final_answer", "")), tr.get("expected_answer", ""))
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

def analyze_solo_budget(data: dict) -> dict:
    summary = {"experiment": "solo_budget", "tasks": []}
    for tr in data["results"]:
        for trial in tr["trials"]:
            score = score_answer(str(trial.get("final_answer", "")), tr.get("expected_answer", ""))
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
    return "\n".join(lines)

ANALYZERS = {
    "baseline": analyze_baseline,
    "multiloop": analyze_multiloop,
    "abc_pipeline": analyze_abc_pipeline,
    "handoff_protocol": analyze_handoff_protocol,
    "solo_budget": analyze_solo_budget,
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_file")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    import glob
    matches = sorted(glob.glob(args.result_file))
    if not matches: return
    
    data = load_result(matches[-1])
    exp_type = data["experiment"]
    if exp_type in ANALYZERS:
        analysis = ANALYZERS[exp_type](data)
        print_report(analysis)
        if args.markdown: print("\n" + generate_markdown_report(analysis))

if __name__ == "__main__":
    main()
