"""
Writer-prompt variants for the Session-371 Opus-5 A/B/C test.

Each variant is a pure function `str -> str` over MASTER_WRITER_PROMPT_V4. They are
deltas from the CURRENT prompt (which carries the third, never-run RULE 8b revision),
so a `base` arm is needed for the deltas to be attributable.

The three arms come from checking current Anthropic guidance during Session 370:

  A  delete the verification scaffolding
     The one Opus-5-specific *delete* in the guidance: Opus 5 verifies its own work
     without being asked, and removing the scaffolding reduces over-verification with
     no capability regression. This explicitly INVERTS standard prompting practice,
     so it needs evidence rather than faith.

  B  flip the negative-example ratio to positive
     Measured 24 negative markers (WEAK/BLOATED/AVOID/NEVER/DON'T/FORBIDDEN) against
     13 positive. Positive examples showing the desired output are documented to beat
     instructions saying what not to do. Exemplars are real in-house sentences mined
     in Session 371 item (a); see docs/plans/WRITER_PROMPT_POSITIVE_EXEMPLARS.md.

  C  add a conciseness instruction
     Documented ~20% reduction in user-facing length, and the guidance is explicit
     that `effort` is NOT the lever for this — prompting is.

EVERY transform asserts its anchors are present and unique before editing. A silent
no-op costs a real ~$2.1 writer call and produces a duplicate of the base arm that
looks like a null result, which is the worst failure mode this harness can have.
"""

from typing import Callable, Dict

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _cut(text: str, anchor: str, what: str) -> str:
    """Delete `anchor`, requiring it to appear exactly once."""
    n = text.count(anchor)
    if n != 1:
        raise ValueError(
            f"variant anchor for {what!r} appears {n} times, expected exactly 1. "
            f"The prompt has changed — update writer_prompt_variants.py before spending "
            f"money on a run that would silently produce the base arm.\n"
            f"anchor starts: {anchor[:120]!r}"
        )
    return text.replace(anchor, "")


def _insert_before(text: str, anchor: str, block: str, what: str) -> str:
    n = text.count(anchor)
    if n != 1:
        raise ValueError(
            f"insertion anchor for {what!r} appears {n} times, expected exactly 1.\n"
            f"anchor: {anchor[:120]!r}"
        )
    if block in text:
        raise ValueError(
            f"block for {what!r} is ALREADY PRESENT in the prompt — inserting it again "
            f"would silently duplicate it. Session 372 shipped arm B's exemplars into "
            f"production `master_editor.py`, so variant_b is now a no-op by construction; "
            f"build new arms as deltas from production instead."
        )
    return text.replace(anchor, block + anchor)


def _replace(text: str, old: str, new: str, what: str) -> str:
    """Replace `old` with `new`, requiring `old` to appear exactly once."""
    n = text.count(old)
    if n != 1:
        raise ValueError(
            f"replacement anchor for {what!r} appears {n} times, expected exactly 1. "
            f"The prompt has changed — update writer_prompt_variants.py before spending "
            f"money on a run whose delta silently did not apply.\n"
            f"anchor starts: {old[:120]!r}"
        )
    return text.replace(old, new)


def _replace_span(text: str, start: str, end: str, new: str, what: str) -> str:
    """Replace everything from `start` up to (not including) `end` with `new`.

    Both delimiters must be unique, and `start` must precede `end`. Used for the
    multi-paragraph blocks that are too long — and too full of Hebrew — to embed
    verbatim in this file.
    """
    for name, anchor in (("start", start), ("end", end)):
        n = text.count(anchor)
        if n != 1:
            raise ValueError(
                f"{name} delimiter for {what!r} appears {n} times, expected exactly 1.\n"
                f"anchor starts: {anchor[:120]!r}"
            )
    i, j = text.index(start), text.index(end)
    if i >= j:
        raise ValueError(f"span for {what!r} is inverted: start at {i}, end at {j}")
    return text[:i] + new + text[j:]


# ---------------------------------------------------------------------------
# ARM A — delete the verification scaffolding
# ---------------------------------------------------------------------------

