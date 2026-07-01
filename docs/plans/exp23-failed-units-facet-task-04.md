---
type: plan-task
status: pending
updated_at: 2026-07-02
parent_plan: exp23-failed-units-facet
parallel_group: D
depends_on: [02, 03]
---

# Task 04 — 분석 + Stage 11 verdict

## Changed files

- `docs/reference/researchNotebook.md` (수정, 한국어) — 핵심가설 표 H23 row + 축 매트릭스 Exp23 + §21 상세 섹션 + frontmatter (`gemento-verdict-record` 스킬).
- `docs/reference/researchNotebook.en.md` (수정, 영문 **Closed-append-only**) — Exp23 섹션 append 만.
- `docs/plans/index.md` (수정) — Active → Recently Done Stage 11.

요약: 신규 0, 수정 3. **A/B 실행 결과(Task 03) 후 진행.**

## Change description

### 배경
Task 01~03 완료 + Task 03 드라이버로 A/B 실행 → `v23_failed_units_result.json` 확보 후 verdict 기록. verdict 방향은 데이터 따라감(Risk 5).

### Step 1 — 결과 판정
3 arm 매트릭스에서 per-arm finalized/correct/used_fu 산출. 핵심 대비:
- **fu_offered vs control**: 도구 제공만으로 개선? (H21 저사용 경고 검증)
- **fu_mandatory vs control**: 강제 시 개선? = "쿼리 형성 우회 레버"의 상한.
- used_fu rate: offered 에서 모델이 실제로 도구를 썼나.

### Step 2 — verdict 기록 (`gemento-verdict-record` 스킬)
가설 H23 — "결정론적 실패-unit 도구가 retrieval_gap 을 우회해 per-attempt 를 올린다". verdict 4종 중 데이터 대응:
- fu_mandatory 유의 개선 + offered 무효 → **조건부 채택 (사용 강제 시)**.
- 양 arm 개선 → 채택.
- 양 arm 무효 → 미결/기각 (retrieval 넘어선 병목 = §20 재확인).

스킬이 3파일 일관 기록 (영문 append-only 강제).

### Step 3 — Stage 함의
- Tool 축 sub-distinction 갱신: deterministic computation(H7/H8+) / agent-iterative retrieval(H13−) / facet aggregation(H21 집계+) / **failed-unit preset(H23 ?)**.
- per-attempt 레버 결론: 프롬프트(H22 반증) vs 도구-제공(H21 저사용) vs 도구-강제(H23) 스펙트럼 정리.

## Dependencies

- Task 02 통과 (회귀 게이트 green).
- Task 03 드라이버로 **A/B 실행** → `v23_failed_units_result.json` 존재.
- 스킬: `gemento-verdict-record`.
- 기존 파일: researchNotebook.md/.en.md, index.md.

## Verification

```bash
# 1. 결과 JSON 존재 + 파싱
python -c "import json; d=json.load(open(r'experiments/exp15_context_router/diagnostics/v23_failed_units_result.json',encoding='utf-8')); print('arms:', list(d.get('arms', d.get('by_arm', {})).keys()))"
```

```bash
# 2. 영문 노트북 append-only 위반 없음 (삭제 라인 = updated_at 만)
git diff docs/reference/researchNotebook.en.md | grep '^-' | grep -v '^---' || echo "append-only OK"
```

```bash
# 3. 영문 표 row 무변경
echo "before: $(git show HEAD:docs/reference/researchNotebook.en.md | grep -c '^| \*\*H')  after: $(grep -c '^| \*\*H' docs/reference/researchNotebook.en.md)"
```

```bash
# 4. index.md Stage 11 등록 + placeholder 0
grep -c "exp23-failed-units-facet" docs/plans/index.md
grep -rn "TODO\|TBD\|0\.XXX\|<verdict>" docs/reference/researchNotebook.md || echo "placeholder 0 OK"
```

## Risks

1. **영문 append-only 위반** — 스킬 강제 + Verification 2/3.
2. **실행 미완 상태 verdict** — Verification 1 로 결과 JSON 선행 확인.
3. **verdict 과대** — 소표본(n=15)/단일 task. 조건부/축 명시. README 갱신은 사용자 결정.
4. **used_fu 해석** — offered 에서 도구 미사용이면 "offered 무효"는 능력이 아닌 사용 문제 — verdict 에 분리 기술.

## Scope boundary

**수정 금지**: 코드(`context_tools.py`/드라이버/테스트), 결과 JSON, conceptFramework(별도), README(사용자 결정). 본 task 는 노트북 2 + index 만.
