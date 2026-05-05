---
type: plan
status: done
updated_at: 2026-05-05
slug: exp14-search-tool
version: 1
author: Architect (Windows)
audience: Developer (Sonnet) + 사용자 검토 (위임 시 Architect default) + 사용자 직접 실행 (Task 04)
parent_strategy: handoff-to-windows-2026-04-30-followup-strategy.md (Stage 5)
---

# Stage 5 — Exp14: Search Tool (Tool 축 신규, agent-active retrieval)

## Description

Stage 5 Role 축 3 회 검증 (Exp11/12/13) 마감 후 Architect 권장 — Tool 축 신규 검증. 직전 두 음수 (Exp11 Mixed −0.08, Exp13 Reducer −0.05) 모두 *비결정성* 외부 (LLM-judge / LLM-reducer). 본 plan = **결정성 외부 도구 (Search Tool)** 도입으로 H7 +18.3pp / H8 +23.3pp 라인 연속 검증.

**가설 H13 후보**: ABC 에이전트가 cycle 중 *능동적으로* `search_chunks(query, top_k)` 도구를 호출하여 long-context document 의 관련 chunk 를 retrieve 하면, Exp09 의 ABC chunked (sequential 수동 처리) 대비 정확도 + cycle 효율성 향상.

**조건**:
- baseline_abc_chunked: ABC + chunked Tattoo (Exp09 의 `abc_chunked` arm 재사용 — sequential chunk → A 의 Tattoo 누적)
- abc_search_tool: ABC + **agent-active Search Tool** (A/B/C 가 cycle 중 BM25 retrieve 호출 가능)

**Stage 5 종합 + 본 plan 동기**:
- ✅ Exp11 H10 ⚠ 미결 (실효적 기각) — Role 강화 = 비결정성 외부 = 위험
- ✅ Exp12 H11 ⚠ 조건부 채택 — Role 분리/추가 pre-stage = 양수 (+0.05)
- ✅ Exp13 H12 ⚠ 미결 (실효적 기각) — Role 분리/추가 post-stage = 음수 (−0.05). **위치-효과 비대칭 확정**
- 🎯 **본 plan H13** — 결정성 Tool 축 (Exp08 H7/H8 +18~23pp 라인 연속). 비결정성 함정 회피 + Stage 2C/Exp11/12/13 의 검정력 한계 영역 (longctx) 신규 측정

**Exp09 (RAG baseline) vs Exp14 (Search Tool) 의 차이**:

| 측면 | Exp09 RAG arm | Exp14 Search Tool |
|------|---------------|-------------------|
| 호출 시점 | 1 회 (시작 전, top-k retrieve → solo) | **N 회** (cycle 별 agent 가 능동 호출) |
| 호출 주체 | 외부 인프라 | **A/B/C 에이전트 자신** |
| query 형성 | 원본 task question | **에이전트의 cycle 별 query 형성** (반복 정밀화) |
| Tattoo 와 결합 | 분리 (RAG 결과 → Tattoo 외부) | **통합** (retrieved chunks → Tattoo assertion 으로 흡수 가능) |
| 효과 가설 | retrieve 자체 | **iterative active retrieval + reasoning 결합** |

→ 본 plan = "retrieve 가 도움" 이 아니라 **"능동적 query 형성 + 반복 retrieval + reasoning 결합"** 가설 검증.

## Expected Outcome

1. `experiments/tools/bm25_tool.py` — 수정. `search_chunks(query, top_k)` TOOL_SCHEMA 등록 + tool_function (closure 로 corpus 주입). stop-word filtering 추가
2. `experiments/tools/__init__.py` — `TOOL_SCHEMAS_SEARCH` / `TOOL_FUNCTIONS_SEARCH` export
3. `experiments/orchestrator.py` — `run_abc_chain` 에 `search_tool: bool = False` + corpus 주입 인자 추가 (1-3 라인 + tool_functions 결합 로직)
4. `experiments/exp14_search_tool/run.py` (신규) — 2 condition (abc_baseline_chunked + abc_search_tool) + cycle-by-cycle tattoo_history 보존 (Stage 2C 결함 fix). `longctx_taskset.json` 로드
5. `experiments/exp14_search_tool/results/exp14_baseline_abc.json` + `exp14_search_tool_abc.json`
6. 분석 보고서 `docs/reference/exp14-search-tool-analysis-<TS>.md`
7. H13 verdict + 문서 갱신 (researchNotebook 한·영 + 신규 result.md `exp-14-search-tool.md` + README 조건부)

## Subtask Index

