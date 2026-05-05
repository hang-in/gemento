"""LLM-as-judge auxiliary evaluation for H12 (Reducer) and H13 (Search Tool).

P1-3 in docs/reference/paper-review-action-items-2026-05-05.md.

Uses Groq GPT-OSS 120B (reasoning model) as cross-evaluator.
"""
from __future__ import annotations

import json

from .groq_client import call_with_meter_retry, GPT_OSS_120B


JUDGE_SYSTEM_PROMPT = """You are an expert evaluator of question answering. \
Given a question, an expected answer, and a candidate answer, you assess whether \
the candidate answer is semantically correct.

Output a single JSON object: {"correct": true|false, "score": 0-5, "reason": "<one sentence>"}

Scoring rubric:
- 5: candidate fully captures the expected answer with correct facts
- 4: candidate captures the core fact but with minor omissions or imprecise phrasing
- 3: candidate is partially correct (some facts right, some wrong/missing)
- 2: candidate is mostly wrong but has some related correct content
- 1: candidate is clearly wrong or contradicts the expected answer
- 0: candidate is empty, irrelevant, or refuses to answer

"correct" is true iff score >= 4."""


def judge_answer(
    question: str,
    expected_answer: str,
    candidate_answer: str,
    model: str = GPT_OSS_120B,
) -> dict:
    """단일 답변의 의미적 채점.

    Returns:
        {"correct": bool, "score": int 0-5, "reason": str, "raw_response": str, "error": str|None}
    """
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"## Question\n{question}\n\n"
            f"## Expected answer\n{expected_answer}\n\n"
            f"## Candidate answer\n{candidate_answer or '(empty)'}\n\n"
            f"Output the JSON verdict only."
        )},
    ]
    result = call_with_meter_retry(
        messages, model=model,
        response_format={"type": "json_object"},
        max_tokens=2048,
    )
    if result.error:
        return {"correct": None, "score": None, "reason": None,
                "raw_response": "", "error": result.error}
    try:
        parsed = json.loads(result.raw_response)
        return {
            "correct": bool(parsed.get("correct")),
            "score": int(parsed.get("score", 0)),
            "reason": parsed.get("reason", ""),
            "raw_response": result.raw_response,
            "error": None,
        }
    except Exception as e:
        return {"correct": None, "score": None, "reason": None,
                "raw_response": result.raw_response, "error": f"parse failed: {e}"}


PAIR_COMPARE_SYSTEM = """You compare two candidate answers (A and B) to the same question. \
Decide which is semantically more correct given the expected answer. Order is randomized — \
do not assume A is always the baseline.

Output a single JSON object: {"winner": "A"|"B"|"tie", "score_A": 0-5, "score_B": 0-5, "reason": "<one sentence>"}"""


def compare_answers(
    question: str,
    expected_answer: str,
    answer_A: str,
    answer_B: str,
    model: str = GPT_OSS_120B,
) -> dict:
    """두 답변의 직접 비교 — paired evaluation. order randomized 권장 (caller 책임)."""
    messages = [
        {"role": "system", "content": PAIR_COMPARE_SYSTEM},
        {"role": "user", "content": (
            f"## Question\n{question}\n\n"
            f"## Expected answer\n{expected_answer}\n\n"
            f"## Answer A\n{answer_A or '(empty)'}\n\n"
            f"## Answer B\n{answer_B or '(empty)'}\n\n"
            f"Output the JSON verdict only."
        )},
    ]
    result = call_with_meter_retry(
        messages, model=model,
        response_format={"type": "json_object"},
        max_tokens=2048,
    )
    if result.error:
        return {"winner": None, "score_A": None, "score_B": None,
                "reason": None, "raw_response": "", "error": result.error}
    try:
        parsed = json.loads(result.raw_response)
        return {
            "winner": parsed.get("winner"),
            "score_A": int(parsed.get("score_A", 0)),
            "score_B": int(parsed.get("score_B", 0)),
            "reason": parsed.get("reason", ""),
            "raw_response": result.raw_response,
            "error": None,
        }
    except Exception as e:
        return {"winner": None, "score_A": None, "score_B": None,
                "reason": None, "raw_response": result.raw_response,
                "error": f"parse failed: {e}"}
