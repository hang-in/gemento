---
type: reference
status: done
updated_at: 2026-04-30
canonical: true
---

# Exp09 5-trial 점수 하락 원인 분석

**작성일**: 2026-04-30
**대상**: Exp09 (longctx) 의 3-trial → 5-trial 시 양 arm 동시 점수 하락 (commit `3ed255a` Phase 1 산출물)
**스크립트**: `experiments/exp09_longctx/analyze_5trial_drop.py`
**입력**:
- `experiments/exp09_longctx/results/exp09_longctx_20260425_144412.json` (3-trial 원본, 모든 arm 정상)
- `experiments/exp09_longctx/results/exp09_longctx_5trial_20260430_111330.json` (5-trial = 3-trial + append)

## 결과 요약

| arm | early_mean (trial 1-3) | late_mean (trial 4-5) | Δ | 3-trial × 3/5 검산 |
|-----|----------------------:|---------------------:|--:|-------------------:|
| abc_tattoo | 0.8833 | 0.0000 | −0.8833 | 0.8833 × 0.6 = **0.530** |
| rag_baseline | 0.8500 | 0.0000 | −0.8500 | 0.8500 × 0.6 = **0.510** |
| solo_dump | 0.2000 | 0.0000 | −0.2000 | 0.2000 × 0.6 = **0.120** |

Phase 1 의 5-trial 종합 mean (`exp09_stats_20260430_091333.json`):

| arm | mean | 검산 mean (3-trial × 3/5) | 일치 |
|-----|-----:|--------------------------:|:----:|
| abc_tattoo | 0.530 | 0.530 | ✅ |
| rag_baseline | 0.510 | 0.510 | ✅ |

→ **5-trial 의 점수는 3-trial mean 에 trial 4-5 의 0점을 합쳐 평균낸 결과 (3/5 dilute)**. 새로운 모델 비결정성 / sampling 변동 0.

## 원인 후보 분석

### (a) 환경 차이 — ✗ 부정

3-trial JSON 과 5-trial JSON 의 top-level meta 비교 (model / arms 라벨 / chunk_size / chunk_overlap / rag_top_k):
- **동일**. 차이 0.

### (b) 모델 비결정성 — ✗ 부정

trial 4-5 에 모델이 **호출조차 되지 않음**:
- rag_baseline / solo_dump trial 4-5 의 `error` 필드:
  ```
  [WinError 10061] 대상 컴퓨터에서 연결을 거부했으므로 연결하지 못했습니다
  ```
  (Windows 환경 model server connection refused — 모델 inference 자체 실패)
- abc_tattoo trial 4-5 의 raw 필드:
  ```json
  {"final_answer": null, "error": null,
   "num_chunks": 5, "num_assertions": 0, "evidence_refs_used": []}
  ```
  → `num_assertions: 0` = ABC orchestrator 의 Proposer 가 한 번도 assertion 을 만들지 못함 (= LLM 호출 실패). `error` 필드가 None 인 이유는 ABC 의 try/except 가 connection 실패를 swallow + 빈 결과로 fall through.

→ trial 4-5 는 **모델 출력이 아님**. sampling 변동 / 비결정성과 무관.

### (c) 시스템 결함 — ✅ 결정

| 증거 | 값 |
|------|-----|
| rag_baseline trial 4-5 error 카운트 | **20/20** (모든 WinError 10061) |
| solo_dump trial 4-5 error 카운트 | **20/20** (모든 WinError 10061) |
| abc_tattoo trial 4-5 final_answer null | **20/20** (`num_assertions: 0`) |
| 3-trial → 5-trial append consistency (trial 1-3 답변 보존) | **10/10 task** (모든 arm) |

→ trial 4-5 는 **실행 환경 인프라 결함** (Windows 환경에서 모델 서버 `http://yongseek.iptime.org:8005` 연결 거부). trial 1-3 의 데이터는 정상 보존.

`run_append_trials.py` 가 connection error 발생해도 trial 결과를 빈 채로 append + JSON 저장. analyze_stats.py 가 빈 trial 의 score 를 0 으로 처리하여 mean 이 dilute.

### (d) 채점 변동 — ✗ 부정

trial 1-3 의 답변은 3-trial JSON 과 5-trial JSON 에서 **10/10 task 일치** (`append consistency 10/10`). 동일 답변에 동일 score → 채점 분산 0.

## 결정 — 가장 가능성 높은 원인

**(c) 시스템 결함** 단독.

trial 4-5 는 모델 inference 실행 자체가 실패한 무효 데이터 (Windows model server connection refused 로 인한 인프라 결함). 5-trial 의 `0.530 / 0.510` 은 사실상 `3-trial mean × 3/5` 의 dilute 결과로, 새로운 통계 정보 없음.

## 함의

### 1. H9b verdict 영향

Phase 1 commit `3ed255a` 가 5-trial 통계 (paired t-test p>0.05, Wilcoxon W=10, p=0.6171) 를 근거로 H9b verdict 를 `Conditionally supported` → `Inconclusive` 강등.

본 분석 결과 trial 4-5 가 무효이므로 **5-trial 통계는 부당한 강등 근거**. **3-trial 결과 (abc=0.883, rag=0.850, Δ=+0.033) 가 여전히 H9b 의 가장 정확한 데이터**.

→ **권고**: H9b verdict 를 `Conditionally supported` 로 환원 또는 5-trial 데이터 무효 disclosure 와 함께 3-trial 기준 verdict 명시.

(verdict 환원은 Architect 결정 — 본 보고서는 데이터 결함 disclosure 까지.)

### 2. `run_append_trials.py` 절차 보강 후보

현재 동작: connection error → 빈 trial append + JSON 저장.

후보 보강:
- 옵션 A: connection error 발생 시 retry (지수 백오프) + 모든 retry 실패 시 trial 카운트 미증가
- 옵션 B: trial 추가 후 마지막 단계에서 trial 별 `error is not None` 비율 검사 → 임계값 초과 시 결과 저장 거부
- 옵션 C: validate_taskset 처럼 별도 healthcheck 단계 (모델 서버 ping 후 진행)

→ 후속 plan 후보 (본 plan Non-goals 보존 — Plan #1 결과 보고 후 사용자 결정).

### 3. 영문 노트북 / README 영향

- 영문 노트북: 5-trial 점수 (0.530 / 0.510) 는 표면상 정확하지만 컨텍스트 설명 필요. **추가 disclosure 노트** 권고 (Closed 추가만 정책).
- README: H9b 가 H1 evidence / Headline 에 직접 인용되지 않음 → README 영향 없음. researchNotebook 의 Exp09 섹션만 disclosure 추가.

## 분석 명령

```bash
.venv/bin/python -m experiments.exp09_longctx.analyze_5trial_drop --arm abc_tattoo
.venv/bin/python -m experiments.exp09_longctx.analyze_5trial_drop --arm rag_baseline
.venv/bin/python -m experiments.exp09_longctx.analyze_5trial_drop --arm solo_dump
```

각 arm 의 trial 1-3 vs 4-5 mean / null_answer / answer overlap / append consistency 출력. 정적 분석 (LLM 호출 0).
