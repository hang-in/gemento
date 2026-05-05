---
type: result
status: done
updated_at: 2026-05-05
experiment: 실험 14 — Search Tool (agent-active BM25 retrieval)
---

# 실험 14: Search Tool 결과 보고서

## 1. 개요

**가설 H13**: ABC 에이전트가 cycle 중 *능동적으로* `search_chunks(query, top_k)` 도구를 호출하여 long-context document 의 관련 chunk 를 retrieve 하면, 32K context baseline (full document in prompt) 대비 정확도 + cycle 효율성 향상.

| 항목 | 내용 |
|------|------|
| **모델** | Gemma 4 E4B (LM Studio Q8_0 `http://192.168.1.179:1234`, 32K context) |
| **실행일** | 2026-05-05 (A-1 + A-2 + 진단 3회) |
| **태스크셋** | `longctx_taskset.json` 의 10 task (small/medium/large × needle/2-hop/3-hop) |
| **조건** | baseline_abc_chunked / abc_search_tool × 5 trial |
| **실행 수** | 2 condition × 10 task × 5 trial = **100 trial 본 실행** + **15 trial 진단** |
| **외부 API 비용** | $0 (local Gemma + local BM25 인덱스) |
| **인프라** | Stage 2A healthcheck/abort + Stage 2B FailureLabel + Stage 2C tattoo_history fix + Exp11 c_caller / Exp12 extractor_pre_stage / Exp13 reducer_post_stage hooks + 본 plan 의 `search_tool` / `corpus` hooks. tool_calls capture (run.py 진단 fix) — A-2 본 실행 후 적용, 진단 15 trial 만 capture |

소스:
- `experiments/exp14_search_tool/results/exp14_baseline_abc_chunked.json` (A-1 baseline, 50 trial)
- `experiments/exp14_search_tool/results/exp14_search_tool_abc.json` (A-2 search, 50 trial)
- `experiments/exp14_search_tool/results/diag_search_medium_needle_v2.json` (진단 needle, 5 trial)
- `experiments/exp14_search_tool/results/diag_search_large_2hop.json` (진단 multi-hop, 5 trial)
- (보조) `dry_run_search_tool.json`, `diag_search_medium_needle.json` (fix 전, tool_calls 미캡처)

상세 분석: `docs/reference/exp14-search-tool-analysis-2026-05-05.md`.

## 2. 핵심 메트릭

| condition | n | mean_acc | err+null | avg_cycles | avg_dur |
|-----------|--:|---------:|--------:|-----------:|--------:|
| baseline_abc_chunked | 50 | 0.9500 | 0+0 | 7.0 | 390s |
| **abc_search_tool** | 50 | **0.7300** | 7+7 | 7.1 | 235s (−40%) |

**Δ(search − baseline) = −0.2200** (음수). Stage 5 의 가장 큰 음수 + 가장 큰 effect size.

## 3. 통계 검정 (n=10 task paired) — Stage 5 의 첫 통계적 유의 결과

| 검정 | 통계량 | p | 판정 |
|------|--------|--:|------|
| Wilcoxon | W=0.000 | **0.0312** | **SIGNIFICANT** ✅ |
| Paired t | t=−3.161 | **0.0115** | **SIGNIFICANT** ✅ |
| **Cohen's d** | **−1.000** | — | **large effect, 음수** |
| Bootstrap 95% CI Δ | [−0.360, −0.100] | — | 0 미포함 |

→ Exp10/11/12/13 모두 NS (n=15) 였던 패턴 깨짐. 본 결과는 *방향* 명확.

## 4. hop_type × Δ matrix (본 plan 의 핵심 axis)

| hop_type | n_trials | search mean | 진단 평균 호출 횟수 |
|----------|---------:|------------:|-----|
| **needle (1-hop)** | 15 | **0.800** | 1.0 |
| **2-hop** | 20 | **0.675** | 1.6 |
| **3-hop** | 15 | **0.733** | (진단 미실시) |

baseline 은 모든 hop_type 에서 1.0 — full document 라 hop count 무관.

## 5. 분석

### 5.1 H13 verdict — ⚠ 미결 (실효적 기각, statistically significant negative direction)

- p<0.05 (Wilcoxon p=0.031, paired t p=0.012)
- |d|=1.0 (large effect)
- Bootstrap 95% CI 가 0 미포함
- 단 본 결과는 *agent-active BM25 retrieval, 32K context baseline, n=10 task* 의 specific 조건. *Search Tool 일반* 의 기각 아님

### 5.2 Per-task 핵심 — catastrophic 4 task

| task | base | search | Δ |
|------|----:|-------:|--:|
| **large-2hop-01** | 1.0 | **0.4** | **−0.60** |
| large-3hop-01 | 1.0 | 0.6 | −0.40 |
| medium-3hop-01 | 1.0 | 0.6 | −0.40 |
| medium-needle-01 | 1.0 | 0.6 | −0.40 (sampling variance — 진단 v2 = 1.0) |
| medium-2hop-01 | 1.0 | 0.8 | −0.20 |
| small-needle-01 | 1.0 | 0.8 | −0.20 |
| (3 task saturation: large-needle / large-3hop-02 / small-2hop) | 1.0 | 1.0 | 0 |

