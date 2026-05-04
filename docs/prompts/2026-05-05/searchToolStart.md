---
type: prompt
status: ready
updated_at: 2026-05-05
for: Sonnet (Developer)
plan: exp14-search-tool
purpose: Stage 5 Exp14 진행 신호 — Search Tool (Tool 축 신규, agent-active retrieval)
prerequisites: Stage 2A + 2B + 2C + Stage 4 (Exp11) + Stage 5 (Exp12, Exp13) 모두 마감
---

# Stage 5 (Exp14) 진행 프롬프트 (Sonnet Developer)

복붙하여 Sonnet 세션에서 실행. self-contained.

---

너는 Developer (Sonnet) 역할이다. Architect (Opus) 가 작성한 Stage 5 Exp14 (Search Tool) plan 을 그대로 진행한다.

## 0. 핵심 규칙

- Plan 그대로 진행. scope 확장 금지
- Changed files 만 수정
- Risk / Scope boundary 위반 직전 즉시 보고
- 사용자 결정 1-8 모두 확정 (Architect 위임 "권장으로 가자, 옵션 ii-A"). 변경 금지
- Task 04 = 사용자 직접 실행 — 모델 호출 금지
- 본 plan = **외부 API 0** (local Gemma + 결정적 BM25)
- **기존 `bm25_tool.py` (Exp09 자산) 재사용** — 신규 BM25 구현 금지
- **SQLite FTS5 도입 금지** — 별도 Stage 5 plan 영역
- **Exp12/13 `run.py` 의 패턴 정확 재사용** — 임의 단순화 금지 (`gemento-experiment-scaffold` 스킬 활용)

## 1. 컨텍스트 동기

```bash
git pull --ff-only
git log --oneline -5
```

**prerequisite 검증**:

```bash
.venv/Scripts/python -c "
# Stage 2A
from experiments.run_helpers import classify_trial_error, build_result_meta, check_error_rate
# Stage 2B
from experiments.schema import FailureLabel
# Stage 2C analyze
from experiments.exp_h4_recheck.analyze import classify_error_mode, count_assertion_turnover
# Exp12 Extractor
from experiments.system_prompt import EXTRACTOR_PROMPT, build_extractor_prompt
# Exp13 Reducer
from experiments.system_prompt import REDUCER_PROMPT, build_reducer_prompt
# Exp14 prerequisite — bm25_tool / chunker / longctx_taskset
from experiments.tools import bm25_retrieve, chunk_document
import json
with open('experiments/tasks/longctx_taskset.json', 'r', encoding='utf-8') as f:
    ts = json.load(f)
assert len(ts['tasks']) == 10
import inspect
import sys; sys.path.insert(0, 'experiments')
from orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
for opt in ('c_caller', 'extractor_pre_stage', 'reducer_post_stage'):
    assert opt in sig.parameters, f'{opt} 미적용'
print('ok: Stage 2A + 2B + 2C + Stage 4 + Stage 5 Exp12/13 마감 + Exp14 prerequisite (bm25/chunker/longctx_taskset)')
"
```

## 2. 읽어야 할 plan 파일

```
docs/plans/exp14-search-tool.md         # parent
docs/plans/exp14-search-tool-task-01.md # group A — search_chunks TOOL_SCHEMA + stop-words
docs/plans/exp14-search-tool-task-02.md # group B — orchestrator search_tool hook
docs/plans/exp14-search-tool-task-03.md # group C — run.py
docs/plans/exp14-search-tool-task-04.md # group D — 사용자 직접 실행
docs/plans/exp14-search-tool-task-05.md # group E — 분석 + verdict + 문서
```

## 3. 사용자 결정 1-8 (Architect 위임 확정)

| 결정 | 값 |
|------|---|
| 1. BM25 backend | **기존 `bm25s` 재사용** — Exp09 자산, SQLite FTS5 미도입 |
| 2. Tool schema | `search_chunks(query, top_k=5)` — top_k clamp [1, 10] |
| 3. Document corpus 주입 | orchestrator 가 closure 로 주입 — agent 는 corpus 존재 모름 |
| 4. Stop-words | English 표준 stop-words 추가 (한 줄 fix, _tokenize 만 영향) |
| 5. taskset | `longctx_taskset.json` 그대로 (10 task) — 신규 task 추가 금지 |
| 6. condition | 2 (baseline_abc_chunked + abc_search_tool) |
| 7. trial / cycles | 5 / 8 (Stage 2C/Exp11/12/13 정합) |
| 8. 메커니즘 측정 | accuracy + tool call count + query 다양성 + evidence hit rate |

## 4. 진행 순서

```
Stage 1 (plan-side):
  Group A: task-01 (search_chunks TOOL_SCHEMA + stop-words)
       ↓
  Group B: task-02 (orchestrator search_tool hook)
       ↓        ↓
  Group C: task-03 (run.py — 01/02 의존, gemento-experiment-scaffold 스킬 활용)
       ↓
Stage 2 (사용자 직접):
  Group D: task-04 (100 trial 실험, ~17-25h)
       ↓
Stage 3 (분석):
  Group E: task-05 (분석 + H13 + 문서, gemento-verdict-record 스킬 활용)
```

