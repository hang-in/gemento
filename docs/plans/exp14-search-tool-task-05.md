---
type: plan-task
status: pending
updated_at: 2026-05-05
parent_plan: exp14-search-tool
parallel_group: E
depends_on: [04]
---

# Task 05 — 분석 + H13 verdict + 문서 갱신

## Changed files

- `docs/reference/exp14-search-tool-analysis-<TS>.md` — **신규**. 분석 보고서 (Exp12/13 패턴)
- `docs/reference/results/exp-14-search-tool.md` — **신규**. result.md
- `docs/reference/researchNotebook.md` — **수정**. H13 entry + 축 매트릭스 + Exp14 섹션 append + frontmatter `updated_at`
- `docs/reference/researchNotebook.en.md` — **수정 (Closed-append-only)**. ## Exp14 섹션 + frontmatter `updated_at`. 표 / 기존 entry 무변경
- `docs/plans/index.md` — **수정**. Active → Recently Done — Stage 5 이동
- `docs/plans/exp14-search-tool.md` + task-NN — **수정**. status: done
- `README.md` / `README.ko.md` — **사용자 결정** 후 H13 entry 추가

신규 2, 수정 5+ (사용자 결정 시).

## Change description

### 활용 권장 — `gemento-verdict-record` 스킬

본 task = `gemento-verdict-record` 스킬의 본격 활용 시점. 영문 노트북 Closed-append-only 정책 + 한국어 노트북 표/매트릭스/섹션 동시 갱신 + index.md 이동을 일괄 처리.

### Step 1 — task-04 결과 정합성 확인

```bash
.venv/Scripts/python -c "
import json
from collections import defaultdict

# 결과 파일 로드 (사용자가 제공한 파일명 사용)
base = json.load(open('experiments/exp14_search_tool/results/exp14_baseline_abc_chunked_<TS>.json', encoding='utf-8'))
search = json.load(open('experiments/exp14_search_tool/results/exp14_search_tool_abc.json', encoding='utf-8'))

# 정합성: 50 + 50 = 100 trial, conditions 분리
assert len(base['trials']) == 50 or len(base['trials']) == 50
assert base.get('conditions') == ['baseline_abc_chunked']
assert search.get('conditions') == ['abc_search_tool']
print('정합성 ok')
"
```

### Step 2 — 분석 통계 산출

Exp12/13 분석 패턴 그대로:

```python
# per-condition aggregate
# per-task Δ
# 카테고리별 Δ (size_class × hop_type 매트릭스 — longctx 특화)
# Cohen's d, paired t, Wilcoxon, Bootstrap 95% CI
# tool call 통계 (search 호출 수, query 다양성)
# evidence hit rate (gold_evidence_chunks vs retrieved chunks)
# 시간 비교 (avg_dur)
# error mode (Stage 2B FailureLabel)
```

**본 plan 특화 메트릭**:
- size_class × Δ (small / medium / large)
- hop_type × Δ (needle / 2hop / 3hop)
- tool_call_count × accuracy 의 상관 (호출 빈도와 정답률 관계)
- evidence hit rate (gold_evidence_chunks 의 retrieval 성공률)
- query lexical 분석 (cycle 별 query 의 token overlap)

### Step 3 — H13 verdict

verdict 결정 트리:

| 조건 | verdict |
|------|---------|
| Δ ≥ +0.10 + p<0.05 | 강한 채택 |
| Δ ≥ +0.05 + p<0.05 | 채택 |
| Δ ≥ +0.05 + p≥0.05 | ⚠ 조건부 채택 (검정력 한계) |
| \|Δ\| < 0.05 | ⚠ 미결 |
| Δ ∈ (−0.05, 0) | ⚠ 미결 |
| Δ < −0.05 | ⚠ 미결 (실효적 기각) 또는 기각 |

### Step 4 — 분석 보고서 신규

`docs/reference/exp14-search-tool-analysis-<TS>.md` (Exp13 = `2026-05-05` 형식). Exp13 의 분석 보고서 (`exp13-reducer-role-analysis-2026-05-05.md`) 형식 정확 복제 — 단 다음 섹션 추가:

- §5 mechanism — query 다양성 case study (특정 task 의 cycle 별 query 진화)
- §6 tool call 통계 (호출 빈도 distribution + accuracy 상관)
- §7 evidence hit rate (vs gold_evidence_chunks)
- §10 비교: Exp09 RAG arm (1-shot retrieve) vs 본 plan (agent-active iterative)
- §11 Stage 5 framework 갱신 — Tool 축 검증 라인 (H7 / H8 / H13)

### Step 5 — result.md 신규

`docs/reference/results/exp-14-search-tool.md`. Exp13 result.md 형식 정확 복제.

### Step 6 — researchNotebook 갱신 (한·영)

**한국어** (`researchNotebook.md`):
- frontmatter `updated_at` → 마감일
- 핵심 가설 표 H13 row 추가
- 축 매트릭스 Exp14 row 추가 (Tattoo / Tool / Role / Orchestrator — Tool ✅)
- `### Exp14: Search Tool` 섹션 append (Exp13 섹션 형식 정확 복제)

**영문** (`researchNotebook.en.md`, **Closed-append-only**):
- frontmatter `updated_at` → 마감일 (예외 한 줄)
- `## Exp14 — Search Tool note (<date>)` 섹션을 `## Change History` 직전에 insert
- 본문 마지막 boilerplate 의무: `The hypothesis table above (H1~H12) remains unchanged (Closed-append-only policy). H13's entry is a new addition only.`
- 표 / 기존 entry 어떤 줄도 변경 금지

