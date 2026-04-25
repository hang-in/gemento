# 실험 10: Reproducibility & Cost Profile

## 개요

3 condition × 9 task × N=20 trial = 540 호출 비교 실험.
- **Q1 (재현성)**: 같은 입력 N=20 trial 의 정답률 표준편차
- **Q2 (비용·시간)**: Gemma 8루프 vs Gemini 2.5 Flash 1회 trade-off

이전 9개 실험은 정확도 평균만 보고했지만 본 실험은 **외부 평가용 데이터**
(분산 + 비용) 를 산출한다.

## dispatcher key

`reproducibility-cost` (`python run_experiment.py reproducibility-cost`)

## 하이퍼파라미터

- DEFAULT_TRIALS: 20 (per condition × task)
- 9 task subset: math-01~04, synthesis-01·03·04, logic-03·04
- 3 condition: `gemma_8loop`, `gemma_1loop`, `gemini_flash_1call`
- gemma_8loop max_cycles: 15 (loop_saturation baseline_phase15 동등)
- Gemini 2.5 Flash 가격 (2025-04 기준): input $0.075/M, output $0.30/M
- gemini_flash_1call rate limit: 호출 후 1초 sleep (Google AI Studio 무료 tier 안전)
- API 키 로드: `gemento/.env` (GEMINI_API_KEY) 또는 `../secall/.env` (SECALL_GEMINI_API_KEY) 자동 fallback

## 결과 파일 (task-06 후 채워짐)

- `results/exp10_reproducibility_cost_*.json` — 540 trial 원본
- `results/exp10_report.md` — analyze.py 가 생성한 markdown report

## 핵심 메트릭 (task-06 후 채워짐)

| condition | accuracy mean ± std | total cost USD | total wallclock (s) |
|-----------|--------------------:|---------------:|--------------------:|
| gemma_8loop | TBD | $0 | TBD |
| gemma_1loop | TBD | $0 | TBD |
| gemini_flash_1call | TBD | TBD | TBD |

## 변경 이력

- 2026-04-26: 본 task-05 까지 — 코드 인프라 + 정적 검증 완료. task-06 에서 실증 실행.
