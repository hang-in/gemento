# 실험 6: Solo Budget (ABC 시너지 비교군)

## 개요

단일 E4B 에이전트가 ABC와 동일한 총 compute 예산을 받았을 때의 성능 측정.
A-B-C 역할 분리가 단순히 반복 횟수 증가로 환원 가능한지 판별.

## dispatcher key

`solo-budget` (`python run_experiment.py solo-budget`)

## 하이퍼파라미터

- SOLO_MAX_LOOPS: 21 (ABC 평균 7.2 사이클 × 3 에이전트 ≈ 21 Ollama 호출)
- repeat: `DEFAULT_REPEAT` (config.py)
- checkpoint: `results/partial_solo_budget.json`

## 비교 기준

- 비교군: exp045_handoff_protocol (5b)
  - 9 tasks × 5 trials, 88.9% accuracy, ~21.6 Ollama calls/trial

## 결과 파일

- `results/exp06_solo_budget_20260415_114625.json`

## 핵심 메트릭

| trial | accuracy | actual_loops | final_phase |
|-------|---------|---------------|-------------|
| (분석 보류 — task-07) | - | - | - |

## 변경 이력

- 2026-04-15: 실험 실행 (Solo vs ABC 시너지 비교).
- 2026-04-25: experiments-task-05 으로 분리.
