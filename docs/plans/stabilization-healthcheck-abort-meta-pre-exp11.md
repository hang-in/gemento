---
type: plan
status: draft
updated_at: 2026-04-30
slug: stabilization-healthcheck-abort-meta-pre-exp11
version: 1
author: Architect (Windows)
audience: Developer (Sonnet) + 사용자 검토
parent_strategy: handoff-to-windows-2026-04-30-followup-strategy.md (Stage 2A)
---

# Stage 2A — 작은 안정화 (healthcheck + abort + 결과 JSON meta 표준화)

## Description

Exp11 (주제 미정 — Mixed Intelligence 또는 Search Tool) 진입 전에, **직전 사고 (Exp09 5-trial 0점 dilute) 재발 방지** + **결과 JSON meta 표준화** 만 정리한다.

직전 사고 root cause:
- Windows 모델 서버 (`http://yongseek.iptime.org:8005`) 가 trial 4-5 동안 connection refused (WinError 10061) 반환
- `run_append_trials.py` 의 trial loop 가 error 여부 무관하게 결과를 그대로 append
- ABC orchestrator 의 try/except 가 connection 실패를 swallow 하여 `num_assertions=0, final_answer=null` 빈 trial 생성
- `analyze_stats.py` 가 빈 trial 의 score 를 0 으로 처리 → mean 이 dilute
- 결과: 5-trial mean 이 `3-trial mean × 3/5` 와 정확 일치 (모델 비결정성 / sampling 변동 0)

본 plan 의 목적:
1. trial 실행 도구가 connection 류 fatal error 를 즉시 abort 하고 빈 trial 저장을 거부하도록 정책 통일
2. 결과 JSON 의 top-level meta 를 표준화하여 향후 분석 / 비교 / (장기) DB import 시 정규화 비용 절감

본 plan 의 **명시 배제** (사용자 합의된 "작은 B" 전략):
- SQLite full ledger / 10-table schema 통합 / 기존 Exp00~10 결과 JSON 의 retroactive import
- FTS / CJK / 형태소 분석 / vector DB / Chroma / graph memory
- LLM diary / sync server / cross-device sync / tattoo lifecycle manager
- tool registry 일반화 / score_answer_v4 도입
- README 외부 노출 톤 변경

## Expected Outcome

1. `experiments/run_helpers.py` (신규) — `classify_trial_error` / `is_fatal_error` / `check_error_rate` / `build_result_meta` 4 함수 + `TrialError` enum
2. `experiments/exp09_longctx/run_append_trials.py` — fatal error 즉시 abort + 저장 직전 error 비율 검사 통합 (proof-of-concept)
3. 모든 `experiments/exp**/run.py` (multi-trial 도구) — 동일 healthcheck/abort 패턴 적용 (또는 도구별 trial loop 구조 차이로 fallback 시 인라인)
4. 결과 JSON top-level meta 표준 (`schema_version="1.0"`) — `model{name,engine,endpoint}` / `sampling_params{temperature,top_p,max_tokens,seed}` / `scorer_version` / `taskset_version` (git short hash) / `started_at` / `ended_at`
5. `experiments/exp09_longctx/analyze_stats.py` 등 analyze 스크립트 — 신규 schema 와 v0 (schema_version 부재) 양쪽 호환
6. `docs/reference/resultJsonSchema.md` (신규) — 결과 JSON schema reference 문서
7. dry-run 통합 검증 — 1 task × 1 trial 짧은 run 으로 (a) 신규 meta 필드 표시 (b) connection 실패 시 abort 동작 둘 다 확인

## Subtask Index

1. [task-01](./stabilization-healthcheck-abort-meta-pre-exp11-task-01.md) — `run_helpers.py` 신규 + `run_append_trials.py` 통합 (S, parallel_group A, depends_on: [])
2. [task-02](./stabilization-healthcheck-abort-meta-pre-exp11-task-02.md) — 모든 multi-trial 도구 healthcheck 확장 (M, parallel_group A, depends_on: [01])
3. [task-03](./stabilization-healthcheck-abort-meta-pre-exp11-task-03.md) — 결과 JSON meta 표준화 (helper + schema reference) (M, parallel_group B, depends_on: [])
4. [task-04](./stabilization-healthcheck-abort-meta-pre-exp11-task-04.md) — analyze 스크립트 backward-compat (S, parallel_group B, depends_on: [03])
5. [task-05](./stabilization-healthcheck-abort-meta-pre-exp11-task-05.md) — dry-run 통합 검증 (S, parallel_group C, depends_on: [02, 04])

