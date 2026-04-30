---
type: plan
status: done
updated_at: 2026-04-30
slug: scorer-failure-label-reference
version: 1
author: Architect (Windows)
audience: Developer (Sonnet) + 사용자 검토 (위임 시 Architect default)
parent_strategy: handoff-to-windows-2026-04-30-followup-strategy.md (Stage 2B)
completed_at: 2026-04-30 (commit e84d943)
---

# Stage 2B — scorer / failure label reference 정리

## Description

Mac 핸드오프 §4.3 영역 — Stage 2A (인프라 정합성) 와 분리하여 score_answer / failure label 의 reference 만 단일화. Stage 3 (Exp11 plan 작성 시 Mixed Intelligence 또는 Search Tool 어느 쪽이든) 에서 표준화된 label 사용 + retrospective 분석 일관성 확보.

본 plan 의 동기:
- `experiments/measure.py` 의 score_answer_v0 / v2 / v3 의 변천 + 적용 범위가 여러 result.md / handoff 에 분산. 단일 reference 부재
- 실패 label (json_parse_fail / evidence_miss / wrong_synthesis / format_error / null_answer / connection_error / timeout) 이 ad-hoc 라벨링 — Exp10 v3 ABC JSON parse 분석 / Exp09 H9c / Stage 2C 의 ErrorMode (분석 helper) 등에서 다른 표현 사용
- 표준 enum + reference 가 있으면 Exp11+ plan / 분석 / 보고서 의 일관성 확보

본 plan 의 **명시 배제**:
- score_answer_v4 도입 (사용자 합의 — 본 plan 영역 외)
- 기존 결과 JSON 의 retroactive label 보강 (분석 시점 라벨링은 보존)
- 채점 알고리즘 자체 변경 (`measure.py` 변경 0)
- failure label 의 자동 분류 helper 강화 (Stage 2C 의 `classify_error_mode` 가 heuristic — 본 plan 은 enum + reference 만)

## Expected Outcome

1. `docs/reference/scoringHistory.md` (신규) — score_answer_v0 / v2 / v3 의 변천 + 적용 범위 + 결정 시점 단일 reference
2. `experiments/schema.py` 에 `FailureLabel` enum 신규 추가 — namingConventions.md §9.3 의 ErrorMode 와 정합 (단 하나가 표준, 다른 하나가 alias)
3. `docs/reference/failureLabels.md` (신규) — failure label 정의 + 기존 ad-hoc 라벨링 매핑 표 + 신규 작성 가이드
4. Stage 2C 의 `experiments/exp_h4_recheck/analyze.py` 의 `ErrorMode` enum 을 본 plan 의 `FailureLabel` 의 alias 로 통합 (정합성)

## Subtask Index

1. [task-01](./scorer-failure-label-reference-task-01.md) — `scoringHistory.md` 신규 (S, parallel_group A, depends_on: [])
2. [task-02](./scorer-failure-label-reference-task-02.md) — `FailureLabel` enum + `schema.py` 추가 (S, parallel_group B, depends_on: [])
3. [task-03](./scorer-failure-label-reference-task-03.md) — `failureLabels.md` 신규 + 기존 ad-hoc 라벨 매핑 표 (M, parallel_group B, depends_on: [02])
4. [task-04](./scorer-failure-label-reference-task-04.md) — Stage 2C 의 `ErrorMode` 통합 (S, parallel_group C, depends_on: [02])

### 의존성

```
Stage 1 (병렬):
  Group A: task-01 (scoringHistory)
  Group B: task-02 (FailureLabel enum) → task-03 (failureLabels.md)
                                       ↘ task-04 (Stage 2C ErrorMode 통합)
```

Group A 독립. Group B 의 task-02 가 enum 정의 → task-03 가 reference 작성 / task-04 가 Stage 2C 통합. 모두 plan-side, 사용자 직접 실행 0.

## Constraints

- 메인 단일 흐름 (브랜치 분기 금지)
- Architect 작성 + Developer 진행 + 사용자 위임 (결과 검증)
- `experiments/measure.py` / `score_answer_v0/v2/v3` 변경 0 — 본 plan 은 reference + enum 추가만
- `experiments/orchestrator.py` 변경 0
- `experiments/run_helpers.py` (Stage 2A 영역) 변경 0 — 본 plan 의 enum 은 `schema.py` 에 추가
- 기존 결과 JSON retroactive label 0
- `experiments/exp_h4_recheck/analyze.py` (Stage 2C 영역) — task-04 한정 alias 변경 (기능 변경 0)
- 영문 노트북 (`researchNotebook.en.md`) 변경 0 (본 plan 은 인프라 정리, 외부 노출 0)
- README 변경 0

