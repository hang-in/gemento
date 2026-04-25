---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: exp10-reproducibility-cost-profile
parallel_group: B
depends_on: [03]
---

# Task 04 — 채점·집계 스크립트 (analyze.py)

## Changed files

- `experiments/exp10_reproducibility_cost/analyze.py` — **신규**. 결과 JSON 분석 → markdown report 변환

신규 외 다른 파일 수정 금지.

## Change description

### 배경

task-03 의 `run.py` 가 540 trial 결과를 JSON 으로 저장. 본 task 의 `analyze.py` 가 그 JSON 을 읽어 사람이 읽을 수 있는 markdown 리포트로 변환한다. 핵심 출력:
- (1) condition × task accuracy mean ± std (Q1: 재현성)
- (2) condition 별 total tokens / cost USD / wallclock (Q2: 비용)
- (3) outlier trial (정답률이 condition 평균에서 ±2σ 벗어난 trial)
- (4) Externalization 효과 데이터 (Gemma_8loop 의 비용 효율)

본 task 는 LLM 호출 0. 단지 통계·텍스트 처리.

### Step 1 — `experiments/exp10_reproducibility_cost/analyze.py` 작성

```python
"""Exp10 결과 JSON 분석 + markdown report 생성.

usage:
    python -m exp10_reproducibility_cost.analyze \\
        results/exp10_reproducibility_cost_YYYYMMDD_HHMMSS.json \\
        > results/exp10_report.md
"""
from __future__ import annotations

import argparse
import json
import math
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
            data = by_key.get((cond, tid), {"accuracies": []})
            m, s = mean_std(data["accuracies"])
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
```

### Step 2 — Verification 패턴 (LLM 호출 0)

본 task 는 dummy result JSON 을 만들어 analyze.py 에 입력하고 expected output 을 검증.

dummy fixture (테스트 안에서 생성):
```json
{
  "experiment": "reproducibility_cost",
  "model": "gemma4-e4b",
  "trials_per_condition": 2,
  "conditions": ["gemma_1loop", "gemini_flash_1call"],
  "task_ids": ["math-01"],
  "trials": [
    {"condition": "gemma_1loop", "task_id": "math-01", "trial": 1, "accuracy": 0.5, "input_tokens": 100, "output_tokens": 50, "cost_usd": 0.0, "duration_ms": 1000, "error": null, "final_answer": "x"},
    {"condition": "gemma_1loop", "task_id": "math-01", "trial": 2, "accuracy": 1.0, "input_tokens": 100, "output_tokens": 50, "cost_usd": 0.0, "duration_ms": 1000, "error": null, "final_answer": "x"},
    {"condition": "gemini_flash_1call", "task_id": "math-01", "trial": 1, "accuracy": 1.0, "input_tokens": 200, "output_tokens": 80, "cost_usd": 0.0001, "duration_ms": 500, "error": null, "final_answer": "x"},
    {"condition": "gemini_flash_1call", "task_id": "math-01", "trial": 2, "accuracy": 1.0, "input_tokens": 200, "output_tokens": 80, "cost_usd": 0.0001, "duration_ms": 500, "error": null, "final_answer": "x"}
  ]
}
```

기대 결과:
- markdown 출력 헤더 `# Exp10 Report` 시작
- `gemma_1loop`: accuracy mean=0.75, std=0.354
- `gemini_flash_1call`: accuracy mean=1.0, std=0.0
- total cost 표 포함

## Dependencies

- **Task 03 완료** — `run.py` 의 결과 JSON schema 와 호환되는 분석 코드 작성.
- 외부 패키지: `statistics` (stdlib), `pathlib` (stdlib), `argparse` (stdlib). 추가 의존성 없음.

## Verification

