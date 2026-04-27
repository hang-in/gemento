---
type: handoff
status: in_progress
updated_at: 2026-04-27
author: Architect Opus
recipient: Codex CLI (Windows)
task: Exp10 Recovery & Re-execution
---

# Handoff: Exp10 Recovery & Re-execution (Clean Run)

## Summary
Exp10 invalid trial results (360 null / 540 total) were caused by Windows working tree corruption: `run.py` had missing return blocks in `trial_gemma_1loop()` and `trial_gemini_flash()` functions. The Mac version is clean. This handoff provides step-by-step recovery.

## Pre-flight Checklist

1. **Verify current state**:
   ```powershell
   cd /path/to/gemento
   git status
   git diff experiments/exp10_reproducibility_cost/run.py
   ```
   Confirm that `trial_gemma_1loop()` (line ~117) and `trial_gemini_flash()` (line ~149) are missing return statements.

2. **Restore from origin/main**:
   ```powershell
   git checkout origin/main -- experiments/exp10_reproducibility_cost/run.py
   ```
   Verify restoration:
   ```powershell
   git diff experiments/exp10_reproducibility_cost/run.py
   ```
   Should show NO diff (run.py now matches origin/main).

3. **Clean partial checkpoint**:
   ```powershell
   rm experiments/exp10_reproducibility_cost/results/partial_exp10_reproducibility_cost.json
   ```
   Verify:
   ```powershell
   ls experiments/exp10_reproducibility_cost/results/
   ```
   Should show only the old invalid result file (exp10_reproducibility_cost_20260427_*.json), NOT the partial checkpoint.

4. **Verify clean state**:
   ```powershell
   git status
   ```
   Expected: working tree clean (no uncommitted changes).

## Execution Command

```powershell
cd /path/to/gemento
..\.venv\Scripts\python experiments/exp10_reproducibility_cost/run.py --trials 20
```

**Expected output**:
- 540 trials total (3 conditions × 9 tasks × 20 trials)
- Execution time: ~2-3 hours (depends on LM Studio + Gemini latency)
- Progress: `[1/540] gemma_8loop | math-01 | trial 1` → `[540/540] gemini_flash_1call | logic-04 | trial 20`
- Final log: `→ Result saved: experiments/exp10_reproducibility_cost/results/exp10_reproducibility_cost_YYYYMMDD_HHMMSS.json`

## Post-execution Validation

After execution completes:

1. **Verify result JSON**:
   ```powershell
   python -c "
   import json
   with open('experiments/exp10_reproducibility_cost/results/exp10_reproducibility_cost_*.json') as f:
       data = json.load(f)
   trials = data['trials']
   valid = sum(1 for t in trials if t['final_answer'] is not None)
   null_count = len(trials) - valid
   print(f'Total: {len(trials)}, Valid: {valid}, Null: {null_count}')
   "
   ```
   Expected: Total=540, Valid=540, Null=0 (all trials successful).

2. **Quick accuracy sanity check**:
   - gemma_8loop: expect mean accuracy ~0.50-0.70 (with Korean penalty present)
   - gemma_1loop: expect mean accuracy ~0.40-0.60
   - gemini_flash_1call: expect mean accuracy ~0.60-0.80

3. **Commit and push** (optional, Architect will analyze first):
   ```powershell
   git add experiments/exp10_reproducibility_cost/results/
   git commit -m "Exp10 recovery: re-run with clean run.py (540 valid trials)"
   git push origin main
   ```
   Or just notify Architect of completion via this channel.

## Known Constraints

- **Gemini API**: Requires active credentials in `.env` (should be inherited from secall)
- **LM Studio**: Must be running locally on Windows at default port (8000 by default)
- **Rate limit**: 1 second sleep per Gemini call (safety margin for free tier)
- **Token metering**: ABC chain (gemma_8loop) returns input/output tokens as 0 (token counting not supported for local loop)

## Abort Conditions

If any of these occur, **STOP and notify Architect immediately**:
1. Import errors (missing dependencies)
2. Gemini API authentication failure
3. LM Studio connection timeout
4. Keyboard interrupt (Ctrl+C) — do NOT discard partial results, notify Architect of last completed trial

## Success Criteria

Execution completes with:
- 540 trials recorded in final JSON
- 0 null final_answer values
- All accuracy scores numeric (not NaN or error strings)
- Checkpoint file deleted automatically

---

**Handoff prepared by**: Architect Opus  
**Date**: 2026-04-27  
**Next step**: Once Codex confirms execution complete, proceed to cost/reproducibility analysis.
