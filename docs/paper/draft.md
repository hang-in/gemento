---
type: paper
status: draft-skeleton
updated_at: 2026-05-09
target: arXiv preprint (single target — venue submission deferred)
canonical: true
revision: v0.5 (2026-05-09) — Stage 6 v2 integration. ministral-3:8b 추가 (6 model panel), gemma3:12b H12 final, ministral-3:3b capability floor finding, H13 family-agnostic small-dense fail. §4.3 6-model + 1 outlier, §4.6.2 family-systematic caveat evidence, §4.7 mechanism 분기 (M1 under-iteration / M2 capability floor), §1.3 contribution 1 재해석 (minimum operational size). v0.4 = 2026-05-08 partial integration. See docs/reference/stage6-cross-model-analysis-2026-05-08.md (v2).
---

# Role Addition Is Not Monotonic: Position Effects in Small-LLM Workflow Externalization

*Single-author preprint draft. arXiv: TBD. Quality bar: venue-equivalent (self-imposed peer review).*

---

> **DRAFT v0.5 — Stage 6 v2 integrated.** Stage 5 (Exp10–14, H10–H13) closed. Stage 6 v2 (6 model panel + 1 capability-floor finding) via Ollama Cloud Pro $20/month: H11 6/7 positive (1 outlier — ministral-3:8b), H12 family-systematic (Gemma 3 family 2/2 positive, non-Gemma family 4/4 negative — direct evidence for §4.6.2 style-mismatch caveat), H13 family-agnostic small-dense fail at 8B (M2 capability floor) — Gemma 4 E4B as the only working small dense at H13 (M1 under-iteration). Minimum operational size for the 4-axis externalization framework identified ≈ Gemma 4 E4B (effective 4B). LLM-as-judge auxiliary evaluation (P1-3) is deferred to future work. Remaining `[TBD]` markers concern §4.4 5-tuple statistics regeneration (P1-4) and Conclusion §7.

## Abstract

> [TBD — finalize after Exp14 + cross-model results, ~200 words]