### 의존성 (Stage 기반)

```
Stage 1 (병렬):
  Group A:                          Group B:
    task-01 (helper + run_append)    task-03 (meta helper + schema 문서)
       │                                │
       ▼                                ▼
    task-02 (모든 run.py 적용)        task-04 (analyze backward-compat)
       │                                │
       └──────────────┬─────────────────┘
                      ▼
              Stage 2 (단독):
                task-05 (dry-run 검증)
```

Group A 직렬 (helper 도입 → 도구 확장), Group B 직렬 (meta 정의 → analyze 호환). Task 05 가 합류.

## Constraints

- 메인 단일 흐름 (브랜치 분기 금지)
- Architect/Developer/Reviewer/사용자 분리 — 본 plan 의 코드 변경은 **Sonnet (Developer) 가 plan 문서 그대로 따라 진행**. 사용자 결정 의존 사항은 별도 절에 분리하여 Developer 가 임의 결정하지 않도록 함
- `experiments/measure.py` / `score_answer_v0/v2/v3` 변경 0 (별도 plan: Stage 2B)
- `experiments/orchestrator.py` 변경 0 — orchestrator 의 try/except swallow 자체는 본 plan 영역 외 (실험 파이프라인 측 healthcheck 가 정합)
- `experiments/schema.py` 의 기존 dataclass / TypedDict 변경 0 — 신규 meta 는 별도 type 으로 추가
- 기존 결과 JSON (Exp00~10) backward compat 유지 — schema_version 부재 = "0" 으로 암묵 처리. retroactive 보강 0
- `experiments/tasks/*.json` 변경 0 (Phase 1 후속에서 정정 완료)
- README / researchNotebook 변경 0 (본 plan 은 인프라 정리. 외부 노출 톤 영향 0)
- 영문 노트북 Closed 추가만 정책 — 본 plan 결과 보고 시 추가 1 단락 정도만

## 사용자 결정 의존 사항 (Architect 가 사용자에게 호출하여 확정)

본 plan 진행 전 사용자 결정 필수:

### 결정 1 — healthcheck/abort 정책 옵션 (Mac §4.1 의 (a)/(b)/(c)/(d))

| 옵션 | 정의 | trade-off |
|------|------|----------|
| (a) | 매 N (예: 10) trial 마다 healthcheck (sentinel 1 trial) | 정확하지만 trial 추가 비용 |
| (b) | 단일 trial 의 connection 류 fatal error 즉시 abort | 보수적. 일시적 네트워크 hiccup 도 abort |
| (c) | 연속 K (예: 3) 회 error 시 abort | 관대. K-1 trial 은 dilute 위험 |
| (d) | 저장 직전 trial 별 `error is not None` 비율이 임계값 (예: 30%) 초과 시 저장 거부 + warning | 사후 안전망 |

**Architect 추천**: **(b) + (d) 조합**.
- (b) 가 직전 사고 패턴 (20/20 connection refused) 을 즉시 차단
- (d) 는 (b) 가 미처 잡지 못한 mixed error 패턴 (timeout / parse / ...) 의 사후 안전망
- (a) / (c) 는 후속 plan 으로 보류 — sentinel task 정의 / K 값 튜닝이 별도 작업

**사용자 호출 사유**: 보수적 abort (b) 가 일시적 네트워크 hiccup 도 차단하므로 사용자 선호 확인 필요. 또는 사용자가 (c) 의 관대 정책을 선호할 가능성.

### 결정 2 — error 비율 임계값 (옵션 (d) 의 threshold)

기본 권장: **0.30** (전체 trial 중 30% 이상이 error 면 결과 저장 거부)

대안:
- 0.10 (엄격) — 1/10 만 fail 해도 거부
- 0.50 (관대) — 절반 미만 fail 까지 허용

