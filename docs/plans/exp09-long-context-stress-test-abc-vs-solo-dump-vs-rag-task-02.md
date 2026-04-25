---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: exp09-long-context-stress-test-abc-vs-solo-dump-vs-rag
parallel_group: A
depends_on: []
---

# Task 02 — Chunker 모듈 (`tools/chunker.py`)

## Changed files

- `experiments/tools/chunker.py` — **신규 파일**. Document → Chunks 분할.
- `experiments/tools/test_chunker.py` — **신규 파일**. 단위 테스트 (unittest).
- `experiments/tools/__init__.py` — **수정**. `chunk_document` export 추가 (선택적).

## Change description

### Step 1 — `chunker.py` 구조

```python
"""Long-context 실험용 document chunker.

순수 Python, 외부 의존성 없음. tiktoken 사용하지 않고 words 기준.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict


@dataclass
class Chunk:
    chunk_id: int
    content: str
    word_count: int
    start_offset: int  # document 시작부터의 word 인덱스
    end_offset: int    # exclusive

    def to_dict(self) -> dict:
        return asdict(self)


def chunk_document(
    text: str,
    size: int = 500,
    overlap: int = 50,
) -> list[Chunk]:
    """Document를 고정 크기 chunk로 분할.

    Args:
        text: 원본 document 문자열.
        size: chunk 당 단어 수 (기본 500).
        overlap: 인접 chunk 간 겹치는 단어 수 (기본 50, stride = size - overlap).

    Returns:
        Chunk 리스트. 인접 chunk는 `overlap` words 공유.

    Raises:
        ValueError: size <= overlap일 때 (무한 루프 방지).
    """
    if size <= 0 or overlap < 0:
        raise ValueError(f"invalid size={size} or overlap={overlap}")
    if size <= overlap:
        raise ValueError(f"size ({size}) must be > overlap ({overlap}) to advance")

    words = text.split()
    if not words:
        return []

    chunks: list[Chunk] = []
    stride = size - overlap
    idx = 0
    chunk_id = 0

    while idx < len(words):
        end = min(idx + size, len(words))
        chunk_words = words[idx:end]
        chunks.append(Chunk(
            chunk_id=chunk_id,
            content=" ".join(chunk_words),
            word_count=len(chunk_words),
            start_offset=idx,
            end_offset=end,
        ))
        chunk_id += 1
        if end == len(words):
            break
        idx += stride

    return chunks
```

### Step 2 — Design 결정

- **단어 기준 분할**: tiktoken 의존성 추가 회피. 단어 수는 토큰 수와 선형 상관 (~1.3x)이므로 chunk 당 500 words ≈ 650 tokens ≈ 평균적으로 E4B sliding_window(512) 근방. 큰 편차가 필요하면 size 파라미터 조정.
- **Overlap 포함**: RAG·chunked QA에서 표준 관행. 경계에 걸린 증거가 한 chunk에만 등장하면 retrieval miss 증가.
- **Stride = size - overlap**: size=500, overlap=50 → stride=450. 500/450 ≈ 11% overlap.
- **순수 함수**: 상태 없음, 결정론적. 파일 I/O 없음 (호출자가 읽어서 넘김).

### Step 3 — 단위 테스트 (`test_chunker.py`)

```python
import unittest
from chunker import chunk_document, Chunk


class TestChunker(unittest.TestCase):
    def test_empty_text(self):
        self.assertEqual(chunk_document(""), [])

    def test_short_text_one_chunk(self):
        text = "hello world " * 100  # 200 words
        chunks = chunk_document(text, size=500, overlap=50)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].word_count, 200)

    def test_exact_size_boundary(self):
        text = " ".join(str(i) for i in range(500))
        chunks = chunk_document(text, size=500, overlap=50)
        self.assertEqual(len(chunks), 1)

    def test_size_plus_one(self):
        text = " ".join(str(i) for i in range(501))
        chunks = chunk_document(text, size=500, overlap=50)
        self.assertEqual(len(chunks), 2)
        # 두 번째 chunk는 450번째부터 시작(stride=450)
        self.assertEqual(chunks[1].start_offset, 450)

    def test_overlap_content(self):
        text = " ".join(str(i) for i in range(1000))
        chunks = chunk_document(text, size=500, overlap=50)
        # chunk 0: 0~499
        # chunk 1: 450~949 → 450~499가 overlap
        overlap_chunk0 = chunks[0].content.split()[-50:]
        overlap_chunk1 = chunks[1].content.split()[:50]
        self.assertEqual(overlap_chunk0, overlap_chunk1)

    def test_invalid_params(self):
        with self.assertRaises(ValueError):
            chunk_document("test", size=100, overlap=100)
        with self.assertRaises(ValueError):
            chunk_document("test", size=0, overlap=0)
        with self.assertRaises(ValueError):
            chunk_document("test", size=100, overlap=-1)

    def test_chunk_to_dict(self):
        text = "a b c d e"
        chunks = chunk_document(text, size=3, overlap=1)
        d = chunks[0].to_dict()
        self.assertEqual(set(d.keys()), {"chunk_id", "content", "word_count", "start_offset", "end_offset"})


if __name__ == "__main__":
    unittest.main()
```

