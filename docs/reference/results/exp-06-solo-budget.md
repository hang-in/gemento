---
type: result
status: done
updated_at: 2026-05-02
experiment: 실험 6 — Solo vs ABC 시너지 측정
revision: 2026-05-02 (Stage 2C — H4 재검증 결과 §6 추가)
---

# 실험 6: Solo-Budget 결과 보고서

## 1. 개요
"A-B-C 역할 분리(E4B×3)가 단일 모델의 단순 반복보다 우월한가?"라는 질문에 답하기 위해, 동일한 컴퓨팅 예산 하에서 단일 에이전트의 성능을 측정한 대조 실험입니다.

## 2. 원본 비교 (2026-04-15)

| 지표 | 실험 5b (ABC 협력) | 실험 6 (Solo 반복) | 차이 |
|------|-------------------|-------------------|------|
| **평균 정확도** | **88.9%** | **66.3%** | **-22.6%p** |
| 수렴률 | 100% | 100% | 동일 |
| 평균 호출 수 | 21.6회 | 4.5회 | -17.1회 |

> ⚠ 원본 비교 전체(ABC 88.9% vs Solo 66.3%, +22.6%p)는 동일 채점 기준으로 재현 불가.
> 단, ABC 88.9% 단일 수치는 trial-level `v1 > 0.2` (40/45) 또는 task-level `v2 mean ≥ 0.75` (8/9)에서 부분 재현됨 (정확한 원본 기준 불명).
> 아래 §5 정합 비교 참조.

## 3. 분석 결과 (원본)
1. **역할 분리 구조의 효과**: Solo 에이전트는 외부의 객관적 비판이 없기 때문에, 평균 4.5루프 만에 빠르게 수렴합니다. ABC는 21.6회 호출로 비판·판단 루프를 수행합니다.
2. **조기 수렴(Early Convergence) 패턴**: Solo는 자신의 논리적 오류를 인지하지 못하고 조기 종료하는 경향이 있습니다.
3. **구조적 차이**: ABC는 A→B→C 비판 루프 구조를 가지며, Solo는 단일 에이전트 반복입니다.

## 4. 다음 단계 (원본)
- '판정자(C)' 역할을 더 강력한 모델로 교체하는 **혼합 지능(Mixed Intelligence)** 실험 후보.

## 5. 정합 비교 (2026-04-29 reconciliation)

기존 비교의 "Solo 표본 9"는 사실 오류 — Solo = 9 task × 5 trial = **45 trial** (ABC와 동일).
아래는 동일 채점법 × 동일 표본(45 vs 45) 비교.

| 채점법 | Solo (45 trial) | ABC (45 trial) | Δ (Solo−ABC) |
|--------|-----------------|----------------|-------------|
| v1 (partial score) | 0.663 | 0.649 | +0.015 |
| v2 (keyword group) | 0.967 | 0.900 | +0.067 |
| v3 (neg+keyword) | 0.967 | 0.900 | +0.067 |

95% CI (bootstrap N=10,000): v1 Solo [0.573, 0.748] vs ABC [0.553, 0.737] — 중첩, 차이 통계적으로 유의미하지 않을 수 있음.

Per-task v2 승패: **ABC 1승** (logic-01), **Solo 3승** (logic-02, synthesis-01, synthesis-02), **무승부 5**.

### "88.9%" 재현 시도
- trial-level: `v1 > 0.2` → ABC 40/45 = 88.9% 재현 가능 (Solo 같은 기준 41/45 = 91.1%)
- task-level: `v2 mean ≥ 0.75` → ABC 8/9 = 88.9% (logic-02만 탈락, v2 mean=0.500)
- 원본 비교의 정확한 채점 기준 불명 — disclosure에 그침

### H4 verdict (이 task set 한정)
재현 가능한 모든 채점법(v1/v2/v3)에서 Solo ≥ ABC.
Solo 조기 수렴(avg 4.5 loops) vs ABC 구조적 비판 루프(21.6 calls) 차이는 실재하나,
이 9-task set에서는 정확도 Δ로 나타나지 않음.

**→ H4: ⚠ 미결 (Inconclusive) — 확대 task set 재검증 필요** (해소 시점: 2026-05-02 Stage 2C, §6 참조)

분석 스크립트: `experiments/exp06_solo_budget/analyze_reconciliation.py`
JSON 결과: `experiments/exp06_solo_budget/results/exp06_reconciliation_<timestamp>.json`

## 6. H4 재검증 (2026-05-02, Stage 2C)

확대 task set (12 → 15) + 3 condition (Solo-1call / Solo-budget / ABC) ablation 재검증.

| 비교 | Δ acc |
|------|------:|
| Solo-budget − Solo-1call (다단계 효과) | +0.0700 |
| **ABC − Solo-budget (역할 분리 단독 효과)** | **+0.0444** |
| ABC − Solo-1call (합산) | +0.1144 |

| condition | n | mean_acc | median per-task |
|-----------|---|---------:|----------------:|
| Solo-1call | 75 | 0.6444 | 0.667 |
| Solo-budget | 75 | 0.7144 | 0.867 |
| ABC | 75 | **0.7589** | **1.000** |

**카테고리별** (Δ abc − sb):
- math: +0.000 (saturation)
- logic: −0.025 (logic-04 negative_patterns 효과)
- **synthesis: +0.140** (H4 회복 핵심)
- planning (신규 2): +0.033

**통계 검정** (n=15 task paired): Wilcoxon p=0.16, t-test p=0.10 (NOT SIGNIFICANT, 검정력 한계). Cohen's d = 0.449 (medium). Bootstrap 95% CI Δ(abc−sb): [−0.0044, +0.0911].

**H4 verdict**: ⚠ **조건부 채택 (synthesis 카테고리 한정)**.
- 9-task subset (본 §5) 의 Solo 우위 → 15-task 확대 시 ABC +0.044 우위로 **방향 반전**
- 추가 task (특히 synthesis) 가 H4 회복의 핵심
- 통계적 유의성 미달 (검정력 한계), 단 medium effect size (d=0.449)

상세: `docs/reference/h4-recheck-analysis-2026-05-02.md`.
plan: `exp06-h4-recheck-expanded-taskset-pre-exp11`.
JSON 결과: `experiments/exp_h4_recheck/results/h4_recheck_{solo_1call,solo_budget,abc}.json`.

**한계 / 후속**: ABC 의 assertion turnover 측정 불가 (`run.py:115` 의 tattoo_history 저장 결함). Stage 4 Exp11 plan 시 보강.
