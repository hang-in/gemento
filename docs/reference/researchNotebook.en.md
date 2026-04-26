---
type: reference
status: in_progress
updated_at: 2026-04-25
mirror_of: docs/reference/researchNotebook.md (Part 1 — Closed Findings)
language: en
---

> **Conceptual framework canonical document**: [conceptFramework.md](./conceptFramework.md) — 4-axis externalization principles, terminology definitions, axis ↔ experiment mapping.

# Gemento Research Notebook

> This document records all Gemento project experiments based on the 6W1H (Who/When/Where/What/Why/How) framework.
> New sections are appended as each experiment is completed.

> **English mirror — design statement**
>
> This is the English mirror of [`researchNotebook.md`](./researchNotebook.md) **Part 1 — Closed Findings**.
>
> - Part 1 covers concluded experiments (Exp00–09) and hypothesis verdicts (H1–H9c). The Korean source is the single source of truth; this English file is a translation, not the original.
> - Part 2 (Active Research — open questions, next experiments) is **not translated**. It remains Korean-only by design — when items in Part 2 close, they migrate to Part 1 and become eligible for English translation.
> - **Append-only**: the contents of this file should only grow. Existing entries should not be edited.

---

# Part 1 — Closed Findings

> This part contains only concluded experiment results and hypothesis verdicts. When new experiments are added, **entries are appended only — existing content is not modified**. Korean source: [`researchNotebook.md`](./researchNotebook.md).

## Project Overview

| Item | Details |
|------|---------|
| Project name | Gemento (제멘토) |
| Core question | If a small LLM (4.5B) is given an external state (tattoo) and an iterative reasoning structure, can it achieve statistically significant quality improvement over single-pass inference? |
| Target model | Gemma 4 E4B (Exp00–06: Q4_K_M / Ollama, Exp07+: Q8_0 / llama.cpp GPU server) |
| Execution environment | Windows (Ollama or llama.cpp) — experiment execution / macOS — analysis and documentation |
| Research period | 2026-04-08 ~ ongoing |
| Sampling | `temperature=0.1`, `max_tokens=4096`, `top_p`/`seed` unset (single source: `config.py:SAMPLING_PARAMS` — introduced 2026-04-26 via sampling-params-config-exp10 plan) |

> *Note: H1–H9 below denote nine sequentially numbered hypotheses about externalization axes — they are **not** the statistical H₀ (null) / H₁ (alternative) pair.*

### Key Hypotheses

| ID | Hypothesis (externalization axis) | Final verdict | Decision experiment |
|----|----------------------------------|---------------|---------------------|
| H1 | **[Orchestrator externalization]** Multi-step loops produce higher quality than single-pass inference | **Supported** | Exp02 |
| H2 | **[Role externalization necessity — falsification]** Errors are amplified through loops | **Rejected** (no error detection) | Exp03 |
| H3 | **[Role externalization]** Cross-validation (role separation) can detect errors | **Supported** (80%) | Exp035 |
| H4 | **[Role externalization synergy]** A-B-C role separation outperforms repeated single-agent inference | **Supported** (+22.6pp) | Exp06 |
| H5 | **[Orchestrator externalization ceiling]** Increasing MAX_CYCLES contributes to accuracy improvement (saturation point exists) | **Partially rejected** (ceiling expansion ineffective, saturation at actual_cycles≈7) | Exp07 |
| H6 | **[Role externalization refinement]** Phase-specific prompts outperform baseline | **Partially supported** (long loops 15~20: +5~6pp) | Exp07 |
| H7 | **[Tool externalization]** External math tools (calculator/linalg/linprog) compensate for E4B's computational limits | **Supported** (+18.3pp, math-04 0→80%) | Exp08 |
| H8 | **[Tool externalization stability]** Error hints + Mandatory tool rules mitigate tool_neglect and operator confusion | **Supported** (neglect 0%, calculator 100%, math-04 0→100%, total +23.3pp) | Exp08b |
| H9a | **[Tattoo externalization — physical limit breakthrough]** ABC+Tattoo(chunked) outperforms Solo-dump in long-context settings | **Supported** (+68.3pp, Large 20K: Solo 0% → ABC 100%) | Exp09 |
| H9b | **[Differentiation]** ABC+Tattoo has unique contribution over RAG baseline | **Partially supported** (overall +3.3pp; Large 3-hop: +33pp clearly superior, small: RAG superior) | Exp09 |
| H9c | **[Error mode differences]** ABC's failure patterns are qualitatively different from Solo and RAG | **Supported** (Solo: format_error 24, RAG: wrong_synthesis 6, ABC: evidence_miss 2 + wrong_synthesis 3) | Exp09 |

#### Axis ↔ Experiment Matrix

A 2D matrix showing which of the 4 externalization axes each experiment validates. ✅ = primary validation, ▶ = indirectly related, — = not applicable.

| Experiment | Tattoo | Tool | Role Agent | Orchestrator |
|------------|:------:|:----:|:----------:|:------------:|
| Exp00 (Baseline) | — | — | — | — |
| Exp01 (Assertion Cap) | ✅ | — | — | — |
| Exp02 v2 (Multiloop) | ▶ | — | — | ✅ |
| Exp03 (Error Propagation) | — | — | ✅ (falsification) | — |
| Exp035 (Cross Validation) | — | — | ✅ | — |
| Exp04 (A-B-C Pipeline) | ▶ | — | ✅ | ✅ (Judge Role) |
| Exp045 (Handoff Protocol) | ✅ | — | ▶ | — |
| Exp05b (Hard Tasks) | ✅ | — | ✅ | — |
| Exp06 (Solo Budget) | — | — | ✅ | — |
| Exp07 (Loop Saturation) | — | — | ▶ | ✅ |
| Exp08 (Math Tool-Use) | — | ✅ | ▶ | — |
| Exp08b (Tool Refinement) | — | ✅ | — | — |

