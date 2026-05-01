---
type: reference
status: done
updated_at: 2026-05-02
canonical: true
---

# Exp06 H4 재검증 분석 (확대 task set, Stage 2C)

**Plan**: `exp06-h4-recheck-expanded-taskset-pre-exp11`
**실행일**: 2026-05-01 ~ 2026-05-02
**조건**: Solo-1call / Solo-budget / ABC × 15 task × 5 trial = **225 trial**
**모델**: Gemma 4 E4B (LM Studio Q8_0, `http://192.168.1.179:1234`)
**채점**: `score_answer_v3` (negative_patterns 적용)

## 1. condition aggregate

| condition | n | mean_acc | median (per-task) | err | avg_cycles | avg_dur |
|-----------|---|---------:|------------------:|----:|-----------:|--------:|
| solo_1call | 75 | 0.6444 | 0.6667 | 0 | 1.0 | 28.7s |
| solo_budget | 75 | 0.7144 | 0.8667 | 10 | 4.9 | 150.9s |
| **abc** | 75 | **0.7589** | **1.0000** | 9 | 7.2 | 441.6s |

err = `error is not None` 의 trial. solo_budget / abc 의 9~10 err 는 `OTHER` 분류 (model API 4xx/5xx 또는 generation timeout 류, fatal connection_error 부재 — Stage 2A healthcheck 발동 0).

## 2. Ablation (n=15 task paired)

| 비교 | Δ acc | 의미 |
|------|------:|------|
| Solo-budget − Solo-1call | **+0.0700** | 다단계 효과 (H1 재확인) |
| **ABC − Solo-budget** | **+0.0444** | **역할 분리 단독 효과 (H4 본 가설)** |
| ABC − Solo-1call | +0.1144 | 합산 (다단계 + 역할 분리) |

다단계 효과 (+0.07) 가 역할 분리 단독 (+0.044) 보다 약간 큼. 단 ABC 는 두 효과 합산으로 +0.114 — 본 plan 의 직접 증거.

## 3. 카테고리별 break-down

| category | n_tasks | solo_1call | solo_budget | abc | **Δ(abc−sb)** | 해석 |
|----------|--------:|-----------:|------------:|----:|--------------:|------|
| math | 4 | 0.7833 | 0.7500 | 0.7500 | +0.0000 | math-01/02/03 saturation, math-04 = 0 모든 condition (use_tools=False, Tool 미주입) |
| logic | 4 | 0.7250 | 0.6000 | **0.5750** | **−0.0250** | logic-01/03 saturation, logic-04 ABC −0.20 (Stage 2A v3 negative_patterns 효과 — false positive 차단) |
| **synthesis** | 5 | 0.4533 | 0.6767 | **0.8167** | **+0.1400** | **H4 회복의 핵심**. synthesis-01/02/03 모두 ABC ≥ +0.13 |
| planning | 2 | 0.6833 | 0.9667 | 1.0000 | +0.0333 | 신규 카테고리 (Stage 2C). planning-01 saturation, planning-02 ABC +0.067 |

→ **synthesis 카테고리 단독으로 H4 회복** (다관점 종합에서 Role 분리 효과 명료). 다른 카테고리는 saturation 또는 logic-04 의 negative_patterns 영향.

## 4. Per-task break-down

| task | category | difficulty | solo_1call | solo_budget | abc | Δ(abc−sb) |
|------|----------|-----------|-----------:|------------:|----:|----------:|
| math-01 | math | medium | 1.000 | 1.000 | 1.000 | +0.000 |
| math-02 | math | hard | 1.000 | 1.000 | 1.000 | +0.000 |
| math-03 | math | hard | 1.000 | 1.000 | 1.000 | +0.000 |
| math-04 | math | very_hard | 0.133 | 0.000 | 0.000 | +0.000 |
| logic-01 | logic | medium | 1.000 | 1.000 | 1.000 | +0.000 |
| logic-02 | logic | hard | 0.300 | 0.200 | 0.300 | +0.100 |
| logic-03 | logic | hard | 1.000 | 1.000 | 1.000 | +0.000 |
| **logic-04** | logic | very_hard | 0.600 | 0.200 | **0.000** | **−0.200** |
| synthesis-01 | information_synthesis | medium | 0.000 | 0.400 | 0.600 | +0.200 |
| synthesis-02 | information_synthesis | hard | 1.000 | 0.800 | 1.000 | +0.200 |
| synthesis-03 | information_synthesis | very_hard | 0.333 | 0.867 | 1.000 | +0.133 |
| synthesis-04 | information_synthesis | very_hard | 0.333 | 0.867 | 0.933 | +0.067 |
| **synthesis-05** | information_synthesis | hard | 0.600 | 0.450 | 0.550 | +0.100 |
| **planning-01** | planning | medium | 0.700 | 1.000 | 1.000 | +0.000 |
| **planning-02** | planning | very_hard | 0.667 | 0.933 | 1.000 | +0.067 |

