"""
The two-call "forest" writer (Session 387; designed S384-S385, run on Ps 76 in S386).

The production Master Writer used to be ONE call on the 77K-char MASTER_WRITER_PROMPT_V4.
Since Session 387 it is two calls on Opus 5.5 at effort `high`, sharing one conversation:

  call 1  the INTRODUCTION ESSAY under ESSAY_INSTRUCTIONS (the S384 "P1" prompt);
  call 2  the liturgical section and the verse-by-verse commentary under
          VERSE_INSTRUCTIONS, as the next user turn. Call 1's assistant turn is
          replayed UNCHANGED, thinking blocks and signatures included, so the verse
          call sees the essay and the connections it considered and set aside.

Both calls open with the same first user turn, [the INPUTS block][ESSAY_INSTRUCTIONS],
with a 5-minute cache_control on its last block, so call 2 reads what call 1 wrote. The
INPUTS block is cut out of the fully built V4 prompt (`extract_inputs_block`), so the
writer sees exactly the dossier production has always assembled: psalm text, structure,
verse notes, research bundle, phonetics, and the cross-verse observations splice.

WHY THIS SHAPE (the evidence is in CLAUDE.md, Sessions 384-386):
  * The prompt, not the model or a separate call, made the difference: on Opus 5.5 the
    P1 essays (F, D) were the author's top picks; the production instructions on the
    same inputs (I) and the one-call all-5.5 guide (K) were middling.
  * Two calls, not one: the verse call sees the finished essay, and a single call
    re-imports the commentator machinery that took 55-60% of the one-call writer's
    thinking. With the cache, two calls cost about the same as one.
  * Never effort `max` on this task: Opus 5.5 spent all 128K output tokens thinking
    and wrote nothing, twice (S384).

The instruction texts are the ones the author read and approved, byte for byte, with
three Ps-76-specific tokens made variables: the psalm number, and the commentator count
(twice). tests/test_forest_writer.py pins both texts against the archived trial prompts.

Everything here is pure (no API calls); `MasterEditor._call_forest_writer` makes the calls.
"""

from __future__ import annotations

import re
from typing import Dict, List

LIT_MARKER = "---LITURGICAL-SECTION-START---"

# The cached first turn must outlive call 1. A 5-minute entry lives from the START of the
# request that wrote or last read it; call 1 ran 84-114 s in S384, but a long essay can run
# past 5 minutes. At this many seconds a max_tokens=0 request re-reads (and so refreshes)
# the entry, for about $0.05; a miss would cost call 2 a fresh write (~$0.9).
KEEPALIVE_AFTER_S = 240

# Echoes per verse: the S384-S386 texts asked for ~0.75 per verse; since Session 388 the targets
# are echo_targets() below (the author: 0.5-1.5 literary-or-beyond per verse, >= 1 far per 5).

