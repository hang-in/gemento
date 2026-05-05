# Gemento

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Status](https://img.shields.io/badge/Status-active-success)]()
[![Last commit](https://img.shields.io/github/last-commit/hang-in/gemento)](https://github.com/hang-in/gemento/commits/main)
[![Paper](https://img.shields.io/badge/Paper-draft%20in%20progress-orange)](docs/paper/draft.md)
[![arXiv](https://img.shields.io/badge/arXiv-TBD-b31b1b)]()

> **On a 9-task cost-aware benchmark, 8-loop ABC orchestration with Gemma 4 E4B scored 78.1% versus 41.3% for the same model in 1-loop solo, and 59.1% for a one-call Gemini 2.5 Flash baseline — at the cost of roughly 20× wall time and zero per-trial API cost.** Across 13 sequentially numbered hypotheses (H1–H13, 540+ trials), a recent role-axis ablation suggests a **position-effect pattern**: pre-stage role addition (Extractor, H11) shows Δ=+0.05 (Cohen's d=+0.32, p=0.198), while post-stage role addition (Reducer, H12) shows Δ=−0.05 (d=−0.32, p=0.180) — a directional mirroring at similar effect sizes. **Both effects are not statistically significant at n=15 paired tasks; cross-model replication is planned to test whether this direction generalizes.**

📚 Korean version: [README.ko.md](./README.ko.md) · 📄 Paper draft: [docs/paper/draft.md](docs/paper/draft.md) · arXiv: TBD

> *Last updated: 2026-05-05*

> **Gemento is an experimental harness, not a new architecture or a paper.** It tests whether small local LLMs can run long workflows when memory, tools, roles, and control are externalized.

## Why I built this

I started this while building secall and tunaFlow. The recurring problems were long-term memory, context over-spend, and work that had to survive across sessions. My first thought was simple: if I clear the prompt context and rely on database retrieval, can the database behave like near-infinite context? That line of thinking brought me back to *Memento* and Leonard's tattoos, polaroids, and phone calls. This repository is the side-track that grew out of that idea: not a new architecture, not a paper, but a measured notebook about whether small models improve when memory, action, critique, and control are externalized.

## What this is / is not

This is:

- a reproducible experiment harness for small local LLM workflows
- a measured notebook about externalized state, tools, roles, and control
- a public baseline for reproduction and disagreement

This is not:

- a new model architecture
- a training method
- a claim that 4B models replace frontier models
- a claim that ABC+Tattoo universally beats RAG

### Scope and reproducibility caveats (read before quoting numbers)

- All headline numbers come from a **single base model** (Gemma 4 E4B) on **a small custom benchmark** (15 tasks main + 10 long-context tasks). Cross-model replication is planned, not completed.
- Several Stage 5 hypotheses (H4, H10, H11, H12) are **not statistically significant at n=15 paired tasks** — they are reported with effect sizes (Cohen's d) and bootstrap CIs as *replication targets*, not as confirmed effects.
- The deterministic keyword scorer (`score_answer_v3`) cannot distinguish "real quality difference" from "answer-style mismatch with the keyword set". This is most relevant to H12 (Reducer compresses multi-source answers); LLM-as-judge replication is planned.
- The Exp10 vs Gemini Flash comparison is benchmark-specific and trades roughly 20× wall time for $0 per-trial API cost — not a general superiority claim.
- The "position-effect" observation from H11+H12 is a *directional pattern at mirrored effect sizes*, not a confirmed asymmetry.

## Core idea

Gemento treats four axes of LLM cognition as **externalizable** — moved out of model weights and into the workflow:

| Axis | What goes outside the model | Mechanism | Anchor experiment |
|------|----------------------------|-----------|-------------------|
| **Tattoo** | Working memory (claims, evidence, status) | Structured JSON state passed across loops | Exp02, Exp09 |
| **Tools** | Computation (math, search, retrieval) | OpenAI-compatible function calls (calculator, linalg, linprog) | Exp08, Exp08b |
| **Role** | Self-validation | A (Proposer) / B (Critic) / C (Judge) — separate prompts, same base model | Exp03, Exp035, Exp06 |
| **Orchestrator** | Termination · phase transition · resource budget | Deterministic Python loop, not the model itself | Exp02, Exp07 |

This is not about replacing a 70B model with a 4B one. It is about asking what **structure** can extract from a small model (Gemma 4 E4B, effective 4B parameters) that single-pass inference does not surface.

## What I measured

This repository tracks sequential hypothesis IDs `H1` to `H9c` across the four externalization axes.

> Note: H1-H9 below denote sequentially numbered hypotheses about externalization axes. They are **not** the statistical H₀/H₁ pair.

| ID | Hypothesis (Axis) | Verdict | Evidence |
|----|-------------------|---------|----------|
| **H1** | [Orchestrator externalization] Multi-step loops outperform single-pass reasoning | ✅ Supported (+44.4pp Exp02; +37pp Exp10) | Exp02 v2, Exp10 |
| **H2** | [Role externalization necessity, falsification] Self-validation can detect its own errors | ❌ Rejected (0/15 detected) | Exp03 |
| **H3** | [Role externalization] Cross-validation with separated roles can detect errors | ✅ Supported (12/15, 80%) | Exp035 |
| **H4** | [Role externalization synergy] A-B-C role separation outperforms repeated single-agent iteration | ⚠ Conditionally supported (synthesis category only, Stage 2C 2026-05-02) — 15-task ablation: ABC > Solo-budget +0.0444 (reverses 9-task subset's Solo +0.067 direction), synthesis +0.140 (recovery driver); not significant at n=15, Cohen's d=0.449 medium. Detail: `docs/reference/h4-recheck-analysis-2026-05-02.md` | Exp06 + Stage 2C |
| **H5** | [Orchestrator ceiling effect] Raising `MAX_CYCLES` improves accuracy | ⚠️ Partially rejected - the ceiling was not the limit; actual saturation appeared around `actual_cycles ≈ 7` | Exp07 |
| **H6** | [Role externalization refinement] Phase-specialized prompts outperform the baseline | ✅ Conditionally supported (+5-6pp in long loops) | Exp07 |
| **H7** | [Tool externalization] External math tools compensate for E4B's calculation limits | ✅ Supported (+18.3pp, math-04 0→80%) | Exp08 |
| **H8** | [Tool externalization stability] Error hints and mandatory tool rules reduce tool neglect and operator confusion | ✅ Supported (neglect 0%, calculator 100%, math-04 0→100%, +23.3pp) | Exp08b |
| **H9a** | [Tattoo externalization, physical limit] ABC+Tattoo (chunked) outperforms solo dump under long context | ✅ Supported (+68.3pp, Solo 0% → ABC 100% at Large 20K) | Exp09 |
| **H9b** | [Distinctiveness] ABC+Tattoo contributes something beyond a RAG baseline | ⚠️ Inconclusive (5-trial stats NOT SIGNIFICANT p=0.798; overall Δ=+2.0pp; 3-hop only +20.0pp differentiation; Small Paradox confirmed) | Exp09 |
| **H9c** | [Error mode difference] ABC fails differently from Solo and RAG | ✅ Supported (Solo: `format_error`, RAG: `wrong_synthesis`, ABC: `evidence_miss` + `wrong_synthesis`) | Exp09 |
| **H10** | [Role externalization — strong Judge / Mixed Intelligence] A stronger Judge C (Gemini 2.5 Flash) compensates for weaker Proposer/Critic (A/B = Gemma 4 E4B) | ⚠ Inconclusive — effectively rejected (Exp11 2026-05-03). Δ(mixed − baseline) = −0.0811 (mixed *underperforms* baseline-all-Gemma); Cohen's d = −0.316 (small, negative); not significant at n=15, p=0.293; logic category catastrophic (−0.275). **Inverse mechanism observed**: stronger Judge interferes with weaker model's self-discovery chain (logic-02 case study). Detail: `docs/reference/exp11-mixed-intelligence-analysis-2026-05-03.md` | Exp11 |
| **H11** | [Role externalization — separation / addition (Extractor Role)] A new Role (Extractor, same Gemma 4 E4B model) that pre-extracts claims/entities from the prompt and prefixes them into A→B→C input improves accuracy | ⚠ Conditionally supported, power-limited (Exp12 2026-05-04). Δ(ext − baseline) = +0.0500; Cohen's d = +0.323 (small, positive); **not significant at n=15, p=0.198 (Wilcoxon)**. Directional improvement on logic-02 (0.3→0.6) and synthesis-05 (0.55→1.0). Suggests Role-axis *separation/addition* may be a safer evolution path than *strengthening*; not yet replicated cross-model. Detail: `docs/reference/exp12-extractor-role-analysis-2026-05-04.md` | Exp12 |
| **H12** | [Role externalization — separation / addition (Reducer Role, post-stage)] A new Role (Reducer, same Gemma 4 E4B model) that *post-stage* polishes the final tattoo + final_answer improves keyword-match accuracy | ⚠ Inconclusive — effectively rejected, power-limited (Exp13 2026-05-05). Δ(reducer − baseline) = −0.0533 (bug-excluded) / −0.0711 (with bug); Cohen's d = −0.323 (mirror of Exp12's +0.323 in magnitude); **not significant at n=15, p=0.180 (Wilcoxon)**. Proposed mechanism — *abstraction loss*: in synthesis-04, baseline produced structured multi-source analyses scoring high under the keyword scorer, while reducer produced compressed single-estimate answers scoring lower. **The current keyword-based scorer (`score_answer_v3`) cannot distinguish "actual quality drop" from "scorer-style mismatch"**; LLM-as-judge replication is planned (P1-3 in `docs/reference/paper-review-action-items-2026-05-05.md`). Together with H11, this provides **evidence consistent with a position effect** at similar effect-size magnitudes in opposite directions; cross-model replication is required before any stronger claim. Detail: `docs/reference/exp13-reducer-role-analysis-2026-05-05.md` | Exp13 |
| **H13** | [Tool externalization — agent-active retrieval] ABC agents that actively call a `search_chunks(query, top_k)` BM25 retrieval tool during cycles outperform a sufficient-context baseline (32K-context window with the full document in the prompt) on long-context tasks | ⚠ Inconclusive — effectively rejected, **statistically significant negative direction at this scale** (Exp14 2026-05-05). Δ(search − baseline) = **−0.220**; Cohen's d = **−1.000 (large)**; **Wilcoxon p=0.0312 / paired t p=0.0115 — first statistically significant verdict in Stage 5**. Bootstrap 95% CI Δ: [−0.36, −0.10] (does not include 0). **Mechanism = insufficient retrieval iterations on multi-hop tasks**: a 5-trial diagnostic on `longctx-large-2hop-01` showed `total_tool_calls` per trial = [1, 2, 2, 3, 0] → accuracy = [0, 1, 1, 1, 0]. The single-call trial recovered the hop-1 entity then prematurely concluded "the document does not contain a [number]" instead of issuing a hop-2 query. Needle (1-hop) tasks succeeded 5/5 with one well-formed call. **Tool axis sub-distinction**: deterministic single-call computation (calculator/linprog, H7/H8 +18~23pp) ≠ probabilistic agent-iterative retrieval (H13 −22pp). The result applies specifically to *agent-active BM25 retrieval against a 32K-context baseline*; a weaker form ("retrieval helps when context is the limit") is not addressed because the baseline saturated. Detail: `docs/reference/exp14-search-tool-analysis-2026-05-05.md` | Exp14 |

## What worked / What didn't

- Exp02 v2: 50% to 94.4% after forcing 8 loops on the same E4B model.
- Exp03: self-validation detected 0 out of 15 planted errors.
- Exp035: role-separated cross-validation recovered to 80%.
- Exp08b: math tool calls plus error-message hints moved math-04 from 0% to 100%.
- Exp09: on Large 20K long-context tasks, Solo dump scored 0%, RAG scored 67%, and ABC+Tattoo scored 100%.
- Exp10: on a 9-task / 540-trial cost-aware comparison, the same Gemma 4 E4B went from 41.3% (1-loop) to 78.1% (8-loop ABC). On this benchmark the ABC condition outperformed a one-call Gemini 2.5 Flash baseline (59.1%) by 19 percentage points, trading API cost for roughly 20× longer wall time. The result is benchmark-specific (9 tasks, math/logic/synthesis/planning) and 1-call vs 8-loop is an asymmetric comparison; it is not a general claim that small local models replace frontier APIs. ABC infrastructure had 4 trial-level JSON parse fails (early-stop pattern, see `docs/reference/exp10-v3-abc-json-fail-diagnosis.md`).
- Stage 2C (2026-05-02) re-evaluated H4 with an expanded 15-task ablation. ABC outperformed Solo-budget by +0.044 (reversing the 9-task subset's Solo +0.067 direction). **The synthesis category was the recovery driver (+0.140)**; statistically not significant at n=15 but Cohen's d=0.449 (medium). H4 verdict moved from Inconclusive to ⚠ Conditionally supported (synthesis only). See `docs/reference/h4-recheck-analysis-2026-05-02.md`.
- Exp11 (2026-05-03) tested Mixed Intelligence (Judge C = Gemini 2.5 Flash, A/B = Gemma 4 E4B) and **the result was negative**: Δ(mixed − baseline) = −0.081, Cohen's d = −0.316 (small, negative). The logic-02 case study (Δ = −0.900) was decisive — baseline produced 4/5 correct answers explicitly stating "105 inconsistent" via the inclusion-exclusion principle, while mixed produced 5/5 nulls or keyword-missing answers. **Inverse mechanism observed**: a stronger Judge interferes with the weaker model's self-discovery chain via Tattoo-schema mismatch and premature convergence. H10 ⚠ Inconclusive — effectively rejected. The framework's next direction shifts from Role *strengthening* to Role *separation/addition*.
- Exp12 (2026-05-04) tested Extractor Role (a new Role using the same Gemma model, pre-extracting claims/entities and prefixing them into A's input). Δ = +0.050 (positive), Cohen's d = +0.323 (small). Directional improvements on logic-02 (0.3→0.6) and synthesis-05 (0.55→1.0). Proposed mechanism: cycle-1 *input organization* (assisting A, not replacing). H11 ⚠ Conditionally supported, **not statistically significant at n=15 (p=0.198)**.
- Exp13 (2026-05-05) tested Reducer Role (a structurally symmetric counterpart — same Gemma model, post-stage polishing of the final tattoo + final_answer). Δ = −0.053 (bug-excluded), Cohen's d = −0.323 — opposite in sign to Exp12 with nearly identical magnitude. In the synthesis-04 illustrative trial, baseline produced structured multi-source analyses ("## Comprehensive Analysis ... Identification of Contradictions ...") scoring 1.0, while the reducer-polished output compressed to single-point estimates ("The best estimate is **270 individuals**.") scoring 0.33–0.67. **Caveat — keyword scorer artifact possibility**: this drop may reflect *real abstraction loss* OR *style mismatch* between compressed answers and the deterministic keyword scorer (`score_answer_v3`). The two explanations are not separable from the current data; LLM-as-judge replication is planned. H12 ⚠ Inconclusive, effectively rejected (**not significant at n=15, p=0.180**). Together with H11, the two results provide **evidence consistent with a position effect** at similar effect-size magnitudes in opposite directions — but the pattern is a replication target, not a confirmed asymmetry.
- Exp14 (2026-05-05) tested an agent-active BM25 search tool against a sufficient-context baseline (32K-context window holds even Large 20K-word documents) on the long-context taskset (10 tasks). Δ = **−0.220**, Cohen's d = **−1.000 (large)**, **Wilcoxon p=0.0312, paired t p=0.0115 — the first statistically significant verdict in Stage 5**. Bootstrap 95% CI Δ: [−0.36, −0.10]. The mechanism is **insufficient retrieval iterations on multi-hop tasks**: in the diagnostic 5-trial run on `longctx-large-2hop-01`, tool-call counts of [1, 2, 2, 3, 0] mapped onto accuracy [0, 1, 1, 1, 0]. The single-call trial recovered the hop-1 entity ("Westbrook Institute") then prematurely concluded the document lacked the answer instead of issuing a hop-2 query. Needle (1-hop) tasks succeeded 5/5 with one well-formed call. H13 ⚠ Inconclusive, effectively rejected. → **Tool-axis sub-distinction**: deterministic single-call computation tools (calculator, linprog — H7/H8 +18~23pp on math tasks) ≠ probabilistic agent-iterative retrieval (H13 −22pp on multi-hop). Combined with the H11+H12 position effect, Stage 5's integrated finding is **"more structure is not monotonically better; what matters is where it is placed and how it iterates"** — the proposed paper's main claim. Stage 6 next: cross-model replication (Llama 3.1 8B, Llama 3.3 70B, Qwen 2.5 7B Q4_K_M) plus LLM-as-judge auxiliary evaluation to address the H12/H13 keyword-scorer caveats.

What clearly did **not** work was expecting the same model to notice its own failure mode without a role change. The most useful result in this repository is probably negative: the model does not reliably criticize itself, even when it can criticize the same reasoning from another role.

## Why this matters

If you are working on externalization for small models, structured state, or multi-role validation, this repo is meant to be a public coordinate rather than a closed notebook. It is MIT-licensed on purpose. I would rather have competing measurements, forks, and disagreements in public than keep this siloed until it looks polished.

## Quickstart

### Environment

Tested with **Python 3.14**. Earlier 3.12+ should work but is not regularly verified — if you hit a syntax/typing error on an older interpreter, please report the version.

```bash
git clone https://github.com/hang-in/gemento.git
cd gemento
python3.14 -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Inference server (LM Studio or llama.cpp — both supported)

Gemento expects an **OpenAI-compatible chat-completions endpoint** that supports `tool_calls`. Two reference setups:

- **LM Studio** (current author's setup): load Gemma 4 E4B Q8_0 with at least 32K context window enabled, server on `http://192.168.1.179:1234` (or `http://localhost:1234`). Set `API_BASE_URL` accordingly in `experiments/config.py`.
- **llama.cpp server**: `./server -m gemma-4-e4b-q8_0.gguf -ngl <max layers> -c 32768 --port 8080`. Default `http://localhost:8080`.

Confirm the active model id and use it for `MODEL_NAME`:

```bash
curl -s $API_BASE_URL/v1/models | jq -r '.data[].id'
```

Expected: a model id such as `gemma4-e4b`, `google/gemma-3n-e4b-it`, or whatever your server reports. Set `MODEL_NAME` in `experiments/config.py` to *exactly* this string — a mismatch causes silent fallback to defaults on some servers.

### Smoke test

```bash
cd experiments
python tools/smoke_test.py
```

Expected: `SMOKE TEST PASSED: math-04 answer=..., tool_calls=...`

### Reproduce the headline Exp10 result (~12-14h on a single 8GB GPU)

The README hero number (Gemma 4 E4B 41.3% → 78.1% across 9 tasks × 60 trials = 540 trials per condition) comes from Exp10. To reproduce on your machine:

```bash
# from the gemento root, after smoke test passes
python -m experiments.exp10_reproducibility_cost.run --conditions gemma_1loop --trials 60
python -m experiments.exp10_reproducibility_cost.run --conditions gemma_8loop --trials 60
# results land in experiments/exp10_reproducibility_cost/results/
# scorer: score_answer_v3 (negative_patterns) — applied automatically
```

Per-trial wall time depends on hardware; on a 3060 Ti 8GB with LM Studio the 8-loop condition averages ~7-8 minutes/trial. Optional: `gemini_flash_1call` condition requires `GEMINI_API_KEY` in `.env` and incurs API cost (≈$0.05 for 60 trials at 2026-05 pricing).

### Other experiments

```bash
python run_experiment.py baseline
python run_experiment.py tool-use
python measure.py "results/exp08_*.json" --markdown --output results/exp08_report.md
```

All experiments support checkpoint resume. If interrupted, rerunning continues from `partial_*.json`.

## Research notes

If you want more than the README:

- **[README.ko.md](./README.ko.md)** — Korean full README with the same hypothesis table, plus extra sections on open questions and Korean-language scoring caveats.
- **[docs/reference/researchNotebook.md](./docs/reference/researchNotebook.md)** — Per-experiment notebook in 5W1H format (who / when / where / what / why / how). Korean.
- **[docs/reference/researchNotebook.en.md](./docs/reference/researchNotebook.en.md)** — English mirror of the above (kept in sync; Closed-append-only policy).
- **[docs/reference/conceptFramework.md](./docs/reference/conceptFramework.md)** — The four-axis externalization framework, including unverified candidate axes (Extractor, Reducer, Search Tool, Graph Tool, Evidence Tool, Critic Tool, Large Model Tool / Mixed Intelligence — Exp11 effectively rejected).
- **[docs/reference/namingConventions.md](./docs/reference/namingConventions.md)** — Notation and terminology rules (Stage NX, task-NN, condition slugs, etc.).
- **[docs/reference/scoringHistory.md](./docs/reference/scoringHistory.md)** — Scorer evolution (v0/v2/v3).
- **[docs/reference/failureLabels.md](./docs/reference/failureLabels.md)** — `FailureLabel` enum and failure classification standard.
- **[docs/reference/resultJsonSchema.md](./docs/reference/resultJsonSchema.md)** — Result JSON top-level meta v1.0.
- **Analysis reports** — [Stage 2C H4 recheck](./docs/reference/h4-recheck-analysis-2026-05-02.md) · [Exp11 Mixed Intelligence](./docs/reference/exp11-mixed-intelligence-analysis-2026-05-03.md) · [Exp12 Extractor Role](./docs/reference/exp12-extractor-role-analysis-2026-05-04.md) · [Exp13 Reducer Role](./docs/reference/exp13-reducer-role-analysis-2026-05-05.md) · [Exp14 Search Tool](./docs/reference/exp14-search-tool-analysis-2026-05-05.md) · [Exp09 5-trial drop](./docs/reference/exp09-5trial-drop-analysis-2026-04-30.md).

Plan-level history (decisions and revisions) lives under `docs/plans/` — see `docs/plans/index.md` for the running list (Active + Recently Done).

## Reproduce / Extend

### (a) Run with another model

Change these lines in `experiments/config.py`:

```python
MODEL_NAME = "qwen2.5-7b-instruct"  # or phi-4, llama-3.2-3b, ...
API_BASE_URL = "http://localhost:8080"
```

The llama.cpp server must support `tool_calls`. Check `/props` for `chat_template_caps.supports_tools: true`.

### (b) Add a new tool

Follow `experiments/tools/math_tools.py`, then register the function and schema in `experiments/tools/__init__.py`.

```python
def search_tool(query: str, limit: int = 10) -> list[dict]:
    """BM25/vector hybrid search over your knowledge base."""
    ...

TOOL_SCHEMAS.append({
    "type": "function",
    "function": {
        "name": "search_tool",
        "parameters": {...},
    },
})
TOOL_FUNCTIONS["search_tool"] = search_tool
```

### (c) Add a new role

Follow the existing `SYSTEM_PROMPT`, `CRITIC_PROMPT`, and `JUDGE_PROMPT` patterns in `experiments/system_prompt.py`, then extend the call order using `experiments/orchestrator.py:run_abc_chain` as the reference.

### (d) Add a new taskset item

Append entries to `experiments/tasks/taskset.json` with `id`, `category`, `difficulty`, `prompt`, `expected_answer`, and `scoring_keywords`. For math tasks, solve the item yourself before trusting `expected_answer`; Exp08 exposed a broken ground-truth entry in `math-04`.

## Roadmap

| Horizon | Item | Status |
|---------|------|--------|
| Phase 1 | Exp00~Exp10 — four-axis externalization baseline + cost-aware (Exp10) | ✅ |
| Phase 1 follow-up (2026-04-30) | Taskset 3-FAIL fix + Exp09 5-trial drop analysis + Exp10 v3 rescore | ✅ |
| Stage 2A/2B (2026-04-30) | Infra stabilization (healthcheck/abort + result JSON meta v1.0) + scorer/failure-label reference | ✅ |
| Stage 2C (2026-05-02) | Exp06 H4 recheck on expanded 15-task set — H4 ⚠ Conditionally supported (synthesis +0.140) | ✅ |
| Stage 4 (2026-05-03) | Exp11 Mixed Intelligence (Flash Judge) — H10 ⚠ Inconclusive, effectively rejected (inverse mechanism observed) | ✅ |
| Stage 5 Exp12 (2026-05-04) | Extractor Role (pre-stage) — H11 ⚠ Conditionally supported (Δ=+0.050, d=+0.323, p=0.198 NS). Directional positive observed | ✅ |
| Stage 5 Exp13 (2026-05-05) | Reducer Role (post-stage) — H12 ⚠ Inconclusive, effectively rejected (Δ=−0.053, d=−0.323, p=0.180 NS). Mirrored directional effect to H11 | ✅ |
| Stage 5 Exp14 (2026-05-05) | Search Tool (agent-active BM25 retrieval) — H13 ⚠ Inconclusive, **effectively rejected, statistically significant** (Δ=−0.220, d=−1.000, **p=0.012 SIG**). Mechanism = insufficient retrieval iterations on multi-hop tasks. **Tool-axis sub-distinction**: deterministic computation (H7/H8 +18~23pp) ≠ agent-iterative retrieval (H13 −22pp) | ✅ |
| **Stage 6 (planned)** | **Cross-model replication + LLM-as-judge** — H10/H11/H12/H13 generalization on Llama 3.1 8B / Llama 3.3 70B / Qwen 2.5 7B Q4_K_M (Groq free + local). LLM-as-judge to address H12/H13 keyword-scorer caveats. Plan in progress (`docs/plans/`) | ⏳ |
| Mid-term | Remaining unexternalized axes — Search Tool / Graph Tool / Evidence Tool. Stage 5 SQLite ledger | |
| Mid/long-term | Test the four-layer external knowledge environment (vector / graph) | |
| Long-term | Cross-model reproduction on Qwen / Phi / Llama, structured ablations, and a public write-up | |

## How to Contribute

This is currently a 1-person research notebook. Reproduction by anyone running a different model is one of the highest-value contributions.

| Difficulty | Example | Contribution form |
|------------|---------|-------------------|
| ⭐ 5 min | Typo or documentation fix | PR |
| ⭐⭐ Hours | Reproduce an existing experiment on another model | Issue (Reproduction) |
| ⭐⭐⭐ Days | Add one Tool with tests and an integration run | PR + result report |
| ⭐⭐⭐⭐ Weeks | Design, implement, and evaluate a new Role | PR + research note section |
| ⭐⭐⭐⭐⭐ Months | Long-context stress or cross-model ablation | Acknowledgements top section + possible co-authorship in a future write-up |

Contribution flow:

1. Open an issue with one line of intent, for example: `I'll try reproducing Exp08 with Qwen 2.5 7B`.
2. Fork and run the experiment in your environment.
3. Share code as a PR or results as an issue comment.

## Related work

The "externalize the LLM" framing is not unique to this project. Adjacent or overlapping ideas:

- **Externalization in LLM Agents** (Zhou et al., 2026)¹ — A unified review proposing four externalization axes (memory / skills / protocols / harness engineering). Gemento was developed independently — out of practical context/memory problems hit while building secall and tunaFlow — and only later did the author become aware of this preprint. The four-axis split (Tattoo / Tools / Role / Orchestrator) is best read as **independent convergence** with that line of work, not as a derivation from it. Axis mapping differs (Gemento separates Role and Orchestrator explicitly; Zhou et al. fold control into harness engineering).
- **LightMem** (Fang et al., 2026)² — Lightweight memory-augmented generation with three-stage memory (sensory / short-term / long-term, sleep-time consolidation). Focused on long-term retrieval across sessions; Gemento is closer to *working state* across loops within a single task, not memory across sessions.
- **StateFlow** (Wu et al., 2024)³ — Conceptualizes complex task-solving as state machines, externalizing control flow from LLM. Conceptually adjacent to Gemento's Orchestrator axis; Gemento adds explicit role separation (A/B/C) and Tattoo schema on top.
- **Chain-of-Agents** (Zhang et al., 2024)⁴ — Sequential multi-agent reading of long inputs (worker agents segment + manager synthesizes). Gemento's A→B→C pipeline shares this structure but uses *the same base model* for all roles, separated only by prompt and validation contract.

What is contributed here, and what is **not**:

- Contributed: a measured workbook of small-LLM (Gemma 4 E4B, effective 4B parameters) behavior across the four axes, with reproducible numbers and sampling parameters.
- Not contributed: a new architecture, a new training method, or a claim that small LLMs replace large ones. Gemento is a structural workflow harness on top of an unmodified open-weight model.

---
¹ Zhou, C., Chai, H., Chen, W., et al. (2026). *Externalization in LLM Agents: A Unified Review of Memory, Skills, Protocols and Harness Engineering*. [arXiv:2604.08224](https://arxiv.org/abs/2604.08224).
² Fang, J., Deng, X., Xu, H., et al. (2026). *LightMem: Lightweight and Efficient Memory-Augmented Generation*. ICLR 2026. [arXiv:2510.18866](https://arxiv.org/abs/2510.18866).
³ Wu, Y., et al. (2024). *StateFlow: Enhancing LLM Task-Solving through State-Driven Workflows*. [arXiv:2403.11322](https://arxiv.org/abs/2403.11322).
⁴ Zhang, Y., Sun, R., Chen, Y., Pfister, T., Zhang, R., Arik, S. Ö. (2024). *Chain of Agents: Large Language Models Collaborating on Long-Context Tasks*. NeurIPS 2024. [arXiv:2406.02818](https://arxiv.org/abs/2406.02818).

## Acknowledgements

- *Memento* (Christopher Nolan, 2000) — original metaphor of external memory aids. Four-axis externalization is the structured-schema cousin of Leonard's tattoos and polaroids.
- secall · tunaflow — the practical origin. The context and memory problems I ran into while building those tools are what made this project necessary.

## License

[MIT](./LICENSE) — fork, modify, redistribute, and use commercially. Just keep the copyright notice.
