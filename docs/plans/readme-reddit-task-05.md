---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: readme-reddit
parallel_group: B
depends_on: [01]
---

# Task 05 — Research notes / Docs Map 섹션 추가

## Changed files

- `README.md` (영문 메인) — **수정**. `## Quickstart` 섹션 다음에 `## Research notes` 신규 섹션 추가.

신규 파일 0. README.ko.md 변경 0.

## Change description

### 배경

지피티 권고에서 영문 README 에 **Research notes / Docs Map** 섹션이 누락 (한국어 README.ko.md 의 § 10. Docs Map 영역과 동등). 외부 검토자가 "더 자세한 내용 어디?" 라고 물었을 때 영문 README 에서 즉시 docs 링크를 제시해야 한다.

대상 링크 4개 (모두 정찰 완료, 파일 존재 확인):
- `README.ko.md` (task-01 swap 후 한국어 풀버전)
- `docs/reference/researchNotebook.md` (한국어 노트, 5W1H 형식)
- `docs/reference/researchNotebook.en.md` (영문 노트)
- `docs/reference/conceptFramework.md` (개념 프레임워크)

### Step 1 — 섹션 위치 확인

현재 영문 README 섹션 순서 (task-02·03·04 후 기준):
1. # Gemento
2. ## Why I built this
3. ## Core idea (task-03)
4. ## What I measured
5. ## What worked / What didn't
6. ## Why this matters
7. ## Quickstart   ← 여기 다음 삽입
8. ## Reproduce / Extend
9. ## Roadmap
10. ## How to Contribute
11. ## Related work (task-04)
12. ## Acknowledgements
13. ## License

### Step 2 — Research notes 섹션 본문 작성

```markdown
## Research notes

If you want more than the README:

- **[README.ko.md](./README.ko.md)** — Korean full README with the same hypothesis table, plus extra sections on open questions and Korean-language scoring caveats.
- **[docs/reference/researchNotebook.md](./docs/reference/researchNotebook.md)** — Per-experiment notebook in 5W1H format (who / when / where / what / why / how). Korean.
- **[docs/reference/researchNotebook.en.md](./docs/reference/researchNotebook.en.md)** — English mirror of the above (kept in sync).
- **[docs/reference/conceptFramework.md](./docs/reference/conceptFramework.md)** — The four-axis externalization framework, including unverified candidate axes (Extractor, Reducer, Search Tool, Graph Tool, Evidence Tool, Critic Tool).

Plan-level history (decisions and revisions) lives under `docs/plans/` — see `docs/plans/index.md` for the running list.
```

### Step 3 — 링크 형식 — relative path

모든 링크는 `[text](./path)` 또는 `[text](path)` relative form. GitHub web view + local clone 모두 작동.

### Step 4 — Plan 디렉토리 안내

`docs/plans/` 의 in-progress / archived plan 들이 결정 history 의 출처. 본 섹션의 마지막 한 줄로 안내.

## Dependencies

- **task-01 완료** — README.md (영문) 메인 위치 + README.ko.md 존재.
- task-02·03·04 와 동일 파일 → 순차 진행.
- 외부 파일: `docs/reference/researchNotebook.md`, `researchNotebook.en.md`, `conceptFramework.md` 모두 존재 (사전 정찰 완료).
- 외부 패키지: 없음.

## Verification

```bash
# 1. ## Research notes 섹션 존재
grep -E "^## Research notes" /Users/d9ng/privateProject/gemento/README.md && echo "OK Research notes section added"

# 2. 4 링크 모두 등장 (대상 파일 경로 grep)
cd /Users/d9ng/privateProject/gemento && grep -F "README.ko.md" README.md && \
grep -F "docs/reference/researchNotebook.md" README.md && \
grep -F "docs/reference/researchNotebook.en.md" README.md && \
grep -F "docs/reference/conceptFramework.md" README.md && \
echo "OK 4 docs links present"

# 3. 링크 대상 파일 모두 실재
test -f /Users/d9ng/privateProject/gemento/README.ko.md && \
test -f /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.md && \
test -f /Users/d9ng/privateProject/gemento/docs/reference/researchNotebook.en.md && \
test -f /Users/d9ng/privateProject/gemento/docs/reference/conceptFramework.md && \
echo "OK 4 link targets exist"

# 4. 섹션 순서 — Research notes 가 Quickstart 다음, Reproduce / Extend 직전
cd /Users/d9ng/privateProject/gemento && _ZO_DOCTOR=0 python3 -c "
text = open('README.md', encoding='utf-8').read()
notes_pos = text.find('## Research notes')
quickstart_pos = text.find('## Quickstart')
repro_pos = text.find('## Reproduce')
assert notes_pos > 0, 'Research notes section missing'
assert notes_pos > quickstart_pos, 'Research notes must come after Quickstart'
assert notes_pos < repro_pos, 'Research notes must come before Reproduce/Extend'
print('OK section order: Quickstart < Research notes < Reproduce/Extend')
"

# 5. plans 안내 등장
cd /Users/d9ng/privateProject/gemento && grep -F "docs/plans" README.md && echo "OK plans directory mentioned"

# 6. README.ko.md 미수정
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only | grep "README.ko.md" && echo "FAIL README.ko.md modified" || echo "OK README.ko.md unchanged"

# 7. 다른 파일 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only | grep -vE "^README\.(md|ko\.md|en\.md)$" | grep -v "^$" || echo "OK no extra changes"
```

## Risks

- **링크 대상 파일 부재**: 사전 정찰로 모두 존재 확인. 단 향후 docs 재구조화 시 broken — task-07 의 broken link 검증으로 잡힘.
- **researchNotebook.md / .en.md 동기화 차이**: 한국어가 영문보다 자주 갱신될 수 있음. 본 task 는 두 파일 모두 링크 — 외부 검토자가 더 최신이라고 판단되는 쪽 선택.
- **plans/index.md 미존재 가능성**: `docs/plans/index.md` 가 실재해야 마지막 안내 줄 의미 있음. 사전 확인 권고. 부재 시 본 task 수정자가 안내 줄 삭제 결정.
- **Reddit 사용자 입장 — 너무 많은 링크**: 4 링크 + 1 plans 안내 = 5 항목. 첫 화면 이탈 우려 vs 외부 검토 가치 trade-off. 4 링크 유지 권고 (각 다른 청중: ko 사용자 / 5W1H notebook / 영문 mirror / 개념 프레임).

## Scope boundary

**Task 05 에서 절대 수정 금지**:

- README.md 의 기존 섹션 (Why I built this, Core idea, What I measured, Quickstart 등) — 본문 변경 0.
- README.ko.md — 별도 task.
- `docs/reference/researchNotebook.md`, `.en.md`, `conceptFramework.md` — 본 task 는 링크만 생성, 본문 변경 0.
- `docs/plans/` 의 모든 파일.
- `experiments/` 의 모든 파일.

**허용 범위**:

- README.md 에 `## Research notes` 섹션 신규 추가 (Quickstart 다음, Reproduce / Extend 직전).
- 본 섹션은 4 bullet 링크 + 1 plans 안내 줄. ~10 줄 신규.
