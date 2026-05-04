# English Notebook Section Template (reference)

For appending to `docs/reference/researchNotebook.en.md`. **APPEND-ONLY**: this file's existing entries (table rows, prior `## Exp##` sections, every other line) must remain byte-identical except for the `updated_at` frontmatter line.

## Insertion algorithm (safe pattern)

1. Read the entire file.
2. Locate the line `## Change History` near the bottom.
3. The `---` separator line directly above `## Change History` is the insertion anchor.
4. Use `Edit` (NOT `Write`) with:
   - `old_string`: the `---\n\n## Change History` pair (3 lines)
   - `new_string`: `---\n\n## Exp{NN} — {name} note ({YYYY-MM-DD})\n\n{body}\n\n---\n\n## Change History`
5. After editing, `Read` the file again and verify:
   - The hypothesis table row count is unchanged
   - All prior `## Exp##` sections retain their original opening line
   - The new section appears once, immediately before `## Change History`

## Section body template

The body section between the inserted heading and the trailing `---` should follow this shape (English prose, ~1 paragraph per item):

```markdown
A follow-up experiment (`<plan-slug>`) tested **H##** — <hypothesis statement in English, one sentence>. <One-sentence motivation tying back to the prior experiment's verdict>.

Conditions: <baseline_name> (<role config>) vs <treatment_name> (<role config>) × <M> tasks × <K> trials = <total> trials. <One-line note on infrastructure: Stage 2A healthcheck/abort + Stage 2B FailureLabel + Stage 2C tattoo_history fix preserved + any new orchestrator hook added>.

Results (v3 scoring, <total> trials):
- <baseline_name>: mean_acc=0.XXXX, median=X.XXXX, err+null=N, avg cycles=X.X, avg dur=XXXs, cost=$0
- **<treatment_name>**: mean_acc=**0.XXXX**, median=X.XXXX, err+null=N, avg cycles=X.X, avg dur=XXXs, cost=**$X.XXXX**

Δ(<treatment> − baseline) = **±0.0XXX** (<positive/negative — comparison to prior experiment if relevant>). Statistics (n=<M> paired): Wilcoxon p=X.XXX, paired t p=X.XXX (<NOT SIGNIFICANT — power-limited / SIGNIFICANT>). Cohen's d = **±0.XXX** (<small/medium/large> effect, <positive/negative>). Bootstrap 95% CI Δ: [±0.XXX, ±0.XXX].

Category-level Δ(<treatment>−baseline):
- math: ±0.XXX
- **logic: ±0.XXX** <⬆/⬇ if notable>
- **synthesis: ±0.XXX** <annotation>
- planning: ±0.XXX

**H## verdict (Architect)**: ⚠ **<English verdict>**. <One-paragraph reasoning citing Δ, Cohen's d, mechanism evidence>.

<Optional: Decisive contrast section — table comparing this Exp with the prior one if the framework's evolution direction is being established>

Limitations: <power, sample, axis-not-exercised, schema-mismatch caveats>.

Detail: `docs/reference/exp##-<slug>-analysis-YYYY-MM-DD.md`. Results: `experiments/exp##_<slug>/results/<file>.json` (<baseline>) + `<file>.json` (<treatment>).

The hypothesis table above (H1~H{prev}) remains unchanged (Closed-append-only policy). H##'s entry is a new addition only.
```

## verdict mapping (English vocabulary)

Use exactly these phrases — the notebook conventions depend on consistent terminology:

| 한국어 | English | with `⚠` prefix? |
|---|---|---|
| 채택 | Supported | no |
| 조건부 채택 | Conditionally supported | yes |
| 미결 | Inconclusive | yes |
| 미결 (실효적 기각) | Inconclusive (effectively rejected) | yes |
| 미결 (실효적 채택) | Inconclusive (effectively supported) | yes |
| 기각 | Rejected | no |
| 부분 기각 | Partially rejected | no |

## Mandatory closing sentence

The final paragraph of the new section MUST be exactly:

```
The hypothesis table above (H1~H{prev}) remains unchanged (Closed-append-only policy). H##'s entry is a new addition only.
```

with `{prev}` = the immediately preceding hypothesis ID (e.g., for H12 use `H1~H11`). This boilerplate signals to future readers (and audits) that the policy was respected.

## Common mistakes to avoid

1. **Don't** edit the hypothesis table at the top — even to add the new H## row. The English file's table is frozen at H1~H9c by design; new hypothesis verdicts are documented in append-only sections, not the table.
2. **Don't** rewrite earlier `## Exp##` sections "for consistency" — they are historical records, even if newer terminology has emerged.
3. **Don't** translate the Korean section verbatim — the English file is a *summary mirror*, not a literal translation. Keep it shorter (~1 paragraph per logical block) and English-native.
4. **Don't** use `Write` to overwrite the whole file — too easy to drop content. Always `Edit` with anchor strings.
