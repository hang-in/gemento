---
name: gemento-plan-create
description: gemento 프로젝트의 새 plan 문서 (parent + N subtask) 와 Sonnet 진행 프롬프트를 일관된 frontmatter / 명명 규칙 / 의존성 다이어그램과 함께 작성하고 docs/plans/index.md 의 Active 섹션에 등록한다. Architect 가 새 실험 / 인프라 / 리팩토링 plan 을 만들 때 사용. "plan 작성", "Stage N 시작", "Exp## plan", "subtask 분할" 등을 사용자가 언급할 때 적극 트리거. plan 의 frontmatter (type=plan/plan-task, parent_plan, parallel_group, depends_on, slug) 와 명명 규칙 (camelCase 또는 kebab-case 일관) 과 index.md 등록 누락을 자동으로 강제한다.
---

# gemento-plan-create

Architect 의 가장 빈도 높은 작업 — plan 문서 셋 작성 — 을 표준화. parent + subtask 의 frontmatter 일관성, 명명 규칙, 의존성 다이어그램, index.md 등록을 자동 강제.

## 언제 실행하는가

다음 신호 중 하나라도:

- 사용자가 "plan 작성", "새 Stage 시작", "Exp## plan", "subtask 로 나누자" 등을 명시
- Architect 가 직접 새 실험 / 인프라 / 리팩토링 작업의 plan 문서를 만들기로 결정
- 기존 plan 마감 후 사용자가 "다음 plan", "후속 plan" 을 요청

## 사용자에게서 확보해야 할 정보

진행 전 다음을 사용자 또는 대화 컨텍스트에서 확보:

1. **slug** — 파일명 stem. kebab-case. 예: `exp14-search-tool`, `stabilization-meta-v2`.
2. **plan 제목** — 예: "Stage 5 — Exp14: Search Tool"
3. **목적/가설** — 1-2 문장
4. **subtask 개수** — 보통 3~6
5. **subtask 별 핵심**: 제목 한 줄 + 변경 파일 + parallel_group (A/B/C/...) + depends_on
6. **Stage 번호** — index.md 의 Active 섹션 표기용
7. **사용자 결정 사항** — 모델, task 수, trial 수, condition 구성 등 (Architect 위임 시 default 명시)
8. **Risk 후보** — 3-6 개. 각각 한 줄
9. **Sonnet 위임 여부** — Yes/No (보통 Yes — Architect 작성, Sonnet 진행)

부족하면 사용자에게 한 번에 묶어 질의.

## 처리 순서

### 1. 사전 검증

- `docs/plans/<slug>.md` 가 이미 존재하면 — 사용자에게 덮어쓸지 / 새 slug 쓸지 질의
- slug 가 kebab-case 가 아니거나 너무 길면 — 사용자에게 시정 제안

### 2. parent plan 작성 — `docs/plans/<slug>.md`

`references/parent_template.md` 를 참고. frontmatter 의무 필드:

```yaml
---
type: plan
status: draft
updated_at: <YYYY-MM-DD>  # 오늘 날짜
slug: <slug>
version: 1
author: Architect (<host>)  # Windows or Mac
audience: <Developer (Sonnet) + 사용자 검토 ...>
parent_strategy: <상위 전략 문서 경로, 없으면 생략>
---
```

본문 구조 (필수):
- `# <제목>`
- `## Description` — 가설/동기 1-2 단락
- `## Expected Outcome` — 번호 매김 list, 산출물 명시
- `## Subtask Index` — 번호 매김 list, 각 항목에 `(<size>, parallel_group <X>, depends_on: [...])` 메타
- `### 의존성` — ASCII 다이어그램 (Stage 1/2/3 + Group A→B→C)
- `## Constraints` — 변경 금지 영역, 외부 의존 한계
- `## 결정 N — <제목> — **<값>** 확정` — 사용자 위임 시 모든 결정 Architect default 라고 명시
- `## Non-goals` — 본 plan 영역 외 명시
- `## Risks` — 번호 매김 list, 각 항목 한 줄 본문 + 대응 방안
- `## Sonnet (Developer) 진행 가이드` — Sonnet 위임 시 7-8 항목
- `## 변경 이력` — 초안 entry 1개 (날짜 + 작성 컨텍스트)

### 3. subtask 작성 — `docs/plans/<slug>-task-NN.md` × N

`NN` 은 0-padded (`01`, `02`, ...). frontmatter 의무 필드:

```yaml
---
type: plan-task
status: pending  # 또는 draft
updated_at: <YYYY-MM-DD>
parent_plan: <slug>
parallel_group: <A/B/C/...>
depends_on: [<NN>, ...]  # 다른 task 번호. 없으면 빈 list []
---
```

