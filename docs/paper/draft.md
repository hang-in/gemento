---
type: paper
status: draft-skeleton
updated_at: 2026-05-05
target: arXiv preprint (single target — venue submission deferred)
canonical: true
revision: v0.2 (2026-05-05) — tone-down + contribution reorder per GPT review + Architect evaluation. See docs/reference/paper-review-action-items-2026-05-05.md.
---

# Role Addition Is Not Monotonic: Position Effects in Small-LLM Workflow Externalization

*Single-author preprint draft. arXiv: TBD. Quality bar: venue-equivalent (self-imposed peer review).*

---

> **DRAFT v0.2 — skeleton with tone adjustments.** Sections marked `[TBD]` await Exp14 verdict (Search Tool, in progress) and cross-model replication (planned via Groq free tier + Local Qwen 2.5 7B Q4_K_M). Statistics in `[stats: pending]` markers will be regenerated with consistent (Δ, n, p, Cohen's d, 95% CI) 5-tuple.

## Abstract

> [TBD — finalize after Exp14 + cross-model results, ~200 words]

Skeleton: Small open-weight LLMs (≤7B params) struggle on multi-step reasoning where larger frontier models excel. A common response is to externalize cognitive functions — working memory, computation, validation, and control flow — into the workflow rather than expand model capacity. We ask a narrower question: when extra Roles are added to such a workflow, does *where* they are inserted matter? Using a single 4B-effective open-weight model (Gemma 4 E4B) across 13 sequentially numbered hypotheses (H1–H13) over 540+ trials, we report three observations. (1) On a 9-task cost-aware benchmark, 8-loop ABC orchestration with the same base model scores 78.1% versus 41.3% for 1-loop solo, outperforming a one-call Gemini 2.5 Flash baseline (59.1%) at the cost of roughly 20× wall time — a benchmark-specific result, not a general superiority claim. (2) Same-model self-validation detects 0/15 planted errors, but role-separated cross-validation (A-Proposer / B-Critic / C-Judge with the same base model) recovers to 80% — isolating role separation, not model capability, as the active ingredient. (3) A paired role-axis ablation produces *mirrored directional effects at similar magnitude*: pre-stage Extractor Δ=+0.05 (Cohen's d=+0.32, p=0.198), post-stage Reducer Δ=−0.05 (d=−0.32, p=0.180); both are not statistically significant at n=15 paired tasks and are reported as a replication target. Cross-model replication on Llama 3.1 8B and Qwen 2.5 7B is planned to test whether this direction generalizes beyond Gemma 4 E4B. We release a reproducible harness covering 13 hypotheses including three negative results (self-validation, mixed-strength Judge, post-stage Reducer).

## 1. Introduction

### 1.1 The small-LLM gap on multi-step reasoning

[TODO: motivation paragraph — small open-weight models on complex reasoning. Cite frontier-model performance differential.]

### 1.2 Externalization vs parameter scaling

The dominant narrative in 2024–2026 has been parameter scaling — Llama 3.3 70B, Qwen 3 235B, GPT-OSS 120B — with proportional inference-time cost. We investigate the orthogonal axis: holding model capacity fixed (Gemma 4 E4B, effective 4B params) and externalizing four cognitive functions into the workflow.

### 1.3 Three contributions

This is positioned as a *measurement / ablation paper*, not a framework proposal — externalization frameworks already exist (Zhou et al., 2026; StateFlow; Chain-of-Agents). What is new is **what we measured** and **how we isolated it**.

1. **Position-effect ablation in role-axis addition (single best claim)**: a paired same-model ablation produces mirrored directional effects of nearly identical magnitude — pre-stage Extractor Δ=+0.05 (Cohen's d=+0.32) vs post-stage Reducer Δ=−0.05 (d=−0.32). Both are not statistically significant at n=15 and are reported as a replication target; the proposed mechanism for the negative direction is *abstraction loss* during post-stage compression, with the explicit caveat that the current keyword scorer cannot fully separate this from style mismatch. Empirical / mechanism contribution.
2. **Same-model isolation protocol for measuring structural workflow effects**: by holding the base model constant (Gemma 4 E4B) across A-Proposer / B-Critic / C-Judge / Extractor / Reducer, we isolate the *structural* effect of role separation and role placement from the model-quality confound that contaminates most multi-agent comparisons. Methodology contribution.
3. **A reproducible small-LLM externalization harness with negative results**: 13 sequentially numbered hypotheses (H1–H13) with verdict / evidence / open-source data, including three negative-direction results (H2 self-validation 0/15; H10 mixed-strength Judge underperforms; H12 post-stage Reducer underperforms). Resource / reproducibility contribution.

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

### 4.3 Cross-model held-out [TBD — Stage 6]

[TBD: replication of H1, H7, H8, H9a, H11, H12 on Llama 3.1 8B (Groq free) and Qwen 2.5 7B Q4_K_M (local). Optional: Llama 3.3 70B (Groq, ceiling check).]

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

[TODO: expand 4.6.1 with full baseline vs reducer answer comparison; add 4.6.3 once LLM-as-judge replication completes]

### 4.7 Search Tool (H13) — [TBD, Exp14 in progress]

[TBD: A-1 (baseline_abc_chunked, n=50) shows mean_acc=0.95 (saturation at 32K context). A-2 (abc_search_tool, n=50) running. Verdict + analysis after Exp14 task-05.]

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

- **Single base model** (Gemma 4 E4B) — partially mitigated by §4.3 cross-model [TBD].
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