직전 사고 (40% trial fail) 기준 0.30 이 차단 + 정상 run 의 일시적 fail (10~20%) 은 통과. 사용자 검토.

### 결정 3 — `experiments/run_helpers.py` 의 위치 + 모듈명

| 후보 | 장단 |
|------|------|
| `experiments/run_helpers.py` | 직관적, 기존 `experiments/measure.py` 와 같은 위치. **추천** |
| `experiments/_health.py` | underscore 로 internal 명시 |
| `experiments/utils/run_helpers.py` | 패키지화 — 작은 helper 라 over-engineering |

Architect 추천: **`experiments/run_helpers.py`**. Developer 가 임의 변경 금지.

## Non-goals

- 본 plan 영역 외 (사용자 합의된 "작은 B" 전략 명시 배제):
  - SQLite full ledger / 10-table schema 통합
  - 기존 Exp00~10 결과 JSON 의 retroactive meta 보강 (신규 run 만 적용)
  - FTS / CJK / 형태소 분석 / vector DB / graph memory
  - LLM diary / sync server / cross-device sync
  - tattoo lifecycle manager / tool registry 일반화
  - score_answer_v4 도입
  - scorer version / failure label reference 문서 정리 (별도 plan: **Stage 2B**)
  - README / researchNotebook 외부 노출 갱신 (변경 영향 0)
  - 새 H 가설 추가
  - orchestrator.py 의 try/except 동작 변경

## Risks

- **Risk 1 — Subtask 02 의 도구 확장 적용 비용**: `experiments/exp**/run.py` 의 trial loop 구조가 도구별로 다를 수 있음. helper 일관 적용 어려우면 도구별 인라인 fallback. Subtask 02 의 Risk 절 참조.
- **Risk 2 — backward-compat 깨짐**: schema_version 부재 (구 결과) 의 호환을 Subtask 04 에서 명시적으로 처리하지 못하면 analyze 스크립트 회귀. Subtask 04 의 Verification 에서 직전 결과 (Exp09 3-trial / Exp10 v3) 로 dry-run 필수.
- **Risk 3 — sampling_params 의 도구별 차이**: `lmstudio_client.py` / `gemini_client.py` / 다른 client 의 sampling_params 표현 방식 차이로 표준화 helper 가 client 별 분기 필요. Subtask 03 의 Risk 절 참조.
- **Risk 4 — fatal error 분류의 false positive**: `connection_error` 외 transient 한 timeout / dns lookup 도 fatal 로 분류되면 정상 run 의 일시적 hiccup 까지 abort. Subtask 01 에서 분류 패턴을 보수적으로 시작 + 후속 plan 에서 튜닝.
- **Risk 5 — Sonnet (Developer) 의 임의 확장**: plan 외 영역 (orchestrator.py / measure.py 등) 손대지 않도록 각 subtask 의 "Scope boundary" 절 엄수. 위반 시 Reviewer 단계에서 차단.

## Sonnet (Developer) 진행 가이드

본 plan 은 Architect 가 작성하고 Developer 가 그대로 따라 진행한다. Developer 는:

1. **각 subtask 의 "Step 1, 2, ..." 순서대로 진행**. 임의 reorder 금지
2. **각 subtask 의 "Changed files" 목록만 수정**. 다른 파일은 read-only
3. **사용자 결정 의존 사항** (위 §사용자 결정 의존 사항) 의 옵션은 plan parent 의 default 값 사용 — 사용자가 본 plan 검토 시 변경하면 그에 맞춰 진행
4. **Verification 명령 실행 + 결과 보고**. 직접 사용자에게 명령 실행 결과를 출력으로 보고
5. **Risk 발견 시 즉시 보고** (Architect 호출 또는 사용자 호출). 임의 우회 금지
6. **Scope boundary 위반 직전이면 멈추고 보고**. 본 plan 영역 외 파일 수정이 정당하다고 판단되면 사용자 호출 — 임의 진행 금지

## 변경 이력

- 2026-04-30 v1: 초안. handoff-to-windows-2026-04-30-followup-strategy.md (Mac, `d61e8ef`) Stage 2A 의 Architect plan 화. 사용자 의도 (Haiku Judge / 시간 vs 성능 trade-off) 는 Stage 3 plan 에서 별도 반영.
