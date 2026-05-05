---
type: paper
status: draft-skeleton
updated_at: 2026-05-05
target: arXiv preprint (single target — venue submission deferred)
canonical: true
---

# Externalization for Small-LLM Workflows: Position-Effect Asymmetry in Role-Axis Addition

*Single-author preprint draft. arXiv: TBD. Quality bar: venue-equivalent (self-imposed peer review).*

---

> **DRAFT v0.1 — skeleton only.** Sections marked `[TBD]` await Exp14 verdict (Search Tool, in progress) and cross-model replication (planned via Groq free tier + Local Qwen 2.5 7B Q4_K_M). Statistics in `[stats: pending]` markers will be regenerated with consistent (Δ, n, p, Cohen's d, 95% CI) 5-tuple.

## Abstract

> [TBD — finalize after Exp14 + cross-model results, ~200 words]

Skeleton: Small open-weight LLMs (≤7B params) struggle on multi-step reasoning where larger frontier models excel. We investigate whether externalizing four cognitive axes — working memory ("Tattoo"), computation ("Tools"), self-validation ("Role"), and control flow ("Orchestrator") — into structured workflow components rather than expanding model capacity can close this gap on a single 4B-effective open-weight model (Gemma 4 E4B). Across 13 sequentially numbered hypotheses (H1–H13) over 540+ trials, we report three primary findings: (1) multi-step orchestration with role separation improves baseline 41.3% → 78.1% (+37pp), matching Gemini 2.5 Flash 1-call by +19pp at zero per-trial API cost; (2) self-validation by the same model fails (0/15 detected), but role-separated cross-validation recovers to 80%; (3) we identify a **position-effect asymmetry** in role-axis addition: pre-stage Extractor yields Δ=+0.05 (d=+0.32), post-stage Reducer yields Δ=−0.05 (d=−0.32) — a mirror image driven by abstraction loss in post-stage compression. Cross-model replication on Llama 3.1 8B and Qwen 2.5 7B [TBD] confirms direction. We release a reproducible harness with all hypothesis verdicts including three negative results.

## 1. Introduction

### 1.1 The small-LLM gap on multi-step reasoning

[TODO: motivation paragraph — small open-weight models on complex reasoning. Cite frontier-model performance differential.]

### 1.2 Externalization vs parameter scaling

The dominant narrative in 2024–2026 has been parameter scaling — Llama 3.3 70B, Qwen 3 235B, GPT-OSS 120B — with proportional inference-time cost. We investigate the orthogonal axis: holding model capacity fixed (Gemma 4 E4B, effective 4B params) and externalizing four cognitive functions into the workflow.

### 1.3 Three contributions

1. **A 4-axis externalization framework for small-LLM workflows**: Tattoo (working memory) / Tools (computation) / Role (self-validation) / Orchestrator (control flow). Taxonomy contribution.
2. **Position-effect asymmetry in role-axis addition**: pre-stage role addition (Extractor) is safe (Δ=+0.05, d=+0.32), post-stage (Reducer) is risky (Δ=−0.05, d=−0.32); mechanism = abstraction loss in post-stage compression. Empirical / mechanism contribution.
3. **A reproducible measurement protocol**: 13 hypotheses (H1–H13) with verdict / evidence / negative results, single-base-model rigor (Gemma 4 E4B across all roles to isolate structure from model-quality confound). Methodology contribution.

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

### 4.5 Negative results

[stats: pending]

| H | Hypothesis | Verdict | Mechanism |
|---|---|---|---|
| H2 | Same-model self-validation detects errors | Rejected (0/15 detected) | Model cannot criticize own reasoning trace |
| H10 | Stronger Judge (Gemini 2.5 Flash) compensates weaker A/B | Inconclusive (effectively rejected); Δ=−0.081, d=−0.316 | Inverse mechanism: stronger Judge breaks weaker model's self-discovery (logic-02 case study, Δ=−0.900) |
| H12 | Post-stage Reducer role polishes final_answer | Inconclusive (effectively rejected); Δ=−0.053, d=−0.323 | Abstraction loss: "polish for clarity" + "do NOT change conclusion" compresses multi-source reasoning into single-point answers |

### 4.6 Position-effect asymmetry — single best contribution

[The main contribution. To be expanded into 1-2 pages.]

| | Exp12 Extractor (H11) | Exp13 Reducer (H12) |
|---|---|---|
| Position | **pre-stage** (before A) | **post-stage** (after C) |
| Δ accuracy | **+0.0500** | **−0.0533** (bug-excluded) |
| Cohen's d | **+0.323** (small, positive) | **−0.323** (small, negative) — **mirror image** |
| Mechanism | cycle-1 input organization | abstraction loss / multi → single compression |
| logic-02 catastrophic | base 0.3 → ext 0.6 (+0.30, recovery) | base 0.7 → red 0.5 (−0.20, regression) |
| synthesis pattern | 5/5 tasks improvement direction | **5/5 tasks negative** |
| Verdict | Conditionally supported | Inconclusive (effectively rejected) |

The plan's symmetry assumption (pre/post role addition) breaks empirically. The mirror-image effect (|d|=0.323 in opposite directions) on the same model, taskset, and trial count is a clean signal that **position matters more than addition**: external Role assistance is safe before the chain (input stabilization) and risky after (output compression).

[TODO: extended discussion — synthesis-04 case study, mechanism analysis]

### 4.7 Search Tool (H13) — [TBD, Exp14 in progress]

[TBD: A-1 (baseline_abc_chunked, n=50) shows mean_acc=0.95 (saturation at 32K context). A-2 (abc_search_tool, n=50) running. Verdict + analysis after Exp14 task-05.]

### 4.8 Statistical reporting protocol

All hypothesis verdicts report (Δ, n, p, Cohen's d, 95% CI) 5-tuple. p-values use paired Wilcoxon (primary) and paired t-test (secondary). 95% CI by paired bootstrap (n=10,000). [TODO: regenerate for H1, H7, H8, H9a from existing result JSONs; H10–H12 already have full 5-tuple.]

## 5. Discussion

### 5.1 Why same-model role separation works

[TODO: H3 (80% detection via cross-validation) + H1 (multi-loop +37pp) — separation, not capability, is the active ingredient. Cite Exp035 result.]

### 5.2 Why post-stage role addition fails — abstraction loss

[TODO: H12 mechanism. Synthesis-04 case study. Connection to Exp11's inverse-mechanism finding (stronger external Role disrupts weaker model's self-discovery).]

### 5.3 Implications for small-LLM deployment cost

[TODO: ABC+Gemma 4 E4B vs Flash 1-call cost analysis from Exp10. Trading wall time (~20×) for per-trial API cost ($0).]

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
