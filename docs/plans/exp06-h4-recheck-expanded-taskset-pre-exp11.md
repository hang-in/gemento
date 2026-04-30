---
type: plan
status: draft
updated_at: 2026-04-30
slug: exp06-h4-recheck-expanded-taskset-pre-exp11
version: 1
author: Architect (Windows)
audience: Developer (Sonnet) + 사용자 검토 + 사용자 직접 실행 (Task 04)
parent_strategy: handoff-to-windows-2026-04-30-followup-strategy.md (Stage 2C)
---

# Stage 2C — Exp06 H4 재검증 (확대 task set, Exp11 전 마감 의무)

## Description

H4 (Role 외부화 시너지 — A-B-C 역할 분리가 단일 에이전트 반복보다 우수하다) 의 verdict 가 ⚠ 미결 상태. Exp06 정합 비교 (45 vs 45 trial) 결과:
- v1: Solo 0.663 vs ABC 0.649 (Solo +0.015)
- v2/v3: Solo 0.967 vs ABC 0.900 (Solo +0.067)
- 9-task set 한정 결론, 통계적 유의성 미달, **확대 task set 재검증 필요**

**사용자 명시 (2026-04-30): Exp11 전 마감 의무**. Mixed Intelligence (Stage 3 Exp11 후보 — Role 축 강화 가설) 가 Role 시너지 미결 상태에서 Judge 강화로 풀리면 측정 정합성 흐려짐. 본 plan 이 H4 채택/기각 결론을 내고 Stage 3 의제를 명료화.

본 plan 의 핵심 ablation — 두 효과 분리:
- **다단계 효과**: Solo-1call (loop=1) vs Solo-budget (loop=N, 자기 반복)
- **역할 분리 효과**: Solo-budget (loop=N, 자기 반복) vs ABC (A→B→C 직렬)

이 두 격차를 분리하여 H4 ("역할 분리 단독 효과") 와 H1 ("다단계 효과") 을 명확히 구분. 직전 Exp06 정합 비교가 두 효과를 분리하지 못한 한계 극복.

## Expected Outcome

1. **확대 task set** — `experiments/tasks/h4_recheck_taskset.json` (신규) 또는 `experiments/tasks/taskset.json` 의 확장. 현 12 task + 신규 3 task (planning 2 + 1 추가 카테고리) = **15 task**
2. **3 condition 정의** — Solo-1call / Solo-budget / ABC. config + run 진입점 명세
3. **측정 인프라** (3 축):
   - `experiments/measure.py` 변경 0 — 별도 분석 helper
   - assertion turnover metric (Tattoo 의 cycle 별 assertion 추가/수정/삭제 카운트)
   - error mode classifier (Exp09 H9c 패턴 적용 — format_error / wrong_synthesis / evidence_miss / null_answer / connection_error)
4. **실험 실행** (사용자 직접) — 15 task × 3 condition × 5 trial = **225 trial**
5. **분석 보고서** + **H4 verdict 갱신** — 채택 / 기각 / 미결 결정 + researchNotebook 한·영 + result.md exp-06 갱신

## Subtask Index

1. [task-01](./exp06-h4-recheck-expanded-taskset-pre-exp11-task-01.md) — 신규 3 task 정의 + validate_taskset 통합 (M, parallel_group A, depends_on: [])
2. [task-02](./exp06-h4-recheck-expanded-taskset-pre-exp11-task-02.md) — 3 condition 정의 (Solo-1call / Solo-budget / ABC) + run 진입점 (M, parallel_group B, depends_on: [])
3. [task-03](./exp06-h4-recheck-expanded-taskset-pre-exp11-task-03.md) — assertion turnover + error mode classifier (분석 helper) (S, parallel_group C, depends_on: [])
4. [task-04](./exp06-h4-recheck-expanded-taskset-pre-exp11-task-04.md) — 실험 실행 (사용자 직접) — 15 × 3 × 5 = 225 trial (L, parallel_group D, depends_on: [01, 02, 03] + Stage 2A 마감)
5. [task-05](./exp06-h4-recheck-expanded-taskset-pre-exp11-task-05.md) — 분석 + H4 verdict 갱신 + 문서 통합 (M, parallel_group E, depends_on: [04])

### 의존성 (Stage 기반)

```
Stage 1 (병렬, plan-side 작업):
  Group A: task-01 (task 정의)
  Group B: task-02 (condition 정의)
  Group C: task-03 (측정 helper)
       │       │       │
       └───────┴───────┘
               ▼
Stage 2 (사용자 직접 실행):
  Group D: task-04 (225 trial 실험)
           ⚠ Stage 2A (healthcheck/abort + meta v1.0) 마감 필수 — 직전 사고 재발 차단
               │
               ▼
Stage 3 (분석 + verdict):
  Group E: task-05 (분석 + H4 verdict + 문서 갱신)
```

Group A/B/C 모두 plan-side (Architect/Developer) 작업이라 병렬 가능. Group D 는 사용자 단독. Group E 는 분석 + 문서 — Architect/Developer.