_A_FIGURATIVE_CHECK = """### VALIDATION CHECK — Figurative Language:
Before finalizing, review each verse with figurative language:
- Does the commentary cite at least ONE specific biblical parallel from the database?
- Does it use the comparison to generate an insight about THIS verse?
- Does it provide pattern analysis (e.g., "This imagery appears 11x in Psalms, predominantly in...")?

"""

_A_QUESTIONS_CHECK = """### VALIDATION CHECK — Reader Questions:
Before finalizing, review the READER QUESTIONS input:
- Is each question elegantly addressed somewhere in the introduction essay or verse commentary?
- The answer should emerge naturally from the analysis — don't restate the question, let the reader discover the answer.
- If a question isn't addressed, weave relevant material into the appropriate section.

"""

_A_CHECKLIST_ANCHOR = "\n---\n\n## FINAL VALIDATION CHECKLIST\n"


def variant_a(prompt: str) -> str:
    """Delete the three verification passes.

    What goes: the FINAL VALIDATION CHECKLIST (24 re-read items) and the two inline
    VALIDATION CHECK blocks — i.e. every instruction to go back over finished output
    and confirm it complies.

    What STAYS, deliberately: RULE 11 (the translation test), PHRASE COVERAGE, RULE
    8b's "state the gloss flatly before quoting", and the essay/commentary "did the
    essay already say this?" rule. Those are phrased as questions but they are rules
    that carry content stated nowhere else — phrase coverage in particular is an
    explicit author requirement. Deleting them would make this a rewrite, and would
    confound the arm with a content change.
    """
    out = _cut(prompt, _A_FIGURATIVE_CHECK, "VALIDATION CHECK — Figurative Language")
    out = _cut(out, _A_QUESTIONS_CHECK, "VALIDATION CHECK — Reader Questions")

    n = out.count(_A_CHECKLIST_ANCHOR)
    if n != 1:
        raise ValueError(
            f"FINAL VALIDATION CHECKLIST anchor appears {n} times, expected 1"
        )
    head, _, tail = out.partition(_A_CHECKLIST_ANCHOR)
    if "- CROSS-CULTURAL ECHOES:" not in tail:
        raise ValueError(
            "the text after the FINAL VALIDATION CHECKLIST anchor does not look like "
            "the checklist (missing the CROSS-CULTURAL ECHOES item) — refusing to "
            "truncate the prompt at the wrong place"
        )
    return head.rstrip() + "\n"


# ---------------------------------------------------------------------------
# ARM B — flip the negative-example ratio to positive
# ---------------------------------------------------------------------------
#
# ADD-ONLY. No negative example is deleted, because deleting them would confound arm
# B with arm A (which is the deletion arm). The 24:13 ratio flips by addition.
#
# Every exemplar is a real in-house sentence, verified present in the COPY-EDITED text
# of the guide it comes from (Pss 65-71). Sourced preferentially from the beta reader's
# independently-tagged AHA / FELT / WIT moments rather than from my own taste. Full
# provenance: docs/plans/WRITER_PROMPT_POSITIVE_EXEMPLARS.md
#
# Each block carries RULE 13's anti-pastiche guard. Voice exemplars invite imitation,
# and an exemplar reproduced verbatim in a new guide is a worse failure than the
# prohibition it replaced.

_B_RULE7 = """**WORKED EXAMPLES — abstractions made concrete.** These calibrate the move only; never quote them, echo their wording, or rebuild their sentence-shapes on new material.

- An abstract theme given a route and a pair of hands: "The warrior's power, withheld until the poem is ready to hand it over, circulates from God to worshiper and home again. The victory anthem ends by arming the congregation." ("The psalm's theme of strength" is the blurry version; this is the same observation with somewhere to go.)
- One abstraction split into two felt situations: "Same eye, opposite emotional charge — the difference between being watched as a suspect and being watched over as a child."
- A psalm's whole reversal, stated as two physical conditions: "No foothold becomes a homeland."

"""

