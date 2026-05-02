---
type: result
status: done
updated_at: 2026-05-03
experiment: 실험 11 — Mixed Intelligence (Flash Judge)
---

# 실험 11: Mixed Intelligence (Flash Judge) 결과 보고서

## 1. 개요

**가설 H10**: 강한 Judge C (Gemini 2.5 Flash) 가 약한 Proposer/Critic (A/B = Gemma 4 E4B) 의 한계를 보완한다. Role 축 강화 가설.

| 항목 | 내용 |
|------|------|
| **모델** | A/B: Gemma 4 E4B (LM Studio Q8_0 `http://192.168.1.179:1234`), C (mixed): `gemini-2.5-flash` |
| **실행일** | 2026-05-02 (baseline_abc) ~ 2026-05-03 (mixed_flash_judge) |
| **태스크셋** | `taskset.json` 의 15 task (Stage 2C 정합 — math 4 + logic 4 + synthesis 5 + planning 2) |
| **조건** | baseline_abc / mixed_flash_judge × 5 trial |
| **실행 수** | 2 condition × 15 task × 5 trial = **150 trial** |
| **채점** | `score_answer_v3` (negative_patterns 적용) |
| **인프라** | Stage 2A healthcheck/abort + Stage 2B FailureLabel + Stage 2C tattoo_history cycle-by-cycle fix |

소스 데이터:
- `experiments/exp11_mixed_intelligence/results/exp11_mixed_intelligence_20260502_143554.json` (baseline_abc, 75 trial)
- `experiments/exp11_mixed_intelligence/results/exp11_mixed_flash_judge.json` (mixed, 75 trial)

상세 분석: `docs/reference/exp11-mixed-intelligence-analysis-2026-05-03.md`.

## 2. 핵심 메트릭

| condition | n | mean_acc | median per-task | err+null | avg_cycles | avg_dur | total cost |
|-----------|--:|---------:|----------------:|--------:|-----------:|--------:|-----------:|
| baseline_abc | 75 | **0.7778** | 0.9333 | 7+7 | 7.2 | 437s | $0.0000 |
| mixed_flash_judge | 75 | **0.6967** | 0.8000 | 8+8 | 6.7 | 377s | **$0.0843** |

**Δ(mixed − baseline) = −0.0811** (음수).

## 3. 카테고리별 break-down

| category | n_tasks | baseline | mixed | Δ | 해석 |
|----------|--------:|---------:|------:|--:|------|
| math | 4 | 0.7500 | 0.7000 | **−0.0500** | math-01 saturation 깨짐 (1.0→0.8) |
| logic | 4 | 0.7750 | 0.5000 | **−0.2750** | logic-02 catastrophic (0.9→0) |
| synthesis | 5 | 0.7267 | 0.7567 | **+0.0300** | 유일한 양수 |
| planning | 2 | 0.9667 | 0.9333 | −0.0333 | |

## 4. 통계 검정 (n=15 task paired)

| 검정 | 통계량 | p-value | 판정 |
|------|--------|--------:|------|
| Wilcoxon | W=10.50 | 0.2930 | NOT SIGNIFICANT |
| Paired t-test | t=−1.225 | 0.2407 | NOT SIGNIFICANT |
| **Cohen's d** | **−0.316** | — | **small effect, 음수 방향** |
| Bootstrap 95% CI Δ | [−0.220, +0.022] | — | 0 거의 포함, 음수 방향 우세 |

## 5. 분석

### 5.1 H10 verdict — ⚠ 미결 (실효적 기각)

- 격차 −0.08 음수
- 통계 비유의 (n=15 검정력 한계)
- Cohen d small 음수
- 모든 metric 의 방향이 mixed < baseline
- assertion turnover 의 H10 메커니즘 (mixed의 modified ↑) 부재

### 5.2 의외 발견 — Flash Judge 가 추론 chain 을 *방해*

logic-02 case study (catastrophic Δ=−0.900):
- baseline 4/5 trial 이 "105 inconsistent" 명시 (inclusion-exclusion 자기 발견)
- mixed 5/5 trial 이 null 또는 keyword 부재 ("-5", "input data set" 등)
- → Flash Judge 가 cycle 단축 (7.2 → 6.7) + Tattoo schema mismatch + 추론 chain 단절

본 plan 의 H10 본 가설 ("강한 Judge → 약한 Proposer 보완") 의 **정반대 메커니즘**: Judge 강화가 약한 모델의 self-discovery chain 을 *방해*.

### 5.3 assertion turnover (Stage 2C 결함 fix 후 첫 측정)

| condition | added | modified | final_count |
|-----------|------:|---------:|------------:|
| baseline_abc | 4.80 | 0.28 | 4.80 |
| mixed_flash_judge | 4.32 | 0.32 | 4.32 |

→ Mixed 의 modified 차이 미미 (0.04). Flash Judge 의 "보완" 메커니즘 부재.

### 5.4 cost / 시간

mixed 의 trial 당 cost = $0.0011, 총 $0.0843. 추정 ($0.18) 의 절반 (Flash 응답 짧음). 시간 -14% 절약. 단 정확도 −0.0811 → cost-aware 평가도 mixed 약함.

## 6. 결론 + 다음 단계

### 결론

1. **H10 ⚠ 미결 (실효적 기각)** — Mixed Intelligence (Flash Judge) 가 baseline (모두 Gemma) 대비 우위를 보이지 못함
2. **synthesis 카테고리 미세 양수** (+0.030) — Stage 2C 의 H4 회복 영역과 정합. 단 logic 카테고리 catastrophic (−0.275) 가 압도
3. **메커니즘 정반대 발견** — Judge 강화가 약한 모델의 추론 chain 을 *방해* 가능. 후속 가설 후보

### 다음 단계 (Stage 5 의제)

- ❌ **Mixed Intelligence (Role 강화) 가설 잠정 기각** — 본 방향 후속 plan 비추천
- 🎯 **Search Tool / 다른 미외부화 축 우선** (Exp12 후보) — Stage 2C 의 H4 ⚠ 조건부 채택 정합성 보존하며 다른 축 검증
- 별도 plan 후보:
  - Judge prompt 강화 + Mixed 재검증 (단 정반대 메커니즘 발견으로 동기 흔들림)
  - math-* use_tools=True 통일 (Exp08 정합)
  - task 확대 (15 → 20+) — 통계 검정력 회복

## 7. 한계

- **n=15 task paired** — 통계 검정력 한계. 단정적 기각보다 "미결" 결론
- **5 trial** — task 별 sample 작음 (단 task 수 우선 정책)
- **synthesis 일부 양수** (+0.03) — 추가 synthesis task 확대 시 Mixed 회복 가능성 못 배제
- **Tool 축 미검증** — math-04 양쪽 0 (use_tools=False), Mixed 측정 노이즈
- **Flash 의 reasoning 능력 활용 안 됨** — JUDGE_PROMPT 가 단순 verdict 요구. Flash 의 잠재력 미발휘 가능성
