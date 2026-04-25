# Review Report: experiments 디렉토리 모듈화 + 인덱스 체계 + 오프라인 정적 검증 — Round 1

> Verdict: fail
> Reviewer: 
> Date: 2026-04-25 22:00
> Plan Revision: 0

---

## Verdict

**fail**

## Findings

1. docs/plans/experiments-result.md:14 — 결과 문서에 `Verification results for Task 07`만 있고 Task 01~06에 대한 검증 블록이 전혀 없습니다. 각 서브태스크의 Verification 충족 여부를 확인할 수 없어 subtasks 1~6을 승인할 수 없습니다.
2. experiments/config.py:9 — `RESULTS_DIR`가 여전히 `experiments/results`를 가리키며, 분리된 러너들도 이를 그대로 사용합니다. 예를 들어 experiments/exp00_baseline/run.py:19 및 experiments/exp00_baseline/run.py:30, experiments/exp08b_tool_use_refined/run.py:39 및 experiments/exp08b_tool_use_refined/run.py:60은 새 결과와 partial checkpoint를 삭제된 상위 평면 디렉토리에 다시 쓰도록 되어 있어, 새 디렉토리 구조의 핵심 요구사항인 실험별 `expXX/results/` 저장을 깨뜨립니다.

## Recommendations

1. Task 01~06 각각에 대해 task 문서의 Verification 섹션을 실제로 실행한 결과를 `docs/plans/experiments-result.md`에 별도 블록으로 추가하세요.
2. 공용 `RESULTS_DIR` 의존을 제거하고, 각 `run.py`가 자신의 디렉토리 기준 `results/` 경로를 사용하도록 저장 helper를 모듈별로 고치거나 공용 helper로 통일하세요. partial checkpoint 파일도 같은 원칙을 따라야 합니다.

## Subtask Verification

| # | Subtask | Status |
|---|---------|--------|
| 1 | 정적 검증 인프라 + 디렉토리 템플릿 + 최상위 INDEX 골격 | ✅ done |
| 2 | 결과 JSON 30+개 → 실험별 `results/` 분류 (코드 변경 0) | ✅ done |
| 3 | exp00 분리 (단독, 패턴 확립) | ✅ done |
| 4 | ABC 계열 분리 | ✅ done |
| 5 | handoff·prompt·solo 계열 분리 | ✅ done |
| 6 | 후속 실험 분리 | ✅ done |
| 7 | dispatcher 슬림화 + 인덱스 완성 | ✅ done |