_B_RULE7B = """**WORKED EXAMPLES — aphorisms that EARN their shape.** A true epigram and a false one are indistinguishable in isolation; what separates them is whether the preceding sentences paid for it. So each is shown WITH its setup — the setup is the part to reproduce, never the cadence.

- *The demonstration first, the antithesis second.* "Psalm 40 places these lines after its earlier thanksgiving; Psalm 70 presents them independently and lets the last line hang. **The theology lives in the cut, not the wording.**" The balanced sentence names a difference the sentence before it has just put on the page.
- *A compression of a completed count, not a substitute for one.* After setting out that the enemies seek my life, delight in my ruin, and say "Aha! Aha!" — and that the faithful seek You, love Your salvation, and say "Extolled be God!" — the guide writes: "Neither group is described through a concrete deed. **Character here is appetite plus voice.**"
- *An antithesis that only labels a contrast already quoted in full.* Both readings of the harvest are given at length, and only then: "**The same earth, in the psalmist's hands a witness and in the poet's a courtier.**"

Strip the rhythm from any of the three and the content survives, because the content was demonstrated before it was compressed. That is the whole difference. Never quote, echo, or rebuild these — a borrowed epigram is a false one by construction, since nothing in YOUR psalm paid for it.

"""

_B_RULE8 = """**WORKED EXAMPLES — a routine fact handled honestly, in one clause.** This is what "state it plainly and move on" looks like on the page. Never quote or rebuild these.

- *A pure deferral — twelve words, zero inflation.* "On the lone סֶלָה here and at v.5 — and conspicuously *not* at the repeated refrain of v.6 — see v.6 below."
- *Two bare words, one breath, neither inflated — and the WORD-LEVEL FLOOR met while you pass.* "Two distinct sin-words sit in one verse: עֲוֺנֹת, from עוה, 'to twist, pervert' — guilt as distortion — and פְּשָׁעֵינוּ, from פשע, deliberate rebellion." Both are now translated; neither was made to sound profound.
- *A commentator handled at Tier 2, in a clause, with no Hebrew and no epigram.* "Ibn Ezra, ever the rationalist, reads מַקְרִן מַפְרִיס simply as 'mature': fully horned and hard-hooved, hence a valid adult animal, no smaller."

None of the three reaches for significance, and all three leave their material visible to the reader — which is all PHRASE COVERAGE and the word-and-phrase floor ask.

**WORKED EXAMPLE — a whole verse swept, nothing left dark.** Psalm 71:21 has four words, and the commentary takes each in turn, in proportion, without inflating any of them:

> תֶּרֶב is causative — You will *make great* — and what gets enlarged is גְּדֻלָּתִי, "my greatness." Not God's… [one paragraph, because the reversal genuinely rewards it]
> וְתִסֹּב, from a root meaning to go around or turn, is the second turning-verb in two verses. [Meiri's gloss, which earns its room]
> תְּנַחֲמֵנִי, "You will comfort me," is the verb of Deutero-Isaiah's opening… and it lands the verse on consolation rather than victory.

Four words, four handled. One got a paragraph, one got a sentence plus a quotation, one got a translation and a cross-reference. That spread — not equal time, but no silence — is what the floor asks for. Do this sweep on every verse, and check the LAST clause hardest: it is where words go dark.

"""