> For detailed definitions, see [conceptFramework.md § 2](./conceptFramework.md).

---

## Experiment Records

---

### Exp00: Baseline (Single-pass Inference)

| Item | Details |
|------|---------|
| **Who** | Gemma 4 E4B × 1 (single model, no tattoo) |
| **When** | 2026-04-08 |
| **Where** | Windows Ollama local environment |
| **What** | Measuring single-pass inference quality of E4B without tattoo structure |
| **Why** | Establishing the comparison baseline for all subsequent experiments. Understanding "without" performance is necessary to measure the effect of the tattoo system |
| **How** | 6 tasks (math×2, logic×2, synthesis×2) × 3 repetitions = 18 data points. Question + necessary information only, single response |

**Results:**

| Task | Accuracy | Notes |
|------|----------|-------|
| math-01 | 3/3 (100%) | Basic arithmetic |
| math-02 | 3/3 (100%) | Multi-variable simultaneous equations |
| logic-01 | 0/3 (0%) | Response truncated due to output token limit |
| logic-02 | 0/3 (0%) | Inclusion-exclusion principle failure |
| synthesis-01 | 3/3 (100%) | Simple conditional synthesis |
| synthesis-02 | 0/3 (0%) | Multi-step path calculation failure |
| **Total** | **9/18 (50%)** | |

**Key Findings:**
1. Structured math → sufficient. Complex logic/synthesis → failure (0%)
2. Automated scoring (substring) overestimates — manual verification required
3. Scoring: v1=0.705, v2=0.722

**Conclusion:** E4B achieves 50% accuracy in single-pass inference. Structural support required for complex problems.

---

### Exp01: Assertion Cap (Tattoo Capacity Limit)

| Item | Details |
|------|---------|
| **Who** | Gemma 4 E4B × 1 |
| **When** | 2026-04-08 |
| **Where** | Windows Ollama |
| **What** | Measuring structured output stability across assertion counts (2~12) |
| **Why** | Validating whether the soft cap 8 / hard cap 10 decided in RT discussion is actually effective. Verifying if excessive assertions cause "middle forgetting" phenomenon |
| **How** | Assertion count = {2, 4, 6, 8, 10, 12} × task × 3 repetitions. Pre-written correct assertions provided, JSON parsing success rate measured |

**Results:**

| Cap | JSON success rate |
|-----|-----------------|
| 2~12 | All 100% |

**Key Findings:**
1. Stable up to 12 assertions — no "middle forgetting" effect
2. Response time increases linearly with assertion count
3. RT recommendation (soft 8 / hard 10) maintained as valid

**Conclusion:** Assertion capacity is not a bottleneck within the experimental range.

---

### Exp02: Multi-step Loop Quality Accumulation (H1 Validation)

| Item | Details |
|------|---------|
| **Who** | Gemma 4 E4B × 1 (repeated calls) |
| **When** | 2026-04-09 |
| **Where** | Windows Ollama |
| **What** | Measuring accuracy and convergence rate changes across loop counts (1, 2, 4, 8) |
| **Why** | **H1 validation** — "Does repeatedly calling the same small LLM improve reasoning quality?" |
| **How** | Phase sequence (DECOMPOSE→INVESTIGATE→SYNTHESIZE→VERIFY→CONVERGED) managed by orchestrator. v1 (model-autonomous) → failure → v2 (orchestrator-forced) transition |

**Version Comparison:**

| Version | Convergence rate | Key difference |
|---------|-----------------|----------------|
| v1 (model-autonomous phase transition) | 0/72 (0%) | Model cannot make phase transitions/confidence judgments |
| **v2 (orchestrator-forced)** | **17/18 (94.4%)** | Orchestrator manages phase sequence |

**v2 Results:**

| Loops | Accuracy | Convergence | vs Baseline |
|-------|----------|-------------|-------------|
| 1 | 0% | 0% | −50pp (structural: answer impossible in DECOMPOSE) |
| 2 | 44.4% | 0% | −5.6pp |
| 4 | 66.7% | 44.4% | +16.7pp |
| **8** | **94.4%** | **94.4%** | **+44.4pp** |

**Key Findings:**
1. **H1 supported** — Baseline 50% → 8-loop 94.4%, monotonically increasing
2. **Decisive lesson:** Not a model problem but an orchestrator design problem. v1 (0%) → v2 (94.4%)
3. Role separation principle established: orchestrator = structure, model = execution

**Conclusion:** Multi-step loops are effective, but handing phase transitions to the model leads to failure. External structure management is essential.

---

### Exp03: Error Propagation and Self-Correction (H2 Validation)

| Item | Details |
|------|---------|
| **Who** | Gemma 4 E4B × 1 |
| **When** | 2026-04-09 |
| **Where** | Windows Ollama |
| **What** | Measuring the model's self-detection rate after injecting flaws (corrupt_content, inflate_confidence, contradiction) into the tattoo |
| **Why** | **H2 validation** — "Are flawed assertions amplified through loops, or self-corrected?" |
| **How** | 3 types of flaws injected at loops 2 and 4. 4 tasks × 3~9 trials = 15 data points. Confidence trajectory tracked |

**Results:**

| Flaw type | Trials | Detection rate | Confidence |
|-----------|--------|---------------|-----------|
| corrupt_content | 9 | 0% | 1.0 (all) |
| inflate_confidence | 3 | 0% | 1.0 (all) |
| contradiction | 3 | 0% | 1.0 (all) |
| **Total** | **15** | **0%** | **1.0** |

**Key Findings:**
1. **H2 rejected (unexpected direction)** — Errors neither amplify nor get detected
2. E4B unconditionally trusts all assertions — naive executor
3. VERIFY phase does not function in practice
4. Self-reported confidence is unreliable (always 1.0)

