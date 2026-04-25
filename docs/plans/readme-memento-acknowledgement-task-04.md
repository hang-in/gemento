---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: readme-memento-acknowledgement
parallel_group: B
depends_on: [03]
---

# Task 04 — `researchNotebook.en.md` 신규 작성 (Closed 파트만 거의 1:1 영문)

## Changed files

- `docs/reference/researchNotebook.en.md` (신규)

## Change description

`docs/reference/researchNotebook.md`의 **Part 1 (Closed Findings)** 만 거의 1:1 영문 번역. 압축 학술 풍 권고는 *철회*되어 있으며, 종결된 사실은 1:1이 정확성·신뢰 측면에서 더 강함.

### Step 1 — frontmatter

```yaml
---
type: reference
status: in_progress
updated_at: 2026-04-25
mirror_of: docs/reference/researchNotebook.md (Part 1 — Closed Findings)
language: en
---
```

`status: in_progress` — Part 1에 새 실험이 append되면 영문판도 동기화 필요하므로.

### Step 2 — Header & 동기화 안내

```markdown
> **English mirror — design statement**
>
> This is the English mirror of [`researchNotebook.md`](./researchNotebook.md) **Part 1 — Closed Findings**. 
>
> - Part 1 covers concluded experiments (Exp00–09) and hypothesis verdicts (H1–H9c). The Korean source is the single source of truth; this English file is a translation, not the original.
> - Part 2 (Active Research — open questions, next experiments) is **not translated**. It remains Korean-only by design — when items in Part 2 close, they migrate to Part 1 and become eligible for English translation.
> - **Append-only**: the contents of this file should only grow. Existing entries should not be edited.
```

### Step 3 — 본문 1:1 번역

한국어 `researchNotebook.md`의 Part 1 영역(line 1~686 중 Part 1 마커로 감싼 부분)을 거의 1:1 영문 번역.

**번역 원칙**:

- 표·수치·실험 이름은 *그대로 보존* (예: "Exp02 v2", "94.4%", "math-04 0→100%", "+18.3%p")
- 한국어 학술 표현은 정확한 영문 학술 표현으로 (예: "정답률" → "accuracy", "수렴" → "convergence", "채택" → "supported", "기각" → "rejected", "조건부 채택" → "partially supported")
- 임의 paraphrase 금지 — 한국어 원문 의미를 정확히 유지
- 6하원칙(누가/언제/어디서/무엇을/왜/어떻게) → "Who / When / Where / What / Why / How"

**번역 범위** (한국어 line 번호 기준, task-03 분할 후):
- § 프로젝트 개요 (line 16~24)
- § 핵심 가설 (line 26~40, H1~H9c 표)
- § 축 ↔ 실험 매트릭스 (line 42~62)
- § 실험 기록 — Exp00 ~ Exp09 (line 65~640) — 각 실험의 6하원칙 표·결과 표·핵심 발견·결론·후속 과제 모두
- § 채점 시스템 변천 (line 642~663) — v1→v2 전환 표 + 전체 재채점 결과 표
- § 종합 발견: E4B 능력 프로파일 (line 665~686) — 능력 표 + 확정된 아키텍처 원칙

**번역하지 *않는* 영역**:
- § 현재 상태 및 다음 단계 (한국어 line 689~720, Part 2) — 본 task 범위 밖
- frontmatter는 새로 작성 (Step 1)
- Part 1 마커 자체는 영문에서 영문 헤더로 (예: `# Part 1 — Closed Findings`)

### Step 4 — H1~H9c 학술 주석 (영문)

한국어판의 학술 주석(task-03 Step 2)을 영문화. 영문 § Hypotheses 섹션 직전:

```markdown
> *Note: H1–H9 below denote nine sequentially numbered hypotheses about externalization axes — they are **not** the statistical H₀ (null) / H₁ (alternative) pair.*
```

### Step 5 — Acknowledgements (영문판 끝)

```markdown
## Acknowledgements

- *Memento* (Christopher Nolan, 2000) — original metaphor of external memory aids.
- secall · tunaflow — practical origin of this research; the context/memory problems hit while building those tools shaped the externalization framework.
```

### Step 6 — License 명시

```markdown
## License

Source code: [MIT](../../LICENSE). Documentation: same as repo policy.
```

### Step 7 — Cross-reference

`researchNotebook.md` Part 1 헤더에 영문판 링크가 *이미* 추가되어야 함 (task-03 Step 3). 본 task에서는 *반대 방향* 링크만 추가 (Step 2의 헤더에서 한국어 원본 가리킴).

추가로 `docs/reference/index.md`에도 영문판 항목이 등장하면 좋겠지만 — 이는 *본 task 범위 밖* (별도 인덱스 갱신은 후속 작업으로).

## Dependencies