_B_RULE8B = """**WORKED EXAMPLES — quotations that passed the admission test, and the ideal cut.** Never quote, echo, or rebuild these; they show what "changes the reading" looks like in practice.

- *The test passed at full strength — TAKE A RISK.* On a verse about sins overpowering the speaker: "Malbim presses the image almost to allegory — the sins, having grown stronger than the man (for human nature is bent toward sin and cannot win the fight alone), themselves step forward and *plead* before God that He pardon them, since their very strength proves a person could not have resisted." Thirty seconds ago the verse was a confession; now the prosecution is arguing for the defence.
- *Compress.* "Rashi, characteristically concrete, refuses to let the image float: a shining face means לתת טל ומטר, 'to give dew and rain' — the favor lands as weather." Four Hebrew words turn an abstract blessing formula into weather.
- *The protected category — a Talmudic scene, not a gloss.* On a verse naming a horned, cloven-hoofed bull: מַקְרִן is written without its yod, "and the sages read it as *one* horn — deducing that the first bull Adam sacrificed was created full-grown and single-horned, unicorn-like: שור שהקריב אדם הראשון קרן אחת היתה לו במצחו, 'the ox Adam offered had one horn in its forehead' (Ḥullin 60a, via Torah Temimah). And because 'horns' precede 'hooves' in the verse, they inferred the primeval beast emerged from the earth head-first." A spelling becomes a cosmology. This is the material to squeeze LAST.
- *THE IDEAL CUT — same insight, citation gone, room not refilled.* Malbim's palm-versus-hand reading, kept without Malbim, in one sentence: "מִ**כַּ**ף, with the מ of 'from' prefixed to כַּף, is the hollow of the palm — the part that closes." The observation survives; the name, the Hebrew gloss and the setup sentence do not. The verse gets SHORTER and loses nothing, and the recovered room is not spent on something else.

**AND NOW THE FAILURES — real quotations from prior guides that should never have been printed.** These were caught by an independent reader, not by the writer. Study the pattern, not the wording.

- **FAILED — the empty gloss the guide ITSELF flagged.** On "incline Your ear to me," the guide quoted a commentator glossing it לְהַאֲזִין תְּפִלָּתִי, "to listen to my prayer" — having already written, in its own prose, that *there is nothing more to be had from it.* It kept the quotation anyway. **This is the single most common failure and the easiest to stop: if you find yourself writing that a gloss adds little, is unsurprising, is the obvious reading, or that there is nothing more in it — you have already completed the admission test. DELETE THE QUOTATION. Do not print the verdict and the evidence together.**
- **FAILED — the gloss that restates the verse's own image.** On enemies wrapped in disgrace, the guide quoted a commentator glossing it יִהְיוּ מְסוּבָּבִים בִּכְלִימָּה כְּהַלְבוּשׁ, "let them be encircled with disgrace like a garment." The garment is already in the Hebrew. The gloss tells the reader only that a medieval commentator also saw what they can see. **FIXED:** describe the image yourself in a clause and move on; cite nobody.
- **FAILED — the citation used as scaffolding for your own point.** The guide noticed, correctly and by itself, that Psalm 71 reverses Psalm 31's clause order — then attached a Radak citation to the front of it as though the observation needed a sponsor. **FIXED:** it is your observation. Make it in your own voice. A commentator is quoted when HE changes the reading, never to authorise something you worked out yourself.
- **FAILED — the synonym-swap paraphrase.** "Until this day, with what has passed over me" for עַד־הֵנָּה. This translates a phrase with a slightly different phrase. It is not a reading; it is a restatement wearing a name. **FIXED:** translate it yourself, in four words, unattributed.

**COUNT THEM BEFORE YOU FINISH.** A 24-verse psalm should land near 24 full Hebrew-quoted commentator citations. If your count is 34, then ten must go — and they are the ten that change the reading LEAST, not the ten that are easiest to lift out. Removing them does not create room for anything else.

"""

_B_RULE3B2 = """**WORKED EXAMPLES — grammar shown, never named.** Calibrate the technique, never the wording.

- *Technique 3 — a whole theological claim carried by bolding two words against each other, with no term named at all.* "Numbers 6:25 reads יָאֵר ה׳ פָּנָיו **אֵלֶיךָ**, 'may the LORD make His face shine **toward you**.' Psalm 67 reads יָאֵר פָּנָיו **אִתָּנוּ**, 'may His face shine **with us**.' The original pictures God's face turning *in your direction*, attention aimed at a recipient; the psalm asks for that shining face to *accompany* — to dwell alongside." The reader sees the change, and never needs the word for it.
- *Bolding sustained across a chain until the morpheme becomes audible.* הַצִּילֵ**נִי**, עֲנֵ**נִי**, פְּדֵ**נִי** … and then שֻׁלְחָ**נָם**, עֵינֵי**הֶם**, עֲלֵי**הֶם** — "The ear registers the reversal — *me* becoming *them* — as a change of ending, before the mind has parsed a single curse. The suffix is the turn."
- *Techniques 1 and 2 together — bold the letter, then say in plain words what it does.* The shape to reproduce: bold the exact prefix inside the Hebrew, then tell the reader what that letter is doing — "the little word 'by'", "the 'but' that swings the sentence around", "'as,' in the course of". Bolding shows which mark you mean; the plain-words clause is what teaches it. Never one without the other.

"""

