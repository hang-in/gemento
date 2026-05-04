# Parent Plan Template

`docs/plans/<slug>.md` 의 본문 형식. 모든 placeholder 채우고, 빈 섹션 금지.

```markdown
---
type: plan
status: draft
updated_at: <YYYY-MM-DD>
slug: <slug>
version: 1
author: Architect (<Windows|Mac>)
audience: Developer (Sonnet) + 사용자 검토 (위임 시 Architect default)
parent_strategy: <상위 전략 문서 경로 또는 생략>
---

# Stage <N> — <plan 제목>

## Description

<1-2 단락 — 동기, 가설, 이전 실험과의 연결>

**가설 H## 후보**: <가설 본문 한 줄>.

**조건**:
- baseline_<name>: <Role 별 모델 구성>
- treatment_<name>: <Role 별 모델 구성, 차이 명시>

**<이전 Stage> 종합**:
- ✅ <이전 결론 1>
- ✅ <이전 결론 2>
- 🎯 **본 plan H##** — <본 plan 의 위치>

## Expected Outcome

1. `<file path>` — <역할 한 줄>
2. `<file path>` (신규) — <역할 한 줄>
3. `<results json path>` × N
4. `docs/reference/exp##-<slug>-analysis-<TS>.md` (분석 보고서)
5. H## verdict + 문서 갱신 (researchNotebook 한·영 + 신규 result.md + README 조건부)

## Subtask Index

1. [task-01](./<slug>-task-01.md) — <한 줄 제목> (S/M/L, parallel_group A, depends_on: [])
2. [task-02](./<slug>-task-02.md) — <한 줄 제목> (S/M, parallel_group B, depends_on: [01])
3. [task-03](./<slug>-task-03.md) — <한 줄 제목> (M, parallel_group C, depends_on: [01, 02])
4. [task-04](./<slug>-task-04.md) — 실험 실행 (사용자 직접) — <task × condition × trial 합계> trial (L, parallel_group D, depends_on: [03])
5. [task-05](./<slug>-task-05.md) — 분석 + H## verdict + 문서 갱신 (M, parallel_group E, depends_on: [04])

### 의존성

\`\`\`
Stage 1 (plan-side):
  Group A: task-01 (<설명>)
       ↓
  Group B: task-02 (<설명>)
       ↓        ↓
  Group C: task-03 (<설명> — 01/02 의존)
       ↓
Stage 2 (사용자 직접):
  Group D: task-04 (<trial 수> trial, ~<시간>h 추정)
       ↓
Stage 3 (분석):
  Group E: task-05 (분석 + H## + 문서)
\`\`\`

## Constraints

- 메인 단일 흐름 (브랜치 분기 금지)
- Architect/Developer/Reviewer/사용자 분리 — Task 04 = 사용자 직접 실행
- `experiments/measure.py` / `score_answer_v0/v2/v3` 변경 0
- `experiments/orchestrator.py` 변경 = <범위 명시>. <이전 Exp 의 hook> 보존
- `experiments/schema.py` 변경 0
- `experiments/run_helpers.py` (Stage 2A) 변경 0
- `experiments/tasks/taskset.json` 변경 0
- 영문 노트북 Closed 추가만
- README 갱신은 사용자 결정

## 결정 (Architect 직접 결정 또는 사용자 결정, <YYYY-MM-DD>)

<사용자 위임 시 다음 한 줄 명시:>
사용자 위임 ("<사용자 발화 인용>") — 모든 결정 Architect default.

### 결정 1 — <제목> — **<값>** 확정

<근거 1-2 단락>

### 결정 2 — <제목> — **<값>** 확정

<근거>

<... 결정 N>

## Non-goals

- <본 plan 영역 외 1>
- <본 plan 영역 외 2>
- <후속 Exp 후보로 미루는 것>
- 외부 API 사용 (해당 시)
- score_answer_v# 도입 (해당 시)

## Risks

- **Risk 1 — <제목>**: <한 줄 본문>. <대응 방안>
- **Risk 2 — <제목>**: <한 줄 본문>. <대응 방안>
- **Risk 3 — <제목>**: <한 줄 본문>. <대응 방안>
- **Risk 4 — Stage 2C 결함 fix 보존**: 이전 Exp 의 cycle-by-cycle tattoo_history 저장 패턴 재사용. 단순 import.

## Sonnet (Developer) 진행 가이드

본 plan 도 Architect 작성 + Developer 그대로 진행:

1. 각 subtask 의 Step 순서대로
2. 각 subtask 의 "Changed files" 만 수정
3. 결정 1-N default 사용 (사용자 위임)
4. Verification 명령 + 결과 보고
5. Risk 발견 시 즉시 보고
6. Scope boundary 위반 직전이면 멈추고 보고
7. Task 04 = 사용자 직접 실행 — Sonnet 모델 호출 금지

## 변경 이력

- <YYYY-MM-DD> v1: 초안. <상위 컨텍스트 — 직전 Stage 마감 commit, 사용자 발화 등>
```

## 작성 시 주의

- **slug 일관성**: parent plan 의 frontmatter `slug` = 파일명 stem = subtask `parent_plan` = index.md 링크 = prompt 파일 prefix. 다섯 곳 동일.
- **결정 번호 의미**: 결정은 *사용자가 / Architect 가 위임받아* 한 선택. Architect 의 분석은 결정이 아니다.
- **Risk vs Constraint 구분**: Constraint = 변경 금지 영역 (확정). Risk = 발생 가능 문제 (불확정).
- **Sonnet 진행 가이드**: Sonnet 비위임 plan (Architect 직접 진행) 이면 이 섹션 생략 가능.
