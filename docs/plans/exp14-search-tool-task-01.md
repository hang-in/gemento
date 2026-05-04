---
type: plan-task
status: pending
updated_at: 2026-05-05
parent_plan: exp14-search-tool
parallel_group: A
depends_on: []
---

# Task 01 — `search_chunks` TOOL_SCHEMA 등록 + stop-words

## Changed files

- `experiments/tools/bm25_tool.py` — **수정 (추가만)**. stop-words filter + `SEARCH_TOOL_SCHEMA` 정의 + `make_search_chunks_tool(corpus)` factory
- `experiments/tools/__init__.py` — **수정 (추가만)**. `SEARCH_TOOL_SCHEMA`, `make_search_chunks_tool` export

수정 2 (추가만), 신규 0.

## Change description

### 배경

기존 `bm25_retrieve(query, chunks, top_k)` 가 작동 — Exp09 RAG arm 검증. 본 task = (i) tokenizer 에 stop-words 추가 + (ii) tool-calling 프로토콜에 등록할 schema 정의 + (iii) corpus 를 closure 로 묶는 factory 함수 추가.

### Step 1 — stop-words 추가

`bm25_tool.py` 의 `_tokenize` 함수 보강:

```python
_STOP_WORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "should", "could", "may", "might", "can", "this", "that",
    "these", "those", "i", "you", "he", "she", "it", "we", "they", "what",
    "which", "who", "whom", "whose", "when", "where", "why", "how",
})


def _tokenize(text: str) -> list[str]:
    """단순 tokenizer — 영숫자만 추출, 소문자화, stop-words 제거."""
    tokens = [m.group(0).lower() for m in _TOKEN_RE.finditer(text)]
    return [t for t in tokens if t not in _STOP_WORDS]
```

기존 `bm25_retrieve` 본체 무변경 (tokenizer 함수 한 곳 수정으로 자동 반영).

### Step 2 — `SEARCH_TOOL_SCHEMA` 정의

`bm25_tool.py` 끝에 추가:

```python
SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_chunks",
        "description": (
            "Retrieve top-k most relevant document chunks via BM25 lexical search. "
            "Use when you need to find specific information in the document. "
            "Returns chunks with their content and BM25 relevance score."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language query. Use specific keywords for best results.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of chunks to return (default 5, max 10).",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
}
```

### Step 3 — `make_search_chunks_tool` factory

corpus 를 closure 로 묶는 factory:

```python
def make_search_chunks_tool(corpus: list[dict]):
    """corpus 가 주입된 search_chunks tool 함수 반환.

    orchestrator 가 task 의 chunked document 를 corpus 로 전달하여
    agent 가 tool 호출 시 본 corpus 에서만 retrieve.

    Args:
        corpus: chunker.chunk_document(doc).to_dict() 리스트.

    Returns:
        callable(query: str, top_k: int = 5) -> list[dict]
    """
    def search_chunks(query: str, top_k: int = 5) -> list[dict]:
        capped_top_k = min(max(1, int(top_k)), 10)
        return bm25_retrieve(query, corpus, top_k=capped_top_k)
    return search_chunks
```

### Step 4 — `__init__.py` export

```python
from .bm25_tool import bm25_retrieve, SEARCH_TOOL_SCHEMA, make_search_chunks_tool

__all__ = [
    ...,
    "bm25_retrieve", "SEARCH_TOOL_SCHEMA", "make_search_chunks_tool",
]
```

## Dependencies

- 패키지: 없음 (`bm25s` 이미 설치됨)
- 기존 파일: `experiments/tools/bm25_tool.py` (수정), `experiments/tools/chunker.py` (read-only)
- 다른 subtask: 없음 (parallel_group A)

## Verification

