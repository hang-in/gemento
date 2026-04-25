---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: readme-memento-acknowledgement
parallel_group: B
depends_on: [01]
---

# Task 02 — `README.en.md` 신규 작성

## Changed files

- `README.en.md` (신규 — repo root, `README.md` 옆)

## Change description

한국어 `README.md`의 1:1 번역 *금지*. 영어권 청중(특히 r/LocalLLaMA / Show HN 후보)에 맞춰 재구성. 톤은 first-person solo notebook — *"I started this while building secall/tunaflow"*.

### 권고 구조

```
# Gemento

> One-line tagline (한국어 헤더 한 줄과 동일한 사실, 영어 표현)

## Why I built this  (Hero — origin story 한 단락)
## What I measured  (90 runs 요약 + H1~H9 첫 등장 학술 주석)
## What worked / What didn't  (솔직한 결과 표)
## Why this matters  (좌표 선점·오픈소스 관점)
## Quickstart
## Reproduce / Extend
## Roadmap
## How to Contribute
## Acknowledgements
## License (MIT)
```

### Step 1 — Header & Tagline

영문 한 줄 설명. 한국어 line 3 *"소형 LLM의 내부 한계를 체계적으로 외부화한다..."* 의 사실을 영어로 옮기되 1:1 번역 X. 권고:

> *Externalize the limits of small LLMs — write memory to the environment, delegate computation to tools, and let other roles validate.*

"Operating System" / "novel framework" / "AGI" 금지.

### Step 2 — `## Why I built this` (Hero — origin story)

한 단락. first-person.

핵심 포함:
- secall / tunaflow를 만들며 마주한 실제 문제들 — long-term memory, context over-spend, multi-session
- 첫 가설("clear context, only DB-search → DB as near-infinite context")의 단순함
- Memento 영화의 외부 메모 메타포로 사고가 확장된 경위
- *not a new architecture, not a paper — just a measured side-track that turned into a research topic*

마케팅 톤 X. 자기 비하도 X(영어권에서는 자기 비하가 약함으로 읽힘). *Plain factual notebook* 톤.

### Step 3 — `## What I measured`

90+ runs 요약 + H1~H9 학술 주석.

권고 첫 문장:

> *Note: H1–H9 below denote nine sequentially numbered hypotheses about externalization axes — they are **not** the statistical H₀/H₁ pair.*

이어서 한국어 README line 121~128의 H1~H9 표를 영문화. **task-01이 갱신한 한국어 README의 H1~H9 표를 single source of truth로 참조**. 사실 어긋남 금지.

### Step 4 — `## What worked / What didn't`

솔직한 수치. 영문 청중에게 강한 evidence:

- *Exp02 v2: 50% → 94.4% with 8-loop iteration on the same E4B model.*
- *Exp08b: math tool calls + error-message hints → math-04 from 0% to 100%.*
- *Exp09 long-context (20K): solo-dump 0%, RAG 67%, ABC+Tattoo **100%** on 3-hop reasoning.*
- *Exp03: self-validation **0%** detection — the model can't catch its own errors.*

위 수치는 task-01이 갱신한 README와 researchNotebook §28~40에서 검증.

### Step 5 — `## Why this matters` (좌표 선점·오픈소스 관점)

한 단락. 사용자 의도 ("위치 선점 + 엎치락뒤치락")를 영어로 옮김. 권고:

> *If you're working on something similar — externalization frameworks for small models, structured state, multi-role validation — let's compare notes. This repo is MIT-licensed, so fork freely. I'd rather other people's measurements existed and improved on this than for it to be siloed.*

"우리가 가야 할 길은 포스트 민주주의" 같은 한국어 톤은 **영어로 옮기지 않음** — 정치적으로 위험.

### Step 6 — `## Quickstart` / `## Reproduce` / `## Roadmap`

한국어 README line 178~263을 거의 1:1 영문화 — 명령어와 코드는 그대로, 설명만 영어로. 한국어 § 7(Reproduce)의 (a)/(b)/(c)/(d) 구조 보존.

### Step 7 — `## How to Contribute`

한국어 § 9(line 268~292)의 contribution ladder 표를 영문화. 톤은 한국어와 동일 — *"This is currently a 1-person research notebook. Reproduction by anyone with another model is the most valuable contribution."*

### Step 8 — `## Acknowledgements`

```markdown
## Acknowledgements

- *Memento* (Christopher Nolan, 2000) — original metaphor of external memory aids. Four-axis externalization is the structured-schema cousin of Leonard's tattoos and polaroids.
- secall · tunaflow — the practical origin. The context/memory problems I hit while building those tools are what made this project necessary.
```

### Step 9 — `## License`

```markdown
## License

[MIT](./LICENSE) — fork, modify, redistribute, and use commercially. Just keep the copyright notice.
```

### Step 10 — Cross-references

영문 README는 한국어 README도 가리켜야 함. Header 직후:

> *📚 한국어 버전: [README.md](./README.md)*

한국어 README는 task-01에서 영문판도 가리키도록 추가:

> *📚 English version: [README.en.md](./README.en.md)*

