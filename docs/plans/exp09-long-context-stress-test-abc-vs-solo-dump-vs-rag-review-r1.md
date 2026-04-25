# Review Report: Exp09 — Long-Context Stress Test (ABC vs Solo-dump vs RAG) — Round 1

> Verdict: fail
> Reviewer: 
> Date: 2026-04-25 09:52
> Plan Revision: 0

---

## Verdict

**fail**

## Findings

1. experiments/orchestrator.py:229 — `run_abc_chunked()` is intended to accumulate evidence across many chunks, but `apply_llm_response()` still drops any new assertion once `len(active_assertions) >= ASSERTION_HARD_CAP` (10 in `experiments/config.py:20`). On medium/large long-context tasks this silently truncates evidence collection after the first 10 assertions, so the Task 05 contract is not actually met.
2. experiments/measure.py:739 — `evidence_hit_rate_abc["overall"]` is computed as the mean of per-trial hit rates instead of total matched evidence refs divided by total evidence refs. This violates the Task 07 metric definition and can misreport ABC retrieval quality when trials emit different numbers of `evidence_ref`s.

## Recommendations

1. Add a chunked-specific accumulation path or configurable hard cap so Exp09 can retain materially more than 10 assertions while still limiting prompt serialization separately.
2. Recompute overall evidence hit rate with global counters (`matched_refs` and `total_refs`) and keep the current per-hop averages as a separate view if desired.

## Subtask Verification

| # | Subtask | Status |
|---|---------|--------|
| 1 | Long-doc 태스크셋 설계 | ✅ done |
| 2 | Chunker 모듈 | ✅ done |
| 3 | BM25 tool 통합 | ✅ done |
| 4 | Tattoo 스키마 확장 | ✅ done |
| 5 | ABC chunked 오케스트레이터 | ✅ done |
| 6 | Exp09 실행 분기 | ✅ done |
| 7 | Measure analyzer + Gemini 핸드오프 | ✅ done |

