# 실험 8: Math Tool-Use

## 개요

A(제안자)에게 calculator/solve_linear_system/linprog 도구를 제공하고
math 태스크의 정답률 향상을 측정한다. B·C는 도구 없음.
2 arm(baseline/tooluse) × 4 math 태스크 × 5 trial = 40 runs.

## dispatcher key

`tool-use` (`python run_experiment.py tool-use`)

## 하이퍼파라미터

- TOOL_USE_REPEAT: 5
- TOOL_USE_MAX_CYCLES: 15
- TOOL_USE_PHASE_PROMPT: True
- TASK_IDS: math-01, math-02, math-03, math-04
- 2 conditions: baseline_phase15, tooluse_phase15
- checkpoint: `results/partial_tool_use.json`

## 결과 파일

- `results/exp08_tool_use_20260424_125350.json`
- `results/exp08_report.md`

## 핵심 메트릭 (H7)

| trial | accuracy | tool_calls | tool_errors |
|-------|---------|-----------|-------------|
| (분석 보류 — exp08_report.md 참조) | - | - | - |

## 변경 이력

- 2026-04-24: 실험 실행 (math-04 baseline 0% → tooluse 80%).
- 2026-04-25: experiments-task-06 으로 분리.
