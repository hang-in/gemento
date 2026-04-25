"""Exp10 결과 JSON 분석 + markdown report 생성.

usage:
    python -m exp10_reproducibility_cost.analyze \\
        results/exp10_reproducibility_cost_YYYYMMDD_HHMMSS.json \\
        > results/exp10_report.md
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from exp10_reproducibility_cost.tasks import EXP10_TASK_IDS


def aggregate(trials: list[dict]) -> dict:
    """trials list → {(condition, task_id): {accuracies, tokens, costs, durations}}."""
    by_key: dict[tuple[str, str], dict] = defaultdict(lambda: {
        "accuracies": [], "input_tokens": [], "output_tokens": [],
        "cost_usds": [], "duration_mss": [], "errors": [],
    })
    for t in trials:
        key = (t["condition"], t["task_id"])
        by_key[key]["accuracies"].append(t["accuracy"])
        by_key[key]["input_tokens"].append(t.get("input_tokens", 0))
        by_key[key]["output_tokens"].append(t.get("output_tokens", 0))
        by_key[key]["cost_usds"].append(t.get("cost_usd", 0.0))
        by_key[key]["duration_mss"].append(t.get("duration_ms", 0))
        if t.get("error"):
            by_key[key]["errors"].append(t["error"])
    return dict(by_key)


def mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    if len(values) < 2:
        return (values[0], 0.0)
    return (statistics.mean(values), statistics.stdev(values))


def find_outliers(by_key: dict, threshold_sigma: float = 2.0) -> list[dict]:
    """condition × task 평균에서 ±2σ 벗어난 trial 식별."""
    outliers = []
    for (cond, task_id), data in by_key.items():
        accs = data["accuracies"]
        if len(accs) < 3:
            continue
        m, s = mean_std(accs)
        if s == 0:
            continue
        for idx, acc in enumerate(accs):
            if abs(acc - m) > threshold_sigma * s:
                outliers.append({
                    "condition": cond, "task_id": task_id,
                    "trial_idx": idx + 1, "accuracy": acc,
                    "mean": m, "std": s,
                })
    return outliers


def build_report(input_path: Path) -> str:
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    trials = data.get("trials", [])
    conditions = data.get("conditions", [])
    trials_per_condition = data.get("trials_per_condition", 0)

    by_key = aggregate(trials)
    outliers = find_outliers(by_key)

    out: list[str] = []
    out.append(f"# Exp10 Report — Reproducibility & Cost Profile\n")
    out.append(f"> Source: `{input_path.name}`")
    out.append(f"> Trials per condition×task: {trials_per_condition}")
    out.append(f"> Conditions: {', '.join(conditions)}")
    out.append(f"> Tasks: {len(EXP10_TASK_IDS)}")
    out.append(f"> Total trials: {len(trials)}\n")

    # === Q1: Reproducibility (accuracy mean ± std) ===
    out.append("## Q1. Reproducibility — accuracy mean ± std (per condition × task)\n")
    out.append("| Task | " + " | ".join(f"{c} mean ± std" for c in conditions) + " |")
    out.append("|------|" + "|".join("---" for _ in conditions) + "|")
    for tid in EXP10_TASK_IDS:
        cells = [f"`{tid}`"]
        for cond in conditions:
            cell_data = by_key.get((cond, tid), {"accuracies": []})
            m, s = mean_std(cell_data["accuracies"])
            cells.append(f"{m:.3f} ± {s:.3f}")
        out.append("| " + " | ".join(cells) + " |")
    out.append("")

    # === Q2: Cost & Time ===
    out.append("## Q2. Cost & Time (per condition, total over 9 tasks × N trials)\n")
    out.append("| Condition | total trials | total in tokens | total out tokens | total cost USD | total wallclock (s) | avg accuracy |")
    out.append("|-----------|-------------:|----------------:|-----------------:|---------------:|--------------------:|-------------:|")
    for cond in conditions:
        total_trials = sum(len(d["accuracies"]) for k, d in by_key.items() if k[0] == cond)
        total_in = sum(sum(d["input_tokens"]) for k, d in by_key.items() if k[0] == cond)
        total_out = sum(sum(d["output_tokens"]) for k, d in by_key.items() if k[0] == cond)
        total_cost = sum(sum(d["cost_usds"]) for k, d in by_key.items() if k[0] == cond)
        total_wallclock_s = sum(sum(d["duration_mss"]) for k, d in by_key.items() if k[0] == cond) / 1000.0
        all_accs = [a for k, d in by_key.items() if k[0] == cond for a in d["accuracies"]]
        avg_acc = statistics.mean(all_accs) if all_accs else 0.0
        out.append(
            f"| `{cond}` | {total_trials} | {total_in:,} | {total_out:,} "
            f"| ${total_cost:.4f} | {total_wallclock_s:.1f} | {avg_acc:.3f} |"
        )
    out.append("")

    # === Outliers ===
    out.append(f"## Outlier trials (|x - μ| > 2σ): {len(outliers)}\n")
    if outliers:
        out.append("| Condition | Task | Trial | accuracy | mean | std |")
        out.append("|-----------|------|-------|---------:|-----:|----:|")
        for o in outliers[:30]:
            out.append(
                f"| `{o['condition']}` | `{o['task_id']}` | {o['trial_idx']} "
                f"| {o['accuracy']:.3f} | {o['mean']:.3f} | {o['std']:.3f} |"
            )
        if len(outliers) > 30:
            out.append(f"| ... ({len(outliers) - 30} more outliers omitted) | | | | | |")
    else:
        out.append("(없음 — 모든 trial 이 평균에서 2σ 이내)")
    out.append("")

    # === Errors ===
    error_trials = [t for t in trials if t.get("error")]
    out.append(f"## Errors: {len(error_trials)} trial(s) with non-null error\n")
    if error_trials:
        # 에러 메시지별 카운트
        from collections import Counter
        msg_counts = Counter(t["error"][:100] for t in error_trials)
        out.append("| Error (first 100 chars) | Count |")
        out.append("|-------------------------|------:|")
        for msg, cnt in msg_counts.most_common(10):
            out.append(f"| `{msg}` | {cnt} |")
    else:
        out.append("(없음)")
    out.append("")

    # === Externalization 비용 효율 (gemma_8loop vs gemini_flash_1call) ===
    out.append("## Externalization 비용 효율 — gemma_8loop vs gemini_flash_1call\n")
    g8 = [a for k, d in by_key.items() if k[0] == "gemma_8loop" for a in d["accuracies"]]
    gf = [a for k, d in by_key.items() if k[0] == "gemini_flash_1call" for a in d["accuracies"]]
    g8_cost = sum(sum(d["cost_usds"]) for k, d in by_key.items() if k[0] == "gemma_8loop")
    gf_cost = sum(sum(d["cost_usds"]) for k, d in by_key.items() if k[0] == "gemini_flash_1call")
    g8_time = sum(sum(d["duration_mss"]) for k, d in by_key.items() if k[0] == "gemma_8loop") / 1000.0
    gf_time = sum(sum(d["duration_mss"]) for k, d in by_key.items() if k[0] == "gemini_flash_1call") / 1000.0
    g8_acc = statistics.mean(g8) if g8 else 0.0
    gf_acc = statistics.mean(gf) if gf else 0.0
    out.append(f"- gemma_8loop   : accuracy {g8_acc:.3f}, cost ${g8_cost:.4f}, wallclock {g8_time:.1f}s")
    out.append(f"- gemini_flash  : accuracy {gf_acc:.3f}, cost ${gf_cost:.4f}, wallclock {gf_time:.1f}s")
    if g8_acc > 0 and gf_acc > 0:
        delta_acc = g8_acc - gf_acc
        out.append(f"- accuracy delta (gemma_8loop - gemini_flash): {delta_acc:+.3f}")
    if gf_cost > 0:
        cost_ratio = g8_cost / gf_cost if gf_cost else float("inf")
        out.append(f"- cost ratio (gemma_8loop / gemini_flash): {cost_ratio:.2f}x")
    out.append("")

    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Exp10 결과 JSON → markdown report")
    parser.add_argument("input", type=Path, help="exp10_reproducibility_cost_*.json 결과 파일")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="기본: stdout. 지정 시 파일에 저장")
    args = parser.parse_args()

    text = build_report(args.input)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"  → Report saved: {args.output}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
