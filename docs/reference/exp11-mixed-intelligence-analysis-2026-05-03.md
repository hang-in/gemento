---
type: reference
status: done
updated_at: 2026-05-03
canonical: true
---

# Exp11 Mixed Intelligence 분석 (Stage 4)

**Plan**: `exp11-mixed-intelligence-haiku-judge` (v2 — Haiku → Gemini 2.5 Flash)
**실행일**: 2026-05-02 (baseline_abc) ~ 2026-05-03 (mixed_flash_judge)
**조건**: baseline_abc (A/B/C 모두 Gemma 4 E4B) vs mixed_flash_judge (A/B = Gemma, C = Gemini 2.5 Flash) × 15 task × 5 trial = **150 trial**
**Judge 모델**: `gemini-2.5-flash` (사용자 GEMINI_API_KEY 보유)
**채점**: `score_answer_v3` (negative_patterns 적용)

## 1. condition aggregate

| condition | n | mean_acc | median per-task | err | null | avg_cycles | avg_dur | total cost |
|-----------|---|---------:|----------------:|----:|----:|-----------:|--------:|-----------:|
| baseline_abc | 75 | 0.7778 | 0.9333 | 7 (9%) | 7 | 7.2 | 437s | $0.0000 |
| **mixed_flash_judge** | 75 | **0.6967** | 0.8000 | 8 (11%) | 8 | 6.7 | 377s | **$0.0843** |

**Δ(mixed − baseline) = −0.0811** (음수 — Mixed 가 baseline 보다 약함).

## 2. 통계 검정 (n=15 task paired)

| 검정 | 통계량 | p-value | 판정 |
|------|--------|--------:|------|
| Wilcoxon signed-rank | W=10.50 | 0.2930 | NOT SIGNIFICANT |
| Paired t-test | t=−1.225 | 0.2407 | NOT SIGNIFICANT |
| **Cohen's d (paired)** | **−0.316** | — | **small effect, 음수 방향** |
| Bootstrap 95% CI Δ (n=10000) | [−0.220, +0.022] | — | 0 거의 포함 (단 음수 방향 우세) |

**해석**:
- 통계 비유의 (p > 0.05) — n=15 검정력 한계
- Cohen d small effect 음수 — Mixed 가 baseline 보다 약함 신호
- Bootstrap CI 가 0 거의 포함 — "확실한 차이" 단언 어려움
- **모든 metric 의 방향이 mixed < baseline** — 채택 가능성 0

## 3. 카테고리별 break-down

| category | n_tasks | baseline | mixed | **Δ(mixed−base)** | 해석 |
|----------|--------:|---------:|------:|-----------------:|------|
| math | 4 | 0.7500 | 0.7000 | **−0.0500** | math-01 saturation 깨짐 (1.0 → 0.8). math-04 양쪽 0 (Tool 부재) |
| **logic** | 4 | 0.7750 | **0.5000** | **−0.2750** ⬇⬇ | logic-02 catastrophic (0.9 → 0). logic-04 0 → 0 (보존) |
| **synthesis** | 5 | 0.7267 | 0.7567 | **+0.0300** ⬆ | **유일한 양수** — Stage 2C 의 H4 회복 영역 정합. 단 +0.03 작음 |
| planning | 2 | 0.9667 | 0.9333 | −0.0333 | planning-02 미세 약화 |

→ **logic 카테고리 catastrophic** (−0.275) 가 종합 음수의 주요 동력.

## 4. Per-task break-down (\|Δ\|>0.01)

| task | category | difficulty | baseline | mixed | Δ | 패턴 |
|------|----------|-----------|---------:|------:|--:|------|
| **logic-02** | logic | hard | 0.900 | **0.000** | **−0.900** | 5/5 catastrophic — case study (§5) |
| logic-04 | logic | very_hard | 0.200 | 0.000 | −0.200 | v3 negative_patterns 보존 |
| math-01 | math | medium | 1.000 | 0.800 | −0.200 | saturation 깨짐 |
| **synthesis-05** | synthesis | hard | 0.700 | 0.450 | **−0.250** | 신규 task (Stage 2C) — Mixed 약함 |
| planning-02 | planning | very_hard | 0.933 | 0.867 | −0.067 | |
| **synthesis-01** | synthesis | medium | 0.600 | 0.800 | **+0.200** ⬆ | Mixed 강함 |
| **synthesis-03** | synthesis | very_hard | 0.600 | 0.733 | **+0.133** ⬆ | Mixed 강함 |
| synthesis-04 | synthesis | very_hard | 0.733 | 0.800 | +0.067 | |

→ synthesis 일부 (01/03/04) 에서 Mixed 우위, 단 logic-02/synthesis-05/math-01 의 약화가 압도. 종합 −0.0811.

## 5. Case study — logic-02 (catastrophic Δ=−0.900)