## Constraints

- 메인 단일 흐름 (브랜치 분기 금지)
- Architect/Developer/Reviewer/사용자 분리 — Task 04 는 **사용자 직접 실행** (메모리 정책 `feedback_agent_no_experiment_run.md`)
- `experiments/measure.py` / `score_answer_v0/v2/v3` 변경 0 (Stage 2B 영역, 본 plan 영역 외)
- `experiments/orchestrator.py` 변경 0 — ABC chain 구조 보존
- `experiments/schema.py` 변경 0 — Tattoo schema 보존 (assertion turnover 분석은 read-only)
- `experiments/tasks/taskset.json` 변경 정책 — 새 task 는 **별도 파일** (`h4_recheck_taskset.json`) 또는 기존 파일에 append. **사용자 결정 의존** (parent plan §사용자 결정 절)
- Stage 2A 마감 후 Task 04 진행 — 인프라 의존성. Stage 2A 의 healthcheck/abort + 결과 JSON meta v1.0 적용 후 실험 = 직전 Exp09 5-trial dilute 사고 재발 0
- 영문 노트북 Closed 추가만 정책 — Task 05 결과 보고에서 새 단락 추가만 (기존 영문 수치 변경 0)

## 사용자 결정 (확정, 2026-04-30 — C1~C4 사용자 답변)

본 plan 의 모든 결정 사항은 사용자 답변으로 확정 (이전 turn 의 C1~C4 응답).

### C1 — task 수 확대 — **task 수 확대 (i) 확정**

12 → 15 task. 단순 trial 수 확대 (ii) 회피 (직전 Exp09 5-trial dilute 사고 학습).

### C2 — 새 도메인 — **(d) 현 카테고리 + planning 1~2 추가 확정**

신규 3 task 구성:
- **planning task 2** — 다단계 분해/조정 task. Role 분리 (A 제안, B 비판, C 판정) 가 가장 명료하게 효과 보일 도메인
- **현 카테고리 추가 task 1** — math / logic / synthesis 중 1 카테고리 1 task. **사용자 결정 의존** (정확히 어느 카테고리 — Architect 권장: math 또는 logic, synthesis 는 이미 균형)

### C3 — Solo 정의 — **(iii) 둘 다 분리 측정 확정**

3 condition:
| condition | 정의 | loop budget | 비교 의미 |
|-----------|------|-------------|----------|
| Solo-1call | 단일 모델 단발 호출 (loop=1) | 1 | H1 baseline |
| Solo-budget | 같은 모델 자기 반복 (loop=N) | max_cycles=8 또는 15 | Exp06 Solo 패턴 — 다단계 효과 측정 |
| ABC | A (Proposer) → B (Critic) → C (Judge) 직렬 (loop=N) | max_cycles=8 또는 15 | 역할 분리 효과 측정 |

ablation 결과 해석:
- **다단계 효과** = Solo-budget − Solo-1call (H1 재확인)
- **역할 분리 단독 효과** = ABC − Solo-budget (H4 본 가설)
- **합산 효과** = ABC − Solo-1call

### C4 — 측정 metric — **(iv) 셋 다 확정**

3 축:
| metric | 정의 | 분석 helper |
|--------|------|------------|
| (i) **정확도** | mean acc (v3 채점) | 기존 measure.py |
| (ii) **assertion turnover** | Tattoo 의 cycle 별 assertion 추가/수정/삭제 변화량 | 신규 helper (task-03) |
| (iii) **error mode** | format_error / wrong_synthesis / evidence_miss / null_answer / connection_error 분류 | 신규 helper (task-03) |

3 축 모두 condition × task 별로 분석. 단일 정확도만 보면 직전 Exp06 정합 비교의 한계 (Solo +0.015 / +0.067 의 작은 격차) 그대로 — assertion turnover 가 Role 분리의 *질적* 차이를 잡아낼 가능성. error mode 는 H9c 패턴.

## 추가 사용자 결정 의존 사항 (plan 작성 진행 시 사용자 호출)

### 결정 5 — max_cycles N (Solo-budget + ABC 의 loop budget)

| 후보 | 사유 |
|------|------|
| 8 | Exp06 의 Solo avg 4.5 loops × 1.8 = ABC 가 더 많은 loop 소비. Exp06 정합 패턴 |
| 15 | Exp10 의 ABC 8-loop 결과 (78.3%) — 충분 budget 보장 |
| **8 권장** | Exp06 정합 비교 우선 — 직전 결과와 직접 비교 가능 |

Architect 추천: **8** (Exp06 정합).

### 결정 6 — 신규 1 추가 task 의 카테고리

| 후보 | 사유 |
|------|------|
| math | 4 → 5. 검증 가능 (validate_taskset 의 _validate_math_xx) |
| logic | 4 → 5. logic-04 천장 효과 확인된 영역 |
| synthesis | 4 → 5. 본 plan 의 H4 (역할 분리) 효과가 가장 명료할 영역 (다관점 종합) |
| **synthesis 권장** | H4 본질 — 역할 분리가 다관점 종합에서 가장 효과적 |

