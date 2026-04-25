# 실험 4.5: Handoff Protocol

## 개요

A-B-C 직렬 파이프라인 + Handoff Protocol 메트릭 측정.
체크포인트 기능 포함: 중간 실패 시 이어서 시작 가능.

## dispatcher key

`handoff-protocol` (`python run_experiment.py handoff-protocol`)

## 하이퍼파라미터

- repeat: `DEFAULT_REPEAT` (config.py)
- termination: "모든 비판이 수렴하고 최종 답변이 확정되면 종료"
- checkpoint: `results/partial_handoff_protocol.json`

## 메트릭

- handoff_b2c (B→C 핸드오프 데이터)
- reject_memo (C의 reject 사유)
- 사이클별 tattoo_in/tattoo_out

## 결과 파일

- `results/exp045_handoff_protocol_20260412_004441.json`
- `results/exp045_handoff_protocol_20260413_045126.json`
- `results/exp045_handoff_protocol_20260414_135634.json`

## 핵심 메트릭

| trial | accuracy | num_assertions | tool_calls |
|-------|---------|---------------|-----------|
| (분석 보류 — exp045-v2 plan 참조) | - | - | - |

## 변경 이력

- 2026-04-12~14: 실험 실행 (3 회). 정답률 88.9% (9 task × 5 trial).
- 2026-04-25: experiments-task-05 으로 분리.
