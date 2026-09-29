# Session 385 — the two-call "forest" writer (built, NOT yet run) and the fact-check question

## Why two calls

The author's blind reading of the S384 essay trials (`archive/psalm_76_S384_essay_trials/AUTHOR_READING_S385.md`)
put the three "forest" essays by Opus 5.5 (F, C, D) at the top, above the P0 essay by the same model on the
same inputs. The open question was whether to carry the forest approach into one call that writes the
whole guide or into two calls. The author asked for two.

- **Quality**: the essay we tested was written by a call with no other job. A single call would bring back the
  per-verse commentator machinery that S384 measured taking 55–60% of the writer's thinking. With two calls,
  the verse writer sees the finished essay and can be told exactly what is already spent. Ps 75's verse 7
  re-argued its essay (S382) in a single call, despite three rules against it.
- **Cost**: two calls are *not* cheaper than one. The cache keeps them close: one call ≈ $1.90, two calls with a
  5-minute cache ≈ $2.15, a 1-hour cache ≈ $2.70, no cache ≈ $2.60 (writer stage, Ps 76, Opus 5.5 $4/$20).

## What was built

`scripts/s385_two_call_writer.py`. Nothing in `src/` changed.

- **Call 1**: the essay under P1, byte-identical to the trials (verified: the archived
  `p1_instructions.txt` equals `P1_INSTRUCTIONS` with its placeholders emptied).
- **Call 2**: the liturgical section, verse commentary and reader questions, as the second turn of the same
  conversation. The essay is the assistant turn and `VERSE_INSTRUCTIONS` is the next user turn.
- **Cache**: the first user turn, [B's inputs][P1], carries a 5-minute `cache_control` on its last block, and
  every call sends it unchanged. A 5-minute entry lives from the START of the request that wrote or read it,
  and the trial essay calls took 84–114 s. If call 1 is still generating at 240 s, one `max_tokens=0` keep-alive
  refreshes the entry (~$0.04). A miss is not a failure; call 2 just pays a fresh write (~$0.9).
- **Two variants of call 2, run in parallel:**
  - **new**: on the essay call 1 writes. Its thinking blocks are replayed unchanged, and Opus 5.5 reads its
    own earlier reasoning (preserved thinking), so the verse writer sees the connections it listed and set
    aside while planning the essay.
  - **F**: on the author's favorite essay, text only (F's thinking was never kept in replayable form). This
    is the clean read of the verse instructions, because the essay is fixed and already judged.
- **Output**, under `archive/psalm_76_S385_two_call/`:
  - production-shaped `full_writer_response.md`;
  - `edited_intro` / `edited_verses` / `reader_questions.json`, split by the production parser's regexes;
  - a structure check covering the marker, every verse header 1–13, a translation line per verse, questions,
    and no `**Verse` line in the liturgy section (the S383 copy-editor split bug);
  - descriptive metrics against K, the S383 one-call guide;
  - a reading DOCX per variant in S383's compact layout, with both calls' thinking as a two-column appendix.
    The psalm text comes from the inputs block, so `tanakh.db`, which is not in the repo, is not needed.
    `--selftest-docx` renders K through the same path at $0, and it works.

### The verse instructions: kept, changed, dropped (vs production Stage 2–4)
- **Kept**: the verse format (header, punctuated Hebrew, one-line `> ` translation of the whole verse, prose
  note), grouping rules, "coverage is discharged", the transcription/bold-sound rule, the liturgical section
  (marker, `####` subsections, Practical Kabbalah if Shimush Tehillim is present, the Nusach disambiguation
  verbatim in substance, and every liturgical use appearing somewhere), the LXX ration (≤ 2 verses in 5),
  the echo budget (~3 per 4 verses across the guide, essay included), show-the-step for derivations, the S382
  deferral to the essay, 4–6 reader questions.
- **Changed**:
  - Everything in P1 is inherited ("still holds"); the new text covers only what differs.
  - Notes are chosen per verse "unevenly" from a menu (what the line does, a rare word, a crux, a commentator,
    rabbinic afterlife, the Greek, the psalm in use, an echo). There is no list of eleven items to cover.
  - The best material is named explicitly: what was gathered for the essay and set aside.
  - Echoes must show something about THIS line: the same event in another voice, the same image turned to the
    opposite use, the same problem solved another way. "A poem that shares only a mood is decoration." This
    follows the S385 reading, where every essay that used a dossier echo was in the lower half.
  - Commentators: work from the text in front of you and keep the shape of the argument (reading / proof /
    alternative). This is the exact failure in F's Rashi on 76:11.
  - "Occurs only here" claims need concordance support.
- **Dropped**: RULE 8b's 15K-char commentator machinery, the wit rule, the per-item WEAK/STRONG examples, and the
  "MUST incorporate EVERY liturgical reference … in the verse commentary" framing (now "somewhere in the guide").
- Length: 8,377 chars, vs ~25K for the production task section plus ~51K of rules.

## How to run (next session)

