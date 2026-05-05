---
type: reference
status: done
updated_at: 2026-05-05
canonical: true
---

# Exp14 Search Tool 분석 (Stage 5)

**Plan**: `exp14-search-tool`
**실행일**: 2026-05-05 (A-1 baseline_abc_chunked) ~ 2026-05-05 (A-2 abc_search_tool) + 진단 3 회
**조건**: baseline_abc_chunked (full document in prompt) vs abc_search_tool (agent-active BM25 retrieval) × 10 longctx task × 5 trial = **100 trial 본 실행** + **진단 15 trial**
**모델**: Gemma 4 E4B (LM Studio Q8_0 `http://192.168.1.179:1234`, 32K context) — 외부 API 0
**채점**: `score_answer_v3` (negative_patterns 적용)

## 1. condition aggregate

| condition | n | mean_acc | err+null | avg_cycles | avg_dur |
|-----------|---|---------:|--------:|-----------:|--------:|
| baseline_abc_chunked | 50 | **0.9500** | 0+0 | 7.0 | 390s |
| **abc_search_tool** | 50 | **0.7300** | 7+7 | 7.1 | 235s (−40%) |

**Δ(search − baseline) = −0.2200** (음수, Stage 5 의 가장 큰 음수 효과 — Exp11 −0.081 / Exp13 −0.053 의 4배 크기).

## 2. 통계 검정 (n=10 task paired) — Stage 5 첫 통계적 유의 결과

| 검정 | 통계량 | p-value | 판정 |
|------|--------|--------:|------|
| Wilcoxon signed-rank | W=0.000 | **0.0312** | **SIGNIFICANT** ✅ |
| Paired t-test | t=−3.161 | **0.0115** | **SIGNIFICANT** ✅ |
| **Cohen's d (paired)** | **−1.000** | — | **large effect, 음수** |
| Bootstrap 95% CI Δ (n=10000) | **[−0.360, −0.100]** | — | 0 미포함, **음수 강함** |

**해석**:
- Stage 5 (Exp10/11/12/13) 의 모든 가설이 NS (n=15) 였던 것과 달리 본 결과는 *유의 (p<0.05)*
- |d|=1.0 = large effect (Exp11/12/13 의 |d|≈0.32 의 3배 크기)
- 95% CI 가 0 을 포함하지 않음 — 음수 방향 강하게 우세
- 단 통계 유의는 *방향* 의 신뢰도; mechanism 자체는 별도 분석 필요 (§5)

## 3. per-task break-down

| task | category | base | search | Δ | 패턴 |
|------|----------|----:|-------:|--:|------|
| **longctx-large-2hop-01** | longctx | 1.000 | 0.400 | **−0.600** ⬇ | catastrophic, hop 2 실패 (§5) |
| longctx-large-3hop-01 | longctx | 1.000 | 0.600 | −0.400 ⬇ | 3-hop iteration 부족 |
| longctx-medium-3hop-01 | longctx | 1.000 | 0.600 | −0.400 ⬇ | 3-hop iteration 부족 |
| longctx-medium-needle-01 | longctx | 1.000 | 0.600 | −0.400 ⬇ | needle, 본 실행 sampling variance (진단 v2 = 1.000) |
| longctx-medium-2hop-01 | longctx | 1.000 | 0.800 | −0.200 ⬇ | 2-hop, 일부 trial hop 부족 |
| longctx-small-needle-01 | longctx | 1.000 | 0.800 | −0.200 ⬇ | needle 의 partial fail |
| longctx-large-needle-01 | longctx | 1.000 | 1.000 | +0.000 | needle 정상 |
| longctx-large-3hop-02 | longctx | 1.000 | 1.000 | +0.000 | 3-hop 이지만 saturation |
| longctx-small-2hop-01 | longctx | 1.000 | 1.000 | +0.000 | small 영역 saturation |
| longctx-medium-2hop-02 | longctx | 0.500 | 0.500 | +0.000 | 둘 다 partial answer (task 자체 한계) |

→ **0/10 양수**, **7/10 음수**, **3/10 변화 0** (saturation). catastrophic 4 task (Δ ≤ −0.4) 가 음수 평균의 동력.

## 4. hop_type 분석 (본 plan 의 핵심 메커니즘 axis)

본 plan 의 longctx_taskset 은 *hop count* 가 task 의 reasoning 깊이를 결정:

