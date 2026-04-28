---
type: reference
status: completed
updated_at: 2026-04-29
author: Codex CLI (Windows)
recipient: Architect Opus
---

# Handoff: Exp10 v2 Results and Math-04 Targeted Debug

## 1. Current State
- The Windows Exp10 v2 full rerun completed: `540/540` trials.
- Result file: `experiments/exp10_reproducibility_cost/results/exp10_reproducibility_cost_20260428_175247.json`.
- The earlier invalid file remains present but should not be used as the canonical v2 result: `exp10_reproducibility_cost_20260427_130235.json`.
- A targeted `math-04` + `gemma_8loop` debug rerun also completed: `20/20` trials.

## 2. Full Exp10 v2 Summary

| condition | n | mean accuracy | errors | null final_answer | cost_usd |
|---|---:|---:|---:|---:|---:|
| `gemma_8loop` | 180 | 0.7093 | 19 | 19 | 0.000000 |
| `gemma_1loop` | 180 | 0.4130 | 0 | 11 | 0.000000 |
| `gemini_flash_1call` | 180 | 0.6130 | 4 | 4 | 0.014164 |

Key interpretation:
- `gemma_8loop` is strongest overall in this run, but its aggregate is depressed by a concentrated `math-04` failure cluster.
- `gemini_flash_1call` finished all 180 slots but had 4 timeout/null failures on `logic-04`.
- `gemma_1loop` had no explicit errors, but multiple low-accuracy/null clusters.

## 3. Math-04 Finding

`math-04` explains the largest `gemma_8loop` anomaly:

| condition | n | mean accuracy | errors | null final_answer |
|---|---:|---:|---:|---:|
| `gemma_8loop` | 20 | 0.0000 | 15 | 15 |
| `gemma_1loop` | 20 | 0.1667 | 0 | 2 |
| `gemini_flash_1call` | 20 | 0.6667 | 0 | 0 |

Diagnosis from Codex Windows:
- The `math-04` task is a linear programming problem.
- `system_prompt.py` tells math/LP tasks to use tools such as `linprog`.
- The original Exp10 `gemma_8loop` path called `run_abc_chain(...)` without `use_tools=True`, so the model often described or attempted tool use but could not execute it.
- A targeted runner enabling tools for this task produced a successful 20-trial result:
  - file: `experiments/exp10_reproducibility_cost/results/exp10_math04_8loop_debug_20260428_205650.json`
  - `20/20` trials completed
  - mean accuracy: `1.0000`
  - errors: `0`
  - null final answers: `0`
  - average cycles: `7.50`
  - average duration: `9.18 min`; median duration: `7.98 min`
  - answer distribution: all 20 returned `{'X': 31, 'Y': 10, 'Z': 37, 'profit': 3060}`.

## 4. Local Patches in Rerun Worktree

The rerun worktree is intentionally dirty and should be reviewed before merging:
- `experiments/config.py`: Windows local LM Studio endpoint/model settings.
- `experiments/orchestrator.py`: LM Studio safe mode plus more lenient JSON extraction for local model outputs.
- `experiments/exp10_reproducibility_cost/run.py`: raw A/B/C debug logging and safer single-call parsing.
- `experiments/exp10_reproducibility_cost/run_math04_8loop_debug.py`: new targeted runner for `gemma_8loop` + `math-04` with tools enabled.
- `watch-exp10.ps1` / `experiments/watch_exp10.ps1`: local monitoring helpers.

Do not treat all local changes as production-ready without review. The targeted runner is diagnostic by design and writes separate result files.

## 5. Targeted Debug Command Used

The completed targeted rerun was produced with:

```powershell
cd D:\privateProject\gemento_rerun_v2
D:\privateProject\gemento\.venv\Scripts\python.exe -u .\experiments\exp10_reproducibility_cost\run_math04_8loop_debug.py --trials 20 --fresh 2>&1 |
  Tee-Object -FilePath .\experiments\exp10_reproducibility_cost\math04_8loop_debug.log
```

`partial_exp10_math04_8loop_debug.json` was cleared after completion. The run log is `experiments/exp10_reproducibility_cost/math04_8loop_debug.log`.

Note: `resource module not available on Windows` appeared when `linprog` was used. It did not indicate failure in this run.

## 6. Recommended Opus Review Questions

1. Should Exp10 official analysis use the raw 540 result as-is, or report an adjusted sensitivity analysis replacing `gemma_8loop math-04` with the targeted tool-enabled rerun?
2. Should `gemma_8loop` enable tools for all math tasks in future Exp10-style runs, or should the current v2 result remain a no-tools condition for strict comparability?
3. Should `math-04` expected answer mention alternate optimal plans? The score currently keys on `31`, `37`, and `3060`, while the LP has multiple optimal points with profit 3060.
4. Should Gemini Flash `logic-04` timeout/null cases be retried or kept as cost/reliability failures?

---
Codex CLI (Windows), 2026-04-29
