---
type: reference
status: done
updated_at: 2026-04-30
canonical: true
---

# H4 재검증 — Metric 정의

## 1. 측정 3 축 (사용자 결정 4 — iv 셋 다)

### 1.1 정확도 (existing)

`measure.py:score_answer_v3`. 변경 0.

### 1.2 assertion turnover (신규)

각 trial 의 Tattoo history (cycle 별 assertion list) 에서:
- **added**: 신규 추가된 assertion 수 (cycle N+1 에 있는데 N 에 없음)
- **modified**: 같은 id 인데 내용 바뀐 assertion 수
- **deleted**: cycle N 에 있는데 N+1 에 없음
- **final_count**: 마지막 cycle 의 assertion 수

`experiments/exp_h4_recheck/analyze.py:count_assertion_turnover` 로 산출.

**의미**:
- Solo-1call: 0 (single cycle, 변화 측정 불가)
- Solo-budget: 같은 모델 자기 반복 — turnover 가 적을수록 조기 수렴 (Exp06 의 avg 4.5 loops 패턴)
- ABC: A→B→C 비판 루프 — turnover 가 클수록 역할 분리가 active 하게 다양성 추가

→ ABC 의 turnover_modified 가 Solo-budget 보다 유의미하게 크면, "B 의 비판이 A 의 assertion 을 수정시킨다" 의 직접 증거.

### 1.3 error mode (신규)

| 분류 | 정의 |
|------|------|
| NONE | 정답 (acc_v3 ≥ 0.5) |
| FORMAT_ERROR | JSON parse / schema 위반 |
| WRONG_SYNTHESIS | 형식 OK 인데 내용 틀림 (acc < 0.5, len > 10) |
| EVIDENCE_MISS | evidence_ref 누락 또는 잘못된 출처 (현 heuristic 미구현, 향후 보강) |
| NULL_ANSWER | final_answer 가 None / 빈 문자열 |
| CONNECTION_ERROR | Stage 2A `TrialError.CONNECTION_ERROR` 와 동기 |
| PARSE_ERROR | Stage 2A `TrialError.PARSE_ERROR` |
| TIMEOUT | Stage 2A `TrialError.TIMEOUT` |
| OTHER | 미분류 |

`experiments/exp_h4_recheck/analyze.py:classify_error_mode` 로 산출. Exp09 H9c 와 호환.

## 2. ablation 정의

| 측정 | 의미 |
|------|------|
| solo_budget − solo_1call | 다단계 효과 (H1 재확인) |
| abc − solo_budget | 역할 분리 단독 효과 (H4 본 가설) |
| abc − solo_1call | 합산 효과 |

H4 채택 조건 (Architect 권장):
- abc − solo_budget ≥ +0.05 (정확도)
- 또는 ABC 의 turnover_modified ≥ Solo-budget × 1.5 (질적 차이)
- 통계적 유의성 검정 — Wilcoxon signed-rank (15 task, paired)

## 3. 향후 확장

- evidence_ref 정합성 검사 — Critic Tool 도입 시 보강
- assertion 의 confidence 변화 — Tattoo 의 confidence 필드 활용 (현 미사용)
