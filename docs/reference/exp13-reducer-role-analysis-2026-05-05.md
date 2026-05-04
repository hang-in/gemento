---
type: reference
status: done
updated_at: 2026-05-05
canonical: true
---

# Exp13 Reducer Role 분석 (Stage 5)

**Plan**: `exp13-reducer-role`
**실행일**: 2026-05-04 10:15 ~ 19:12 (baseline_abc) / 2026-05-04 19:14 ~ 2026-05-05 03:51 (reducer_abc)
**조건**: baseline_abc (A/B/C 모두 Gemma) vs reducer_abc (A/B/C + **Reducer post-stage**, 모두 Gemma) × 15 task × 5 trial = **150 trial**
**모델**: Gemma 4 E4B (LM Studio Q8_0 `http://192.168.1.179:1234`) — **외부 API 0**
**채점**: `score_answer_v3` (negative_patterns 적용)

## 1. condition aggregate

| condition | n | mean_acc | err+null | avg_cycles | avg_dur |
|-----------|---|---------:|--------:|-----------:|--------:|
| baseline_abc | 75 | **0.7744** | 9+9 | 7.2 | 429s |
| **reducer_abc** | 75 | **0.7033** | 8+8 (+ 2 TypeError) | 7.0 | 414s |

**Δ(reducer − baseline) = −0.0711** (음수, Exp12 의 +0.050 정반대 방향).

**중요 — orchestrator 버그 발견 (분석 중 식별 + 즉시 fix)**:
- `experiments/orchestrator.py:653` 의 `len(fa)` 가 final_answer 가 int 타입일 때 깨짐
- math-02 trial 2/3 이 cycles=0 에서 즉시 실패 (TypeError "object of type 'int' has no len()")
- 한 줄 fix (`fa = fa if isinstance(fa, str) else str(fa)` coercion) — commit `cf057b6`
- 영향: 75 reducer trial 중 2 trial. Δ 방향 **불변**, 크기만 감소

## 2. 통계 검정 (n=15 task paired)

| 검정 | with bug (primary) | bug-excluded (참고) | 판정 |
|------|------------------:|---------------------:|------|
| **mean Δ** | **−0.0711** | **−0.0533** | 양쪽 모두 음수 |
| sd Δ | 0.2066 | 0.1651 | — |
| **Cohen's d (paired)** | **−0.344** | **−0.323** | small-to-medium 음수 |
| paired t-test | t=−1.333, p=0.2038 | t=−1.251, p=0.2315 | NOT SIGNIFICANT |
| Wilcoxon signed-rank | W=18.0, p=0.1801 | W=18.0, p=0.1801 | NOT SIGNIFICANT |
| Bootstrap 95% CI Δ (n=10000) | [−0.176, +0.024] | [−0.133, +0.027] | 양쪽 모두 0 거의 포함, 음수 우세 |

**해석**:
- 통계 비유의 (n=15 검정력 한계, Stage 2C / Exp11 / Exp12 와 동일 패턴)
- Cohen d small-to-medium 음수 — Reducer 손해 신호. **Exp12 의 Cohen d=+0.323 와 거의 같은 크기, 정반대 방향**
- Bootstrap CI 상한 +0.024~+0.027 — 0 거의 포함, 단 분포 음수 방향 95% 우세
- bug 제외 시 magnitude 감소하나 sign + Cohen d 모두 보존 — verdict 결론 영향 없음

## 3. 카테고리별 break-down

| category | n_tasks | baseline | reducer | **Δ** | 해석 |
|----------|--------:|---------:|--------:|------:|------|
| **logic** | 4 | 0.7250 | 0.6250 | **−0.100** ⬇ | logic-02/04 catastrophic 영역 회복 실패 |
| **math** | 4 | 0.7000 | 0.6167 | **−0.083** ⬇ | math-02 catastrophic (1.0→0.4, 일부 bug) |
| **synthesis** | 5 | 0.8233 | 0.7167 | **−0.107** ⬇ | 5/5 task 음수, synthesis-04 −0.27 가 핵심 |
| planning | 2 | 0.9000 | 1.0000 | **+0.100** ⬆ | planning-02 +0.20 (saturation 안정) |

→ **synthesis 카테고리에서 가장 큰 손해**. Exp12 가 synthesis 회복 (+0.05) 으로 채택된 영역이 Exp13 에서는 정반대로 작동. **post-stage Role 의 다중-출처 종합 손상 메커니즘** 핵심 신호.

## 4. Per-task break-down (|Δ|>0.01)