- **depends_on: [03]** — task-03에서 Part 1 / Part 2 분할이 완료되어야 Part 1 영역을 정확히 식별·번역 가능. Part 1 경계가 단일 출처.
- 외부 패키지 추가 없음.
- task-02(영문 README)와는 직접 의존성 없음 — 단 H1~H9c 영문 표기·측정 수치는 task-02와 일관성 유지 (둘 다 Part 1을 single source of truth로 참조).

## Verification

```bash
# 1. 신규 파일 존재
test -f /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.en.md && echo "OK file exists"
# 기대: OK file exists

# 2. 영문 헤더 시작
head -10 /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.en.md | grep -q "English mirror\|Part 1 — Closed" && echo "OK header"
# 기대: OK header

# 3. H1~H9c 모두 번역되어 있는지 (한국어판과 동일 라벨)
grep -cE "^\| H[1-9]" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.en.md
# 기대: 11 (H1, H2, H3, H4, H5, H6, H7, H8, H9a, H9b, H9c)

# 4. 핵심 측정 숫자 보존 (한국어판과 1:1)
grep -cE "94\.4|0→80|0→100|\+18\.3|\+23\.3|\+68\.3|100%" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.en.md
# 기대: 6 이상 (Exp02·Exp08·Exp08b·Exp09 핵심 수치 보존)

# 5. Exp00 ~ Exp09 모두 등장 (14개 실험 라벨)
grep -cE "Exp(00|01|02|03|035|04|045|05a|05b|06|07|08|08b|09)" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.en.md
# 기대: 14 (각 실험 헤더에서)

# 6. Active(Part 2) 콘텐츠 미포함 — "현재 상태 및 다음 단계"의 16개 열린 질문
grep -c "Open Questions\|Active Research\|다음 실험 후보\|Exp10 후보\|Small Paradox" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.en.md
# 기대: 0 (Part 2 콘텐츠 번역 안 함)
# 단 "Acknowledgements" 직전까지 Part 2 항목이 없어야 함

# 7. 학술 주석 (statistical H₀/H₁ 구분)
grep -c "H₀\|H_0\|null hypothesis\|statistical" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.en.md
# 기대: 1 이상

# 8. Acknowledgements 섹션 + Nolan
grep -c "Christopher Nolan\|Nolan, 2000" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.en.md
# 기대: 1 이상

# 9. 한국어 원본 cross-reference
grep -c "researchNotebook\.md\|Korean source" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.en.md
# 기대: 1 이상

# 10. 한국어 원본 줄 수와 비교 (1:1 번역이므로 비슷한 규모)
korean_lines=$(grep -c "" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.md)
english_lines=$(grep -c "" /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.en.md)
echo "Korean: $korean_lines lines, English: $english_lines lines"
# 기대: English가 약 600~750줄 (Part 1만 번역이므로 한국어 전체보다 약간 작거나 비슷)

# 11. Manual: 표 구조 보존 점검 (수동)
echo "# Manual: open researchNotebook.en.md and verify (a) H1-H9 verdict labels match Korean source, (b) all Exp00-09 sections have 6W1H tables, (c) no Part 2 content (open questions list) appears"
```

## Risks

- **압축으로 인한 사실 손실**: 본 task는 *1:1* 번역. 임의 paraphrase / 압축 / 요약 금지. 사용자가 직전 토론에서 "거의 1:1로 할 수 있겠지?"라고 명시.
- **학술 표현 정확성**: "정답률 100%" → "100% accuracy" (단순), "수렴" → "convergence" (정확), "채택/기각/조건부 채택" → "supported / rejected / partially supported". 임의 표현 사용 시 학술 신뢰도 깎임. Developer가 사전 검토.
- **task-03 분할 경계 부정확**: task-03에서 Part 1/Part 2 경계가 명확하지 않으면 본 task 번역 범위 모호. Part 1 마커가 single source of truth.
- **Part 2 콘텐츠 실수로 번역**: 한국어 line 689~720 (Active 영역)을 *번역하지 않음*. 만약 모르고 번역 시 설계 위반.
- **표·수치 영문화 시 단위 변환 위험**: 한국어 "+18.3%p" → 영문 "+18.3 percentage points" 또는 "+18.3pp" — 일관성. Developer는 첫 등장에서 표기를 확정하고 끝까지 일관 사용.
- **줄 수 차이 — 영문이 한국어보다 긴 경우**: 영문이 한국어보다 약간 길 수 있음(영어 단어 수 vs 한국어 음절). 그러나 *압축* 또는 *과도 확장*은 모두 위반.

## Scope boundary

본 task에서 *허용*:

- `docs/reference/researchNotebook.en.md` (신규 작성) — 핵심

본 task에서 *절대 수정 금지*:

- `docs/reference/researchNotebook.md` (task-03 영역)
- `README.md` (task-01 영역)
- `README.en.md` (task-02 영역)
- `docs/reference/conceptFramework.md`
- `docs/reference/index.md`
- `LICENSE`
- `experiments/` 하위 어느 파일도
- `docs/plans/` 하위 어느 파일도 (본 task 문서 자신 포함)
- 한국어 원본의 Part 2 콘텐츠 — 영문 번역 금지