1. Add the Anthropic key to the cloud environment as **`PSALMS_ANTHROPIC_API_KEY`** (environment settings, then Edit,
   then environment variables); the name keeps it out of Claude Code's own view. Add `OPENAI_API_KEY` for later
   copy-editor work. A new session picks them up. On the author's own machine, `.env`'s `ANTHROPIC_API_KEY` is used.
2. `pip install anthropic python-docx python-dotenv` if the container lacks them.
3. `python scripts/s385_two_call_writer.py --dry-run`, then `python scripts/s385_two_call_writer.py`.
   Estimate ≈ $3.1 (call 1 ≈ $1.13; each call 2 ≈ $0.97); the hard cap is $8.
4. Check `ledger.json`: call 2's `cache_read` should be ~185K and its `cache_write` ~0. If not, the cache
   missed; note the cost and why.
5. Send the author the two DOCXs. Neither has been copy edited.

What to look for when reading (descriptively, no scores unless the author asks): does the verse commentary
re-argue the essay? Is it uneven in the right places? Which outside-the-Bible material appears, and is it
accurate? Does "new" (with replayed reasoning) use connections the essay set aside, compared with "F"? How do
length and texture compare with K's 6,261 words (notes of 240–670 words)?

## The copy editor, now that the writer draws on its own knowledge

**Cost of switching `gpt-5.4` → `gpt-6-sol`: roughly a wash.** Ps 76 (S383): one call, ~21K input, ~17K visible
output plus ~20K reasoning, $0.62–0.65. The same tokens on Sol cost ~$0.41 at the promo price ($2/$10, through
2026-11-21) and ~$0.82 at the assumed durable $4/$20. Sol reasons far less at `high` (2.5–5K tokens on the
essays), so the likely figure is lower still. Either way that is under ±$0.2 on a ~$8 run.

**Do not switch on price or capability alone.** `COPY_EDITOR_TERRA_FINDINGS.md` found that a more assertive
editor does harm: Terra "corrected" claims about non-biblical works from memory and once invented a Hebrew
reading (Ps 40:17's waw) that `tanakh.db` refutes. The prompt fix for that backfired. That doc's own verdict
still holds: ground truth, not a sterner rule. The forest writer makes this more pressing. The Terra doc argued
that the writer was the better-informed party on non-biblical claims because it worked from a web-verified
echoes dossier. The forest writer instead brings Herodotus, Byron and Sennacherib's prism from memory. (I checked F against my own
knowledge, not against sources: the Byron lines, Herodotus 2.141's mice and inscription, and the prism's "bird in a
cage" and 30/800 talents all look right. The error the author found was in handling a text in front of it, Rashi.)

**Looking things up is possible, three ways, cheapest first:**
1. **Give the checker the evidence the writer had**, i.e. the research bundle (~129K Sol tokens: +$0.26/psalm
   at the promo, +$0.52 durable). This catches commentator misreadings (F's Rashi), concordance claims ("the only
   other plural"; the S383 copy editor *introduced* that false one) and liturgy claims. S380 noted this gap and
   left it.
2. **Our own lookups as function tools**, $0 each: a verse from `tanakh.db`, a commentator's text on a verse
   (bundle or Sefaria), a concordance search. `scripture_verifier.verify_citations_tooluse` already runs a Haiku
   tool loop with `lookup_verse`, so the pattern exists.
3. **Web search** for outside-the-Bible claims (Herodotus, Byron, inscriptions, dates). It is built into both the
   OpenAI Responses API and Claude (`web_search_20260209` / `web_fetch_20260209` on Opus/Sonnet 5.5), billed per
   search plus the tokens read. Measure it on one guide before quoting a figure.

**Proposal, not built: split fact-checking from copy editing.** A FACT-CHECK pass reads the guide, lists every
checkable claim that isn't common knowledge (quotations, attributions and the shape of a commentator's
argument, "only here" counts, dates, names, quotations from memory), verifies each against the bundle and the
tools, and returns verdicts WITH evidence (the quoted source text, or a URL). The copy editor then corrects facts
only from that list and never from memory, and keeps its style and logic job. Two cheap additions:
- re-run the $0 `verify_citations` AFTER the copy edit, the "Open" item in the Terra doc, since the copy editor's
  own assertions are checked by nothing today;
- a checker from a different model family from the writer, so it doesn't share the writer's false memories.

GPT-6 Sol with web search is the natural candidate.

**Probe cases for any checker/copy-editor change** (it must catch the first two and leave the rest alone):
- F's Rashi on 76:11. Rashi gives ONE reading (fury → praise, Nebuchadnezzar; *and thereby* the rest of the
  fury is restrained, תחגר in the Mishnah's sense of a knife-nick that catches the nail) and then an alternative
  (literal girding). F presents the two halves of the first as two alternatives.
- S383's copy-edit error: "the only other plural use" of רשף (Ps 78:48 has לָרְשָׁפִים). The writer's original,
  "the only other occurrence of the form רִשְׁפֵי is Song 8:6", was right.
- The four Terra probe cases (Herbert's *Denial*; two figures; Ps 40:17 vs 70:5 waw). Their saved Ps 70 input
  lives in `output/` on the author's machine, not in the repo.
- Claims from memory that should survive, once a source confirms them: F's Byron quotation, Herodotus 2.141, the
  prism's wording.