1. [task-01](./exp14-search-tool-task-01.md) — `search_chunks` TOOL_SCHEMA 등록 + stop-words (S, parallel_group A, depends_on: [])
2. [task-02](./exp14-search-tool-task-02.md) — `run_abc_chain` 의 search_tool hook + corpus 주입 (S, parallel_group B, depends_on: [01])
3. [task-03](./exp14-search-tool-task-03.md) — `experiments/exp14_search_tool/run.py` (M, parallel_group C, depends_on: [01, 02])
4. [task-04](./exp14-search-tool-task-04.md) — 실험 실행 (사용자 직접) — 10 task × 2 condition × 5 trial = 100 trial (L, parallel_group D, depends_on: [03])
5. [task-05](./exp14-search-tool-task-05.md) — 분석 + H13 verdict + 문서 갱신 (M, parallel_group E, depends_on: [04])

### 의존성

```
Stage 1 (plan-side):
  Group A: task-01 (search_chunks TOOL_SCHEMA + stop-words)
       ↓
  Group B: task-02 (orchestrator search_tool hook)
       ↓        ↓
  Group C: task-03 (run.py — 01/02 의존)
       ↓
Stage 2 (사용자 직접):
  Group D: task-04 (100 trial 실험, ~15-20h 추정)
       ↓
Stage 3 (분석):
  Group E: task-05 (분석 + H13 + 문서)
```

## Constraints

- 메인 단일 흐름 (브랜치 분기 금지)
- Architect/Developer/Reviewer/사용자 분리 — Task 04 = 사용자 직접 실행
- `experiments/measure.py` / `score_answer_v0/v2/v3` 변경 0
- `experiments/orchestrator.py` 변경 = `run_abc_chain` 의 `search_tool` 옵션 추가 + 기존 tool_function 결합 로직 (5-15 라인). Exp11 c_caller / Exp12 extractor_pre_stage / Exp13 reducer_post_stage 보존
- `experiments/schema.py` 변경 0
- `experiments/run_helpers.py` (Stage 2A) 변경 0
- `experiments/tasks/longctx_taskset.json` 변경 0 (기존 10 task 그대로)
- `experiments/tasks/taskset.json` 변경 0 (main 15 task 비참여)
- `experiments/tools/chunker.py` 변경 0 (read-only 재사용)
- `experiments/tools/bm25_tool.py` = TOOL_SCHEMA 등록 + stop-words 추가만 (기존 `bm25_retrieve` 본체 무변경)
- `experiments/tools/math_tools.py` 변경 0 (Exp08 영역 보존)
- 영문 노트북 Closed 추가만
- README 갱신은 사용자 결정
- SQLite FTS5 / ledger 도입 금지 (별도 Stage 5 plan 영역, Mac §2)
- 벡터 / embedding 도입 금지 (Exp15+ 후보)
- 본 plan = **외부 API 0** (local Gemma + 결정적 BM25)

## 결정 (Architect 직접 결정, 2026-05-05)

사용자 위임 ("권장으로 가자" — 옵션 ii-A 확정).

### 결정 1 — BM25 backend — **기존 `bm25s` 재사용** 확정

기존 `experiments/tools/bm25_tool.py` (`bm25s` 패키지) 가 Exp09 RAG arm 에서 검증됨. SQLite FTS5 마이그레이션 = 별도 Stage 5 plan 영역. 본 plan 의 가설 (agent-active retrieval) 과 backend 선택은 독립.

### 결정 2 — Tool schema — **`search_chunks(query, top_k=5)`** 확정

```python
{
  "type": "function",
  "function": {
    "name": "search_chunks",
    "description": "Retrieve top-k most relevant document chunks via BM25 lexical search. Use when you need to find specific information in the document.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {"type": "string", "description": "Natural-language query"},
        "top_k": {"type": "integer", "description": "Number of chunks to return (default 5, max 10)", "default": 5}
      },
      "required": ["query"]
    }
  }
}
```

return: `[{chunk_id, content, bm25_score}, ...]` plain list. agent 가 결과를 reasoning 에 통합.

### 결정 3 — Document corpus 주입 — **orchestrator 에서 closure 로 주입** 확정

`run_abc_chain` 에 `corpus: list[dict] | None = None` 인자 추가. tool_function 등록 시 closure:

```python
def _search_chunks(query: str, top_k: int = 5):
    return bm25_retrieve(query, corpus, top_k=min(top_k, 10))
```

agent 는 corpus 의 존재 자체 모름. tool 만 노출.

### 결정 4 — Stop-words — **English 표준 stop-words 추가** 확정

기존 `_tokenize` 에 stop-word filter 추가. 후보 list:
```python
_STOP_WORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "should", "could", "may", "might", "can", "this", "that",
    "these", "those", "i", "you", "he", "she", "it", "we", "they", "what",
    "which", "who", "whom", "whose", "when", "where", "why", "how",
})
```

`_tokenize` 후 `[t for t in tokens if t not in _STOP_WORDS]` 적용. 기존 `bm25_retrieve` 본체 변경 0 (tokenizer 만 영향).

### 결정 5 — taskset — **`longctx_taskset.json` 그대로 (10 task)** 확정

10 task = small (3K) / medium (10K) / large (20K) × needle / 2hop / 3hop. Search Tool 의 변별력 검증 영역 (특히 hop 류). 신규 task 추가 금지 — Exp09 결과와 직접 비교 가능 + scope 폭증 차단.

