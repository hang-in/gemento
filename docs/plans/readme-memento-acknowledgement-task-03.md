---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: readme-memento-acknowledgement
parallel_group: A
depends_on: []
---

# Task 03 — `researchNotebook.md` 분할·재구조화 + H1~H9 학술 주석

## Changed files

- `docs/reference/researchNotebook.md` (전체, 723줄)
  - line 1~5 frontmatter — `updated_at` 갱신, 분할 구조 명시 (frontmatter에 `parts: [closed, active]` 같은 메타 추가 권고)
  - line 9~15 헤더 영역 — 분할 구조 안내 단락 추가
  - line 26~40 § 핵심 가설 표 (Closed) — H1 첫 등장 위치에 학술 주석 추가
  - line 65~640 § 실험 기록 (Closed) — Part 1 마커로 감쌈
  - line 642~686 § 채점 시스템 변천 + § 종합 발견 (Closed) — Part 1에 포함
  - line 689~720 § 현재 상태 및 다음 단계 (Active) — Part 2 마커로 감쌈

새 파일 없음.

## Change description

### Step 1 — frontmatter / 헤더 갱신

기존 frontmatter (line 1~5):

```yaml
---
type: reference
status: in_progress
updated_at: 2026-04-25
---
```

`updated_at`을 본 task 작업일로 갱신. `status`는 `in_progress` 유지 (Active 파트가 계속 갱신되므로).

frontmatter 직후 또는 line 9~15 사이에 분할 구조 안내 단락 추가:

```markdown
> **이 노트의 구조 (2026-04-25 분할 적용)**
>
> - **Part 1: Closed Findings** — 종결된 실험 결과(Exp00~09)와 가설 판정(H1~H9c). 추가 실험이 나오면 **항목을 append만 하고 기존 내용은 수정하지 않습니다**. 영문 미러: [`researchNotebook.en.md`](./researchNotebook.en.md).
> - **Part 2: Active Research** — 진행 중 가설, 열린 질문, 다음 실험 후보. 계속 갱신됩니다. 영문 번역 없음(설계상).
```

### Step 2 — H1 첫 등장 위치 학술 주석

line 26~28 *"### 핵심 가설"* 표 직전에 한 줄:

```markdown
> *H1–H9는 외부화 축에 대해 *순차 번호를 매긴 가설*들입니다 — 통계학의 H₀(영가설) / H₁(대립가설)과는 다른 의미입니다.*
```

(Developer 판단으로 위치 미세 조정 가능 — 표 위가 가독성 좋음)

### Step 3 — Part 1 / Part 2 마커 삽입

**Part 1 시작** — line 16 *"## 프로젝트 개요"* 직전(또는 그 위치)에:

```markdown
---

# Part 1 — Closed Findings

> 이 파트는 종결된 실험 결과와 가설 판정만 포함합니다. 새 실험이 추가될 때 **항목을 append만 하고 기존 내용은 수정하지 않는다**는 원칙을 따릅니다. 영문 미러는 [`researchNotebook.en.md`](./researchNotebook.en.md)입니다.
```

**Part 1 포함 범위**: line 16(프로젝트 개요) ~ line 686(종합 발견의 마지막 표).

**Part 2 시작** — line 689 *"## 현재 상태 및 다음 단계"* 직전에:

```markdown
---

# Part 2 — Active Research

> 이 파트는 진행 중 가설, 열린 질문, 다음 실험 후보를 다룹니다. **계속 갱신됩니다**. 영문 번역은 설계상 두지 않습니다 — 종결되면 Part 1으로 이동합니다.
```