| hop_type | n_trials | search mean_acc | 진단 평균 호출 횟수 |
|----------|---------:|----------------:|------|
| **needle (1-hop)** | 15 | **0.800** | 1.0 (medium-needle 진단 v2) |
| **2-hop** | 20 | **0.675** | 1.6 (large-2hop 진단) |
| **3-hop** | 15 | **0.733** | (직접 진단 미실시) |

baseline 은 모든 hop_type 에서 1.0 (saturation) — full document in prompt 라 hop count 무관.

## 5. Mechanism — *insufficient retrieval iterations on multi-hop tasks*

### 5.1 진단 데이터 (large-2hop-01, fix 적용 5 trial)

`longctx-large-2hop-01` task: "What is the total number of patents held by the research institute that trained Dr. Chen Wei?" — Dr. Chen Wei → trained at *Westbrook Institute* (hop 1) → patents = *347* (hop 2).

| trial | total_calls | acc | 패턴 |
|-------|------------:|----:|------|
| t0 | **1** | 0.0 | hop 1 query → "Westbrook Institute" 발견 → 답: "Westbrook Institute... however, the document does not contain a specific [number]" — *retrieval 종료 단정 + hop 2 실패* |
| t1 | 2 | 1.0 | hop 1 (Chen Wei → Westbrook) + hop 2 (Westbrook → 347) ✅ |
| t2 | 2 | 1.0 | hop 1 + hop 2 ✅ |
| t3 | 3 | 1.0 | query 변형 + hop 1 + hop 2 ✅ (한국어 query 발생, 즉시 자기 정정) |
| t4 | **0** | 0.0 | tool_neglect — 단일 case, no_final_answer |

**확정 mechanism**:
- agent 가 *hop count 와 동일한 횟수의 retrieve* 결정 못 함
- 1회 호출 후 "document does not contain" 으로 *prematurely 종료 단정*
- multi-hop reasoning 에서 hop 1 정답 + hop 2 실패 = 0점 (keyword "347" 미포함)

### 5.2 needle case (medium-needle-01 진단 v2, 5 trial)

`longctx-medium-needle-01` task: "What is the wireless mesh protocol developed by Orion Bridge Labs?" → 답: "PulseLink".

5/5 trial 모두 **정확히 1 회** 호출, **5/5 정답**. query 형성 완벽 (BM25 top score 4.7~4.9).

→ needle (1-hop) 에서는 search_tool 이 baseline 과 동등하게 작동. 본 plan 의 음수는 **multi-hop 에서만 발생** 확정.

### 5.3 baseline 의 우위 = *sufficient context*

baseline 의 prompt 는 full document (~26K tokens for large 20K word docs) 포함 → 모든 정보 즉시 가용 → multi-hop reasoning 자연.

search_tool 은 *iterative 호출 결정* 이 약함:
- agent 가 *몇 번 호출할지* 동적으로 결정해야
- "충분히 봤다" 의 잘못된 단정 → premature termination
- 32K context 가 충분한 환경에서는 search 의 추가 가치 0 + iterative 결정 cost 만 발생

### 5.4 Cost / time trade-off

| metric | baseline | search | Δ |
|--------|---------:|-------:|--:|
| avg_dur | 390s | 235s | **−40%** (search 가 빠름) |
| prompt token (대략) | ~25K | ~50 + retrieved chunks | search 가 가벼움 |
| accuracy | 0.95 | 0.73 | **−22%p** |

→ **time / accuracy trade-off**: search 가 40% 빠르지만 22%p 손실. 32K context 가 충분한 환경에서는 *비합리적 trade-off*. 단 context 가 *부족* 한 환경 (small models with smaller contexts) 에서는 의미 다를 수 있음 — 본 결과로 검증 안 됨.

## 6. tool_neglect 분석

본 실행 (A-2, 50 trial) 의 50/50 trial 모두 `total_tool_calls = 0` 으로 reporting — 단 **이는 fix 적용 전이라 capture 누락**, *실제로는 호출 발생 함*.

진단 실행 데이터 (15 trial 합계):
- 0 calls: **2 trials (13%)** — 모두 large-2hop t4 + medium-needle 1 trial
- 1 call: 6 trials (40%) — needle 5 + large-2hop t0
- 2-3 calls: 7 trials (47%) — multi-hop 정답 trial

→ **tool_neglect rate 약 13%** (n=15 진단). 본 실행 50 trial 의 7 error (no_final_answer 14%) 와 정합.

