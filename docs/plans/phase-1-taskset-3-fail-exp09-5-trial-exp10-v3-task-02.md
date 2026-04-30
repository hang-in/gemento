---
type: plan-task
status: done
updated_at: 2026-04-30
parent_plan: phase-1-taskset-3-fail-exp09-5-trial-exp10-v3
parallel_group: B
depends_on: []
conclusion: "(c) 시스템 결함 단독 — trial 4-5 가 WinError 10061 인프라 결함으로 무효"
---

# Task 02 — Exp09 5-trial 점수 하락 원인 분석

## Changed files

- `experiments/exp09_longctx/analyze_5trial_drop.py` — **신규**. 또는 기존 `analyze_stats.py` 에 `--trial-comparison` 옵션 추가. trial 1-3 vs 4-5 답변 / duration / 채점 분포 비교.
- `docs/reference/exp09-5trial-drop-analysis-2026-04-30.md` — **신규**. 분석 결과 보고서 + 원인 후보 결정.

신규 파일 2.

## Change description

### 배경

Phase 1 산출물 (commit `3ed255a`) 에서 Exp09 의 3-trial → 5-trial 시 양 arm 동시 점수 하락 확인:

|  | abc | rag | Δ(abc−rag) |
|--|-----|-----|------------|
| 3-trial | 0.883 | 0.850 | +0.033 |
| 5-trial | 0.530 | 0.510 | +0.020 |
| 변화 | **−0.353** | **−0.340** | −0.013 |

→ 추가 trial (4, 5) 에서 양 arm 동시 큰 하락. abc-rag 상대 차이 (Δ) 는 비슷하게 유지 → H9b verdict 는 `Inconclusive` 로 강등 (이미 commit `3ed255a` 에 반영). 그러나 **하락 자체의 원인** 은 미해결.

### 원인 후보 (분석 대상)

| # | 후보 | 검증 방법 |
|---|------|-----------|
| (a) | 환경 차이 (sampling seed / model weight / inference engine 변경) | 결과 JSON 의 sampling_params / model 메타 비교 |
| (b) | 모델 비결정성 (같은 sampling 에서도 trial 별 답변 분산) | trial 별 답변 텍스트 비교 + 답변 길이 / duration 분포 |
| (c) | 시스템 결함 (분석 스크립트 버그, run 무효 trial 포함) | 5-trial 결과 JSON 의 trial 4/5 의 raw 응답 + final_answer 정합성 |
| (d) | 채점 변동 (같은 답변에 다른 점수) | 동일 task 의 동일 답변 trial 의 score 비교 |

### Step 1 — 분석 스크립트 신규

`experiments/exp09_longctx/analyze_5trial_drop.py` 신규:

```python
"""Exp09 5-trial 점수 하락 원인 분석.

3-trial 결과 (exp09_longctx_20260425_144412.json) vs 5-trial 결과
(exp09_longctx_5trial_20260430_111330.json) 의 trial 1-3 vs 4-5 답변 / duration /
채점 분포를 비교하여 하락 원인을 식별.
"""
from __future__ import annotations
import argparse, json, sys, statistics
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


DEFAULT_3TRIAL = Path('experiments/exp09_longctx/results/exp09_longctx_20260425_144412.json')
DEFAULT_5TRIAL = Path('experiments/exp09_longctx/results/exp09_longctx_5trial_20260430_111330.json')


def load_arms(path: Path) -> dict:
    """결과 JSON 의 results_by_arm 반환."""
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    return d.get('results_by_arm') or {}


def trial_breakdown(path: Path, arm: str) -> dict:
    """arm 의 task 별 trial answer / duration / score 추출."""
    arms = load_arms(path)
    if arm not in arms:
        return {}
    out = {}
    for r in arms[arm]:
        task_id = r.get('task_id')
        trials = r.get('trials') or []
        out[task_id] = [
            {
                'trial_idx': i,
                'final_answer': str(t.get('final_answer') or '')[:200],
                'duration_ms': t.get('duration_ms'),
                'accuracy': t.get('accuracy'),
                'error': t.get('error'),
            }
            for i, t in enumerate(trials)
        ]
    return out


def compare(path_3: Path, path_5: Path, arm: str) -> dict:
    """trial 1-3 vs 4-5 비교 metric 산출."""
    breakdown_5 = trial_breakdown(path_5, arm)
    summary = defaultdict(list)
    for task_id, trials in breakdown_5.items():
        if len(trials) < 5:
            continue
        early = trials[:3]
        late = trials[3:5]
        early_acc = [t['accuracy'] or 0 for t in early]
        late_acc = [t['accuracy'] or 0 for t in late]
        summary['early_acc'].extend(early_acc)
        summary['late_acc'].extend(late_acc)
        summary['early_dur'].extend([t['duration_ms'] for t in early if t['duration_ms']])
        summary['late_dur'].extend([t['duration_ms'] for t in late if t['duration_ms']])
        # 답변 동일성 (early vs late)
        early_answers = {t['final_answer'] for t in early}
        late_answers = {t['final_answer'] for t in late}
        summary['unique_answers_early'].append(len(early_answers))
        summary['unique_answers_late'].append(len(late_answers))
        summary['answer_overlap'].append(len(early_answers & late_answers))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description='Exp09 5-trial drop analysis')
    parser.add_argument('--3trial', dest='three', default=str(DEFAULT_3TRIAL))
    parser.add_argument('--5trial', dest='five', default=str(DEFAULT_5TRIAL))
    parser.add_argument('--arm', default='abc_tattoo')
    args = parser.parse_args()
    summary = compare(Path(args.three), Path(args.five), args.arm)
    print(f'=== arm: {args.arm} ===')
    for k, v in summary.items():
        if v and isinstance(v[0], (int, float)):
            print(f'  {k:25} mean={statistics.mean(v):.3f}  stdev={statistics.stdev(v) if len(v)>1 else 0:.3f}  n={len(v)}')
        else:
            print(f'  {k:25} {v}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

### Step 2 — 사용자 직접 실행 (메모리 정책)

```bash
.venv/bin/python -m experiments.exp09_longctx.analyze_5trial_drop --arm abc_tattoo
.venv/bin/python -m experiments.exp09_longctx.analyze_5trial_drop --arm rag_baseline
```

각 arm 의 trial 1-3 vs 4-5 의 mean accuracy / stdev / 답변 unique 수 / answer overlap 출력.

### Step 3 — `docs/reference/exp09-5trial-drop-analysis-2026-04-30.md` 보고서

분석 결과 기반:

```markdown
---
type: reference
status: done
updated_at: 2026-04-30
---

