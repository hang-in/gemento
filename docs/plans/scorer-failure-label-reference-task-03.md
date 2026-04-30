---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: scorer-failure-label-reference
parallel_group: B
depends_on: [02]
---

# Task 03 — `failureLabels.md` 신규 + 기존 ad-hoc 라벨 매핑 표

## Changed files

- `docs/reference/failureLabels.md` — **신규**. failure label 정의 + 기존 ad-hoc 라벨 매핑 표 + 신규 작성 가이드

신규 1, 수정 0.

## Change description

### 배경

`FailureLabel` enum (task-02 도입) 의 reference 문서. 기존 result.md / handoff 의 ad-hoc 라벨링 (Exp09 H9c / Exp10 §4.5 reliability / Stage 2C analyze 등) 의 매핑 표 + 신규 분석 시 표준 사용 가이드.

### Step 1 — `docs/reference/failureLabels.md` 신규 작성

다음 내용 그대로:

```markdown
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
```

위 내용 그대로 작성.

### Step 2 — `docs/reference/index.md` 갱신

본 reference 를 "설계 / 규약" 섹션에 등재:

```markdown
- [scoringHistory.md](scoringHistory.md) — 채점 시스템 변천 (v0/v2/v3 적용 범위) — Stage 2B
- [failureLabels.md](failureLabels.md) — failure label 표준 reference (FailureLabel enum + 기존 매핑) — Stage 2B
```

(scoringHistory 는 task-01 영역 — 본 task 는 failureLabels 만 추가)

## Dependencies

- task-02 마감 (FailureLabel enum 정의)
- 패키지: 없음 (마크다운 + 짧은 검증 명령)

## Verification

```bash
# 1) failureLabels.md 신규 + canonical
.venv/Scripts/python -c "
text = open('docs/reference/failureLabels.md', encoding='utf-8').read()
assert 'canonical: true' in text
assert 'FailureLabel' in text
assert 'TrialError' in text  # 매핑 표
print('verification 1 ok: failureLabels.md 신규')
"

# 2) §1 의 enum value 가 schema.py:FailureLabel 와 일치
.venv/Scripts/python -c "
from experiments.schema import FailureLabel
text = open('docs/reference/failureLabels.md', encoding='utf-8').read()
for label in FailureLabel:
    assert label.value in text, f'{label.value} missing in failureLabels.md'
print('verification 2 ok: enum value 일치')
"

# 3) §3 매핑 표 — 기존 result.md 의 ad-hoc 라벨 keyword 모두 포함
.venv/Scripts/python -c "
text = open('docs/reference/failureLabels.md', encoding='utf-8').read()
keywords = ('format_error', 'wrong_synthesis', 'evidence_miss', 'WinError', 'fence_unclosed', 'JSON parse fail')
for kw in keywords:
    assert kw in text, f'{kw} mapping missing'
print('verification 3 ok: 매핑 표 완성')
"
```

3 명령 모두 정상.

## Risks

- **Risk 1 — 매핑 표의 정확성**: 기존 result.md / handoff 의 ad-hoc 라벨 cnt 값과 매핑 의미가 정합한지 검증 필수. Verification 3 의 keyword 확인 + 사용자 위임 (Architect 시각 검토)
- **Risk 2 — `EVIDENCE_MISS` 의 자동 분류 미구현 disclosure**: 본 reference 의 §1 / §4 명시 — 향후 Critic Tool 도입 시 자동화 예정
- **Risk 3 — 기존 result.md 의 ad-hoc 라벨 retroactive 변경 시도**: 본 plan 영역 외. Scope boundary 엄수

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/schema.py` (task-02 영역) — `FailureLabel` 변경 금지
- `experiments/run_helpers.py` (Stage 2A 영역) — `TrialError` 변경 금지
- 기존 result.md (`exp-XX-*.md`) — ad-hoc 라벨 변경 금지 (retroactive 0)
- 기존 reference 문서 — 변경 금지
- Stage 2C `experiments/exp_h4_recheck/analyze.py` — task-04 영역
- 결과 JSON (모두 read-only)

`docs/reference/index.md` 갱신은 허용 (Step 2).
