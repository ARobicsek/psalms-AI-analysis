# Session 361 Brief — Local Validation of the Session-360 Features

**Written by**: the Session-360 cloud instance (branch `claude/psalms-guide-quality-l668wo`,
commit `efa6a5d`), for the next Claude instance running LOCALLY on the author's machine.
**Read this first, then execute top to bottom.** Everything below exists because the
cloud environment could not do it: the real `tanakh.db` and the most recent psalm
outputs (incl. Pss 61/62) live only on this machine.

**Context in one paragraph**: Session 360 shipped four features — (1) writer prompt:
one *affective landing* per guide + items-of-interest #11 rewritten as "The Psalm in a
Human Mouth"; (2) `src/concordance/distributional_facts.py`, a deterministic SQL
pre-pass feeding the synthesis sidecar exact counts; (3) a measurement-only *beta
reader* agent (`src/agents/beta_reader.py`, `scripts/run_beta_reader.py`, pipeline
STEP 5d, ON by default); (4) `docs/prompts_reference/voice_exemplars.md`, wit
exemplars mined from Pss 58/59/60 (the only outputs reachable from the cloud).
Details: IMPLEMENTATION_LOG.md, Session 360 entry.

**Environment notes** (from prior session records): repo lives at
`C:\dev\personal\psalms`; in git bash activate the venv with
`source venv/Scripts/activate` (PowerShell auto-resolves). `ANTHROPIC_API_KEY` must
be set for Task 3. Total expected spend for this brief: **~$1 (all beta reads)**;
Tasks 1–2 are free.

---

## Task 1 — Find the real tanakh.db and smoke-test distributional facts (free)

