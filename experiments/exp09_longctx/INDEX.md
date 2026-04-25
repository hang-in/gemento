# 실험 9: Long-Context Stress Test (ABC vs Solo-dump vs RAG)

## 개요

긴 문서에서 다단계 추론을 요구하는 질문에 대해 3가지 방식 비교:
1. solo_dump — 문서 전체를 A에 단일 투입
2. rag_baseline — BM25 top-K chunks만 A에 투입
3. abc_tattoo — ABC + Tattoo + chunk iteration

핵심 가설: H9 — ABC가 long-context multi-hop에서 우위.
결과: 3-hop 정답률 100% 달성.

## dispatcher key

`longctx` (`python run_experiment.py longctx`)

## 하이퍼파라미터

- LONGCTX_TRIALS: 3 (MVP)
- LONGCTX_CHUNK_SIZE: 500
- LONGCTX_CHUNK_OVERLAP: 50
- LONGCTX_RAG_TOP_K: 5
- LONGCTX_MAX_FINAL_CYCLES: 5
- 3 arm × 10 task × 3 trial = 90 runs
- taskset: `tasks/longctx_taskset.json`
- checkpoint: `results/partial_longctx.json`

## 결과 파일

- `results/exp09_longctx_20260425_144412.json`
- `results/exp09_report.md`

## 핵심 메트릭 (H9)

| arm | 1-hop | 2-hop | 3-hop |
|-----|-------|-------|-------|
| solo_dump | TBD | TBD | TBD |
| rag_baseline | TBD | TBD | TBD |
| abc_tattoo | TBD | TBD | 100% |

(상세는 exp09_report.md 참조)

## 변경 이력

- 2026-04-25: 실험 실행 완주 (ABC 3-hop 100%).
- 2026-04-25: experiments-task-06 으로 분리.