```bash
# 1) syntax + import
.venv/Scripts/python -m py_compile experiments/tools/bm25_tool.py
.venv/Scripts/python -c "
from experiments.tools import (
    bm25_retrieve, SEARCH_TOOL_SCHEMA, make_search_chunks_tool,
    chunk_document,
)
print('verification 1 ok: imports')
"

# 2) stop-words 적용 확인
.venv/Scripts/python -c "
from experiments.tools.bm25_tool import _tokenize
tokens = _tokenize('The quick brown fox jumps over the lazy dog')
# 'the', 'over' 제거 후 ['quick', 'brown', 'fox', 'jumps', 'lazy', 'dog'] 기대
assert 'the' not in tokens, f'stop-word the not removed: {tokens}'
assert 'quick' in tokens
assert 'fox' in tokens
print(f'verification 2 ok: stop-words tokens={tokens}')
"

# 3) SEARCH_TOOL_SCHEMA 형식 검증
.venv/Scripts/python -c "
from experiments.tools import SEARCH_TOOL_SCHEMA
assert SEARCH_TOOL_SCHEMA['type'] == 'function'
assert SEARCH_TOOL_SCHEMA['function']['name'] == 'search_chunks'
assert 'query' in SEARCH_TOOL_SCHEMA['function']['parameters']['required']
print('verification 3 ok: SEARCH_TOOL_SCHEMA')
"

# 4) make_search_chunks_tool 동작
.venv/Scripts/python -c "
from experiments.tools import make_search_chunks_tool, chunk_document
doc = 'The first chunk talks about apples. ' * 100
chunks = [c.to_dict() for c in chunk_document(doc, size=50, overlap=5)]
tool_fn = make_search_chunks_tool(chunks)
results = tool_fn('apples', top_k=3)
assert len(results) <= 3
assert all('content' in r and 'bm25_score' in r for r in results)
print(f'verification 4 ok: factory returned {len(results)} chunks')
"

# 5) top_k clamp 검증
.venv/Scripts/python -c "
from experiments.tools import make_search_chunks_tool, chunk_document
doc = 'word ' * 5000
chunks = [c.to_dict() for c in chunk_document(doc, size=100, overlap=10)]
tool_fn = make_search_chunks_tool(chunks)
results = tool_fn('word', top_k=999)
assert len(results) <= 10, f'top_k not clamped: {len(results)}'
print(f'verification 5 ok: top_k clamped to {len(results)}')
"
```

5 명령 모두 정상.

## Risks

- **Risk 1 — stop-words 가 짧은 query 에서 모든 token 제거**: 예 query="when was it" → 모든 stop-word → 빈 list → `bm25_retrieve` 의 `ValueError("query has no retrievable tokens")`. 본 task 영역 외 (model 의 query 형성 능력에 의존, prompt 가이드로 차단)
- **Risk 2 — Exp09 RAG arm 의 tokenizer 변경**: Exp09 RAG 결과 재현 시 stop-words 미적용 버전과 차이 가능. 단 Exp09 결과 JSON 은 read-only 보존 (재실행 안 함). Architect 의 후속 cross-Exp 비교 시 본 변경 명시
- **Risk 3 — Sonnet 이 `bm25_retrieve` 본체 변경**: 본 task = stop-words tokenizer + 신규 SEARCH_TOOL_SCHEMA + factory 만. `bm25_retrieve` 함수 본체 절대 변경 금지

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/orchestrator.py` (task-02 영역)
- `experiments/exp14_search_tool/run.py` (task-03 영역, 미존재)
- `experiments/measure.py` / `score_answer_v*`
- `experiments/run_helpers.py` (Stage 2A)
- `experiments/schema.py`
- `experiments/system_prompt.py` (Reducer/Extractor 영역)
- `experiments/tools/math_tools.py` (Exp08 영역)
- `experiments/tools/chunker.py` (read-only)
- 모든 기존 `experiments/exp**/run.py`
- `experiments/tasks/longctx_taskset.json`
- 결과 JSON

`bm25_tool.py` 에서 변경 금지 영역:
- 기존 `bm25_retrieve` 함수 본체 (signature + 핵심 로직). tokenizer 함수만 stop-words filter 추가