```bash
# 1. 신규 파일 존재
test -f /Users/d9ng/privateProject/gemento/experiments/exp10_reproducibility_cost/analyze.py && \
echo "OK analyze.py exists"

# 2. import smoke
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.analyze import build_report, aggregate, mean_std, find_outliers
assert callable(build_report)
print('OK analyze.py imports')
"

# 3. dummy JSON → markdown 검증 (LLM 호출 0)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import json
import tempfile
from pathlib import Path
from exp10_reproducibility_cost.analyze import build_report

dummy = {
    'experiment': 'reproducibility_cost',
    'model': 'gemma4-e4b',
    'trials_per_condition': 2,
    'conditions': ['gemma_1loop', 'gemini_flash_1call'],
    'task_ids': ['math-01'],
    'trials': [
        {'condition': 'gemma_1loop', 'task_id': 'math-01', 'trial': 1, 'accuracy': 0.5, 'input_tokens': 100, 'output_tokens': 50, 'cost_usd': 0.0, 'duration_ms': 1000, 'error': None, 'final_answer': 'x'},
        {'condition': 'gemma_1loop', 'task_id': 'math-01', 'trial': 2, 'accuracy': 1.0, 'input_tokens': 100, 'output_tokens': 50, 'cost_usd': 0.0, 'duration_ms': 1000, 'error': None, 'final_answer': 'x'},
        {'condition': 'gemini_flash_1call', 'task_id': 'math-01', 'trial': 1, 'accuracy': 1.0, 'input_tokens': 200, 'output_tokens': 80, 'cost_usd': 0.0001, 'duration_ms': 500, 'error': None, 'final_answer': 'x'},
        {'condition': 'gemini_flash_1call', 'task_id': 'math-01', 'trial': 2, 'accuracy': 1.0, 'input_tokens': 200, 'output_tokens': 80, 'cost_usd': 0.0001, 'duration_ms': 500, 'error': None, 'final_answer': 'x'},
    ],
}
with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as f:
    json.dump(dummy, f)
    p = Path(f.name)
report = build_report(p)
assert '# Exp10 Report' in report
assert 'gemma_1loop' in report
assert '0.750 ± 0.354' in report  # math-01 gemma_1loop
assert '1.000 ± 0.000' in report  # math-01 gemini_flash
assert '\$0.0002' in report or '0.0002' in report  # total cost gemini_flash
print('OK dummy report generation')
p.unlink()
"

# 4. CLI --help 동작
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m exp10_reproducibility_cost.analyze --help 2>&1 | grep -q "input" && echo "OK --help works"

# 5. find_outliers — 빈 데이터·작은 데이터 fallback
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.analyze import find_outliers, aggregate
# 빈 trials → 빈 outliers
assert find_outliers({}) == []
# 1 trial → outlier 검출 안 함 (len < 3)
data = {('gemma_1loop', 'math-01'): {'accuracies': [0.5], 'input_tokens': [], 'output_tokens': [], 'cost_usds': [], 'duration_mss': [], 'errors': []}}
assert find_outliers(data) == []
print('OK outlier edge cases')
"

# 6. mean_std edge cases
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.analyze import mean_std
assert mean_std([]) == (0.0, 0.0)
assert mean_std([0.5]) == (0.5, 0.0)
m, s = mean_std([0.0, 1.0])
assert m == 0.5 and abs(s - 0.7071) < 0.01
print('OK mean_std edge cases')
"

# 7. 다른 파일 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only experiments/ | grep -vE "^experiments/exp10_reproducibility_cost/analyze\.py$" | grep -v "^$" || echo "OK no extra changes"
```

## Risks

- **markdown 셀 escape**: dollar sign 등이 markdown viewer 에서 다르게 렌더 가능. 단순 backtick wrap 으로 처리 — 큰 문제 없음.
- **statistics.stdev**: 표본 ≥ 2 필요. 1 개일 때 fallback (mean_std 에서 처리).
- **outlier threshold 임의성**: ±2σ 가 표준이지만 보수적. ±3σ 또는 IQR 기반 옵션 — 본 task 범위 밖, 별도 plan.
- **memory**: 540 trial × ~500 byte = 0.3MB. 무시 가능.
- **trial schema 변경**: task-03 의 trial dict 키가 바뀌면 analyze.py 깨짐. 본 task 의 verification (dummy JSON) 이 schema 일치 여부 확인.
- **Report 의 한국어/영어 혼용**: 표 헤더는 영어, 설명은 한국어. 의도된 디자인 (코드와 학술 용어는 영어).

## Scope boundary

**Task 04 에서 절대 수정 금지**:

- `experiments/exp10_reproducibility_cost/run.py`, `tasks.py`, `__init__.py` — task-02·03 영역.
- `experiments/run_experiment.py` — task-05 영역.
- `experiments/_external/` — task-01 영역.
- `experiments/orchestrator.py`, `config.py`, `measure.py`, `schema.py`.
- `experiments/tests/test_static.py` — task-05 영역.
- `experiments/INDEX.md` — task-05 영역.
- 다른 expXX/ 디렉토리.

**허용 범위**:

- `experiments/exp10_reproducibility_cost/analyze.py` 신규 작성.
