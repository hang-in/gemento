# 실험 3.5: Cross-Validation Gate

## 개요

B(비판자)가 A의 결함 assertion을 교차 검증으로 감지할 수 있는지 테스트한다.
A-B-C 파이프라인 구축 전 게이트 실험 — B 단독 능력 검증.

감지율이 낮으면 오케스트레이터 레벨의 방어 메커니즘이 필수임을 의미한다.

## dispatcher key

`cross-validation` (`python run_experiment.py cross-validation`)

## 결함 유형

- `corrupt_content`: 3번째 assertion 내용 교체
- `inflate_confidence`: 1번째 assertion confidence 0.99로 부풀림
- `contradiction`: 모순되는 새 assertion 추가

## 하이퍼파라미터

- 사용 assertion: prefab_assertions[:8]
- repeat: `DEFAULT_REPEAT` (config.py)
- max attempts (parse retry): 2
- skip_tasks: {"logic-01", "logic-02"}

## 결과 파일

- `results/exp035_cross_validation_20260409_150703.json`

## 핵심 메트릭

| trial | accuracy | num_assertions | tool_calls |
|-------|---------|---------------|-----------|
| (분석 보류 — task-07) | - | - | - |

## 변경 이력

- 2026-04-09: 실험 실행 (B 단독 게이트 검증).
- 2026-04-25: experiments-task-04 으로 분리. INDEX.md 신규 작성.