### 결정 6 — condition 구성 — **2 condition** (baseline_abc_chunked + abc_search_tool) 확정

- baseline_abc_chunked: Exp09 의 `abc_chunked` arm 패턴 재사용 (sequential chunk → A 의 Tattoo 누적). 단 본 plan 에서는 Exp09 코드 의존성 minimum — 가능하면 별도 함수 작성, Exp09 와 분리
- abc_search_tool: ABC + search_chunks tool callable. corpus 는 chunked document 전체 (chunker.chunk_document 결과)

### 결정 7 — trial / cycles — **5 trial × 8 max_cycles** (Stage 2C/Exp11/12/13 정합) 확정

10 task × 2 condition × 5 trial = 100 trial. 시간 추정: ~10-15min/trial × 100 = ~17-25h (Exp09 longctx 평균보다 길 수 있음 — Search Tool 호출이 cycle 시간 ↑).

### 결정 8 — 메커니즘 측정 — **accuracy + tool call count + evidence hit rate** 확정

본 plan 의 핵심 메커니즘 = agent 의 능동 retrieval. 측정:
- accuracy (v3 채점) — primary
- tool call count per trial (search_tool 사용 빈도)
- query diversity (cycle 별 query 의 lexical overlap)
- hit rate vs `gold_evidence_chunks` (Exp09 와 직접 비교 가능)
- cycle 단축 (search 가 수동 chunk 처리보다 빠른지)

## Non-goals

- SQLite FTS5 / ledger 인프라 (별도 Stage 5 plan)
- 벡터 / embedding (Exp15+ 후보)
- multi-collection / 카테고리별 routing
- 커스텀 tokenizer / stemmer (기본 + stop-words 만)
- main `taskset.json` 의 15 task 참여 (Search Tool 변별력 0 영역)
- Exp09 baseline 재실행 (read-only 비교만)
- Mixed Intelligence 재시도 (Exp11 비추천)
- Reducer prompt 강화 / Reducer + Search 조합 (Exp13 위치 효과 한계)
- score_answer_v4 도입

## Risks

- **Risk 1 — Gemma 의 tool 호출 신뢰성**: Exp08 의 `tool_neglect` 문제. dry-run 시 (사용자 직접) 1 task × 1 trial 에서 search_chunks 호출 발생 확인. neglect 시 prompt 강화 검토 (별도 plan)
- **Risk 2 — search_chunks 의 query 형성 품질**: Gemma 가 "the document about X" 같은 nonsense query 형성 시 BM25 무효. dry-run 첫 trial 의 tool_call_log 정찰 후 prompt 보강 후보
- **Risk 3 — Exp09 RAG arm 과의 차별성 부족**: 본 plan 효과가 RAG arm 과 같은 크기면 "agent-active" 가설 기각, 단순 retrieve 효과로 환원
- **Risk 4 — corpus 주입의 메모리 증가**: longctx-large (20K word) 의 chunked corpus = ~200KB 메모리. closure 보유 OK, 단 LM Studio 컨텍스트 윈도우와는 무관
- **Risk 5 — Stage 2A/2B/2C 인프라 보존 실패**: Sonnet 이 run.py 작성 시 Exp12/13 패턴 정확 복사 의무 (`gemento-experiment-scaffold` 스킬 활용 권장)
- **Risk 6 — orchestrator 의 search_tool / extractor_pre_stage / reducer_post_stage / c_caller 4 hook 공존**: 인자 4 개 동시 활성화 시 우선순위 정의 필요. 본 plan = `search_tool=True, extractor_pre_stage=False, reducer_post_stage=False, c_caller=None` 만 사용 — 다른 조합 비활성화 명시
- **Risk 7 — 시간 비용**: 100 trial × ~10-15min = ~17-25h. baseline 12h + search 5-13h. 사용자 직접 실행 부담

## Sonnet (Developer) 진행 가이드

본 plan 도 Architect 작성 + Developer 그대로 진행:

1. 각 subtask 의 Step 순서대로
2. 각 subtask 의 "Changed files" 만 수정
3. 결정 1-8 default 사용 (사용자 위임)
4. Verification 명령 + 결과 보고
5. Risk 발견 시 즉시 보고
6. Scope boundary 위반 직전이면 멈추고 보고
7. Task 04 = 사용자 직접 실행 — Sonnet 모델 호출 금지
8. **신규**: `gemento-experiment-scaffold` 스킬 task-03 작성 시 활용 — 기존 Exp12/13 패턴 정확 복제

## 변경 이력

- 2026-05-05 v1: 초안. Stage 5 Exp13 마감 (`3c5d9f4`) + 사용자 위임 ("권장으로 가자, ii-A") 직후 Architect 작성. Stage 5 Role 축 3 회 검증 마감 후 Tool 축 신규 도입. 직전 두 음수 (Exp11/13) 의 비결정성 함정 회피 + H7/H8 결정성 라인 연속.
