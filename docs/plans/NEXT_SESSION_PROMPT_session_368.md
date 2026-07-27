# Session 368 — next-session prompt

Three items, set by the author at the close of Session 367. Read
`docs/session_tracking/IMPLEMENTATION_LOG.md` § Session 367 first; everything
below assumes it.

**State at hand-off**: `gpt-5.6-terra` is live in production (shipped Session 367,
cost-neutral, first run Ps 70 clean). The Master Writer is still on
`claude-opus-4-8`; Opus 5 is *recommended but NOT adopted* — `claude-opus-5` is
unblocked in both runners' `--master-editor-model` choices and priced in
`cost_tracker`, but no default was changed. Micro stays on `claude-sonnet-4-6`.

---

## (a) Is Terra overstepping as copy editor?

**The evidence that prompted this.** Finishing the Ps 70 A/B arms, the Terra copy
editor overwrote a **correct** statement about George Herbert's *Denial* — that
its final stanza restores the rhyme (*chime* / *rhyme*) after five stanzas of
unrhymed fifth lines — with the false *"the final stanza still withholds a final
rhyme. Psalm 70 does not use rhyme,"* and flattened the passage's closing image
("a shattered vessel that repairs itself in the last line" → "marks the strain in
broken rhymes"). It also **deleted the Anna Akhmatova comparison outright** from
the Opus 4.8 arm, taking that guide from two literary echoes to one.

Change volume was high on both arms: **26 edits to 4.8, 25 to Opus 5** on a
five-verse psalm.

**The question is narrower than "is the copy editor good."** Many of those edits
were plainly right — real overclaims softened, unglossed technical terms
(*piyyut*, *maḥzor*, "pleonastic") explained, and two genuine citation fixes
(1 Chr 16:4's dropped וּלְהַלֵּל; Ps 22:20's עוּשָׁה → חוּשָׁה). The problem is a
specific class: **claims about non-biblical literary and formal matters, where the
copy editor has no source in front of it and asserts anyway.**

**Suggested approach**

1. **Establish whether this is new or pre-existing.** Terra shipped this session,
   so the obvious hypothesis is that the swap caused it — but that is untested.
   Re-run the copy editor on the same input with `--model gpt-5.4` (the pin-back
   path still works: `run_copy_editor.py --model gpt-5.4`, or the
   `--gpt-5-4-copy` pipeline flag) and diff the change lists. If gpt-5.4 makes
   the same Herbert "correction," the swap is exonerated and this is a
   long-standing prompt problem.
2. **Audit the last few production psalms' `*_copy_edit_changes.md`** for the same
   class — edits to claims about literature, music, prosody, or history where no
   source was supplied. Categories `[7] Factual/textual accuracy` and `[9x]`
   overclaim are where they will sit.
3. **If it is a prompt problem**, the likely fix is a scope rule in
   `COPY_EDITOR_SYSTEM_PROMPT`: correct factual claims *only* where the guide's
   own supplied material (dossier, literary-echoes file, cited biblical text)
   contradicts them; for claims about outside works, flag rather than rewrite.
   Note the copy editor already receives the citation-verifier fix prompt as
   `supplementary_prompt` — that channel is the model for "flag, don't rewrite."
4. **Guard against over-deletion** of literary echoes, which the writer is
   explicitly instructed to include and which Session 365 showed drive the best
   passages.

Watch that this does not regress the genuinely useful edits — the goal is scope,
not timidity.

---

## (b) Can Opus 5 be made shorter without losing quality?

**Why this matters.** Opus 5 is the recommended writer but produced **6,527 words
for a five-verse psalm** (vs 4.8's 4,216) — 1.55× words, 1.97× output tokens,
1.87× latency, +$0.37 on the writer stage alone (~+$1.5/run if macro and
synthesis discovery follow). Session 367's close read concluded the extra length
is **utilization, not padding** — four real doublet variants and two first-rate
arguments 4.8 missed, every addition traceable to the dossier. So the goal is to
cut length **without cutting the scholarship that justified adopting it**.

**Levers, in the order I would try them**

1. **The conciseness instruction** from the Opus 5 migration guide. Anthropic's
   guidance is explicit that **`effort` does NOT reliably shorten visible output**
   — prompting is the lever. Do not try to solve this by dropping `effort` to
   `medium`; that trades away the reasoning that produced the good material.
2. **Cap literary echoes at 2–3.** Opus 5 used 4 of 5 available; 4.8 used 2. The
   Miłosz passage in v.4 in particular runs long. This is a writer-prompt rule,
   and it is the single largest block of cuttable text.
3. **A deliverable-length instruction** — the migration guide notes Opus 5 writes
   longer files to disk independent of conversational verbosity.
4. **Style drift to fix while in there**: Opus 5 introduced two `###` body headers
   in the intro ("What the poet removed" / "What the cut leaves behind") that
   production intros do not use.

**How to measure.** `scripts/ab_writer_models.py` takes arbitrary `--models`, but
this is a *prompt* A/B on one model, not a model A/B — either add a
`--prompt-variant` switch or run the two arms as separate invocations against the
same psalm and diff. The success criterion is **word count down, insight count
flat**: count doublet variants, cross-references, and distinct arguments before
and after, not just length. Session 367's Ps 70 read is the baseline to beat.

---

## (c) Run Psalm 71

Straight production run on the finalized pipeline:

```bash
python scripts/run_enhanced_pipeline.py 71
```

**What to check, given everything above**

- **Terra**: does the run stay clean on a longer psalm? Ps 71 is 24 verses vs
  Ps 70's 6. Watch literary-echoes **pass 4** specifically — gpt-5.1 historically
  self-terminated early on the ~30K-char Pass-4 prompt, and if Terra regresses the
  same way, pin `GPT_RECONSTRUCT_MODEL` back to `"gpt-5.4"` in
  `src/agents/literary_echoes_agent.py`. A pass reporting **$0.00** means a model
  constant moved without a matching price branch in `_compute_cost_gpt`.
- **Reasoning tokens**: GPT agents should now report non-zero `thinking_tokens`
  (Ps 70: 8,944 on Terra). Totals stay comparable to earlier runs — only the
  output/thinking split changed.
- **Writer model**: decide before running whether Ps 71 is the first production
  Opus 5 psalm. If yes, land item (b)'s conciseness fix **first** so the length
  question is answered in the same run rather than after the fact.
- **Ps 71 is contextually interesting**: it is widely read as an aged-David
  companion to Ps 70 and shares vocabulary with it (and with Ps 31). The
  related-psalms librarian's Session-365 doublet detection should have something
  to say — worth checking whether the writer engages it, per the Session-365
  rule that "a doublet flagged in the research but absent from the guide is a
  scholarship gap."

---

## Carried forward (not this session's items)

- **Opus 5 adoption decision** is still open. Recommendation stands: adopt, with
  (b)'s conciseness fix.
- **Both models missed** a genuine observation on Ps 70: Ps 40:18 ends
  **אֱלֹהַי** אַל־תְּאַחַר while Ps 70:6 ends **יְהוָה** אַל־תְּאַחַר — the
  Yahwistic psalm closing with *Elohim* and the Elohistic psalm with the
  Tetragrammaton, a clean inversion of the redaction both guides build an
  argument on. That is a Synthesis Scholar gap, not a writer gap.
- **Prompt caching** (`docs/plans/DOSSIER_CACHE_KEEPALIVE_PLAN.md`) is where the
  remaining money is: ~$1.98/run of un-cached Opus input tokens,
  `cache_read_tokens: 0` on every run to date. Opus 5 halves the cacheable-prefix
  minimum (1024 → 512 tokens), which improves the case slightly.
- **Gemini 3.6 Flash** for literary-echoes passes 1–2: −$0.12/run, verified
  working at `thinking_budget=24000`. Cleanup, not a cost program.
- **Archive** `scripts/EXPERIMENT_micro_terra_probe.py` per the File Organization
  Rules once (a) is settled.
- Session 366 leftovers still open: **יָהּ has no divine-names rule**, and the
  16 psalm outputs affected by the prefixed-El fix have **not been re-rendered**
  (no AI spend — the modifier runs at DOCX-build time).
