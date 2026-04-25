# 실험 3: 오류 전파와 자기 교정

## 개요

**가설 H2를 검증한다:**

> 문신에 결함이 존재하면, 오류는 루프 진행에 따라 감쇠되지 않고 증폭된다.

추가로, 4.5B 모델이 기존 assertion의 모순을 스스로 감지할 수 있는지 확인한다.
감지율이 낮으면 오케스트레이터 레벨의 방어 메커니즘이 필수임을 의미한다.

## dispatcher key

`error-propagation` (`python run_experiment.py error-propagation`)

## 결함 유형

- `corrupt_content`: assertion 내용을 틀린 값으로 교체
- `inflate_confidence`: confidence 값을 0.95로 인위 부풀림
- `contradiction`: 모순되는 새 assertion 추가

## 하이퍼파라미터

- 정상 체인: 2 루프 실행 후 결함 주입
- 결함 후: 최대 6 루프 추가
- repeat: `DEFAULT_REPEAT` (config.py)
- skip_tasks: {"logic-01", "logic-02"} (JSON 파싱 불안정)

## 결과 파일

- `results/exp03_error_propagation_20260409_135411.json`

## 핵심 메트릭

| trial | accuracy | num_assertions | tool_calls |
|-------|---------|---------------|-----------|
| (분석 보류 — task-07) | - | - | - |

## 변경 이력

- 2026-04-09: 실험 실행.
- 2026-04-25: experiments-task-04 으로 분리. 설명.md 흡수.