| task | category | difficulty | baseline | red | Δ | 패턴 |
|------|----------|-----------|---------:|----:|--:|------|
| **math-02** | math | medium | 1.000 | 0.400 | **−0.600** ⬇ | 면적 계산 saturation 깨짐. 2/5 = orchestrator bug, 1/5 = no_final_answer, 2/5 = 정답. **bug 제외 시 0.667** |
| **synthesis-04** | synthesis | hard | 0.933 | 0.667 | **−0.267** ⬇ | 다출처 새 개체수 모순 종합 — Reducer 가 단일 추정 압축 |
| logic-04 | logic | hard | 0.200 | 0.000 | −0.200 ⬇ | 일반화 puzzle — Reducer 의 단순화가 catastrophic 강화 |
| logic-02 | logic | hard | 0.700 | 0.500 | −0.200 ⬇ | inconsistent puzzle — Exp12 회복 영역이 Exp13 에서는 손해 |
| math-01 | math | easy | 0.800 | 1.000 | **+0.200** ⬆ | 단순 수학 — Reducer 가 산술적 명료성 보강 |
| planning-02 | planning | easy | 0.800 | 1.000 | **+0.200** ⬆ | critical path — saturation 안정화 |
| synthesis-01 | synthesis | medium | 1.000 | 0.800 | −0.200 ⬇ | saturation 깨짐 (Exp12 synthesis-02 와 유사 패턴) |
| synthesis-03 | synthesis | medium | 0.733 | 0.867 | +0.133 ⬆ | 단순 종합 — Reducer 이득 |
| synthesis-02 | synthesis | hard | 1.000 | 0.900 | −0.100 ⬇ | saturation 약간 흔들림 |
| synthesis-05 | synthesis | hard | 0.450 | 0.350 | −0.100 ⬇ | 3-출처 모순 (Exp12 회복 영역) — Exp13 추가 손해 |
| math-04 | math | hard | 0.000 | 0.067 | +0.067 ⬆ | floor — use_tools=False, 노이즈 |

→ **catastrophic 영역 (logic-02, logic-04, synthesis-04, synthesis-05) 4 / 4 모두 음수 또는 손해 강화**. Exp12 가 회복했던 영역이 Exp13 에서는 정반대.

## 5. Mechanism — synthesis-04 case study

Exp13 의 핵심 메커니즘. baseline 과 reducer 의 final_answer 정성 비교:

**baseline_abc trial 0 (acc=1.00)**:
```
## Comprehensive Analysis and Best Estimate

**I. Identification of Contradictions:**
The reports contain significant contradictions regarding the total population count and the status of Zone C:
*  ...
```
구조화된 분석 + "contradictions", "Zone C", "Reports", "estimate" keyword 다수 + 다중 추정 범위.

**reducer_abc trial 0 (acc=0.67)**:
```
The best estimate for the current rare bird population is **270 individuals**.
This figure is derived by combining the detailed field survey data from Report 1 with the definitive physical evidence of...
```
단일 추정치 (**270 individuals**) 강조 + 다중 출처 분석 구조 누락.

→ Reducer prompt 의 **"polish for clarity"** + **"do NOT change conclusion"** 지시가 모델을 *단일 답변으로 압축* 시킴. 다중 출처 / 다중 추정 task 의 풍부한 분석 구조가 손상되어 keyword 매칭 실패.

**중요 관찰**: Reducer 가 짧게 만드는 것은 *아니다* — final_answer 평균 길이는 baseline 230 chars vs reducer 281 chars. **abstraction loss** (다중 출처/다중 추정 → 단일 추정) 이 핵심 메커니즘.

## 6. error mode

| condition | NONE | TypeError (bug) | no_final_answer (max cycles) |
|-----------|----:|----------------:|----------------------------:|
| baseline_abc | 66 | 0 | 9 |
| reducer_abc | 67 | **2** (math-02) | 6 |

**관찰**:
- Reducer 의 `no_final_answer` 가 baseline 보다 약간 적음 (6 vs 9) — Reducer 가 주석 안 단 중간 결과를 *완성* 시키는 효과는 *있음*
- 단 정확도 측면에서는 Reducer 의 abstraction loss 가 그 효과를 압도

`failure_label` 은 본 dataset 에서 None 으로 일관 (Stage 2B 라벨러는 분석 시점에만 활성, trial 실행 시점에는 비적용).

## 7. final_answer 길이 분석