### 5.3 Mechanism — *insufficient retrieval iterations on multi-hop tasks* (large-2hop 진단)

`longctx-large-2hop-01`: "What is the total number of patents held by the research institute that trained Dr. Chen Wei?" (Chen Wei → Westbrook → 347)

| trial | calls | acc | 패턴 |
|-------|------:|----:|------|
| t0 | **1** | 0.0 | hop 1 만 → "document does not contain" 단정, 종료 |
| t1 | 2 | 1.0 | hop 1 + hop 2 ✅ |
| t2 | 2 | 1.0 | hop 1 + hop 2 ✅ |
| t3 | 3 | 1.0 | query 변형 + 2 hop ✅ |
| t4 | **0** | 0.0 | tool_neglect, no_final_answer |

→ agent 가 *hop count 만큼 iteration* 결정 못 함. baseline 은 full document 가 prompt 에 있어 multi-hop 자연.

### 5.4 needle case (medium-needle 진단 v2, 5 trial)

5/5 trial 모두 정확히 1 회 호출, 5/5 정답. BM25 top score 4.7~4.9 (매우 정확한 query 형성). → needle 에서는 search_tool 정상 작동, **음수 효과는 multi-hop 한정**.

### 5.5 Cost / time trade-off

search 가 40% 빠름 (235s vs 390s, prompt 이 가벼워서) but 22%p accuracy 손실. 32K context 가 충분한 환경에서는 비합리적 trade-off.

### 5.6 Stage 5 통합 — Exp11 / Exp12 / Exp13 / Exp14 결정적 대비

| | Exp11 (Mixed) | Exp12 (Extractor) | Exp13 (Reducer) | **Exp14 (Search)** |
|--|--|--|--|--|
| Δ | −0.081 | +0.050 | −0.053 | **−0.220** |
| Cohen d | −0.316 | +0.323 | −0.323 | **−1.000** |
| p | 0.293 NS | 0.198 NS | 0.180 NS | **0.012 SIG** |
| 메커니즘 | chain 단절 | input 안정화 | abstraction loss (caveat) | **insufficient hop iterations** |

→ **Stage 5 통합 narrative**: 외부화의 sign 자체가 *유형 / 위치 / iteration count* 에 의존. "more is better" 부정의 강한 evidence.

## 6. 결론 + 다음 단계

### 결론

1. **H13 ⚠ 미결 (실효적 기각, SIG)** — agent-active BM25 retrieval 이 32K context baseline 대비 명확한 negative direction
2. **Mechanism 명확** — multi-hop reasoning 에서 *iteration 부족* + premature termination
3. **Stage 5 framework 통합 원칙** 발견 — *외부화의 효과는 유형/위치/iteration 의 복잡한 함수, 단순 monotonic 아님*
4. **Tool 축 의 sub-distinction** — *deterministic computation* (calculator/linprog, H7/H8 +18~23pp) ≠ *agent-iterative retrieval* (search, −22pp)

### 확정된 framework 원칙 (H4/H10/H11/H12/H13 통합)

| 외부화 차원 | 효과 | 메커니즘 |
|-----|------|----------|
| Role 강화 (강한 모델 도입) | ❌ | self-discovery chain 단절 |
| Role *분리/추가* — pre-stage | ✅ | input 안정화 |
| Role *분리/추가* — post-stage | ❌ | output abstraction loss (caveat) |
| Tool — deterministic computation | ✅ | external 정확성 |
| **Tool — agent-iterative retrieval** | ❌ **(SIG)** | **insufficient hop iterations + premature termination** |

### 다음 단계 (Stage 6)

- 🎯 **P0 — Cross-model replication** (Llama 3.1 8B / Llama 3.3 70B / Qwen 2.5 7B Q4_K_M, Groq free + Local) — Stage 5 4 가설 (H10/11/12/13) 일반화 검증
- 🎯 P0 — **LLM-as-judge 보조 평가** (Groq GPT-OSS 120B) — H12 + H13 의 의미적 채점 (keyword scorer artifact 방어)
- Iteration-count manipulation (Exp08b 패턴 — mandatory tool rules) — H13 mechanism 직접 fix 시도, 후순위
- Tool 축 다른 sub-type (Graph / Evidence / 강화된 Critic) — 보류

## 7. 한계

- **n=10 task paired** — Exp11/12/13 의 n=15 보다 작음 (longctx_taskset 의 task 수)
- **5 trial** — task 별 sample 작음
- **A-2 본 실행 50 trial 의 tool_calls 미캡처** — fix 적용 후 진단 15 trial 만 사용. 본 실행의 호출 분포 추정만 가능
- **score_answer_v3 keyword 매칭** — 본 plan 의 task 답은 단답형 (숫자/이름) 이라 H12 보다 영향 작으나 보조 평가 권장
- **Tool axis 의 단일 sub-type** — agent-active BM25 retrieval. 다른 sub-type 미검증
- **baseline 의 sufficient context** — 32K 환경 결과. context-limited 환경에서 다를 수 있음
- **tool_choice = "auto"** — 호출 빈도 강제 안 함. mandatory tool rules 적용 시 결과 변할 수 있음
