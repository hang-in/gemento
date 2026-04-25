# 실험 2: 다단계 루프 품질 누적

## 개요

**제멘토의 핵심 가설(H1)을 검증한다:**

> 동일한 소형 LLM + 구조화된 문신 스키마에서,
> 추론 단계를 증가시킬 때 단일 추론 대비
> 통계적으로 유의미한 품질 개선이 발생하는가?

이 실험이 제멘토 프로젝트의 존재 이유를 증명하거나 반증한다.

## dispatcher key

`multiloop` (`python run_experiment.py multiloop`)

## 하이퍼파라미터

- loop_counts: [1, 2, 4, 8]
- repeat: `DEFAULT_REPEAT` (config.py)
- soft cap: `ASSERTION_SOFT_CAP` (config.py)

## 측정 항목

- 루프 수(1,2,4,8)별 최종 답변 정확도
- Baseline(실험 0) 대비 품질 향상(Quality_gain)
- 루프별 assertion 증가 곡선
- 루프별 confidence 추이
- 수렴까지 걸린 루프 수

## 판정 기준

```
Quality_gain > 0 이고 일관적 → H1 채택
Quality_gain ≤ 0           → H1 기각, 설계 재검토
```

## 결과 파일

- `results/exp02_multiloop_20260408_195242.json`
- `results/exp02_multiloop_20260409_072735.json`
- `results/exp02_report.md`

## 핵심 메트릭

| trial | accuracy | num_assertions | tool_calls |
|-------|---------|---------------|-----------|
| (분석 보류 — task-07) | - | - | - |

## 변경 이력

- 2026-04-08~09: 실험 실행 (6 task × 4 loop_count × 3 trial = 72 체인).
- 2026-04-25: experiments-task-04 으로 분리. 설명.md 흡수.
