---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: readme-reddit
parallel_group: B
depends_on: [01]
---

# Task 02 — 영문 README 톤 정정

## Changed files

- `README.md` (구 README.en.md, task-01 swap 후) — **수정**. 첫 문장 + 본문의 강한 주장 단어 정정.

신규 파일 0. README.ko.md 변경 0 (다음 task 영역).

## Change description

### 배경

지피티의 외부 검토 의견에 따르면 현재 영문 README 의 톤이 강함:
- 첫 문장: "**Externalize the limits of small LLMs.** Write memory into the environment, delegate computation to tools, and let other roles criticize the result." — 명령형, 단정적.
- 본문 곳곳에 "proves", "beats RAG" 등 학계 reviewer 에게 claim inflation 으로 읽힐 단어.

본 task 는 학술 톤 (서술형, 잠정 결과) 으로 정정하되 검증된 수치·verdict 는 그대로 유지한다.

### Step 1 — 첫 문장 (line 1-3) 정정

현재 (`README.md:1-3`):
```markdown
# Gemento

> **Externalize the limits of small LLMs.** Write memory into the environment, delegate computation to tools, and let other roles criticize the result.
```

→ 권고 (두 문장 분리, claim 톤다운):
```markdown
# Gemento

> **Gemento is an experimental harness, not a new architecture or a paper.** It tests whether small local LLMs can run long workflows when memory, tools, roles, and control are externalized.
```

### Step 2 — 본문 강한 주장 단어 정정

전체 README.md 본문에서 다음 패턴 식별 후 톤다운:

- `proves` → `suggests` 또는 `we observe`
- `beats RAG` → `outperforms RAG on long, multi-hop synthesis tasks` (구체화)
- `conquers` / `solves` → `appears to compensate for` / `allows`
- 명령형 문장 (`Externalize ...`, `Write memory ...`) → 서술형 (`Memory is written into ...`, `When memory is externalized ...`)

본 task 는 **단어 단위 grep + 정정** — 전면 재작성 금지. 검증된 수치·verdict 표는 그대로.

검색 패턴 (정정 대상 후보):
```bash
grep -nE "\b(proves|beats|conquers|solves|wins)\b" README.md
```

각 매치를 케이스별로 검토 후 정정.

### Step 3 — Verdict 단어 검토

`What I measured` 표 안의 verdict 컬럼:
- "Supported" — 그대로 OK (결과의 직접 보고)
- "Rejected" — 그대로 OK
- "Partially rejected" / "Conditionally supported" — 그대로 OK (이미 보수적)

**verdict 변경 금지** — 본 task 는 narrative 톤 정정만, 결과 컬럼 변경 금지.

### Step 4 — 수치·표 보존 확인

표 안의 정량 수치 (`+44.4pp`, `94.4%`, `0%`, `100%`, `+68.3pp` 등) 변경 금지. grep 으로 사후 확인.

## Dependencies

- **task-01 완료** — `README.md` 가 영문이어야 함 (rename 후).
- 외부 패키지: 없음.

## Verification

```bash
# 1. 첫 문장 정정 확인
head -3 /Users/d9ng/privateProject/gemento/README.md | grep -F "experimental harness" && echo "OK first line is harness-tone"

# 2. 명령형 표현 ("Externalize the limits") 부재 확인
grep -F "Externalize the limits" /Users/d9ng/privateProject/gemento/README.md && echo "FAIL command-tone still present" || echo "OK command-tone removed"

# 3. claim inflation 단어 grep — 0건 (단어 boundary 매칭)
cd /Users/d9ng/privateProject/gemento && grep -nE "\b(proves|conquers|wins)\b" README.md && echo "FAIL strong-claim words found" || echo "OK no claim-inflation words"

# 4. 검증 수치 보존 — 핵심 수치 모두 등장
cd /Users/d9ng/privateProject/gemento && grep -F "94.4" README.md && grep -F "+44.4" README.md && grep -F "+68.3" README.md && echo "OK key numbers preserved"

# 5. verdict 컬럼 보존 — Supported / Rejected / Conditionally 모두 등장
cd /Users/d9ng/privateProject/gemento && grep -F "Supported" README.md && grep -F "Rejected" README.md && grep -F "Conditionally" README.md && echo "OK verdict column preserved"

# 6. README.ko.md 미수정
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only | grep "README.ko.md" && echo "FAIL README.ko.md modified" || echo "OK README.ko.md unchanged in this task"

# 7. 다른 파일 변경 없음 (README.md 만)
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only | grep -vE "^README\.(md|ko\.md|en\.md)$" | grep -v "^$" || echo "OK no extra changes"
```

## Risks

- **regex grep false positive**: `\b(proves|...)\b` 가 다른 단어 (예: "improved", "approves") 와 우연 매칭 가능. boundary `\b` 로 보수적이지만 발생 시 케이스별 판단.
- **첫 문장 길이**: 권고 문장이 길어 첫 화면 한 줄 초과 가능. 필요 시 두 줄 분리. 이건 markdown 렌더 결과로 결정 — Verification 1 은 텍스트 검증만.
- **수치 우연 변경**: 검색-치환 시 숫자 우연 변경 위험. Verification 4 가 강제.
- **verdict 컬럼 우연 변경**: Verification 5 가 강제. 변경 시 즉시 발견.
- **다음 task (Core idea, Related work, Research notes 추가) 와의 동시 편집**: 본 task 는 line 1-3 + 본문 grep 정정만. 신규 섹션 추가 X. task-03~05 와 영역 분리 가능하나 동일 파일이라 순차 진행 권고 (plan Constraints).

## Scope boundary

**Task 02 에서 절대 수정 금지**:

- README.md 의 표 (`What I measured` 등) — 수치·verdict 컬럼 변경 금지.
- README.md 의 신규 섹션 추가 — task-03~05 의 영역.
- README.md 의 링크 — task-06 의 영역.
- README.ko.md — 별도 task (task-06 의 영문 링크 정정만).
- `docs/` 의 모든 파일.
- `experiments/` 의 모든 파일.

**허용 범위**:

- README.md 의 첫 문장 (line 1-3) 정정.
- README.md 본문의 단어 단위 톤다운 (proves, conquers, wins 등 → 서술형).
- 명령형 문장 → 서술형 변환 (단, 단락 구조·길이 대폭 변경 금지).
