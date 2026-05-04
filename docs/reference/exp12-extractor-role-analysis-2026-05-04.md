---
type: reference
status: done
updated_at: 2026-05-04
canonical: true
---

# Exp12 Extractor Role 분석 (Stage 5)

**Plan**: `exp12-extractor-role-pre-search`
**실행일**: 2026-05-03 (baseline_abc) ~ 2026-05-04 (extractor_abc)
**조건**: baseline_abc (A/B/C 모두 Gemma) vs extractor_abc (Extractor + A/B/C, 모두 Gemma) × 15 task × 5 trial = **150 trial**
**모델**: Gemma 4 E4B (LM Studio Q8_0 `http://192.168.1.179:1234`) — **외부 API 0**
**채점**: `score_answer_v3` (negative_patterns 적용)

## 1. condition aggregate

| condition | n | mean_acc | median per-task | err+null | avg_cycles | avg_dur |
|-----------|---|---------:|----------------:|--------:|-----------:|--------:|
| baseline_abc | 75 | 0.7500 | 1.0000 | 10+10 | 7.3 | 412s |
| **extractor_abc** | 75 | **0.8000** | 1.0000 | 5+5 | 7.1 | 425s |

**Δ(ext − baseline) = +0.0500** (양수, Exp11 의 −0.0811 정반대).

## 2. 통계 검정 (n=15 task paired)

| 검정 | 통계량 | p-value | 판정 |
|------|--------|--------:|------|
| Wilcoxon signed-rank | W=1.50 | 0.1975 | NOT SIGNIFICANT |
| Paired t-test | t=1.252 | 0.2311 | NOT SIGNIFICANT |
| **Cohen's d (paired)** | **+0.323** | — | **small effect, 양수 방향** |
| Bootstrap 95% CI Δ (n=10000) | [−0.020, +0.133] | — | 0 거의 포함, 양수 방향 우세 |

**해석**:
- 통계 비유의 (n=15 검정력 한계, Stage 2C / Exp11 와 동일 패턴)
- Cohen d small effect 양수 — Extractor 우위 신호
- Bootstrap CI 하한 −0.020 — 0 거의 포함, 단 양수 방향 95% 분포 우세

## 3. 카테고리별 break-down

| category | n_tasks | baseline | extractor | **Δ** | 해석 |
|----------|--------:|---------:|----------:|------:|------|
| math | 4 | 0.7500 | 0.7500 | +0.000 | saturation (math-01/02/03 = 1.0, math-04 = 0 — Tool 부재) |
| **logic** | 4 | 0.5250 | 0.6500 | **+0.125** ⬆ | logic-02 회복 (+0.30) — Stage 2C / Exp11 catastrophic 영역 |
| **synthesis** | 5 | 0.8300 | 0.8800 | **+0.050** | synthesis-05 catastrophic 회복 (+0.45) |
| planning | 2 | 1.0000 | 1.0000 | +0.000 | saturation |

→ **logic + synthesis 의 catastrophic 영역에서 효과 명확**. math/planning 은 saturation 으로 측정 불가.

## 4. Per-task break-down (\|Δ\|>0.01)

| task | category | difficulty | baseline | ext | Δ | 패턴 |
|------|----------|-----------|---------:|----:|--:|------|
| **logic-02** | logic | hard | 0.300 | 0.600 | **+0.300** ⬆ | inconsistent puzzle — Extractor 가 105/inconsistent 사전 추출 → A 인식 회복 |
| logic-03 | logic | hard | 0.800 | 1.000 | +0.200 ⬆ | 일반화 문제 — Extractor entity 분리가 도움 |
| **synthesis-05** | synthesis | hard | 0.550 | 1.000 | **+0.450** ⬆ | 3 출처 모순 종합 — Extractor 가 source/claim 분리 → A 의 다관점 종합 안정화 |
| synthesis-02 | synthesis | hard | 1.000 | 0.800 | −0.200 ⬇ | saturation 깨짐 — Extractor 의 prefix 가 *오히려* A 의 안정 답을 흔듦 |

