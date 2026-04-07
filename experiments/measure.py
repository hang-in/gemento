"""제멘토 실험 측정/채점 스크립트.

실험 결과 JSON을 읽어 메트릭을 계산하고 요약 보고서를 생성한다.

Usage:
    python measure.py results/exp00_baseline_*.json
    python measure.py results/exp02_multiloop_*.json --compare results/exp00_baseline_*.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict


def load_result(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


# ── 정확도 채점 ──

def score_answer(response: str, expected: str) -> float:
    """답변의 정확도를 0.0-1.0으로 채점한다.

    단순 포함 기반 채점 (v0).
    향후 LLM 기반 채점이나 정규표현식 매칭으로 교체 가능.
    """
    if not response or not expected:
        return 0.0
    response_lower = response.lower().strip()
    expected_lower = expected.lower().strip()

    # 정확 일치
    if expected_lower in response_lower:
        return 1.0

    # 핵심 숫자/단어 추출 비교
    import re
    expected_tokens = set(re.findall(r'\b\w+\b', expected_lower))
    response_tokens = set(re.findall(r'\b\w+\b', response_lower))
    if expected_tokens and expected_tokens.issubset(response_tokens):
        return 0.8

    # 부분 일치
    overlap = expected_tokens & response_tokens
    if expected_tokens:
        return len(overlap) / len(expected_tokens) * 0.6

    return 0.0


# ── 실험별 메트릭 계산 ──

def analyze_baseline(data: dict) -> dict:
    """실험 0 분석: 태스크별 baseline 점수."""
    summary = {"experiment": "baseline", "tasks": []}

    for task_result in data["results"]:
        scores = []
        durations = []
        for trial in task_result["trials"]:
            if trial.get("error"):
                continue
            score = score_answer(trial["response"], task_result.get("expected_answer", ""))
            scores.append(score)
            durations.append(trial["duration_ms"])

        summary["tasks"].append({
            "task_id": task_result["task_id"],
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "scores": scores,
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "trials": len(scores),
        })

    all_scores = [t["avg_score"] for t in summary["tasks"]]
    summary["overall_avg_score"] = sum(all_scores) / len(all_scores) if all_scores else 0
    return summary


def analyze_assertion_cap(data: dict) -> dict:
    """실험 1 분석: assertion 수별 품질 변곡점."""
    summary = {"experiment": "assertion_cap", "by_cap": defaultdict(list)}

    for entry in data["results"]:
        cap = entry["cap"]
        for trial in entry["trials"]:
            if trial.get("error"):
                continue
            summary["by_cap"][cap].append({
                "task_id": entry["task_id"],
                "duration_ms": trial["duration_ms"],
                "has_response": bool(trial.get("parsed")),
            })

    # cap별 평균
    cap_summary = []
    for cap in sorted(summary["by_cap"].keys()):
        entries = summary["by_cap"][cap]
        cap_summary.append({
            "cap": cap,
            "success_rate": sum(1 for e in entries if e["has_response"]) / len(entries) if entries else 0,
            "avg_duration_ms": sum(e["duration_ms"] for e in entries) / len(entries) if entries else 0,
            "sample_count": len(entries),
        })

    return {"experiment": "assertion_cap", "cap_analysis": cap_summary}


def analyze_multiloop(data: dict) -> dict:
    """실험 2 분석: 루프 수별 품질 누적."""
    summary = {"experiment": "multiloop", "by_loops": defaultdict(list)}

    for entry in data["results"]:
        max_loops = entry["max_loops"]
        for trial in entry["trials"]:
            # 최종 답변 채점
            final_answer = trial.get("final_answer", "")
            score = score_answer(str(final_answer), entry.get("expected_answer", ""))

            summary["by_loops"][max_loops].append({
                "task_id": entry["task_id"],
                "score": score,
                "actual_loops": trial["actual_loops"],
                "final_confidence": trial["final_confidence"],
                "total_assertions": trial["total_assertions"],
                "final_phase": trial["final_phase"],
                "confidence_trajectory": [
                    d["confidence"] for d in trial.get("loop_details", [])
                ],
            })

    loop_summary = []
    for loops in sorted(summary["by_loops"].keys()):
        entries = summary["by_loops"][loops]
        scores = [e["score"] for e in entries]
        confidences = [e["final_confidence"] for e in entries]
        loop_summary.append({
            "max_loops": loops,
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "converged_rate": sum(1 for e in entries if e["final_phase"] == "CONVERGED") / len(entries) if entries else 0,
            "avg_assertions": sum(e["total_assertions"] for e in entries) / len(entries) if entries else 0,
            "sample_count": len(entries),
        })

    return {"experiment": "multiloop", "loop_analysis": loop_summary}


def analyze_error_propagation(data: dict) -> dict:
    """실험 3 분석: 오류 전파 메트릭."""
    summary = {"experiment": "error_propagation", "by_fault_type": defaultdict(list)}

    for entry in data["results"]:
        fault_type = entry["fault"]["type"]
        for trial in entry["trials"]:
            trajectory = trial.get("confidence_trajectory", [])
            # error_half_life: confidence < 0.5 까지 걸린 루프 수
            half_life = None
            for i, conf in enumerate(trajectory):
                if conf < 0.5:
                    half_life = i + 1
                    break

            summary["by_fault_type"][fault_type].append({
                "task_id": entry["task_id"],
                "error_half_life": half_life,
                "final_confidence": trial["final_confidence"],
                "confidence_trajectory": trajectory,
                "post_loops": trial["post_injection_loops"],
            })

    fault_summary = []
    for fault_type, entries in summary["by_fault_type"].items():
        half_lives = [e["error_half_life"] for e in entries if e["error_half_life"] is not None]
        fault_summary.append({
            "fault_type": fault_type,
            "avg_error_half_life": sum(half_lives) / len(half_lives) if half_lives else None,
            "detection_rate": len(half_lives) / len(entries) if entries else 0,
            "avg_final_confidence": sum(e["final_confidence"] for e in entries) / len(entries) if entries else 0,
            "sample_count": len(entries),
        })

    return {"experiment": "error_propagation", "fault_analysis": fault_summary}


# ── 보고서 생성 ──

def print_report(analysis: dict):
    """분석 결과를 사람이 읽을 수 있는 형태로 출력한다."""
    exp = analysis["experiment"]
    print(f"\n{'═' * 60}")
    print(f"  실험 분석: {exp}")
    print(f"{'═' * 60}")

    if exp == "baseline":
        print(f"\n  전체 평균 점수: {analysis['overall_avg_score']:.3f}")
        print(f"\n  {'태스크':<20} {'평균점수':>8} {'평균시간(ms)':>12} {'시행':>6}")
        print(f"  {'-' * 50}")
        for t in analysis["tasks"]:
            print(f"  {t['task_id']:<20} {t['avg_score']:>8.3f} {t['avg_duration_ms']:>12.0f} {t['trials']:>6}")

    elif exp == "assertion_cap":
        print(f"\n  {'Cap':>4} {'성공률':>8} {'평균시간(ms)':>12} {'샘플':>6}")
        print(f"  {'-' * 34}")
        for c in analysis["cap_analysis"]:
            print(f"  {c['cap']:>4} {c['success_rate']:>8.2%} {c['avg_duration_ms']:>12.0f} {c['sample_count']:>6}")

    elif exp == "multiloop":
        print(f"\n  {'Loops':>6} {'평균점수':>8} {'평균신뢰도':>10} {'수렴률':>8} {'평균Assertion':>14}")
        print(f"  {'-' * 50}")
        for l in analysis["loop_analysis"]:
            print(f"  {l['max_loops']:>6} {l['avg_score']:>8.3f} {l['avg_confidence']:>10.3f} "
                  f"{l['converged_rate']:>8.2%} {l['avg_assertions']:>14.1f}")

    elif exp == "error_propagation":
        print(f"\n  {'결함유형':<20} {'평균Half-life':>14} {'감지율':>8} {'최종신뢰도':>10}")
        print(f"  {'-' * 56}")
        for f in analysis["fault_analysis"]:
            hl = f"{f['avg_error_half_life']:.1f}" if f['avg_error_half_life'] else "N/A"
            print(f"  {f['fault_type']:<20} {hl:>14} {f['detection_rate']:>8.2%} "
                  f"{f['avg_final_confidence']:>10.3f}")

    print()


# ── 결과 마크다운 생성 ──

def generate_markdown_report(analysis: dict) -> str:
    """분석 결과를 마크다운으로 변환한다."""
    exp = analysis["experiment"]
    lines = [
        "---",
        f"type: result",
        f"status: done",
        f"updated_at: {__import__('time').strftime('%Y-%m-%d')}",
        "---",
        "",
        f"# 실험 결과: {exp}",
        "",
    ]

    if exp == "baseline":
        lines.append(f"**전체 평균 점수:** {analysis['overall_avg_score']:.3f}")
        lines.append("")
        lines.append("| 태스크 | 평균점수 | 평균시간(ms) | 시행 |")
        lines.append("|--------|---------|-------------|------|")
        for t in analysis["tasks"]:
            lines.append(f"| {t['task_id']} | {t['avg_score']:.3f} | {t['avg_duration_ms']:.0f} | {t['trials']} |")

    elif exp == "multiloop":
        lines.append("| Loops | 평균점수 | 평균신뢰도 | 수렴률 | 평균Assertion |")
        lines.append("|-------|---------|----------|--------|-------------|")
        for l in analysis["loop_analysis"]:
            lines.append(f"| {l['max_loops']} | {l['avg_score']:.3f} | {l['avg_confidence']:.3f} | "
                        f"{l['converged_rate']:.1%} | {l['avg_assertions']:.1f} |")

    elif exp == "error_propagation":
        lines.append("| 결함유형 | 평균Half-life | 감지율 | 최종신뢰도 |")
        lines.append("|---------|-------------|--------|----------|")
        for f in analysis["fault_analysis"]:
            hl = f"{f['avg_error_half_life']:.1f}" if f['avg_error_half_life'] else "N/A"
            lines.append(f"| {f['fault_type']} | {hl} | {f['detection_rate']:.1%} | "
                        f"{f['avg_final_confidence']:.3f} |")

    return "\n".join(lines)


# ── CLI ──

ANALYZERS = {
    "baseline": analyze_baseline,
    "assertion_cap": analyze_assertion_cap,
    "multiloop": analyze_multiloop,
    "error_propagation": analyze_error_propagation,
}


def main():
    parser = argparse.ArgumentParser(description="제멘토 실험 결과 분석")
    parser.add_argument("result_file", help="결과 JSON 파일 경로")
    parser.add_argument("--markdown", action="store_true", help="마크다운 보고서 출력")
    parser.add_argument("--save-md", help="마크다운 파일로 저장할 경로")
    args = parser.parse_args()

    data = load_result(args.result_file)
    exp_type = data["experiment"]

    if exp_type not in ANALYZERS:
        print(f"Unknown experiment type: {exp_type}")
        sys.exit(1)

    analysis = ANALYZERS[exp_type](data)
    print_report(analysis)

    if args.markdown or args.save_md:
        md = generate_markdown_report(analysis)
        if args.save_md:
            Path(args.save_md).parent.mkdir(parents=True, exist_ok=True)
            with open(args.save_md, "w") as f:
                f.write(md)
            print(f"  → Markdown saved: {args.save_md}")
        else:
            print(md)


if __name__ == "__main__":
    main()