기존 line 689 헤더 `## 현재 상태 및 다음 단계`는 그대로 유지 (Part 2 헤더 *아래의* 첫 ## 섹션).

### Step 4 — 분류 모호한 항목 처리

researchNotebook의 자연스러운 분할은 line 689 (`## 현재 상태 및 다음 단계`) 이전·이후. 그러나 일부 모호 영역이 있을 수 있음:

- line 642~663 § 채점 시스템 변천 — **Closed**로 분류 (v1→v2 전환은 종결됨)
- line 665~686 § 종합 발견: E4B 능력 프로파일 — **Closed**로 분류 (확정된 아키텍처 원칙)
- line 689~720 § 현재 상태 및 다음 단계 — **Active**로 분류 (열린 질문 16개 포함)

기준: *"이 내용은 새 실험이 나오면 갱신되는가?"* 갱신 → Active, 그렇지 않음 → Closed.

### Step 5 — 가설 라벨 및 판정 변경 금지

H1~H9c의 *라벨 자체*와 *판정*은 본 task에서 변경 *금지*. README의 H1~H9 표(task-01)와 어긋남 방지.

*허용*: 학술 주석 한 줄 추가 (Step 2)와 Part 1/2 분할 마커 삽입 (Step 3).

### Step 6 — RQ 병기 옵션 (선택)

각 H 소제목에 RQ(Research Question) 병기는 *옵션*. Developer 판단으로 가능 — 예: `H1 (RQ1) — [Orchestrator 외부화] ...`. 단 H 라벨 자체 변경 금지. 본 task에서 선택하지 않아도 OK (영문판도 H 라벨 그대로 유지).

### Step 7 — Part 2 안내 메시지

line 689의 새 Part 2 헤더 직후에 *"이 파트는 영문 번역되지 않음"* 안내가 명시되어야 함 (Step 3에서 정의). Developer는 이 메시지가 누락되지 않도록 점검.

## Dependencies

- 없음 (parallel_group A, depends_on 없음)
- task-01과 같은 group A이지만 *다른 파일* 수정 — 병렬 가능
- 외부 패키지 추가 없음

## Verification

```bash
# 1. researchNotebook의 Part 1 / Part 2 마커 존재
grep -c "^# Part 1\|^# Part 2" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.md
# 기대: 2

# 2. H1~H9c 라벨 보존 (변경 금지)
grep -cE "^\| H[1-9]" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.md
# 기대: 11 (H1, H2, H3, H4, H5, H6, H7, H8, H9a, H9b, H9c)

# 3. 학술 주석 등장
grep -c "H₀\|H_0\|영가설\|대립가설\|statistical" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.md
# 기대: 1 이상

# 4. Part 1 안내 단락 (append-only 원칙)
grep -c "append만 하고 기존 내용은 수정하지 않는다\|append만 하고\|append-only" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.md
# 기대: 1 이상

# 5. Part 2 안내 (영문 번역 없음)
grep -c "영문 번역.*없\|영문 번역.*설계상\|not translated\|Korean-only" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.md
# 기대: 1 이상

# 6. researchNotebook.en.md 링크 존재 (영문 미러 가리킴)
grep -c "researchNotebook\.en\.md" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.md
# 기대: 1 이상 (Part 1 헤더에서)

# 7. 기존 실험 기록(Exp00~09) 모두 보존
grep -cE "^### Exp(00|01|02|03|035|04|045|05a|05b|06|07|08|08b|09)" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.md
# 기대: 14 (Exp00, Exp01, Exp02, Exp03, Exp035, Exp04, Exp045, Exp05a, Exp05b, Exp06, Exp07, Exp08, Exp08b, Exp09)

# 8. 전체 줄 수 (대략적인 변화 확인)
wc -l /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.md
# 기대: 약 723 ~ 760 (Part 마커 + 학술 주석으로 약간 증가)

# 9. § 현재 상태 및 다음 단계 보존
grep -c "^## 현재 상태 및 다음 단계" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.md
# 기대: 1
```

## Risks

- **H 라벨 변경**: 본 task에서 가설 라벨이나 판정을 *수정*하면 README(task-01)의 H1~H9 표와 어긋나 신뢰 깎임. **변경 금지** 원칙 엄수.
- **Part 1/2 분류 모호**: § 채점 시스템 변천, § 종합 발견을 어디로 분류할지 모호할 수 있음. Step 4의 기준(*"새 실험이 나오면 갱신되는가"*)으로 판단. 의문 있으면 Closed로 — 보수적 분류가 안전 (Active는 *진행 중* 표지).
- **Part 1의 "append-only" 원칙 명시**: 이 원칙이 명시되지 않으면 향후 사용자가 Closed 파트를 직접 수정해 영문판과 어긋날 위험. 안내 단락(Step 3)이 명확해야 함.
- **task-04와의 동기화**: Part 1 분할 결과가 task-04(영문 1:1 번역)의 입력. Part 1 경계가 명확하지 않으면 영문판 작성 시 번역 범위 모호. **본 task의 분할이 task-04의 single source of truth**.
- **frontmatter 변경**: `status: in_progress` 그대로 — Active 파트가 계속 갱신됨. 변경 금지.

## Scope boundary

본 task에서 *절대 수정 금지*:

- `README.md` (task-01 영역)
- `README.en.md` (task-02 영역, 아직 존재하지 않음)
- `docs/reference/researchNotebook.en.md` (task-04 영역, 아직 존재하지 않음)
- `docs/reference/conceptFramework.md` (본 plan 범위 밖)
- `docs/reference/index.md` (필요 시 별도 task로 갱신 — 본 task 범위 밖)
- `experiments/` 하위 어느 파일도
- `docs/plans/` 하위 어느 파일도 (본 task 문서 자신 포함)
- H1~H9c 라벨·판정 자체 — 변경 금지

*허용*: `docs/reference/researchNotebook.md` 단일 파일의 Step 1~7 영역만.
