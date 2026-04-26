---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: readme-reddit
parallel_group: B
depends_on: [01]
---

# Task 03 — Core idea 섹션 추가

## Changed files

- `README.md` (영문 메인) — **수정**. `## What I measured` 섹션 직전에 `## Core idea` 신규 섹션 추가.

신규 파일 0. README.ko.md 변경 0.

## Change description

### 배경

지피티 권고 섹션 매핑 결과 영문 README 에 **Core idea** 섹션이 누락. 현재 구조에서는 H1~H9 표 안에 4축이 분산 등장하지만 한눈에 보이지 않음. 본 task 는 4축 (Tattoo / Tools / Role / Orchestrator) 을 1 단락 + 미니 표로 명시한다.

이 정보는 한국어 README.ko.md 의 "2. The Core Idea — 외부화" 섹션 (line 57-122) 에 이미 존재. 영문 압축 버전을 만든다.

### Step 1 — 섹션 위치 확인

현재 영문 README 섹션 순서 (task-02 후 기준):
1. # Gemento (첫 문장)
2. ## Why I built this
3. ## What I measured
4. ## What worked / What didn't
5. ## Why this matters
6. ## Quickstart
...

**Core idea** 는 `## Why I built this` 다음, `## What I measured` 직전에 삽입 — 독자 흐름: "왜 만들었나" → "어떤 아이디어인가" → "결과 수치".

### Step 2 — Core idea 섹션 본문 작성

```markdown
## Core idea

Gemento treats four axes of LLM cognition as **externalizable** — moved out of model weights and into the workflow:

| Axis | What goes outside the model | Mechanism | Anchor experiment |
|------|----------------------------|-----------|-------------------|
| **Tattoo** | Working memory (claims, evidence, status) | Structured JSON state passed across loops | Exp02, Exp09 |
| **Tools** | Computation (math, search, retrieval) | OpenAI-compatible function calls (calculator, linalg, linprog) | Exp08, Exp08b |
| **Role** | Self-validation | A (Proposer) / B (Critic) / C (Judge) — separate prompts, same base model | Exp03, Exp035, Exp06 |
| **Orchestrator** | Termination · phase transition · resource budget | Deterministic Python loop, not the model itself | Exp02, Exp07 |

This is not about replacing a 70B model with a 4.5B one. It is about asking what **structure** can extract from a 4.5B model that single-pass inference does not surface.
```

### Step 3 — 미니 표 검증

표 컬럼 4개:
- Axis (4축 이름)
- What goes outside the model (한 줄 정의)
- Mechanism (구현 방식)
- Anchor experiment (해당 외부화를 검증한 실험 ID)

본 표는 한국어 README.ko.md 의 § 2 본문 + researchNotebook.md 의 "축 ↔ 실험 매트릭스" (line 58-64) 에서 추출. 본 task 는 영문 압축 — 새 정보 추가 X.

### Step 4 — 마지막 문장 ("This is not about replacing...")

claim 톤다운: "Gemento doesn't replace 70B" 같은 단정 X. "It is about asking what structure can extract" 식 question framing — 학계 reviewer 에게 모험 톤 회피.

## Dependencies

- **task-01 완료** — README.md (영문) 가 메인 위치에 있어야 함.
- task-02 와 영역 분리: task-02 는 line 1-3 + 본문 단어 정정, task-03 은 신규 섹션 추가. 하지만 동일 파일 → **순차 진행** (plan Constraints).
- 외부 패키지: 없음.

## Verification

```bash
# 1. ## Core idea 섹션 존재
grep -E "^## Core idea" /Users/d9ng/privateProject/gemento/README.md && echo "OK Core idea section added"

# 2. 4축 키워드 모두 등장 (Tattoo / Tools / Role / Orchestrator)
cd /Users/d9ng/privateProject/gemento && grep -F "Tattoo" README.md && grep -F "Tools" README.md && grep -F "Role" README.md && grep -F "Orchestrator" README.md && echo "OK 4 axes mentioned"

# 3. anchor experiment ID 등장 (Exp02, Exp08, Exp035 중 하나 이상)
cd /Users/d9ng/privateProject/gemento && grep -E "Exp(02|08|035)" README.md && echo "OK anchor experiments cited"

# 4. 섹션 순서 — Core idea 가 What I measured 직전
cd /Users/d9ng/privateProject/gemento && _ZO_DOCTOR=0 python3 -c "
text = open('README.md', encoding='utf-8').read()
core_pos = text.find('## Core idea')
measured_pos = text.find('## What I measured')
why_pos = text.find('## Why I built this')
assert core_pos > 0, 'Core idea section missing'
assert measured_pos > core_pos, 'Core idea must come before What I measured'
assert core_pos > why_pos, 'Core idea must come after Why I built this'
print('OK section order: Why I built this < Core idea < What I measured')
"

# 5. 표의 4 행 (Tattoo / Tools / Role / Orchestrator) 모두 등장
cd /Users/d9ng/privateProject/gemento && grep -cE "^\| \*\*(Tattoo|Tools|Role|Orchestrator)\*\* \|" README.md | grep -E "^4$" && echo "OK 4 axis rows in table"

# 6. README.ko.md 미수정
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only | grep "README.ko.md" && echo "FAIL README.ko.md modified" || echo "OK README.ko.md unchanged"

# 7. 다른 파일 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only | grep -vE "^README\.(md|ko\.md|en\.md)$" | grep -v "^$" || echo "OK no extra changes"
```

## Risks

- **task-02 와 동일 파일 동시 편집**: README.md 를 task-02 직후 task-03 진행. 순차 진행 강제 (plan Constraints).
- **마크다운 표 정합성**: 4 컬럼 표 — 헤더·구분자 일치 필요. Verification 5 가 강제.
- **Mechanism 컬럼의 정확성**: "OpenAI-compatible function calls" 같은 기술 용어 — 코드와 일치 (`experiments/orchestrator.py:call_model()` 의 tools loop 와 일치). 정확성 보장.
- **Anchor experiment 매핑**: Exp02 (multiloop) → Tattoo + Orchestrator, Exp08 → Tool, Exp035 → Role 등. researchNotebook.md 의 "축 ↔ 실험 매트릭스" 와 일치 — 본 task 가 그 매트릭스의 영문 압축이라 충돌 없음.
- **첫 문장의 4축 정의 표현**: "treats as externalizable" 단어가 학계에서 안전. "moved out of model weights" 단정 — 위험. 본 task 본문에 "is about asking" question framing 으로 보완.

## Scope boundary

**Task 03 에서 절대 수정 금지**:

- README.md 의 첫 문장 (task-02 결과물 그대로).
- README.md 의 표 (`What I measured`) — 수치·verdict 컬럼 그대로.
- README.md 의 다른 기존 섹션 (Why I built this, Quickstart, Acknowledgements 등).
- README.ko.md — 별도 task.
- `docs/` 의 모든 파일.
- `experiments/` 의 모든 파일.

**허용 범위**:

- README.md 에 `## Core idea` 섹션 신규 추가 (Why I built this 다음, What I measured 직전).
- 본 섹션은 1 단락 + 미니 표 + 마지막 한 줄로 구성. ~15 줄 신규.
