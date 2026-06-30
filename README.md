# gemento

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Status](https://img.shields.io/badge/Status-active-success)]()
[![Last commit](https://img.shields.io/github/last-commit/hang-in/gemento)](https://github.com/hang-in/gemento/commits/main)
[![Paper](https://img.shields.io/badge/Paper-draft%20in%20progress-orange)](docs/paper/draft.md)

> **You can't make a small LLM bigger.  
> But you can move its missing memory, computation, validation, and control outside the model.**

gemento is an experiment repository that measures how far a small local LLM (like Gemma 4 E4B) can be carried on tasks it struggles to solve alone, using **external state + tools + role separation + orchestration**.

It is not a project that builds or trains a new model. It is a **one-person research notebook and a reproducible experiment harness** that lays a structured workflow on top of an existing small model and verifies the effect through repeated experiments.

*Last updated: 2026-06-30*  
📚 Korean version: [README.ko.md](./README.ko.md)

---

## At a glance

gemento's core observations are simple.

| Question | Observed result |
|---|---|
| Do small LLMs improve when given a repeated structure? | Exp02: 1-shot 50% → 8-loop 94.4% |
| Can they self-validate? | Exp03: error detection 0% |
| Does splitting roles improve validation? | Exp035: cross-validation 80% |
| Do compute tools help math problems? | Exp08b: math-04 0% → 100% |
| Is a router better than stuffing a whole log into the prompt? | Exp15/16: on large logs, router + mandatory + retry is the most stable combination |
| Does adding a stronger model as Judge always help? | Exp11: it got *worse* — a strong Judge can cut off a weak model's self-discovery |

These are not general laws. Most are **results for Gemma 4 E4B on a custom taskset**, and several hypotheses are statistically non-significant. This repository does **not** claim that small models replace large ones.

---

## What this repo is

gemento provides:

- experiment code to reproduce small-local-LLM workflows
- experiment records comparing external state, tools, role separation, and control
- a research notebook that includes the failures too
- a baseline you can reproduce — or refute — with other models and tasks

It is **not**:

- a new LLM architecture
- a new training method
- a claim that it replaces frontier models
- a claim that it always beats RAG
- a production agent framework

---

## Why gemento

A small LLM is not a miniature of a large one. Small models have their own strengths and clear weaknesses.

gemento does not try to fix those weaknesses *inside* the model. It moves four things *outside* it.

| Axis | Problem inside the model | gemento's handling |
|---|---|---|
| State | forgets prior judgments and evidence | keeps them in a structured JSON state (Tattoo) |
| Tools | fakes computation/search with reasoning | uses calculator, linprog, grep/read tools |
| Role | can't catch its own errors when self-validating | separates Proposer, Critic, Judge |
| Control | unstable about when to stop or repeat | uses a Python orchestrator together with a Judge |

In one sentence:

> Leave memory in the environment, delegate computation to tools, and assign validation to a different role.

---

## Core idea: externalization

gemento's metaphor is the film *Memento*.

Leonard can't trust his memory, so he relies on external devices — tattoos, photos, notes, phone calls. gemento is similar: it does not trust the small LLM's internal memory and judgment as-is, and fixes important information in external structure.

| Memento element | gemento counterpart | Externalized |
|---|---|---|
| tattoo | Tattoo JSON | state |
| polaroid | `evidence_ref` | evidence |
| phone call | tool call | action |
| supporting characters | Role Agent | perspective |
| repeated investigation | Orchestrator loop | control |

The difference: gemento uses explicit schemas and a fixed call order, not accidental notes.

---

## Architecture

```text
            Small LLM
               │
        ┌──────┴──────┐
        │  internal   │
        │   limits    │
        └──────┬──────┘
               │
 ┌─────────────┼─────────────┐
 ▼             ▼             ▼
Tattoo        Tools        Roles
state store  compute/search A/B/C separation
               │
               ▼
        Orchestrator
        loop · stop · validate
```

gemento splits Critic into two kinds:

| | Critic Tool | Critic Agent |
|---|---|---|
| Nature | deterministic verification | semantic critique |
| Example | JSON schema, citation resolve, file-exists check | logical contradiction, weak evidence, conflicting interpretation |
| Implemented as | Python/Rust function | LLM role prompt |

And so is the Orchestrator:

| | Python Orchestrator | Judge Role |
|---|---|---|
| Nature | deterministic safety net | non-deterministic meta-judgment |
| Owns | max cycles, schema validation, tool loop | convergence decision, retry, accept/reject |
| Role | prevents runaway | drives the judgment flow |

They are not substitutes. Python is the safety net; the Judge is the decision-maker.

---

## Key results

### 1. Loops worked

| Experiment | Before | After | Δ | Meaning |
|---|---:|---:|---:|---|
| Exp02 | 50% | 94.4% | +44.4pp | forced loops beat single-pass |
| Exp10 | 41.3% | 78.1% | +36.8pp | ABC loops improve a 9-task cost-aware benchmark |

Interpretation: the same model produces very different results when asked to answer in one shot vs. when external structure pushes it step by step.

Caveat: the Exp10 comparison is on a 9-task benchmark. There is a condition where it scored above a one-call Gemini 2.5 Flash baseline, but wall time was ~20× longer. Do not read it as a general superiority claim.

---

### 2. Self-validation failed; role separation worked

| Experiment | Condition | Result |
|---|---|---|
| Exp03 | model validates its own answer | error detection 0/15 |
| Exp035 | a separate Critic role validates | error detection 12/15, 80% |

*Exp035 is an interstitial experiment between Exp03 and Exp04 (a cross-validation gate) — not the "35th" experiment. New experiments use letter suffixes instead (see `docs/reference/namingConventions.md` §5).*

Interpretation: separating "the role that answers" from "the role that criticizes" changed the failure-recovery rate — even with the same model.

---

### 3. Tools helped or hurt depending on the problem type

| Experiment | Tool type | Result |
|---|---|---|
| Exp08 / Exp08b | deterministic compute (calculator, linprog) | large improvement |
| Exp14 | agent-active BM25 retrieval | worse than a 32K-context baseline |
| Exp15–16 | Redis context router + grep/read tools | better on large logs, overhead on small logs |

Interpretation: "add a tool and it gets better" is false. Results depend on the tool's nature, the call count, the model's tool-use ability, and the input size.

In Exp14 the search tool failed to iterate enough on multi-hop tasks and lost accuracy. Conversely in Exp15–16 the context router was effective exactly where stuffing the whole log broke down.

---

### 4. A stronger Judge wasn't always better

In Exp11 a Gemini 2.5 Flash Judge underperformed an all-Gemma baseline.

Plausible explanations:

- the strong Judge cut off the weak model's intermediate exploration too early
- the Tattoo schema and the Judge's judgment style didn't match
- the chain the weak model was discovering on its own got severed

So gemento's current direction is **less "stack a stronger model on top," more "split roles better and organize the needed input better."**

---

## Hypotheses

| ID | Topic | Verdict | Summary |
|---|---|---|---|
| H1 | Orchestrator loop | Supported | multi-step loops beat single-pass |
| H2 | Self-check | Rejected | self-validation failed |
| H3 | Role Critic | Supported | role-separated validation recovered errors |
| H4 | ABC role separation | Conditional | positive signal in the synthesis category |
| H7/H8 | Compute tools | Supported | calculator/linprog compensate for math limits |
| H9 | Tattoo long-context | Conditional | beats Solo-dump under long input in some conditions |
| H10 | Strong Judge | Inconclusive / eff. rejected | mixed intelligence got worse |
| H11 | Extractor | Conditional | pre-stage input organization is positive-leaning |
| H12 | Reducer | Inconclusive / eff. rejected | post-stage compression can lose information |
| H13 | Search Tool | Inconclusive / eff. rejected | agent-active retrieval under-iterates on multi-hop |
| H14 | Cross-model | Conditional | direction generalizes across families (with caveats) |
| H15 | Context Router | Conditional | effective on large logs, overhead on small ones |
| H16b/c | mandatory prompt + retry | Supported | output stabilization for the large-log router (e4b per-attempt 27%→83%; +retry ~100%) |
| H17 | complexity ceiling | Partial | e4b+router scales to multi-hop/aggregation/distractor (baseline ~92%); but the mandatory stack is a failure-mode-specific fix, not a general booster (−3pp on hard tasks) |

Detailed numbers and analysis live in the per-experiment reports under `docs/reference/`.

---

## Reproducibility notes

Check these conditions before quoting any number:

- Headline results are for Gemma 4 E4B on a custom benchmark.
- Some experiments are statistically non-significant at n=15 paired tasks.
- The keyword scorer cannot fully separate real quality differences from answer-style differences.
- The Gemini 2.5 Flash comparison is limited to a 9-task cost-aware benchmark.
- Context Router results depend heavily on input size and the model's tool-use ability (e4b uses agent-driven *pull*; ~2B e2b is below the tool-use floor and needs orchestrator-driven *push*).

The numbers here are "experiments that show what's possible," not generalized benchmark conclusions.

---

## Quickstart

### 1. Install

```bash
git clone https://github.com/hang-in/gemento.git
cd gemento

python3.14 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 2. Configure the inference server

Set an OpenAI-compatible server address in `experiments/config.py`.

```python
MODEL_NAME = "gemma4-e4b"
API_BASE_URL = "http://localhost:8080"
```

If you use a llama.cpp server, it must support `/v1/chat/completions` and `tool_calls`.

Check the server:

```bash
curl -s http://localhost:8080/v1/models | jq .data[].id
```

### 3. Smoke test

```bash
cd experiments
python tools/smoke_test.py
```

Expected:

```text
SMOKE TEST PASSED: math-04 answer=..., tool_calls=...
```

### 4. Run your first experiment

A short baseline:

```bash
python run_experiment.py baseline
```

A tool-use experiment:

```bash
python run_experiment.py tool-use
python measure.py "results/exp08_*.json" --markdown --output results/exp08_report.md
```

Experiments support checkpoints. If interrupted, rerunning continues from `partial_*.json`.

---

## Running other models

Change only the model name and server address in `experiments/config.py`.

```python
MODEL_NAME = "qwen2.5-7b-instruct"
API_BASE_URL = "http://localhost:8080"
```

Notes:

- the server must support `tool_calls`.
- tool-calling ability can differ a lot between models on the same task.
- small models may do better with an orchestrator-forced *push* than with the agent picking tools itself (*pull*).

---

## Adding a new Tool

Follow the structure in `experiments/tools/math_tools.py`.

```python
def search_tool(query: str, limit: int = 10) -> list[dict]:
    """BM25/vector hybrid search over your knowledge base."""
    ...
```

Register in:

- `experiments/tools/__init__.py`
- `TOOL_FUNCTIONS`
- `TOOL_SCHEMAS`

Note: adding a tool does not automatically improve performance. As in Exp14, if the agent doesn't iterate enough it can get worse.

---

## Adding a new Role

See the existing role prompts in `experiments/system_prompt.py`.

Built-in roles:

- Proposer: proposes an answer
- Critic: criticizes errors and evidence
- Judge: decides convergence, retry, termination
- Extractor: pre-extracts claims/entities from the input
- Reducer: post-processes/cleans up the result

The call order is in `experiments/orchestrator.py:run_abc_chain`.

In current experiments a pre-stage Extractor looked safer than a post-stage Reducer — but this too is not a settled conclusion and needs per-model/task replication.

---

## Adding a new taskset item

Append entries to `experiments/tasks/taskset.json`.

Required fields:

```json
{
  "id": "task-id",
  "category": "logic",
  "difficulty": "medium",
  "prompt": "...",
  "expected_answer": "...",
  "scoring_keywords": ["..."]
}
```

Note: for math tasks, first verify that `expected_answer` itself satisfies the constraints. In Exp07/Exp08, a broken ground-truth entry changed the experiment's conclusion.

---

## Repository layout

| Path | Contents |
|---|---|
| `docs/reference/conceptFramework.md` | the four-axis externalization concept |
| `docs/reference/researchNotebook.md` | the main research notebook |
| `docs/reference/researchNotebook.en.md` | English mirror (Closed-append-only) |
| `docs/reference/results/` | per-experiment result docs |
| `docs/reference/scoringHistory.md` | scorer evolution |
| `docs/reference/failureLabels.md` | failure classification |
| `docs/reference/resultJsonSchema.md` | result JSON schema |
| `docs/plans/` | experiment plans and progress log |
| `docs/agents/` | role definitions |
| `experiments/schema.py` | Tattoo schema |
| `experiments/system_prompt.py` | per-role system prompts |
| `experiments/orchestrator.py` | loop, tool call, ABC chain |
| `experiments/measure.py` | result scoring |
| `experiments/tools/math_tools.py` | calculator, linprog, etc. |

---

## Roadmap

| Stage | Status | Contents |
|---|---|---|
| Phase 1 | done | Exp00~Exp10, four-axis baseline |
| Stage 2 | done | infra stabilization, scorer/failure-label cleanup |
| Stage 5 | done | Extractor, Reducer, Search Tool ablation |
| Stage 6 | done | cross-model replication, LLM-as-judge auxiliary check |
| Stage 7 | done | Context Router, mandatory prompt, retry combination |
| Mid-term | planned | Graph Tool, Evidence Tool |
| Long-term | planned | more systematic cross-model ablation and a technical report |

---

## How to contribute

gemento is currently close to a one-person research notebook. Still, reproductions, counterexamples, and documentation improvements are all valuable.

| Effort | Example | Form |
|---|---|---|
| 5 min | typo, README fix | PR |
| hours | reproduce an existing experiment on another model | Issue |
| days | implement a new Tool + tests | PR + result report |
| weeks | design/evaluate a new Role | PR + research note |
| months | systematic ablation | shared research-record review |

Flow:

1. Open an Issue describing what you'll try.
2. Experiment in a fork.
3. Share code changes as a PR; share reproduction results as an Issue comment or gist.

---

## Related work

gemento's "externalize LLM cognition" direction is not an isolated idea. It is adjacent to:

- **Externalization in LLM Agents** (Zhou et al., 2026) — a unified review of externalization from the memory / skills / protocols / harness-engineering angle. [arXiv:2604.08224](https://arxiv.org/abs/2604.08224)
- **LightMem** (Fang et al., 2026) — lightweight memory-augmented generation. [arXiv:2510.18866](https://arxiv.org/abs/2510.18866)
- **StateFlow** (Wu et al., 2024) — structures LLM task-solving as a state machine. [arXiv:2403.11322](https://arxiv.org/abs/2403.11322)
- **Chain-of-Agents** (Zhang et al., 2024) — long inputs split across worker agents, synthesized by a manager. [arXiv:2406.02818](https://arxiv.org/abs/2406.02818)

gemento differs in:

- measuring around a small model like Gemma 4 E4B
- splitting one base model into A/B/C by role only
- using an explicit working-state schema (Tattoo)
- recording failure modes and scoring errors in the notebook, not just successes

gemento was developed independently — out of practical context/memory problems hit while building secall and tunaFlow — and is best read as *independent convergence* with the above line of work, not a derivation from it.

---

## Acknowledgements

- *Memento* (Christopher Nolan, 2000) — the core metaphor of external memory aids
- secall · tunaflow — the real problem space gemento started from

---

## License

[MIT](./LICENSE) — fork, modify, redistribute, and use commercially. Just keep the copyright notice.

---

## Questions & suggestions

Open a GitHub Issue or Discussion. Reproductions and counterexamples are welcome too.
