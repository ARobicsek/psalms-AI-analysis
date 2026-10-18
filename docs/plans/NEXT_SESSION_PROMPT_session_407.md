# Next session (407) — start here

Session 406 (record: `IMPLEMENTATION_LOG.md` Session 406; `archive/psalm_82_S406_opus_argon_ab/README.md`) ran Ps 82
as a head-to-head of the writer: **A** Opus 5.5 (full pipeline, production `output/psalm_82/`, $7.22) and **B**
Gemini 4 Argon for the essay, verse notes and post-fact-check revision on A's copied inputs ($2.56 writer-onward).
No code changed. Both on the S405 prompts; this was the first run of the few-absolutes line.

## 1. The author's read of Ps 82 A and B

`Documents/Psalm study guide/Psalm 82 - A test (Opus 5.5).docx` and `Psalm 82 - B test (Gemini 4 Argon).docx`
(+ PDFs), 14 pp each. Ask for the read. What the numbers say (do not let them decide; the author decides by reading):

| | A Opus | B Argon |
|---|---|---|
| Fact check contradicted / claims | 21 / 168 (12.5/100) | 23 / 205 (11.2/100) |
| Essay words, share of sentences 40+ | 1,855, 5% (no edit turn) | 2,241, 9% (edit turn: 2,838 → 2,618) |
| Notes words, share 40+ | 3,024, 4% | 3,457, 26% |
| Hebrew words | 418 | 583 |
| Writer cost | $0.90 (SD cache exact) | $0.87 |

- Argon's error rate fell to Opus's level (Ps 81: 2.5–3×), but the absolutes count did not fall (9.1 per 1,000
  words vs 8.4 on Ps 81 D), so the drop is not shown to be the new line. Ps 82 is 8 verses; one run.
- With the SD → writer cache working, Opus's writer costs the same as Argon's ($0.90 vs $0.87); Ps 81's $2.20 had
  no warm-up. Argon's price doubles on 2026-12-01. Cost no longer separates them.
- Argon's notes are still long-sentenced (26% vs 4%), as on Ps 81 (33% by the same count).

## 2. The writer-model decision

Memory `writer-model-choice`: production stays Opus until the author decides. If Argon is chosen: the default is
`--master-editor-model` (`run_enhanced_pipeline.py`); Argon must always run with the fact check and revision; check
the verse call's output against the 65,536 cap before long psalms (Ps 82 used 20.9K; Ps 81 32.7K); re-check the
price row after 2026-11-30 (`INTRO_PRICING`). If Opus: nothing to change. A split is possible (Argon essay, Opus
notes, or the reverse) but un-built: the two forest calls share one model and the verse call replays the essay
call's thinking.

## 3. The shared-dossier errors (both writers made them)

About half the contradictions were in BOTH arms, so they arrive from the dossier: the LXX of Deut 32:8 read as "sons
of God" (Brenton: "angels of God"), Avot 3's three as a court (a study group), Reish Lakish's no-children line as the
Talmud's conclusion, Irenaeus as first (Justin), "נִצָּב alone" marks the singular (יִשְׁפֹּט too), Radak's
"perhaps" made definite. Worth tracing to the source (deep research, SD, micro?) if the author wants fewer
fact-check catches upstream; offer it, do not build unasked.

## 4. Watch on any run

- The S405 block-quote guard fired once in Argon's revision (P52, prose fix kept): Argon keeps returning block
  quotes with a paragraph; Opus has never done so.
- The post-copy-edit citation check flags a commentator's lead-in joined to a verse when the copy editor strips
  inner quotation marks (Ps 82 A: Rashi's עַל דֶּרֶךְ before Exod 23:8). A false alarm; fix only if it recurs.
- The essay edit: Opus has not triggered it (Ps 81 B, Ps 82 A); Argon has every time (Ps 81 D, Ps 82 B), landing
  ~2,600 words, slightly over its 2,400 ceiling.

## 5. Carried

The whole 406 handoff (`NEXT_SESSION_PROMPT_session_406.md`; its §2 Ps 82 run is done): the author's read of Ps 81 D's
notes; the batch re-render offer for the S405 DOCX changes (§3: punctuation and end marks reach every guide on its
next render; nothing re-rendered except Ps 81 C/D); the Argon watch items; and the 405/404/403 handoffs it carried.
Production `output/psalm_81/` is still arm A (S402); `output/psalm_82/` is arm A (Opus, S406).