_B_LANDING = """**WORKED EXAMPLES — three landings that worked, deliberately unlike each other in shape.** Do not reproduce their wording or their imagery; find the shape your own psalm offers.

- *A paraphrase stripped to the human minimum.* "He is not asking, at this moment, to be rescued from the water or vindicated before the court. He is asking for one person to sit near him and move their head — to signal, wordlessly, *I see that this is terrible.* And he looks up, and the room is empty."
- *An undressing, after the apparatus has done its work.* "And here the analysis can rest. Strip away the doublet, the name-count, the frozen idiom, and what remains is the oldest prayer there is: *I have nothing, and I cannot wait. Come now.*"
- *A direct address, earned by everything before it.* "If you have ever been the person without a place at anyone's table, this verse is doing something the storm cannot: it is turning the whole apparatus of cosmic power toward the one who has no one."

Two, three, four sentences. None of them names a device, cites a source, or reaches for an epigram. Length is not what makes a landing — plainness is.

"""

# (block, anchor it is inserted BEFORE, description for the error message)
_B_INSERTIONS = [
    (_B_RULE7, "### RULE 7b: NO FALSE PROFUNDITY", "RULE 7 exemplars"),
    (_B_RULE7B, "### RULE 8: NO ORPHANED FACTS", "RULE 7b exemplars"),
    (_B_RULE8, "### RULE 8b: THE COMMENTATOR'S BURDEN", "RULE 8 exemplars"),
    (_B_RULE8B, "### RULE 9: COMMIT TO AMBIGUITY", "RULE 8b exemplars"),
    (_B_RULE3B2, "### RULE 3c: NO LINGUISTICS JARGON", "RULE 3b-2 exemplars"),
    (_B_LANDING, "**Pipeline voice (FORBIDDEN):**", "affective landing exemplars"),
]


def variant_b(prompt: str) -> str:
    """Attach a positive worked-example block to each rule that currently teaches by
    prohibition alone."""
    out = prompt
    for block, anchor, what in _B_INSERTIONS:
        out = _insert_before(out, anchor, block, what)
    return out


# ---------------------------------------------------------------------------
# ARM C — conciseness instruction
# ---------------------------------------------------------------------------
#
# Placed in STYLISTIC GUIDANCE rather than as a new numbered RULE, so it reads as a
# standing property of the voice rather than one more thing to verify.
#
# Deliberately NOT phrased as a word budget or a percentage. Session 370 showed this
# prompt is sensitive to permission-shaped language in both directions: "going over
# budget is better than losing it" rebounded length +19%, so a numeric target invites
# either gaming or padding-to-fill. The lever here is the ordinary conciseness
# instruction the guidance describes, aimed at the sentence rather than the document.

_C_INSTRUCTION = """**Say it once, at the length it needs.** Every paragraph you write should be as short
as its content allows and no shorter. Length is earned by material, never by
elaboration: a point that is fully made in two sentences is finished at two sentences,
and a third sentence restating it in fresh diction subtracts. When you have said the
thing, stop — do not summarize what you just said, do not pivot to a closing cadence,
and do not add a sentence whose only job is to end the paragraph gracefully. Prefer the
shorter of two formulations that carry the same content. This is a constraint on
*prose*, not on *coverage*: it never licenses skipping a phrase, dropping a verse, or
thinning the evidence — cut words, never material.

"""

_C_ANCHOR = "**Vary your texture.**"


def variant_c(prompt: str) -> str:
    """Add a conciseness instruction to STYLISTIC GUIDANCE."""
    return _insert_before(prompt, _C_ANCHOR, _C_INSTRUCTION, "conciseness instruction")


