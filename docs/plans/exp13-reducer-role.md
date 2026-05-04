---
type: plan
status: draft
updated_at: 2026-05-04
slug: exp13-reducer-role
version: 1
author: Architect (Windows)
audience: Developer (Sonnet) + 사용자 검토 (위임 시 Architect default) + 사용자 직접 실행 (Task 04)
parent_strategy: handoff-to-windows-2026-04-30-followup-strategy.md (Stage 5)
---

# Stage 5 — Exp13: Reducer Role (Role 다양화 라인 연속)

## Description

Stage 5 Exp12 (Extractor Role) 의 H11 ⚠ 조건부 채택 (Δ=+0.050 양수, catastrophic 영역 회복) 후, Architect 권장 — Role 분리/추가 라인 연속 검증.

**가설 H12 후보**: 신규 Role (Reducer) 가 ABC chain 의 final tattoo + final_answer 후보를 받아 *post-stage* 에서 final answer 를 정리/통합하면, keyword 매칭 정확도 + final answer 명료성 향상.

**조건**:
- baseline_abc: A/B/C 모두 Gemma 4 E4B (Stage 2C / Exp11 / Exp12 정합)
- reducer_abc: A→B→C → **Reducer (Gemma)** post-stage. Reducer 가 final tattoo 의 assertions + 원 final_answer 를 받아 정리한 새 final_answer 반환

**Stage 2C / Exp11 / Exp12 종합**:
- ✅ Stage 2C H4 ⚠ 조건부 채택 (synthesis +0.140 회복) 정합성
- ✅ Exp11 H10 ⚠ 미결 (실효적 기각) — 강한 모델 도입 비추천
- ✅ Exp12 H11 ⚠ 조건부 채택 (Δ +0.050 양수) — Role 분리/추가 안전한 진화 방향
- 🎯 **본 plan H12** — Role 다양화 라인 연속 (Extractor *입력 정리* + Reducer *출력 정리*)

**Extractor (Exp12) vs Reducer (본 plan) 의 대칭**:

| 측면 | Extractor (Exp12) | Reducer (Exp13) |
|------|-------------------|-----------------|
| 위치 | pre-stage (cycle 시작 전) | post-stage (cycle 종료 후) |
| 효과 | 입력 정리 (claims/entities prefix) | 출력 정리 (final_answer 재정리) |
| 호출 횟수 | 1 / trial | 1 / trial |
| 모델 | 동일 Gemma | 동일 Gemma |
| 메커니즘 | A 의 cycle 1 input 안정화 | C 결정 후 final answer 명료화 |

## Expected Outcome

1. `experiments/system_prompt.py` — `REDUCER_PROMPT` 신규 + `build_reducer_prompt(assertions, candidate_answer)` 함수
2. `experiments/orchestrator.py` — `run_abc_chain` 에 `reducer_post_stage: bool = False` 옵션 추가 (1-2 라인, default backward compat)
3. `experiments/exp13_reducer_role/run.py` (신규) — 2 condition (baseline_abc, reducer_abc) + cycle-by-cycle tattoo_history (Stage 2C 결함 fix 보존)
4. `experiments/exp13_reducer_role/results/exp13_baseline_abc.json` + `exp13_reducer_abc.json`
5. 분석 보고서 `docs/reference/exp13-reducer-role-analysis-<TS>.md`
6. H12 verdict + 문서 갱신 (researchNotebook 한·영 + 신규 result.md `exp-13-reducer-role.md` + README 조건부)

## Subtask Index

1. [task-01](./exp13-reducer-role-task-01.md) — `REDUCER_PROMPT` + `build_reducer_prompt()` (S, parallel_group A, depends_on: [])
2. [task-02](./exp13-reducer-role-task-02.md) — `run_abc_chain` 에 reducer_post_stage hook (S, parallel_group B, depends_on: [01])
3. [task-03](./exp13-reducer-role-task-03.md) — `exp13_reducer_role/run.py` (M, parallel_group C, depends_on: [01, 02])
4. [task-04](./exp13-reducer-role-task-04.md) — 실험 실행 (사용자 직접) — 15 task × 2 condition × 5 trial = 150 trial (L, parallel_group D, depends_on: [03])
5. [task-05](./exp13-reducer-role-task-05.md) — 분석 + H12 verdict + 문서 갱신 (M, parallel_group E, depends_on: [04])

### 의존성

```
Stage 1 (plan-side):
  Group A: task-01 (Reducer prompt 정의)
       ↓
  Group B: task-02 (orchestrator hook)
       ↓        ↓
  Group C: task-03 (run.py — 01/02 의존)
       ↓
Stage 2 (사용자 직접):
  Group D: task-04 (150 trial 실험, ~25h 추정)
       ↓
Stage 3 (분석):
  Group E: task-05 (분석 + H12 + 문서)
```

## Constraints

- 메인 단일 흐름 (브랜치 분기 금지)
- Architect/Developer/Reviewer/사용자 분리 — Task 04 = 사용자 직접 실행
- `experiments/measure.py` / `score_answer_v0/v2/v3` 변경 0
- `experiments/orchestrator.py` 변경 = `run_abc_chain` 의 `reducer_post_stage` 옵션 추가 1-2 라인 + post-stage 호출 로직 (5-10 라인). Exp11 의 c_caller 와 Exp12 의 extractor_pre_stage 보존
- `experiments/schema.py` 변경 0 — Tattoo schema 보존
- `experiments/run_helpers.py` (Stage 2A) 변경 0
- `experiments/tasks/taskset.json` 변경 0 (Stage 2C / Exp12 의 15 task 정합)
- 영문 노트북 Closed 추가만
- README 갱신은 사용자 결정

