# Novelty A/B Runbook — R1–R6 vs. production (Psalms 58, 59, 60)

**Session:** 358 · **Branch:** `claude/sweet-fermat-pje3t7` (the R1–R6 changes live ONLY here)
**Findings doc:** `docs/plans/PIPELINE_NOVELTY_REVIEW_FINDINGS.md` (on `main`)
**Eval tool:** `scripts/evaluate_novelty_ab.py` (on `main`, merged into this branch)

## What changed on this branch (the B arm)

| Rec | File(s) | Change |
|---|---|---|
| R1 | `src/agents/master_editor.py` (+ propagates to `master_editor_si.py`) | "GOLD INVENTORY" reasoning-phase mandate: list the 6-10 best finds first; hook + closing must come from the list; gold finds get the depth budget; checklist line enforces it. Splice block now tells the writer to treat sidecar observations as gold-inventory CANDIDATES (adopt/demote/reject deliberately). SI splice also gains the previously missing CONJECTURE-rendering sentence (S357 drift fix). |
| R2 | `src/agents/copy_editor.py` | "DEMONSTRATION vs. FLAGGED CONJECTURE" rule: verify a flagged conjecture's facts and hedge-honesty; never delete or de-hedge it; unflagged leaps get a hedge added, not deleted. Category 6 rewritten: judge parallels by the specificity of the SHARED element; contrast-developed parallels are explicitly legitimate. |
| R3 | `src/agents/research_assembler.py` | Concordance display sample is purpose-aware: results whose book:chapter:verse is named in the request's purpose/insight notes are PINNED into the 10 shown (marked `†` with a legend) instead of being left to the random draw. |
| R4 | `src/agents/liturgical_librarian.py` | All four summary prompts (phrase/full-psalm × GPT/Claude) gain "FLAG THE NON-OBVIOUS PLACEMENT": one sentence naming a placement anomaly when (and only when) the placement is not self-explanatory; no invented explanations. Sentence budget 4→4-7 (QC already accepts 3-7). |
| R5 | `src/agents/master_editor.py` `_format_analysis_for_prompt` | Macro `poetic_devices` (with function) and `working_notes` now reach the Master Writer AND the synthesis-discovery sidecar (previously dropped entirely). |
| R6 | `src/agents/micro_analyst.py` | Macro research questions are injected into the Stage-2 research-request prompt: each lookup-answerable question must steer ≥1 request, within the existing quotas. |

Production code on `main` is untouched.

## How to run (local machine, API keys required)

```bash
git checkout claude/sweet-fermat-pje3t7
source venv/Scripts/activate          # git-bash; PowerShell auto-resolves

# 1. Run the three psalms through the R1-R6 pipeline (identical harness,
#    isolated output dir; macro held constant from the baseline run;
#    literary echoes file reused, not regenerated):
python scripts/run_novelty_ab.py 58 59 60
#    ~$5.5-6/psalm, ~3 × 30-45 min. Outputs land in output/ab_novelty/psalm_NN.

# 2. Evaluate old vs new — deterministic metrics + blind Opus judge:
python scripts/evaluate_novelty_ab.py 58 59 60
#    ~$1/psalm. Reports in output/ab_novelty/eval/ (per-psalm + summary table).
#    Add --skip-judge first for a free metrics-only pass if you want.
```

The OLD arm is found automatically: `output/psalm_N/psalm_0NN_copy_edited.md`
if present, else the published DOCX in `Documents/Psalm study guide/Psalm N.docx`.

## Design decisions (why the arms are comparable)

- **Same harness**: the runner shells out to `scripts/run_enhanced_pipeline.py`
  with production defaults — same steps, same models, same delays.
- **Macro held constant**: the baseline `psalm_0NN_macro.json` is copied into
  the arm dir and `--skip-macro` passed. R5/R6 change how macro output is
  consumed, not produced, so this removes macro run-to-run noise from the
  comparison (and the R5 formatter + R6 injection still fire on the copied
  JSON). `--fresh-macro` overrides.
- **Echoes held constant**: `--skip-lit-echoes`; both arms read the same
  existing `data/literary_echoes/psalm_0NN_literary_echoes.txt`. R1-R6 don't
  touch the echoes pipeline, and regeneration would overwrite the shared file.
  `--with-lit-echoes` overrides (accepts overwrite + variance).
- **Everything else reruns**: micro (R6), research assembly (R3), liturgical
  summaries are read from DB caches or regenerated as production normally does,
  synthesis sidecar, writer (R1/R5), verifier, copy editor (R2), DOCX.

## Honest caveats for reading the results

1. **The old arm is "production as of when it ran," not "main as of today."**
   Psalms 58/59 predate the synthesis-discovery sidecar v2 (S357) and possibly
   other recent changes, so part of any delta belongs to those, not to R1-R6.
   If the result is positive and you want strict attribution before adopting,
   run a control arm from main into a third dir:
   `git checkout main && git checkout claude/sweet-fermat-pje3t7 -- scripts/run_novelty_ab.py && python scripts/run_novelty_ab.py 58 59 60 --out-root output/ab_novelty_mainarm --allow-any-branch`
   then `python scripts/evaluate_novelty_ab.py 58 59 60 --old-dir "output/ab_novelty_mainarm/psalm_{n}"`.
2. **Single runs per arm**: writer variance between two runs of the SAME prompt
   is real. Treat a narrow judge verdict as a tie; look for consistent
   direction across all three psalms plus the deterministic markers
   (hedge counts, copy-editor conjecture cuts) before concluding.
3. **Liturgical summaries (R4)** only regenerate if the pipeline recomputes
   them for the run; if they come from a cached DB artifact for these psalms,
   the R4 effect won't show in this A/B — check the new arm's liturgical
   section for the flag sentence to confirm R4 actually fired.
4. The judge is blind to arm identity but not to style; R1's gold-inventory
   could change length/shape. The rubric instructs the judge to ignore length
   and formatting — still, read the two best/worst insight tables yourself
   before trusting the bottom-line verdict.

## Adoption path

If the new arm wins: merge this branch to `main` (R1-R6 + runner + runbook).
If mixed: the six changes are independent — each sits in its own file region
and can be cherry-picked or reverted individually (R1/R5 in `master_editor.py`,
R2 in `copy_editor.py`, R3 in `research_assembler.py`, R4 in
`liturgical_librarian.py`, R6 in `micro_analyst.py`).