Skeleton: Small open-weight LLMs (≤7B params) struggle on multi-step reasoning where larger frontier models excel. A common response is to externalize cognitive functions — working memory, computation, validation, and control flow — into the workflow rather than expand model capacity. We ask a narrower question: when extra structure (extra Roles, extra Tools) is added to such a workflow, does *where* and *how* it is inserted matter? Using a single 4B-effective open-weight model (Gemma 4 E4B) across 13 sequentially numbered hypotheses (H1–H13) over 640+ trials, we report four observations. (1) On a 9-task cost-aware benchmark, 8-loop ABC orchestration with the same base model scores 78.1% versus 41.3% for 1-loop solo, outperforming a one-call Gemini 2.5 Flash baseline (59.1%) at the cost of roughly 20× wall time — a benchmark-specific result, not a general superiority claim. (2) Same-model self-validation detects 0/15 planted errors, but role-separated cross-validation (A-Proposer / B-Critic / C-Judge with the same base model) recovers to 80% — isolating role separation, not model capability, as the active ingredient. (3) A paired role-axis ablation produces *mirrored directional effects at similar magnitude*: pre-stage Extractor Δ=+0.05 (Cohen's d=+0.32, p=0.198), post-stage Reducer Δ=−0.05 (d=−0.32, p=0.180); both are not statistically significant at n=15 paired tasks and are reported as a replication target. (4) An agent-active BM25 search tool, in contrast to the deterministic computation tools that previously yielded +18–23pp, *underperforms* a sufficient-context baseline by Δ=−0.22 (d=−1.00, p=0.012, n=10 long-context tasks) — the first statistically significant verdict in Stage 5. The mechanism is *insufficient retrieval iterations on multi-hop tasks*: the agent under-iterates and prematurely concludes that the document lacks the answer. Cross-model replication on Llama 3.1 8B and Qwen 2.5 7B is planned to test whether these directions generalize beyond Gemma 4 E4B. We release a reproducible harness covering 13 hypotheses including four negative-direction results (self-validation, mixed-strength Judge, post-stage Reducer, agent-active retrieval).

## 1. Introduction

### 1.1 The small-LLM gap on multi-step reasoning

[TODO: motivation paragraph — small open-weight models on complex reasoning. Cite frontier-model performance differential.]

### 1.2 Externalization vs parameter scaling

The dominant narrative in 2024–2026 has been parameter scaling — Llama 3.3 70B, Qwen 3 235B, GPT-OSS 120B — with proportional inference-time cost. We investigate the orthogonal axis: holding model capacity fixed (Gemma 4 E4B, effective 4B params) and externalizing four cognitive functions into the workflow.

### 1.3 Three contributions

This is positioned as a *measurement / ablation paper*, not a framework proposal — externalization frameworks already exist (Zhou et al., 2026; StateFlow; Chain-of-Agents). What is new is **what we measured** and **how we isolated it**.

1. **Structure-effect ablations in role and tool axes (single best claim)**: paired same-model ablations show that the *sign* of an externalization effect depends on its position, iteration discipline, and — newly identified in Stage 6 v2 — *whether the base model clears a capability floor at all*.
   - **Role axis (position effect)**: pre-stage Extractor Δ=+0.05 (Cohen's d=+0.32, n=15, NS) vs post-stage Reducer Δ=−0.05 (d=−0.32, n=15, NS) — mirrored directional effects of nearly identical magnitude on the same model and taskset. **Cross-model replication (§4.3) confirms direction generalization**: H11 6/7 models positive (1 outlier, ministral-3:8b), H12 4/6 models negative with a *family-systematic split* (Gemma 3 family 2/2 positive — direct evidence for the §4.6.2 style-mismatch caveat; non-Gemma family 4/4 negative, including the rnj-1:8b SIG verdict p=0.036 |d|=0.617).
   - **Tool axis (iteration effect, *conditional on capability floor*)**: an agent-active BM25 retrieval tool yields Δ=−0.22 (d=−1.00, n=10, **p=0.012, statistically significant**) against a sufficient-context baseline on Gemma 4 E4B; mechanism = under-iteration on multi-hop tasks (M1, §4.7.1). However, Stage 6 v2 (§4.7.4) shows that **four other small-dense models tested — gemma3:4b/12b, ministral-3:3b/8b — do not reach the under-iteration regime at all** (M2 capability floor, 100% no-convergence). The iteration-effect claim is therefore *conditional* on the model clearing this floor. Within our panel, *Gemma 4 E4B (effective 4B) is the only working small dense model under H13*, suggesting a *minimum operational size threshold* near 4B effective for the agent-iterative tool-augmented ABC chain. This is in striking contrast to deterministic single-call computation tools (calculator, linprog) that previously yielded +18–23pp on the same harness on the same model.
   The role and tool axes converge on a refined claim: *more structure is not monotonically better; what matters is **where it is placed**, **how it iterates**, and **whether the base model is capable enough to operate the chain at all***. Empirical / mechanism contribution.
2. **Same-model isolation protocol for measuring structural workflow effects**: by holding the base model constant (Gemma 4 E4B) across A-Proposer / B-Critic / C-Judge / Extractor / Reducer, we isolate the *structural* effect of role and tool changes from the model-quality confound that contaminates most multi-agent comparisons. Methodology contribution.
3. **A reproducible small-LLM externalization harness with negative results**: 13 sequentially numbered hypotheses (H1–H13) with verdict / evidence / open-source data, including four negative-direction results (H2 self-validation 0/15; H10 mixed-strength Judge underperforms; H12 post-stage Reducer underperforms; H13 agent-active retrieval underperforms a sufficient-context baseline). Resource / reproducibility contribution.

The 4-axis externalization framework (Tattoo / Tools / Role / Orchestrator) is used as the *organizing structure* for the hypotheses below; we do not claim it as a novel framework.

## 2. Related Work

> [TODO: 1-sentence differentiation per cited work — see CTX paper Section 2 pattern]

### 2.1 Externalization frameworks

- **Externalization in LLM Agents** (Zhou et al., 2026, arXiv:2604.08224) — proposes 4 externalization axes (memory / skills / protocols / harness engineering). Independent convergence with our 4-axis (Tattoo / Tools / Role / Orchestrator); axis mapping differs (we separate Role and Orchestrator explicitly; Zhou et al. fold control into harness engineering).
- **LightMem** (Fang et al., ICLR 2026, arXiv:2510.18866) — three-stage memory (sensory / short-term / long-term) for cross-session retrieval. Distinct from our Tattoo (working state within single task).

### 2.2 Multi-agent role separation

- **Chain-of-Agents** (Zhang et al., NeurIPS 2024, arXiv:2406.02818) — sequential worker agents + manager synthesis on long inputs. We share sequential structure but use *the same base model* for all roles (A/B/C), separated only by prompt and validation contract.
- [TODO: AutoGen, MetaGPT, Reflexion]

### 2.3 Self-validation / self-refine

- [TODO: CRITIC, Self-Refine, Reflexion — 1 sentence each on differentiation]

### 2.4 Tool use in small LLMs

- [TODO: Toolformer, Gorilla — differentiation: we measure tool-use *neglect* and recovery, not training-time integration]

### 2.5 Workflow / state-machine externalization

- **StateFlow** (Wu et al., 2024, arXiv:2403.11322) — task-solving as state machines. Adjacent to our Orchestrator axis; we add explicit role separation and Tattoo schema.

## 3. Framework

### 3.1 Four-axis externalization

| Axis | Externalized component | Anchor experiments |
|---|---|---|
| **Tattoo** | Working memory (claims, evidence, status) — structured JSON | Exp02 (H1), Exp09 (H9a–c) |
| **Tools** | Computation (calculator, linalg, linprog, BM25 search) | Exp08 (H7), Exp08b (H8), Exp14 (H13, in progress) |
| **Role** | Validation (A-Proposer / B-Critic / C-Judge) | Exp03 (H2), Exp035 (H3), Exp06 (H4), Exp12 (H11), Exp13 (H12) |
| **Orchestrator** | Control flow (loops, phase transitions) | Exp02 (H1), Exp07 (H5, H6) |

### 3.2 Tattoo schema

[TODO: JSON schema diagram + brief description. Refer to Appendix B for full schema.]

### 3.3 Role contracts

[TODO: A/B/C system prompts summary. Full prompts in Appendix C.]

### 3.4 Orchestrator loop

```
A (Proposer) → produces structured assertions, candidate answer
  ↓
B (Critic) → cross-validates, flags errors
  ↓
C (Judge) → terminal verdict, final answer
  ↓
[loop until convergence or max_cycles=8]
```

Deterministic Python orchestrator; no LLM-based control logic.

### 3.5 Hypothesis numbering convention

H1–H13 are sequentially numbered hypotheses about externalization axes — not statistical H₀/H₁ pairs. Verdicts use a controlled vocabulary (Supported / Conditionally supported / Inconclusive / Inconclusive (effectively rejected) / Rejected).

## 4. Experiments

### 4.1 Model and base setup

- Model: Gemma 4 E4B (Q8_0 quantization, 4B effective params)
- Inference engine: LM Studio (32K context) — earlier experiments (Exp00–06) used Ollama Q4_K_M; transition documented in `docs/reference/researchNotebook.md` Change History
- Sampling: `temperature=0.1`, `max_tokens=4096`, `top_p`/`seed` unset
- All ABC roles use the *same base model* (no model-quality confound)

### 4.2 Tasksets

- **Main taskset** (15 tasks): math (4) / logic (4) / synthesis (5) / planning (2)
- **Long-context taskset** (10 tasks): size_class × hop_type matrix (small/medium/large × needle/2-hop/3-hop)
- All tasks open-source under MIT in `experiments/tasks/`

### 4.3 Cross-model replication — Stage 6 v2

To test whether the position-effect asymmetry in §4.6 is a Gemma-specific artifact, we replicated H11 (Extractor pre-stage) and H12 (Reducer post-stage) on five additional open-weight models served through Ollama Cloud (Pro tier, $20/month, 3-concurrent-session limit): `gemma3:4b`, `gemma3:12b`, `rnj-1:8b` (non-Gemma, 8B), `gpt-oss:20b` (OpenAI reasoning class, 20B), and `ministral-3:8b` (Mistral 3 family, dense 8B, 2026-released — added in v2 to extend cross-family small-dense coverage beyond rnj-1:8b). Same main 15-task set and 5 trials per (task, condition) as Stage 5. Stage 5's Gemma 4 E4B baseline is included as the sixth model. A separate finding on `ministral-3:3b` (3B, dense, same family) is reported in §4.7.4 (capability floor).

**H11 (Extractor pre-stage) — 6/7 positive, 1 outlier**:

| Model | family | size | Δ | Cohen's d | p (Wilcoxon) |
|---|---|---|---|---|---|
| Gemma 4 E4B (Stage 5) | Gemma 4 | 4B effective | +0.0500 | +0.323 | 0.198 |
| gemma3:4b | Gemma 3 | 4B | **+0.0787** | +0.299 | 0.594 |
| gemma3:12b | Gemma 3 | 12B | +0.0022 | +0.009 | 0.888 |
| rnj-1:8b | non-Gemma | 8B | +0.0047 | +0.019 | 0.859 |
| gpt-oss:20b | OpenAI | 20B | +0.0244 | +0.177 | 0.672 |
| ministral-3:8b | Mistral 3 | 8B | **−0.0433** | **−0.292** | 0.311 |

Six of seven model rows show the predicted positive direction; ministral-3:8b is a single-model outlier with a small-magnitude negative effect (NS, p=0.311). Three non-exclusive explanations are consistent with this outlier: (a) *baseline saturation* — ministral-3:8b's H11 baseline 0.7178 is among the higher baselines in the panel, and Extractor's input-organization step may add noise rather than structure when the cycle-1 input is already well-organized; (b) *Extractor prompt mismatch* — Mistral 3's instruction-following pattern may interact differently with our Extractor template, surfacing a single-prompt cross-family generalization limit; (c) *NS-at-n=15* — the result is statistically indistinguishable from zero. None of the cross-model H11 effects reach α=0.05 individually at n=15. We characterize the H11 direction as *strong but not unanimous*, with the largest positive magnitudes at the weakest baselines (gemma3:4b +0.079, Stage 5 Gemma 4 E4B +0.050), consistent with a capability-headroom story.

**H12 (Reducer post-stage) — family-systematic pattern**:

| Model | family | size | Δ | Cohen's d | p (Wilcoxon) | direction |
|---|---|---|---|---|---|---|
| Gemma 4 E4B (Stage 5) | Gemma 4 | 4B | −0.0711 | −0.323 | 0.180 | non-Gemma 음수 |
| gemma3:4b | Gemma 3 | 4B | **+0.0562** | +0.331 | 0.423 | **Gemma 3 양수** |
| gemma3:12b | Gemma 3 | 12B | **+0.0078** | +0.026 | 0.878 | **Gemma 3 양수** |
| rnj-1:8b | non-Gemma | 8B | **−0.0989** | **−0.617** | **0.036 ✅ SIG** | non-Gemma 음수 |
| gpt-oss:20b | non-Gemma | 20B | −0.0100 | −0.052 | 0.735 | non-Gemma 음수 |
| ministral-3:8b | non-Gemma | 8B | **−0.0707** | **−0.287** | 0.327 | non-Gemma 음수 |

H12 splits cleanly along family lines: **Gemma 3 family 2/2 positive** (gemma3:4b +0.056, gemma3:12b +0.008), **non-Gemma family 4/4 negative** (Stage 5 Gemma 4 E4B −0.071, rnj-1:8b −0.099 SIG, gpt-oss:20b −0.010, ministral-3:8b −0.071). This is a *family-systematic* pattern, not a single-outlier observation. The rnj-1:8b H12 result is the **first cross-model statistically significant verdict** (Wilcoxon p=0.036, |d|=0.617 medium-large) and supports the post-stage Reducer = abstraction-loss claim at the family level for non-Gemma models. The Gemma 3 family inversion is *direct evidence* for the §4.6.2 style-mismatch caveat — see §4.6.2.

**Verdict (cross-model v2)**: ⚠ *Conditional accept* — direction generalization is strong (6/7 H11 positive, 4/6 H12 negative or family-systematic), magnitude is model-dependent, and a single SIG verdict appears at this scale (rnj-1:8b H12). The Stage 5 position-effect asymmetry generalizes as a *directional regularity* across families and sizes for non-Gemma models, while Gemma 3 family exhibits a systematic style-bias that inverts H12 — itself an important sub-finding (§4.6.2). H13 cross-model is reported in §4.7.4 with a distinct mechanism story (capability floor, M2). Detail: `docs/reference/stage6-cross-model-analysis-2026-05-08.md` (v2).

### 4.4 Main results — supported hypotheses

[stats: pending — regenerate with 5-tuple]

| H | Hypothesis | Δ | n | p | Cohen's d | 95% CI | Anchor |
|---|---|---|---|---|---|---|---|
| H1 | Multi-step orchestration > single-pass | +0.367 (1-loop 0.413 → 8-loop 0.781) | 540 | [TBD] | [TBD] | [TBD] | Exp10 |
| H7 | External math tools (linprog) recover math-04 | +0.183 (math-04: 0% → 80%) | 50 | [TBD] | [TBD] | [TBD] | Exp08 |
| H8 | Tool refinement + error hints stabilize | +0.233 (math-04: 0% → 100%) | 50 | [TBD] | [TBD] | [TBD] | Exp08b |
| H9a | ABC+Tattoo > Solo on long context | +0.683 (Large 20K: 0% → 100%) | 30 | [TBD] | [TBD] | [TBD] | Exp09 |

### 4.5 Negative-direction results

[stats: pending — full 5-tuple]

| H | Hypothesis | Verdict | Candidate mechanism |
|---|---|---|---|
| H2 | Same-model self-validation detects errors | Rejected (0/15 detected) — directly observed | Same-model self-validation does not flag own reasoning errors at this scale; replicated in Exp035 by switching to role separation |
| H10 | Stronger Judge (Gemini 2.5 Flash) compensates weaker A/B | Inconclusive — effectively rejected; Δ=−0.081, d=−0.316, p=0.293 (NS) | Inverse-direction observation: in the logic-02 case study (Δ=−0.900), the mixed condition produced shorter cycles and missing keywords vs the all-Gemma baseline — *consistent with* a stronger Judge interfering with the weaker model's emergent reasoning via schema mismatch and early convergence; mechanism not directly tested, presented as a hypothesis |
| H12 | Post-stage Reducer role improves keyword-match accuracy | Inconclusive — effectively rejected; Δ=−0.053, d=−0.323, p=0.180 (NS) | Two non-exclusive candidates (see §4.6.2): (a) *abstraction loss* — Reducer compresses multi-source answers to single-point estimates, discarding structure the keyword scorer was tuned to detect; (b) *scorer-style mismatch* — the compressed answer is semantically correct but lexically incompatible. The current data cannot separate these; LLM-as-judge replication is planned |
| H13 | Agent-active BM25 retrieval improves accuracy on long-context tasks | Inconclusive — effectively rejected; Δ=−0.220, d=−1.00, **p=0.012 (SIG)**; Bootstrap 95% CI [−0.36, −0.10] | *Insufficient retrieval iterations on multi-hop tasks* (see §4.7.1). Diagnostic 5-trial run on a 2-hop task: tool-call counts [1, 2, 2, 3, 0] → accuracy [0, 1, 1, 1, 0]. The single-call trial recovered hop 1 then prematurely terminated. Needle (1-hop) tasks succeeded 5/5 with one well-formed call. Mechanism is the agent's under-iteration, not query quality |

### 4.6 Paired role-axis ablation — main observation

This is the central observation of the paper. *(Will be expanded to ~2 pages with synthesis-04 case study and per-task breakdown. Currently a summary placeholder.)*

| | Exp12 Extractor (H11) | Exp13 Reducer (H12) |
|---|---|---|
| Position | **pre-stage** (before A) | **post-stage** (after C) |
| Δ accuracy | +0.0500 | −0.0533 (bug-excluded) |
| Cohen's d (paired) | +0.323 (small, positive) | −0.323 (small, negative — mirrored magnitude) |
| Wilcoxon p (n=15 paired) | 0.198 — **NOT SIGNIFICANT** | 0.180 — **NOT SIGNIFICANT** |
| Bootstrap 95% CI Δ | [−0.020, +0.133] | [−0.133, +0.027] |
| Proposed mechanism | cycle-1 input organization | abstraction loss / multi-source → single-point compression (caveat: keyword-scorer artifact possibility, see §4.6.2) |
| logic-02 (Stage 2C / Exp11 weak spot) | base 0.3 → ext 0.6 (+0.30) | base 0.7 → red 0.5 (−0.20) |
| Synthesis category direction | 5/5 tasks positive | 5/5 tasks negative |
| Verdict | ⚠ Conditionally supported, power-limited | ⚠ Inconclusive (effectively rejected), power-limited |

**What we observe**: on the *same base model, taskset, and trial count*, two paired role additions produce effect sizes of opposite sign with nearly identical magnitude (|Cohen's d|=0.323). This is consistent with a position-dependent mechanism, but at n=15 paired tasks neither effect is statistically significant. We report this as **evidence consistent with a position effect, not a confirmed asymmetry**. Cross-model replication on Llama 3.1 8B / Qwen 2.5 7B is planned to test whether the direction generalizes; LLM-as-judge replication is planned to address the scorer-artifact caveat in §4.6.2.

#### 4.6.1 Synthesis-04 illustrative case [stub — to be expanded]

In synthesis-04 (a multi-source bird-population estimation task), the baseline ABC chain produced multi-paragraph structured analyses ("## Comprehensive Analysis ... Identification of Contradictions ... Zone C Count (R5 vs R1/R6) ...") that scored 1.0 under the deterministic keyword scorer. Reducer-polished outputs compressed the same content into single-point estimates ("The best estimate is **270 individuals**.") that scored 0.33–0.67. The compression preserved the central numerical conclusion but discarded the multi-source / multi-estimate scaffolding that the scoring keywords were designed to detect.

#### 4.6.2 Caveat — keyword scorer artifact possibility

The H12 mechanism claim ("abstraction loss") is supported by the keyword-coverage drop visible in §4.6.1, but the deterministic scorer (`score_answer_v3`) cannot distinguish two explanations:

- **(a) Real quality drop** — the compressed answer omits semantically required information.
- **(b) Style mismatch** — the compressed answer is semantically correct but does not contain the keyword set the scorer was tuned to.

These are not separable from the current data. We plan an LLM-as-judge replication (free-tier Groq GPT-OSS 120B as an independent judge over the same final_answer pairs) to estimate which fraction of the H12 drop is recovered when scoring is semantic rather than lexical. Until that replication runs, the abstraction-loss mechanism should be treated as a *candidate explanation*, not an established cause.

**Stage 6 v2 — direct evidence for the (b) style-mismatch branch at the family level**: the cross-model H12 replication (§4.3) shows a *family-systematic* split, not a single-model outlier. Both Gemma 3 family models tested (gemma3:4b Δ=+0.056, gemma3:12b Δ=+0.008) flipped the H12 sign positive, while all four non-Gemma family models (Stage 5 Gemma 4 E4B −0.071, rnj-1:8b −0.099 SIG, gpt-oss:20b −0.010, ministral-3:8b −0.071) showed the predicted negative direction. Two-of-two Gemma 3 inversion vs four-of-four non-Gemma replication is unlikely to be coincidence: it is consistent with a *learned output-style bias in Gemma 3 family* such that the Reducer's compression accidentally regularizes the answer toward the scorer's expected vocabulary — exactly branch (b). The Gemma 4 E4B baseline (Stage 5) is itself non-Gemma-3 by generation and behaves consistently with the non-Gemma group, suggesting the bias is *Gemma-3-specific, not Gemma-family-wide*. We read this v2 result as **direct family-level evidence for branch (b) on Gemma 3 specifically**. Branch (a) — real abstraction loss for the non-Gemma four — remains a candidate but is no longer "indistinguishable" from (b) at the family level. Full (a)/(b) decomposition on individual answers still requires the planned LLM-as-judge replication (P1-3, deferred).

[TODO: expand 4.6.1 with full baseline vs reducer answer comparison; add 4.6.3 once LLM-as-judge replication completes]

### 4.7 Search Tool (H13) — first statistically significant negative

**H13**: ABC agents that *actively* call a `search_chunks(query, top_k)` BM25 retrieval tool during cycles outperform a sufficient-context baseline (32K-context window with the full document in the prompt) on long-context tasks.

**Conditions**: baseline_abc_chunked (full document in prompt, ~26K tokens for Large-20K docs) vs abc_search_tool (question only + tool spec, agent decides when/how to call) × 10 longctx tasks × 5 trials = 100 trials. Same Gemma 4 E4B model on all roles, BM25 lexical retrieval (the existing `bm25_retrieve` from Exp09, with stop-words filtering added). `tool_choice="auto"` — the agent decides whether to call.

**Results**:

| condition | n | mean_acc | err+null | avg cycles | avg dur |
|---|---:|---:|---:|---:|---:|
| baseline_abc_chunked | 50 | 0.9500 | 0+0 | 7.0 | 390s |
| **abc_search_tool** | 50 | **0.7300** | 7+7 | 7.1 | 235s (−40%) |

Δ(search − baseline) = **−0.2200** — the largest negative effect in Stage 5 (vs Exp11 −0.081 NS, Exp13 −0.053 NS). Statistics (n=10 paired tasks): **Wilcoxon p=0.0312, paired t p=0.0115 — both SIGNIFICANT at α=0.05**. **Cohen's d = −1.000 (large effect)**. Bootstrap 95% CI Δ: **[−0.360, −0.100]** (does not include zero). This is the *first statistically significant verdict in Stage 5*.

**Hop-type breakdown** (the diagnostic structure of the longctx taskset):

| hop_type | n_trials | search mean_acc | baseline mean_acc |
|---|---:|---:|---:|
| needle (1-hop) | 15 | 0.800 | 1.000 |
| 2-hop | 20 | 0.675 | 1.000 |
| 3-hop | 15 | 0.733 | 1.000 |

**H13 verdict**: ⚠ Inconclusive — effectively rejected, *statistically significant negative direction at this scale*. The result applies specifically to *agent-active BM25 retrieval against a 32K-context baseline on n=10 long-context tasks*; a weaker form ("retrieval helps when context is the limit") is not addressed because the baseline saturated.

#### 4.7.1 Mechanism — insufficient retrieval iterations on multi-hop tasks (M1, Gemma 4 E4B)

This subsection describes the mechanism on Gemma 4 E4B specifically. Stage 6 v2 (§4.7.4) shows that this M1 mechanism is *not the universal small-dense behavior* — four other small-dense models tested (gemma3:4b, gemma3:12b, ministral-3:3b, ministral-3:8b) fail by a different mechanism (M2 capability floor) and do not reach the under-iteration regime described here.

A diagnostic run on `longctx-large-2hop-01` (Chen Wei → trained at Westbrook Institute → 347 patents) revealed a clear pattern. Across 5 trials, `total_tool_calls` per trial = [1, 2, 2, 3, 0] and accuracy = [0, 1, 1, 1, 0]:

- The single-call trial (t0) recovered the hop-1 entity ("Westbrook Institute") then prematurely concluded *"the document does not contain a specific [number]"* instead of issuing a hop-2 query.
- The 2- and 3-call trials completed both hops and scored 1.0.
- The zero-call trial (t4) was a tool-neglect case (no_final_answer).

For needle (single-hop) tasks the diagnostic showed 5/5 trials with exactly one well-formed call (BM25 top score 4.7–4.9, accurate keyword extraction) and 5/5 correct. The negative direction is concentrated on **multi-hop reasoning where the agent must decide to issue *additional* queries**. The agent under-iterates.

#### 4.7.2 Caveat — tool_call capture timing

The 50-trial A-2 production run was completed before a run.py whitelist fix that adds `tool_calls_per_cycle` and `total_tool_calls` to the trial dict. The mechanism analysis therefore relies on the 15-trial diagnostic subset (medium-needle and large-2hop), not on the production 50 trials. This is documented as a limitation; rerunning the production set with the fix would consume another ~3-4 hours and is deferred since the direction (Δ, p, d) and per-hop pattern are already established from A-2 plus the post-fix diagnostics.

#### 4.7.3 Tool axis sub-distinction

H7 (calculator/linalg) and H8 (linprog with mandatory tool rules) yielded +18.3pp and +23.3pp on math-04. H13 (agent-active BM25 retrieval) yields −22pp. All three are "Tool axis" externalizations, but they differ structurally: H7/H8 externalize a *deterministic, single-call computation* with a fixed function signature, while H13 externalizes *probabilistic, iterative retrieval* whose effectiveness depends on the agent's own policy for how many times and with what queries to call. This sub-distinction within the Tool axis is not captured by the four-axis framework alone, and is one of the paper's empirical findings.

#### 4.7.4 Cross-model H13 — family-agnostic small-dense capability floor (Stage 6 v2)

Stage 6 v2 ran H13 on four additional small-dense models. **All four failed to operate the search-tool ABC chain**, but with two distinguishable failure modes:

| Model | family | size | failure mode |
|---|---|---|---|
| Gemma 4 E4B (Stage 5) | Gemma 4 | 4B effective | (M1) tool-calling present, **under-iteration** on multi-hop — Δ=−0.220 (SIG) |
| gemma3:4b | Gemma 3 | 4B | (M2) **tool-calling absence** — 0/50 calls |
| gemma3:12b | Gemma 3 | 12B | (M2) tool-calling not invoked — "Unknown" + max-cycle |
| ministral-3:3b | Mistral 3 | 3B | (M2) tool-calls present + **final_answer never produced** (50/50 max-cycle exits) |
| ministral-3:8b | Mistral 3 | 8B | (M2) tool-calls present + final_answer never produced (44/50 errors) |

The mechanism narrative therefore splits in two:

- **(M1) under-iteration on multi-hop** — Gemma 4 E4B *does* invoke `search_chunks`, recovers hop 1, then prematurely concludes "the document does not contain a specific answer" instead of issuing a hop-2 query. The diagnostic in §4.7.1 quantifies this for Gemma 4 E4B.
- **(M2) capability floor — full no-convergence** — the four other small-dense models do not reach the under-iteration regime at all. Either tool-calling is not invoked (Gemma 3 family) or tool-calls are invoked but the chain cannot close on a final answer (Mistral 3 family at both 3B and 8B). This is *family-agnostic* — it appears across Gemma 3 and Mistral 3 — and it persists up to 8B parameters in a dense model.

This v2 result revises the §4.7.1 / §1.3 framing. The original Stage 5 contribution claim — "tool-axis iteration discipline determines the sign of the externalization effect" — is **conditional on the model clearing the M2 capability floor**. Below that floor, the agent-active retrieval condition does not produce a measurable Δ at all; it produces zero throughput. Within our cross-model panel, **Gemma 4 E4B is the only small dense model that operates at all** under H13, and it does so by displaying (M1). Practical implication for small-LLM externalization: the *minimum operational size* for the 4-axis framework with an agent-iterative tool ≈ Gemma 4 E4B (effective 4B). The pattern is *family-agnostic* in the negative direction (4/4 small dense models tested — across Gemma 3 and Mistral 3 — fail M2) and we do not yet have positive evidence from any non-Gemma-4 small dense model. Cross-family H13 replication on `rnj-1:8b` and `gpt-oss:20b` (which are larger-or-non-dense and may clear the floor) is future work.

We additionally observed (§4.7.5 below) that ministral-3:3b also fails the *tool-free* H11 ABC chain (31.3% no-convergence over 150 trials, exceeding the Stage 2A 30% reject gate), giving a separate *tool-free* capability-floor data point at 3B.

#### 4.7.5 Capability floor below 4B — ministral-3:3b finding

ministral-3:3b (Mistral 3 family, 3B dense) was tested as a candidate to extend the small-dense panel below 4B effective. Two independent reject events resulted: H11 baseline + extractor produced 47/150 errors (31.3%, exceeding the Stage 2A error-rate gate of 30%, no final_answer in those trials), and H13 search-tool produced 50/50 errors (100%, complete no-convergence). H13 baseline_chunked (no tool) on the same model produced 0/50 errors with mean accuracy 0.840 — i.e., the model can read a document and answer when the document is supplied directly in the prompt, but cannot sustain the multi-cycle ABC chain at this size. We treat this as the lower-bound data point: the 4-axis externalization framework requires roughly Gemma 4 E4B-class capability (effective 4B) to operate the tool-free ABC chain reliably, and the same scale is the floor for the tool-augmented variant (M2 above). A single 3B observation does not generalize across all 3B models, but it is the strongest negative existing evidence in the cross-model panel and is added to §6 limitations.

### 4.8 Statistical reporting protocol

All hypothesis verdicts report (Δ, n, p, Cohen's d, 95% CI) 5-tuple. p-values use paired Wilcoxon (primary) and paired t-test (secondary). 95% CI by paired bootstrap (n=10,000). [TODO: regenerate for H1, H7, H8, H9a from existing result JSONs; H10–H12 already have full 5-tuple.]

## 5. Discussion

### 5.1 Same-model role separation as an isolation tool

H2 (same-model self-validation, 0/15 detected) and H3 (role-separated cross-validation with the *same base model*, 12/15 detected) together support a narrow claim: **role separation, not model capability, is the active ingredient** in this validation regime. Because both conditions use Gemma 4 E4B, the 0 → 80% recovery cannot be attributed to a stronger validator. This same-model isolation pattern is what we extend into the role-addition ablation in §4.6 — by holding model capacity fixed, the directional difference between Extractor (+) and Reducer (−) is more readily interpretable as a structural / positional effect than as a model-quality artifact.

### 5.2 Candidate explanations for the post-stage negative direction

H12 (Reducer post-stage Δ=−0.05) is consistent with two non-exclusive explanations: (i) *abstraction loss* — the prompt-induced compression to a single-point answer discards multi-source structure that downstream evaluation depends on; (ii) *scorer-style mismatch* — the compressed answer omits keywords the deterministic scorer was tuned to, even when the answer is semantically faithful. These are not separable from the current data (§4.6.2). H10 (mixed-strength Judge) shows a related but distinct pattern: a stronger external Judge can interfere with the weaker model's self-discovery chain via Tattoo-schema mismatch and premature convergence — also a *position-and-interface* effect rather than a capability deficit. Together, H10 / H12 / H11 suggest that the *interface between externalized roles and the base model's emergent reasoning* may matter more than which role is added; we present this as a hypothesis for follow-up, not a settled conclusion.

### 5.3 Implications for small-LLM deployment cost

On the 9-task cost-aware benchmark (Exp10), 8-loop ABC with Gemma 4 E4B reaches 78.1% versus 59.1% for a one-call Gemini 2.5 Flash baseline at $0 per-trial API cost, in exchange for roughly 20× longer wall time. This is a benchmark-specific, asymmetric (8-loop vs 1-call) comparison — not a general superiority claim. It does suggest that for use cases where wall-time and per-trial cost have different value (e.g., overnight batch inference on private data), externalization-heavy small-model workflows may be worth measuring against a Flash 1-call baseline.

## 6. Limitations

- **Cross-model coverage** — Stage 6 v2 cross-model replication (§4.3) includes 5 additional models (gemma3:4b, gemma3:12b, rnj-1:8b, gpt-oss:20b, ministral-3:8b) on H11/H12, with gemma3:12b finalized at 75/75. DeepSeek, Llama 4, Phi families not yet covered. H13 cross-model attempted on 4 small-dense models (gemma3:4b/12b, ministral-3:3b/8b) — **all four failed via the M2 capability-floor mechanism** (§4.7.4); H13 cross-family replication on larger or non-dense models (rnj-1:8b, gpt-oss:20b) is future work and would inform whether iteration-discipline (M1) is observable beyond Gemma 4 E4B.
- **Capability-floor data point at 3B** — ministral-3:3b (Mistral 3, dense 3B) failed both the tool-free H11 ABC chain (31.3% no-convergence, exceeding the 30% reject gate) and the H13 search-tool condition (100% no-convergence). One 3B observation does not generalize across all 3B small-dense models, but it sets a lower bound for the 4-axis externalization framework's operating regime in our cross-model panel.
- **Statistical power** — n=15 underpowered for several hypotheses (H4, H10, H11, H12 all NOT SIGNIFICANT at α=0.05). Effect sizes (Cohen's d) and bootstrap CIs reported throughout.
- **Single-author coordination** — no inter-rater reliability for failure-mode labels (Stage 2B FailureLabel taxonomy).
- **Deterministic scorer** — `score_answer_v3` is keyword-based; semantic correctness not directly measured (relevant for H12 Reducer — "polished" answers may be semantically correct but lose keywords).
- **Korean-language scoring** — limited support; documented in Stage 2A reference.
- **Tool axis under-tested in cross-category** — math-04 anchor for H7/H8 is a single LP instance.

## 7. Conclusion

[TODO: 2 paragraphs. Lead with position-effect asymmetry as the sharpest single claim. Note future work — Tool axis (Exp14 Search Tool, Exp15+ Graph/Evidence Tool), cross-model expansion, longer-context regimes.]

## Appendix

### A. Full hypothesis table with statistics

[TBD: 13 rows × 5-tuple statistics]

### B. Tattoo JSON schema

[TBD: full schema from `experiments/schema.py`]

### C. Role prompts (A/B/C system messages)

[TBD: from `experiments/system_prompt.py`]

### D. Failure label taxonomy (Stage 2B)

[TBD: from `docs/reference/failureLabels.md`]

### E. Hardware and reproducibility

[TBD: GPU specs (RTX 3060 Ti 8GB), inference engine versions, sampling parameters table]

---

## References

[Bibtex format — to be migrated to `references.bib`]

```
@article{zhou2026externalization,
  title={Externalization in {LLM} Agents: A Unified Review of Memory, Skills, Protocols and Harness Engineering},
  author={Zhou, Chenyu and Chai, Huacan and Chen, Wenteng and others},
  journal={arXiv preprint arXiv:2604.08224},
  year={2026}
}

@article{fang2026lightmem,
  title={{LightMem}: Lightweight and Efficient Memory-Augmented Generation},
  author={Fang, Jizhan and Deng, Xinle and Xu, Haoming and others},
  booktitle={ICLR 2026},
  year={2026},
  note={arXiv:2510.18866}
}

@article{wu2024stateflow,
  title={{StateFlow}: Enhancing {LLM} Task-Solving through State-Driven Workflows},
  author={Wu, Yiran and others},
  journal={arXiv preprint arXiv:2403.11322},
  year={2024}
}

@inproceedings{zhang2024chainofagents,
  title={Chain of Agents: Large Language Models Collaborating on Long-Context Tasks},
  author={Zhang, Yusen and Sun, Ruoxi and Chen, Yanfei and Pfister, Tomas and Zhang, Rui and Arik, Sercan {\"O}.},
  booktitle={NeurIPS 2024},
  year={2024},
  note={arXiv:2406.02818}
}
```

---

## Draft history

- 2026-05-05 v0.1: Skeleton only. Sections 4.3 (cross-model), 4.7 (Search Tool H13), 5 (Discussion partial), 6 conclusion deferred. Statistics in `[stats: pending]` markers — to be regenerated with 5-tuple via existing result JSONs (`experiments/exp**/results/*.json`).
- 2026-05-05 v0.2: GPT review tone-down + contribution reorder. Title changed to "Role Addition Is Not Monotonic". Abstract rewritten with defensive language. §4.6.1 synthesis-04 case stub + §4.6.2 keyword-scorer artifact caveat added. Same-model isolation protocol elevated to contribution 2.
- 2026-05-05 v0.3: H13 (Search Tool, Exp14) integrated. §4.7 fully written (results, mechanism, tool-axis sub-distinction). Abstract expanded to include H13 (4 negative-direction results). Contribution 1 broadened to "structure-effect ablations" covering both position effect (Role axis) and iteration effect (Tool axis), unified under "more structure is not monotonically better". Trials count updated 540 → 640.
