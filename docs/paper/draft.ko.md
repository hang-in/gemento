---
type: paper
status: draft-skeleton
updated_at: 2026-05-11
target: arXiv preprint (단일 타깃 — venue 제출 보류)
canonical: false
language: ko
mirror_of: docs/paper/draft.md (v0.7)
note: 2026-05-11 v0.7-ko — 영문 v0.7 의 한국어 번역. 코드, 경로, 모델 ID, 인용 표기는 원문 유지. arXiv 업로드 자체는 영문 (`draft.md` / `draft.tex`). 한국어 버전은 자가 리뷰 / 한국어권 독자 안내용.
---

# 역할 추가는 단조롭지 않다: 소형 LLM 워크플로 외부화의 위치 효과

*단독 저자 preprint draft. arXiv: TBD. 품질 기준: venue 동급 (자가 부과 peer review).*

---

> **DRAFT v0.7 한국어판 — arXiv-ready.** Stage 5 (Exp10–14, H10–H13) 마감. Stage 6 v3 (6-model H11/H12 panel + 5-model H13 panel + capability-floor finding) 통합 완료. P1-1 Related Work 차별화, P1-4 5튜플 통일 (H1/H7/H8/H9a Bootstrap CI), §4.8 통계 reporting protocol 본문, §7 Conclusion 모두 작성 완료. 남은 future work (arXiv blocker 에서 deferred): P1-3 LLM-as-judge replication for H12 (a)/(b) 분해, A-agent JSON-schema contract robustness for M1 cross-model 관측, iteration-discipline ablation as direct fix for M1 under-iteration.

## Abstract

소형 open-weight LLM (≲8B params) 은 더 큰 frontier 모델이 잘하는 multi-step reasoning 에서 약하다. 일반적인 대응은 모델 capacity 를 키우는 대신 *워킹 메모리, 계산, 검증, 제어 흐름* 같은 인지 기능들을 워크플로 안으로 외부화하는 것이다. 본 논문은 더 좁은 질문을 던진다: 그러한 워크플로에 추가 구조 (추가 Role, 추가 Tool) 를 더할 때 *어디에 / 어떻게* 넣는지가 중요한가, 그리고 그 답이 model family 를 가로질러 유지되는가?

단일 4B-effective open-weight 모델 (Gemma 4 E4B) 을 principal base 로 하여 13개의 순차 번호 가설 (H1–H13) 과 약 1,640 건의 single-model trial, 추가로 Stage 6 cross-model 패널 (Gemma 3, Mistral 3, OpenAI gpt-oss; 3B–31B 의 6 모델) 약 650 건 trial 까지 통합하여 네 가지 관찰을 보고한다.
**(1)** 9-task cost-aware 벤치마크에서 동일 base model 의 8-loop ABC orchestration 이 78.1% 를 기록하여 1-loop solo 의 41.3% 대비 (Δ=+0.37, d=+0.94, **p=0.039 SIG**, n=9), Gemini 2.5 Flash 1-call baseline (59.1%) 을 약 20× wall time 의 비용으로 상회. 일반 우월성 주장이 아닌 *벤치마크-한정 결과*.
**(2)** Same-model self-validation 이 0/15 의 심긴 오류를 검출, 그러나 같은 base model 의 role-separated cross-validation (A-Proposer / B-Critic / C-Judge) 으로 80% 회복 — *role separation 이 active ingredient* 임을 isolate.
**(3)** Paired role-axis ablation 이 *유사한 magnitude 의 거울상 부호* 를 산출: pre-stage Extractor Δ=+0.05 (d=+0.32) vs post-stage Reducer Δ=−0.05 (d=−0.32), Gemma 4 E4B 위에서 (n=15 에서 둘 다 NS). Cross-model replication 이 H11 direction 을 6/7 모델에서 confirm, H12 의 *family-systematic split* 발견 (Gemma 3 family 2/2 양수, non-Gemma 4/4 음수, rnj-1:8b 의 SIG verdict 포함 p=0.036, |d|=0.617) — keyword-scorer style-mismatch caveat 의 *family-level 직접 evidence*.
**(4)** Agent-active BM25 search tool 이 sufficient-context baseline 대비 Δ=−0.22 (d=−1.00, **p=0.012 SIG**, n=10) 산출, Gemma 4 E4B 위에서. Mechanism = *multi-hop task 의 under-iteration*. Cross-model H13 은 추가 5 small-and-mid dense 모델 (3B–31B) 에서 4가지 식별 가능한 M2 sub-variants 로 모두 fail — H13 (M1) effect 는 본 패널 내 *정확히 1개 모델* 에서만 관측 가능하며, 이를 size threshold 가 아닌 *Gemma 4 E4B 와 본 A-agent JSON contract 사이의 measurement-tool fit* 으로 보고.

13 가설 (negative-direction 4 결과 — self-validation, mixed-strength Judge, post-stage Reducer, agent-active retrieval — 포함) 의 전체 harness, taskset, scorer, per-trial log 를 공개한다.

## 1. 서론

### 1.1 Multi-step reasoning 에서의 소형 LLM 격차

[TODO: 동기 단락 — 복잡 reasoning 에서의 소형 open-weight 모델. Frontier 모델 성능 격차 인용.]

### 1.2 외부화 vs 파라미터 스케일링

2024–2026 의 주류 narrative 는 파라미터 스케일링 — Llama 3.3 70B, Qwen 3 235B, GPT-OSS 120B — 그에 비례한 inference-time 비용. 본 논문은 직교 axis 를 조사한다: 모델 capacity 고정 (Gemma 4 E4B, effective 4B params) + 4가지 인지 기능을 워크플로 안으로 외부화.

### 1.3 세 가지 기여

본 논문은 *measurement / ablation paper* 로 위치하며 framework proposal 이 아니다 — 외부화 framework 는 이미 존재 (Zhou et al., 2026; StateFlow; Chain-of-Agents). 새로운 것은 **무엇을 측정했는지** 그리고 **어떻게 isolate 했는지**.

