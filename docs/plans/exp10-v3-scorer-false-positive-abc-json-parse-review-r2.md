# Review Report: Exp10 v3 — Scorer 강화 (false positive 제거) + ABC JSON parse 안정성 — Round 2

> Verdict: fail
> Reviewer: 
> Date: 2026-04-29 05:22
> Plan Revision: 0

---

## Verdict

**fail**

## Findings

1. experiments/measure.py:83 — `score_answer_v3`가 `negative_patterns`를 응답 전체에 대해 즉시 검사해 `contradiction` 같은 단어가 추론 본문에만 있어도 0.0을 반환합니다. `logic-04`의 정상적인 귀류법 풀이도 오답 처리될 수 있어, plan 의도인 “모순 결론 답 차단”보다 과도하게 넓은 차단입니다.

## Recommendations

1. `negative_patterns` 평가는 전체 응답이 아니라 tail/conclusion 영역으로 제한하거나, `conclusion_required`와 결합해 최종 결론 문맥에서만 차단되도록 좁히세요.
2. Task 01/03의 테스트와 rescore 근거 문서에 “정답 결론이 있으나 중간 추론에 contradiction이 포함된 정상 답안” 케이스를 추가해 false negative가 재발하지 않게 하세요.

## Subtask Verification

| # | Subtask | Status |
|---|---------|--------|
| 1 | v3 채점기 설계 + 구현 | ✅ done |
| 2 | taskset.json 의 task 보강 | ✅ done |
| 3 | 540 trial 전수 v3 재산정 | ✅ done |
| 4 | ABC JSON parse 4 fail 진단 | ✅ done |
| 5 | orchestrator JSON 추출 강화 | ✅ done |
| 6 | result.md / 노트북 갱신 | ✅ done |