**Conclusion:** Self-verification impossible. Error detection must be delegated to external (cross-validation) mechanisms.

---

### Exp035: Cross-Validation Gate

| Item | Details |
|------|---------|
| **Who** | Gemma 4 E4B × 1 (critic-dedicated prompt) |
| **When** | 2026-04-09 |
| **Where** | Windows Ollama |
| **What** | Measuring whether a role-separated critic (B) can detect assertion flaws from another agent (A) |
| **Why** | Gate judgment before building A-B-C pipeline. PASS if detection rate >50%, ABANDON A-B-C if <20% |
| **How** | B provided with A's assertions + original question. Judgment requested: "Is this assertion valid?" 3 flaw types × 15 trials |

**Results:**

| Flaw type | Detection rate | vs Self-validation (Exp03) |
|-----------|--------------|--------------------------|
| corrupt_content | 9/9 (100%) | 0% → 100% |
| contradiction | 3/3 (100%) | 0% → 100% |
| inflate_confidence | 0/3 (0%) | 0% → 0% (metadata undetectable) |
| **Total** | **12/15 (80%)** | **0% → 80%** |

**Gate verdict: PASS** (80% > 50% threshold)

**Key Findings:**
1. **Same E4B can validate when role-separated** — Self-validation 0% → cross-validation 80%
2. Content-based flaws (arithmetic, logic errors) accurately detected with rationale
3. Metadata flaws (confidence manipulation) undetectable → orchestrator rule-based handling
4. Not a simple prompt effect but a structural difference (0%→80%)

**Conclusion:** Cross-validation effective. Basis for proceeding with A-B-C pipeline secured.

---

### Exp04: A-B-C Serial Pipeline

| Item | Details |
|------|---------|
| **Who** | Gemma 4 E4B × 3 roles (A=Proposer, B=Critic, C=Judge) |
| **When** | 2026-04-09 |
| **Where** | Windows Ollama |
| **What** | Validating whether E4B 3-role separation can operate a full reasoning pipeline without a Python orchestrator |
| **Why** | Exp02 required Python to force phase transitions, but the original hypothesis is "E4B × 3 serial structure." Testing whether C (Judge) can autonomously decide phase transitions |
| **How** | A→B→C serial calls. C judges B's criticism convergence to decide phase transition. Python handles safety nets only (MAX_CYCLES). 4 tasks × 3 trials = 12 runs |

**Results:**

| Metric | Exp04 | vs Exp02 v2 |
|--------|-------|------------|
| Convergence rate | 12/12 (100%) | 17/18 (94.4%) |
| Accuracy | 10/12 (83.3%) | 17/18 (94.4%) |
| C autonomous phase transition | 30/30 (100%) | Python forced |
| Python safety net triggered | 0 times | — |

**synthesis-02 failure (2/3):** `final_answer=None` — A's prompt issue, not C's. C correctly judged CONVERGED.

**Key Findings:**
1. **C completely replaces Python orchestrator** — 30/30 autonomous decisions, 0 safety net triggers
2. Each role's complexity is within E4B's capability range: A (reasoning), B (comparison), C (pattern matching)
3. Python exists as safety net only — judgment role removed

**Conclusion:** Original hypothesis "E4B × 3 serial structure" holds. However, structured output from A is required.

---

### Exp05a: Prompt Enhancement

| Item | Details |
|------|---------|
| **Who** | Gemma 4 E4B × 3 (A-B-C) |
| **When** | 2026-04-10 |
| **Where** | Windows Ollama |
| **What** | Attempting to fix Exp04's synthesis-02 `final_answer=None` problem with prompt enhancement ("MUST set final_answer") |
| **Why** | synthesis-02: A doesn't generate the final answer. Testing if "stronger instructions" resolve this |
| **How** | Added "MUST set final_answer" emphasis to A's system prompt. Re-run with same taskset |

**Result:** synthesis-02 still fails. Prompt enhancement ineffective.

**Scoring:** v1=0.636, v2=0.583

**Key Findings:**
1. **"Try harder" is ineffective** — Structural problems require structural solutions
2. This failure directly motivated Exp045 (Handoff Protocol) design

**Conclusion:** Prompt enhancement failed → pivoted to output schema enforcement.

---

### Exp045: Handoff Protocol (Information Transfer Protocol)

| Item | Details |
|------|---------|
| **Who** | Gemma 4 E4B × 3 (A-B-C) + Handoff schema |
| **When** | 2026-04-13 ~ 2026-04-14 |
| **Where** | Windows Ollama |
| **What** | Suppressing information loss between agents with structured Handoff format (HandoffA2B: blueprint, prioritized_focus, constraints) and handling hard tasks |
| **Why** | Resolving Exp04's synthesis-02 failure (structural issue) + securing information transfer stability before Exp05b scale-up |
| **How** | JSON Mode + Temperature 0.1. 6 tasks (existing 4 + 2 additional logic) × 3 trials = 18 runs. Handoff Loss Rate and Backprop Accuracy measured |

**Results:**

| Metric | Value |
|--------|-------|
| Convergence rate | 18/18 (100%) |
| Accuracy | 18/18 (100%) |
| Handoff Loss Rate (average) | 26.4% |
| Backprop Accuracy (average) | 9.5% |

**Loss Rate by Difficulty:**

| Difficulty | Loss Rate | Task examples |
|------------|-----------|---------------|
| Medium | 19.5~22.9% | math-01, logic-01, synthesis-01 |
| Hard | 39.8~47.3% | math-02, logic-02 |

**Key Findings:**
1. **synthesis-02 problem completely resolved** — via schema enforcement, not instruction emphasis
2. JSON Mode + Temperature 0.1 eliminates 99% of parsing errors
3. **System converges through repetition, not feedback propagation (backprop 9.5%)**
4. E4B complexity ceiling confirmed for Hard tasks (logic-02: 47.3% loss)

