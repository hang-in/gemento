---
type: reference
status: done
updated_at: 2026-04-30
canonical: true
---

# Failure Label 표준 reference

> trial result 의 failure / success 분류 표준. 도입 plan: `scorer-failure-label-reference` (Stage 2B).
> Python enum: `experiments/schema.py:FailureLabel`. Stage 2C 의 `experiments/exp_h4_recheck/analyze.py:ErrorMode` 는 본 enum 의 alias.

## 1. 표준 enum 값

| enum | value (str) | 정의 | 자동 분류 가능? |
|------|-------------|------|----------------|
| `NONE` | `"none"` | 정답 (acc_v3 ≥ 0.5 또는 task 별 기준) | ✅ (acc_v3 기반) |
| `FORMAT_ERROR` | `"format_error"` | JSON parse / schema 위반. final_answer 가 dict 형식 아니거나 malformed | ✅ (Stage 2A `TrialError.PARSE_ERROR` 의 일부 + final_answer null 의 일부) |
| `WRONG_SYNTHESIS` | `"wrong_synthesis"` | 형식은 OK 인데 내용 틀림. acc < 0.5 + final_answer 길이 > 10 | ✅ (heuristic, Stage 2C `classify_error_mode`) |
| `EVIDENCE_MISS` | `"evidence_miss"` | evidence_ref 누락 또는 잘못된 출처. 본 reference 도입 시점 자동 분류 미구현 — 수동 라벨링 권장 | ❌ (Critic Tool 도입 시 자동화) |
| `NULL_ANSWER` | `"null_answer"` | final_answer 가 None / 빈 문자열. ABC orchestrator 의 swallow 패턴 (Exp09 5-trial dilute 사고) 의 핵심 | ✅ (직접 비교) |
| `CONNECTION_ERROR` | `"connection_error"` | 모델 서버 connection refused / WinError 10061 등. Stage 2A `TrialError.CONNECTION_ERROR` 와 동기 | ✅ (Stage 2A `classify_trial_error`) |
| `PARSE_ERROR` | `"parse_error"` | JSON parse fail. Stage 2A `TrialError.PARSE_ERROR` 와 동기 | ✅ (Stage 2A) |
| `TIMEOUT` | `"timeout"` | ReadTimeout 등. Stage 2A `TrialError.TIMEOUT` 와 동기 | ✅ (Stage 2A) |
| `OTHER` | `"other"` | 미분류 | (분류 어려운 잔여) |

## 2. Stage 2A `TrialError` 와의 관계

`experiments/run_helpers.py:TrialError` 는 *trial loop 측의 fatal abort 결정용* enum. 본 `FailureLabel` 은 *분석 측의 retrospective 분류용* enum. 의미적 동기:

| TrialError (Stage 2A) | FailureLabel (Stage 2B) | 사용 영역 |
|----------------------|------------------------|----------|
| `NONE` | `NONE` 또는 `WRONG_SYNTHESIS` 또는 `NULL_ANSWER` (acc_v3 따라 분기) | run loop vs analyze |
| `CONNECTION_ERROR` | `CONNECTION_ERROR` | run loop fatal abort vs analyze 라벨 |
| `TIMEOUT` | `TIMEOUT` | 동일 |
| `PARSE_ERROR` | `PARSE_ERROR` | 동일 |
| `MODEL_ERROR` | `OTHER` | 모델 응답 자체 error (4xx/5xx) — 분석 시 OTHER |
| `OTHER` | `OTHER` | 동일 |

→ run loop 시 `TrialError` 사용, 분석 시 `FailureLabel` 사용. 통합 금지 — 영역 다름.

## 3. 기존 ad-hoc 라벨 매핑

본 reference 도입 *이전* 의 result.md / handoff 의 라벨링 (retroactive 변경 0):

### Exp09 H9c (`docs/reference/results/exp-09-longctx.md` §"에러 모드")

| 기존 표현 | 매핑 (FailureLabel) |
|-----------|---------------------|
| `format_error` (24, solo_dump) | `FORMAT_ERROR` |
| `wrong_synthesis` (6, rag_baseline / 3, abc_tattoo) | `WRONG_SYNTHESIS` |
| `evidence_miss` (2, abc_tattoo) | `EVIDENCE_MISS` |

### Exp10 v3 ABC JSON parse 분석 (`docs/reference/exp10-v3-abc-json-fail-diagnosis.md`)

| 기존 표현 | 매핑 |
|-----------|------|
| `fence_unclosed` (3) | `PARSE_ERROR` (또는 `FORMAT_ERROR`) |
| `empty` (1) | `NULL_ANSWER` |
| `truncate` (0) | — |

### Exp10 §4.5 reliability (`docs/reference/results/exp-10-reproducibility-cost.md` §4.5)

| 기존 표현 | 매핑 |
|-----------|------|
| `JSON parse fail` (gemma_8loop 4건) | `PARSE_ERROR` |
| `null` (gemma_1loop 11건) | `NULL_ANSWER` |
| `timeout` (gemini_flash 4건) | `TIMEOUT` |

### Exp09 5-trial drop 분석 (`docs/reference/exp09-5trial-drop-analysis-2026-04-30.md`)

| 기존 표현 | 매핑 |
|-----------|------|
| `WinError 10061` (rag/solo trial 4-5: 20/20 each) | `CONNECTION_ERROR` |
| `num_assertions=0, final_answer=null` (abc trial 4-5: 20/20) | `NULL_ANSWER` (ABC orchestrator swallow 의 결과) |

→ 위 모두 *분석 시점 라벨링 그대로 보존* (retroactive 변경 0). 신규 분석 시 표준 enum 사용.

## 4. 신규 분석 / plan 작성 가이드

신규 분석 helper 또는 result.md 작성 시:

1. `from experiments.schema import FailureLabel` import
2. `FailureLabel.NULL_ANSWER` 등 enum 사용 (string literal `"null_answer"` 직접 사용 회피)
3. 표 / 보고서의 column header: enum value (소문자 snake_case) 사용
4. 자동 분류 미구현 항목 (`EVIDENCE_MISS`) 은 수동 라벨링 + disclosure 명시

## 5. 향후 확장 (본 reference 영역 외)

- `EVIDENCE_MISS` 자동 분류 — Critic Tool / Evidence Tool 도입 시 (conceptFramework §5)
- `WRONG_SYNTHESIS` 의 sub-classification (계산 오류 vs 추론 오류 vs 출처 오류) — 별도 plan
- 다국어 응답 분류 — 별도 plan

→ 모두 본 plan (Stage 2B) 영역 외. 사용자 합의 "작은 B" 전략.

## 6. 변경 이력

- 2026-04-30 v1: 초안. Stage 2B (`scorer-failure-label-reference`) plan 의 task-03 결과. 분산된 ad-hoc 라벨 표준화.
