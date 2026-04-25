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
        c = dict(chunks[int(idx)])
        c["bm25_score"] = float(score)
        out.append(c)
    return out
