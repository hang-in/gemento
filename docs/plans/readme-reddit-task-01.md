---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: readme-reddit
parallel_group: A
depends_on: []
---

# Task 01 — README 파일 swap (git mv)

## Changed files

- `README.md` — **rename**. 한국어 (현재 339 줄) → `README.ko.md` 로 이동.
- `README.en.md` — **rename**. 영문 (현재 160 줄) → `README.md` 로 이동.

신규 파일 0. 본 task 는 본문 변경 0 — rename only.

## Change description

### 배경

레딧 (r/LocalLLaMA, r/MachineLearning) 공개 시 첫 화면 이탈률 최소화를 위해 영문이 메인 README 가 되어야 한다. 현재는 한국어 README 가 메인 위치 (`README.md`). 본 task 는 git history 보존을 위해 `git mv` 로 swap.

### Step 1 — git mv 로 한국어 → README.ko.md

```bash
cd /Users/d9ng/privateProject/gemento
git mv README.md README.ko.md
```

### Step 2 — git mv 로 영문 → README.md

```bash
git mv README.en.md README.md
```

### Step 3 — 본문 변경 0

본 task 는 **rename only**. 한국어 본문도 영문 본문도 변경 금지. 톤 정정·섹션 추가는 task-02~05 의 영역.

### Step 4 — git status 확인

```bash
git status --short
```

기대 출력 (rename 인식):
```
R  README.md -> README.ko.md
R  README.en.md -> README.md
```

`A`/`D` 가 아닌 `R` 가 보여야 git 이 rename 을 추적함 (history 보존).

## Dependencies

- 없음. 본 task 는 plan 의 foundation.
- 외부 패키지: 없음. `git mv` 만 사용.

## Verification

```bash
# 1. 두 README 파일 모두 존재 + README.en.md 부재
test -f /Users/d9ng/privateProject/gemento/README.md && \
test -f /Users/d9ng/privateProject/gemento/README.ko.md && \
test ! -f /Users/d9ng/privateProject/gemento/README.en.md && \
echo "OK README.md + README.ko.md exist, README.en.md removed"

# 2. README.md 가 영문 (첫 줄에 'Externalize' 또는 'Gemento is an experimental' 등)
head -3 /Users/d9ng/privateProject/gemento/README.md | grep -E "Externalize|Gemento is an" && echo "OK README.md is English"

# 3. README.ko.md 가 한국어 (첫 줄에 '제멘토' 등)
head -3 /Users/d9ng/privateProject/gemento/README.ko.md | grep -E "제멘토|소형 LLM" && echo "OK README.ko.md is Korean"

# 4. git rename 추적 — git status 가 R 표시
cd /Users/d9ng/privateProject/gemento && git status --short | grep -E "^R" | wc -l | grep -E "^\s*2$" && echo "OK git tracks 2 renames"

# 5. git log --follow 로 history 추적 가능
cd /Users/d9ng/privateProject/gemento && git log --follow --oneline -1 README.md && echo "OK README.md history follows"
cd /Users/d9ng/privateProject/gemento && git log --follow --oneline -1 README.ko.md && echo "OK README.ko.md history follows"

# 6. 다른 파일 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only | grep -vE "^README\.(md|ko\.md|en\.md)$" | grep -v "^$" || echo "OK no extra changes"
```

## Risks

- **`git mv` 가 R 대신 A+D 로 인식**: 두 파일 본문이 너무 달라 git 이 rename heuristic 을 통과 못 할 가능성. 본 case 는 한국어 ↔ 영문이라 본문 차이 매우 큼. 그래도 mv 명령 자체는 성공 (파일 시스템 레벨). git 이 R 인식 못 해도 본 task 의 핵심 (파일 이름 swap) 은 성취. Verification 4 가 실패해도 1·2·3·5 통과면 진행 가능 — Reviewer 판단.
- **README.en.md 가 다른 파일에서 참조**: 본 task 후 link 깨짐 위험. task-06 에서 일괄 정정.
- **CI/CD 또는 외부 링크가 README.en.md 참조**: 본 repo 는 사용자 1인 연구로 외부 의존성 미미. 위험 무시 가능.
- **macOS HFS+ 대소문자 무시**: 본 case 는 .md vs .en.md, .ko.md 구분으로 안전.
- **충돌 — 이미 README.ko.md 존재 시**: 사전 정찰 결과 README.ko.md 부재 확인됨. 안전.

## Scope boundary

**Task 01 에서 절대 수정 금지**:

- README.md 본문 (한국어 → README.ko.md 이동만, 본문 변경 금지)
- README.en.md 본문 (영문 → README.md 이동만, 본문 변경 금지)
- `docs/` 의 모든 파일 (link 정정은 task-06)
- `experiments/` 의 모든 파일
- `.gitignore`, `.env.example`
- 다른 모든 파일

**허용 범위**:

- `git mv README.md README.ko.md`
- `git mv README.en.md README.md`
- 두 명령 외 어떤 파일 변경도 금지.