(이건 task-01에 추가 의무로 적힘 — Reviewer가 양쪽 cross-reference 확인 필요. 본 task에서 한국어 README를 한 줄 추가하는 것은 *허용* — Step 10 명시적 허용.)

## Dependencies

- **depends_on: [01]** — task-01이 한국어 README의 H1~H9 표·Acknowledgements 문구를 single source of truth로 확정해야 본 task의 영문판이 그것을 1:1로 따라갈 수 있음.
- 외부 패키지 추가 없음.
- task-03/04와는 *researchNotebook* 영역이라 직접 의존성 없음 — 단 측정 숫자는 researchNotebook을 통해 *간접* 참조됨.

## Verification

```bash
# 1. README.en.md 신규 파일 존재
test -f /Users/d9ng/privateProject/gemento/README.en.md && echo "OK file exists"
# 기대: OK file exists

# 2. 영문 README 헤더가 영어로 시작
head -3 /Users/d9ng/privateProject/gemento/README.en.md | grep -q "^# Gemento" && echo "OK title"
# 기대: OK title

# 3. 한국어 README와의 cross-reference
grep -c "README\.md\|한국어" /Users/d9ng/privateProject/gemento/README.en.md
# 기대: 1 이상

# 4. 한국어 README도 영문판을 가리키는지 (Step 10)
grep -c "README\.en\.md\|English" /Users/d9ng/privateProject/gemento/README.md
# 기대: 1 이상

# 5. Acknowledgements 섹션 존재 + Nolan
grep -c "Christopher Nolan\|Nolan, 2000" /Users/d9ng/privateProject/gemento/README.en.md
# 기대: 1 이상

# 6. secall / tunaflow origin 단락 존재
grep -c "secall\|tunaflow" /Users/d9ng/privateProject/gemento/README.en.md
# 기대: 2 이상 (origin + Acknowledgements)

# 7. H1–H9 학술 주석 존재
grep -c "H₀\|H_0\|statistical" /Users/d9ng/privateProject/gemento/README.en.md
# 기대: 1 이상

# 8. 핵심 측정 숫자가 영문 README에 등장
grep -c "94\.4\|+23\.3\|+68\.3\|100%" /Users/d9ng/privateProject/gemento/README.en.md
# 기대: 4 이상 (Exp02·Exp08b·Exp09·Exp03 등)

# 9. MIT License 명시
grep -c "MIT" /Users/d9ng/privateProject/gemento/README.en.md
# 기대: 1 이상

# 10. 정치적/마케팅 과적재 명칭 미등장
grep -ci "Operating System\|novel framework\|AGI\|breakthrough\|groundbreaking" /Users/d9ng/privateProject/gemento/README.en.md
# 기대: 0

# 11. Manual 가독성 점검 (수동)
# - 첫 단락이 first-person notebook 톤인가
# - 마케팅 표현 없는가
# - H1~H9 표가 한국어 README와 사실 일치하는가
# - Quickstart 명령어가 한국어판과 동일한가
echo "# Manual: open README.en.md and verify tone matches first-person solo notebook, H1-H9 facts match README.md, no marketing language"
```

## Risks

- **한국어 README 단일 출처 위반**: 영문 README의 H1~H9 표·측정 수치가 한국어판과 어긋나면 신뢰 깎임. *task-01 완료 후* 시작 강제 (depends_on=01).
- **자기 비하 톤이 영어로 약함으로 읽힘**: "동네아저씨" 같은 한국어 표현을 *그대로* 영어로 옮기면 신뢰 깎임. "weekend tinkerer" / "solo notebook" 같은 *기능적 정직* 표현으로 옮김.
- **정치적 톤 직역**: § 1의 "쓸 땐 쓰고 새는 건 막는다", "맥락 없는 절약" 같은 한국어 메타포는 영문에서 *옮기지 않음*. 영문판은 4가지 운영 원칙을 *plain functional* 표현으로.
- **Memento 메타포 약화**: 영어권 청중도 영화는 알지만 메타포 강도가 한국어보다 낮을 수 있음. 그러나 직전 토론에서 사용자가 "양키들이 메타포 강도가 낮든 높든 1인 연구라면 중요한 가치"라고 명시. *제거 금지·보존* 방침.
- **README.md 한 줄 수정**: Step 10에서 한국어 README에 영문판 링크 한 줄을 추가하는 것은 task-02에서 명시적으로 허용. 그 외 한국어 README 수정 금지.

## Scope boundary

본 task에서 *허용*:

- `README.en.md` (신규 작성) — 핵심
- `README.md`에 영문판 링크 한 줄 추가 (Step 10) — *예외적 허용*

본 task에서 *절대 수정 금지*:

- `README.md`의 Step 10 외 다른 부분 (task-01 영역)
- `docs/reference/researchNotebook.md` (task-03 영역)
- `docs/reference/researchNotebook.en.md` (task-04 영역, 아직 존재하지 않음)
- `docs/reference/conceptFramework.md`
- `LICENSE`
- `experiments/` 하위 어느 파일도
- `docs/plans/` 하위 어느 파일도 (본 task 문서 자신 포함)
