---
type: plan-task
status: pending
updated_at: 2026-07-01
parent_plan: retrieval-discipline-opt-in
parallel_group: D
depends_on: [02, 03]
---

# Task 04 — 문서 + Stage 10 verdict

## Changed files

- `docs/reference/conceptFramework.md` (수정) — retrieval-discipline opt-in 을 "언제 켜나" 가이드에 추가 (under-query 실패 특화, MANDATORY 와 독립).
- `docs/reference/researchNotebook.md` (수정, 한국어) — Stage 10 verdict 표 갱신 + 새 섹션 append + 축 매트릭스 갱신 (`gemento-verdict-record` 스킬 경유).
- `docs/reference/researchNotebook.en.md` (수정, 영문 **Closed-append-only**) — 새 entry append 만. 기존 문장/표 절대 수정 금지.
- `docs/plans/index.md` (수정) — Active → Recently Done Stage 10 이동 (`gemento-verdict-record` 담당).

요약: 신규 0, 수정 4. **재검증 결과(Task 03 사용자 실행) 반영 후 진행.**

## Change description

### 배경
Task 01~03 완료 + 사용자가 Task 03 재검증(n≥10, task A+B)을 실행해 결과 JSON 이 나온 뒤, verdict 를 기록한다. verdict 방향은 **데이터 따라감** (Risk 5): 재검증이 레버 A/B(+50pp)를 재현하면 채택, task 의존적이면 조건부, 소멸하면 미결/롤백 근거.

### Step 1 — 재검증 결과 판정
`diagnostics/v22_retrieval_discipline_result.json` 읽어 task × arm 매트릭스로 Δfinalized / Δempty_tattoo / Δcorrect 산출. 레버 A/B 대비 재현 여부 + task A vs task B 차이(집계 task 에서 더 큰가?) 기술.

### Step 2 — verdict 기록 (`gemento-verdict-record` 스킬)
가설 라벨 부여 (예: H22 — retrieval-discipline nudge 가 under-query finalization 실패를 완화). 스킬이 3파일 일관 기록:
- researchNotebook.md: 표 갱신 + 새 섹션 + 축 매트릭스.
- researchNotebook.en.md: **append-only** entry.
- index.md: Active → Recently Done Stage 10.

### Step 3 — conceptFramework "언제 켜나" 가이드
`retrieval_discipline_prompt` 을 mandatory 와 나란히 실패-모드별 처방으로 기술:
- `mandatory_tool_prompt`: 단일-needle 전사누락 (Exp16b, 큰 로그 1-needle).
- `retrieval_discipline_prompt`: under-query 조기포기 (집계/대형 로그 crashloop, 레버 A/B / Stage 10).
- 둘 다 opt-in, 기본 off, caller-decides, 자동 게이트 없음.

## Dependencies

- Task 02 통과 (회귀 게이트 green).
- Task 03 드라이버로 **사용자가 재검증 실행** → `v22_retrieval_discipline_result.json` 존재.
- 스킬: `gemento-verdict-record` (영문 append-only 강제).
- 기존 파일: researchNotebook.md/.en.md, conceptFramework.md, index.md.

## Verification

```bash
# 1. 결과 JSON 존재 + 파싱 (재검증 완료 확인)
python -c "import json; d=json.load(open(r'experiments/exp15_context_router/diagnostics/v22_retrieval_discipline_result.json',encoding='utf-8')); print('arms:', list(d.get('arms', d).keys()) if isinstance(d,dict) else 'n/a')"
```

```bash
# 2. 영문 노트북 append-only 위반 없음 (기존 라인 수 ≤ 신규 라인 수, 기존 내용 보존)
git diff --stat docs/reference/researchNotebook.en.md
git diff docs/reference/researchNotebook.en.md | grep '^-' | grep -v '^---' || echo "append-only OK (삭제 라인 없음)"
```

```bash
# 3. index.md Stage 10 등록 확인
grep -c "retrieval-discipline-opt-in" docs/plans/index.md
```

```bash
# 4. placeholder 0 (분석 문서 의무)
grep -rn "TODO\|TBD\|XXX\|placeholder" docs/reference/researchNotebook.md docs/reference/conceptFramework.md || echo "placeholder 0 OK"
```

## Risks

1. **영문 노트북 기존 내용 수정** — append-only 위반. → `gemento-verdict-record` 스킬이 강제, Verification 2 로 삭제 라인 0 확인.
2. **재검증 미완 상태로 verdict 작성** — 데이터 없이 결론. → Verification 1 로 결과 JSON 존재 선행 확인. 없으면 Task 04 진행 금지.
3. **verdict 과대** — 소표본/task 의존을 무시하고 "채택" 단정. → 조건부/축 명시(Exp21 교훈: task-specific), README 갱신은 사용자 결정.

## Scope boundary

**수정 금지**: 코드(`system_prompt.py`/`orchestrator.py`/드라이버), 테스트, 결과 JSON. README.md/README.ko.md 갱신은 **사용자 결정** (본 task 자동 아님). 본 task 는 문서 4개(conceptFramework + 노트북 2 + index)만.