# ---------------------------------------------------------------------------
# ARM D — SUBTRACT (Session 372)
# ---------------------------------------------------------------------------
#
# Session 371 ran seven arms that each ADDED something, and the metrics oscillated
# without ever improving jointly. Two structural items had never been an A/B
# variable, and each one's known cost is the other's cause:
#
#   (i)  the FINAL VALIDATION CHECKLIST (24 re-read items) + 2 VALIDATION CHECK
#        blocks. Arm A deleted these and produced the best citation numbers ever
#        measured (INERT 6, 3.3 commentators/1k vs base's 4.0), the best wit score
#        of any Opus 5 arm (6 vs 3), and the second-best word coverage (79.2%).
#        Its costs were length (+13%) and a Tier-1 overshoot — both of which (ii)
#        predicts, because A deleted the item that carried the count while leaving
#        the floor that forces the padding.
#
#   (ii) "300-500 words per verse", which `git log -S` dates to Session ~130 —
#        written for models that UNDER-produced, never revisited in 360+ sessions,
#        never varied in any arm. It is binding: across all seven Session-371 arms
#        the median verse section is 330-437 words and never once falls below 330.
#        24 verses x 300 = a 7,200-word floor the prompt itself mandates. It is
#        also the likeliest reason arm C's conciseness instruction backfired — the
#        instruction contradicted a word target sitting 15K chars further down —
#        and the likeliest engine of inert citations, since the cheapest way to
#        fill 300 words on a routine verse is to quote a commentator.
#
# Anthropic's current Opus 5 guidance independently recommends (i) as a DELETE
# ("removing them reduces over-verification with no capability regression") and
# notes that self-check phrasing inverts standard practice on this model.
#
# Arm D deletes both. It keeps the Tier-1 budget, the word floor and PHRASE
# COVERAGE, which are stated in the RULE bodies — the checklist items were
# duplicates of them, not the only home.

_D_WORDCOUNT_OLD = """Then provide commentary (300-500 words per verse).**
   - **Target:** 1-3 transformative angles per verse.
"""

_D_WORDCOUNT_NEW = """Then provide commentary. Length follows the material.**
   - **Target:** 1-3 transformative angles per verse.
   - **There is no per-verse word target.** A verse holding a real discovery earns a long section; a verse of routine construction is complete in a short one. If your sections all come out about the same length, they were filled rather than written.
"""

# Session 371's affect audit: `Emotional impact` scored 7/10 in every single arm.
# A number that never moves is measuring the ceiling the rule sets, not the arms.
# The fix is a SCOPE change, not a permission grant — Session 370 showed this
# prompt reads permissive language ("spend what you save") as licence and rebounds.
# So the built passage stays capped at exactly one; what is un-capped is the plain
# human sentence, which was never the thing that caused dilution.
_D_PATHOS_OLD = (
    "Exactly one per guide — spread it thinner and nothing lands. One means one "
    "across the WHOLE guide: if the essay carries the landing, the corresponding "
    "verse's commentary may point at it in a single plain sentence with different "
    "imagery — never rebuild it."
)

_D_PATHOS_NEW = (
    "**What is capped is the BUILT PASSAGE: exactly one per guide.** If the essay "
    "carries it, the corresponding verse's commentary may point at it in a single "
    "plain sentence with different imagery — never rebuild it. **The cap is on "
    "construction, not on feeling.** A single plain human sentence, where the "
    "material genuinely carries one, is not a second landing and is not rationed — "
    "the discipline is that it stays a sentence and never grows into a passage."
)


def _delete_scaffolding(prompt: str) -> str:
    """Arm A's deletion, reused: the two inline VALIDATION CHECK blocks and the
    24-item FINAL VALIDATION CHECKLIST."""
    out = _cut(prompt, _A_FIGURATIVE_CHECK, "VALIDATION CHECK — Figurative Language")
    out = _cut(out, _A_QUESTIONS_CHECK, "VALIDATION CHECK — Reader Questions")

    n = out.count(_A_CHECKLIST_ANCHOR)
    if n != 1:
        raise ValueError(
            f"FINAL VALIDATION CHECKLIST anchor appears {n} times, expected 1"
        )
    head, _, tail = out.partition(_A_CHECKLIST_ANCHOR)
    if "- CROSS-CULTURAL ECHOES:" not in tail:
        raise ValueError(
            "the text after the FINAL VALIDATION CHECKLIST anchor does not look like "
            "the checklist (missing the CROSS-CULTURAL ECHOES item) — refusing to "
            "truncate the prompt at the wrong place"
        )
    return head.rstrip() + "\n"


