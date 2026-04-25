# 실험 1: Assertion 상한과 추론 품질

## 개요

assertion 수가 증가할 때 Gemma 4 E4B의 추론 품질이 어떻게 변하는지 측정한다.
변곡점(품질이 정체/하락하는 지점)을 찾아 실제 soft cap을 확정한다.

## dispatcher key

`assertion-cap` (`python run_experiment.py assertion-cap`)

## 하이퍼파라미터

- cap 값: [2, 4, 6, 8, 10, 12]
- repeat: `DEFAULT_REPEAT` (config.py)
- 시작 phase: SYNTHESIZE
- next_directive: "주어진 assertions를 종합하여 최종 답을 작성하라."

## 측정 항목

- assertion 수별 추론 정확도
- assertion 참조율 (실제 사용한 수 / 제공된 수)
- 응답 시간

## 판정 기준

- 품질이 정체/하락하는 변곡점 → 실제 soft cap 확정
- RT 결론(soft cap 8)이 적절한지 검증

## 결과 파일

- `results/exp01_assertion_cap_20260408_170400.json` (final)
- `results/exp01_assertion_cap_partial_*.json` (6 partial — 중간 저장)
- `exp01_run.log` (실행 로그)

## 핵심 메트릭

| trial | accuracy | num_assertions | tool_calls |
|-------|---------|---------------|-----------|
| (분석 보류 — task-07) | - | - | - |

## 변경 이력

- 2026-04-08: 실험 실행 (5 task × 6 cap × 3 trial = 90회 호출).
- 2026-04-25: experiments-task-04 으로 분리. 설명.md 흡수.
