# Implementation Result: Exp09 — Long-Context Stress Test (ABC vs Solo-dump vs RAG)

> Developer: claude
> Branch: N/A
> Date: 2026-04-25 10:02
> Plan Revision: 0

---

## Summary

두 수정이 의도한 대로 적용되었습니다.

**Fix 1 — `orchestrator.py`**:
- `apply_llm_response` 시그니처에 `hard_cap: int | None = None` 추가 (기존 실험은 기본값 그대로 `ASSERTION_HARD_CAP=10` 사용)
- `run_abc_chunked`에서 `hard_cap=ASSERTION_HARD_CAP * 20` (=200)으로 호출 → 20K 문서 ~40 chunks × 5 assertions 분량도 수용

**Fix 2 — `measure.py`**:
- `hit_total / hit_matched` (trial 카운트 + rate 누적) → `hit_total_refs / hit_matched_refs` (전역 ref 카운트) 로 교체
- `overall` hit rate가 refs 수가 서로 다른 trial에 동일 가중치를 부여하던 오류 해소
- `hop_hits`에 쌓는 per-trial rate는 `by_hop` 평균 계산에만 사용되므로 그대로 유지

## Subtask Results

### 1. 두 수정이 의도한 대로 적용되었습니다.

**Fix 1 — `orchestrator.py`**:
- `apply_llm_response` 시그니처에 `hard_cap: int | None = None` 추가 (기존 실험은 기본값 그대로 `ASSERTION_HARD_CAP=10` 사용)
- `run_abc_chunked`에서 `hard_cap=ASSERTION_HARD_CAP * 20` (=200)으로 호출 → 20K 문서 ~40 chunks × 5 assertions 분량도 수용

**Fix 2 — `measure.py`**:
- `hit_total / hit_matched` (trial 카운트 + rate 누적) → `hit_total_refs / hit_matched_refs` (전역 ref 카운트) 로 교체
- `overall` hit rate가 refs 수가 서로 다른 trial에 동일 가중치를 부여하던 오류 해소
- `hop_hits`에 쌓는 per-trial rate는 `