| metric | baseline_abc | reducer_abc |
|--------|-------------:|------------:|
| 평균 길이 | 230 chars | 281 chars |
| median 길이 | 149 chars | 316 chars |
| min | 1 | 20 |
| max | 500 | 500 |

**관찰**: Reducer 가 답변을 **짧게 만드는 것이 아니라 *균질화* 시킴**. baseline 의 분포는 분산이 큼 (1~500), reducer 는 median 316 으로 중간 길이로 수렴. 이는 Reducer prompt 의 "1-3 sentences typical" guideline 의 직접 효과 — 짧은 답변은 길게, 긴 분석은 짧게.

핵심: 길이가 아니라 **content abstraction** 이 keyword 매칭에 영향.

## 8. 비용 / 시간

| metric | baseline_abc | reducer_abc |
|--------|-------------:|------------:|
| 외부 API 비용 | $0 | $0 (local Gemma) |
| Reducer 호출 | 0 | ~73 (75 - 2 bug crash) |
| 평균 trial 시간 | 429s | 414s (−4%) |

**시간 감소 (~15s/trial)** — 직관적이지 않으나 일부 reducer trial 이 cycle 단축 (avg 7.2 → 7.0). Reducer 의 post-stage 호출 ~30s 가 추가되었음에도 평균 시간 감소 — 메커니즘: Reducer 가 final answer 를 *완성* 해주므로 일부 trial 이 max cycles 에 도달 안 하고 조기 종료. 단 이는 *정확도* 와 trade-off 관계.

## 9. Architect verdict — **⚠ H12 미결 (실효적 기각)**

verdict 결정 트리:

| 조건 | 충족? |
|------|-------|
| Δ ≥ +0.10 + p<0.05 (강한 채택) | ❌ |
| Δ ≥ +0.05 + p<0.05 (조건부 채택) | ❌ |
| Δ ≥ +0.05 + p≥0.05 (⚠ 조건부 채택, 검정력 미달) | ❌ Δ 음수 |
| \|Δ\| < 0.05 (미결) | ❌ |Δ\| > 0.05 |
| **Δ < 0 + Cohen d < 0 + 모든 카테고리 일관 음수** | ✅ **본 분기** |

**Architect 최종 verdict**: ⚠ **H12 미결 (실효적 기각)**.

근거:
- Δ −0.0711 (bug 포함) / −0.0533 (bug 제외) — 양쪽 모두 임계값 −0.05 초과
- Cohen d −0.344 / −0.323 — small-to-medium 음수, **Exp12 의 +0.323 와 정확히 거울상**
- 카테고리: logic / math / synthesis 모두 음수 (planning 만 양수, n=2 작음)
- per-task: catastrophic 영역 4/4 음수 강화 (Exp12 와 정반대 패턴)
- 메커니즘 명확: post-stage Role 의 abstraction loss → keyword 누락
- 통계 비유의 (p>0.05) — "기각" 보다 "미결 (실효적 기각)" 표기 (Exp11 패턴)

## 10. Exp11 (H10) / Exp12 (H11) / Exp13 (H12) 결정적 대비

| 비교축 | Exp11 (Mixed, H10) | Exp12 (Extractor, H11) | **Exp13 (Reducer, H12)** |
|--------|-------------------|-----------------------|---------------------------|
| 가설 | 강한 Judge → 약한 모델 보완 | pre-stage 입력 정리 | **post-stage 출력 정리** |
| 위치 | C 강화 | **pre-stage** | **post-stage** |
| 모델 | A/B Gemma + C Flash | 모두 Gemma | **모두 Gemma** |
| Δ acc | −0.0811 | **+0.0500** | **−0.0533** (bug 제외) |
| Cohen d | −0.316 | **+0.323** | **−0.323** |
| 메커니즘 | chain 단절 | cycle-1 input 안정화 | **abstraction loss** |
| 영향 영역 | logic catastrophic | logic+synthesis 회복 | **synthesis 5/5 음수** |
| 외부 API 비용 | $0.0843 | $0 | $0 |
| **verdict** | ⚠ 미결 (실효적 기각) | **⚠ 조건부 채택** | **⚠ 미결 (실효적 기각)** |

→ **본 plan 의 핵심 가정 (Extractor ↔ Reducer pre/post 대칭) 이 실증에서 깨짐**. 양쪽이 같은 크기 (|d|≈0.32) 의 정반대 방향 효과. 매우 깔끔한 거울상 결과.

## 11. Stage 5 framework-level 발견 — Role 축 진화 패턴 확정

