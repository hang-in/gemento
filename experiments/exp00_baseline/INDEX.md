# 실험 0: Baseline

## 개요

Gemma 4 E4B 단독 실행 (Tattoo·ABC 없음). 단순 prompt → response.
이후 모든 실험의 기준선.

## dispatcher key

`baseline` (`python run_experiment.py baseline`)

## 하이퍼파라미터

- repeat: `DEFAULT_REPEAT` (config.py)
- 모델: `MODEL_NAME` (config.py)
- system prompt: "You are a helpful reasoning assistant. Think step by step..."

## 결과 파일

- `results/exp00_baseline_20260408_080053.json`
- `results/exp00_baseline_20260408_082421.json`
- `results/exp00_baseline_20260408_102018.json`

## 핵심 메트릭

| trial | accuracy | num_assertions | tool_calls |
|-------|---------|---------------|-----------|
| (분석 보류 — task-07) | - | - | - |

## 변경 이력

- 2026-04-08: 실험 실행 (3 trial, 18회 실행).
- 2026-04-25: experiments-task-03 으로 분리.
