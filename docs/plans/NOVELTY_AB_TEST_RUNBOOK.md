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

## Round 2 (Session 358, after the round-1 verdict)

**Round-1 result (Pss 58/59/60, judged blind): OLD won 3–0** (best-5 margins
−1.0 / −1.0 / −0.2). Recurring failure structure, same in all three: the new
arm matched or beat OLD on best individual finds and bridging-gold, but (a)
its essay spine was always the sidecar's GOVERNING OBSERVATION, adopted
uncritically — and that pick was the locus of every overreach complaint
(58 "organs" strained; 59 "the phonetics confirm" inherited verbatim from the
sidecar; 60's bow-genre hedge hardened into fact by the close); (b) the
copy editor under-enforced hedge-hardening. The generation machinery
(R3→sidecar anchors, R4→snail insight, R1 no-evaporation) demonstrably worked.

**Round-2 changes (writer + copy editor prompts only; upstream untouched):**
1. `master_editor.py`/`master_editor_si.py` splice block rewritten: the writer
   explicitly OUTRANKS the discovery pass — RE-RANK (its tiering is opinion;
   its governing pick has no claim on the essay spine), ADAPT (sharpen /
   recombine / keep anchors, draw a different conclusion), IGNORE
   (deliberately), and CALIBRATION IS ONE-WAY (never promote phrasing
   strength; demoting or cutting overstated wording is encouraged — the old
   "keep its phrasing strength as you find it" locked sidecar overclaims in).
2. GOLD INVENTORY: "the inventory is YOURS" — own fresh discoveries expected,
   upstream rankings carry no authority; new checklist line "HEDGES HOLD TO
   THE END" (no hedge introduced early may be restated as fact in the close).
3. `copy_editor.py`: dedicated HEDGE-HARDENING CHECK pass — trace each hedged
   claim forward; restore the hedge where later restatements (especially
   closing paragraphs) exceed it; police unsourced attributions
   ("commentators found it hard to justify") and authorial mind-reading.
4. **Judge: deliberately UNCHANGED.** The round-1 rubric already scores both
   arms symmetrically on groundedness/calibration; editing it now would break
   round-to-round comparability and risk tilting it toward the new arm.

**Round-2 run (lowest cost — writer-and-downstream only, ~$3.7/psalm, ~$11):**
upstream evidence (macro, micro, research bundle, synthesis-discovery
observations) is copied byte-identical from the round-1 arm, so the delta
isolates the two prompt changes. Uses the new
`--reuse-synthesis-discovery` pipeline flag (writer receives the cached
observations without paying for regeneration).

```bash
git pull
python scripts/run_novelty_ab.py 58 59 60 --reuse-upstream output/ab_novelty --out-root output/ab_novelty_r2
python scripts/evaluate_novelty_ab.py 58 59 60 --new-dir "output/ab_novelty_r2/psalm_{n}" --out output/ab_novelty_r2/eval
```

Reading round 2: the question is whether the new arm keeps its round-1 wins
(bridging gold, best-single-insight quality) while closing the two gaps the
judge identified (spine quality, overreach count). Since upstream is
byte-identical to round 1, also worth a direct eyeball: did the r2 essay
choose a different organizing insight than the sidecar's governing pick where
round 1's choice was the strained one (58, 60)?

## Round 3 (Session 358, after the round-2 verdict)

**Round-2 result: OLD won 3–0 again** (six straight verdicts). Decisive
diagnostics: (1) the round-2 writer-empowerment patch did not move the writer
— all three essays kept the sidecar's governing pick as their spine, and
overreach did not drop; **R1 is falsified** across two variants. (2) Judge
noise was measured for free (the OLD text was byte-identical across rounds,
yet its best-5 moved up to ±1.0 and gold counts ±4) — margins are near the
noise floor but 6/6 same-signed verdicts is real signal. (3) Forensics on the
v2 sidecar files: it FOUND the judges' favorite observation (Ps 59 ־מוֹ
badge) but tiered it ADDITIONAL while strained constructions wore GOVERNING;
it missed Ps 60's Edom preposition track (v1 had found it) and produced only
a weak local form of Ps 58's name-withholding. The sidecar's discovery is
good and its *tiering judgment* is bad — and the writer obeys tiers.

**Round-3 changes:**
1. **R1 fully reverted** — the Master Writer prompt and the splice block are
   back to the proven production baseline (S357 state). Thesis selection is
   entirely the writer's call, with zero added selection mandates. (R5's
   macro pass-through and the SI conjecture drift fix are retained.)
2. **Sidecar v2.1** (`synthesis_discovery.py`, prompt-only):
   - **De-tiered output**: a flat, UNRANKED observation list ordered by
     primary verse — no GOVERNING/CORE/ADDITIONAL, no salience signals;
     Type/Confidence/Anchors/Payoff retained (Confidence is calibration,
     not salience). Selecting and weighting is explicitly named as the
     Master Writer's job. Extraction markers unchanged.
   - **Additive DISTRIBUTIONAL sweep** in the collision pass: pick axes the
     psalm's own surface suggests, tabulate them in reasoning, inspect for
     lopsidedness including CONSPICUOUS ABSENCES ("a table you never build
     is a pattern you never see"). Explicitly a generator, NOT a gate: the
     qualitative TYPE P sweep is unchanged and needs no tabulation.
   - Honesty filters (a)-(j) untouched. Judge untouched.
3. **Copy editor**: retains R2 + the hedge-hardening check (unproven but
   principled; no observed harm).

**Round-3 run** (regenerates synthesis-discovery + writer + downstream on the
byte-identical round-1 macro/micro/research; ~$5.7/psalm ≈ $17 + ~$3 judge):

```bash
git pull
python scripts/run_novelty_ab.py 58 59 60 --reuse-upstream output/ab_novelty --out-root output/ab_novelty_r3 --regen-synthesis
python scripts/evaluate_novelty_ab.py 58 59 60 --new-dir "output/ab_novelty_r3/psalm_{n}" --out output/ab_novelty_r3/eval
```

Reading round 3 — three questions, in order:
1. Do the v2.1 sidecar files now contain the known pattern gold (Edom
   preposition track; whole-poem name-withholding; ־מוֹ badge present
   without being buried)? Eyeball the three
   `psalm_0NN_synthesis_discovery.md` files first — this is checkable
   before judging.
2. With the baseline writer free of tier anchoring, do the essays choose
   stronger spines (e.g., does 58's essay organize around something other
   than the anatomical scheme)?
3. The verdicts. Given measured judge noise (~±1.0), read sign-consistency
   across the three psalms, not margins; a 2-1 or 3-0 split either way at
   small margins means "rough parity with the old arm," which — combined
   with the kept plumbing wins — would already justify adopting the
   non-writer changes.

## Adoption path

If the new arm wins: merge this branch to `main` (R1-R6 + runner + runbook).
If mixed: the six changes are independent — each sits in its own file region
and can be cherry-picked or reverted individually (R1/R5 in `master_editor.py`,
R2 in `copy_editor.py`, R3 in `research_assembler.py`, R4 in
`liturgical_librarian.py`, R6 in `micro_analyst.py`).