The production database convention is **`database/tanakh.db`** relative to the repo
root (that's what `master_editor.py` and most agents use); `data/tanakh.db` is a
secondary location some older code references. The cloud clone shipped an EMPTY stub
— every table 0 rows — so the module has only ever run against a synthetic test DB.

1. Verify which file is real:
   ```bash
   python -c "import sqlite3; c=sqlite3.connect('database/tanakh.db'); print(c.execute('SELECT COUNT(*) FROM concordance').fetchone())"
   ```
   Expect a count in the hundreds of thousands (full-Tanakh word tokens). If
   `database/tanakh.db` is empty but `data/tanakh.db` is populated, note that —
   the module auto-searches both, in that order (`_DEFAULT_DB_CANDIDATES` in
   `src/concordance/distributional_facts.py`).

2. Smoke-test and eyeball:
   ```bash
   python -m src.concordance.distributional_facts 60
   python -m src.concordance.distributional_facts 58
   ```
   Checks, in order of importance:
   - **Runs at all** against the real schema, and in reasonable time (the bigram
     pass does one indexed self-join per adjacent pair; if a psalm takes more than
     ~60s, report it — the fix is pre-filtering pairs by per-word corpus count).
   - **Known facts appear**: Ps 60 should flag פצמתה (v. 4) as a unique form; Ps 58
     should flag שבלול (v. 9). Divine-name tally for both should show 0 YHWH-final
     forms... actually Ps 58 v. 7 contains ה׳ — check the tally against the printed
     text rather than assuming; disagreement between the tally and your own count of
     the printed psalm is exactly the kind of bug to catch here.
   - **Block size** stays ~3–6K chars (caps: MAX_RARE_ROWS/MAX_REPEAT_ROWS/
     MAX_BIGRAM_ROWS in the module).
   - **Signal check**: would any row have fed a real published insight? (Ps 60's
     seal-verse/inclusio material, Ps 58's hapax cluster.) If the tables are all
     noise, say so honestly — tuning RARE_MAX/MIN_FORM_LEN is cheap.
3. Record the outcome (works / needs tuning / bug) in the session log. The sidecar
   splice activates automatically on the next pipeline run — nothing to enable.

## Task 2 — Read the last 7 final outputs; finish the wit-exemplar file (free)

Identify the 7 most recently produced psalms:
```bash
ls -t output/psalm_*/psalm_*_copy_edited.md | head -10
```
(Fall back to `*_print_ready.md` where no copy-edited file exists; the Session-359
writer-compare outputs for 61/62 are in gitignored
`output/psalm_6X/_writer_compare_new/` and count — they're the only outputs written
under the post-359 wit rule.)

Read all 7 end to end and:
1. **Harvest wit for `docs/prompts_reference/voice_exemplars.md`.** The file has 10
   Tier-1 entries from Pss 58/59/60 (pre-359 prompt) and an empty seat reserved for
   61/62. Known 61/62 candidates from the Session-359 log: "Rank does not add a
   single gram," "a fact worth stating plainly rather than padding," "the lexicons
   throw up their hands ('text dubious,' says BDB)," "Sanctuary-access is the estate
   God deeds to the landless," "the word for it is *tomorrow, and the day after
   that*." Verify each in situ (quote exactly, note psalm/verse/section), keep only
   what survives the RULE-13 test, and check every addition against the file's
   anti-patterns section (especially the "One does not…" template — if 61/62 leak
   it too, record that; it means the mold survived the Session-359 deletion).
2. **Note affective-landing near-misses.** These guides predate the feature. Mark
   the passage in each that comes CLOSEST to an affective landing (or "none") —
   this is the informal baseline for judging whether the new prompt actually
   changes anything on the next fresh psalm.

## Task 3 — Run the beta reader on recent outputs and evaluate THE AGENT (~$1)

This is a meta-evaluation: the question is not "are the guides good?" but **"is the
beta reader a trustworthy instrument?"** Run:
```bash
python scripts/run_beta_reader.py 58 59 60 61 62        # adjust to the actual last-7 list
python scripts/run_beta_reader.py 60                     # second run on ONE psalm, for noise
```
(~$0.08 each; the repeat run gauges run-to-run score noise before anyone trusts a
delta. If 61/62 finals only exist in `_writer_compare_new/`, point the runner at
them with `--input-file`.)

Then evaluate each `psalm_NNN_beta_read.md` against the guide it read:

| Check | Pass looks like | Fail looks like |
|---|---|---|
| **Quote fidelity** | Every quoted passage exists verbatim in the guide | Paraphrase presented as quotation — disqualifying for a measurement tool |
| **Discrimination** | Scores vary across psalms AND dimensions | Everything clumps at 7/10 (classic LLM-judge flattery) |
| **Known-contrast calibration** | WIT scores for 61/62 (post-359 prompt) > 58/59/60 (pre-359) | No wit gap where a known prompt-change gap exists |
| **Affective-landing honesty** | On these pre-360 guides it reports absence or near-misses plainly | It "finds" a landing in every guide (eager-to-please) |
| **Sag-point plausibility** | Your own read of the flagged stretches agrees more often than not | Random or boilerplate sag claims |
| **Stays in role** | Zero edit suggestions | Slips into editor mode ("consider trimming…") — prompt violation |
| **Noise** | Repeat-run scores within ±1 | ±2+ swings — then only sign-consistency across psalms is meaningful (cf. the Session-358 judge-noise finding) |

**Deliverables**: (a) a verdict — is the beta reader usable as-is, does its prompt
need tightening (say exactly where), or should it be demoted to advisory-only;
(b) the baseline score table for the psalms run (these are the "before" numbers for
the affective-landing feature); (c) updated `voice_exemplars.md`; (d) the Task-1
distributional-facts outcome. Update CLAUDE.md (Session 361) + IMPLEMENTATION_LOG
per the end-of-session checklist, and delete this brief (or move it to
`docs/plans/archive/`) once executed.

**Deferred, do not do without the author**: wiring the voice sampler into the
writer prompt; any writer-only A/B of the affective-landing/human-mouth edits
(~$1.3 via `archive/development_scripts/compare_writer.py`); any change to the
beta reader's role (it stays measurement-only — author decision, Session 360).