def variant_d(prompt: str) -> str:
    """Delete the verification scaffolding AND the per-verse word target; uncap the
    plain human sentence."""
    out = _delete_scaffolding(prompt)
    out = _replace(out, _D_WORDCOUNT_OLD, _D_WORDCOUNT_NEW, "per-verse word target")
    out = _replace(out, _D_PATHOS_OLD, _D_PATHOS_NEW, "affective-landing cap")
    return out


# ---------------------------------------------------------------------------
# ARM E — SUBTRACT + THE TRANSLATION SLOT (Session 372, author's design)
# ---------------------------------------------------------------------------
#
# The author's idea: print a full English translation of the verse at the top of
# each verse block, offset. Then coverage is guaranteed BY CONSTRUCTION and the
# commentary below is free to select purely on how interesting the material is.
#
# This converts an obligation into a slot, which is the one move that escapes the
# standing hazard (five instances where added restraint text produced its
# opposite): there is nothing left to exhort. It also severs the coverage ->
# citation channel at the source, because a commentator can no longer be the
# cheapest way to make a dull word visible — the translation already did.
#
# So arm E DELETES what the slot replaces: the PHRASE COVERAGE paragraph, the
# WORD-AND-PHRASE FLOOR block, and arm B's "whole verse swept" worked example
# (which teaches the sweep and would now contradict the contract).
#
# NOTE for scoring: `check_phrase_coverage.py` matches Hebrew skeletons in the
# commentary BODY. The translation line is English, so it does not move that
# number. Under arm E the old metric no longer measures coverage — it measures
# how much of the verse the commentary chose to ENGAGE. A fall is the intended
# behaviour, not a regression; read it next to the translation-line check.

_E_TRANSLATION_STEP = """**2. THEN give the whole verse in English, offset as a block quote.**
   - Format: one markdown block quote line, beginning with `> `, immediately after the Hebrew and before your commentary.
   - Example:
     > When I call, answer me, God of my righteousness — in the narrow place You made room for me; be gracious to me and hear my prayer.
   - **It is YOUR translation.** You are the scholar of RULE 12, not a compiler of someone else's version. Render the verse as you actually read it, and let the choices you have argued for elsewhere show up here.
   - **Translate the WHOLE verse — every word, no ellipsis, no summary.** This line is the reader's guarantee that nothing in the verse is dark to them.
   - **Every verse gets its own Hebrew line and its own translation, including when you group verses for commentary.** Grouping shares the analysis, never the text: print verse 5's Hebrew and translation, then verse 6's, then the commentary that covers both.
   - Keep it clean: no Hebrew, no citations, no brackets of alternatives, no commentary. Where a word is genuinely undecidable, pick the reading you argue for below and let the commentary do the arguing.

"""

# What the slot replaces. Delimited by two unique ASCII anchors because the block
# between them is ~3.5K chars of mixed English and Hebrew.
_E_SPAN_START = "   - **Phrase coverage (CRITICAL"
_E_SPAN_END = "**ITEMS OF INTEREST TO ILLUMINATE**"

_E_SPAN_NEW = """   - **COVERAGE IS ALREADY DISCHARGED — now select on interest alone.** The translation line above has rendered every word of this verse, so the reader can always say what each word means. Nothing below it is owed to completeness. Choose what to discuss by one question: *is this genuinely interesting?* A phrase you pass over in silence is not a gap — it is a judgement that the translation already said everything worth saying about it, and that judgement is right far more often than not.

     **Do NOT walk the verse word by word looking for something to say.** That habit is what inflates a routine phrase into false profundity (RULE 7b) and what reaches for a commentator on a word that needed nothing (RULE 8b). The translation carries the routine words. You are here for the ones that repay attention.

"""

