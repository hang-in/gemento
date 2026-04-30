---
type: result
status: done
updated_at: 2026-04-30
experiment: 실험 9 — Long-Context Stress Test (ABC vs Solo-dump vs RAG)
revision: 2026-04-30 (Phase 1 후속 — 5-trial 점수 하락 원인 분석 추가)
---

# 실험 9: Long-Context Stress Test 결과 보고서

## 1. 개요

Gemento ABC+Tattoo가 (a) Solo-dump를 능가하는가, (b) RAG baseline 대비 고유 기여를 가지는가를 장문 컨텍스트 환경에서 직접 측정한 실험.

| 항목 | 내용 |
|------|------|
| **모델** | Gemma 4 E4B (Ollama Q4_K_M, n_ctx=8K×4슬롯) |
| **실행일** | 2026-04-25 |
| **태스크셋** | `longctx_taskset.json` — 10 tasks, 3 size class × 3 hop type |
| **Arms** | `solo_dump` / `rag_baseline` / `abc_tattoo` |
| **실행 수** | 3 arms × 10 tasks × 3 trials = **90 runs** |

## 2. 3-Trial 결과 (원본)

### 전체 정확도 (v2 채점)

| Arm | Accuracy v2 | Accuracy v1 | Errors |
|-----|-------------|-------------|--------|
| solo_dump | 0.200 | 0.200 | 24/30 (format_error) |
| rag_baseline | 0.850 | 0.900 | 0 |
| **abc_tattoo** | **0.883** | **0.933** | 0 |

**Key Deltas (v2):**
- **H9a (abc − solo)**: **+68.3%p** ✅ 압도적 채택
- **H9b (abc − rag)**: **+3.3%p** ⚠️ 조건부 채택 (전체 미세, 3-hop에서 차별성)

### Size Class 분해

| Arm | Small 3K | Medium 10K | Large 20K |
|-----|----------|------------|-----------|
| solo_dump | 1.000 | 0.000 | 0.000 |
| rag_baseline | 1.000 | 0.875 | 0.750 |
| **abc_tattoo** | **0.667** | 0.875 | **1.000** |

### Hop Type 분해

| Arm | needle | 2-hop | 3-hop |
|-----|--------|-------|-------|
| solo_dump | 0.333 | 0.250 | 0.000 |
| rag_baseline | 1.000 | 0.875 | 0.667 |
| **abc_tattoo** | 0.778 | 0.875 | **1.000** |

### Per-Task 하이라이트

- `longctx-large-3hop-01`: solo 0% / rag 0% / **abc 100%** — RAG의 정보 단절 실증
- `longctx-small-needle-01`: solo 1.00 / rag 1.00 / **abc 0.33** — Small Paradox 핵심 케이스

### 에러 모드 (H9c)

| Arm | 주요 실패 패턴 |
|-----|--------------|
| solo_dump | `format_error` 24건 — n_ctx 초과 truncation |
| rag_baseline | `wrong_synthesis` 6건 — retrieval 성공 but 통합 실패 |
| abc_tattoo | `evidence_miss` 2 + `wrong_synthesis` 3건 |

## 3. 통계 검정 최종 결과 (Phase 1, 2026-04-30)

5 trial × 10 task (50 데이터포인트/arm) 기반 H9b 통계 검정:

### H9b (abc_tattoo vs rag_baseline)

| 검정 | 통계량 | p-value | 판정 |
|------|--------|---------|------|
| Paired t-test (task mean, n=10) | t=0.264 | 0.7976 | **NOT SIGNIFICANT** |
| Wilcoxon signed-rank | W=1.0 | 1.000 | **NOT SIGNIFICANT** |

- Overall mean: abc=0.530, rag=0.510 (Δ=+0.020)
- Cohen's d = 0.084 (효과 크기 극히 작음)
- Bootstrap 95% CI for Δ(abc−rag): **[−0.170, 0.210]** (포함 0)

**해석**: n=10 tasks로 검정력 부족. 비유의 = "효과 없음"이 아니라 "현재 데이터로 판단 불가". 전체 Δ=+2.0%p는 실질적 차이로 보기 어려움. → **H9b verdict: "조건부 채택"→"미결"로 변경**

### Size Class / Hop Type 분해 (5-trial)

| 그룹 | 값 | n_tasks | abc_mean | rag_mean | Δ |
|------|-----|---------|----------|----------|---|
| size_class | small | 2 | 0.400 | 0.600 | **−0.200** ◄ Small Paradox |
| size_class | medium | 4 | 0.525 | 0.525 | 0.000 |
| size_class | large | 4 | 0.600 | 0.450 | **+0.150** |
| hop_type | needle | 3 | 0.467 | 0.600 | −0.133 |
| hop_type | 2hop | 3 | 0.525 | 0.525 | 0.000 |
| hop_type | 3hop | 3 | 0.600 | 0.400 | **+0.200** |