# Exp09 5-trial 점수 하락 원인 분석

## 결과 요약

| arm | early_acc (1-3) | late_acc (4-5) | Δ |
|-----|----------------:|---------------:|--:|
| abc_tattoo | <FILL> | <FILL> | <FILL> |
| rag_baseline | <FILL> | <FILL> | <FILL> |

## 원인 후보 분석

(a) 환경 차이: <FILL — sampling_params / model 메타 비교 결과>
(b) 모델 비결정성: <FILL — answer overlap / unique 수>
(c) 시스템 결함: <FILL — error / null 답변 분포>
(d) 채점 변동: <FILL — 동일 답변 score 분산>

## 결정 — 가장 가능성 높은 원인

<FILL — 후보 (a)/(b)/(c)/(d) 중 결정 + 근거>

## 함의

<FILL — H9b verdict 영향 + run_append_trials 절차 보강 후보>
```

`<FILL>` 자리는 Step 2 실행 결과로 대체.

## Dependencies

- 패키지: 표준 `json`, `argparse`, `statistics`, `collections`. 신규 의존성 0.
- 입력: `exp09_longctx_20260425_144412.json` (3-trial 원본), `exp09_longctx_5trial_20260430_111330.json` (5-trial)
- 다른 subtask: 없음 (parallel_group B, 독립).

## Verification

```bash
# 1) 정적 import + 도움말
.venv/bin/python -m experiments.exp09_longctx.analyze_5trial_drop --help
# 기대: usage 출력, --3trial / --5trial / --arm 옵션 표시

# 2) 두 arm 모두 실행 (사용자 직접)
.venv/bin/python -m experiments.exp09_longctx.analyze_5trial_drop --arm abc_tattoo
.venv/bin/python -m experiments.exp09_longctx.analyze_5trial_drop --arm rag_baseline
# 기대: early_acc / late_acc / stdev / answer overlap 출력

# 3) 보고서 작성 + placeholder 0
grep -E '<FILL[^>]*>' docs/reference/exp09-5trial-drop-analysis-2026-04-30.md | wc -l
# 기대: 0
```

3 명령 모두 정상.

## Risks

- **5-trial JSON schema 변동**: `results_by_arm` 가 아니라 다른 키일 가능성 — Step 1 의 `load_arms` 가 실패 시 schema 정찰 후 보강.
- **trial 4/5 의 무효 데이터**: 일부 task 가 trial 4/5 가 비어있으면 `if len(trials) < 5: continue` 로 제외. 실제 5-trial 카운트 < 10 task 가능.
- **분석 결과의 결정성**: 4 후보 중 어느 것도 단독 원인이 아닐 가능성 — 보고서에 "혼합 원인" 명시.
- **사용자 직접 실행 의존**: 본 task 는 분석 스크립트 작성까지 (Architect/Developer). 실제 실행 + 결과 해석은 사용자 + 후속 보고.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/exp09_longctx/run.py` / `run_append_trials.py` / `analyze_stats.py` — 기존 인프라 변경 0
- 모든 결과 JSON (3-trial / 5-trial / Exp10 / Exp06 reconciliation 등) — read-only
- `experiments/tasks/*` — Task 01 영역
- `experiments/exp10_reproducibility_cost/` — Task 03 영역
- `docs/reference/results/exp-09-longctx.md` — Task 04 영역 (본 task 는 신규 분석 보고서만)
- README / researchNotebook — Task 04 영역
