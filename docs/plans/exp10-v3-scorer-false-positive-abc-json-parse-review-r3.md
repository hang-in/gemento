# Review Report: Exp10 v3 — Scorer 강화 (false positive 제거) + ABC JSON parse 안정성 — Round 3

> Verdict: fail
> Reviewer: 
> Date: 2026-04-29 05:35
> Plan Revision: 0

---

## Verdict

**fail**

## Findings

1. experiments/tasks/taskset.json:254 — `logic-04` 의 첫 `negative_patterns` 가 `no other suspect` 같은 정상 결론 문장까지 매칭할 만큼 과도하게 넓습니다. `score_answer_v3` 가 이 패턴을 응답 전체에 대해 선행 검사하므로, “No other suspect fits the rules. Casey is the culprit.” 같은 올바른 답안도 0점 처리되는 false negative 가 남아 있습니다.

## Recommendations

1. `negative_patterns` 를 “no solution / no clear answer / cannot be identified” 같은 최종 부정 결론 표현으로 더 좁히거나, `score_answer_v3` 의 negative 검사를 결론부 tail 에만 적용하도록 제한하세요.
2. Task 01/02 검증 케이스에 “No other suspect ... Casey is the culprit” 형태의 정상 답안을 추가해 이 false negative 를 재발 방지하세요.

## Subtask Verification

| # | Subtask | Status |
|---|---------|--------|
| 1 | v3 채점기 설계 + 구현 | ✅ done |
| 2 | taskset.json 의 task 보강 | ✅ done |
| 3 | 540 trial 전수 v3 재산정 | ✅ done |
| 4 | ABC JSON parse 4 fail 진단 | ✅ done |
| 5 | orchestrator JSON 추출 강화 | ✅ done |
| 6 | result.md / 노트북 갱신 | ✅ done |

