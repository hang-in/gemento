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

## 결과 파일

- `results/exp10_reproducibility_cost_20260428_175247.json` — v2 본 run 540 trial (Windows 측 산출)
- `results/exp10_logic04_flash_retry_20260429_033743.json` — gemini_flash logic-04 4 timeout 재시도 (timeout=300s)
- `results/exp10_math04_8loop_debug_20260428_205650.json` — gemma_8loop math-04 use_tools=True debug rerun (20 trial)
- `results/exp10_v2_final_20260429_033922.json` — math-04 + logic-04 patch 통합 v2 final (**canonical**)
- `results/exp10_v3_rescored_20260429_053939.json` — score_answer_v3 적용 540 trial 재산정 (**canonical**, rework r2 적용)
- 정식 보고서: `docs/reference/results/exp-10-reproducibility-cost.md`
- 패치 절차 disclosure: `docs/reference/exp10-v2-finalize-2026-04-29.md`, `docs/reference/exp10-v3-abc-json-fail-diagnosis.md`

## 핵심 메트릭 (v3 final, 540 trial)

| condition | mean_acc (v3) | cost_usd (180) | avg_dur | err+null |
|-----------|--------------:|---------------:|--------:|---------:|
| gemma_8loop | **0.781** | $0.0000 | 8 min | 8 |
| gemini_flash_1call | 0.591 | $0.0143 | 24 s | 0 |
| gemma_1loop | 0.413 | $0.0000 | 33 s | 11 |

상세 조건/per-task/disclosure 는 정식 보고서 참조.

## 변경 이력

- 2026-04-26: task-05 까지 — 코드 인프라 + 정적 검증 완료
- 2026-04-28: v2 본 run (540 trial, Windows)
- 2026-04-29: math-04 / logic-04 patch 통합 → v2 final, score_answer_v3 적용 v3 rescored, ABC 4 fail 진단 + full-cycles 사후 분석
