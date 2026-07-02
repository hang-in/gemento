---
type: plan-task
status: pending
updated_at: 2026-07-03
parent_plan: exp24-a2a-planner-executor
parallel_group: D
depends_on: [02, 03]
---

# Task 04 — 분석 + Stage 12 verdict

## Changed files

- `docs/reference/researchNotebook.md` (수정, 한국어) — 핵심가설 표 H24 + 축 매트릭스 Exp24 + §22 상세 + frontmatter (`gemento-verdict-record` 스킬).
- `docs/reference/researchNotebook.en.md` (수정, 영문 **Closed-append-only**) — Exp24 섹션 append.
- `docs/plans/index.md` (수정) — Active → Recently Done Stage 12.

요약: 신규 0, 수정 3. **A/B 실행 결과(Task 03) 후 진행.**

## Change description

### 배경
Task 01~03 완료 + 사용자/에이전트가 A/B 실행 → `v24_a2a_result.json` 확보 후 verdict. 방향은 데이터 따라감.

### Step 1 — 결과 판정
control vs a2a finalized/correct 비교 + a2a 비용(호출 2배/latency). 핵심 대비:
- a2a finalized 가 control(~47%) 대비 유의 상승(→ 스코프 분할 유효, probe 100% 에 근접?) 인가.
- planner 실패(finding 못 찾음) vs executor 실패 분해(가능하면 로그로).

### Step 2 — verdict (`gemento-verdict-record` 스킬)
H24 — "Planner→Executor 스코프 분할이 per-attempt overload 를 우회해 finalization 을 올린다". verdict:
- a2a 유의 상승 + 비용 수용가능 → **채택/조건부 채택** — per-attempt 근본 레버 확보(H22/H23 실패 뒤 첫 성공).
- 무개선 → **미결/기각** — 구조 추가 무효(H12/H13 계열) 재확인 → **per-attempt = retry 수용** 최종 확정.

### Step 3 — Stage 함의
- Orchestrator 축: proposer 분할이 per-attempt 레버인가. probe(scoped 100%) → 실제 a2a 간 gap 해석.
- per-attempt 트랙 최종 정리: 프롬프트(H22)·도구(H23)·구조분할(H24) 스펙트럼.

## Dependencies

- Task 02 통과.
- Task 03 드라이버로 A/B 실행 → `v24_a2a_result.json` 존재.
- 스킬: `gemento-verdict-record`.

## Verification

```bash
# 1. 결과 JSON 존재 + 파싱
python -c "import json; d=json.load(open(r'experiments/exp15_context_router/diagnostics/v24_a2a_result.json',encoding='utf-8')); print('arms:', list(d.get('arms',{}).keys()))"
```

```bash
# 2. 영문 append-only (삭제 라인 = updated_at 만)
git diff docs/reference/researchNotebook.en.md | grep '^-' | grep -v '^---' || echo "append-only OK"
echo "rows before/after: $(git show HEAD:docs/reference/researchNotebook.en.md | grep -c '^| \*\*H') / $(grep -c '^| \*\*H' docs/reference/researchNotebook.en.md)"
```

```bash
# 3. index Stage 12 + placeholder 0
grep -c "exp24-a2a-planner-executor" docs/plans/index.md
grep -rn "TODO\|TBD\|0\.XXX\|<verdict>" docs/reference/researchNotebook.md || echo "placeholder 0 OK"
```

## Risks

1. **영문 append-only 위반** — 스킬 강제 + Verification 2.
2. **실행 미완 verdict** — Verification 1 선행.
3. **verdict 과대/과소** — 소표본(n=15)/단일 task/비용 caveat 명시. a2a 유효해도 비용 대비 retry 와 비교. README 갱신 사용자 결정.

## Scope boundary

**수정 금지**: 코드/테스트/드라이버/결과 JSON, conceptFramework(별도), README(사용자 결정). 노트북 2 + index 만.