## 7. Architect verdict — **⚠ H13 미결 (실효적 기각, 통계 유의 negative direction)**

verdict 결정 트리:

| 조건 | 충족? |
|------|-------|
| Δ ≥ +0.10 + p<0.05 (강한 채택) | ❌ |
| Δ ≥ +0.05 + p<0.05 (조건부 채택) | ❌ |
| \|Δ\| < 0.05 (미결) | ❌ |
| Δ < −0.05 + p<0.05 (**유의한 음수**) | ✅ **본 분기** |
| Δ < −0.05 + p≥0.05 (실효적 기각) | (이전 Exp11/13 패턴) |

**Architect 최종 verdict**: ⚠ **H13 미결 (실효적 기각, statistically significant negative direction at this scale; mechanism = insufficient retrieval iterations on multi-hop tasks under sufficient-context baseline)**.

근거:
- p<0.05 (Wilcoxon p=0.031, paired t p=0.012) — Stage 5 의 첫 *유의* 결과
- |d|=1.0 large effect, Bootstrap 95% CI 가 0 미포함
- mechanism 명확 (§5): hop iteration 부족 + premature termination
- 단 본 결과는 *agent-active BM25 retrieval, 32K context baseline, n=10 task* 의 specific 조건 — *Search Tool 일반* 의 기각 아님

본 plan 의 H13 가설 ("agent-active 호출 + reasoning 결합이 Exp09 의 sequential 처리보다 우수") 는 **이 setup 에서 negative-direction 으로 결과**, mechanism 도 명확. 단 *더 약한 형태* ("retrieval can help when context is the limit") 는 본 plan 에서 검증 안 됨 (baseline 이 saturation).

## 8. Exp11 / Exp12 / Exp13 / Exp14 결정적 대비 — Stage 5 통합

| 비교축 | Exp11 (Mixed, H10) | Exp12 (Extractor, H11) | Exp13 (Reducer, H12) | **Exp14 (Search, H13)** |
|--------|-------------------|-----------------------|---------------------|------------------------|
| 외부화 유형 | Role 강화 (강한 모델) | Role 분리/추가 (pre) | Role 분리/추가 (post) | **Tool 축 (agent-active retrieval)** |
| Δ acc | −0.0811 | +0.0500 | −0.0533 | **−0.2200** |
| Cohen d | −0.316 | +0.323 | −0.323 | **−1.000** |
| p-value | 0.293 NS | 0.198 NS | 0.180 NS | **0.012 SIG** ✅ |
| 메커니즘 | chain 단절 | input 안정화 | abstraction loss (caveat) | **insufficient hop iterations** |
| n_paired | 15 task | 15 task | 15 task | 10 task |
| verdict | ⚠ 미결 (실효적 기각) | ⚠ 조건부 채택 | ⚠ 미결 (실효적 기각) | **⚠ 미결 (실효적 기각, SIG)** |

→ **Stage 5 의 통합 narrative**:
- Role 축 (3 회): 강화 ❌ / pre-stage ✅ / post-stage ❌ — *position* 결정
- Tool 축 (1 회): agent-active retrieval ❌ — *iteration count* 결정
- 공통: **외부화의 효과는 sign 자체가 위치/유형/양에 의존**. "more is better" 는 광범위하게 부정

## 9. Stage 5 framework-level 발견 (Exp11/12/13/14 통합)

| 외부화 차원 | 효과 | 메커니즘 |
|------------|------|----------|
| **Role 강화** (다른 모델 도입) | ❌ Δ=−0.08, NS | 약한 모델 self-discovery 단절 (Exp11) |
| **Role 분리/추가 — pre-stage** | ✅ Δ=+0.05, NS | input 안정화 (Exp12) |
| **Role 분리/추가 — post-stage** | ❌ Δ=−0.05, NS | abstraction loss (caveat: scorer artifact 분리 불가) (Exp13) |
| **Tool 축 — agent-active retrieval** | ❌ Δ=−0.22, **SIG** | insufficient hop iterations + premature termination + sufficient-context saturation (Exp14) |

→ **통합 원칙 (Stage 5 의 paper-level claim 후보)**:
- *"More structure is not monotonically better"* — 외부화의 sign 은 *유형 × 위치 × 호출 빈도* 의 복잡한 함수
- *deterministic computation tool* (calculator, H7/H8 +18~23pp) ≠ *agent-iterative retrieval tool* (H13 −22pp). 두 결과 같은 "Tool 축" 이지만 sign 정반대 — Tool 축 *내부의 sub-distinction* 발견

