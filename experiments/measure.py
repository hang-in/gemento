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

    elif exp == "cross_validation":
        print(f"\n  전체 감지율: {analysis['overall_detection_rate']:.1%}")
        print(f"  게이트 판정: {analysis['gate_result']}")
        print(f"\n  {'결함유형':<20} {'감지':>6} {'/ 전체':>8} {'감지율':>8}")
        print(f"  {'-' * 44}")
        for f in analysis["fault_analysis"]:
            print(f"  {f['fault_type']:<20} {f['detected']:>6} {'/ ' + str(f['total']):>8} "
                  f"{f['detection_rate']:>8.1%}")

    elif exp == "abc_pipeline":
        o = analysis["overall"]
        print(f"\n  수렴률: {o['convergence_rate']:.1%}")
        print(f"  평균 점수: {o['avg_score']:.3f}")
        print(f"  평균 사이클: {o['avg_cycles']:.1f}")
        print(f"  C 평균 전이 횟수: {o['c_transition_rate']:.1f}")
        print(f"\n  {'태스크':<15} {'Trial':>6} {'수렴':>6} {'점수':>6} {'사이클':>8} {'C전이':>6}")
        print(f"  {'-' * 50}")
        for t in analysis["tasks"]:
            conv = "✓" if t["converged"] else "✗"
            print(f"  {t['task_id']:<15} {t['trial']:>6} {conv:>6} {t['score']:>6.2f} "
                  f"{t['total_cycles']:>8} {t['c_transitions']:>6}")

    elif exp == "handoff_protocol":
        print(f"\n  전체 Handoff Loss Rate: {analysis['overall_avg_loss_rate']:.1%}")
        print(f"  전체 Backprop Accuracy: {analysis['overall_avg_backprop_accuracy']:.1%}")
        print(f"\n  {'태스크':<20} {'Loss Rate':>10} {'Backprop Acc':>12} {'샘플':>6}")
        print(f"  {'-' * 52}")
        for t in analysis["tasks"]:
            print(f"  {t['task_id']:<20} {t['avg_handoff_loss']:>10.1%} {t['avg_backprop_accuracy']:>12.1%} {t['sample_cycles']:>6}")

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


def analyze_cross_validation(data: dict) -> dict:
    """실험 3.5 분석: 교차 검증 감지율."""
    summary = {"experiment": "cross_validation", "by_fault_type": defaultdict(list)}

    for entry in data["results"]:
        fault_type = entry["fault"]["type"]
        for trial in entry["trials"]:
            summary["by_fault_type"][fault_type].append({
                "task_id": entry["task_id"],
                "detected": trial["detected"],
                "error": trial.get("error"),
            })

    fault_summary = []
    for fault_type, entries in summary["by_fault_type"].items():
        valid = [e for e in entries if not e.get("error")]
        detected = sum(1 for e in valid if e["detected"])
        fault_summary.append({
            "fault_type": fault_type,
            "detection_rate": detected / len(valid) if valid else 0,
            "detected": detected,
            "total": len(valid),
            "errors": len(entries) - len(valid),
        })

    total_valid = sum(f["total"] for f in fault_summary)
    total_detected = sum(f["detected"] for f in fault_summary)
    return {
        "experiment": "cross_validation",
        "fault_analysis": fault_summary,
        "overall_detection_rate": total_detected / total_valid if total_valid else 0,
        "gate_result": "PASS" if total_valid and total_detected / total_valid > 0.5 else "FAIL",
    }