→ **catastrophic 영역에서 회복 + saturation 영역에서 약간 흔들림** 패턴. 종합 양수.

## 5. error mode (FailureLabel, Stage 2B)

| condition | NONE | wrong_synthesis | other | format_error |
|-----------|----:|----------------:|------:|-------------:|
| baseline_abc | 58 | 5 | 10 | 2 |
| **extractor_abc** | **63** | 6 | 5 | 1 |

- **NONE +5 증가** (58 → 63) — 정답 비율 ↑
- **OTHER -5 감소** — 안정성 ↑
- **CONNECTION_ERROR 0** 모든 condition (Stage 2A 작동)

→ Extractor 효과 = 정답 안정성 ↑ (catastrophic fail 회피).

## 6. assertion turnover — Stage 2C 결함 fix 후 측정

| condition | added (mean) | modified (mean) | first_cycle_assertions | final_count |
|-----------|-------------:|----------------:|----------------------:|------------:|
| baseline_abc | 5.00 | 0.35 | 0.00 | 5.00 |
| extractor_abc | 4.88 | 0.29 | 0.00 | 4.88 |

→ **메커니즘 측정 한계**:
- first_cycle_assertions = 0 모든 condition — `tattoo_history[0]` 가 cycle 1 *시작* 전 의 빈 Tattoo. Extractor 효과가 cycle 1 의 첫 assertions 에 prefix 형태로 주입됐어도 turnover 측정에 직접 안 잡힘
- added/modified 차이 미미 (−0.12 / −0.06) — Extractor 가 A 의 작업 *대체* 보다는 *입력 정리* 효과
- 효과는 **error mode + 카테고리 별 정확도** 에서 명확히 측정 (메커니즘은 cycle-by-cycle turnover 가 아니라 첫 cycle 의 input 안정성)

## 7. 비용 / 시간

| metric | baseline_abc | extractor_abc |
|--------|-------------:|--------------:|
| 외부 API 비용 | $0 | $0 (local Gemma) |
| Extractor 호출 | 0 | 75 (1회/trial) |
| 평균 trial 시간 | 412s | 425s (+3% — Extractor 호출 ~30s × 1회) |

→ 비용 / 시간 trade-off: **+3% 시간으로 +5% 정확도** — Stage 2C 의 H4 회복 영역 (synthesis +0.140) 과 다른 메커니즘 (입력 정리) 으로 추가 효과.

## 8. Architect verdict — **⚠ H11 조건부 채택 (양수 방향, 검정력 한계)**

verdict 결정 트리 (Plan task-05):

| 조건 | 충족? |
|------|-------|
| Δ ≥ +0.10 + p<0.05 (강한 채택) | ❌ Δ=+0.05 임계, p=0.20 |
| Δ ≥ +0.05 + p<0.05 (조건부 채택) | ❌ p=0.20 |
| Δ ≥ +0.05 + p≥0.05 (⚠ 조건부 채택, 검정력 미달) | ✅ **본 분기** |
| \|Δ\| < 0.05 (미결) | ❌ |
| Δ < 0 (기각) | ❌ |

**Architect 최종 verdict**: **⚠ H11 조건부 채택 (logic / synthesis catastrophic 영역 회복)**.

근거:
- Δ +0.05 임계 + p>0.05 (검정력 한계)
- Cohen d +0.323 small 양수
- 모든 metric 의 방향이 ext > baseline:
  - mean_acc: 0.75 → 0.80
  - error 비율: 13% → 7% (절반)
  - error mode NONE: 58 → 63
  - 카테고리 logic +0.125 / synthesis +0.050 (둘 다 양수)
- per-task: catastrophic 영역 (logic-02 / synthesis-05) 회복 명확
- 단 saturation 영역 (synthesis-02) 약간 흔들림 — 단정적 채택보다 조건부

## 9. Exp11 (H10) 와의 결정적 대비