본문 구조 (필수):
- `# Task NN — <제목>`
- `## Changed files` — 신규/수정 파일 list. 각 파일에 한 줄 설명. 마지막에 "신규 N, 수정 M" 요약
- `## Change description` — `### 배경` + `### Step 1` + `### Step 2` ...
- `## Dependencies` — 다른 task 번호 + 외부 패키지 + 기존 파일 (read-only)
- `## Verification` — `bash` 코드 블록 N 개. syntax check + import test + behavior test. 모든 명령이 사용자가 그대로 실행 가능해야 함
- `## Risks` — 본 task 한정 risk 3-5 개
- `## Scope boundary` — 본 task 에서 **수정 금지** 파일 명시. parent plan 의 Constraints 와 일관

`references/subtask_template.md` 참고.

### 4. index.md 등록 — `docs/plans/index.md`

`## Active` 섹션 맨 위에 한 줄 추가:

```markdown
- [<slug>.md](<slug>.md) — **Stage N (Exp##)**: <한 줄 요약>. <사용자 결정 / 위임 / 진행 신호 정보>. Sonnet 진행 프롬프트: `docs/prompts/YYYY-MM-DD/<slug>Start.md`
```

기존 entry 와 형식 일관 — 다른 line 들의 패턴을 grep 으로 확인 후 맞춘다.

### 5. (선택) Sonnet 진행 프롬프트 — `docs/prompts/YYYY-MM-DD/<slug>Start.md`

Sonnet 위임 시 작성. self-contained 프롬프트:

frontmatter:
```yaml
---
type: prompt
status: ready
updated_at: <YYYY-MM-DD>
for: Sonnet (Developer)
plan: <slug>
purpose: <한 줄>
prerequisites: <어떤 Stage 가 마감되어야 하는가>
---
```

본문 (필수 섹션):
1. 핵심 규칙 (5-7 개 — Plan 그대로, scope 확장 금지, 사용자 결정 변경 금지, ...)
2. 컨텍스트 동기 (`git pull --ff-only` + prerequisite 검증 명령)
3. 읽어야 할 plan 파일 list (parent + subtask N 개)
4. 사용자 결정 표 (parent plan 의 결정 N 표 mirror)
5. 진행 순서 (parent plan 의 의존성 다이어그램 mirror)
6. 각 subtask 진행 패턴 (read → Step → Verification → commit → 사용자 confirm)
7. 사용자 호출 분기 (Verification 실패 / Scope boundary 위반 직전 / Risk 발견 / 사용자 직접 task / README 갱신 결정)
8. (사용자 직접 실행 task 가 있으면) 특이사항 — Sonnet 모델 호출 금지 명시
9. 분석 task 특이사항 (placeholder 0 의무, 문서 갱신 list)
10. 본 plan 마감 신호 (검증 명령 셋)
11. 부수 사항 (영문 노트북 Closed-append-only / README 결정 / 변경 금지 영역)
12. 다음 단계 (Architect 가 본 plan 마감 후 결정할 후보 N 개)

`references/sonnet_prompt_template.md` 참고.

## 명명 규칙 강제

다음 규칙 위반 시 사용자에게 시정 제안:

- **slug**: `exp##-<descriptive-kebab-case>` 형식 (실험), 또는 `<feature-kebab-case>` (인프라/리팩토링)
- **task 번호**: `01`, `02`, ... — 0-padded 두 자리
- **parallel_group**: `A`, `B`, `C`, ... — 알파벳 대문자, 의존성 순서대로
- **depends_on**: list of 0-padded 두 자리 문자열, 빈 list `[]` 명시 (omit 금지)
- **prompt 파일**: `<slug>Start.md` 또는 `<slug>Continue.md` 등 camelCase 접미사

## verdict 와의 차이

본 스킬 = plan **시작** 시점.  
`gemento-verdict-record` 스킬 = plan **마감** 시점 (verdict 기록 + index.md Active→Recently Done 이동).

본 스킬은 index.md 의 **Active** 섹션 등록만 한다 — Recently Done 이동은 verdict-record 가 담당.

## 외부에서 변경 금지

- `experiments/**/*.py` (코드 — 본 스킬은 plan 문서만 작성)
- `experiments/**/results/*.json`
- `docs/reference/researchNotebook.md` / `.en.md` (verdict-record 영역)
- `docs/reference/conceptFramework.md`
- `README.md` / `README.ko.md`

## 종료 시 보고

```
plan 작성 완료 — <slug>

생성:
- docs/plans/<slug>.md (parent)
- docs/plans/<slug>-task-NN.md × <N> (subtask)
- docs/plans/index.md (Active 섹션 등록)
- docs/prompts/YYYY-MM-DD/<slug>Start.md (Sonnet 위임 시)

다음 단계:
- 사용자 검토 → Sonnet 세션에 진행 프롬프트 복붙
- 또는 Architect 직접 진행 (위임받은 결정 사항 그대로)
```