# Arm B's RULE 8 exemplar block ends with a worked example of sweeping a whole
# verse so no word is left dark. Under the translation slot that teaches the
# behaviour we just cancelled, so it comes out.
_E_SWEEP_START = "**WORKED EXAMPLE — a whole verse swept, nothing left dark.**"
# End at the heading that follows arm B's RULE 8 block. Do NOT end at the next
# WORKED EXAMPLES block — that one is inserted before RULE 9, so the span would
# swallow the whole of RULE 8b including the Tier-1 budget. (It did, first try;
# the pre-flight check below is the only reason that cost nothing.)
_E_SWEEP_END = "### RULE 8b: THE COMMENTATOR'S BURDEN"


def variant_e(prompt: str) -> str:
    """Arm D, plus the offset translation slot that discharges coverage."""
    out = variant_d(prompt)
    # Insert the translation step, then renumber the commentary step 2 -> 3.
    out = _insert_before(
        out, "**2. Then provide commentary. Length follows the material.**",
        _E_TRANSLATION_STEP, "translation slot",
    )
    out = _replace(
        out,
        "**2. Then provide commentary. Length follows the material.**",
        "**3. Then provide commentary. Length follows the material.**",
        "commentary step renumber",
    )
    out = _replace_span(
        out, _E_SPAN_START, _E_SPAN_END, _E_SPAN_NEW,
        "phrase coverage + word-and-phrase floor -> translation slot",
    )
    out = _replace_span(
        out, _E_SWEEP_START, _E_SWEEP_END, "",
        "arm B's whole-verse-sweep worked example",
    )
    return out


# ---------------------------------------------------------------------------
# registry
# ---------------------------------------------------------------------------

def variant_base(prompt: str) -> str:
    """Current prompt, unchanged. Needed because A/B/C are deltas from a prompt whose
    third RULE 8b revision has never been run."""
    return prompt


VARIANTS: Dict[str, Callable[[str], str]] = {
    "base": variant_base,
    "A_no_scaffolding": variant_a,
    "B_positive_examples": variant_b,
    "C_conciseness": variant_c,
    # Same transform as B, run under a fresh id so the first B (contaminated
    # exemplars, no word-level floor, old observation guards) stays on disk for
    # comparison. Session 371 second pass.
    "B2_final": variant_b,
    # Session 371 third pass: word-and-phrase floor strengthened (production side)
    # plus B's citation block rebuilt around real failed quotations and a restored
    # concrete IDEAL CUT.
    "B3_final": variant_b,
    # Session 371 fourth pass: coverage/citation channel severed — a commentator may
    # never be the instrument of coverage (production side, floor + RULE 8b).
    "B4_final": variant_b,
    # Session 372. Production now carries arm B's exemplars and no longer carries
    # B4's two edits, so these are deltas from the B3 configuration.
    "D_subtract": variant_d,
    "E_translation": variant_e,
}

# Session 373: the author read arm E and moved it to production. `master_editor.py`
# now IS `variant_e(the Session-372 prompt)` — verified byte-identical to
# output/psalm_71/_prompt_ab/E_translation/_prompt_template.txt before shipping.
#
# So variant_d and variant_e are no-ops by construction, exactly as variant_b became
# in Session 372. They do not need a guard clause: `_delete_scaffolding` calls `_cut`
# on the two VALIDATION CHECK blocks, which are gone, and `_cut` raises on a count of
# 0. Any attempt to re-run D or E fails during the harness's pre-flight build, before
# a writer call is paid for. Build new arms as deltas from production.

LABELS: Dict[str, str] = {
    "base": "Baseline",
    "A_no_scaffolding": "Arm A - no verification scaffolding",
    "B_positive_examples": "Arm B - positive exemplars",
    "C_conciseness": "Arm C - conciseness instruction",
    "B2_final": "Arm B2 - exemplars + word floor + essay promotion",
    # Label is interpolated as "Psalm <n> (<label>).docx" — keep it short and do NOT
    # repeat the psalm number, or the filename doubles it.
    "B3_final": "B3",
    "B4_final": "final",
    "D_subtract": "Arm D - subtract",
    "E_translation": "Arm E - translation slot",
}
