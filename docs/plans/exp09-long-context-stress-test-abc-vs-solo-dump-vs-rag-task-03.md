---
type: plan-task
status: todo
updated_at: 2026-04-25
parent_plan: exp09-long-context-stress-test-abc-vs-solo-dump-vs-rag
parallel_group: A
depends_on: []
---

# Task 03 — BM25 tool 통합 (`tools/bm25_tool.py` + bm25s 의존성)

## Changed files

- `experiments/tools/bm25_tool.py` — **신규 파일**. BM25 기반 chunk retrieval.
- `experiments/tools/test_bm25_tool.py` — **신규 파일**. 단위 테스트.
- `experiments/tools/__init__.py` — **수정**. `bm25_retrieve` export (선택적).

## Change description

### Step 1 — 패키지 선정: `bm25s`

**권장**: [`bm25s`](https://pypi.org/project/bm25s/)
- 순수 Python + numpy. 의존성 가벼움.
- Active maintenance (2024~).
- 다중 BM25 변형 지원 (Okapi, BM25L, BM25+).

**대안**: `rank_bm25` — 더 오래된 패키지, API 단순하지만 성능 열세.

**결정**: `bm25s`. 단 범위 제한 — tokenization은 **단순 whitespace split + lowercase**로 통일 (언어 중립).

### Step 2 — `bm25_tool.py` 구조

```python
"""BM25 기반 chunk retrieval. Exp09 RAG baseline용."""
from __future__ import annotations
import re

import bm25s  # type: ignore[import-untyped]


_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    """단순 tokenizer — 영숫자만 추출, 소문자화.

    언어 중립 · 재현성 우선. 영어 외 언어에서는 형태소 분석기가 더 낫지만
    Exp09는 영어 기준이므로 이걸로 충분.
    """
    return [m.group(0).lower() for m in _TOKEN_RE.finditer(text)]


def bm25_retrieve(
    query: str,
    chunks: list[dict],  # from chunker.Chunk.to_dict()
    top_k: int = 5,
) -> list[dict]:
    """BM25 점수로 query와 가장 관련 높은 top_k chunks 반환.

    Args:
        query: 검색 쿼리 (자연어 질문).
        chunks: Chunk.to_dict() 리스트 (chunker 모듈 출력).
        top_k: 상위 몇 개 chunk를 반환할지.

    Returns:
        입력 chunk 딕셔너리 리스트 중 상위 top_k. 각 chunk에 `bm25_score`
        필드가 추가됨. 점수 내림차순.

    Raises:
        ValueError: chunks가 비어있거나 query가 비어있을 때.
    """
    if not chunks:
        raise ValueError("no chunks to retrieve from")
    if not query.strip():
        raise ValueError("empty query")

    corpus_tokens = [_tokenize(c["content"]) for c in chunks]
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)

    query_tokens = _tokenize(query)
    if not query_tokens:
        raise ValueError("query has no retrievable tokens after tokenization")

    k = min(top_k, len(chunks))
    results, scores = retriever.retrieve([query_tokens], k=k)

    out: list[dict] = []
    for idx, score in zip(results[0], scores[0]):
        # results[0]는 chunk 인덱스 (0-based)
        c = dict(chunks[int(idx)])
        c["bm25_score"] = float(score)
        out.append(c)
    return out
```

### Step 3 — `test_bm25_tool.py`

```python
import unittest
from chunker import chunk_document
from bm25_tool import bm25_retrieve


class TestBM25Tool(unittest.TestCase):
    def setUp(self):
        self.chunks = [
            {"chunk_id": 0, "content": "apple orange banana fruit basket", "word_count": 5, "start_offset": 0, "end_offset": 5},
            {"chunk_id": 1, "content": "car vehicle transportation highway", "word_count": 4, "start_offset": 5, "end_offset": 9},
            {"chunk_id": 2, "content": "apple pie recipe baking kitchen", "word_count": 5, "start_offset": 9, "end_offset": 14},
        ]

    def test_top_k_returns_relevant(self):
        results = bm25_retrieve("apple recipe", self.chunks, top_k=2)
        self.assertEqual(len(results), 2)
        # chunk_2 (apple pie recipe)가 가장 높은 점수여야 함
        self.assertEqual(results[0]["chunk_id"], 2)

    def test_empty_chunks_raises(self):
        with self.assertRaises(ValueError):
            bm25_retrieve("test", [], top_k=3)

    def test_empty_query_raises(self):
        with self.assertRaises(ValueError):
            bm25_retrieve("", self.chunks, top_k=3)

    def test_top_k_exceeds_chunks(self):
        results = bm25_retrieve("apple", self.chunks, top_k=10)
        self.assertLessEqual(len(results), 3)

    def test_score_descending(self):
        results = bm25_retrieve("apple fruit", self.chunks, top_k=3)
        scores = [r["bm25_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_end_to_end_with_chunker(self):
        long_text = "This is a document about planets. Jupiter is the largest. " * 50
        long_text += "The smallest dwarf planet is Ceres. " * 30
        long_text += "Mars has two moons. " * 40
        chunks = chunk_document(long_text, size=30, overlap=5)
        dicts = [c.to_dict() for c in chunks]
        results = bm25_retrieve("smallest planet", dicts, top_k=3)
        # Ceres가 언급된 chunk가 top에 등장해야 함
        self.assertTrue(any("ceres" in r["content"].lower() for r in results[:2]))


if __name__ == "__main__":
    unittest.main()
```

### Step 4 — 의존성 기록

프로젝트에 `requirements.txt`가 없으므로 **설치 명령만 문서화**:

```bash
pip install bm25s
```

README / conceptFramework에 명시적 기록은 안 하되, Gemini 핸드오프(Task 07)에서 Windows 설치 지시에 포함.

### Step 5 — `__init__.py` 업데이트

```python
# experiments/tools/__init__.py
from .math_tools import TOOL_FUNCTIONS, TOOL_SCHEMAS, calculator, solve_linear_system, linprog
from .chunker import chunk_document, Chunk
from .bm25_tool import bm25_retrieve

__all__ = [
    "TOOL_FUNCTIONS", "TOOL_SCHEMAS",
    "calculator", "solve_linear_system", "linprog",
    "chunk_document", "Chunk",
    "bm25_retrieve",
]
```

**주의**: `bm25_retrieve`는 **OpenAI `TOOL_SCHEMAS`에 등록하지 않음** — RAG arm 내부에서만 직접 호출. LLM이 호출 주체가 아님.

## Dependencies

- 선행 Task 없음 (Task 02 chunker와 병렬 개발 가능).
- 단위 테스트 중 `test_end_to_end_with_chunker`는 Task 02 완료 시점에만 유효 — 없으면 해당 테스트만 skip.
- **외부 패키지**: `bm25s` (`pip install bm25s`). numpy는 Exp08에서 이미 설치됨.

## Verification

```bash
# 0. 의존성 설치 확인
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "import bm25s; print('bm25s', bm25s.__version__)"
# 기대: 버전 문자열 출력. 없으면 'pip install bm25s' 선행.

# 1. 파일 존재
test -f experiments/tools/bm25_tool.py && echo "bm25_tool.py: OK"
test -f experiments/tools/test_bm25_tool.py && echo "test_bm25_tool.py: OK"

# 2. 단위 테스트 전체 통과
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -m unittest tools.test_bm25_tool -v
# 기대: "OK", 6개 테스트 전부 pass

# 3. 기본 호출 sanity
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "
import sys; sys.path.insert(0, 'experiments')
from tools.bm25_tool import bm25_retrieve
chunks = [
    {'chunk_id':0,'content':'apple banana','word_count':2,'start_offset':0,'end_offset':2},
    {'chunk_id':1,'content':'car vehicle','word_count':2,'start_offset':2,'end_offset':4},
]
r = bm25_retrieve('apple', chunks, top_k=1)
assert len(r) == 1 and r[0]['chunk_id'] == 0
assert 'bm25_score' in r[0]
print('OK:', r[0]['bm25_score'])
"

# 4. math_tools 회귀 없음
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -m unittest tools.test_math_tools tools.test_chunker 2>&1 | tail -3
# 기대: "OK"
```

## Risks

- **bm25s 버전 호환성**: API 변화 가능성. 초기 구현은 최소 메소드(`index`, `retrieve`)만 사용 — 버전 의존성 낮춤. Verification 0번에서 버전 확인.
- **Tokenization 단순화**: 영숫자만 추출·소문자화. 한국어·일본어 문서에서는 형태소 분석 없이 매우 낮은 점수. Exp09 영어 한정이므로 수용.
- **Numerical stability**: bm25s는 numpy 의존. 빈 corpus나 모든 document가 동일 token인 edge case에서 score NaN 가능성. 단위 테스트에 대비 케이스 추가 완료.
- **`TOOL_SCHEMAS` 미등록 의도적**: bm25_retrieve는 LLM의 tool_call 대상이 아니라 orchestrator 내부 유틸. RAG arm의 단일 retrieval 호출로만 사용.
- **성능**: 20K words 문서를 500 words chunk로 나누면 40 chunks. BM25 인덱싱은 즉시. 성능 이슈 없음.

## Scope boundary

**Task 03에서 절대 수정 금지**:
- `experiments/tools/math_tools.py`, `test_math_tools.py` (기존 Tool 영역)
- `experiments/tools/chunker.py` (Task 02 영역) — import만 허용
- `experiments/schema.py` (Task 04 영역)
- `experiments/orchestrator.py`, `run_experiment.py`, `measure.py`, `system_prompt.py`
- `experiments/tasks/` (Task 01 영역)

**허용 범위**:
- 신규: `experiments/tools/bm25_tool.py`, `experiments/tools/test_bm25_tool.py`
- 수정: `experiments/tools/__init__.py` (import 1줄 + `__all__` 확장)