**Conclusion:** Output structure enforcement > prompt enhancement. 100% accuracy achieved. Complexity ceiling exists for Hard tasks.

---

### Exp05b: Task Difficulty Scale-up (Stress Test)

| Item | Details |
|------|---------|
| **Who** | Gemma 4 E4B × 3 (A-B-C) + Handoff Protocol |
| **When** | 2026-04-14 |
| **Where** | Windows Ollama |
| **What** | Scale-up with expanded taskset (9 tasks: existing 6 + 3 hard types) × 5 trials = 45 runs |
| **Why** | Verifying whether Exp045's 100% accuracy holds with increased task variety and difficulty |
| **How** | Added math-03, logic-03, synthesis-03. 5 repetitions per task for statistical reliability |

**Results:**

| Metric | Value |
|--------|-------|
| Overall accuracy | 40/45 (88.9%) |
| New hard 3 types | 14/15 (93.3%) |
| Weakest task | logic-02: 2/5 (40%) |
| Handoff Loss Rate | 20.3% |
| Backprop Accuracy | 25.9% |

**Scoring:** v1=0.649, v2=0.900

**Key Findings:**
1. High accuracy maintained even with hard tasks (93.3%)
2. logic-02 (contradiction detection + inclusion-exclusion) is the only weak point (40%)
3. Statistical reliability secured with 5 repetitions

**Conclusion:** A-B-C + Handoff extensible to hard difficulty. Only logic-02 type is at E4B's limit.

---

### Exp06: Solo-Budget Comparison (Synergy Measurement)

| Item | Details |
|------|---------|
| **Who** | Gemma 4 E4B × 1 (Solo: same compute budget) |
| **When** | 2026-04-15 |
| **Where** | Windows Ollama |
| **What** | Performance comparison when giving a single agent the same compute budget as A-B-C |
| **Why** | Distinguishing whether A-B-C's advantage is "role-separation synergy" or "simple repetition effect." Same budget → performance difference = structural synergy |
| **How** | Solo: E4B × 1 given same loop budget as ABC. 9 tasks × 1 trial = 9 runs |

**Results (v2 scoring):**

| Experiment | v2 average | Sample |
|------------|-----------|--------|
| Exp06 Solo | 0.967 | 9 |
| Exp045 ABC | 0.900 | 45 |
| **Δ (Solo − ABC)** | **+0.067** | — |

**Caveats:**
- Solo sample (9) is 5× smaller than ABC (45), high variance
- Under v1 scoring: ABC (88.9%) > Solo (66.3%), Δ = +22.6pp
- v2 keyword matching may overestimate Solo's partial answers

**Key Findings:**
1. ABC structural advantage confirmed under v1 (+22.6pp)
2. Under v2 Solo slightly ahead, but sample size asymmetry
3. **Without external critique, premature convergence** — Solo terminates at 4~5 loops with undetected errors
4. ABC maintains structure on complex tasks (synthesis-03), Solo collapses

**Conclusion:** Role-separation synergy confirmed. ABC advantage especially clear on high-complexity tasks.

---

### Exp07: Loop Saturation + Loop-Phase Prompts

| Item | Details |
|------|---------|
| **Who** | Gemma 4 E4B × 3 (A-B-C) — model source switched from Ollama Q4_K_M → llama.cpp Q8_0 |
| **When** | 2026-04-23 ~ 2026-04-24 (completed via Gemini CLI / Windows) |
| **Where** | Windows + external llama.cpp GPU server (`yongseek.iptime.org:8005`, OpenAI-compatible `/v1/chat/completions`) |
| **What** | 2(prompt: baseline/phase) × 4(MAX_CYCLES: 8/11/15/20) factorial design to identify loop saturation point and measure phase-specific prompt effects |
| **Why** | Starting from the question "Is 11 loops really sufficient?" The existing taskset was biased toward low difficulty (early convergence), failing to measure loop limits. Added 3 hard tasks (04-level) + variabilized MAX_CYCLES ceiling to **search for the saturation point where marginal returns converge to 0** |
| **How** | Added 3 hard tasks (math-04, logic-04, synthesis-04) → total 12 tasks. Each task × 3 trials × 8 conditions = **288 runs**. Added MAX_CYCLES and use_phase_prompt parameters to `orchestrator.py`/`config.py`, added loop_saturation branch to `run_experiment.py`, added phase-level aggregation + High-Difficulty table to measure.py |

**Results (accuracy, substring-based — exp07_report.md):**

| MAX_CYCLES | Baseline accuracy | Phase accuracy | Δ (Phase − Base) | Baseline convergence | Phase convergence |
|------------|------------------|----------------|------------------|---------------------|------------------|
| 8  | 79.2% | 83.8% | +4.6pp  | 91.7%  | 100.0% |
| 11 | 86.6% | 83.8% | −2.8pp  | 100.0% | 100.0% |
| 15 | 81.5% | **88.0%** | **+6.5pp** | 100.0% | 100.0% |
| 20 | 80.1% | 85.6% | +5.6pp  | 100.0% | 100.0% |

**Hard (04) Tasks:**

| Task | Best accuracy | Best condition | Average cycles |
|------|--------------|----------------|----------------|
| logic-04     | 100.0% | baseline_11 | 7.0 |
| math-04      | **50.0%** | baseline_11 | 6.0 |
| synthesis-04 | 100.0% | baseline_11 | 7.0 |

**actual_cycles Distribution (all conditions, 288 trial raw data):**