⭐ 신규 3 task (Stage 2C 추가): planning-01, planning-02, synthesis-05.
**logic-04 ABC −0.20**: ABC 가 "no unique solution" / "contradiction" 으로 결론 내는 경향 → v3 negative_patterns 가 false positive 차단 → strict 0/20. Solo-1call 은 'Casey' 등 개인명 단순 substring 으로 false positive (0.6) 잔존.

## 5. 통계 검정 (paired, n=15)

| 검정 | 통계량 | p-value | 판정 |
|------|--------|--------:|------|
| Wilcoxon signed-rank (abc vs sb) | W=8.00 | 0.1609 | NOT SIGNIFICANT |
| Paired t-test (abc vs sb) | t=1.740 | 0.1038 | NOT SIGNIFICANT |
| Wilcoxon (sb vs s1) | W=17.00 | 0.2842 | NOT SIGNIFICANT |
| **Cohen's d (paired, abc vs sb)** | **d = 0.449** | — | **medium effect** |
| Bootstrap 95% CI Δ(abc−sb), n=10000 | [−0.0044, +0.0911] | — | **0 거의 포함 (임계)** |

**해석**:
- 통계 비유의 (p > 0.05) — n=15 task 검정력 한계 (Exp09 H9b 와 동일 패턴)
- Cohen's d = 0.449 — medium effect size (Cohen 기준 0.5 가 medium 경계)
- Bootstrap CI 의 lower bound −0.004 — 0 을 거의 포함 (단 0.95 + 표본 한계)
- **격차 자체는 medium effect, 단 검정력으로는 부족**

## 6. error mode 분포 (FailureLabel, Stage 2B)

| condition | NONE | FORMAT_ERROR | WRONG_SYNTHESIS | NULL_ANSWER | OTHER | CONNECTION_ERROR | TIMEOUT |
|-----------|----:|-------------:|----------------:|------------:|------:|-----------------:|--------:|
| solo_1call | 51 | 5 | 14 | 5 | 0 | 0 | 0 |
| solo_budget | 56 | 1 | 8 | 0 | 10 | 0 | 0 |
| abc | 59 | 2 | 5 | 0 | 9 | 0 | 0 |

- ABC 가 NONE 최다 (59/75 = 78.7%) — 정답 안정성 우위
- ABC 의 WRONG_SYNTHESIS 5 / Solo-1call 14 — Role 분리가 의미 오류 줄임 (단 OTHER 9 잔존)
- **CONNECTION_ERROR 0 모든 condition** — Stage 2A healthcheck/abort 가 직전 사고 (Exp09 5-trial WinError 10061) 재발 차단 ✓

## 7. assertion turnover — 분석 결함 disclosure

| condition | added | modified | final_count | n |
|-----------|------:|---------:|------------:|---:|
| solo_1call | 0.00 | 0.00 | 0.00 | 75 |
| solo_budget | 4.59 | 0.19 | 4.59 | 75 |
| abc | 0.00 | 0.00 | 0.00 | 75 |

⚠ **abc 의 turnover 측정 불가**: `experiments/exp_h4_recheck/run.py:115` 의 `tattoo_history = [tattoo.to_dict()] if tattoo else None` — ABC 의 tattoo_history 가 final tattoo 1 개만. cycle-by-cycle history 미저장.

→ Plan task-05 의 verdict 결정 트리 중 "turnover_modified(abc) ≥ 1.5 × solo_budget" 조건 측정 불가. 정확도 + median + 카테고리 break-down 만으로 verdict.

**후속 plan 후보**: ABC 의 cycle-by-cycle tattoo history 저장 + turnover 재분석 — Stage 4 Exp11 plan 작성 시 보강.

## 8. H4 verdict — **⚠ 조건부 채택 (synthesis 카테고리 한정)**

verdict 결정 트리 적용 (Plan task-05 Step 3):

```
abc - solo_budget = +0.0444 < +0.05 → 정확도 격차 작음
turnover_modified 측정 불가 → 정확도 + 카테고리로 결정
synthesis 카테고리 +0.1400 (명료) + median per-task +0.1333 → 부분 채택
통계 비유의 (p=0.16) + Cohen d=0.449 medium → 조건부
```

**최종 verdict**:

