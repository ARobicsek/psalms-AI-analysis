# Next Session Prompt — Session 372

**Written**: 2026-08-02 (end of Session 371)

The author set this agenda explicitly at the end of Session 371, in this order:

> *"let's start our next session by reexamining our writer prompt thinking about the
> concepts above, and by looking at B4, and by considering whether we should do an
> opus 5 vs 4.8 A/B test with all our 'B' changes."*

---

## (a) THE AFFECT WORK — the author's headline item

The trigger: *"do we say enough in the prompt about finding the pathos, wonder, humor,
etc in the poem? I know we try to have one moment of this, but is it working, and is it
enough?"* — followed by *"let's try to do something about each of wonder, wit and pathos
(and any other 'connecting to the reader's heart' sorts of items)."*

### READ THIS FIRST — what the author means by "wonder"

The author corrected an initial misreading, and the distinction is the whole point:

> *"When I say 'wonder' here, I'm not talking about 'AHA' moments (though those are the
> #1 most essential thing I'm looking for) — I'm talking about conveying **the poet's
> sense of wonder about something**. It doesn't have to be wonder — it could be some
> other powerful emotion as well."*

So there are **two different things**, and the prompt currently conflates them at best:

| | whose feeling | current prompt coverage |
|---|---|---|
| **AHA** | the READER's — "huh, really?" | the stated mission; RULE 11's translation test polices it indirectly. **The author calls this the #1 most essential thing.** |
| **WONDER** (this item) | **the POET's** — awe, terror, longing, gratitude, bewilderment, delight, felt inside the poem and conveyed to the reader | **nothing. No rule, no exemplar, no checklist item.** |

The new target is *conveying the poet's own powerful emotion* — showing that the person
who wrote this was struck by something. That is a distinct craft task from making the
reader say "aha," and from the affective landing (which is about the reader's
recognition of a human situation).

### The evidence gathered in Session 371

Beta-reader scores, Ps 71, all six prompt arms plus recent production guides:

| | Wit | Emotional impact |
|---|---|---|
| Opus 5 arms: base / B / B2 / B3 / C | 3 / 5 / 3 / 3 / 3 | **7 / 8 / 7 / 7 / 7** |
| Opus 5 arm **A** (scaffolding deleted) | **6** | 7 |
| 4.8-era production Pss 65, 66, 67, 68, 70 | 7, 7, 7, 7, 7 | 7, 7, 6, 6, 7 |

Three findings:

1. **Pathos is capped, not broken.** `LANDING: found` in all six arms, and
   `Emotional impact` is **7/10 in literally every arm** (B alone 8). A number that never
   moves is measuring the ceiling the rule sets, not the arms. The rule says *"Exactly
   one per guide — spread it thinner and nothing lands."*
   **The author is explicitly sceptical of this cap**: *"I'm a little skeptical of the
   'only one' for pathos, btw."* Treat the cap as the thing to test, not a given. Note
   the rule was written to prevent dilution BEFORE the beta reader's engagement curves
   existed; those curves reliably show sag stretches (Ps 69: *"verses 15–26… industrious
   rather than alive"*), and a second human moment is forbidden exactly where it would
   help most.

2. **Wit is broken, and it is Opus-5-specific.** 4.8 scores 7 with the same RULE 13;
   Opus 5 scores 3. The beta reader is precise about the failure: base is *"eloquent and
   warm rather than deadpan"*; B3 has genuine dry wit *"only once, maybe."* Opus 5
   substitutes warmth for dryness — a register miss, not an absence.
   **Watch item:** arm A scored **6**, the only Opus 5 arm near 4.8, and the WIT
   checklist item was one of the 24 entries A deleted. Second signal that asking "is
   there wit?" produces eloquence rather than deadpan. Consider deleting the WIT
   checklist item while KEEPING RULE 13.

3. **Wonder is unnamed.** Everything that landed in this register arrived by luck — the
   Ḥullin unicorn, *"BDB shrugs,"* the LXX turning a bark into *"bravo, bravo."*

### Suggested shape (not decided)

- A positive-exemplar block for the poet's-wonder register, mined the way Session 371
  mined the others (see `WRITER_PROMPT_POSITIVE_EXEMPLARS.md` for the method — beta
  reader AHA/FELT/WIT tags as an independently-judged candidate pool, verified present
  in the COPY-EDITED text, RULE 13's anti-pastiche guard attached).
- Replace the pathos "exactly one" cap with something like *one full landing + brief
  human moments permitted wherever the material genuinely carries them*, and measure
  `Emotional impact` against the 7 ceiling.
- For wit, the lever is probably NOT more rule text (RULE 13 is already the richest
  affect rule we have). Test deleting the checklist item; consider a
  4.8-vs-Opus-5 register diff to find what 4.8 does that Opus 5 does not.

**Mind the standing hazard.** Five times now, adding prompt text intended to produce
restraint has produced its opposite (Session 368 copy editor; Session 370 RULE 8b
amendment; Session 371 arms C, B2's abstract IDEAL CUT, and B3's citation gallery).
Affect instructions are the same shape. Prefer demonstrations to exhortation.

## (b) Look at B4

`output/psalm_71/_prompt_ab/B4_final/` — the coverage/citation decoupling fix, run at
the very end of Session 371. **Its scorecard was not read before the session closed.**

What it tests: B3 hit the coverage target (85.2%, best of any arm, while coming in
SHORTER than baseline at 0.96×) but drove citations to their worst ever
(`INERT CITATIONS: 8`, 44 commentator mentions, 4.8 per 1k words). Diagnosis: coverage
demand recruits commentators, exactly the channel `WRITER_PROMPT_RULE_8B_FINDINGS.md` §3
named a session earlier — *"the cheapest way to make a dull phrase visible is to quote
the commentator who paraphrases it."*

B4's fix, now live in `master_editor.py` (production, both halves):
- In the word-and-phrase floor: **"COVER IN YOUR OWN WORDS — a commentator is never the
  instrument of coverage… Coverage is a translation duty, not a research duty."**
- In RULE 8b: **"COVERAGE IS NEVER AN ADMISSION TICKET… If the only reason a gloss is in
  front of you is that its word needed covering, it fails this test by construction."**

**RESULT, read before anything else: B4 FAILED both halves.** Beta counters:
`INERT CITATIONS: 7` — unchanged from baseline, i.e. the fix bought nothing on the exact
metric it targeted — `UNEXPLAINED GRAMMAR: 12` (worst of any arm), `LANDING: found`.

| | base | B3 | **B4** |
|---|---|---|---|
| verse words | 9,507 | 9,101 | **8,413** (shortest of seven arms) |
| word coverage | 77.6% | **85.2%** | **76.5%** |
| commentator mentions | 38 | 44 | **48** (worst) |
| commentators / 1k words | 4.0 | 4.8 | **5.7** (worst) |
| Tier-1 / verse | 1.00 | 1.33 | **1.42** (worst) |

Coverage fell 8.7 points AND citation density hit its worst level — the opposite of the
intervention on both axes. The failure shape is the clue: **shortest arm, most
commentators.** The model appears to have cut its own coverage prose rather than its
citations, plausibly because *"coverage is a translation duty, not a research duty"* read
as licence to do less covering while the extra RULE 8b text raised commentator salience
(the standing pattern again).

**So the coverage→citation diagnosis is NOT established.** Re-derive it rather than
inheriting it. Concretely, consider: is the tension real at all, or were B3's citation
numbers driven by something else? A cheap discriminator is to run the word floor WITHOUT
any citation-block changes and see whether citations move.

**Both B4 edits are currently live in production `master_editor.py`** ("COVER IN YOUR OWN
WORDS" in the floor, "COVERAGE IS NEVER AN ADMISSION TICKET" in RULE 8b). Given the
result, **decide early whether to revert them.** B3's configuration — the floor without
these two additions — is the best-performing state and is what `Psalm 71 (final).docx`
was written from.

Finishing B4 to DOCX is optional and was not done:
`python scripts/ab_finish_arms.py 71 --ab-dir _prompt_ab --arms B4_final
--writer-model claude-opus-5 --copy-to-documents`.

## (c) Opus 5 vs 4.8 A/B with all the "B" changes

The author's own suggestion. Rationale: every Session-371 finding is Opus-5-only, the
prompt has changed substantially since the Session 367/368 comparisons, and two separate
results now point the same way — 4.8 wins on **wit** (7 vs 3) and on **essay framing**
(it is the only model that built the Ps 71 essay on the anthology idea, which is the
author's favourite insight in any Ps 71 essay).

Run `scripts/ab_writer_models.py 71 --models claude-opus-4-8 claude-opus-5 --beta-read`
with the current prompt, then score both with `score_prompt_ab.py --ab-dir _writer_ab`.

**The live question is whether the answer is a split-model run** — 4.8 for the
introduction essay, Opus 5 for the verse commentary. Sessions 367 and 368 independently
concluded "Opus 5 = better GUIDE, 4.8 = better ESSAY," and Session 371 found the
mechanism for the essay half: across five Opus 5 runs it never once chose the
compositional thesis, consistently preferring the lexical/legal one. That is a model
preference, not a suppressed instruction — the suppressors were fixed and it did not
move. A split run needs a new pipeline mode; scope it before building it.

## (d) Carried forward, untouched

- **Colon-level doublet alignment** for the Ps 71↔31 class (Session 368: the pair misses
  by 0.05 because the unit is the verse, not the colon — do NOT just lower the 0.8
  threshold).
- **Post-copy-edit scripture verification** (~$0.15/run; the durable fix for fabricated
  biblical claims).
- **Free, no-API**: re-render DOCX for the 17 psalms affected by Session 366's
  divine-names fix and any guide quoting a phonetic transcription (Session 370's empty
  bold runs). `scripts/run_docx_only.py <n>`, $0.
- **One human check**: open `Psalm 71 (final).docx` and confirm the bolded Hebrew prefix
  letters render without a hairline gap in Word. The XML is correct; only the eye can
  confirm the visual join.
