"""BM25 기반 chunk retrieval. Exp09 RAG baseline용."""
from __future__ import annotations
import re

import bm25s  # type: ignore[import-untyped]


_TOKEN_RE = re.compile(r"\w+", re.UNICODE)

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


def make_search_chunks_tool(corpus: list[dict]):
    """corpus가 주입된 search_chunks tool 함수 반환.

    orchestrator가 task의 chunked document를 corpus로 전달하여
    agent가 tool 호출 시 본 corpus에서만 retrieve.
    """
    def search_chunks(query: str, top_k: int = 5) -> list[dict]:
        capped_top_k = min(max(1, int(top_k)), 10)
        return bm25_retrieve(query, corpus, top_k=capped_top_k)
    return search_chunks