logic-02 = 의도적 inconsistent 데이터 (집합 inclusion-exclusion 105 > 100). 정답 keyword `[['105', 'inconsistent'], ['0']]` — "105 inconsistent" 명시 필수.

### baseline (모두 Gemma) — 4/5 trial acc=1.0

| trial | answer 첫 200자 |
|-------|----------------|
| 0 | "The problem data set is mathematically **inconsistent** because the number of people speaking at least one language (**105**) exceeds the total population (100)..." |
| 2 | "The input data provided for the problem is mathematically **inconsistent**. Based on the Inclusion-Exclusion Principle (IEP), the number of people speaking at least one language is calculated... (**105**)" |
| 3, 4 | 동일 패턴 — "105", "inconsistent" 명시 |

→ Gemma A/B/C 가 inclusion-exclusion 적용 + 105 도출 + inconsistent 명시까지 **자기 발견** 성공.

### mixed (Flash Judge) — 5/5 trial acc=0

| trial | cycles | answer |
|-------|-------:|--------|
| 0 | 8 | (null) — max cycle 도달, final_answer 부재 |
| 1 | 6 | "**-5**" — 단순 계산만, inconsistent 결론 없음 |
| 2 | 8 | (null) |
| 3 | 7 | "negative number is impossible, indicates that the **input data set** for the problem is..." — keyword "105"/"inconsistent" 부재 |
| 4 | 8 | (null) |

→ Flash Judge 가 cycle 단축 (avg 7.2 → 6.7) 또는 final_answer 부재 패턴. Gemma 의 자기 발견 chain 을 **방해**.

## 6. error mode 분포 (FailureLabel, Stage 2B)

| condition | NONE | wrong_synthesis | other | format_error |
|-----------|----:|----------------:|------:|-------------:|
| baseline_abc | 61 | 6 | 7 | 1 |
| mixed_flash_judge | **53** | **11** | 8 | 3 |

- **NONE 8 감소** (61→53) — 정답 비율 ↓
- **WRONG_SYNTHESIS 5 증가** (6→11) — Flash Judge 가 잘못된 결론 유도 신호
- **FORMAT_ERROR 2 증가** (1→3) — 작지만 schema mismatch 신호

## 7. assertion turnover (cycle-by-cycle, Stage 2C 결함 fix 후 첫 측정)

| condition | added (mean) | modified (mean) | final_count (mean) |
|-----------|-------------:|----------------:|-------------------:|
| baseline_abc | 4.80 | 0.28 | 4.80 |
| mixed_flash_judge | **4.32** | **0.32** | 4.32 |

→ **H10 의 메커니즘 부재**:
- mixed 의 added (4.32) 가 baseline (4.80) 보다 적음 — cycle 단축 (6.7 vs 7.2) 영향
- modified 차이 미미 (0.04) — Flash Judge 가 A 의 assertion 을 의미 있게 수정시킨 효과 **부재**
- 본 plan 의 핵심 가설 ("Judge 가 약한 Proposer 의 assertion 을 수정하여 보완") **직접 반증**

## 8. cost / 시간 효율

| metric | baseline_abc | mixed_flash_judge |
|--------|-------------:|------------------:|
| total cost | $0.0000 | $0.0843 |
| trial 당 cost | $0.0000 | $0.0011 |
| Flash 호출 수 (mixed) | 0 | ~538 (75 trial × 7.17 cycle) |
| 추정 비용 vs 실제 | — | $0.18 추정 / $0.084 실제 (output 짧음) |
| avg duration | 437s | 377s (-14% 시간 절약) |

→ 비용 측면 Flash 합리. 단 본 plan 의 의의는 "비용 효율" 이 아니라 "Judge 강화 효과" — 효과 부재라 비용 효율 무관.

## 9. Architect verdict — **⚠ H10 미결 (실효적 기각)**

verdict 결정 트리 적용:

| 조건 | 충족? |
|------|-------|
| Δ ≥ +0.10 (강한 채택) | ❌ 음수 |
| Δ ≥ +0.05 + p<0.05 (조건부 채택) | ❌ |
| \|Δ\| < 0.05 (미결) | ❌ Δ −0.08 |
| **Δ < 0** | ✅ **기각 분기** |

**Architect 최종 verdict**: **⚠ 미결 (음의 방향, 실효적 기각)**.

근거:
- Δ −0.0811 음수
- Cohen d −0.316 small effect 음수
- 통계 비유의 (n=15 검정력 한계, 단정적 기각 어려움)
- Bootstrap CI 0 거의 포함, 단 음수 방향 우세
- 모든 metric 의 방향이 mixed < baseline
- assertion turnover 의 H10 메커니즘 부재
- logic-02 catastrophic case study confirm

→ "확실한 채택" 또는 "확실한 기각" 대신 정직한 결론: **Mixed Intelligence (Flash Judge) 가 baseline 대비 우위를 보이지 못함. H10 가설은 본 데이터로 미지원.**