```
H4 (Role 외부화 시너지 — A-B-C 역할 분리 > 단일 에이전트 반복):
⚠ 조건부 채택 (synthesis 카테고리 한정)
```

세부:
- ✅ synthesis (5 task): ABC > Solo-budget +0.140 (명료)
- ⚠ planning (2 task): ABC > Solo-budget +0.033 (작음, sample 한계)
- ➖ math (4 task): saturation, 격차 0
- ⚠ logic (4 task): ABC < Solo-budget −0.025 (logic-04 negative_patterns 효과)

## 9. 비교 — Exp06 정합 비교 (2026-04-29) 와 본 결과

| 메트릭 | Exp06 (9 task × 5 trial, 2026-04-29) | 본 결과 (15 task × 5 trial, 2026-05-02) | 변화 |
|--------|-------------------------------------:|----------------------------------------:|------|
| Solo (loop=N) acc | 0.967 (v2/v3) | 0.7144 | -0.253 |
| ABC acc | 0.900 (v2/v3) | 0.7589 | -0.141 |
| **Δ (Solo − ABC)** | **+0.067** | **−0.0444 (ABC > Solo)** | **방향 반전** |
| n_tasks | 9 | 15 | 확대 |

**해석**:
- 9 task subset 한정 비교에서는 Solo +0.067 우위 (ceiling effect 수렴)
- 15 task 확대 (planning 2 + synthesis-05 추가) 시 ABC +0.044 우위로 **방향 반전**
- 추가 task (특히 synthesis 카테고리) 가 H4 회복의 핵심
- 본 결과 의 mean acc 가 Exp06 보다 낮은 이유: planning task 가 어려운 쪽 (planning-02 very_hard) 추가 + 9 task subset 의 ceiling 효과 해소

## 10. Stage 3 (Exp11 Mixed Intelligence) 함의

- ✅ **Mixed Intelligence (Role 축 강화) 가설 정합성 부분 회복** — Stage 2C 의 H4 ⚠ 조건부 채택이 Mixed Intelligence 의 동기 보강
- 🎯 **synthesis 카테고리 강조** — Mixed Intelligence task 선택 시 synthesis 가 가장 명료한 효과
- ⚠ **logic 카테고리 신중** — ABC 약함, Judge 강화 효과 미확정. Mixed Intelligence plan 에 logic 포함 시 신중 평가
- 🐛 **assertion turnover 측정 결함** — Stage 4 Exp11 plan 작성 시 ABC 의 cycle-by-cycle tattoo history 저장 필수 (run.py 의 history 저장 로직 보강)
- 📊 **통계 검정력 한계** — Exp11 시 n_tasks 추가 확대 (15 → 18~20) 또는 trial 확대 (5 → 10) 검토. 단 직전 Exp09 5-trial dilute 사고 학습 — task 확대 우선

## 11. 한계

- **n=15 task paired**: Wilcoxon / t-test 검정력 부족. 비유의 = "효과 없음" 아니라 "현재 데이터로 통계적 검정력 부족". Cohen's d=0.449 는 medium effect 시사
- **assertion turnover 측정 결함** — ABC 의 질적 차이 측정 불가 (위 §7)
- **logic-04 의 ABC −0.20** — Stage 2A v3 negative_patterns 효과로 false positive 차단. 본 effect 가 ABC 약함 vs 채점 정직성 어느 쪽인지 분리 어려움
- **planning task 2 개만** — 신규 카테고리 sample 부족. 추가 planning task 확대 후속 plan 후보
- **5 trial 한계** — 직전 Exp09 5-trial dilute 학습으로 task 수 확대 우선했으나, condition 별 75 trial 검정력은 paired n=15 에 의존
- **Solo-1call 의 cycles=1** — Tattoo 미사용. solo_1call vs solo_budget 비교는 다단계 효과 + Tattoo 사용 합산. 두 효과 분리 불가 (별도 plan)

## 12. 향후 보강 (본 plan 영역 외)

- Stage 4 Exp11 plan: ABC tattoo_history 저장 보강
- 별도 plan: planning task 확대 (2 → 5+), n_tasks 확대 (15 → 20+)
- 별도 plan: math-04 use_tools 정책 통일 (현재 0/0/0 — Tool 미주입)
- 별도 plan: logic-04 의 ABC −0.20 원인 분리 — negative_patterns 효과 vs ABC 약함

## 13. 변경 이력

- 2026-05-02 v1: 초안. Stage 2C Task 04 (사용자 직접 실행, 2026-05-01 ~ 2026-05-02) 마감 후 Architect 분석.
