# Session 372 — the translation slot, and the measurement that wasn't measuring

**Date**: 2026-08-02
**Cost**: ~$6.0 (arms D+E $4.01, judge-variance calibration $1.68, arm E copy-edit/DOCX ~$0.3)

Two results. One is a prompt design that finally moved the citation problem. The other is
that most of the evidence Sessions 370–371 used to reach their conclusions was noise, and
some of it pointed the wrong way.

---

## 1. READ THIS FIRST — the beta reader does not survive repeated measurement

`scripts/beta_reader_variance.py` (new) re-reads **one fixed text** N times and reports the
spread. Nobody had ever run it. Four reads each of Psalm 71's `base`, `A_no_scaffolding`,
and `E_translation`:

| metric | base | E_translation | A_no_scaffolding |
|---|---|---|---|
| Wit | 4, 6, 3, 4 (**4.25**) | 5, 3, 4, 4 (**4.0**) | 7, 7, 6 (**6.7**) |
| Emotional impact | 8, 6, 6, 7 (**6.75**) | 6, 6, 7, 7 (**6.5**) | 7, 7, 7 (**7.0**) |
| INERT CITATIONS | 8, 9, 6, 6 (**7.25**) | 7, 6, 4, 7 (**6.0**) | 6, 6, 8, 7 (**6.75**) |
| UNEXPLAINED GRAMMAR | 6, 6, 1, 5 (**4.5**) | 7, 9, 4, 7 (**6.75**) | 14, 9, 11, 15 (**12.25**) |
| POET'S FEELING | 1, 0, 1, 1 | 1, 0, 1, 2 | 0, 0, 1, 1 |

Engagement and Freshness are stable (range 0–1). Everything we drew conclusions from is not.

**Consequences, all load-bearing:**

- **Every between-arm gap of 1–3 on these rows in the Session 370–372 record is inside the
  judge's own noise.** That covers essentially all the `INERT CITATIONS` reasoning.
- **Session 371's arm-A finding is INVERTED.** The record says "UNEXPLAINED GRAMMAR 11 → 9…
  no capability regression," which was the central defence of deleting the verification
  scaffolding. On four reads base averages **4.5** and arm A averages **12.25** — deleting the
  checklist made grammar explanation *markedly worse*. Single-sampling hid it because the two
  originals happened to be off in opposite directions.
- **`POET'S FEELING`, added this session, does not discriminate** — 0–2 everywhere. Measuring
  before legislating was the right call, and this is what it returned. Redesign or drop it.
- **Wit survives as real signal**: A at 6.7 vs ~4.1 for base and E, a gap wider than the noise.
  "Wit is Opus-5-specific and the scaffolding deletion recovers it" holds.

**Action taken: the beta reader is now OFF by default** in `run_enhanced_pipeline.py` and
`run_si_pipeline.py` (`--beta-reader` opts back in; `--skip-beta-reader` kept as a no-op so
existing invocations don't break). Repeat-sampling to beat the noise was considered and
rejected by the author: it multiplies cost for a judge we do not trust at any n.

**What IS trustworthy**: every deterministic count — `score_prompt_ab.py`'s regex metrics and
`check_phrase_coverage.py`. Same text, same number, always. Arm E's result rests entirely on
those. Beta-sourced rows in the scorecard are now marked `†` with their measured noise band.

**The general lesson**: an LLM judge's *rubric-scored counters* are not the same kind of
instrument as a deterministic count, and Session 370's "the beta reader's independent audit is
the trustworthy signal" over-generalised from a true observation (that canary regexes matching
on *wording* are fragile) to a false one.

---

## 2. What actually fixed the citation problem: the author's translation slot

**The idea (author's).** Print a full English translation of each verse at the top of its
block, offset as a block quote. Coverage then holds *by construction*, and the commentary
below is free to select purely on interest.

This is the one move that escapes the standing hazard — five prior instances where added
restraint text produced its opposite — because there is nothing left to exhort.

**Arms D and E were identical except for the slot**, so the comparison is single-variable:

| | D (no slot) | **E (slot)** | best prior |
|---|---|---|---|
| commentator mentions | 50 | **32** | 35 |
| Tier-1 / verse | 1.96 | **1.21** | 1.00 |
| commentators / 1k | 5.8 | **3.7** | 3.3 |
| grammar terms named | 16 | **9** | 7 |
| redundancy markers | 4 | **0** | 0 |
| verse words | 8,589 | 8,628 (**0.91×**) | 8,413 |
| quoted echo lines | 23 | **49** | 36 |
| translation guarantee (`xlat`) | — | **24/24** | — |
| cost / seconds | $1.98 | **$2.02 / 722** (fastest) | — |

**32 commentator mentions is the lowest ever recorded**, at near-shortest length, with every
verse carrying a full translation. The freed room went to literary echoes (49 quoted lines,
highest ever), not to paraphrase.

**This confirms the Session-370 coverage→citation mechanism and explains why B4 failed.** B4
tried to sever the channel with *words* ("a commentator is never the instrument of coverage")
and bought nothing. The channel is structural, so only a structural fix closes it.

Also verified: **arm E needs no pipeline changes.** `document_generator.py` already routes `>`
lines into indented italic quote blocks, and renders only `verse["commentary"]` (the per-verse
`english` field it populates is dead code) — so there is no duplication. Grouped verses keep
the guarantee: E grouped once (`Verses 10–11`) and correctly printed Hebrew 10 → English 10 →
Hebrew 11 → English 11 → shared commentary.

---

## 3. The other structural finding: `300-500 words per verse`

`git log -S` dates this line to Session ~130 — written for models that *under*-produced, never
revisited in 360+ sessions, never an A/B variable. It is binding: across all seven Session-371
arms the median verse section is 330–437 words and **never once falls below 330**.

Deleting it (arm D) produced **−918 words**. Arm C's *instruction* to be concise produced
**+373**. That settles the length question and explains arm C's backfire: the instruction
contradicted a word target sitting 15K chars further down the same prompt. Coverage went *up*
at the same time, so length and coverage were never in tension.

---

## 4. Production state

`master_editor.py` was restored to the **B3 configuration** and verified byte-identical to the
saved `B3_final` arm template:

- B4's two edits **reverted** (they failed both halves they targeted).
- Arm B's six `WORKED EXAMPLES` blocks **shipped** (+10,890 chars). They had won in Session 371
  and were never merged out of `writer_prompt_variants.py` — production had been running the
  losing half of that session's work.
- `variant_b` now **raises** rather than silently double-inserting.

**Arm E's changes are NOT yet in production** — awaiting the author's read of the DOCX.

---

## 5. Open

- **Ship E to production** once the DOCX is read.
- **Validate on a fresh psalm.** Nine arms have now run on Psalm 71 alone; E's margin could be
  partly fitted to a doublet-heavy, commentator-dense text.
- **Wonder / the poet's own feeling** is unaddressed. No exemplars were mined because the
  register genuinely isn't in the Pss 65–70 corpus in usable quantity, and fabricating them
  would break the method that made arm B work. The best brief we have is the §5d readout on E:
  *"a courtroom argument is the form a person uses to manage an overwhelming emotion, not the
  emotion itself… the pride, the terror underneath the pride."*
- **Arm A's grammar regression** (12.25 vs base 4.5) is newly visible and unexplained. E, which
  deletes the same checklist but keeps arm B's RULE 3b-2 worked examples, lands at 6.75 — the
  exemplars appear to do the job the checklist item was doing. Worth confirming deterministically
  (`grammar terms named` is a regex count: base 8, A 12, E 9 — same ordering, no noise).