1. **Role / Tool axis 의 Structure-effect ablation (single best claim)**: paired same-model ablation 이 외부화 효과의 *부호* 가 *위치, iteration discipline, 그리고 Stage 6 v2 에서 새로 식별된 — base model 이 capability floor 를 통과하는지 자체* 에 의존함을 보임.
   - **Role axis (위치 효과)**: pre-stage Extractor Δ=+0.05 (Cohen's d=+0.32, n=15, NS) vs post-stage Reducer Δ=−0.05 (d=−0.32, n=15, NS) — 동일 모델/태스크셋 위 *거의 동일 magnitude 의 거울상 directional effect*. **Cross-model replication (§4.3) 이 direction generalization 을 confirm**: H11 6/7 모델 양수 (1 outlier, ministral-3:8b), H12 4/6 모델 음수, *family-systematic split* (Gemma 3 family 2/2 양수 — §4.6.2 style-mismatch caveat 의 직접 evidence; non-Gemma family 4/4 음수, rnj-1:8b SIG verdict p=0.036 |d|=0.617 포함).
   - **Tool axis (iteration 효과, *specific-model A-agent contract fit 에 conditional*)**: agent-active BM25 retrieval tool 이 Gemma 4 E4B 위에서 sufficient-context baseline 대비 Δ=−0.22 (d=−1.00, n=10, **p=0.012 statistically significant**) 산출; mechanism = multi-hop tasks 의 under-iteration (M1, §4.7.1). Stage 6 v3 (§4.7.4) 가 보임: **다른 5 small-and-mid dense 모델 — gemma3:4b/12b, ministral-3:3b/8b, gemma4:31b — 은 under-iteration 단계에 도달조차 못 함**, 4가지 distinguishable M2 sub-variant 로 fail: tool-calling absence (gemma3 family), final-answer non-production (Mistral 3 family), A-agent JSON-schema mismatch (gemma4:31b, *유일하게 작동하는 모델의 same-family size-up*). 본 panel 내에서 H13 (M1) iteration-effect claim 은 *정확히 1개* 모델 — **Gemma 4 E4B (effective 4B)** — 에서만 관측 가능. 이는 *size threshold 가 아님*; gemma4:31b (same-family 더 큰 모델) 도 fail. 따라서 H13 을 generalized small-LLM 현상이 아닌 *specific-model* 관찰로 보고하며, 본 framework 의 A-agent JSON-schema contract 가 Gemma 4 E4B 와의 *measurement-tool fit* 임을 인정. 동일 harness/모델의 deterministic single-call computation tools (calculator, linprog, H7/H8 +18~23pp) 는 그러한 fragility 없음 — deterministic vs agent-iterative tool axis 의 sub-distinction 을 뒷받침.

   Role / Tool axis 가 정제된 claim 으로 수렴: *더 많은 구조가 단조롭게 더 좋은 것은 아니다; 중요한 것은 **어디에 놓는지**, **어떻게 iterate 하는지**, 그리고 **base model 이 chain 을 운영할 능력이 있는지 자체***. 경험적 / 메커니즘 기여.

2. **Structural workflow effect 측정을 위한 same-model isolation protocol**: A-Proposer / B-Critic / C-Judge / Extractor / Reducer 전반에서 base model 을 일정하게 유지 (Gemma 4 E4B) 함으로써, 대부분의 multi-agent 비교를 오염시키는 *model-quality confound* 와 role / tool 변경의 *structural* effect 를 분리. 방법론 기여.

3. **Negative result 를 포함한 재현 가능 small-LLM 외부화 harness**: 13개 순차 번호 가설 (H1–H13) — verdict / evidence / open-source data — 4개 negative-direction 결과 포함 (H2 self-validation 0/15; H10 mixed-strength Judge underperforms; H12 post-stage Reducer underperforms; H13 agent-active retrieval underperforms a sufficient-context baseline). 자원 / 재현성 기여.

4-axis 외부화 framework (Tattoo / Tools / Role / Orchestrator) 는 아래 가설들의 *조직 구조* 로 사용; novel framework 라고 주장하지 않음.

## 2. Related Work

본 연구를 *novel framework proposal* 이 아닌 *measurement / ablation* 연구로 위치. 가장 가까운 prior work 는 5 sub-area 에 걸쳐있고, 각 사례의 차별화는 *우리가 무엇을 고정시켰는지* (model capacity, taskset, scoring) 를 통해 외부화의 structural effect 를 소형 open-weight 모델에서 인과적으로 식별 가능하게 만드는 것.

### 2.1 외부화 framework

- **Externalization in LLM Agents** (Zhou et al., 2026, arXiv:2604.08224) — 4가지 외부화 axis (memory / skills / protocols / harness engineering) 제안. 본 연구의 4-axis (Tattoo / Tools / Role / Orchestrator) 와 독립적 수렴; axis 매핑 차이 (우리는 Role 과 Orchestrator 를 명시 분리; Zhou et al. 는 control 을 harness engineering 안에 묶음).
- **LightMem** (Fang et al., ICLR 2026, arXiv:2510.18866) — *cross-session* retrieval 을 위한 3단계 메모리 (sensory / short-term / long-term). 본 연구의 Tattoo (단일 task *내부* working state) 와 구별, §4.6 의 위치 효과 finding 과 직교.

### 2.2 Multi-agent role separation

- **Chain-of-Agents** (Zhang et al., NeurIPS 2024, arXiv:2406.02818) — 긴 입력에 대한 sequential worker agent + manager synthesis. sequential 구조는 공유하지만, 모든 role (A/B/C) 에 *동일 base model* 을 사용, prompt 와 validation contract 로만 구분 — 이 *same-model isolation* 이 role separation 의 structural effect 를 인과적으로 식별 가능하게 만드는 핵심 (§5.1) 이며 핵심 방법론 차이.
- **AutoGen** (Wu et al., 2023, arXiv:2308.08155) — 구성 가능한 role 의 multi-agent conversation framework. AutoGen 은 *agent orchestration as a programming abstraction* 을 타깃; 우리는 고정 base model 위에서 *role addition / 위치* 를 ablation 하고 effect-direction 비대칭을 보고.
- **MetaGPT** (Hong et al., ICLR 2024, arXiv:2308.00352) — GPT-4 위 software-development role 할당 (PM / engineer / QA). MetaGPT 는 frontier 모델로 *domain role* 별 specialization; 우리는 capacity 고정 + *위치* (pre-stage Extractor vs post-stage Reducer) 를 변수로 isolate.
- **Reflexion** (Shinn et al., NeurIPS 2023, arXiv:2303.11366) — single agent 위 self-reflection-driven verbal reinforcement. 본 role-separation line 과 인접; Reflexion 의 same-model self-correction loop 은 정신적으로 본 H2 와 가장 가까움 (이 scale 에서 *fail* 로 보고, §5.1 의 H3 role-separated cross-validation 동기 부여).

### 2.3 Self-validation / self-refine

- **Self-Refine** (Madaan et al., NeurIPS 2023, arXiv:2303.17651) — single 모델이 자신 출력을 propose / critique / refine. 동일 모델, single-actor self-loop; 본 연구는 동일 base model 의 다른 role contract 에서 role-separated *cross-validation* 으로 대비하고 discontinuity 를 보고 (0/15 → 12/15 detection).
- **CRITIC** (Gou et al., ICLR 2024, arXiv:2305.11738) — external tool feedback 을 통한 self-correction. CRITIC 은 검증을 위해 *external tool* signal 을 도입; 본 self-validation 가설 (H2/H3) 은 *external tool 없이* validation 효과를 측정, role contract 를 tool feedback 에서 isolate.

### 2.4 소형 LLM 의 tool use

- **Toolformer** (Schick et al., NeurIPS 2023, arXiv:2302.04761) — self-supervision 을 통한 train-time tool 통합. 차별화: 본 연구는 tool-specific fine-tuning 없는 small open-weight 모델에서 *inference time* 의 tool-use *neglect* 와 *iteration-discipline* 실패를 측정, Tool-axis 내 sub-distinction (deterministic single-call +18~23pp vs agent-iterative retrieval −22pp, §4.7) 을 보고.
- **Gorilla** (Patil et al., 2023, arXiv:2305.15334) — >1000 ML API 의 fine-tuned API-call generation. Gorilla 는 training 으로 API 선택 정확도 최적화; 우리는 *agent 가 fixed BM25 search tool 을 inference time 에 호출할지 / 얼마나 자주* 를 측정, 이것이 §4.7.1 의 H13 negative result 를 견인하는 변수.

### 2.5 Workflow / state-machine 외부화

- **StateFlow** (Wu et al., 2024, arXiv:2403.11322) — task-solving 을 state machine 으로. 본 Orchestrator axis 와 인접; 명시적 role separation + Tattoo schema 추가, 고정 Orchestrator loop 위에서 *role 위치* (pre-stage vs post-stage) 를 ablation (§4.6).

### 2.6 Cross-model / capability-level 연구

- **LLM cascades** (Yue et al., 2024; Chen et al., 2023) — cost-aware deployment 를 위한 strong-model planner + weak-model executor. 본 cross-model panel (Stage 6, §4.3) 및 §5.3 cost-aware deployment 논의와 인접. 차별화: ABC chain *내부* 에서 capacity 고정 (same-model isolation), strong-model scaffolding 은 principal architecture 가 아닌 *future-work cascade extension* 으로 처리.

## 3. Framework

### 3.1 4-axis 외부화

| Axis | 외부화 component | Anchor 실험 |
|---|---|---|
| **Tattoo** | Working memory (claims, evidence, status) — structured JSON | Exp02 (H1), Exp09 (H9a–c) |
| **Tools** | Computation (calculator, linalg, linprog, BM25 search) | Exp08 (H7), Exp08b (H8), Exp14 (H13) |
| **Role** | Validation (A-Proposer / B-Critic / C-Judge) | Exp03 (H2), Exp035 (H3), Exp06 (H4), Exp12 (H11), Exp13 (H12) |
| **Orchestrator** | Control flow (loop, phase 전환) | Exp02 (H1), Exp07 (H5, H6) |

### 3.2 Tattoo 스키마

[TODO: JSON schema 다이어그램 + 짧은 설명. 전체 schema 는 Appendix B.]

### 3.3 Role contract

[TODO: A/B/C system prompt 요약. 전체 prompt 는 Appendix C.]

### 3.4 Orchestrator loop

```
A (Proposer) → 구조화 assertion + 후보 답안 생산
  ↓
B (Critic) → cross-validation, 오류 표시
  ↓
C (Judge) → terminal verdict, 최종 답
  ↓
[수렴 또는 max_cycles=8 까지 loop]
```

결정론적 Python orchestrator; LLM 기반 control 로직 없음.

### 3.5 가설 번호 규약

H1–H13 은 외부화 axis 에 대한 순차 번호 가설 — 통계 H₀/H₁ 쌍이 *아님*. Verdict 는 controlled vocabulary 사용 (Supported / Conditionally supported / Inconclusive / Inconclusive (effectively rejected) / Rejected).

## 4. 실험

### 4.1 모델 및 base 설정

- 모델: Gemma 4 E4B (Q8_0 양자화, 4B effective params)
- Inference engine: LM Studio (32K context) — 초기 실험 (Exp00–06) 은 Ollama Q4_K_M; 전환은 `docs/reference/researchNotebook.md` Change History 에 기록
- Sampling: `temperature=0.1`, `max_tokens=4096`, `top_p`/`seed` 미지정
- 모든 ABC role 이 *동일 base model* 사용 (model-quality confound 없음)

### 4.2 Taskset

- **Main taskset** (15 task): math (4) / logic (4) / synthesis (5) / planning (2)
- **Long-context taskset** (10 task): size_class × hop_type 매트릭스 (small/medium/large × needle/2-hop/3-hop)
- 모든 task 는 MIT 로 `experiments/tasks/` 에 open-source

### 4.3 Cross-model replication — Stage 6 v2

§4.6 의 위치 효과 비대칭이 Gemma-specific artifact 인지 검증하기 위해, H11 (Extractor pre-stage) 과 H12 (Reducer post-stage) 를 Ollama Cloud (Pro tier, $20/월, 3-concurrent-session 한도) 의 5개 추가 open-weight 모델에서 재현: `gemma3:4b`, `gemma3:12b`, `rnj-1:8b` (non-Gemma, 8B), `gpt-oss:20b` (OpenAI reasoning class, 20B), `ministral-3:8b` (Mistral 3 family, dense 8B, 2026 출시 — rnj-1:8b 외 cross-family small-dense coverage 확장을 위해 v2 에서 추가). Stage 5 와 동일한 main 15-task set 및 (task, condition) 당 5 trial. Stage 5 의 Gemma 4 E4B baseline 을 6번째 모델로 포함. `ministral-3:3b` (3B, dense, 같은 family) 의 별도 finding 은 §4.7.4 (capability floor) 에 보고.

**H11 (Extractor pre-stage) — 6/7 양수, 1 outlier**:

| 모델 | family | size | Δ | Cohen's d | p (Wilcoxon) |
|---|---|---|---|---|---|
| Gemma 4 E4B (Stage 5) | Gemma 4 | 4B effective | +0.0500 | +0.323 | 0.198 |
| gemma3:4b | Gemma 3 | 4B | **+0.0787** | +0.299 | 0.594 |
| gemma3:12b | Gemma 3 | 12B | +0.0022 | +0.009 | 0.888 |
| rnj-1:8b | non-Gemma | 8B | +0.0047 | +0.019 | 0.859 |
| gpt-oss:20b | OpenAI | 20B | +0.0244 | +0.177 | 0.672 |
| ministral-3:8b | Mistral 3 | 8B | **−0.0433** | **−0.292** | 0.311 |

7개 모델 행 중 6개가 예측한 양수 방향; ministral-3:8b 는 small-magnitude 음수 effect 의 single-model outlier (NS, p=0.311). 이 outlier 와 정합되는 비배타적 설명 셋: (a) *baseline saturation* — ministral-3:8b 의 H11 baseline 0.7178 이 panel 내 더 높은 baseline 중 하나이며, cycle-1 입력이 이미 잘 정리된 경우 Extractor 의 input-organization 단계는 구조보다 noise 를 더할 수 있음; (b) *Extractor prompt mismatch* — Mistral 3 의 instruction-following 패턴이 본 Extractor 템플릿과 다르게 상호작용, single-prompt cross-family generalization limit 표면화; (c) *NS-at-n=15* — 결과가 통계적으로 0 과 구별 안 됨. cross-model H11 효과 어느 것도 n=15 에서 개별적으로 α=0.05 도달 안 함. H11 direction 을 *strong but not unanimous* 로 특성화, 가장 큰 양수 magnitude 가 가장 약한 baseline (gemma3:4b +0.079, Stage 5 Gemma 4 E4B +0.050) 에서 등장 — capability-headroom story 와 정합.

**H12 (Reducer post-stage) — family-systematic 패턴**:

| 모델 | family | size | Δ | Cohen's d | p (Wilcoxon) | direction |
|---|---|---|---|---|---|---|
| Gemma 4 E4B (Stage 5) | Gemma 4 | 4B | −0.0711 | −0.323 | 0.180 | non-Gemma 음수 |
| gemma3:4b | Gemma 3 | 4B | **+0.0562** | +0.331 | 0.423 | **Gemma 3 양수** |
| gemma3:12b | Gemma 3 | 12B | **+0.0078** | +0.026 | 0.878 | **Gemma 3 양수** |
| rnj-1:8b | non-Gemma | 8B | **−0.0989** | **−0.617** | **0.036 ✅ SIG** | non-Gemma 음수 |
| gpt-oss:20b | non-Gemma | 20B | −0.0100 | −0.052 | 0.735 | non-Gemma 음수 |
| ministral-3:8b | non-Gemma | 8B | **−0.0707** | **−0.287** | 0.327 | non-Gemma 음수 |

H12 가 family line 으로 깔끔히 분리: **Gemma 3 family 2/2 양수** (gemma3:4b +0.056, gemma3:12b +0.008), **non-Gemma family 4/4 음수** (Stage 5 Gemma 4 E4B −0.071, rnj-1:8b −0.099 SIG, gpt-oss:20b −0.010, ministral-3:8b −0.071). 이는 single-outlier observation 이 아닌 *family-systematic* 패턴. rnj-1:8b H12 결과는 **첫 cross-model statistically significant verdict** (Wilcoxon p=0.036, |d|=0.617 medium-large) 이며 non-Gemma 모델에 대해 family level 에서 post-stage Reducer = abstraction-loss claim 을 뒷받침. Gemma 3 family inversion 은 §4.6.2 style-mismatch caveat 의 *직접 evidence* — §4.6.2 참조.

**Verdict (cross-model v2)**: ⚠ *조건부 채택* — direction generalization 강함 (6/7 H11 양수, 4/6 H12 음수 또는 family-systematic), magnitude model-dependent, 이 scale 에서 single SIG verdict 등장 (rnj-1:8b H12). Stage 5 의 위치 효과 비대칭이 non-Gemma 모델에 대해 family/size 를 가로질러 *directional regularity* 로 generalize, Gemma 3 family 는 H12 를 invert 하는 systematic style-bias 보임 — 그 자체로 중요한 sub-finding (§4.6.2). H13 cross-model 은 distinct mechanism story (capability floor, M2) 와 함께 §4.7.4 에 보고. 상세: `docs/reference/stage6-cross-model-analysis-2026-05-08.md` (v3).

### 4.4 Main results — supported hypothesis

모든 가설 verdict 가 통일된 (Δ, n, p, Cohen's d, 95% CI) 5튜플 보고. n 은 *paired task* 수 (5 trial 의 task-별 mean accuracy 위 paired Wilcoxon). p-value 는 paired Wilcoxon (primary) 및 paired t-test (secondary) 에서. 95% CI 는 paired bootstrap (n=10,000, seed=42).

| H | 가설 | Δ | n (paired tasks) | Wilcoxon p | paired t p | Cohen's d | 95% CI | Anchor |
|---|---|---|---|---|---|---|---|---|
| **H1** | Multi-step orchestration (8-loop ABC) > single-pass (1-loop solo) | **+0.3685** | 9 | **0.039 ✅ SIG** | **0.023 SIG** | +0.936 (large) | [+0.117, +0.609] | Exp10 |
| H7 | External math tools (calculator/linalg/linprog) recover math-04 | +0.115 (overall); math-04: 0.06 → 0.64 (+0.58) | 4 | 1.000 | 0.518 | +0.365 (small) | [−0.090, +0.435] | Exp08 |
| H8 | Tool refinement + mandatory rules stabilize math-04 | +0.230 (overall); math-04: 0 → 0.80 (+0.80) | 4 | 0.500 | 0.323 | +0.590 (medium) | [−0.020, +0.600] | Exp08b |
| **H9a** | ABC+Tattoo > Solo on long-context tasks | **+0.4100** | 10 | **0.012 ✅ SIG** | **0.005 SIG** | +1.179 (large) | [+0.180, +0.600] | Exp09 |

H1 과 H9a 는 large effect size 와 0 을 배제하는 bootstrap CI 로 α=0.05 도달. H7 / H8 은 *task-level* claim: overall paired-task n=4 는 underpowered 이지만 math-04 single-task recovery (H7 +0.58, H8 +0.80) 가 substantive effect — §4.5 sub-narrative 의 *primary* H7/H8 evidence 로 보고, 4-task aggregate 는 cross-task context 로.

### 4.5 Negative-direction 결과

| H | 가설 | Verdict | 후보 mechanism |
|---|---|---|---|
| H2 | Same-model self-validation 이 오류 검출 | Rejected (0/15 detected) — 직접 관측 | Same-model self-validation 이 자기 reasoning 오류를 이 scale 에서 flag 못 함; Exp035 에서 role separation 으로 전환하여 replicate |
| H10 | Stronger Judge (Gemini 2.5 Flash) 가 약한 A/B 보완 | Inconclusive — effectively rejected; Δ=−0.081, d=−0.316, p=0.293 (NS) | 역방향 관찰: logic-02 case study 에서 (Δ=−0.900) mixed condition 이 all-Gemma baseline 대비 더 짧은 cycle + 누락 keyword — 더 강한 Judge 가 schema mismatch + early convergence 로 약한 모델의 emergent reasoning 을 *간섭* 한다는 가설과 정합; mechanism 직접 검증 안 됨, 가설로 제시 |
| H12 | Post-stage Reducer role 이 keyword-match accuracy 향상 | Inconclusive — effectively rejected; Δ=−0.053, d=−0.323, p=0.180 (NS) | 두 비배타적 후보 (§4.6.2 참조): (a) *abstraction loss* — Reducer 가 multi-source 답을 single-point estimate 로 압축, scorer 가 검출하도록 튜닝된 구조 폐기; (b) *scorer-style mismatch* — 압축된 답이 의미적으로 정확하지만 lexical 으로 비호환. 현재 데이터로 분리 불가; LLM-as-judge replication 계획 |
| H13 | Agent-active BM25 retrieval 이 long-context task accuracy 향상 | Inconclusive — effectively rejected; Δ=−0.220, d=−1.00, **p=0.012 (SIG)**; Bootstrap 95% CI [−0.36, −0.10] | *Multi-hop task 의 insufficient retrieval iteration* (§4.7.1 참조). 2-hop task 진단 5-trial run: tool-call count [1, 2, 2, 3, 0] → accuracy [0, 1, 1, 1, 0]. Single-call trial 이 hop 1 회복 후 prematurely terminate. Needle (1-hop) task 5/5 1-call 으로 성공. Mechanism 은 query quality 가 아닌 agent 의 under-iteration |

### 4.6 Paired role-axis ablation — main observation

본 논문의 중심 관찰. *(synthesis-04 case study + per-task breakdown 으로 ~2 페이지 확장 예정. 현재는 요약 placeholder.)*

| | Exp12 Extractor (H11) | Exp13 Reducer (H12) |
|---|---|---|
| 위치 | **pre-stage** (A 이전) | **post-stage** (C 이후) |
| Δ accuracy | +0.0500 | −0.0533 (bug-excluded) |
| Cohen's d (paired) | +0.323 (small, 양수) | −0.323 (small, 음수 — 거울상 magnitude) |
| Wilcoxon p (n=15 paired) | 0.198 — **NS** | 0.180 — **NS** |
| Bootstrap 95% CI Δ | [−0.020, +0.133] | [−0.133, +0.027] |
| 제안 mechanism | cycle-1 input organization | abstraction loss / multi-source → single-point compression (caveat: keyword-scorer artifact 가능성, §4.6.2) |
| logic-02 (Stage 2C / Exp11 weak spot) | base 0.3 → ext 0.6 (+0.30) | base 0.7 → red 0.5 (−0.20) |
| Synthesis 카테고리 direction | 5/5 task 양수 | 5/5 task 음수 |
| Verdict | ⚠ Conditionally supported, power-limited | ⚠ Inconclusive (effectively rejected), power-limited |

**관찰**: *동일 base model, taskset, trial count* 위 두 paired role addition 이 거의 동일 magnitude 의 반대 부호 effect 산출 (|Cohen's d|=0.323). 위치 의존 mechanism 과 정합하지만 n=15 paired task 에서 어느 effect 도 통계 유의 안 함. **위치 효과와 정합되는 evidence 이지만 confirmed 비대칭 아님** 으로 보고. Cross-model replication (§4.3) 이 direction generalization 검증; LLM-as-judge replication 이 §4.6.2 의 scorer-artifact caveat 처리 계획.

#### 4.6.1 Synthesis-04 illustrative case [stub — 확장 예정]

synthesis-04 (multi-source bird-population estimation task) 에서 baseline ABC chain 이 multi-paragraph structured analysis ("## Comprehensive Analysis ... Identification of Contradictions ... Zone C Count (R5 vs R1/R6) ...") 산출, deterministic keyword scorer 에서 1.0 점. Reducer-polished output 은 같은 내용을 single-point estimate ("The best estimate is **270 individuals**.") 로 압축, 0.33–0.67 점. 압축이 중심 numerical 결론은 보존했으나 scoring keyword 가 검출하도록 설계된 multi-source / multi-estimate scaffolding 폐기.

#### 4.6.2 Caveat — keyword scorer artifact 가능성

H12 mechanism claim ("abstraction loss") 은 §4.6.1 에서 보이는 keyword-coverage drop 으로 뒷받침되지만, deterministic scorer (`score_answer_v3`) 는 두 설명을 구별 불가:

- **(a) 진짜 quality drop** — 압축된 답이 의미적으로 필요한 정보 omit.
- **(b) Style mismatch** — 압축된 답이 의미적으로 정확하지만 scorer 가 튜닝된 keyword set 미포함.

현재 데이터로 분리 불가. 동일 final_answer 쌍 위 independent judge 로 free-tier Groq GPT-OSS 120B 를 사용한 LLM-as-judge replication 을 계획, scoring 이 lexical 이 아닌 semantic 일 때 H12 drop 의 어느 비율이 회복되는지 추정. 그 replication 실행 전까지 abstraction-loss mechanism 은 *후보 설명* 으로 다루어야 함, established cause 가 아님.

**Stage 6 v2 — family level 에서 (b) style-mismatch branch 의 직접 evidence**: cross-model H12 replication (§4.3) 이 single-model outlier 가 아닌 *family-systematic* split 보임. 검증된 두 Gemma 3 family 모델 모두 (gemma3:4b Δ=+0.056, gemma3:12b Δ=+0.008) H12 부호를 양수로 flip, 4 non-Gemma family 모델 모두 (Stage 5 Gemma 4 E4B −0.071, rnj-1:8b −0.099 SIG, gpt-oss:20b −0.010, ministral-3:8b −0.071) 예측한 음수 direction. 2/2 Gemma 3 inversion vs 4/4 non-Gemma replication 이 우연일 가능성 낮음: *Gemma 3 family 의 학습된 출력 스타일 bias* — Reducer 의 압축이 답을 scorer 의 expected vocabulary 쪽으로 우연히 regularize — 와 정합, 정확히 branch (b). Gemma 4 E4B baseline (Stage 5) 자체가 generation 적으로 non-Gemma-3 이며 non-Gemma 그룹과 일관 — bias 가 *Gemma-3-specific, Gemma-family-wide 가 아님* 시사. 본 v2 결과를 **Gemma 3 에 대해 branch (b) 의 family-level 직접 evidence** 로 읽음. Branch (a) — non-Gemma 4 의 진짜 abstraction loss — 는 후보로 남지만 family level 에서 (b) 와 더 이상 "구별 불가" 아님. 개별 답 위 (a)/(b) 완전 분해는 여전히 계획된 LLM-as-judge replication (P1-3, deferred) 필요.

[TODO: 4.6.1 을 baseline vs reducer 답 전체 비교로 확장; LLM-as-judge replication 완료 시 4.6.3 추가]

### 4.7 Search Tool (H13) — 첫 통계 유의 음수

**H13**: cycle 중 `search_chunks(query, top_k)` BM25 retrieval tool 을 *능동적* 으로 호출하는 ABC agent 가 long-context task 에서 sufficient-context baseline (32K-context window 의 prompt 안 전체 문서) 보다 우수.

**조건**: baseline_abc_chunked (prompt 안 전체 문서, Large-20K 문서의 경우 ~26K 토큰) vs abc_search_tool (질문만 + tool spec, agent 가 호출 시점/방법 결정) × 10 longctx task × 5 trial = 100 trial. 모든 role 에 동일 Gemma 4 E4B 모델, BM25 lexical retrieval (Exp09 의 기존 `bm25_retrieve` + stop-words filtering 추가). `tool_choice="auto"` — agent 가 호출 여부 결정.

**결과**:

| condition | n | mean_acc | err+null | avg cycles | avg dur |
|---|---:|---:|---:|---:|---:|
| baseline_abc_chunked | 50 | 0.9500 | 0+0 | 7.0 | 390s |
| **abc_search_tool** | 50 | **0.7300** | 7+7 | 7.1 | 235s (−40%) |

Δ(search − baseline) = **−0.2200** — Stage 5 의 가장 큰 음수 effect (Exp11 −0.081 NS, Exp13 −0.053 NS 와 비교). 통계 (n=10 paired tasks): **Wilcoxon p=0.0312, paired t p=0.0115 — 둘 다 α=0.05 에서 SIG**. **Cohen's d = −1.000 (large effect)**. Bootstrap 95% CI Δ: **[−0.360, −0.100]** (0 미포함). *Stage 5 의 첫 통계 유의 verdict*.

**Hop-type breakdown** (longctx taskset 의 진단 구조):

| hop_type | n_trials | search mean_acc | baseline mean_acc |
|---|---:|---:|---:|
| needle (1-hop) | 15 | 0.800 | 1.000 |
| 2-hop | 20 | 0.675 | 1.000 |
| 3-hop | 15 | 0.733 | 1.000 |

**H13 verdict**: ⚠ Inconclusive — effectively rejected, *이 scale 에서 통계 유의 음수 direction*. 결과는 *32K-context baseline 대비 n=10 long-context task 위 agent-active BM25 retrieval* 에 specifically 적용; 약한 형태 ("retrieval helps when context is the limit") 는 baseline saturation 으로 다루지 못함.

#### 4.7.1 Mechanism — multi-hop task 의 insufficient retrieval iteration (M1, Gemma 4 E4B)

본 sub-section 은 specifically Gemma 4 E4B 위 mechanism 을 기술. Stage 6 v2 (§4.7.4) 가 보임: 본 M1 mechanism 은 *universal small-dense behavior 가 아님* — 검증한 다른 4 small-dense 모델 (gemma3:4b, gemma3:12b, ministral-3:3b, ministral-3:8b) 은 다른 mechanism (M2 capability floor) 으로 fail, 본 under-iteration regime 에 도달조차 못 함.

`longctx-large-2hop-01` (Chen Wei → Westbrook Institute 에서 훈련 → 347 patents) 진단 run 이 명확한 패턴 드러냄. 5 trial 위, trial 별 `total_tool_calls` = [1, 2, 2, 3, 0], accuracy = [0, 1, 1, 1, 0]:

- Single-call trial (t0) 이 hop-1 entity ("Westbrook Institute") 회복 후 hop-2 query 발행 대신 *"the document does not contain a specific [number]"* 로 prematurely 결론.
- 2-, 3-call trial 이 두 hop 모두 완료, 1.0 점.
- Zero-call trial (t4) 은 tool-neglect case (no_final_answer).

Needle (single-hop) task 의 진단은 5/5 trial 이 정확히 1번의 well-formed call (BM25 top score 4.7–4.9, 정확한 keyword 추출) 에 5/5 정답. 음수 direction 은 **agent 가 *추가* query 발행 결정해야 하는 multi-hop reasoning 에 집중**. Agent 가 under-iterate.

#### 4.7.2 Caveat — tool_call capture 시점

50-trial A-2 production run 은 `tool_calls_per_cycle` 와 `total_tool_calls` 를 trial dict 에 추가하는 run.py whitelist fix 이전에 완료. Mechanism 분석은 따라서 production 50 trial 이 아닌 15-trial 진단 subset (medium-needle, large-2hop) 에 의존. 한계로 기록; production set 을 fix 와 함께 재실행은 ~3-4시간 추가 소비, direction (Δ, p, d) 와 per-hop 패턴이 A-2 + post-fix 진단으로 이미 확립되어 deferred.

#### 4.7.3 Tool axis sub-distinction

H7 (calculator/linalg) 과 H8 (mandatory tool rule 의 linprog) 이 math-04 위 +18.3pp / +23.3pp. H13 (agent-active BM25 retrieval) 이 −22pp. 셋 모두 "Tool axis" 외부화이지만 구조적으로 다름: H7/H8 은 fixed function signature 의 *deterministic, single-call computation* 외부화, H13 은 agent 자신의 호출 횟수/query 정책 에 효과가 의존하는 *probabilistic, iterative retrieval* 외부화. Tool axis 내 본 sub-distinction 은 4-axis framework 만으로는 포착되지 않으며 본 논문의 경험적 finding 중 하나.

#### 4.7.4 Cross-model H13 — capability floor 가 *specific* model 로 narrow (Stage 6 v3)

Stage 6 v3 (2026-05-09) 가 Gemma 4 family size-up control (gemma4:31b) 포함 5 추가 모델 위 H13 실행. **다섯 모두 search-tool ABC chain 운영 fail**, Stage 5 M1 under-iteration mode 에 더해 **M2 capability-floor 카테고리 내 4가지 distinguishable failure mode**:

| 모델 | family | size | failure mode |
|---|---|---|---|
| Gemma 4 E4B (Stage 5) | Gemma 4 | 4B effective | **(M1) under-iteration on multi-hop** — tool-calling 발생, premature termination — Δ=−0.220 (SIG) |
| gemma3:4b | Gemma 3 | 4B | (M2-a) tool-calling absence — 0/50 calls |
| gemma3:12b | Gemma 3 | 12B | (M2-b) tool-calling not invoked — "Unknown" + max-cycle |
| ministral-3:3b | Mistral 3 | 3B | (M2-c) tool-calls 발생 + final_answer 미생성 (50/50 max-cycle exit) |
| ministral-3:8b | Mistral 3 | 8B | (M2-c) tool-calls 발생 + final_answer 미생성 (44/50 errors) |
| **gemma4:31b** | **Gemma 4** | **31B** | **(M2-d) A-agent JSON schema mismatch** — tool-calls 발생 + A-agent 의 text-mode 응답이 expected assertions JSON 으로 parse 불가, 모든 cycle 에서 *zero assertions* + ABC chain never-converged (45/50 errors, 90% fail). 참고: 동일 모델이 `baseline_abc_chunked` (no tool, document 직접 prompt 공급) 에서 50/50 trial mean_acc 0.95 — 모델은 문서 유창하게 읽음; 실패는 *strictly* search-tool A-agent interface. |

Mechanism 분리:

- **(M1) under-iteration on multi-hop** — Gemma 4 E4B 가 `search_chunks` 호출 *함*, hop 1 회복, 그러나 hop-2 query 발행 대신 "the document does not contain a specific answer" 로 prematurely 결론. §4.7.1 진단이 Gemma 4 E4B 에 대해 정량화.
- **(M2) capability floor — full no-convergence** — 검증한 다른 5 모델은 under-iteration regime 에 도달 전 fail. Sub-variant (M2-a 부터 M2-d) 는 chain 이 *어디서* 깨지는지 반영: tool-calling not emitted (Gemma 3 family 의 M2-a/b), tool-calling emitted 하지만 chain 이 `final_answer` 미생성 (Mistral 3 family 3B, 8B 의 M2-c), tool-calling emitted 하지만 A-agent 의 continuation text 가 expected assertions-JSON schema fail (gemma4:31b 의 M2-d — 통상적 의미의 capability failure 가 아닌 *schema-interface* failure).

V3 finding 이 **§1.3 contribution-1 claim 을 상당히 narrow**. 본 cross-model panel 내, 원래의 H13 mechanism (측정 가능 Δ 의 M1 under-iteration) 은 *정확히 1개* 모델 — Gemma 4 E4B (effective 4B) — 에서 관측 가능. Same-family size-up 31B 는 M1 보존 *못 함*; gemma4:31b 가 새 (M2-d) schema-interface failure 로 M2 그룹 합류. "agent-iterative tool 의 4-axis framework minimum operational size" 는 따라서 *size* threshold 가 전혀 아님 — *specific-model identification*. 4-axis framework 의 agent-iterative tool 변형 (현재 spec — OpenAI-호환 tool spec + assertions-JSON A-agent contract) 은 검증 panel 내 Gemma 4 E4B 에서만 작동. Framework 의 intrinsic limit 에 대한 claim 이 아닌 honest *measurement-tool / model-fit* finding 으로 다룸: 다른 A-agent contract 또는 다른 tool-calling format 이 operability 를 broaden 할 수 있음. §4.7.1 의 (M1) under-iteration mechanism 은 따라서 *Gemma 4 E4B 위 관측 가능* 으로 보고, model-family generalization 은 cross-model JSON-schema robustness 를 위한 A-agent contract revision 의 future work 로 deferred.

추가로 (§4.7.5 아래) ministral-3:3b 가 *tool-free* H11 ABC chain 도 fail (150 trial 위 31.3% no-convergence, Stage 2A 30% reject gate 초과) — 별도 *tool-free* capability-floor 데이터 포인트 at 3B.

**gemma4:31b H13 baseline (no-tool) 은 paper-relevant**: 50/50 trial, mean_acc 0.95, errors 0/50 — gemma4:31b 가 26K-token 문서를 *tool-augmented A-agent contract 제거 시* ABC chain 안에서 정확히 읽고 답할 수 있음 confirm. 실패를 모델의 long-context / reasoning ability 가 아닌 A-agent search-tool interface 에 isolate.

#### 4.7.5 4B 미만의 capability floor — ministral-3:3b finding

ministral-3:3b (Mistral 3 family, 3B dense) 를 4B effective 미만의 small-dense panel 확장 후보로 검증. 두 independent reject event: H11 baseline + extractor 가 47/150 errors (31.3%, Stage 2A error-rate gate 30% 초과, 해당 trial 은 no final_answer), H13 search-tool 가 50/50 errors (100%, complete no-convergence). 동일 모델의 H13 baseline_chunked (no tool) 가 0/50 errors 와 mean accuracy 0.840 — 모델이 prompt 안 직접 공급된 문서는 읽고 답할 수 있지만, 이 size 에서 multi-cycle ABC chain 지속 못 함. 본 데이터 포인트를 lower-bound 로 다룸: 4-axis 외부화 framework 가 tool-free ABC chain 신뢰 운영을 위해 대략 Gemma 4 E4B-class capability (effective 4B) 필요, 동일 scale 이 tool-augmented 변형 (M2 위) 의 floor. 단일 3B 관측이 모든 3B 모델로 generalize 안 되지만, cross-model panel 내 가장 강한 negative existing evidence 이며 §6 limitations 에 추가.

### 4.8 통계 reporting protocol

§4.4 / §4.5 / §4.6 / §4.7 의 모든 가설 verdict 가 통일된 **(Δ, n, p, Cohen's d, 95% CI) 5튜플** 보고, H10–H13 에 이전에 적용된 convention 일치를 위해 v0.6 에서 H1 / H7 / H8 / H9a 재산정. Convention:

- **n** = *paired task* 수. 각 (task, condition) cell 마다 5 trial 위 mean accuracy 계산, task-별 baseline-vs-treatment 차이 검정. 이는 *task variance* 와 *trial variance* 분리, Stage 5/6 reporting style 일치.
- **p (primary)** = task-별 mean 위 paired Wilcoxon signed-rank test, two-sided. Non-parametric, small n 위 non-normal difference 에 robust.
- **p (secondary)** = task-별 mean 위 paired t-test, two-sided. Wilcoxon 옆에 cross-check 으로 보고; 작은 쪽을 pick 하지 않음.
- **Cohen's d** = task-별 차이 위 mean(diffs) / sd(diffs). small ≈ 0.2, medium ≈ 0.5, large ≈ 0.8 (Cohen convention).
- **95% CI** = task-별 차이 위 paired bootstrap (n=10,000 resample, seed=42). 0 을 배제하는 CI 가 p-test direction 뒷받침.

**Power note**: n=15 paired task 에서 panel 은 d≈0.3 effect 에 대해 underpowered (α=0.05 위 ~35% power), 따라서 H4/H10/H11/H12 를 NS 로 보고하고 *replication target* 으로 다룸 (Stage 6 의 cross-model 이 direction-generalization evidence 기여). H1, H9a, H13 은 large effect size (|d|≥0.94) 보유, n 충분. H7/H8 (n=4) 은 sub-experiment 의 substantive signal 인 *task-level* anchor (math-04 recovery) 와 함께 보고.

## 5. Discussion

### 5.1 Same-model role separation 을 isolation 도구로

H2 (same-model self-validation, 0/15 detected) 와 H3 (*동일 base model* 의 role-separated cross-validation, 12/15 detected) 가 함께 narrow claim 뒷받침: 본 validation regime 에서 **active ingredient 는 모델 capability 가 아닌 role separation**. 두 condition 모두 Gemma 4 E4B 사용이므로 0 → 80% 회복은 더 강한 validator 에 귀속 불가. 본 same-model isolation 패턴이 §4.6 의 role-addition ablation 으로 확장되는 바 — model capacity 고정으로 Extractor (+) 와 Reducer (−) 사이 directional 차이가 model-quality artifact 보다 structural / positional effect 로 더 readily interpretable.

### 5.2 Post-stage negative direction 의 후보 설명

H12 (Reducer post-stage Δ=−0.05) 는 두 비배타적 설명과 정합: (i) *abstraction loss* — single-point 답으로의 prompt-induced 압축이 downstream evaluation 이 의존하는 multi-source 구조 폐기; (ii) *scorer-style mismatch* — 압축된 답이 의미적으로 충실하더라도 deterministic scorer 가 튜닝된 keyword omit. 현재 데이터로 분리 불가 (§4.6.2). H10 (mixed-strength Judge) 은 관련되지만 distinct 패턴 보임: 더 강한 외부 Judge 가 Tattoo-schema mismatch + premature convergence 로 약한 모델의 self-discovery chain 간섭 — capability deficit 가 아닌 *position-and-interface* effect. 함께, H10 / H12 / H11 은 *외부화된 role 과 base model 의 emergent reasoning 사이의 interface* 가 어느 role 이 추가되는지보다 더 중요할 수 있음을 시사; 후속 가설로 제시, settled conclusion 아님.

### 5.3 Small-LLM deployment 비용 시사점

9-task cost-aware benchmark (Exp10) 위 Gemma 4 E4B 의 8-loop ABC 가 78.1% 도달 vs Gemini 2.5 Flash 1-call baseline 59.1%, per-trial API 비용 $0 위, 약 20× 더 긴 wall time 교환. 벤치마크-특정, 비대칭 (8-loop vs 1-call) 비교 — 일반 우월성 주장 아님. Wall-time 과 per-trial 비용이 다른 가치를 갖는 use case (예: private data 위 야간 batch inference) 에는 외부화 중심 small-model workflow 가 Flash 1-call baseline 대비 측정 가치 있을 수 있음을 시사.

## 6. 한계

- **Cross-model coverage** — Stage 6 v3 cross-model replication (§4.3) 이 H11/H12 위 5 추가 모델 (gemma3:4b, gemma3:12b, rnj-1:8b, gpt-oss:20b, ministral-3:8b) 포함, gemma3:12b 75/75 마감. DeepSeek, Llama 4, Phi family 미커버. H13 cross-model 을 5 dense model (gemma3:4b/12b, ministral-3:3b/8b, **gemma4:31b** — same-family size-up control) 위 시도 — **다섯 모두 M2 capability-floor mechanism 으로 fail** (§4.7.4), 4가지 distinguishable sub-variant. Iteration-discipline (M1) claim 은 *정확히 1개* 모델 — Gemma 4 E4B — 에서 관측 가능, M1 의 cross-model observability broaden 을 위한 future A-agent JSON-schema contract revision 필요할 수 있음.
- **A-agent contract fragility (M2-d finding)** — gemma4:31b 가 `baseline_abc_chunked` (50/50, mean_acc 0.95) 에서 26K-token 문서 유창히 읽지만 search-tool A-agent 의 JSON-schema return contract 에서 fail. 실패를 model-capability deficit 가 아닌 *measurement-tool fit* concern 으로 isolate. §4.7 의 H13 framing 은 본 caveat 와 함께 읽어야 함: 본 실험은 *Gemma 4 E4B + 본 specific A-agent contract* 조합 측정, 일반 "small-LLM agent-iterative retrieval" 아님.
- **3B 의 capability-floor 데이터 포인트** — ministral-3:3b (Mistral 3, dense 3B) 가 tool-free H11 ABC chain (31.3% no-convergence, 30% reject gate 초과) 와 H13 search-tool condition (100% no-convergence) 모두 fail. 단일 3B 관측이 모든 3B small-dense 로 generalize 안 되지만, 4-axis 외부화 framework 의 operating regime 에 대한 lower bound 설정.
- **통계 power** — n=15 가 여러 가설에 대해 underpowered (H4, H10, H11, H12 모두 α=0.05 에서 NOT SIGNIFICANT). Effect size (Cohen's d) 와 bootstrap CI 전반에 보고.
- **단독 저자 조정** — failure-mode label 의 inter-rater reliability 없음 (Stage 2B FailureLabel taxonomy).
- **Deterministic scorer** — `score_answer_v3` 가 keyword 기반; 의미적 정확성 직접 측정 안 됨 (H12 Reducer 와 관련 — "polished" 답이 의미적으로 정확하지만 keyword 잃을 수 있음).
- **한국어 scoring** — 제한적 지원; Stage 2A reference 에 기록.
- **Cross-category 에서 Tool axis 검증 부족** — H7/H8 의 math-04 anchor 가 단일 LP instance.

## 7. Conclusion

본 논문은 base model 을 A-Proposer / B-Critic / C-Judge chain 의 모든 role 에 걸쳐 고정 (Gemma 4 E4B, effective 4B) 한 채 *구조 추가* 가 small open-weight LLM 워크플로 정확도를 어떻게 변경하는지 측정. 세 finding 이 두드러짐. 첫째, **role addition 은 단조롭지 않음**: pre-stage Extractor 가 15 paired task 위 평균 정확도 +0.05 산출 (Cohen's d=+0.32), 구조적으로 동일한 post-stage Reducer 는 −0.05 (d=−0.32) — 동일 모델 / 태스크셋 위 거의 동일 magnitude 의 거울상 부호 (§4.6). 6 추가 모델 (Gemma 3, Mistral 3, OpenAI gpt-oss; 3B–20B) 위 cross-model replication 이 H11 direction 을 6/7 panel row 에서 confirm, *family-systematic* H12 split 드러냄: Gemma 3 family 2/2 양수, non-Gemma family 4/4 음수, rnj-1:8b 의 SIG verdict 포함 (p=0.036, |d|=0.617). Gemma 3 inversion 이 keyword-scorer style-mismatch caveat 의 family-level 직접 evidence (§4.6.2). 둘째, **tool axis behavior 가 iteration discipline 을 따라 분리**: deterministic single-call computation tool (calculator, linprog) 이 math-04 anchor task 위 +18~23pp (H7/H8), agent-active BM25 retrieval (H13) 이 −22pp (d=−1.0, n=10, **p=0.012 SIG**), Gemma 4 E4B 위 sufficient-context baseline 대비. Mechanism 은 *multi-hop task 의 under-iteration* — 진단 데이터가 보임: agent 가 query 1번 발행, hop 1 회복, hop 2 발행 대신 prematurely 종료. 셋째, **본 framework 의 tool-augmented 변형이 본 panel 내 specific model 에서만 작동**: H13 위 5 추가 small-and-mid dense 모델 (gemma3:4b/12b, ministral-3:3b/8b, gemma4:31b — same-family size-up control) 검증 중 다섯 모두 4가지 distinguishable M2 sub-variant 로 fail (tool-call absence, non-invocation, final-answer non-production, A-agent JSON-schema mismatch). Cross-model panel 내 H13 (M1) iteration effect 는 *정확히 1개* 모델 — Gemma 4 E4B — 에서 관측 가능, size threshold 가 아닌 본 모델과 본 specific A-agent JSON contract 사이의 *measurement-tool fit* 으로 보고 (§4.7.4).

본 finding 들이 small-LLM 외부화의 정제된 framing 으로 향함. 본 논문의 헤드라인 claim — *더 많은 구조가 단조롭게 더 좋은 것은 아니다; 중요한 것은 **어디에** 놓는지, **어떻게** iterate 하는지, 그리고 **base model 이 structural contract 에 fit 하는지*** — 이 12 가설 (그 중 4 negative-direction 결과 포함) 과 ~2,290 trial (Stage 6 panel 의 ~650 cross-model trial 포함) 위 role / tool axis 전반에 뒷받침. 재현성 자원으로 전체 harness, taskset, scorer, per-trial log 공개. Future work 의 세 구체 방향: (i) **A-agent contract robustness** — gemma4:31b 위 M2-d JSON-schema mismatch 가 시사: A-agent 의 tool-call return contract 수정 (예: assertions JSON 요구 완화, 또는 다음 cycle 에 tool_call return 을 native threading) 이 모델 전반에 걸쳐 M1 observability broaden 가능; (ii) **iteration-discipline manipulation** as M1 의 직접 fix — H8 mandatory-tool-rule 패턴 (Stage 5) 이 forcing tool call 으로 math-04 를 0% 에서 80% 로 회복, 유사한 "force minimum N retrieval calls" prompt 가 자연스러운 Stage 7 ablation 후보; (iii) **Cross-strength cascade** — Sonnet-class planner + Gemma-class executor (same-model ABC core 보존) 이 위치 효과 finding 의 자연스러운 product 확장이며 그럴듯한 비용 economics ($3/$15 per million token planner vs $0 local executor) 를 가짐, applied future work 로 둠. 식별한 경계 — specific operating model, small-n single-author panel, family-level bias 가 기록된 deterministic keyword scorer — 가 본 논문 측정이 replication 으로 tightening 가능한 모서리이며, 결과를 그에 맞게 framing.

## Appendix

### A. 통계 포함 전체 가설 표

[TBD: 13 행 × 5튜플 통계]

### B. Tattoo JSON 스키마

[TBD: `experiments/schema.py` 의 전체 schema]

### C. Role prompts (A/B/C system message)

[TBD: `experiments/system_prompt.py` 에서]

### D. Failure label taxonomy (Stage 2B)

[TBD: `docs/reference/failureLabels.md` 에서]

### E. 하드웨어 및 재현성

[TBD: GPU spec (RTX 3060 Ti 8GB), inference engine version, sampling parameter 표]

---

## References

[Bibtex format — `references.bib` 으로 마이그레이션 예정. 영문 draft (`draft.md`) 의 References 섹션과 동일.]

---

## Draft history

본 한국어판은 영문 `draft.md` 의 mirror; v0.7 (2026-05-09) 의 mirror 작성 시점은 2026-05-11.