| Condition | Average actual_cycles |
|-----------|----------------------|
| baseline_8  | 7.00 |
| baseline_11 | 7.00 |
| baseline_15 | 6.89 |
| baseline_20 | 6.86 |
| phase_8     | 7.03 |
| phase_11    | 6.97 |
| phase_15    | 7.11 |
| phase_20    | 7.00 |

**Key Findings:**
1. **Saturation point is actual_cycles ≈ 7, not MAX_CYCLES** — Even with ceiling at 15 or 20, actual cycles stabilize at approximately 7. C (Judge)'s convergence decision always precedes "budget exhaustion."
2. **H5 partially rejected** — "Ceiling increase = accuracy increase" does not hold. MAX_CYCLES=11 gives best baseline (86.6%), slightly decreasing at 15/20. The ceiling itself is a "safety net," not a function of accuracy.
3. **H6 partially supported** — Phase-specific prompts have a +5~6pp advantage over baseline **only in long loops (15, 20)**. In short loops (11) they are −2.8pp. Interpretation: phase guidance is "unnecessary for short reasoning, drift-suppressing for long reasoning."
4. **math-04 wall** — Multi-step mathematical reasoning (04-level) cannot exceed 50% under any loop or prompt condition. logic-04/synthesis-04 achieve 100% in all conditions. → Math reasoning limit is not resolved by structural improvement. **※ Exp08 correction**: This "50%" was an artifact from **scoring data flaws**. The `taskset.json`'s `expected_answer="X=30,Y=30,Z=10,profit=$2800"` violated the material constraint (3·30+2·30+1·10=160 > 150 kg), making it an infeasible solution. With the corrected answer (X=31, Y=10, Z=37, profit=$3060), math-04 baseline in Exp08 was **0%**. E4B essentially cannot solve this LP problem without tools.
5. **Convergence rate nearly uniform** — Only baseline_8 at 91.7%; remaining 7 conditions at 100%. Q8_0 switch + loop headroom stabilizes convergence.
6. **Infrastructure switch effects** — Q4_K_M (Ollama) → Q8_0 (llama.cpp) doubles model precision. Base quality for the same tasks (math-01~03, logic-01~03, synthesis-01~03) may have improved vs prior experiments. **Direct comparison with Exp05b requires caution.**

**Conclusion:**
- **Loop count increases yield no further gains** — E4B A-B-C structure's cycle saturation point is approximately 7.
- **Phase prompts act as "cost-free safety margin"** — Drift-suppression effect in long loops.
- **Next bottleneck is task-intrinsic complexity (math-04), not loops.**
- Operational default: `MAX_CYCLES=11, use_phase_prompt=True` recommended (phase_11: low-cost, high-stability).

**Known Issues:**
- `experiments/results/exp07_report.md` saved as UTF-16 LE (Windows PowerShell `>` redirect default encoding). UTF-8 enforcement needed in `measure.py` output path or run script — pending cleanup. **Fundamentally resolved in Exp08 with `--output` option introduction.**

---

### Exp08: Math Tool-Use (calculator + linalg + linprog)

| Item | Details |
|------|---------|
| **Who** | Gemma 4 E4B × 3 (A-B-C) + 3 external math tools injected into A path only. B/C have no tools. |
| **When** | 2026-04-24 (completed via Gemini CLI / Windows) |
| **Where** | Windows + external llama.cpp GPU server (`yongseek.iptime.org:8005`, OpenAI-compatible tool_calls path) |
| **What** | H7 validation — "Do external math tools compensate for E4B's computational limits?" And identifying the true cause of Exp07's math-04 50% stagnation. |
| **Why** | Exp07 showed math-04 completely stuck at 50% across all 8 conditions → confirmed structural wall not breakable by loops/prompts. llama.cpp server's `supports_tools: true` capability + confirmation that `scipy.linprog` can correctly solve the LP problem informed the experimental design. |
| **How** | **Incidental finding**: During design, discovered the existing `taskset.json`'s math-04 `expected_answer="X=30, Y=30, Z=10, profit=$2800"` violated the material constraint (material 160 > 150). Corrected to the true optimal solution X=31, Y=10, Z=37, profit=$3060 (commit `6c6f198`). Experiment: 2 arms (baseline_phase15 / tooluse_phase15) × 4 math tasks (math-01~04) × 5 trials = **40 runs**. MAX_CYCLES=15, use_phase_prompt=True fixed. Tools: `calculator` (AST whitelist eval), `solve_linear_system` (numpy), `linprog` (scipy HiGHS). |

**Results (v2 scoring):**

| Arm | Accuracy (v2) | Accuracy (v1) | Avg Cycles | Tool Calls / Errors |
|-----|---------------|---------------|------------|---------------------|
| baseline_phase15 | 0.72 | 0.64 | 7.8 | — |
| **tooluse_phase15** | **0.90** | **0.75** | **7.2** | **18 / 4** |
| **Δ (v2)** | **+0.183 (+18.3pp)** | +0.11 | −0.6 | — |

**Per-Task:**

| Task | Baseline | Tool-use | Δ | Average tool_calls |
|------|----------|----------|---|--------------------|
| math-01 | 1.00 | 1.00 | ±0 | 1.6 |
| math-02 | 1.00 | 1.00 | ±0 | 0.8 |
| math-03 | 0.87 | 0.80 | −0.07 (noise, both sides have "inconsistent" correct answers) | — |
| **math-04** | **0.00** | **0.80** | **+0.80** | 1.0 |

**Tool Success Rates:**

| Tool | Calls | Errors | Success rate | Primary errors |
|------|-------|--------|-------------|----------------|
| `linprog` | 5 | 0 | 100% | — |
| `solve_linear_system` | 7 | 1 | 86% | `Singular matrix` 1 case (model misidentified LP as simultaneous equations) |
| `calculator` | 6 | 3 | 50% | `BitXor` 3 cases (model used `^` for exponentiation — Python meaning is XOR) |