## 결정 (Architect 직접 결정, 2026-04-30)

사용자 위임 (2026-04-30): "사용자 검토 의미 없음, Architect 분석이 더 정확". 본 plan 의 모든 결정 Architect default.

### 결정 1 — `FailureLabel` enum 위치 — **`experiments/schema.py` 확정**

`schema.py` 가 Tattoo / Assertion 등 schema 영역. failure label 도 result schema 의 일부라 정합. 별도 파일 (`experiments/labels.py`) 회피 — over-engineering.

### 결정 2 — `ErrorMode` (Stage 2C) vs `FailureLabel` 의 관계 — **alias 확정**

Stage 2C 의 `ErrorMode` 는 본 plan 의 `FailureLabel` 의 alias. 두 enum 의 value 가 동일. import 시:

```python
from experiments.schema import FailureLabel as ErrorMode  # alias
```

또는:
```python
from experiments.schema import FailureLabel
# Stage 2C 의 analyze.py 에서 ErrorMode 변수명을 FailureLabel 로 rename
```

→ task-04 에서 결정.

### 결정 3 — failure label 의 enum value naming — **SCREAMING_SNAKE_CASE 확정**

namingConventions.md §9.3 와 정합:
- `NONE`, `FORMAT_ERROR`, `WRONG_SYNTHESIS`, `EVIDENCE_MISS`, `NULL_ANSWER`, `CONNECTION_ERROR`, `PARSE_ERROR`, `TIMEOUT`, `OTHER`
- value (string) 은 소문자: `"none"`, `"format_error"`, ...

### 결정 4 — 기존 ad-hoc 라벨 retroactive 보강 — **0 (보존)**

Exp09 H9c 의 라벨 (`format_error 24`, `wrong_synthesis 6`, `evidence_miss 2`) 등은 분석 시점 라벨링 — 정보 손실 0 이라 보존. 신규 분석 (Stage 2C 등) 부터 표준 enum 사용.

## Non-goals

- score_answer_v4 도입 (별도 plan 후보)
- failure label 의 자동 분류 algorithm 강화 (Stage 2C 의 heuristic 그대로)
- `measure.py` / orchestrator / schema 의 dataclass 변경 (FailureLabel enum 추가만)
- 기존 result.md 의 ad-hoc 라벨 정정 (retroactive 보강 0)
- 영문 노트북 / README 변경

## Risks

- **Risk 1 — `schema.py` 에 enum 추가 시 기존 import 영향**: `from experiments.schema import Tattoo` 등 기존 import 와 충돌 0 (enum 은 신규 추가). 검증: task-02 의 Verification.
- **Risk 2 — Stage 2C 의 `ErrorMode` 와 통합 시 코드 변경**: Stage 2C 의 `analyze.py` 가 이미 `ErrorMode` 정의. task-04 에서 alias / rename 결정. 단순 1 import 변경.
- **Risk 3 — Sonnet 이 `measure.py` 를 임의 수정**: 본 plan 영역 외. Scope boundary 엄수.
- **Risk 4 — failure label 의 정의 모호성** (특히 `EVIDENCE_MISS` 의 자동 분류): 본 plan 은 enum + reference 만. 자동 분류 algorithm 은 Stage 2C 의 heuristic 그대로 — 후속 plan 후보.

## Sonnet (Developer) 진행 가이드

본 plan 도 Architect 작성 + Developer 그대로 진행. Developer 는:

1. **각 subtask 의 Step 순서대로**
2. **각 subtask 의 "Changed files" 만 수정**
3. **결정 1-4 default 사용** — 모두 Architect 확정
4. **Verification 명령 실행 + 결과 보고**
5. **Risk 발견 시 즉시 보고**
6. **Scope boundary 위반 직전이면 멈추고 보고**

## 변경 이력

- 2026-04-30 v1: 초안. Stage 2A 마감 (`c0e18c9`) 직후 Architect 작성. 사용자 위임 ("결정 사용자 검토 의미 없음, Architect 분석") 으로 결정 1-4 모두 Architect 확정.