### Step 4 — `__init__.py` 업데이트 (선택)

기존 `experiments/tools/__init__.py`는 `math_tools`만 export. `chunker`는 실험 내부에서만 사용되므로 export 필수는 아님. 단 명시성을 위해 추가:

```python
# experiments/tools/__init__.py
from .math_tools import TOOL_FUNCTIONS, TOOL_SCHEMAS, calculator, solve_linear_system, linprog
from .chunker import chunk_document, Chunk

__all__ = [
    "TOOL_FUNCTIONS", "TOOL_SCHEMAS",
    "calculator", "solve_linear_system", "linprog",
    "chunk_document", "Chunk",
]
```

## Dependencies

- 선행 Task 없음.
- 외부 패키지 추가 없음 (표준 라이브러리만).

## Verification

```bash
# 1. 파일 존재
test -f experiments/tools/chunker.py && echo "chunker.py: OK"
test -f experiments/tools/test_chunker.py && echo "test_chunker.py: OK"

# 2. 단위 테스트 전체 통과
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -m unittest tools.test_chunker -v
# 기대: "OK" 종료, 모든 테스트 pass (약 6~7개)

# 3. 기본 호출 sanity
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "
import sys; sys.path.insert(0, 'experiments')
from tools.chunker import chunk_document
text = 'word ' * 1200  # 1200 words
chunks = chunk_document(text, size=500, overlap=50)
assert len(chunks) == 3, f'expected 3 chunks, got {len(chunks)}'
assert all(c.word_count <= 500 for c in chunks)
# Stride 450: chunk0=0-499, chunk1=450-949, chunk2=900-1199
assert chunks[0].start_offset == 0
assert chunks[1].start_offset == 450
assert chunks[2].start_offset == 900
print(f'OK: {len(chunks)} chunks, sizes={[c.word_count for c in chunks]}')
"

# 4. 기존 math_tools 회귀 없음
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -m unittest tools.test_math_tools -v 2>&1 | tail -3
# 기대: "OK", 기존 9개 테스트 pass
```

## Risks

- **Word 기준의 한계**: 영어 기준 words 수와 llama.cpp tokenizer tokens 수는 선형이지만 비율이 언어·텍스트에 따라 변동. Exp09 영어 문서에 한해 안전하나 한국어·중국어 확장 시 재검토 필요.
- **Overlap 경계 버그**: stride 계산 오류 시 무한 루프 또는 중복 chunk 생성 가능. Verification의 overlap_content 테스트가 이를 차단.
- **메모리**: `chunks.append`로 모든 chunk를 메모리에 유지. 20K words 문서는 문제 없으나 수백 K words+는 generator 패턴 고려 필요 (범위 외).
- **__init__.py 수정**: 기존 import 경로에 영향 없어야 함. Verification 4번으로 검증.

## Scope boundary

**Task 02에서 절대 수정 금지**:
- `experiments/tools/math_tools.py` — 기존 도구 (수정 금지)
- `experiments/tools/test_math_tools.py` — 기존 테스트 (수정 금지)
- `experiments/tools/smoke_test.py` — 기존 smoke (수정 금지)
- `experiments/schema.py` (Task 04 영역)
- `experiments/orchestrator.py`, `run_experiment.py`, `measure.py`
- `experiments/tasks/` (Task 01 영역)

**허용 범위**:
- 신규: `experiments/tools/chunker.py`, `experiments/tools/test_chunker.py`
- 수정: `experiments/tools/__init__.py` (import 1줄 + `__all__` 확장)