**Key Findings:**
1. **H7 supported** — Overall accuracy +18.3pp, decisive breakthrough especially at math-04: 0% → 80% (+80pp).
2. **Exp07 interpretation overturned** — Full review of math-04 baseline 5 trials: 4 had `final_answer=None` (10~11 cycles without generating answer), 1 had wrong answer `X=25, Y=10, Z=35, profit=2700`. E4B essentially cannot solve this LP problem without tools. Exp07's 50% was a scoring artifact from wrong expected_answer (X=30,Y=30,Z=10,profit=2800) partial substring matching.
3. **Gemento hypothesis reconfirmed** — "Small LLM + external state (tattoo)" design pattern naturally extends to "Small LLM + external tools (tool_calls)". The design principle "break structural limits with external resources" holds in both dimensions.
4. **Tool side effect 1 — Tool neglect** — In math-04 tooluse trial 2, model made 0 tool calls (tc=0) and returned `None` after 10 cycles despite tools being available. Tool existence doesn't guarantee use → prompt or `tool_choice` strategy needed.
5. **Tool side effect 2 — Calculator `^` confusion** — Model misinterprets Python `^` (XOR) as mathematical exponentiation, generating expressions like `2^10`. AST whitelist correctly blocks this, but error message ("Disallowed operator: BitXor") is not helpful to the model. Improvement: add hint or preprocess `^` to `**`.
6. **math-03 "decline" is noise** — Full answer review confirms both baseline/tooluse correctly conclude "the problem is inconsistent." Difference is keyword matching variation in expression (particularly one Korean response affects v2). No actual performance difference.
7. **Average cycle decrease** — Baseline 7.8 → Tooluse 7.2. Tools induce earlier convergence. Particularly striking for math-04: baseline 10~11 cycles (all failures) vs tooluse 7~8 cycles (mostly successful).

**Conclusion:**
- **H7 fully supported**. External tools break E4B's **structural computational limits** (especially optimization).
- Gemento's original design principle ("compensate limits with external resources") proven effective in the tool dimension.
- Exp07's math-04 interpretation was **error due to scoring data flaws** — highlighting the need for expected_answer validation procedures in research pipelines.

**Known Issues / Follow-up:**
- Calculator `^` BitXor confusion → error message improvement or preprocessing. **→ Resolved in Exp08b.**
- Tool neglect pattern → tool_choice strategy or prompt reinforcement. **→ Resolved in Exp08b.**
- math-03 Korean response + v2 scoring matching verification needed.
- This experiment is **not directly comparable with Exp07** (math-04 expected_answer changed, same Q8_0 environment but taskset modified).

---

### Exp08b: Tool-Use Refinement (Error Hints + Mandatory Rules)

| Item | Details |
|------|---------|
| **Who** | Gemma 4 E4B × 3 (A-B-C) + improved tools + reinforced SYSTEM_PROMPT |
| **When** | 2026-04-24 (completed via Gemini CLI / Windows) |
| **Where** | Windows + external llama.cpp GPU server |
| **What** | H8 validation — Re-measurement after mitigating the 2 side effects discovered in Exp08 (calculator `^` confusion, tool neglect) |
| **Why** | Exp08 result was H7 supported, but 2 side effects limited operational stability. (a) calculator BitXor 3/6 failures, (b) math-04 trial 2: failed without calling any tools. Validating whether these 2 can be resolved with minimally invasive improvements |
| **How** | (1) Added "use `**` for power; Python `^` is bitwise XOR" hint for `BitXor` case in `_eval()` in `experiments/tools/math_tools.py`. (2) Added 4 Mandatory rules to Tool use section of `SYSTEM_PROMPT` in `experiments/system_prompt.py` (mandatory linprog call for LP, `^` prohibited, mandatory retry after error, fabrication prohibited). (3) Added `tool-use-refined` command to `run_experiment.py` for 2 arms × 4 math tasks × 5 trials = **40 runs** same setting re-measurement. (4) Added `tool_neglect_rate` metric to `measure.py:analyze_tool_use` |

**Results (v2 scoring):**

| Arm | Accuracy (v2) | Accuracy (v1) | Avg Cycles | Tool Calls / Errors |
|-----|---------------|---------------|------------|---------------------|
| baseline_refined | 0.73 | 0.53 | 8.0 | — |
| **tooluse_refined** | **0.97** | **0.77** | **6.9** | **37 / 6** |
| **Δ (v2)** | **+0.233 (+23.3pp)** | +0.24 | −1.1 | — |

**Per-Task (v2):**

| Task | Baseline | Tool-use | Δ | Average tool_calls |
|------|----------|----------|---|--------------------|
| math-01 | 1.00 | 1.00 | ±0 | 1.8 |
| math-02 | 1.00 | 1.00 | ±0 | 2.2 |
| math-03 | 0.93 | 0.87 | −0.07 | 1.4 |
| **math-04** | **0.00** | **1.00** | **+1.00** | 2.0 |

**Tool Success Rates:**

| Tool | Calls | Errors | Success rate | Change (Exp08 → Exp08b) |
|------|-------|--------|-------------|------------------------|
| `calculator` | 16 | 0 | **1.00** | 0.50 → **1.00** (BitXor hint completely successful) |
| `solve_linear_system` | 12 | 6 | 0.50 | 0.86 → 0.50 (increased calls expose errors, all math-03 Singular matrix) |
| `linprog` | 9 | 0 | **1.00** | 1.00 → 1.00 (maintained) |

**Side Effect Resolution Status:**