## 결정 (Architect 직접 결정, 2026-05-04)

사용자 위임 ("리듀서 롤 먼저 해보자, 작성해 줘") — 모든 결정 Architect default.

### 결정 1 — Reducer 모델 — **Gemma 4 E4B (동일)** 확정

Exp11 정반대 메커니즘 학습 + Exp12 Extractor 의 양수 결과 (같은 모델). 외부 API 0.

### 결정 2 — Reducer 입력 / 출력 schema — **assertions list + candidate answer → 정리된 final answer** 확정

```
Input:
  - assertions: [{"claim": "...", "confidence": 0.9}, ...] (final tattoo 의 active_assertions)
  - candidate_answer: 원 final_answer (C role 결정)

Output:
  - 정리된 final_answer (text 형식, JSON 아님 — keyword 매칭 위해 plain text 권장)
```

A 의 `final_answer` 와 호환 — measure.py:score_answer_v3 의 keyword 매칭이 그대로 동작.

### 결정 3 — 호출 시점 — **trial 종료 시 1회 (post-stage)** 확정

Extractor 의 pre-stage 와 대칭. cycle 별 호출 회피 (비용 8배). final tattoo 가 ABC chain 종료 후 확정된 시점에 1회.

### 결정 4 — task set / trial / cycles — **Stage 2C / Exp12 정합** 확정

- task: 15 (math 4 + logic 4 + synthesis 5 + planning 2)
- trial: 5
- max_cycles: 8

### 결정 5 — condition 구성 — **2 condition** (baseline_abc + reducer_abc) 확정

Exp12 와 같은 패턴. 단 Exp12 baseline_abc 결과 (mean=0.7500) 와 본 plan baseline_abc 의 cross-reference 분석 가능 (3 회차 baseline 안정성).

### 결정 6 — Reducer prompt 의 자율도 — **재정리만, 새 결론 추가 금지** 확정

Reducer 가 자기 추론으로 missing keyword 추가하면 false positive 위험. prompt 명시:

```
You may polish the candidate answer for clarity and ensure all key entities/numbers are explicitly stated. You MUST NOT change the core conclusion or add new factual claims not present in the assertions.
```

### 결정 7 — 메커니즘 측정 — **error mode + final_answer 길이 + keyword 출현** 확정

본 plan 의 효과 = final answer 의 명료성. 측정:
- error mode: NONE 비율 (Exp12 패턴)
- final_answer 길이 평균 (baseline vs reducer)
- task 의 essential keyword 출현 비율 (예: logic-02 의 "105", "inconsistent")

assertion turnover 는 본 plan 영역 외 (Reducer 가 cycle 안 변경 안 함, post-stage 만).

## Non-goals

- Search Tool / Graph Tool / Evidence Tool (Exp14+ 후보)
- Mixed Intelligence 재시도 (Exp11 정반대 메커니즘)
- Extractor + Reducer 조합 (Exp15 후보 — 본 plan 마감 후 검토)
- score_answer_v4 도입
- 외부 API 사용
- 새 task / 새 카테고리

## Risks

- **Risk 1 — Reducer 가 답을 *바꿈***: prompt 의 "do NOT change the core conclusion" 제약에도 Gemma 가 자기 추론 추가 가능. dry-run 시 logic-02 case 확인 — 원 답이 inconsistent 결론이면 Reducer 가 보존하는지
- **Risk 2 — Reducer JSON 응답 한계**: Reducer 출력은 plain text (final_answer) 라 JSON 아님 — Gemma 의 plain text 응답이 더 안정적 예상
- **Risk 3 — Extractor (Exp12) 의 negative case 재발**: synthesis-02 의 saturation 깨짐 (−0.20). Reducer 도 비슷한 패턴 가능 — 본 plan 의 task-05 분석에서 saturation 영역 별도 측정
- **Risk 4 — Reducer 가 keyword 추가 (false positive)**: prompt 강제 + dry-run 시 답변 표본 검증
- **Risk 5 — 비용/시간**: local Gemma 만, 외부 API 0. 시간 ~25h (baseline 12h + reducer 12.5h, Reducer 호출 ~30s × 75 trial 추가)
- **Risk 6 — Stage 2C 결함 fix 보존**: Exp12 의 cycle-by-cycle tattoo_history 저장 패턴 재사용. 단순 import.

## Sonnet (Developer) 진행 가이드

본 plan 도 Architect 작성 + Developer 그대로 진행:

1. 각 subtask 의 Step 순서대로
2. 각 subtask 의 "Changed files" 만 수정
3. 결정 1-7 default 사용 (사용자 위임)
4. Verification 명령 + 결과 보고
5. Risk 발견 시 즉시 보고
6. Scope boundary 위반 직전이면 멈추고 보고
7. Task 04 = 사용자 직접 실행 — Sonnet 모델 호출 금지

## 변경 이력

- 2026-05-04 v1: 초안. Stage 5 Exp12 마감 (`7f72394`) + 사용자 위임 ("리듀서 롤 먼저 해보자, 작성해 줘") 직후 Architect 작성. Mac 핸드오프 §2 의 Stage 5 진행 — Search Tool (Exp14+) 이전 Role 다양화 라인 연속.
