---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: readme-reddit
parallel_group: B
depends_on: [01]
---

# Task 06 — 내부 링크 정정

## Changed files

- `README.md` (영문 메인) — **수정**. 한국어 버전 cross-link 정정.
- `README.ko.md` (한국어, task-01 swap 후) — **수정**. 영문 버전 cross-link 정정.

신규 파일 0.

## Change description

### 배경

task-01 의 파일 swap 후 두 README 의 cross-link 가 깨진다:

- 구 `README.en.md:5` (지금 `README.md:5`) 에는 `📚 한국어 버전: [README.md](./README.md)` — 자기 자신을 가리킴 (broken).
- 구 `README.md:21` (지금 `README.ko.md:21`) 에는 `📚 English version: [README.en.md](./README.en.md)` — 더 이상 존재하지 않는 파일 (broken).

본 task 는 두 곳 모두 정정.

### Step 1 — README.md (영문) 의 한국어 링크 정정

현재 `README.md:5` (사전 정찰 결과):
```markdown
📚 한국어 버전: [README.md](./README.md)
```

→ 정정:
```markdown
📚 Korean version: [README.ko.md](./README.ko.md)
```

라벨도 영문화 ("한국어 버전" → "Korean version") — 영문 README 답게 정렬.

### Step 2 — README.ko.md (한국어) 의 영문 링크 정정

현재 `README.ko.md:21` (사전 정찰 결과):
```markdown
> 📚 English version: [README.en.md](./README.en.md)
```

→ 정정:
```markdown
> 📚 English version: [README.md](./README.md)
```

라벨 ("English version") 그대로 — 한국어 사용자도 읽기 명확.

### Step 3 — 그 외 cross-link 검색

본 사전 정찰에서는 위 2 곳만 발견. 정정 후 추가 검증으로 잔여 broken link 확인:

```bash
# README.md 안에 README.en.md 참조 0건
grep -F "README.en.md" /Users/d9ng/privateProject/gemento/README.md && echo "FAIL stale link" || echo "OK"

# README.ko.md 안에 README.en.md 참조 0건
grep -F "README.en.md" /Users/d9ng/privateProject/gemento/README.ko.md && echo "FAIL stale link" || echo "OK"
```

### Step 4 — docs/ 내 README* 참조 정찰 (informational, 본 task 에서 정정 X)

`docs/plans/readme-memento-acknowledgement*` 등 archived plan 의 README.en.md 참조는 archive 기록이므로 정정 금지. plan history 보존.

다음 명령으로 archive 외부 참조 확인:
```bash
grep -rE "README\.en\.md" /Users/d9ng/privateProject/gemento --include="*.md" | grep -v "docs/plans/" | grep -v "README.md:" | grep -v "README.ko.md:"
```

매치가 있으면 archive 외 영역의 broken link — 별도 fix 필요. 없으면 본 task 영역 완료.

## Dependencies

- **task-01 완료** — `git mv` 후 README.md 가 영문, README.ko.md 가 한국어.
- task-02·03·04·05 와 영역 분리: task-02~05 는 README.md 본문 변경, task-06 은 README.md + README.ko.md 의 link 만. 다만 README.md 동시 편집 위험 → 순차 진행 권고.
- 외부 패키지: 없음.

## Verification

```bash
# 1. README.md 안에 README.en.md 참조 0건
cd /Users/d9ng/privateProject/gemento && grep -F "README.en.md" README.md && echo "FAIL stale en.md link in README.md" || echo "OK README.md has no stale en.md link"

# 2. README.ko.md 안에 README.en.md 참조 0건
cd /Users/d9ng/privateProject/gemento && grep -F "README.en.md" README.ko.md && echo "FAIL stale en.md link in README.ko.md" || echo "OK README.ko.md has no stale en.md link"

# 3. README.md 안에 README.ko.md 링크 1건 이상
cd /Users/d9ng/privateProject/gemento && grep -F "README.ko.md" README.md && echo "OK README.md cross-links to README.ko.md"

# 4. README.ko.md 안에 README.md 링크 1건 이상
cd /Users/d9ng/privateProject/gemento && grep -F "[README.md]" README.ko.md && echo "OK README.ko.md cross-links to README.md" || \
grep -F "(./README.md)" README.ko.md && echo "OK README.ko.md cross-links to README.md (alt form)"

# 5. archive 외 영역의 broken README.en.md 참조 0건 (informational)
cd /Users/d9ng/privateProject/gemento && grep -rlE "README\.en\.md" --include="*.md" | grep -v "docs/plans/" | grep -v "^README\.md$" | grep -v "^README\.ko\.md$" || echo "OK no broken en.md refs outside plans/"

# 6. cross-link target 실재
test -f /Users/d9ng/privateProject/gemento/README.ko.md && echo "OK README.ko.md exists"
test -f /Users/d9ng/privateProject/gemento/README.md && echo "OK README.md exists"

# 7. 다른 파일 변경 없음 (README.md, README.ko.md 만)
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only | grep -vE "^README\.(md|ko\.md|en\.md)$" | grep -v "^$" || echo "OK no extra changes"
```

## Risks

- **archive plan 안의 README.en.md 참조**: `docs/plans/readme-memento-acknowledgement*` 등 archived plan 에 README.en.md 참조 잔존. 본 task 는 archive 영역 정정 안 함 (history 보존). Verification 5 가 archive 외부만 확인 — 안전.
- **link form 차이**: `[label](./README.ko.md)` vs `[label](README.ko.md)` — 둘 다 GitHub 에서 작동. 본 task 는 일관성 위해 `./` prefix 권고하나 자유 재량.
- **task-02·03·04·05 와 README.md 동시 편집 충돌**: 동일 파일 — 순차 진행 (plan Constraints).
- **README.ko.md 안의 영문 README 링크 외 다른 cross-link**: 사전 정찰로 line 21 만 발견. 다른 위치에 잔존하면 Verification 1·2 가 잡음.

## Scope boundary

**Task 06 에서 절대 수정 금지**:

- README.md 의 본문 (task-02~05 결과물).
- README.ko.md 의 본문 (한국어 사용자 경험 유지) — link 1 줄만 정정.
- `docs/plans/readme-memento-acknowledgement*` 의 README.en.md 참조 — archived plan, history 보존.
- `docs/reference/`, `experiments/` 의 모든 파일.
- `.gitignore`, `.env.example`.

**허용 범위**:

- `README.md:5` 의 한국어 cross-link 정정 (`README.md` → `README.ko.md`, label 영문화).
- `README.ko.md:21` 의 영문 cross-link 정정 (`README.en.md` → `README.md`).
- 추가 cross-link 발견 시 동일 패턴 정정 (Verification 1·2 가 잡으면 그 위치만).