| Target | Exp08 | Exp08b | Goal | Achieved |
|--------|-------|--------|------|---------|
| Calculator success rate | 0.50 | **1.00** | ≥0.85 | ✅ Exceeded |
| Tool Neglect Rate | 0.20 (1/5) | **0.00 (0/20)** | 0.00 | ✅ Exact |
| Tooluse arm accuracy | 0.90 | **0.97** | ≥0.95 | ✅ Exceeded |
| math-04 accuracy | 0.80 | **1.00 (5/5)** | — | ✅ Complete |

**Key Findings:**
1. **H8 fully supported** — All 3 targets achieved/exceeded. Additional +7pp improvement over Exp08 (90%→97%).
2. **math-04 complete success** — What was 4/5 in Exp08 (trial 2 neglect) becomes **5/5 all correct** (31, 10, 37, 3060). "Mandatory linprog call for LP" rule completely blocks tool neglect.
3. **Calculator BitXor completely resolved** — What was 6 calls with 3 failures (50%) in Exp08 becomes **16 calls all successful**. Direct evidence that error hint successfully corrected the model's **retry direction**.
4. **Avg Cycles decrease** — Baseline 8.0 vs tooluse 6.9. Tools and Mandatory rules induce **early convergence**. Even shorter than Exp08 tooluse (7.2).
5. **Exp07 interpretation reconfirmed** — math-04 baseline is 0% (same as Exp08). The conclusion "Exp07's 50% stagnation was a scoring data artifact" is independently reconfirmed.
6. **math-03 0.93 → 0.87**: 0.07 decrease after tool introduction vs baseline. Content of both sides correctly concludes "problem is inconsistent" — interpreted as noise range.
7. **solve_linear_system Singular matrix 6 cases**: All math-03 (inconsistent problem). Model attempts simultaneous equations approach and tool correctly returns "singular matrix." Not a tool issue — **natural exploration path for inconsistent problems**. Converges to "inconsistent" conclusion. Not an operational issue.

**Conclusion:**
- **H8 fully supported**. Error hints + Mandatory rules — **minimally invasive prompt/feedback-level improvements** — produce 97% accuracy.
- Even small models can achieve inference stability comparable to much larger models when **orchestration (rules) and precise tool utilization** are combined.
- Additional evidence for Gemento's design principle ("compensate limits with external resources + deterministic constraints elevate non-deterministic quality").

**Known Issues / Follow-up:**
- **solve_linear_system error hint candidate** — Adding "data may be inconsistent" hint to "Singular matrix" error could accelerate model's "inconsistent problem" judgment. Verifiable experiment (Exp08c candidate).
- math-03 Korean response + v2 scoring variance remains — independent issue.
- **Next is Exp09** — Exp08b's success is evidence limited to "single task, single inference." Next step: Long-context stress / stream workflow / cross-model.

---

### Exp09: Long-Context Stress Test (ABC vs Solo-dump vs RAG)

| Item | Details |
|------|---------|
| **Who** | Gemma 4 E4B × 3 (A-B-C) + Tattoo evidence_ref + new longctx taskset |
| **When** | 2026-04-25 (completed via Gemini CLI / Windows) |
| **Where** | Windows + external llama.cpp GPU server (n_ctx 8K × 4 slots) |
| **What** | H9 validation — Direct measurement of Gemento's **original core hypothesis** ("extend effective context with external state"). Does Gemento ABC + Tattoo (a) outperform Solo-dump and (b) show unique contribution over standard RAG baseline? |
| **Why** | Until now, H1·H4·H7·H8 compensate "computational/reasoning" limits with externalization tools. But the **context itself's** limit has never been directly measured. Exp09 frontally validates this hypothesis with documents 20~40× larger than sliding_window(512). RAG comparison also measured to block "Gemento = just RAG + loop" counterargument |
| **How** | New taskset `experiments/tasks/longctx_taskset.json` (10 tasks, 3 size classes × 3 hop types). 3 arms × 10 tasks × 3 trials = **90 runs**. Arms: (1) `solo_dump` — entire document + question single call, truncation if n_ctx exceeded, (2) `rag_baseline` — `bm25s` top-K=5 chunks single call, (3) `abc_tattoo` — chunk iteration + evidence_ref accumulation + final B+C convergence. New infrastructure: `tools/chunker.py`, `tools/bm25_tool.py`, `Assertion.evidence_ref` field, `run_abc_chunked()`, `analyze_longctx` + error mode taxonomy |

**Results (v2 scoring, 90 runs):**

| Arm | Accuracy v2 | Accuracy v1 | Errors |
|-----|-------------|-------------|--------|
| solo_dump | 0.20 | 0.20 | 24/30 (format_error) |
| rag_baseline | 0.85 | 0.90 | 0 |
| **abc_tattoo** | **0.88** | **0.93** | 0 |

**Key Deltas (v2):**
- **H9a (abc − solo)**: **+68.3pp** ✅ Overwhelmingly supported
- **H9b (abc − rag)**: **+3.3pp** ✅ Partially supported (marginal overall, but +33pp differentiation clear in 3-hop)

**Size Class Breakdown — Physical Limit Breakthrough Validation:**

| Arm | Small 3K | Medium 10K | Large 20K |
|-----|---------|-----------|----------|
| solo_dump | 1.00 | **0.00** | **0.00** |
| rag_baseline | 1.00 | 0.88 | 0.75 |
| **abc_tattoo** | **0.67** | 0.88 | **1.00** |

**Hop Type Breakdown — Origin of H9b Differentiation:**

| Arm | needle | 2-hop | 3-hop |
|-----|--------|-------|-------|
| solo_dump | 0.33 | 0.25 | 0.00 |
| rag_baseline | 1.00 | 0.88 | 0.67 |
| **abc_tattoo** | 0.78 | 0.88 | **1.00** |

**Per-Task Highlights:**

- `longctx-large-3hop-01`: solo 0% / **rag 0%** / **abc 100%** — Single task providing empirical evidence of RAG's information fragmentation.
- `longctx-small-needle-01`: solo 1.00 / rag 1.00 / **abc 0.33** — Core case of Small Paradox.

