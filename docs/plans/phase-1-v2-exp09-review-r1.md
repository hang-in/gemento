# Review Report: Phase 1 측정 기반 보강 — v2 역행 분석 + Exp09 통계 검정 — Round 1

> Verdict: fail
> Reviewer: 
> Date: 2026-04-30 09:53
> Plan Revision: 0

---

## Verdict

**fail**

## Findings

1. experiments/exp09_longctx/results — Task 03의 필수 산출물인 `exp09_longctx_5trial_*.json`이 존재하지 않습니다. 현재 디렉터리에는 원본 3-trial 결과(`exp09_longctx_20260425_144412.json`)와 stats 파일만 있어, "모든 (arm, task)가 5 trial" 검증 조건을 충족하지 못합니다.
2. experiments/exp09_longctx/analyze_stats.py:39-46 — 5-trial 결과가 없을 때 최신 `exp09_longctx_*.json`으로 자동 대체하도록 구현되어 있습니다. 실제 생성된 `exp09_stats_20260430_091333.json`도 `result_file=...exp09_longctx_20260425_144412.json`, `n_trials_per_task=3`를 기록하고 있어, Task 04가 요구한 5-trial 기반 분석이 아니라 3-trial 사전 분석으로 잘못 완료 처리됩니다.
3. docs/reference/researchNotebook.md:829 — Task 05는 열린 질문 #15를 닫아야 하는데, 현재 문구는 "`5-trial 실행 대기 중 — 미결`"로 남아 있습니다. 플랜 문서의 "열린 질문 폐쇄" 계약과 일치하지 않으며, Task 04 완료를 전제로 한 문서 갱신이 아직 끝나지 않았습니다.

## Recommendations

1. Task 03은 실제 `exp09_longctx_5trial_*.json` 산출 후에만 완료 처리하고, 필요하면 `run_append_trials.py` 실행 전제(Ollama 가동 여부)를 문서가 아니라 결과로 증명하는 쪽이 안전합니다.
2. `analyze_stats.py`는 기본 동작에서 5-trial 파일이 없으면 실패하도록 바꾸고, 3-trial 분석은 `--result`를 명시한 경우에만 허용하는 편이 Task 계약과 맞습니다.
3. 5-trial 분석 완료 후 `researchNotebook.md`, `researchNotebook.en.md`, `README.ko.md`, `README.md`, `docs/reference/results/exp-09-longctx.md`를 한 번에 동기화해 H9b verdict와 열린 질문 상태를 맞추는 것이 좋습니다.

## Subtask Verification

| # | Subtask | Status |
|---|---------|--------|
| 1 | v2 역행 진단 스크립트 | ✅ done |
| 2 | taskset expected_answer 전수 검증 | ✅ done |
| 3 | Exp09 추가 trial 실행 | ✅ done |
| 4 | Exp09 통계 검정 스크립트 | ✅ done |
| 5 | 문서 갱신 + 열린 질문 폐쇄 | ✅ done |

