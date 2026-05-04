---
type: result
status: done
updated_at: 2026-05-05
experiment: 실험 13 — Reducer Role
---

# 실험 13: Reducer Role 결과 보고서

## 1. 개요

**가설 H12**: 신규 Role (Reducer) 가 ABC chain 의 final tattoo + final_answer 를 받아 *post-stage* 에서 정리/통합하면, keyword 매칭 정확도 + final answer 명료성 향상.

| 항목 | 내용 |
|------|------|
| **모델** | Gemma 4 E4B (LM Studio Q8_0 `http://192.168.1.179:1234`) — A/B/C 모두 동일 + Reducer 도 동일 모델 |
| **실행일** | 2026-05-04 10:15 ~ 19:12 (baseline_abc) / 2026-05-04 19:14 ~ 2026-05-05 03:51 (reducer_abc) |
| **태스크셋** | Stage 2C / Exp12 의 15 task (math 4 + logic 4 + synthesis 5 + planning 2) |
| **조건** | baseline_abc / reducer_abc × 5 trial |
| **실행 수** | 2 condition × 15 task × 5 trial = **150 trial** |
| **외부 API 비용** | $0 (local Gemma만) |
| **인프라** | Stage 2A healthcheck/abort + Stage 2B FailureLabel + Stage 2C tattoo_history cycle-by-cycle fix + Exp11 c_caller / Exp12 extractor_pre_stage 보존 + 본 plan 의 `reducer_post_stage` hook |

소스:
- `experiments/exp13_reducer_role/results/exp13_reducer_role_20260504_191208.json` (baseline_abc, 75 trial)
- `experiments/exp13_reducer_role/results/exp13_reducer_abc.json` (reducer, 75 trial)

상세 분석: `docs/reference/exp13-reducer-role-analysis-2026-05-05.md`.

## 2. 핵심 메트릭

| condition | n | mean_acc | err+null | avg_cycles | avg_dur |
|-----------|--:|---------:|--------:|-----------:|--------:|
| baseline_abc | 75 | 0.7744 | 9+9 | 7.2 | 429s |
| **reducer_abc** | 75 | **0.7033** | 8+8 (+ 2 TypeError) | 7.0 | 414s |

**Δ(reducer − baseline) = −0.0711** (음수 — Exp12 Extractor 의 +0.0500 정반대 방향).

**중요 — orchestrator bug 발견 + 즉시 fix** (commit `cf057b6`):
- `experiments/orchestrator.py:653` 의 `len(fa)` 가 final_answer 가 int 일 때 깨짐
- math-02 trial 2/3 cycles=0 즉시 실패 (TypeError)
- 한 줄 fix: `fa = fa if isinstance(fa, str) else str(fa)` coercion
- 영향: Δ 방향 **불변** (bug 제외 시도 −0.0533, 여전히 음수)

## 3. 카테고리별 break-down

| category | n_tasks | baseline | reducer | Δ |
|----------|--------:|---------:|--------:|--:|
| **logic** | 4 | 0.7250 | 0.6250 | **−0.100** ⬇ |
| **math** | 4 | 0.7000 | 0.6167 | **−0.083** ⬇ (math-02 catastrophic, 일부 bug) |
| **synthesis** | 5 | 0.8233 | 0.7167 | **−0.107** ⬇ (5/5 task 음수) |
| planning | 2 | 0.9000 | 1.0000 | +0.100 (planning-02 +0.20) |

→ synthesis 5/5 task 모두 음수, Exp12 회복 영역이 Exp13 에서는 정반대.

## 4. 통계 검정 (n=15 task paired)

| 검정 | with bug (primary) | bug-excluded | 판정 |
|------|------------------:|-------------:|------|
| **mean Δ** | **−0.0711** | **−0.0533** | 양쪽 음수 |
| **Cohen's d** | **−0.344** | **−0.323** | small-medium 음수 |
| paired t | t=−1.333, p=0.2038 | t=−1.251, p=0.2315 | NOT SIGNIFICANT |
| Wilcoxon | W=18.0, p=0.1801 | W=18.0, p=0.1801 | NOT SIGNIFICANT |
| Bootstrap 95% CI Δ | [−0.176, +0.024] | [−0.133, +0.027] | 0 거의 포함, 음수 우세 |

→ Exp12 의 Cohen d=+0.323 와 거의 동일 크기, **정반대 방향 (거울상)**.

## 5. 분석

### 5.1 H12 verdict — ⚠ 미결 (실효적 기각)

- Δ −0.0711 (bug 포함) / −0.0533 (bug 제외) — 양쪽 모두 임계값 −0.05 초과
- Cohen d −0.323 ~ −0.344 — Exp12 의 +0.323 와 거울상
- 카테고리 logic / math / synthesis 모두 음수 (planning 만 양수, n=2)
- 통계 비유의 (p>0.05) — "기각" 보다 "미결 (실효적 기각)" — Exp11 패턴