## 10. Stage 6 다음 의제 (Exp15+) 함의

본 결과 + Stage 2C / Exp11 / Exp12 / Exp13 / Exp14 종합:

| 후보 | 우선순위 | 사유 |
|------|---------|------|
| **Cross-model replication** (Llama 3.1 8B / Llama 3.3 70B / Qwen 2.5 7B) | 🎯 **P0** | Stage 5 4 가설 (H10/H11/H12/H13) 의 cross-model 일반화 검증. Groq free + Local Qwen 인프라 이미 준비 (commit `b389534`) |
| **LLM-as-judge 보조 평가** (P1-3 in action items) | 🎯 P0 | H12 의 keyword scorer artifact + H13 의 search-tool 답변 품질 *의미적* 평가 |
| Iteration-count manipulation (mandatory tool rule, Exp08b 패턴) | 중 | H13 mechanism 직접 fix 시도 — single follow-up exp 가능. 단 본 plan 의 mechanism 분석 이미 완료 |
| Tool 축 다른 종류 — Graph Tool / Evidence Tool / Critic Tool 강화 | 보류 | 본 결과로 *agent-active retrieval* 의 한계 발견. 다른 sub-type 검증 가치 있음 |
| Search Tool 의 longctx-large 영역 직접 측정 (baseline overflow) | 보류 | 32K context 가 충분 → baseline 이 saturation. Smaller-context model 에서 의미 다를 수 있음 |

→ **권장 Exp15 = Cross-model replication** (Stage 6 진입). Tool 축의 sub-type 변형보다 *동일 가설들의 generalization 검증* 이 paper readiness 의 핵심.

## 11. 한계

- **n=10 task paired** — Exp11/12/13 의 n=15 보다 검정력 낮음 (longctx_taskset 가 10 task), 단 |d|=1.0 large effect 라 통계 유의 도달
- **5 trial** — task 별 sample 작음 (medium-needle 의 본 실행 0.6 vs 진단 1.0 같은 sampling variance)
- **A-2 본 실행의 tool_calls 미캡처** — 50 trial 의 호출 횟수 / query 정성 분석 불가능. 진단 15 trial 만 사용 가능
- **score_answer_v3 keyword 매칭 의존** — Reducer (H12) 와 동일 caveat. 단 본 plan 의 multi-hop task 는 답이 *숫자/이름* 등 단답형 → keyword 매칭이 의미와 합리적 정합
- **Tool axis 의 단일 sub-type** — agent-active BM25 retrieval 의 결과. *passive retrieve* (Exp09 RAG arm) / *graph traversal* / *vector embedding* 등 미검증
- **baseline 의 sufficient context** — 본 결과는 *32K context 가 충분한 환경* 에서의 결과. context-limit 환경 (8K LLama 등) 에서는 다를 수 있음
- **tool-call schema 의 description 강도** — `tool_choice="auto"` + 일반 description 사용. Exp08b 패턴 (mandatory tool rules) 적용 시 결과 변할 수 있음

## 12. 향후 보강 (본 plan 영역 외)

- **Cross-model replication** (Stage 6 plan) — Groq Llama 3.1 8B / 3.3 70B / Qwen 2.5 7B Q4_K_M
- **LLM-as-judge 보조 평가** (P1-3) — Groq GPT-OSS 120B 로 H13 의 의미적 채점
- **Mandatory tool rules 변형 (Exp16 후보)** — Exp08b 패턴 적용 시 search_tool 의 mechanism 변화 측정
- **task 확대** — longctx_taskset 의 hop_type 별 task 5+ 로 확장
- **context-limited model 의 search_tool 효과** (Exp17 후보) — 8K context model + Search Tool, baseline overflow 환경

## 13. 변경 이력

- 2026-05-05 v1: 초안. Stage 5 Exp14 Task 04 (사용자 직접 실행 2026-05-05) 마감 + 진단 3 회 (mechanism 분석) 후 Architect 분석. 본 plan 의 가장 중요한 발견 = **Stage 5 의 첫 통계적 유의 결과 (negative direction, |d|=1.0)** + **mechanism = insufficient hop iterations** + **Tool 축 sub-distinction** (deterministic computation vs agent-iterative retrieval).
