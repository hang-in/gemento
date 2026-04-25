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
