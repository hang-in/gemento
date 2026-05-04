---
type: result
status: done
updated_at: 2026-05-04
experiment: 실험 12 — Extractor Role
---

# 실험 12: Extractor Role 결과 보고서

## 1. 개요

**가설 H11**: 신규 Role (Extractor) 이 task prompt 의 claims/entities 를 사전 추출하여 A→B→C chain 의 input 으로 prefix 주입하면, A 의 부담 감소 + 정확도 향상.

| 항목 | 내용 |
|------|------|
| **모델** | Gemma 4 E4B (LM Studio Q8_0 `http://192.168.1.179:1234`) — A/B/C 모두 동일 + Extractor 도 동일 모델 |
| **실행일** | 2026-05-03 (baseline_abc) ~ 2026-05-04 (extractor_abc) |
| **태스크셋** | Stage 2C 의 15 task (math 4 + logic 4 + synthesis 5 + planning 2) |
| **조건** | baseline_abc / extractor_abc × 5 trial |
| **실행 수** | 2 condition × 15 task × 5 trial = **150 trial** |
| **외부 API 비용** | $0 (local Gemma만) |
| **인프라** | Stage 2A healthcheck/abort + Stage 2B FailureLabel + Stage 2C tattoo_history cycle-by-cycle fix + Exp11 c_caller 보존 + 본 plan 의 `extractor_pre_stage` hook |

소스:
- `experiments/exp12_extractor_role/results/exp12_extractor_role_20260503_151724.json` (baseline_abc, 75 trial)
- `experiments/exp12_extractor_role/results/exp12_extractor_abc.json` (extractor, 75 trial)

상세 분석: `docs/reference/exp12-extractor-role-analysis-2026-05-04.md`.

## 2. 핵심 메트릭

| condition | n | mean_acc | median per-task | err+null | avg_cycles | avg_dur |
|-----------|--:|---------:|----------------:|--------:|-----------:|--------:|
| baseline_abc | 75 | 0.7500 | 1.0000 | 10+10 | 7.3 | 412s |
| **extractor_abc** | 75 | **0.8000** | 1.0000 | 5+5 | 7.1 | 425s |

**Δ(extractor − baseline) = +0.0500** (양수 — Exp11 Mixed Intelligence 의 −0.0811 정반대).

## 3. 카테고리별 break-down

| category | n_tasks | baseline | extractor | Δ |
|----------|--------:|---------:|----------:|--:|
| math | 4 | 0.7500 | 0.7500 | +0.000 (saturation) |
| **logic** | 4 | 0.5250 | **0.6500** | **+0.125** (logic-02 회복 +0.30) |
| **synthesis** | 5 | 0.8300 | **0.8800** | **+0.050** (synthesis-05 회복 +0.45) |
| planning | 2 | 1.0000 | 1.0000 | +0.000 (saturation) |

## 4. 통계 검정 (n=15 task paired)

| 검정 | 통계량 | p-value | 판정 |
|------|--------|--------:|------|
| Wilcoxon | W=1.50 | 0.1975 | NOT SIGNIFICANT |
| Paired t | t=1.252 | 0.2311 | NOT SIGNIFICANT |
| **Cohen's d** | **+0.323** | — | **small effect, 양수** |
| Bootstrap 95% CI Δ | [−0.020, +0.133] | — | 0 거의 포함, 양수 우세 |

## 5. 분석

### 5.1 H11 verdict — ⚠ 조건부 채택 (양수 방향, 검정력 한계)

- 격차 +0.05 임계 + p>0.05 (n=15 검정력 한계)
- Cohen d +0.323 small 양수
- 모든 metric 의 방향이 ext > baseline (mean_acc / error 비율 / NONE 카운트)
- catastrophic 영역 (logic-02 / synthesis-05) 회복 명확

### 5.2 Per-task 핵심 — catastrophic 회복 + saturation 흔들림

| task | base | ext | Δ | 패턴 |
|------|----:|----:|--:|------|
| **logic-02** | 0.30 | 0.60 | **+0.30** | inconsistent puzzle 회복 (Stage 2C/Exp11 catastrophic 영역) |
| logic-03 | 0.80 | 1.00 | +0.20 | 일반화 문제 |
| **synthesis-05** | 0.55 | 1.00 | **+0.45** | 3 출처 모순 종합 — Extractor source/claim 분리 효과 |
| synthesis-02 | 1.00 | 0.80 | −0.20 | saturation 깨짐, 역효과 |

### 5.3 Exp11 (H10) 와의 결정적 대비

| 비교 | Exp11 Mixed (H10) | Exp12 Extractor (H11) |
|------|------------------:|----------------------:|
| Δ acc | **−0.0811** | **+0.0500** |
| Cohen d | −0.316 | **+0.323** |
| logic-02 | 0.9 → 0.0 (catastrophic) | 0.3 → 0.6 (회복) |
| 메커니즘 | schema mismatch + 단축 | 입력 정리 + 안정화 |
| 외부 API | $0.0843 | $0 |

→ **Role 축의 진화 방향**: 강화 (Mixed) ❌ vs 분리/추가 (Extractor) ✅.

### 5.4 메커니즘 — error mode 안정성

baseline NONE 58 → extractor NONE 63 (+5). err 13% → 7% (절반). Extractor 효과 = 정답 안정성 ↑ + catastrophic fail 회피.

assertion turnover (added/modified) 차이 미미 — Extractor 가 A 의 작업 *대체* 가 아니라 *입력 정리* 효과 (cycle 1 의 prompt prefix).

## 6. 결론 + 다음 단계

### 결론

1. **H11 ⚠ 조건부 채택** — Extractor 가 catastrophic 영역 (logic-02 +0.30, synthesis-05 +0.45) 에서 명확한 회복
2. **Exp11 의 정반대 메커니즘** — 같은 모델 Role 분리는 양수, 강한 모델 Role 강화는 음수
3. **framework 진화 방향**: Role 축 *다양화* (분리/추가) 가 *강화* 보다 안전

### 다음 단계 (Stage 5 다음)

- 🎯 **Reducer Role (Exp14 후보)** — Role 다양화 라인 연속
- **Search Tool (Exp13 후보)** — Tool 축 신규, Stage 5 SQLite ledger 동기
- Mixed Intelligence 재시도 — 비추천 (Exp11 정반대 메커니즘 disclosure)
- math-* use_tools 통일 — 별도 plan 후보

## 7. 한계

- **n=15 task paired** — 통계 검정력 부족
- **5 trial** — sample 한계
- **first_cycle_assertions = 0** — Extractor 메커니즘 의 직접 측정 결함 (효과는 정확도/error mode 로 간접)
- **synthesis-02 역효과** (−0.20) — Extractor 의 negative case. 추가 분석 필요
- **Tool 축 미검증** — math-04 양쪽 0