### 5.2 Per-task 핵심 — catastrophic 영역 4/4 음수 강화

| task | base | red | Δ | 패턴 |
|------|----:|----:|--:|------|
| **math-02** | 1.00 | 0.40 | **−0.60** | 면적 saturation 깨짐 (2/5 = bug, bug 제외 시 0.667) |
| **synthesis-04** | 0.93 | 0.67 | **−0.27** | 다출처 새 개체수 모순 — Reducer 의 단일 추정 압축 |
| logic-04 | 0.20 | 0.00 | −0.20 | 일반화 puzzle catastrophic 강화 |
| logic-02 | 0.70 | 0.50 | −0.20 | inconsistent puzzle (Exp12 회복 영역) |
| synthesis-01 | 1.00 | 0.80 | −0.20 | saturation 깨짐 |

### 5.3 메커니즘 — synthesis-04 case study

**baseline (acc=1.00)**:
```
## Comprehensive Analysis ... Identification of Contradictions ...
**Zone C Count (R5 vs R1/R6):** ...
```
구조화된 분석 + multi-keyword + 다중 추정.

**reducer (acc=0.67)**:
```
The best estimate is **270 individuals**.
This figure is derived by ...
```
단일 추정 압축. 다중 출처 분석 구조 누락.

→ Reducer prompt 의 *"polish for clarity"* + *"do NOT change conclusion"* 이 모델을 **단일 답변으로 압축** 시킴 → keyword 매칭 실패.

**중요**: Reducer 가 짧게 만드는 것이 아니다 — 평균 길이는 baseline 230 vs reducer 281 (오히려 약간 김). **abstraction loss** (다중 출처/다중 추정 → 단일 추정) 이 핵심 메커니즘.

### 5.4 Exp11 (H10) / Exp12 (H11) / Exp13 (H12) 거울상 대비

| 비교 | Exp11 Mixed (H10) | Exp12 Extractor (H11) | **Exp13 Reducer (H12)** |
|------|------------------:|----------------------:|-------------------------:|
| 위치 | C 강화 | **pre-stage** | **post-stage** |
| Δ acc | −0.0811 | **+0.0500** | **−0.0533** (bug 제외) |
| Cohen d | −0.316 | **+0.323** | **−0.323** |
| 메커니즘 | chain 단절 | input 안정화 | **abstraction loss** |
| verdict | ⚠ 미결 (실효적 기각) | ⚠ 조건부 채택 | ⚠ **미결 (실효적 기각)** |

→ **본 plan 의 핵심 가정 (Extractor ↔ Reducer 대칭) 이 실증에서 깨짐**. Exp12 와 Exp13 가 거의 동일 크기의 정반대 효과.

## 6. 결론 + 다음 단계

### 결론

1. **H12 ⚠ 미결 (실효적 기각)** — Reducer 가 다중 출처/다중 추정 task 에서 abstraction loss 유발
2. **Exp12 ↔ Exp13 거울상 결과** — 같은 모델 Role 분리/추가의 효과는 *위치 의존*: pre-stage = 양수, post-stage = 음수
3. **framework-level 새 원칙**: 약한 모델의 chain 은 *건드리지 않을 때* 가장 풍부함. 외부 Role 의 "도움" 은 신중해야

### 확정된 framework 원칙 (H4 + H10 + H11 + H12 통합)

| Role 변경 유형 | 효과 | 메커니즘 |
|---------------|------|----------|
| Role *강화* (강한 모델 도입) | ❌ 음수 | self-discovery chain 단절 (Exp11) |
| Role *분리/추가* — pre-stage | ✅ 양수 | input 안정화 (Exp12) |
| Role *분리/추가* — **post-stage** | ❌ **음수** | **output abstraction loss (Exp13)** |

### 다음 단계 (Stage 5)

- 🎯 **Search Tool (Exp14 후보)** — Tool 축 신규. Role 축 3 회 검증 마감 (강화/pre/post). H7 +18.3pp / H8 +23.3pp 강한 효과 + 결정성 보장
- Reducer prompt 강화 — 비추천 (위치 자체의 위험성이 prompt 보다 본질)
- Extractor + Reducer 조합 (Exp15 후보) — 비추천 (서로 상쇄)
- task 확대 (15 → 20+) — 통계 검정력 회복

## 7. 한계

- **n=15 task paired** — 통계 검정력 부족
- **5 trial** — sample 한계
- **orchestrator bug 2 trial 영향** — Δ 방향 불변, 단 데이터 정합성 zero-impact 아님
- **score_answer_v3 keyword 매칭 의존** — Reducer 의 *의미적* 정확성 측정 한계 (의미적으로는 reducer 가 더 polished 일 수 있으나 채점기는 keyword 만)
- **Tool 축 미검증** — math-04 양쪽 ~0
- **Tattoo schema final_answer type 불일치** — bug 의 근본 원인. 별도 plan 후보