| 비교축 | **Exp11 (Mixed, H10)** | **Exp12 (Extractor, H11)** |
|--------|----------------------|---------------------------|
| 가설 | 강한 Judge → 약한 모델 보완 | 같은 모델 Role 분리/추가 → 입력 정리 |
| 모델 | A/B Gemma + **C Flash** | **모두 Gemma**, Extractor 신규 분리 |
| Δ acc | **−0.0811** (음수) | **+0.0500** (양수) |
| Cohen d | **−0.316** (small 음수) | **+0.323** (small 양수) |
| 메커니즘 | Tattoo schema mismatch + chain 단절 | 입력 정리 + cycle 1 안정화 |
| logic-02 | base 0.9 → mixed 0.0 (catastrophic) | base 0.3 → ext 0.6 (회복) |
| synthesis | +0.030 (약한 효과) | +0.050 (약한 효과) |
| 외부 API 비용 | $0.0843 (Flash) | $0 (local) |
| verdict | ⚠ 미결 (실효적 기각) | **⚠ 조건부 채택** |

→ **Role 축 진화 방향 명확**: 강화 (X) ≠ 분리/추가 (○). framework 의 다음 외부화 축 우선순위 결정 신호.

## 10. Stage 2C / Exp11 / Exp12 종합 — Role 축 정밀화 진화

| 가설 | 결과 | 메커니즘 |
|------|------|----------|
| H4 (Stage 2C) | ⚠ 조건부 채택 | A-B-C 시너지 (synthesis +0.140 회복) |
| H10 (Exp11) | ⚠ 미결 (실효적 기각) | 강한 Judge 가 약한 모델 self-discovery 방해 |
| **H11 (Exp12)** | **⚠ 조건부 채택** | **신규 Role 추가 — 입력 정리, catastrophic 회복** |

→ Role 축의 *다양화* (분리/추가) 가 framework 의 자연 진화. 강한 모델 도입은 비추천.

## 11. Stage 5 다음 의제 (Exp13+) 함의

본 결과 + Stage 2C / Exp11 종합:

| 후보 | 우선순위 | 사유 |
|------|---------|------|
| **Reducer Role** (Exp14 후보, Role 분리/추가 계열) | 🎯 상승 | Extractor 채택 신호 — Role 다양화 방향 검증 |
| **Search Tool** (Exp13 후보) | 중 | 큰 인프라 (FTS/tokenizer). Extractor 보다 후순위 (Mac 핸드오프 §2 의 Stage 5 SQLite 동기) |
| Mixed Intelligence 재시도 | 비추천 | Exp11 정반대 메커니즘. 별도 prompt 강화 plan 후 시점 |
| math-* use_tools 통일 | 보류 | 회귀 fix, 별도 plan |

→ **권장 Exp13 = Reducer Role** (Role 다양화 라인 연속) 또는 **Exp13 = Search Tool** (Tool 축 신규). 사용자 결정.

## 12. 한계

- **n=15 task paired** — 통계 검정력 부족. 단정적 채택 어려움
- **5 trial** — task 별 sample 작음
- **first_cycle_assertions = 0** 측정 결함 — Extractor 효과의 직접 메커니즘 (cycle 1 input 안정화) 측정 한계. 효과는 정확도/error mode 로만 간접 확인
- **synthesis-02 saturation 깨짐** (−0.20) — Extractor 의 negative case. 추가 분석 필요
- **Tool 축 미검증** — math-04 양쪽 0 (use_tools=False), Extractor 측정에 노이즈
- **외부 API 비교 부재** — Exp11 의 Flash 비용/시간 trade-off 와 직접 비교 불가 (다른 메커니즘)

## 13. 향후 보강 (본 plan 영역 외)

- Reducer Role (Exp14 후보) — Role 다양화 라인 연속
- Search Tool (Exp13 후보) — Tool 축 신규
- Extractor + Reducer 조합 (Exp15 후보) — 다중 Role 결합
- task 확대 (15 → 20+) — 통계 검정력 회복

## 14. 변경 이력

- 2026-05-04 v1: 초안. Stage 5 Exp12 Task 04 (사용자 직접 실행 2026-05-03~04) 마감 후 Architect 분석.