### Small Paradox 상세 (5-trial)

| task_id | abc_mean | rag_mean | Δ | abc_trials |
|---------|----------|----------|---|------------|
| longctx-small-needle-01 | 0.200 | 0.600 | −0.400 | [0,0,1,0,0] |
| longctx-small-2hop-01 | 0.600 | 0.600 | 0.000 | [1,1,1,0,0] |

- 전체 소형 태스크: abc=0.400 vs rag=0.600 (Δ=−0.200) — **Small Paradox 확인**
- `small-needle-01`에서 ABC가 5 trial 중 1회만 정답 (0.200) vs RAG 3회 정답 (0.600)
- 5-trial 확대 후에도 패턴 지속: 노이즈가 아닌 실제 현상으로 판단

### 5-trial 점수 하락 분석 (2026-04-30 Phase 1 후속)

3-trial → 5-trial 시 양 arm 동시 큰 점수 하락 (abc 0.883→0.530, rag 0.850→0.510, 양쪽 약 −0.34) 의 원인 분석 결과 (`docs/reference/exp09-5trial-drop-analysis-2026-04-30.md`, `experiments/exp09_longctx/analyze_5trial_drop.py`):

- **(c) 시스템 결함 단독** 결정. trial 4-5 의 모든 데이터가 Windows 환경 model server (`http://yongseek.iptime.org:8005`) connection refused (WinError 10061) 로 인한 무효 실행.
  - rag/solo trial 4-5: 20/20 모두 `WinError 10061` error 필드
  - abc trial 4-5: 20/20 모두 `num_assertions=0, final_answer=null` (ABC orchestrator 의 try/except 가 connection 실패를 swallow)
- **3-trial × 3/5 검산 정확 일치**: 0.883 × 0.6 = **0.530** (abc), 0.850 × 0.6 = **0.510** (rag). 새로운 모델 비결정성 / sampling 변동 0.
- **답변 일치성**: trial 1-3 의 답변은 3-trial JSON 과 5-trial JSON 에서 10/10 task 일치 (append consistency 100%).

**H9b verdict 영향**: 위 §3 의 5-trial 통계 (paired t-test p=0.7976) 는 trial 4-5 무효 데이터 dilute 결과로 부당한 강등. 3-trial 결과 (Δ=+0.033) 가 여전히 H9b 의 가장 정확한 데이터. verdict 환원 또는 disclosure 추가는 후속 결정 (본 보고서는 데이터 결함 disclosure 까지).

**`run_append_trials.py` 절차 보강 후보**: connection error 발생 시 retry / trial 카운트 미증가 / 사전 healthcheck — 별도 plan.

## 4. 미결 사항 / 다음 단계

- **H9b 통계적 유의성 미달**: 전체 abc-rag 차이(+2.0%p)가 실질적으로 의미 없음. 3-hop(+20.0%p)에서만 차별성 잔존. **단**: 5-trial 데이터의 trial 4-5 가 인프라 결함 (위 §5-trial 점수 하락 분석) 으로 무효 — 통계 비유의 결론은 부당한 강등 근거. 3-trial 결과 (Δ=+0.033) 우선시 권고.
- **Small Paradox 해결 필요**: Phase 2/Exp10 후보. chunk 수가 적을 때 cycle iteration이 오버킬인지, 또는 ABC의 evidence_ref 축적 전략이 작은 문서에서 비효율적인지 분석 필요.
- ✅ **Taskset 오류 3건 수정 완료** (2026-04-30 Phase 1 후속): math-03 (96→88 + "round = square + 2" 제약), synthesis-04 (`[["reports"],["5"],["6"]]`), longctx-medium-2hop-02 (`"500 horsepower (500 hp)"`). `validate_taskset` 22 PASS / 0 FAIL.

## 5. 관련 파일

- 원본 결과: `experiments/exp09_longctx/results/exp09_longctx_20260425_144412.json`
- 5-trial 결과: `experiments/exp09_longctx/results/exp09_longctx_5trial_20260430_111330.json`
- 추가 trial 스크립트: `experiments/exp09_longctx/run_append_trials.py`
- 통계 검정 스크립트: `experiments/exp09_longctx/analyze_stats.py`
- 5-trial 점수 하락 분석 스크립트: `experiments/exp09_longctx/analyze_5trial_drop.py`
- 5-trial 점수 하락 분석 보고서: `docs/reference/exp09-5trial-drop-analysis-2026-04-30.md`
- 태스크셋: `experiments/tasks/longctx_taskset.json`
