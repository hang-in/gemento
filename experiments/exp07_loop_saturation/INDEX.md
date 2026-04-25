# 실험 7: Loop Saturation + Loop-Phase 프롬프트

## 개요

ABC 파이프라인의 루프 포화점 실측 + 루프 단계별 프롬프트 분화의 효과 검증.
2×4 요인 설계: 프롬프트(baseline/phase) × MAX_CYCLES(8/11/15/20).

## dispatcher key

`loop-saturation` (`python run_experiment.py loop-saturation`)

## 하이퍼파라미터

- LOOP_SAT_REPEAT: 3
- 8개 조건 (2 phase × 4 max_cycles)
- 12 task × 3 trial × 8 condition = 288 runs
- checkpoint: `results/partial_loop_saturation.json`

## 결과 파일

- `results/exp07_loop_saturation_20260424_015343.json`
- `results/exp07_report.md`

## 핵심 메트릭

| trial | accuracy | num_assertions | tool_calls |
|-------|---------|---------------|-----------|
| (분석 보류 — exp07_report.md 참조) | - | - | - |

## 변경 이력

- 2026-04-24: 실험 실행 완주 (288 runs).
- 2026-04-25: experiments-task-06 으로 분리.