`gemento-verdict-record` 스킬의 안전 패턴 (`Edit` with anchor `---\n\n## Change History`) 준수.

### Step 7 — index.md + plan status

- `docs/plans/index.md`: Active 의 `exp14-search-tool` 라인 제거 + Recently Done — Stage 5 의 맨 위에 추가 (Δ + Cohen d + 한 줄 요약 + verdict + 날짜)
- `docs/plans/exp14-search-tool.md` + task-04 + task-05: status: done + updated_at 갱신

### Step 8 — README (사용자 결정)

H13 entry 추가는 H10/H11/H12 패턴 따라:
- README.md / README.ko.md 의 핵심 가설 표
- "What worked / What didn't" 섹션 단락
- Roadmap entry
- Last updated

**사용자 결정 의무**: README 갱신 진행할지 사용자에게 명시 질의 후 진행.

### Step 9 — 통합 commit

```bash
git add docs/reference/exp14-search-tool-analysis-*.md \
        docs/reference/results/exp-14-search-tool.md \
        docs/reference/researchNotebook.md \
        docs/reference/researchNotebook.en.md \
        docs/plans/index.md \
        docs/plans/exp14-search-tool.md \
        docs/plans/exp14-search-tool-task-04.md \
        docs/plans/exp14-search-tool-task-05.md
# README 사용자 결정 시 추가
git commit -m "docs(stage-5-exp14-task-05): Exp14 Search Tool 마감 — H13 verdict + 분석 + 문서 통합"
```

## Dependencies

- task-04 마감 (사용자 직접 실행 결과 JSON 2 종)
- 기존 `experiments/measure.py:score_answer_v3` — read-only 채점
- 기존 분석 보고서 (Exp11/12/13) — 패턴 참조
- `gemento-verdict-record` 스킬 — 영문 노트북 정책 강제
- `scipy` — paired t / Wilcoxon / bootstrap (이미 사용 중)

## Verification

```bash
# 1) 분석 보고서 + result.md 신규 + 노트북 갱신
ls docs/reference/exp14-search-tool-analysis-*.md
ls docs/reference/results/exp-14-search-tool.md

# 2) 영문 노트북 정책 검증
.venv/Scripts/python -c "
with open('docs/reference/researchNotebook.en.md', 'r', encoding='utf-8') as f:
    content = f.read()
assert '## Exp14 — Search Tool note' in content, 'Exp14 섹션 부재'
assert 'H1~H12' in content, 'boilerplate 부재'
# 표 row 수 검증 (H1~H9c = 11 row 그대로)
import re
table_rows = [l for l in content.split('\n') if re.match(r'^\| H[0-9]', l)]
print(f'H## table rows: {len(table_rows)} (Exp13 마감 시 11 그대로)')
print('영문 노트북 정책 검증 ok')
"

# 3) 한국어 노트북 갱신
.venv/Scripts/python -c "
with open('docs/reference/researchNotebook.md', 'r', encoding='utf-8') as f:
    content = f.read()
assert '### Exp14: Search Tool' in content, 'Exp14 섹션 부재'
assert '| **H13**' in content, 'H13 row 부재'
assert 'Exp14 (Search Tool)' in content, '축 매트릭스 갱신 부재'
print('한국어 노트북 갱신 ok')
"

# 4) plan + index status
.venv/Scripts/python -c "
import re
with open('docs/plans/exp14-search-tool.md', 'r', encoding='utf-8') as f:
    content = f.read()
assert re.search(r'^status: done', content, re.MULTILINE), 'status: done 미적용'
print('plan status: done ok')
"
```

4 명령 모두 정상.

## Risks

- **Risk 1 — context overflow 의 H13 verdict 영향**: longctx-large 의 baseline_abc_chunked 가 다수 fail 시 Δ 계산 왜곡. 분석 보고서 §12 한계에 명시 + size_class 별 Δ 별도 보고
- **Risk 2 — tool_neglect 의 H13 verdict 영향**: abc_search_tool 의 일부 trial 이 search 호출 0회로 baseline 과 동등 → Δ 0. tool call count 통계로 명시 + neglect rate 보고
- **Risk 3 — Sonnet 의 영문 노트북 정책 위반**: H13 entry 작성 시 표 갱신 또는 기존 entry 변경 시도 가능. `gemento-verdict-record` 스킬 활용 + 정책 검증 의무 (Verification 2)
- **Risk 4 — placeholder 0 의무**: 분석 보고서의 모든 `<TS>`, `<file>`, 수치 placeholder 채움. 빈 곳 없음
- **Risk 5 — README 갱신 임의 진행**: 사용자 결정 의무. Sonnet/Architect 가 사용자 명시 동의 없이 README 변경 금지

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/**/*.py` (코드)
- `experiments/**/results/*.json` (결과 데이터)
- `experiments/tasks/*.json` (taskset)
- `docs/reference/conceptFramework.md` (별도 plan 영역)
- 다른 실험의 분석 보고서 / result.md (Exp00~13 영역)

본 task 에서 **변경 가능**:
- `docs/reference/exp14-search-tool-analysis-<TS>.md` (신규)
- `docs/reference/results/exp-14-search-tool.md` (신규)
- `docs/reference/researchNotebook.md` (한국어, 표 + 매트릭스 + 섹션 + frontmatter)
- `docs/reference/researchNotebook.en.md` (영문, **append-only** — 섹션 + frontmatter `updated_at` 만)
- `docs/plans/index.md` (Active → Recently Done)
- `docs/plans/exp14-search-tool.md` + task-04 + task-05 (status: done)
- `README.md` / `README.ko.md` (**사용자 결정 후만**)
