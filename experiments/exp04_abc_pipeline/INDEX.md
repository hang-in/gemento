# 실험 4: A-B-C Pipeline

## 개요

A-B-C 직렬 구조로 전체 파이프라인을 검증한다.
비교군: 실험 2 v2 (Python 오케스트레이터)와 동일한 태스크를 A-B-C로 실행.

## dispatcher key

`abc-pipeline` (`python run_experiment.py abc-pipeline`)

## 하이퍼파라미터

- repeat: `DEFAULT_REPEAT` (config.py)
- skip_tasks: {"logic-01", "logic-02"}
- 호출: `run_abc_chain` (orchestrator.py)

## 결과 파일

- `results/exp04_abc_pipeline_20260409_182751.json`

## 핵심 메트릭

| trial | accuracy | num_assertions | tool_calls |
|-------|---------|---------------|-----------|
| (분석 보류 — task-07) | - | - | - |

## 변경 이력

- 2026-04-09: 실험 실행 (A-B-C 통합 검증).
- 2026-04-25: experiments-task-04 으로 분리. INDEX.md 신규 작성.
