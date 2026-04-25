# 실험 8b: Tool-Use Refinement (에러 메시지 + Prompt 강화)

## 개요

Exp08의 2개 부작용(calculator ^ 혼동, tool neglect)을 프롬프트·에러
메시지 개선으로 보완한 재측정. 태스크·파라미터는 Exp08과 동일.

핵심 가설: H8 — 도구 호출 에러 메시지 명료화로 정답률 개선.
결과: math-04 100% 달성.

## dispatcher key

`tool-use-refined` (`python run_experiment.py tool-use-refined`)

## 하이퍼파라미터

- TOOL_USE_REFINED_REPEAT: 5
- TOOL_USE_REFINED_MAX_CYCLES: 15
- TOOL_USE_REFINED_PHASE_PROMPT: True
- TASK_IDS: math-01, math-02, math-03, math-04
- 2 conditions: baseline_refined, tooluse_refined
- 2 arm × 4 task × 5 trial = 40 runs
- checkpoint: `results/partial_tool_use_refined.json`

## 결과 파일

- `results/exp08b_tool_use_refined_20260424_234043.json`
- `results/exp08b_report.md`

## 핵심 메트릭 (H8 채택)

| 조건 | 정답률 | 핵심 메모 |
|------|-------|----------|
| baseline_refined | TBD | exp08b_report.md 참조 |
| tooluse_refined | TBD | exp08b_report.md 참조 (math-04 100%) |

## 변경 이력

- 2026-04-24: 실험 실행 완주 (정답률 97% 달성).
- 2026-04-25: experiments-task-06 으로 분리.
