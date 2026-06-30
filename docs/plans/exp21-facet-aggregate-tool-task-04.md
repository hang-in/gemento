---
type: plan-task
status: pending
updated_at: 2026-06-30
parent_plan: exp21-facet-aggregate-tool
parallel_group: C
depends_on: [03]
---

# Task 04 — 분석 + H21 verdict

## Changed files

- `docs/reference/exp21-facet-ab-analysis-2026-06-30.md` (신규) — A/B 분석(non-null rate 1차, score 2차, facet 사용률, 메커니즘).
- `docs/reference/researchNotebook.md` (수정) — H21 verdict 표/섹션 추가 (한국어, `gemento-verdict-record` 스킬).
- `docs/reference/researchNotebook.en.md` (수정) — **Closed-append-only** H21 entry (기존 절대 무수정).
- `docs/plans/index.md` (수정) — Active→Recently Done 이동(`gemento-verdict-record` 스킬).

> 신규 1, 수정 3.

## Change description

### 배경
**실험 실행/결과 JSON 존재 후에만** 진행. placeholder 금지 — 모든 수치는 `results/exp21_facet_ab_gemma4_e4b.json` 실측.

### Step 1 — 분석 문서
- arm×task 매트릭스: non_null_rate(1차), mean_score(2차), mean_attempts, facet_calls.
- 핵심 질문: **grep_facet 이 grep_only 대비 finalization(non-null rate) 을 회복했는가?**
  - 회복 + 유의 → H21 채택(facet 이 절단-firehose 병목 해소).
  - 미회복(0v0 또는 무차) → H21 기각, 병목=harness 수렴(orchestrator 사안)으로 결론.
  - facet_calls==0 → "도구 제공≠사용"(under-query at tool-arg level) finding.
- Exp20 진단([[exp20-finalization-diagnosis]])과 연결: 같은 megalog/task 에서 도구만 바꾼 통제 비교.
- caveat: n=5 소표본, keyword scorer artifact(Exp19 교훈), single model(e4b).

### Step 2 — H21 verdict (`gemento-verdict-record` 스킬 사용)
- 한국어 `researchNotebook.md`: H21 표 갱신 + 새 섹션 append + 축 매트릭스 갱신.
- 영문 `researchNotebook.en.md`: **append-only** — 기존 entry/표/문장 절대 수정 금지, Change History 위에 H21 entry append.
- verdict 형식: ✅ 채택 / ⚠ 조건부 / ⚠ 미결 / ❌ 기각 + Δ(non-null rate) + 메커니즘 1-2 문장.

### Step 3 — index.md 이동
Active 의 exp21 entry → Recently Done — Stage 9 로 이동(요약 + verdict + 커밋 해시 + 날짜).

### Step 4 — test_static 위생(필요 시)
신규 `exp21_facet_ab_gemma4_e4b.json` 으로 `tests/test_static` 의 결과-인벤토리 카운트가 흔들리면 갱신(Stage 7/8 선례). `python -m pytest tests/test_static* -q` 로 확인.

## Dependencies

- task-03 실행 완료 + 결과 JSON 존재.
- 스킬: `gemento-verdict-record`(영문 append-only 강제).
- 기존(read-only): `exp20-finalization-diagnosis`(메모리), Exp19/Exp20 결과(대조).

## Verification

```bash
# 1) 결과 JSON 존재 + 파싱
cd experiments && python -c "import json; d=json.load(open('exp15_context_router/results/exp21_facet_ab_gemma4_e4b.json',encoding='utf-8')); print({a:{t:v['non_null_rate'] for t,v in d['arms'][a].items()} for a in d['arms']})"

# 2) 영문 노트북 append-only 검증 (기존 라인 무수정 — diff 가 순수 추가인지)
cd "D:/privateProject/gemento" && git diff docs/reference/researchNotebook.en.md | grep -E "^-" | grep -v "^---" || echo "append-only OK (no deletions)"

# 3) 문서 메타 (type/status/updated_at)
cd "D:/privateProject/gemento" && head -5 docs/reference/exp21-facet-ab-analysis-2026-06-30.md

# 4) test_static (인벤토리 카운트)
cd experiments && python -m pytest tests/test_static* -q
```

## Risks

1. **placeholder 유혹** — 실행 전 분석 작성. 절대 금지(실측 후에만). 대응: Verification 1 로 결과 존재 강제.
2. 영문 노트북 기존 수정 → append-only 위반. 대응: `gemento-verdict-record` 스킬 + Verification 2.
3. H21 기각/0v0 결과를 "실패"로 축소 기록 — 오히려 "병목=harness 수렴"은 가치 있는 finding. 정직하게 기록.
4. keyword scorer artifact 로 score 가 finalization 을 왜곡 → non-null rate 1차, score 2차 명시.

## Scope boundary

- **수정 금지**: `context_tools.py`/`native_ollama_caller.py`/`run_v21_facet_ab.py`(코드 task 영역), `orchestrator.py`, `conceptFramework.md`.
- 본 task 는 분석/verdict/index 문서만.