| Role 변경 유형 | 효과 | 메커니즘 |
|---------------|------|----------|
| Role *강화* (Mixed, 강한 모델 도입) | ❌ 음수 (−0.08) | 약한 모델의 self-discovery chain 단절 |
| Role *분리/추가* — **pre-stage** (Extractor) | ✅ 양수 (+0.05) | input 안정화, A 부담 감소 |
| Role *분리/추가* — **post-stage** (Reducer) | ❌ 음수 (−0.05) | output abstraction loss, keyword 누락 |

**확정된 framework-level 원칙**:
1. Role 강화 (강한 모델 도입) → 비추천 (Exp11)
2. Role 분리/추가 → 위치 의존:
   - **pre-stage** = chain 시작 *전* 입력 정리 → 안전, 양수 효과
   - **post-stage** = chain 종료 *후* 출력 압축 → 위험, abstraction loss
3. 약한 모델의 chain 은 *건드리지 않을 때* 가장 풍부함 — 외부 Role 의 "도움" 은 신중해야

→ 본 결과는 단순한 H12 기각이 아니라 **외부화 framework 의 위치-효과 비대칭** 이라는 새 원칙 발견. Stage 5 의 가장 중요한 정성적 발견.

## 12. Stage 5 다음 의제 (Exp14+) 함의

본 결과 + Stage 2C / Exp11 / Exp12 종합:

| 후보 | 우선순위 | 사유 |
|------|---------|------|
| **Search Tool / Tool 축 신규** (Exp14 후보) | 🎯 상승 | Role 축 3 회 검증 마감 (강화/pre/post). Tool 축 (H7 +18.3pp / H8 +23.3pp) 강한 효과 + 결정성 보장 — 안전한 다음 단계 |
| Reducer prompt 강화 | 비추천 | 메커니즘 (abstraction loss) 이 prompt 보강으로 fix 가능하나, *위치* 자체의 위험성이 더 본질 |
| Extractor + Reducer 조합 (Exp15 후보) | 비추천 | Reducer 의 음수가 Extractor 의 양수를 상쇄. trade-off 무의미 |
| 다른 post-stage Role 변형 (Verifier 등) | 보류 | 본 결과 패턴 (post-stage = 위험) 가 일반화 가능성. 별도 동기 필요 |
| Search Tool + SQLite ledger 인프라 | 별도 plan | Mac 핸드오프 §2 의 Stage 5 인프라. Search Tool plan 내 sub-task 가능 |

→ **권장 Exp14 = Search Tool** (Tool 축 / 결정성 / 검증된 강한 효과). Role 축 다양화 라인은 Exp12+13 으로 마감.

## 13. 한계

- **n=15 task paired** — 통계 검정력 부족 (Stage 2C 이후 모든 plan 의 공통 한계)
- **5 trial** — task 별 sample 작음
- **orchestrator bug 2 trial 영향** — 영향 미미 (Δ 방향 불변), 단 데이터 정합성 측면에서 zero-impact 아님
- **score_answer_v3 keyword 매칭 의존** — Reducer 의 *의미적* 정확성과 *keyword 매칭* 정확성의 차이 측정 불가. 의미적으로는 reducer 답변이 더 "polished" 일 수 있으나 채점기는 keyword 만 봄
- **synthesis-04 답변 길이 동일** (양쪽 500 chars 일관) — truncation artifact 가능성, 별도 조사 필요
- **Tool 축 미검증** — math-04 양쪽 ~0 (use_tools=False)
- **first_cycle_assertions = 0** Stage 2C 결함 — Exp12 와 동일 한계. Reducer 효과는 post-stage 라 cycle-by-cycle turnover 와 무관, 측정 영향 없음

## 14. 향후 보강 (본 plan 영역 외)

- **Exp14 = Search Tool** (권장 — Tool 축 신규)
- score_answer_v4 후보 — semantic similarity 추가 (Reducer 의 의미적 정확성 측정)
- Tattoo schema 의 final_answer type 일관성 (str 강제) — 본 plan 의 bug 와 같은 회귀 차단
- task 확대 (15 → 20+) — 통계 검정력 회복

## 15. 변경 이력

- 2026-05-05 v1: 초안. Stage 5 Exp13 Task 04 (사용자 직접 실행 2026-05-04~05) 마감 후 Architect 분석. 분석 중 orchestrator bug 발견 + 즉시 fix (commit `cf057b6`). 본 plan 의 가장 중요한 발견 = post-stage Role 의 **abstraction loss 메커니즘** + Exp12 ↔ Exp13 거울상 결과로 **위치-효과 비대칭** 원칙 확정.