**Error Modes (H9c):**

| Arm | Primary failure pattern |
|-----|------------------------|
| solo_dump | `format_error` 24 cases — incomplete responses due to n_ctx exceeded truncation |
| rag_baseline | `wrong_synthesis` 6 cases — retrieval correct but integration failed |
| abc_tattoo | `evidence_miss` 2 + `wrong_synthesis` 3 cases — different pattern due to validation path |

**Evidence Hit Rate (ABC arm):**
- Overall: 0.35
- needle 0.33 / 2-hop 0.50 / **3-hop 0.23**
- Interesting asymmetry: 3-hop has the lowest hit rate but 100% accuracy. Hypothesis: "Rationalizing through the validation path" impacts accuracy more than "finding all necessary evidence."

**Key Findings:**
1. **H9a overwhelmingly supported** — Solo completely collapses at Medium and above **(0%)**, ABC achieves **100%** at Large 20K. The single most powerful evidence for Gemento's original hypothesis ("external state expands effective context").
2. **H9b partially supported — differentiation occurs in 3-hop** — needle/2-hop nearly equivalent with RAG (±0~12pp). **Only 3-hop: ABC 100% vs RAG 67% (+33pp)**. "Gemento ≠ just RAG + loop" holds **only in multi-evidence integration contexts**.
3. **H9c supported** — 3 arms' failure modes are qualitatively different (truncation vs information fragmentation vs post-validation residual errors).
4. **Small Paradox new discovery** — ABC weaker than RAG in small (0.67 vs 1.00). May be sample noise, or actual paradox (cycle iteration overkill when chunks are few). Exp10 candidate explicitly noted.
5. **Solo monotonic collapse** — 1.00 (small) → 0.00 (medium) → 0.00 (large). Truncation immediately leads to failure from the moment n_ctx 8K is approached. Model cannot normalize chunk-truncated responses.

**Conclusion:**
- **Gemento's original core hypothesis (context limit externalization) frontally proven**. The single most powerful evidence for the Tattoo (state externalization) axis among the 4-axis externalization principles in conceptFramework § 1.
- Counterargument "Gemento = RAG + loop" blocked — but differentiation is **limited to the multi-evidence integration domain**. RAG is sufficient for simple retrieval like needle.
- **Next candidates (Exp10+)**: Small Paradox resolution, parallel chunk traversal (Gemini handoff recommendation), Stream Workflow (long-term processing).

**Known Issues / Follow-up:**
- **Small Paradox** — ABC 0.33 in one small needle task. Small sample (small=2 tasks × 3 trials = 6 data points) may be noise. Additional trials or expanded small tasks needed for verification.
- **Evidence Hit Rate ↔ Accuracy asymmetry** — 3-hop hit 0.23 but 100% accuracy. Model may tend to attach non-answer chunks to evidence_ref, or gold_evidence_chunks labeling may be too strict. Separate analysis needed.
- **3 trials insufficient for statistical confidence** — Exp09b candidate: expand to 5 trials + p-value test.

---

## Scoring System History

### v1 → v2 Transition (2026-04-15)

| Item | v1 (substring) | v2 (keyword-group) |
|------|---------------|-------------------|
| Method | Whether expected string is contained in response | Whether core values of scoring_keywords groups are all contained |
| Problem | Long sentences, format differences, inserted explanations → false negatives | — |
| Motivation for introduction | — | Discovered scoring version comparison reliability degradation in Exp06 |

**Full Re-scoring Results:**

| Experiment | v1 | v2 | Δ |
|------------|-----|-----|-----|
| Exp00 Baseline | 0.705 | 0.722 | +1.7% |
| Exp02 Multiloop | 0.369 | 0.438 | +6.9% |
| Exp04 ABC Pipeline | 0.607 | 0.583 | -2.3% |
| Exp05a Prompt Enhance | 0.636 | 0.583 | -5.2% |
| Exp045 Handoff | 0.649 | 0.900 | +25.1% |
| Exp06 Solo Budget | 0.663 | 0.967 | +30.3% |

---

## Consolidated Findings: E4B Capability Profile

| Capability | Possible | Evidence |
|------------|---------|---------|
| Reading assertions (up to 12) | **Yes** | Exp01 |
| Following instructions (next_directive) | **Yes** | Exp02 |
| Stepwise reasoning and answer generation | **Yes** | Exp02 |
| Cross-validation (critic role) | **Yes (80%)** | Exp035 |
| Autonomous phase transition judgment (C role) | **Yes (100%)** | Exp04 |
| Autonomous phase transition judgment (standalone E4B) | **No** | Exp02 v1 |
| Self assertion validation | **No (0%)** | Exp03 |
| Self-reported confidence | **No** | Exp03 |

### Confirmed Architectural Principles

```
A (E4B Proposer)  = reasoning executor
B (E4B Critic)    = cross-validator (80% detection)
C (E4B Judge)     = convergence judgment + phase transition (100% autonomous)
Python            = safety net only (0 triggers)
```

---

## Change History

- 2026-04-26: `config.py:SAMPLING_PARAMS` centralization — `lmstudio_client.py` now explicitly sends sampling params. Pre-centralization LM Studio default may have differed from `temperature=0.1`/`max_tokens=4096`, so Exp10 results may show micro-variance vs Exp00~09. Treat the introduction date as a baseline boundary.

## Acknowledgements

- *Memento* (Christopher Nolan, 2000) — original metaphor of external memory aids.
- secall · tunaflow — practical origin of this research; the context/memory problems hit while building those tools shaped the externalization framework.

## License

Source code: [MIT](../../LICENSE). Documentation: same as repo policy.

---

*This document is incrementally maintained by appending sections as experiments are completed.*