Architect 추천: **synthesis** (Role 분리 효과 명료).

### 결정 7 — task set 저장 위치

| 후보 | 사유 |
|------|------|
| 별도 파일 `h4_recheck_taskset.json` | 본 plan 한정 set 명시. 다른 실험에 영향 0 |
| 기존 `taskset.json` 에 append | 단일 source. 다른 실험 (Exp11+) 도 사용 가능 |
| **append 권장** | 신규 task 가 일반 task — 다른 실험 (Exp11 Mixed Intelligence) 도 동일 task set 사용 정합 |

Architect 추천: **기존 taskset.json 에 append** (12 → 15).

### 결정 8 — 영어 vs 한국어 task

현 12 task 가 영어 (한국어 답변 capability 측정 안 함). 신규 3 task 도 영어 통일 권장. **Architect 추천: 영어 통일**.

## Non-goals

- Exp11 Mixed Intelligence (Judge C 강한 모델 교체) — 본 plan 영역 외 (Stage 3/4 의 Exp11 plan)
- Search Tool / Graph Tool / Extractor Role / Reducer Role — 본 plan 영역 외
- score_answer_v4 도입 — 본 plan 영역 외
- 영문 README 외부 노출 톤 변경 — Task 05 결과가 H4 채택/기각 어느 결론이든 README 본문 갱신은 **사용자 별도 결정** (본 plan 자체는 result.md + researchNotebook 한·영 갱신까지)
- 12 task 의 기존 정답 / 채점 / 카테고리 변경 — Phase 1 후속에서 정정 완료
- 새 H 가설 추가 (H10+) — Stage 3 의제

## Risks

- **Risk 1 — 신규 3 task 의 정답 검증 결함** (Exp07 math-04 expected_answer 결함 사례). 대응: validate_taskset 의 _validate_xxx 추가 + 사용자 시각 검토 + planning task 의 정답은 외부 ground truth 또는 명시적 채점 기준
- **Risk 2 — Solo-budget 의 "자기 반복" 정의 모호성**: Solo 가 cycle 마다 자기 출력을 자기 입력으로 받는다 — 첫 cycle 의 단발 호출과 ABC 의 A 호출 차이 명료화 필요. Task 02 에서 명세
- **Risk 3 — 225 trial 실행 시간**: ABC 의 max_cycles=8 × 평균 21.6 calls/trial × 5 trial × 15 task × 3 condition. ABC 만 ~1500 model call. Exp10 의 8-loop ABC trial 당 8 min — 본 실험 ABC condition ~10 시간 예상. Solo-budget 도 비슷. Solo-1call 은 짧음. **사용자 직접 실행 시 분할 권장**
- **Risk 4 — assertion turnover metric 의 정의 모호성**: Tattoo 의 assertion list 가 cycle 별로 어떻게 변화하는지 (추가/수정/삭제) 의 분류 기준 명세 필요. Task 03 에서 정의
- **Risk 5 — Stage 2A 마감 의존**: Task 04 가 Stage 2A 의 healthcheck/abort 인프라 위에서 실행되어야 직전 사고 (Exp09 5-trial dilute) 재발 0. Stage 2A 미마감 시 Task 04 진행 금지
- **Risk 6 — H4 verdict 의 결론적 영향**: 본 plan 결과가 H4 기각이면 Mixed Intelligence (Stage 3 Exp11 Role 강화) 가설 동기 자체가 흔들림. 단 기각 자체가 의미 있는 결과 — Stage 3 의제 재검토 가능
- **Risk 7 — planning task 의 채점 어려움**: 다단계 분해 task 는 정답이 sequence 형태라 keyword 매칭이 어색할 수 있음. Task 01 에서 채점 기준 명세 (sub-step keyword group)

## Sonnet (Developer) 진행 가이드

본 plan 도 Architect 작성 + Developer 그대로 진행 패턴. Developer 는:

1. **각 subtask 의 Step 순서대로**. 임의 reorder 금지
2. **각 subtask 의 "Changed files" 만 수정**. 다른 파일 read-only
3. **결정 5/6/7/8 의 default 값 사용** (Architect 추천): max_cycles=8 / 신규 카테고리=synthesis / append to taskset.json / 영어 통일
4. **Verification 명령 실행 + 결과 보고**
5. **Risk 발견 시 즉시 보고** (Architect 호출 또는 사용자 호출). 임의 우회 금지
6. **Scope boundary 위반 직전이면 멈추고 보고**
7. **Task 04 는 Developer 가 실행 안 함** — 사용자 직접. Developer 는 명령 명세 + 보고서 placeholder 까지

## 변경 이력

- 2026-04-30 v1: 초안. handoff-to-windows-2026-04-30-followup-strategy.md (Mac, `d61e8ef`) Stage 2C 의 Architect plan 화. 사용자 (b) 결정 (Exp11 전 마감 의무) + C1-C4 답변 반영. 결정 5-8 은 Architect default 로 진행 — 사용자 검토 시 변경 가능.
