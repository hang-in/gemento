---
type: result
status: done
updated_at: 2026-04-29
experiment: 실험 6 — Solo vs ABC 시너지 측정
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

**→ H4: ⚠ 미결 (Inconclusive) — 확대 task set 재검증 필요**

분석 스크립트: `experiments/exp06_solo_budget/analyze_reconciliation.py`
JSON 결과: `experiments/exp06_solo_budget/results/exp06_reconciliation_<timestamp>.json`