## 10. 의외 발견 — Flash Judge 가 추론 chain 을 *방해*

본 plan 의 사전 예측: Mixed 가 우위 또는 미결. 실제 결과: **음수 방향 + 메커니즘 정반대**.

가설 H10 의 정반대 메커니즘:
- Flash Judge 가 verdict + 메타 판단 외에 *추론 결과* 까지 영향 (Risk 1 정반대 — 단순 verdict 강제 어려움)
- Gemma 의 self-discovery chain (logic-02 의 inclusion-exclusion 적용 → 105 도출 → inconsistent 결론) 을 Flash 가 단축 시도 → final_answer 부재 또는 keyword 부재
- **약한 모델의 자기 발견 chain 이 강한 Judge 의 간섭으로 깨질 수 있다** — 새 가설 후보

## 11. Stage 2C (H4) 와의 관계

| 비교 | Stage 2C abc vs Solo-budget | Exp11 mixed vs baseline |
|------|----------------------------:|-----------------------:|
| Δ | +0.0444 (ABC > Solo) | **−0.0811** (Mixed < ABC) |
| synthesis 카테고리 Δ | +0.140 (ABC 회복 핵심) | +0.030 (Mixed 약한 우위) |
| logic 카테고리 Δ | −0.025 | −0.275 (catastrophic) |
| 통계 | p=0.16 (NOT SIG) | p=0.29 (NOT SIG) |
| Cohen d | +0.449 (medium 양수) | −0.316 (small 음수) |

→ Stage 2C 의 H4 ⚠ 조건부 채택 (synthesis 한정 회복) 위에서, **Exp11 의 Judge 강화는 회복 효과 약화**. synthesis 영역의 미세한 Mixed 우위 (+0.03) 가 Stage 2C 의 H4 회복 (+0.140) 보다 작음 — Judge 강화의 *역효과* 시사.

## 12. Stage 5 (다음 외부화 축) 함의

본 결과 + Stage 2C H4 ⚠ 조건부 채택 종합:

| 외부화 축 | Stage 2C / Exp11 결과 | 다음 plan 권고 |
|----------|----------------------|----------------|
| **Role Agent (A/B/C 분리)** | Stage 2C: synthesis 회복 +0.140 | ✓ 현 framework 유지 |
| **Role 강화 (Judge 강한 모델)** | Exp11: 종합 −0.0811 (실효적 기각) | ❌ 본 방향 비추천 |
| **Tool 외부화** | Exp08 채택 (math-04 0→80%) | ✓ math-* use_tools 통일 후속 plan |
| **Search Tool / Extractor / Reducer** | 미검증 | **🎯 Exp12 우선 후보** (본 결과로 우선순위 상향) |
| **Tattoo (long context)** | Exp09 H9a 채택 | ✓ small paradox 후속 plan |

→ **Mixed Intelligence (Role 강화) 가설 잠정 기각** + Search Tool / 다른 미외부화 축 우선 전환.

## 13. 한계

- **n=15 task paired** — Wilcoxon / t-test 검정력 부족. 단정적 기각보다 "미결" 결론 권장
- **Flash Judge 응답 raw text 표본 분석 미완** — JUDGE_PROMPT 가 Gemma 최적화 / Flash 와 mismatch 인지 미확정. 후속 plan 후보 (Judge prompt 강화 + Mixed 재검증)
- **5 trial 한계** — task 별 sample 작음. 단 직전 Exp09 5-trial dilute 학습 + 본 plan 의 task 수 (15) 우선
- **synthesis 카테고리 일부 양수** (+0.03) — 추가 synthesis task 확대 시 Mixed 가 우위 회복 가능성. 본 결과 단정적 기각 어려움
- **Tool 축 미검증** — math-04 양쪽 0 (use_tools=False). Mixed 도 Tool 부재라 H10 측정에 노이즈
- **Flash 가 짧게 응답** — JUDGE_PROMPT 가 verdict 만 요구. Flash 의 reasoning 능력 활용 안 됨 가능성

## 14. 향후 보강 (본 plan 영역 외)

- Search Tool (Exp12 후보) — Stage 5 시점에 우선 검토
- Judge prompt 강화 + Mixed 재검증 — 단 본 결과의 정반대 메커니즘 발견으로 동기 흔들림
- math-* use_tools=True 통일 (Exp08 정합) — 별도 plan
- task 확대 (15 → 20+) + n_trials 확대 — 통계 검정력 회복

## 15. 변경 이력

- 2026-05-03 v1: 초안. Stage 4 Task 04 (사용자 직접 실행 2026-05-02~03) 마감 후 Architect 분석. 사용자 위임 ("Architect 권장대로 진행", "진행해") 으로 verdict 직접 결정.
