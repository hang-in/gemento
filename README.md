# Gemento

> **Gemento is an experimental harness, not a new architecture or a paper.** It tests whether small local LLMs can run long workflows when memory, tools, roles, and control are externalized.

📚 Korean version: [README.ko.md](./README.ko.md)

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
| **H4** | [Role externalization synergy] A-B-C role separation outperforms repeated single-agent iteration | ⚠ Inconclusive (Exp06 9-task × 45-trial reconciled comparison: v1 +0.015 / v2 +0.067, both slightly favor Solo. Original "+22.6pp" not reproducible. Structural difference confirmed but accuracy Δ not observed — needs expanded task set) | Exp06 |
| **H5** | [Orchestrator ceiling effect] Raising `MAX_CYCLES` improves accuracy | ⚠️ Partially rejected - the ceiling was not the limit; actual saturation appeared around `actual_cycles ≈ 7` | Exp07 |
| **H6** | [Role externalization refinement] Phase-specialized prompts outperform the baseline | ✅ Conditionally supported (+5-6pp in long loops) | Exp07 |
| **H7** | [Tool externalization] External math tools compensate for E4B's calculation limits | ✅ Supported (+18.3pp, math-04 0→80%) | Exp08 |
| **H8** | [Tool externalization stability] Error hints and mandatory tool rules reduce tool neglect and operator confusion | ✅ Supported (neglect 0%, calculator 100%, math-04 0→100%, +23.3pp) | Exp08b |
| **H9a** | [Tattoo externalization, physical limit] ABC+Tattoo (chunked) outperforms solo dump under long context | ✅ Supported (+68.3pp, Solo 0% → ABC 100% at Large 20K) | Exp09 |
| **H9b** | [Distinctiveness] ABC+Tattoo contributes something beyond a RAG baseline | ⚠️ Conditionally supported (overall +3.3pp; strongly ahead on Large 3-hop, behind on small tasks) | Exp09 |
| **H9c** | [Error mode difference] ABC fails differently from Solo and RAG | ✅ Supported (Solo: `format_error`, RAG: `wrong_synthesis`, ABC: `evidence_miss` + `wrong_synthesis`) | Exp09 |

## What worked / What didn't

- Exp02 v2: 50% to 94.4% after forcing 8 loops on the same E4B model.
- Exp03: self-validation detected 0 out of 15 planted errors.
- Exp035: role-separated cross-validation recovered to 80%.
- Exp08b: math tool calls plus error-message hints moved math-04 from 0% to 100%.
- Exp09: on Large 20K long-context tasks, Solo dump scored 0%, RAG scored 67%, and ABC+Tattoo scored 100%.
- Exp10: same Gemma 4 E4B went from 41.3% (1-loop) to 78.1% (8-loop ABC) on a 9-task / 540-trial cost-aware comparison. The same ABC condition matched Gemini 2.5 Flash 1-call by +19pp (78.1% vs 59.1%) at zero per-trial API cost, trading off ~20× wall time. ABC infrastructure had 4 trial-level JSON parse fails (early-stop pattern, see `docs/reference/exp10-v3-abc-json-fail-diagnosis.md`).

What clearly did **not** work was expecting the same model to notice its own failure mode without a role change. The most useful result in this repository is probably negative: the model does not reliably criticize itself, even when it can criticize the same reasoning from another role.

## Why this matters

If you are working on externalization for small models, structured state, or multi-role validation, this repo is meant to be a public coordinate rather than a closed notebook. It is MIT-licensed on purpose. I would rather have competing measurements, forks, and disagreements in public than keep this siloed until it looks polished.

## Quickstart

### Environment

```bash
git clone https://github.com/hang-in/gemento.git
cd gemento
python3.14 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Connect an inference server

Set `API_BASE_URL` in `experiments/config.py` to a llama.cpp server that exposes OpenAI-compatible `/v1/chat/completions` and supports `tool_calls`. For local use, `http://localhost:8080` is the expected default.

```bash
curl -s $API_BASE_URL/v1/models | jq .data[].id
```

Expected: `gemma4-e4b` or the model ID you loaded.

### Smoke test

```bash
cd experiments
python tools/smoke_test.py
```

Expected: `SMOKE TEST PASSED: math-04 answer=..., tool_calls=...`

### First run

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
- **[docs/reference/researchNotebook.en.md](./docs/reference/researchNotebook.en.md)** — English mirror of the above (kept in sync).
- **[docs/reference/conceptFramework.md](./docs/reference/conceptFramework.md)** — The four-axis externalization framework, including unverified candidate axes (Extractor, Reducer, Search Tool, Graph Tool, Evidence Tool, Critic Tool).

Plan-level history (decisions and revisions) lives under `docs/plans/` — see `docs/plans/index.md` for the running list.

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

| Horizon | Item |
|---------|------|
| Short-term | Exp10 (cost-aware reproducibility) completed — see `docs/reference/results/exp-10-reproducibility-cost.md`. Next candidates: math-* `use_tools=True` policy unification + v3 re-run, logic category multi-stage / tooling, scorer extension to Exp00–09 (low priority — `logic-04` absent in those task subsets). |
| Mid-term | Add missing axes: Extractor/Reducer roles and Search Tool integration |
| Mid/long-term | Test the four-layer external knowledge environment |
| Long-term | Cross-model reproduction on Qwen / Phi / Llama, structured ablations, and a public write-up |

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

- **Externalization frame** — A 2026-04 arXiv preprint¹ proposes a general framework for externalizing memory, reasoning, and verification away from the model. Gemento was developed independently — out of practical context/memory problems hit while building secall and tunaFlow — and only later did the author become aware of this preprint. The four-axis split (Tattoo / Tools / Role / Orchestrator) is best read as **independent convergence** with that line of work, not as a derivation from it.
- **LightMem**² — Long-term memory externalization for LLMs. Focused on retrieval and key-value memory; Gemento is closer to *working* state across loops, not retrieval against past sessions.
- **ESAA (Externally Stateful Agentic Architectures)**³ — Treats the agent as a state machine with external state. Conceptually adjacent; Gemento adds explicit role separation (A/B/C) and tool integration on top of the same idea.
- **Chain-of-Agents**⁴ — Sequentially passes a long input across multiple agents. Gemento's A→B→C pipeline shares this structure but uses *the same base model* for all roles, separated only by prompt and validation contract.

What is contributed here, and what is **not**:

- Contributed: a measured workbook of small-LLM (Gemma 4 E4B, effective 4B parameters) behavior across the four axes, with reproducible numbers and sampling parameters.
- Not contributed: a new architecture, a new training method, or a claim that small LLMs replace large ones. Gemento is a structural workflow harness on top of an unmodified open-weight model.

---
¹ A 2026-04 arXiv preprint on externalization frame for LLM agents — *citation pending; the author has not directly verified the preprint, the reference is the GPT-discovered framing only*.
² LightMem (long-term memory module for LLMs) — *citation pending; needs bibliographic verification*.
³ ESAA — Externally Stateful Agentic Architectures — *citation pending; needs bibliographic verification*.
⁴ Chain-of-Agents — sequential multi-agent reading — *citation pending; needs bibliographic verification*.

## Acknowledgements

- *Memento* (Christopher Nolan, 2000) — original metaphor of external memory aids. Four-axis externalization is the structured-schema cousin of Leonard's tattoos and polaroids.
- secall · tunaflow — the practical origin. The context and memory problems I ran into while building those tools are what made this project necessary.

## License

[MIT](./LICENSE) — fork, modify, redistribute, and use commercially. Just keep the copyright notice.