def analyze_handoff_protocol(data: dict) -> dict:
    """실험 4.5 분석: Handoff Protocol 메트릭 (v1)."""
    summary = {
        "experiment": "handoff_protocol",
        "handoff_loss_rates": [],
        "backprop_accuracies": [],
        "tasks": []
    }

    for task_result in data.get("results", []):
        task_handoff_scores = []
        task_backprop_scores = []

        for trial in task_result.get("trials", []):
            cycles = trial.get("cycle_details", [])
            for i in range(len(cycles)):
                cycle = cycles[i]
                tattoo_in = cycle.get("tattoo_in", {})
                tattoo_out = cycle.get("tattoo_out", {})
                
                # ── 1. handoff_loss_rate 계산 ──
                # A2B의 제약 조건이 B2C에서 언급되었는지 확인
                handoff_a2b = tattoo_out.get("handoff", {}).get("a2b", {})
                handoff_b2c = tattoo_out.get("handoff", {}).get("b2c", {})
                
                constraints = handoff_a2b.get("constraints", [])
                if constraints:
                    b_content = str(handoff_b2c.get("implementation_summary", "")) + \
                                str(handoff_b2c.get("self_test_results", ""))
                    
                    matched = 0
                    for c in constraints:
                        # 키워드/문장 포함 여부 확인 (소형 모델 대응)
                        if c.lower() in b_content.lower():
                            matched += 1
                        else:
                            # 핵심 키워드 매칭 시도 (단어 3개 이상 겹치면 일치로 간주)
                            c_words = set(re.findall(r'\b\w+\b', c.lower()))
                            b_words = set(re.findall(r'\b\w+\b', b_content.lower()))
                            if len(c_words & b_words) >= 3:
                                matched += 1
                    
                    loss_rate = 1.0 - (matched / len(constraints))
                    task_handoff_scores.append(loss_rate)

                # ── 2. backprop_accuracy 계산 ──
                # RejectMemo가 A를 향했을 때, 다음 턴의 A가 blueprint를 수정했는지 확인
                reject_memo = tattoo_out.get("handoff", {}).get("reject_memo")
                if reject_memo and reject_memo.get("target_phase") == "A" and i + 1 < len(cycles):
                    next_cycle = cycles[i+1]
                    next_tattoo_out = next_cycle.get("tattoo_out", {})
                    
                    prev_blueprint = handoff_a2b.get("blueprint", "")
                    next_blueprint = next_tattoo_out.get("handoff", {}).get("a2b", {}).get("blueprint", "")
                    
                    # blueprint가 변경되었으면 수정한 것으로 간주
                    modified = prev_blueprint != next_blueprint
                    task_backprop_scores.append(1.0 if modified else 0.0)

        summary["tasks"].append({
            "task_id": task_result["task_id"],
            "avg_handoff_loss": sum(task_handoff_scores) / len(task_handoff_scores) if task_handoff_scores else 0,
            "avg_backprop_accuracy": sum(task_backprop_scores) / len(task_backprop_scores) if task_backprop_scores else 0,
            "sample_cycles": len(task_handoff_scores),
        })

    all_loss = [t["avg_handoff_loss"] for t in summary["tasks"]]
    all_acc = [t["avg_backprop_accuracy"] for t in summary["tasks"]]
    
    summary["overall_avg_loss_rate"] = sum(all_loss) / len(all_loss) if all_loss else 0
    summary["overall_avg_backprop_accuracy"] = sum(all_acc) / len(all_acc) if all_acc else 0
    
    return summary


def analyze_abc_pipeline(data: dict) -> dict:
# ... (기존 코드)
    """실험 4 분석: A-B-C 파이프라인 품질."""
    import re

    summary = {"experiment": "abc_pipeline", "tasks": []}

    for entry in data["results"]:
        task_id = entry["task_id"]
        expected = entry.get("expected_answer", "")

        for trial in entry["trials"]:
            fa = trial.get("final_answer", "")
            # 간이 채점
            score = score_answer(str(fa), expected) if fa else 0.0

            # C의 phase 전이 횟수
            c_transitions = [t for t in trial.get("phase_transitions", []) if t]
            c_decided = sum(1 for d in trial.get("c_decisions", []) if d is True)

            summary["tasks"].append({
                "task_id": task_id,
                "trial": trial["trial"],
                "score": score,
                "converged": trial["final_phase"] == "CONVERGED",
                "total_cycles": trial["total_cycles"],
                "total_assertions": trial["total_assertions"],
                "c_transitions": len(c_transitions),
                "c_decided_converge": c_decided,
                "phase_transitions": c_transitions,
            })

    tasks = summary["tasks"]
    converged = [t for t in tasks if t["converged"]]
    scores = [t["score"] for t in tasks]

    summary["overall"] = {
        "total_trials": len(tasks),
        "convergence_rate": len(converged) / len(tasks) if tasks else 0,
        "avg_score": sum(scores) / len(scores) if scores else 0,
        "avg_cycles": sum(t["total_cycles"] for t in tasks) / len(tasks) if tasks else 0,
        "c_transition_rate": sum(t["c_transitions"] for t in tasks) / len(tasks) if tasks else 0,
    }

    return summary


# ── CLI ──

ANALYZERS = {
    "baseline": analyze_baseline,
    "assertion_cap": analyze_assertion_cap,
    "multiloop": analyze_multiloop,
    "error_propagation": analyze_error_propagation,
    "cross_validation": analyze_cross_validation,
    "abc_pipeline": analyze_abc_pipeline,
    "handoff_protocol": analyze_handoff_protocol,
}


def resolve_path(pattern: str) -> str:
    """글롭 패턴을 실제 파일 경로로 해석한다. 윈도우 호환."""
    import glob
    matches = sorted(glob.glob(pattern))
    if not matches:
        print(f"No files matching: {pattern}")
        sys.exit(1)
    # 가장 최신 파일 (알파벳순 마지막 = 타임스탬프 최신)
    return matches[-1]


def main():
    parser = argparse.ArgumentParser(description="제멘토 실험 결과 분석")
    parser.add_argument("result_file", help="결과 JSON 파일 경로 (글롭 패턴 가능, 예: results/exp01_*.json)")
    parser.add_argument("--markdown", action="store_true", help="마크다운 보고서 출력")
    parser.add_argument("--save-md", help="마크다운 파일로 저장할 경로")
    args = parser.parse_args()

    path = resolve_path(args.result_file)
    print(f"  → Loading: {path}")
    data = load_result(path)
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
