# 실험 5a: Prompt Enhancement

## 개요

A의 프롬프트 강화 후 A-B-C 파이프라인을 재실행한다.
변경점: SYNTHESIZE/VERIFY의 next_directive에서 final_answer 필수 제출 강조.

## dispatcher key

`prompt-enhance` (`python run_experiment.py prompt-enhance`)

## 하이퍼파라미터

- repeat: `DEFAULT_REPEAT` (config.py)
- skip_tasks: {"logic-01", "logic-02"}
- 변경 범위: prompt 만 (구조·로직 동일)

## 비교 기준

- 비교군: exp04_abc_pipeline (정답률 83.3%, synthesis-02 1/3)
- 통과 기준: synthesis-02 정답률 33%→66%+, 전체 정답률 ≥ 90%, 퇴행 없음

## 결과 파일

- `results/exp05a_prompt_enhance_20260410_145033.json`

## 핵심 메트릭

| trial | accuracy | num_assertions | tool_calls |
|-------|---------|---------------|-----------|
| (분석 보류 — task-07) | - | - | - |

## 변경 이력

- 2026-04-10: 실험 실행 (synthesis-02 trial 2,3 final_answer=None 실패).
- 2026-04-25: experiments-task-05 으로 분리.
