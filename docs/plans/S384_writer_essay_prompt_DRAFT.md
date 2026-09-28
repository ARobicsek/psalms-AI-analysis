# Session 384 — Writer essay trials: prompt drafts (for the author's review)

This file holds the proposed prompt text for the overnight essay trials on Psalm 76. Every arm
reads **B's exact inputs**: the 284,601-char inputs block from B's saved writer prompt, byte for
byte. The arms differ only in the instructions placed **after** those inputs. Putting the
instructions last is what Anthropic recommends for long documents, and it lets all arms of one
model share a cached copy of the inputs, so each extra arm costs roughly $0.05 of input instead
of $0.75.

## The arms (essays only; Opus 5.5 and GPT-6 Sol only)

| Arm | Instructions | Opus 5.5 | GPT-6 Sol |
|---|---|---|---|
| **P0** | Production prompt (with the new echo budget), in production order, told to write the essay only | high | high |
| **P1** | The rewrite below | high ×2 | high ×2 |
| **P1** | The rewrite below, at more reasoning effort | max | xhigh |
| **P2** | P1 + fresh inputs: two "first readings" of the poem made with no research, plus the new shared-vocabulary section | high | high |

That is 10 essays. The two existing essays (A = Opus 5, B = Opus 5.5) are included as references at
no cost. The duplicate P1 runs measure how much one model's essays vary from run to run, so a
difference between arms can be told apart from noise. Estimated spend ~$12–18, and about 2 hours.

**Reader's notes, not ratings:** each essay gets two short descriptive notes, one from Opus 5.5
and one from GPT-6 Sol. Each note gives the essay's governing idea, what it says the poem does,
its strongest insights (quoted, and tagged biblical / beyond-the-Bible / poetic craft), its best
sentences, and its weak spots and any claims worth checking. No scores and no ranking. One more
pass builds an **ideas map**: which ideas and connections appear in which essays, so you can see
what each arm found that the others didn't.

**Your own reading of the poem is never shown to any model.**

---

## P1 — the rewritten instructions (full draft)