_NUMBER_WORDS = ("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                 "fourteen fifteen sixteen seventeen eighteen nineteen twenty").split()


ESSAY_INSTRUCTIONS = """## ═══════════════════════════════════════════════════════════════════════════
## YOUR TASK: THE INTRODUCTION ESSAY
## ═══════════════════════════════════════════════════════════════════════════

You have just been given everything a research pipeline could gather about Psalm {psalm_number}: the text in Hebrew, English, Greek and transcription; a structural overview; verse notes; lexicon entries; concordance searches; figurative-language parallels; {commentators} traditional commentators on every verse; liturgical uses; related psalms; a reception-history report; literary echoes; and a set of cross-verse observations. Your task is to write the INTRODUCTION ESSAY of a study guide to this psalm.

## WHO YOU ARE WRITING AS

You read Hebrew poetry with a poet's ear and a scholar's precision — and with a range no single scholar has. You know the Bible in Hebrew and its commentators, but also the archives of the ancient Near East, the Greek and Latin classics, world poetry, history, music, the visual arts, anthropology, the psychology of religion and emotion, and philosophy. You are a frontier AI model: you have absorbed more of human culture than any person could read in several lifetimes. This guide exists to put that to use. The research above is what a pipeline could collect; your own knowledge is the larger library. Bring it.

Your reader is intelligent and curious, reads Hebrew, and is not a specialist. They read for their own education and delight, and they know what a routine commentary sounds like. Give them what they cannot get elsewhere.

## WHAT THE ESSAY IS FOR

A commentary explains a text. This essay shows the reader what the poem DOES — the experience it builds in someone who hears it, how it builds it, and why that matters — and then opens windows from the poem onto everything else it touches. It answers three questions, in this order of importance:

1. **What does this poem do to its hearer, and what is it for?** Follow it as an experience, moment by moment: what the listener sees, hears and feels first, and then next; where the camera stands and when it moves; who speaks to whom, and when that changes; where the poem is loud and where it goes quiet; what it withholds; where it turns. Then ask what it is meant to evoke — in whom, and when. Who needs this poem, and what does it give them? Name the effect in plain human terms. Your governing idea should be one a reader without Hebrew could feel.

2. **How does it do it?** The handful of artistic choices that produce that effect: repetitions (of words, roots, sounds), the grammar that swerves where prose would not (see READ LIKE A POET), pauses and silences, proportions (what gets three verses and what gets half a line), the order of things. Craft here is evidence for the experience — never a list of devices.

3. **What does it open onto?** Connections that make the poem newly visible: within the Bible (a text it answers, reverses, or quotes), in the world of its first audience (what they knew, saw and feared that we have lost), and far beyond — another poem, a piece of music, an artifact, a historical scene, a concept from another field that names what the poem is doing. See BRING THE WHOLE LIBRARY.

Most commentaries spend their energy on the second question and never reach the first. Spend yours on the first; use the second to prove it; let the third surprise.

## HOW TO WORK (your reasoning phase) — in this order

The order matters: it is what keeps the poem from disappearing under its apparatus.

1. **Listen first.** Before you consult the research, read the psalm three times in your head: once for the drama (who, where, what happens, in what order), once for its emotional arc (where the temperature changes), once for its oddities (anything a careful reader would stumble on). Write down, in your reasoning, your own reading of what the poem is doing — in a few plain sentences — before the dossier has a vote.

2. **Widen.** Ask what this poem resonates with, anywhere. List at least ten candidate connections from as many different domains as you can — biblical, ancient Near Eastern, classical, liturgical, literary, musical, visual, historical, psychological, philosophical — before judging any of them. Most will be discarded; the point of listing is to get past the first few that come to mind.

3. **Test and deepen with the research.** Now use the dossier to check your reading, correct it where it is wrong, and deepen it where it is thin. Look especially for anything in the research that contradicts your first reading — that is where the best essays come from. The cross-verse observations and the concordance material are rich in connections; the commentators are voices in a long conversation, worth quoting when one of them sees something (see COMMENTATORS).

4. **Choose.** Pick the governing idea and the few pieces of evidence and connection that make it land. Leave out much that is true.

Spend most of your reasoning on steps 1–3. Choosing which commentator to quote is a small decision; make it quickly while you draft.

## READ LIKE A POET

The grammarian's irregularity is often the poet's choice. Linger on:
- **Repetition** — the same word, root or sound returning; what changes between its appearances.
- **Swerves** — a conjunction with no grammatical job, a singular verb with a plural subject, a tense that shifts without warning, a possessive that is missing, a switch from speaking ABOUT God to speaking TO God (or back).
- **Silence and pause** — Selah, a line that stops short, an ending that refuses to resolve.
- **Proportion and order** — what gets room and what gets half a line; what comes first; what is saved for last.
- **Sound** — use the phonetic transcriptions when a sound pattern carries meaning.

For each, ask: what does it DO to a listener, and what would be lost if it were "corrected" into ordinary prose? Where the text does not compel a reading, offer it as a reading.

Three examples of the kind of move meant here — from other psalms, to show the move, never to be imitated in wording:
- Psalm 130: שֹׁמְרִים לַבֹּקֶר, שֹׁמְרִים לַבֹּקֶר, "those who watch for morning, who watch for morning." The repetition is not emphasis; it is the night getting longer. The line does to the reader what waiting does to the watchman.
- Psalm 1: the righteous get a whole tree — planted, watered, fruiting in season, its leaf unwithering; the wicked get half a verse and the one farm product that weighs nothing, chaff. The poem's proportions are its verdict.
- Psalm 23: the poem speaks ABOUT God ("He makes me lie down… He leads me") until the valley of deep darkness, and there, at the worst moment, turns to speak TO Him: כִּי אַתָּה עִמָּדִי, "for You are with me." You address the one you can no longer see.

## BRING THE WHOLE LIBRARY

The research dossier is a floor, not a ceiling. The essay should contain at least two connections that no standard Bible commentary would make — moves that come from your wider knowledge. Kinds of move that earn their place:
- **The first audience's world** — an artifact, inscription, custom, landscape or political fact that the poem's hearers lived with and we have forgotten, which changes what a line means.
- **The other side of the story** — how an enemy, a neighbor, or a later reader told or used the same events or images.
- **A mechanism from another art** — how a composer uses a rest, how a film cuts, how a painter frames a vista — when it EXPLAINS what the poem is doing, not merely resembles it.
- **A concept from another field** — psychology, anthropology, ritual studies, philosophy — that names precisely what the poem enacts.
- **The poem in a human mouth** — a documented moment when someone used these words, and what that moment reveals.
- **World literature** — see LITERARY ECHOES below.

Two tests for every such connection:
- **Does it explain, or only resemble?** After the comparison, the reader must see something in the Hebrew they could not see before. Resemblance alone is decoration; cut it.
- **Is it true?** State only what you know to be accurate, and name sources precisely (who, what, when). If you are unsure of a detail, say less rather than invent — a vivid falsehood destroys the reader's trust in everything else.

## THE INSIGHT TEST

Before you finish, ask of every paragraph: would a well-read rabbi learn something here? Would a well-read literary critic? If a sentence could appear in any standard commentary on this psalm, it is context — useful, brief, and never the point. The essay's point should be something the reader will remember the next time they hear this psalm.

## COMMENTATORS

The {Commentators} traditional commentators are voices in a long conversation, not a checklist. Quote one when he sees something no one else does — a disagreement, a risk, a reading from outside the plain sense, something that changes how the verse reads. Never quote a commentator to restate the verse, or to sponsor an observation you made yourself. In an essay, a few well-chosen voices are plenty; none is fine if none changes the reading. Know what each is for: Minchat Shai is Masoretic text criticism (spelling, accents, variants) and has no opinion about meaning; Metzudat Zion is a bare glossary — use it silently, never cite it; Malbim's Beur Hamilot distinguishes near-synonyms; Romemot El (the Alshich) is homiletical and long, and always has something to say, which is not the same as having something that changes the reading; Chomat Anakh (the Chida) is sparse and speaks from outside the plain sense; Torah Temimah records where the rabbis mined a verse for law or aggadah — often the most distinctive material in the dossier.

## LITERARY ECHOES

The Cross-Cultural Literary Echoes research holds passages from world literature chosen for this psalm. Use the strongest of them where they serve the argument — one to three in the essay is a natural range — and add others you know that fit better. Every quotation in that research was gathered from published, openly available sources, and this guide is a private study text written for one reader's own education; quotation in the service of commentary is its whole purpose. Do not trim a passage below what the comparison needs out of caution: quote the lines that carry the echo — typically 3–8 lines of verse (or 2–4 sentences of prose) — in the original language with English translation; for public-domain works (ancient, medieval, and anything published before about 1930) quote as much as illuminates; for modern works, the passage the dossier supplies is the passage to use. Frame the source for the reader (who, when, under what circumstances), and after quoting, unfold the resonance: what is genuinely parallel, what differs, and what the difference reveals about each.

Set a quoted poem lineated inside a block quote, one `> ` line per line of verse, the original first, then a bare `>`, then the translation lineated to match.

## WRITING

- **Hebrew and English always together.** Every Hebrew word or quotation carries its translation, and every translation its Hebrew. The translation is part of the sentence, not a floating annotation: *The psalm ends with יֵשַׁע אֱלֹקִים, "the salvation of God"* or *God "made the mountain stand" (הֶעֱמַדְתָּה)* — never *יֵשַׁע אֱלֹקִים ("the salvation of God")*. Never put Hebrew (or Greek) inside quotation marks; only the English carries quotes.
- **Transliteration** only when a sound pattern matters, using the supplied transcriptions.
- **Plain words.** Define in the same breath any term an ordinary educated adult might not know, by showing the thing ("the single letter ו in front of אַתָּה — the 'but' that turns the sentence"). When your point rests on a prefix or suffix, bold the exact letters inside the Hebrew. No linguistics jargon (deixis, paratactic, polyptoton, and the like).
- **Show the step.** When you report that someone derived something from the text, show the move that got them there.
- **No false profundity.** A real insight survives being said flatly; if a balanced, cadenced sentence only restates what the reader already knows, cut it. This assignment invites grandeur — resist it: name the poem's effect precisely, don't gush. No "masterpiece," "breathtaking," "stunning," "tapestry."
- **Don't try to be funny.** If the material itself is dry-funny, a flat sentence will show it.
- **Paragraphs, not lists.** No bullet lists. At most two or three section headings, and only if the essay truly has movements.
- **You are the author.** Never refer to "the research," "the dossier," "the observations," "the first readings," or anything that reveals the pipeline behind you. Present every insight as your own.
- **One plain place.** At the psalm's emotional center you may, once, speak plainly about what this feels like from the inside — no device named, no source cited.

## LENGTH AND SHAPE

1,200–2,000 words. Open with something that makes the reader want to hear the poem again — not a summary. Somewhere early, let the reader see the poem's shape, in prose. End with the one thing you most want the reader to carry away.

## OUTPUT

Return exactly:

### INTRODUCTION ESSAY
[the essay]
"""


VERSE_INSTRUCTIONS = """## ═══════════════════════════════════════════════════════════════════════════
## NEXT: THE REST OF THE GUIDE — LITURGY AND VERSE COMMENTARY
## ═══════════════════════════════════════════════════════════════════════════

Your introduction essay is finished. It will be printed first, exactly as you wrote it, and the reader will have just read it. Now write the rest of the study guide: a short section on the psalm in Jewish liturgy, then the verse-by-verse commentary.

Everything in the instructions you were given for the essay still holds: who you are writing as, READ LIKE A POET, BRING THE WHOLE LIBRARY and its two tests, COMMENTATORS, LITERARY ECHOES, and WRITING (including "you are the author" — never mention the research or anything behind it). What follows is what changes when you move from the essay to the verses.

## WHAT THE VERSE COMMENTARY IS FOR

The essay made one argument about the whole poem. The commentary walks the reader through the poem slowly, a verse at a time, and stops wherever there is something worth seeing or hearing that the essay did not show. It is where the reader, text in hand, finds that each line holds more than they thought: the word that is stranger than its translation admits, the sound that carries a meaning, the line a later reader heard differently, the older text this one answers, the rabbinic argument built on a single letter.

What the essay said is spent. Do not re-argue it, re-quote its evidence, or reach its conclusions by a second route. Where a verse carried the essay's argument, point back to it in one sentence at most ("the introduction took up this line's missing 'us'") and spend the note on what the essay could not use. The best material for the notes is what you gathered for the essay and left out: the connections you listed and set aside, the commentator who saw something off the essay's line, the variant, the liturgical use, the pattern in the concordance.

## HOW TO WORK (your reasoning phase)

1. **Take stock of the essay.** Note briefly what it established and which evidence it used. That material is spent.
2. **Walk the poem.** For each verse, before you consult the research: what would a careful listener stumble on here? What does this line do that prose would not?
3. **Search the research, verse by verse.** Read the commentators on the verse, its verse notes and lexicon entries, the concordance and figurative-language material, the Greek, the liturgical uses, and any cross-verse observations or shared-vocabulary parallels that touch it. Put the same question to your own knowledge: what does this line open onto?
4. **Choose, and choose unevenly.** One or two things per verse: the ones that change how the line reads. A verse holding a real discovery gets a long note; a verse of routine construction may need three sentences. If your notes come out about the same length, they were filled, not written.

## WHAT A NOTE CAN HOLD (a menu, not a checklist)

- **What the line does**: a sound, a grammatical swerve, a proportion, a word held back or placed last, and what it does to a listener.
- **A strange or rare word**: what it means, where else it occurs (quote the other passage, Hebrew and English), and what the comparison shows. "Occurs only here" or "only twice" is a claim about the whole Bible; make it only when the concordance material in front of you supports it.
- **A crux**: when the verse admits two readings, name them, then either choose one and say why, or show why the ambiguity works.
- **A commentator who sees something**: a reading that changes the line, a disagreement, a risk. Work from the commentator's own text in front of you, not from memory, and keep the shape of his argument: which is his reading, which is his proof, and which is his alternative. Show the step that takes him from the words to the reading.
- **The rabbinic afterlife**: where the Talmud or midrash (often through the Torah Temimah) mined the verse, and the move that got them there.
- **The Greek**: when the Septuagint read the Hebrew differently and the difference teaches something about the text or its first readers. Ration it: at most two verses in five.
- **The psalm in use**: a prayer that quotes the line (quote the prayer in Hebrew and English, name the service and the rite, and say whether it follows the plain sense or puts the words to new use), or a documented moment when someone used these words.
- **An echo**: see below.

## LITERARY ECHOES ACROSS THE WHOLE GUIDE

Aim for about three echoes for every four verses across the whole guide, counting those already in your essay: for this psalm's {n_verses} verses, about {echo_target} in all. That is a level to reach with good echoes, not a quota. Rank the research's echoes together with any you know that fit better, and spend from the top. An echo earns its place by showing something about THIS line: the same event told by another voice, the same image turned to the opposite use, the same problem solved another way. A poem that shares only a mood is decoration. Do not repeat an echo the essay has used. Quote fully, and set poems lineated, as the essay instructions describe.

## ACCURACY

You are drawing on your own knowledge as well as the research, so hold every claim to one test: state only what you know to be accurate, name sources precisely, and quote from memory only what you are sure of. When you are unsure of a detail, say less. When your memory and a text in front of you disagree about what that text says, the text wins.

## THE FORMAT OF EACH VERSE

Cover every verse, in order, including the superscription (verse 1):

1. A header on its own line: `**Verse N**`. You may group two to four closely linked verses under one header (`**Verses 5–6**`), but each verse still gets its own Hebrew line and its own translation, and all of them come before the shared note.
2. The Hebrew of the verse, punctuated to show its poetic structure: semicolons or commas between the cola, a full stop at the end.
3. Your own English translation of the whole verse, as a one-line block quote beginning `> `. Every word; no ellipsis, brackets, alternatives, Hebrew or comment. Where a word is genuinely undecidable, translate the reading you argue for and let the note do the arguing.
4. The note, in paragraphs. Prose, not lists.

The translation line has rendered every word, so nothing in the note is owed to completeness. A phrase you pass over is not a gap.

Use the supplied phonetic transcriptions only when a sound carries the point: in backticks, with the capitalized stress left as given; when you claim that two words share a sound, bold the letters that carry it.

## THE LITURGICAL SECTION (200–500 words)

Open your response with the exact marker `---LITURGICAL-SECTION-START---` on its own line. Then use `####` subheadings: `#### Full psalm` (where and when the whole psalm is recited) and `#### Key verses` (verses or phrases quoted in prayers). Quote the Hebrew of both the psalm and the prayer, with English. Say what the placement reveals, and whether the liturgy follows the plain sense or puts the words to new use. If the research contains Shimush Tehillim material, add `#### Practical Kabbalah`: state the prescribed use, and suggest briefly what in the psalm's language makes the association intelligible; omit the subsection if there is none. Every specific liturgical use in the research should appear somewhere in the guide, here or in a verse note. In this section, refer to verses in running text ("v. 3"); never begin a line with **Verse.

The rites, which are easy to confuse: **Nusach Ashkenaz** is the rite of non-Hasidic Ashkenazi Jews. **Nusach Sefard** is the HASIDIC rite, used by Ashkenazi Hasidim; never call it "Sephardic." **Edot HaMizrach** is the rite of the Sephardic and Middle Eastern communities. When the research says "Sefard," it means the Hasidic rite.

## OUTPUT

Return exactly this shape, with nothing before the marker:

---LITURGICAL-SECTION-START---

#### Full psalm
...

#### Key verses
...

### VERSE COMMENTARY

**Verse 1**

[Hebrew]

> [translation]

[note]

**Verse 2**
...
"""


# ---------------------------------------------------------------------------
# Session 388: echoes v3.2. The author: the writer receives an UNFILTERED dossier of literary
# echoes, resonances beyond literature and far associations, and chooses -- at least one
# Jewish/Hebrew poem, at least one far association per 5 verses, 0.5-1.5 literary-or-beyond
# items per verse, space no object, choosing for illumination AND beauty, humour, haunting,
# originality -- and never reuses a work already used in the collection.
#
# The texts above are the S384-S386 texts the author approved, with exactly these edits
# (old -> new). tests/test_forest_writer.py applies them to the archived approved texts and
# requires a byte-for-byte match, so any other drift still fails.
# ---------------------------------------------------------------------------

_ESSAY_ECHOES_OLD = """## LITERARY ECHOES

The Cross-Cultural Literary Echoes research holds passages from world literature chosen for this psalm. Use the strongest of them where they serve the argument — one to three in the essay is a natural range — and add others you know that fit better. Every quotation in that research was gathered from published, openly available sources, and this guide is a private study text written for one reader's own education; quotation in the service of commentary is its whole purpose. Do not trim a passage below what the comparison needs out of caution: quote the lines that carry the echo — typically 3–8 lines of verse (or 2–4 sentences of prose) — in the original language with English translation; for public-domain works (ancient, medieval, and anything published before about 1930) quote as much as illuminates; for modern works, the passage the dossier supplies is the passage to use. Frame the source for the reader (who, when, under what circumstances), and after quoting, unfold the resonance: what is genuinely parallel, what differs, and what the difference reveals about each.
"""

_ESSAY_ECHOES_NEW = """## ECHOES AND RESONANCES

The research includes a section of echoes and resonances proposed for this psalm, in three kinds: literary echoes (poems, prose, liturgy, song), resonances beyond literature (history, art, music, science, anthropology and the rest), and far associations (a pattern the psalm makes, found in a distant field). Two readers proposed them independently and nobody has filtered them: there is more than you can use, and some miss. Choosing is your job. Choose by what an item does for THIS psalm — how much it illuminates a line — and by its own force: its beauty, humour, haunting power, originality, its power to make the reader think, how long it will stay with them. An item that is haunting, funny or strange deserves a real boost over one that is merely apt; one that shares only a mood or a theme is decoration. Add items of your own that fit better, but never anything ruled out by the list of what this collection has already used, which ends that section (for a text only the passage it names is ruled out; another passage of the same work is fine): the collection must not repeat itself, even from your memory.

In the essay, use the strongest where they serve the argument — one to four is a natural range, and a far association may open or turn the essay. Every quotation in that research was cut from a published, openly available page, and this guide is a private study text written for one reader's own education; quotation in the service of commentary is its whole purpose. Do not trim a passage below what the comparison needs out of caution: quote the lines that carry the echo — typically 3–8 lines of verse (or 2–4 sentences of prose) — in the original language with English translation; for public-domain works (ancient, medieval, and anything published before about 1930) quote as much as illuminates; for modern works, the passage the research supplies is the passage to use. Where an entry says *text not confirmed*, quote it only if you know the passage exactly. Frame the source for the reader (who, when, under what circumstances), and after quoting, unfold the resonance: what is genuinely parallel, what differs, and what the difference reveals about each. For a resonance beyond literature, state the fact precisely — quote the supplied source where it helps — and say what it shows about the line.
"""

_VERSE_ECHOES_OLD = """## LITERARY ECHOES ACROSS THE WHOLE GUIDE

Aim for about three echoes for every four verses across the whole guide, counting those already in your essay: for this psalm's {n_verses} verses, about {echo_target} in all. That is a level to reach with good echoes, not a quota. Rank the research's echoes together with any you know that fit better, and spend from the top. An echo earns its place by showing something about THIS line: the same event told by another voice, the same image turned to the opposite use, the same problem solved another way. A poem that shares only a mood is decoration. Do not repeat an echo the essay has used. Quote fully, and set poems lineated, as the essay instructions describe.
"""

_VERSE_ECHOES_NEW = """## ECHOES AND RESONANCES ACROSS THE WHOLE GUIDE

Across the whole guide, counting what the essay already used, include:
- **at least one Jewish or Hebrew poem** of the last 2,000 years — piyyut, Andalusian verse, kinot, Yiddish or modern Hebrew poetry, secular or liturgical — beyond whatever the liturgical section quotes;
- **at least one far association for every five verses**: for this psalm's {n_verses} verses, at least {far_target};
- **between half and one and a half literary echoes or resonances beyond literature per verse**: for this psalm, about {lit_lo} to {lit_hi} in all.

Do not worry about space: this guide is read slowly and for pleasure, and a good echo is worth the length it adds. Rank the research's items together with any you know that fit better (never a passage or item the already-used list rules out), and spend from the top, choosing by how much each illuminates its line and by its beauty, humour, haunting force, originality and power to make the reader think. An item earns its place by showing something about THIS line: the same event told by another voice, the same image turned to the opposite use, the same problem solved another way, the same pattern at work in another field. Place each at the verse it illuminates. Do not repeat an item the essay used. Quote fully, set poems lineated, and frame every source, as the essay instructions describe.
"""

S388_ECHO_EDITS = {
    "essay": (
        ("a reception-history report; literary echoes; and a set of cross-verse observations",
         "a reception-history report; echoes and resonances; and a set of cross-verse observations"),
        ("- **World literature** — see LITERARY ECHOES below.",
         "- **World literature, and the rest** — see ECHOES AND RESONANCES below."),
        (_ESSAY_ECHOES_OLD, _ESSAY_ECHOES_NEW),
    ),
    "verse": (
        ("BRING THE WHOLE LIBRARY and its two tests, COMMENTATORS, LITERARY ECHOES, and WRITING",
         "BRING THE WHOLE LIBRARY and its two tests, COMMENTATORS, ECHOES AND RESONANCES, and WRITING"),
        ("- **An echo**: see below.", "- **An echo or a resonance**: see below."),
        (_VERSE_ECHOES_OLD, _VERSE_ECHOES_NEW),
    ),
}

# The writer's targets (the author, S388).
FAR_PER_VERSES = 5                  # at least one far association per five verses
LIT_PER_VERSE = (0.5, 1.5)          # literary echoes + resonances beyond literature, per verse


def echo_targets(n_verses: int) -> Dict[str, int]:
    return {"far_target": max(1, n_verses // FAR_PER_VERSES),
            "lit_lo": max(1, int(n_verses * LIT_PER_VERSE[0] + 0.5)),
            "lit_hi": max(2, int(n_verses * LIT_PER_VERSE[1] + 0.5))}


def _apply_edits(text: str, edits) -> str:
    for old, new in edits:
        if text.count(old) != 1:
            raise AssertionError(f"S388 echo edit does not apply exactly once: {old[:60]!r}")
        text = text.replace(old, new)
    return text


# ---------------------------------------------------------------------------
# Session 394: the author, before Ps 78: "I like it when in the verse commentary, the commentary
# for verse a is aware that verse b is coming and sometimes prepares the reader for it - it
# creates a sense of continuity between verses so it's not just one-damn-thing-after-another.
# also - the writer should know that (esp in long psalms) it can group together small numbers of
# verses in the commentary when relevant." Applied after the S388 edits; the pin tests apply both.
# ---------------------------------------------------------------------------

_VERSE_THREAD_SECTION = """## THE THREAD BETWEEN THE NOTES

The notes are read in order, and they should read as one walk through the poem, not one thing after another. As you write each note, know what the verses after it will do. Where a coming verse turns on something in this one (a word it will take up, a question it will answer, an image it will reverse), let this note prepare the reader for it: a sentence that tells them what to listen for, or a question left open for a later note to close. When a note arrives at what an earlier note prepared, let the reader feel the connection close, in a phrase. Do this where the poem itself carries the thread; do not bolt a bridge onto every note, and never summarize the verse to come.

## WHAT A NOTE CAN HOLD (a menu, not a checklist)
"""

S394_VERSE_EDITS = (
    ("2. **Walk the poem.** For each verse, before you consult the research: what would a careful listener stumble on here? What does this line do that prose would not?",
     "2. **Walk the poem.** For each verse, before you consult the research: what would a careful listener stumble on here? What does this line do that prose would not? What does it hand on to the verses after it, and where does the poem move in units larger than a verse?"),
    ("## WHAT A NOTE CAN HOLD (a menu, not a checklist)\n", _VERSE_THREAD_SECTION),
    ("1. A header on its own line: `**Verse N**`. You may group two to four closely linked verses under one header (`**Verses 5–6**`), but each verse still gets its own Hebrew line and its own translation, and all of them come before the shared note.",
     "1. A header on its own line: `**Verse N**`. Group two to four verses under one header (`**Verses 5–6**`) wherever they make one movement and one note will serve them better than several: a sentence that runs across verses, a list or catalogue, a stretch of narrative, a pair whose point is the pairing. In a long psalm, do this freely, so that the commentary moves at the pace of the poem rather than stopping at every verse. Each verse in a group still gets its own Hebrew line and its own translation, and all of them come before the shared note."),
)

# ---------------------------------------------------------------------------
# Session 395: the liturgy section of the research is now a complete catalogue (every placement
# under its verse, minor echoes gathered at the end, the texts searched stated by code). "Every
# specific liturgical use" would now oblige the writer to print every echo in Ma'avar Yabbok; and
# the old guides' errors were restrictions inferred from absence ("in the Nusach Sefard and Edot
# HaMizrach forms of Uva le-Tziyon", "in certain selichot"), which the writer must not reintroduce.
# ---------------------------------------------------------------------------

S395_LITURGY_EDITS = (
    ("Every specific liturgical use in the research should appear somewhere in the guide, here or in a verse note.",
     "Every placement the research's liturgy section gives under a verse heading should appear somewhere in the guide, "
     "here or in a verse note; the echoes it gathers at the end are there to use where they illuminate a verse. "
     "Say where a verse is said as broadly as the research does and no more narrowly: the research names the texts "
     "that were searched, so never write that a verse is said only somewhere, or in certain or some services or "
     "communities, unless the research quotes a rubric that says so."),
)

# ---------------------------------------------------------------------------
# Session 399: the author, reading Ps 79: "the writer seems maniacally intent on mentioning every
# usage … it could say 'various selichot services' … the modern jewish liturgical section is the
# place to list liturgical uses. IF it's discussing liturgical uses in the verse by verse commentary
# it should be doing that to make a specific point about reception, interpretation, emotional
# resonance … NOT to provide a complete catalogue." The S395 coverage clause above did it: the
# Ps 79 writer was "mapping out every liturgical placement I need to cover", overran the section
# (599 words of 500) and was "distributing the remaining liturgical cross-references into their
# verse-specific notes" (v. 1: two rites' fast-day selichot and the Lithuanian fourth day; v. 6:
# five fasts, the selichot and Yom Kippur). The no-restriction rule stays; a summary by kind
# ("in various selichot") is not a restriction, and the fact checker flags only restrictions.
# ---------------------------------------------------------------------------

S399_LITURGY_EDITS = (
    ("Every placement the research's liturgy section gives under a verse heading should appear somewhere in the guide, "
     "here or in a verse note; the echoes it gathers at the end are there to use where they illuminate a verse. "
     "Say where a verse is said as broadly as the research does and no more narrowly:",
     "This section is the guide's one survey of where the psalm is said; the verse notes do not repeat it or continue it. "
     "Survey, do not catalogue: name the main placements, and gather the many smaller ones by kind (\"in various "
     "selichot\", \"in kinnot for Tisha B'Av\", \"through the Yom Kippur services\") instead of listing every day, rite "
     "and book. Leave out a placement that adds nothing to what the reader already has. "
     "Say where a verse is said as broadly as the research does and no more narrowly; a summary by kind is not a "
     "narrowing:"),
    ("- **The psalm in use**: a prayer that quotes the line (quote the prayer in Hebrew and English, name the service "
     "and the rite, and say whether it follows the plain sense or puts the words to new use), or a documented moment "
     "when someone used these words.",
     "- **The psalm in use**: a prayer that quotes the line, when the setting says something about the line: how the "
     "prayer rereads it, what its placement shows about how the words were heard, what it does to their weight. Quote "
     "that prayer in Hebrew and English, name its service and rite, and say whether it follows the plain sense or puts "
     "the words to new use. Bring in only the setting that makes the point, never the places the line is said: the "
     "liturgical section surveys those, and a note that lists services stops the reader. Or a documented moment when "
     "someone used these words."),
)

# ---------------------------------------------------------------------------
# Session 398: the author, after reading Pss 78-79. (1) Divine names: the Ps 78 writer decided
# "to avoid quoting them directly in Hebrew where I can" and cut 78:65 short to leave out
# אֲדֹנָי; the Ps 79 writer converted names itself, copying the example below. "It would be better
# … to have none of the models worry at all about divine names and then have something
# programmatic convert everything in the final output, including the thinking." The converter
# (divine_names_modifier, run on every paragraph of the DOCX) does that, so the writer is told to
# spell names in full, and the example no longer models a converted name. (2) "My strong
# preference would be to always include the Hebrew quotations as well. It is OK if that puts us a
# little over a word limit." About 40% of quotations in both guides had no Hebrew (Ps 74 "You
# split the sea", Ps 89, Ezek 24:7, Avot 3:17 …) while both essays sat at the 2,000-word cap.
# ---------------------------------------------------------------------------

_HEBREW_RULE_OLD = """- **Hebrew and English always together.** Every Hebrew word or quotation carries its translation, and every translation its Hebrew. The translation is part of the sentence, not a floating annotation: *The psalm ends with יֵשַׁע אֱלֹקִים, "the salvation of God"* or *God "made the mountain stand" (הֶעֱמַדְתָּה)* — never *יֵשַׁע אֱלֹקִים ("the salvation of God")*. Never put Hebrew (or Greek) inside quotation marks; only the English carries quotes.
"""

_HEBREW_RULE_NEW = """- **Hebrew and English always together.** Every Hebrew word or quotation carries its translation, and every translation of a Hebrew or Aramaic text carries its Hebrew. This holds for every such source, not only the psalm: other biblical verses, the Mishnah, Talmud and midrash, the commentators, the liturgy, and later Hebrew poetry. Whenever you quote one of them in English, quote it in Hebrew too, taking the words from the text in front of you where the research has it. (A source written in another language follows the echo rule: the original, then the translation.) The translation is part of the sentence, not a floating annotation: *The psalm ends with נוֹרָא לְמַלְכֵי־אָרֶץ, "awesome to the kings of the earth"* or *God "made the mountain stand" (הֶעֱמַדְתָּה)* — never *נוֹרָא לְמַלְכֵי־אָרֶץ ("awesome to the kings of the earth")*. Never put Hebrew (or Greek) inside quotation marks; only the English carries quotes.
- **Divine names as written.** Write every name of God exactly as your source spells it, and never shorten a quotation, leave out a line or choose a different passage to avoid a name. The printed guide converts every divine name, in the essay, the notes and your reasoning alike, into the forms traditionally used in print, so this is not something you need to think about.
"""

_LENGTH_OLD = "1,200–2,000 words. Open with"
_LENGTH_NEW = ("1,200–2,000 words of English. The Hebrew does not count toward them: never drop or shorten "
               "the Hebrew of a quotation to save space. Open with")

_VERSE_CARRYOVER_OLD = """and WRITING (including "you are the author" — never mention the research or anything behind it)."""
_VERSE_CARRYOVER_NEW = ("""and WRITING (including "you are the author" — never mention the research or anything behind it; """
                        """"Hebrew and English always together," which matters most in the notes, where most of the """
                        """quotations are; and "divine names as written")."""
                        """ Length is measured in English words only; the Hebrew never counts against it.""")

S398_HEBREW_EDITS = {
    "essay": (
        (_HEBREW_RULE_OLD, _HEBREW_RULE_NEW),
        (_LENGTH_OLD, _LENGTH_NEW),
    ),
    "verse": (
        (_VERSE_CARRYOVER_OLD, _VERSE_CARRYOVER_NEW),
        ("## THE LITURGICAL SECTION (200–500 words)", "## THE LITURGICAL SECTION (200–500 words of English, not counting the Hebrew)"),
    ),
}

ESSAY_INSTRUCTIONS = _apply_edits(ESSAY_INSTRUCTIONS, S388_ECHO_EDITS["essay"])
ESSAY_INSTRUCTIONS = _apply_edits(ESSAY_INSTRUCTIONS, S398_HEBREW_EDITS["essay"])
VERSE_INSTRUCTIONS = _apply_edits(VERSE_INSTRUCTIONS, S388_ECHO_EDITS["verse"])
VERSE_INSTRUCTIONS = _apply_edits(VERSE_INSTRUCTIONS, S394_VERSE_EDITS)
VERSE_INSTRUCTIONS = _apply_edits(VERSE_INSTRUCTIONS, S395_LITURGY_EDITS)
VERSE_INSTRUCTIONS = _apply_edits(VERSE_INSTRUCTIONS, S399_LITURGY_EDITS)
VERSE_INSTRUCTIONS = _apply_edits(VERSE_INSTRUCTIONS, S398_HEBREW_EDITS["verse"])


# ---------------------------------------------------------------------------
# Prompt assembly (pure)
# ---------------------------------------------------------------------------

def extract_inputs_block(prompt: str) -> str:
    """The `## YOUR INPUTS` block of a fully built MASTER_WRITER_PROMPT_V4: from the
    separator line above that heading to the separator line above `## YOUR TASK`.
    The same cut the S384 trials made on the saved Ps 76 prompt."""
    a = prompt.index("## YOUR INPUTS")
    a = prompt.rfind("\n## ═", 0, a) + 1
    b = prompt.index("## YOUR TASK: WRITE THE COMMENTARY")
    b = prompt.rfind("\n## ═", 0, b) + 1
    if not 0 < a < b:
        raise ValueError("could not locate the INPUTS block in the writer prompt")
    return prompt[a:b]


def commentator_names(inputs: str) -> List[str]:
    """Distinct commentators with a `### ch:v — Name` entry in the research bundle."""
    return sorted({m.group(1).strip() for m in re.finditer(r"^### \d+:\d+ — (.+?)\s*$", inputs, re.M)})


def _count_word(n: int) -> str:
    return _NUMBER_WORDS[n] if 0 < n < len(_NUMBER_WORDS) else str(n)


def essay_instructions(psalm_number: int, inputs: str) -> str:
    n = len(commentator_names(inputs))
    text = ESSAY_INSTRUCTIONS.replace("{psalm_number}", str(psalm_number))
    if n:
        word = _count_word(n)
        text = (text.replace("{commentators} traditional", f"{word} traditional")
                    .replace("The {Commentators} traditional", f"The {word} traditional"))
    else:  # no commentator entries at all: say nothing about a number
        text = (text.replace("{commentators} traditional", "the traditional")
                    .replace("The {Commentators} traditional", "The traditional"))
    assert "{" not in text, "unfilled placeholder in the essay instructions"
    return text


def psalm_verse_numbers(inputs: str) -> List[int]:
    """Verse numbers in the inputs' PSALM TEXT section (`### Verse N` headers)."""
    a = inputs.index("### PSALM TEXT")
    b = inputs.index("### STRUCTURAL OVERVIEW", a)
    return sorted({int(m.group(1)) for m in re.finditer(r"^### Verse (\d+)\s*$", inputs[a:b], re.M)})


def verse_instructions(n_verses: int) -> str:
    text = VERSE_INSTRUCTIONS.replace("{n_verses}", str(n_verses))
    for key, value in echo_targets(n_verses).items():
        text = text.replace("{" + key + "}", str(value))
    assert "{" not in text, "unfilled placeholder in the verse instructions"
    return text


# Session 388: the dossier cache SHARED WITH SYNTHESIS DISCOVERY. The INPUTS block's head
# (psalm text, structure, verse notes, research bundle, phonetics: ~222K tokens on Ps 77) is
# built from the same files and helpers for both stages; everything from KEY INSIGHTS on
# (curated insights, discovery's own observations) is the writer's alone.
# Discovery sends the head first under a cache breakpoint and keeps it warm while it runs, so
# the writer READS that head instead of writing it again (~$0.7/psalm on Opus 5.5).
SHARED_DOSSIER_END = "### KEY INSIGHTS TO INCORPORATE"


def split_inputs(inputs: str):
    """(shared head, writer-only tail) of an INPUTS block; ('', inputs) if it has no marker.

    The head ENDS WITHOUT WHITESPACE; the whitespace opens the tail. Measured in Session 388:
    the API trims trailing whitespace from the LAST block of a message, so a head ending in
    a blank line is one token shorter when it is sent alone (discovery's keep-alive) than when a
    block follows it (discovery itself, the writer) -- a different prefix, a cache miss, and on
    Ps 77 three ~$1.1 cache writes where reads were meant."""
    i = inputs.find(SHARED_DOSSIER_END)
    if i <= 0:
        return "", inputs
    head = inputs[:i].rstrip()
    return head, inputs[len(head):]


def shared_dossier(v4_template: str, psalm_number: int, psalm_text: str, macro_text: str,
                   micro_text: str, research_bundle: str, phonetic_section: str) -> str:
    """The shared head, built exactly as the writer builds its prompt: the V4 template
    formatted with the same pieces, cut the same way (the writer-only fields are blank and
    fall after the cut)."""
    prompt = v4_template.format(psalm_number=psalm_number, psalm_text=psalm_text,
                                macro_analysis=macro_text, micro_analysis=micro_text,
                                research_bundle=research_bundle, phonetic_section=phonetic_section,
                                curated_insights="", cross_verse_observations="")
    head, _ = split_inputs(extract_inputs_block(prompt))
    if not head:
        raise ValueError(f"the writer's INPUTS block has no {SHARED_DOSSIER_END!r} marker")
    return head


def first_turn(inputs: str, essay_instr: str) -> List[Dict]:
    """The shared first user turn; the cache breakpoint sits on its last block. Session 388:
    a second breakpoint closes the dossier head that synthesis discovery may already have
    cached. The text is unchanged, only split into blocks (head + tail == inputs)."""
    head, tail = split_inputs(inputs)
    blocks = ([{"type": "text", "text": head, "cache_control": {"type": "ephemeral"}},
               {"type": "text", "text": tail}] if head else [{"type": "text", "text": inputs}])
    return blocks + [{"type": "text", "text": essay_instr, "cache_control": {"type": "ephemeral"}}]


def replayable(content: List[Dict]) -> List[Dict]:
    """Call 1's assistant content to send back unchanged: thinking blocks byte for byte
    with their signatures (Opus 5.5 reads its own earlier reasoning), text as text."""
    out = []
    for b in content:
        t = b.get("type")
        if t == "thinking":
            out.append({"type": "thinking", "thinking": b["thinking"], "signature": b["signature"]})
        elif t == "redacted_thinking":
            out.append({"type": "redacted_thinking", "data": b["data"]})
        elif t == "text":
            out.append({"type": "text", "text": b["text"]})
    return out


# ---------------------------------------------------------------------------
# Output checks (pure)
# ---------------------------------------------------------------------------

VERSE_HEAD = re.compile(r"(?m)^\*\*Verses?\s+(\d+)(?:\s*[–-]\s*(\d+))?\*\*\s*$")
_VC_HEAD = re.compile(r"(?m)^#{1,4}\s*VERSE COMMENTARY\s*$")


def check_structure(rest: str, verse_numbers: List[int]) -> List[str]:
    """Problems with call 2's output that would break the guide downstream."""
    problems = []
    if not rest.lstrip().startswith(LIT_MARKER):
        problems.append("response does not open with the liturgical marker")
    vc = _VC_HEAD.search(rest)
    if not vc:
        problems.append("no VERSE COMMENTARY header")
        return problems
    if re.search(r"(?m)^\*\*Verses?\s+\d", rest[:vc.start()]):
        # CopyEditor._reassemble splits intro from verses at the first such line (S383).
        problems.append("a line in the liturgical section begins with **Verse (breaks the copy editor's split)")
    heads = list(VERSE_HEAD.finditer(rest))
    covered = []
    for i, h in enumerate(heads):
        lo, hi = int(h.group(1)), int(h.group(2) or h.group(1))
        covered += list(range(lo, hi + 1))
        body = rest[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(rest)]
        if len(re.findall(r"(?m)^> \S", body)) < hi - lo + 1:
            problems.append(f"verse(s) {lo}-{hi}: fewer '> ' translation lines than verses")
    if sorted(covered) != sorted(verse_numbers):
        missing = sorted(set(verse_numbers) - set(covered))
        extra = sorted(set(covered) - set(verse_numbers))
        problems.append(f"verse headers do not cover the psalm exactly (missing {missing}, extra {extra}, "
                        f"{len(covered)} headers for {len(verse_numbers)} verses)")
    if re.search(r"(?mi)^#{1,4}\s*(REFINED )?READER QUESTIONS", rest):
        problems.append("contains a reader-questions section (retired; should not be there)")
    return problems


def check_essay(essay: str) -> List[str]:
    problems = []
    if not re.match(r"#{1,4}\s*INTRODUCTION ESSAY\s*$", essay.lstrip().split("\n", 1)[0]):
        problems.append("essay does not open with '### INTRODUCTION ESSAY'")
    if _VC_HEAD.search(essay) or LIT_MARKER in essay:
        problems.append("essay call wrote beyond the essay (liturgy or verse commentary)")
    return problems


def assemble(essay: str, rest: str) -> str:
    """The full writer response, in the shape _parse_writer_response and the copy editor
    expect: essay, then the liturgical marker section, then `### VERSE COMMENTARY`."""
    return essay.strip() + "\n\n" + rest.strip() + "\n"


__all__ = [
    "LIT_MARKER", "KEEPALIVE_AFTER_S", "ESSAY_INSTRUCTIONS", "VERSE_INSTRUCTIONS",
    "extract_inputs_block", "split_inputs", "shared_dossier", "SHARED_DOSSIER_END", "commentator_names", "essay_instructions", "psalm_verse_numbers",
    "verse_instructions", "first_turn", "replayable", "check_structure", "check_essay", "assemble",
]