권장: task-01 → 02 → 03 직렬, 그 후 task-04 사용자 호출.

## 5. 각 subtask 진행 패턴

1. subtask 파일 read (Step + Verification + Risk + Scope boundary)
2. Step 순서대로 실행
3. Verification 명령 + 결과 캡처
4. commit message: `feat(stage-5-exp14-task-NN): <summary>` 또는 `docs(stage-5-exp14-task-NN): ...`
5. 다음 subtask 이동 전 사용자 confirm

## 6. 사용자 호출 분기

- Verification 실패
- Scope boundary 위반 직전
- Risk 발견 — 특히:
  - task-01 의 Risk 2 — Exp09 RAG arm 의 tokenizer 변경 (stop-words 영향)
  - task-02 의 Risk 1 — A 호출 분기에 search_tool 미주입
  - task-03 의 Risk 1 — Exp12/13 패턴 복사 실패
- task-04 진행 시점 (사용자 직접 실행 신호)
- task-05 README 갱신 결정

## 7. Task 04 특이사항 (사용자 직접 실행)

**Sonnet 직접 실행 금지**. 책임:
1. Task 04 plan 본문 명령 정합성 확인
2. 사용자에게 명령 제시 (분할 옵션 권장 — A-1 / A-2)
3. dry-run 명령 사용자에게 제시 (1 task × 1 trial × abc_search_tool, ~10-15min)
4. 사용자 결과 받으면 task-05 진행
5. **모델 호출 / dry-run / 결과 JSON 생성 절대 금지**

## 8. Task 05 특이사항

분석 보고서 + 5종 문서 갱신:
- analysis 신규 (placeholder 0 의무)
- result.md 신규 (`docs/reference/results/exp-14-search-tool.md`)
- researchNotebook.md (한국어): H13 entry + Exp14 섹션 + 축 매트릭스
- researchNotebook.en.md: **Closed 추가만**
- README 갱신: **사용자 결정**

분석 보고서의 **본 plan 특화 메트릭** 의무:
- size_class × Δ (small / medium / large)
- hop_type × Δ (needle / 2hop / 3hop)
- tool_call_count × accuracy 상관
- evidence hit rate (vs gold_evidence_chunks)
- Exp09 RAG arm 과 본 plan (agent-active) 결정적 대비 표

`gemento-verdict-record` 스킬 활용 — 영문 노트북 Closed-append-only 정책 자동 강제.

## 9. Stage 5 Exp14 완료 신호

5 subtask 완료 + 검증 (Exp12/13 task-05 패턴):

```bash
# 1) 도구 import
.venv/Scripts/python -c "
from experiments.tools import SEARCH_TOOL_SCHEMA, make_search_chunks_tool, bm25_retrieve
from experiments.exp14_search_tool.run import (
    run_baseline_abc_chunked, run_abc_search_tool, CONDITION_DISPATCH,
)
import inspect
import sys; sys.path.insert(0, 'experiments')
from orchestrator import run_abc_chain
for opt in ('search_tool', 'corpus'):
    assert opt in inspect.signature(run_abc_chain).parameters
print('ok: Exp14 도구')
"

# 2) trial 수 = 100 (50 baseline + 50 search)
# 3) 분석 보고서 + result.md 신규
# 4) 영문 노트북 표 / 기존 entry 무변경 (Closed-append-only)
```

## 10. 부수 사항

- 영문 노트북 Closed 추가만 — 기존 H1~H12 entry 변경 절대 금지
- README 갱신 = 사용자 결정
- `experiments/measure.py` / `system_prompt.py` 의 기존 prompt / `schema.py` / `run_helpers.py` 변경 금지
- `experiments/_external/gemini_client.py` 변경 금지 (Exp11 영역)
- Exp11 c_caller / Exp12 extractor_pre_stage / Exp13 reducer_post_stage — orchestrator 의 read-only 보존
- 기존 `bm25_tool.bm25_retrieve` 함수 본체 변경 금지 (tokenizer 만 stop-words 추가)
- `experiments/tools/math_tools.py` 변경 금지 (Exp08 영역)
- 본 plan = Exp13 마감 (H12 ⚠ 미결, 실효적 기각, 위치-효과 비대칭) 후 Architect 권장. Tool 축 신규 도입 (H7 +18.3pp / H8 +23.3pp 라인 연속)

## 11. 다음 단계 (Stage 5 Exp14 마감 후)

Exp14 마감 후 Architect 가:
1. H13 verdict + Exp09 RAG arm 비교 결과
2. Stage 5 다음 plan 결정 — Critic Tool 강화 (Exp15 후보) / Evidence Tool / SQLite ledger / Cross-model 재현
3. Stage 6 후보 — Qwen / Phi / Llama 재현 (4축 검증 마감 후)

준비되었으면 task-01 부터 시작. 보고는 한국어.