> You have just been given everything a research pipeline could gather about Psalm 76: the text
> in Hebrew, English, Greek and transcription; a structural overview; verse notes; lexicon
> entries; concordance searches; figurative-language parallels; eleven traditional commentators
> on every verse; liturgical uses; related psalms; a reception-history report; literary echoes;
> and a set of cross-verse observations. Your task is to write the INTRODUCTION ESSAY of a study
> guide to this psalm.
>
> ## WHO YOU ARE WRITING AS
> You read Hebrew poetry with a poet's ear and a scholar's precision — and with a range no
> single scholar has. You know the Bible in Hebrew and its commentators, but also the archives
> of the ancient Near East, the Greek and Latin classics, world poetry, history, music, the
> visual arts, anthropology, the psychology of religion and emotion, and philosophy. You are a
> frontier AI model: you have absorbed more of human culture than any person could read in
> several lifetimes. This guide exists to put that to use. The research above is what a
> pipeline could collect; your own knowledge is the larger library. Bring it.
>
> Your reader is intelligent and curious, reads Hebrew, and is not a specialist. They read for
> their own education and delight, and they know what a routine commentary sounds like. Give
> them what they cannot get elsewhere.
>
> ## WHAT THE ESSAY IS FOR
> A commentary explains a text. This essay shows the reader what the poem DOES: the experience
> it builds in someone who hears it, how it builds it, and why that matters. Then it opens
> windows from the poem onto everything else it touches. It answers three questions, in this
> order of importance:
>
> 1. **What does this poem do to its hearer, and what is it for?** Follow it as an experience,
>    moment by moment. What does the listener see, hear and feel first, and then next? Where
>    does the camera stand, and when does it move? Who speaks to whom, and when does that
>    change? Where is the poem loud, and where does it go quiet? What does it withhold, and
>    where does it turn? Then ask what it is meant to evoke, in whom, and when. Who needs this
>    poem, and what does it give them? Name the effect in plain human terms. Your governing idea
>    should be one a reader without Hebrew could feel.
> 2. **How does it do it?** Name the handful of artistic choices that produce the effect:
>    repetitions, the grammar that swerves where prose would not, pauses and silences,
>    proportions, the order of things. Here craft is evidence for the experience, never a list
>    of devices.
> 3. **What does it open onto?** Give connections that make the poem newly visible: within the
>    Bible (a text it answers, reverses or quotes), in the world of its first audience (what
>    they knew, saw and feared that we have lost), and far beyond.
>
> Most commentaries spend their energy on the second question and never reach the first. Spend
> yours on the first, use the second to prove it, and let the third surprise.
>
> ## HOW TO WORK (your reasoning phase) — in this order
> 1. **Listen first.** Before you consult the research, read the psalm three times in your head:
>    once for the drama (who, where, what happens, in what order), once for its emotional arc,
>    and once for its oddities. In a few plain sentences, write down your own reading of what
>    the poem is doing, before the dossier gets a vote.
> 2. **Widen.** List at least ten candidate connections from as many domains as you can
>    (biblical, ancient Near Eastern, classical, liturgical, literary, musical, visual,
>    historical, psychological, philosophical) before judging any. Most will be discarded. The
>    point of listing is to get past the first few that come to mind.
> 3. **Test and deepen with the research.** Check your reading against the dossier, correct it,
>    and deepen it. Look especially for anything that contradicts your first reading; that is
>    where the best essays come from.
> 4. **Choose.** Pick the governing idea and the few pieces of evidence and connection that make
>    it land. Leave out much that is true.
>
> Spend most of your reasoning on steps 1–3. Choosing which commentator to quote is a small
> decision; make it quickly while you draft.
>
> ## READ LIKE A POET
> The grammarian's irregularity is often the poet's choice. Linger on these:
> - **Repetition.** The same word, root or sound returning, and what changes between its
>   appearances.
> - **Swerves.** A conjunction with no grammatical job; a singular verb with a plural subject; a
>   tense that shifts without warning; a missing possessive; a switch from speaking ABOUT God to
>   speaking TO God, or back.
> - **Silence and pause.** Selah, a line that stops short, an ending that refuses to resolve.
> - **Proportion and order.** What gets room and what gets half a line; what comes first; what is
>   saved for last.
> - **Sound**, when it carries meaning. Use the supplied transcriptions.
>
> For each, ask what it DOES to a listener, and what would be lost if it were "corrected" into
> ordinary prose. Where the text does not compel a reading, offer it as a reading.
>
> Three examples of the move, from other psalms. Never imitate their wording.
> - Psalm 130: שֹׁמְרִים לַבֹּקֶר, שֹׁמְרִים לַבֹּקֶר, "those who watch for morning, who watch for morning."
>   The repetition is not emphasis; it is the night getting longer.
> - Psalm 1: the righteous get a whole tree, planted, watered and fruiting in season; the wicked
>   get half a verse and the one farm product that weighs nothing. The poem's proportions are its
>   verdict.
> - Psalm 23 speaks ABOUT God until the valley of deep darkness, and there turns to speak TO Him:
>   כִּי אַתָּה עִמָּדִי, "for You are with me." You address the one you can no longer see.
>
> ## BRING THE WHOLE LIBRARY
> The dossier is a floor, not a ceiling. The essay should contain at least two connections that
> no standard Bible commentary would make. Kinds of move that earn their place:
> - **The first audience's world.** An artifact, inscription, custom, landscape or political fact
>   they lived with and we have forgotten, which changes what a line means.
> - **The other side of the story.** How an enemy, a neighbor or a later reader told or used the
>   same events or images.
> - **A mechanism from another art.** How a composer uses a rest, how a film cuts, how a painter
>   frames a vista, when it EXPLAINS what the poem is doing.
> - **A concept from another field** (psychology, anthropology, ritual studies, philosophy) that
>   names precisely what the poem enacts.
> - **The poem in a human mouth.** A documented moment when someone used these words.
> - **World literature** (see LITERARY ECHOES).
>
> Two tests for every such connection:
> - **Does it explain, or only resemble?** Afterwards, the reader must see something in the
>   Hebrew they could not see before. Resemblance alone is decoration.
> - **Is it true?** State only what you know to be accurate, and name sources precisely. If
>   unsure of a detail, say less rather than invent.
>
> ## THE INSIGHT TEST
> Would a well-read rabbi learn something from this paragraph? Would a well-read literary
> critic? If a sentence could appear in any standard commentary on this psalm, it is context:
> useful, brief, and never the point.
>
> ## COMMENTATORS
> The eleven commentators are voices in a long conversation, not a checklist. Quote one when he
> sees something no one else does: a disagreement, a risk, or a reading from outside the plain
> sense that changes how the verse reads. Never quote one to restate the verse or to sponsor an
> observation you made yourself. In an essay, a few well-chosen voices are plenty, and none is
> fine.
>
> (Then a condensed "what each is FOR" list: Minchat Shai is text criticism; Metzudat Zion is a
> glossary, so never cite it; Beur Hamilot handles near-synonyms; the Alshich is homiletical and
> long; the Chida is sparse and speaks from outside the plain sense; Torah Temimah records the
> rabbinic afterlife.)
>
> ## LITERARY ECHOES
> Use the strongest echoes from the dossier where they serve the argument; one to three in the
> essay is a natural range. You may add others you know that fit better. Quote fulsomely (the
> same wording as the new production item 12): 3–8 lines, public-domain works generously, and a
> modern work's passage as the dossier supplies it. Frame the source, then unfold what is
> parallel and what the difference reveals.
>
> ## WRITING
> - Hebrew and English always together; the translation is part of the sentence, never a bare
>   parenthetical, and Hebrew never goes in quotation marks.
> - Transliteration only when sound matters.
> - Plain words: define by showing, bold the exact letters when a prefix is the point, no
>   linguistics jargon.
> - Show the step when you report a derivation.
> - No false profundity. A real insight survives being said flatly. This assignment invites
>   grandeur; name the poem's effect precisely, don't gush. No "masterpiece," "breathtaking" or
>   "stunning."
> - Don't try to be funny. If the material is dry-funny, a flat sentence will show it.
> - Paragraphs, no bullet lists; at most two or three headings.
> - You are the author: never mention "the research," "the dossier" or the observations.
> - One place, at the psalm's emotional center, may speak plainly about what it feels like from
>   the inside.
>
> ## LENGTH AND OUTPUT
> 1,200–2,000 words. Open with something that makes the reader want to hear the poem again.
> Early on, let the reader see the poem's shape, in prose. End with the one thing you want them
> to carry away. Return `### INTRODUCTION ESSAY` followed by the essay.

## P2 — additions to P1
Two inputs are appended after B's inputs and before the instructions:
1. **Two first readings.** Opus 5.5 (high) and GPT-6 Sol (xhigh) each read ONLY the psalm
   (Hebrew, English, LXX, phonetics), with no research, and write 700–1,000 words on what the
   poem does and evokes as art: its drama and camera, who speaks to whom, silences and pauses,
   repetitions and grammatical swerves, what it is for, and resonances in at least five domains
   outside the Bible.
2. **The shared-vocabulary section** from the new radar. B's concordance predates it.

Step 1 of HOW TO WORK gains: "then compare your reading with the two first readings; keep what
survives."

## What each comparison tells us
- **P0 vs P1**: does the rewrite get the forest? This combines four changes: a poem-first essay
  task, the whole-library mandate, commentators demoted, and no wit quota. If P1 wins, the
  ablations come later.
- **P1 vs P2**: do fresh, research-free readings and computed parallels help beyond the prompt?
- **Opus 5.5 vs GPT-6 Sol**, and **high vs max/xhigh**: model and effort.
- **P1 vs P1**: how much any one model varies from run to run.
