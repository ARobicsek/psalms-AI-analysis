# Psalm 83, Session 409: first full run on the Shared Passages section

Command: `python scripts/run_enhanced_pipeline.py 83` (all defaults: Gemini 4 Argon writer + revision, Opus 5.5 SD and macro,
fact check on flex, reception, Targum). Output: production `output/psalm_83/`; guide copied to
`Documents/Psalm study guide/Psalm 83.docx` (+ PDF). Log: `run.log` here (local only; `*.log` is not committed).

Before the run: the deep research was cleaned at a $0.30 cap (Sonnet 5.5, $0.092, 14 of 15 edits applied; the Goldingay
page range was not found) because at the then-$0.10 cap a 31K-token report would have gone to Haiku.

| Stage | Cost |
|---|---|
| macro analysis (Opus 5.5) | $0.254 |
| echoes v3 | $1.104 |
| micro + research bundle | $1.402 |
| synthesis discovery (Opus 5.5) | $1.649 |
| writer (Argon: essay $0.487, edit $0.121, verses $0.266) | $0.874 |
| fact check (flex) | $1.067 |
| writer revision (Argon) | $0.593 |
| copy editor (gpt-5.4) | $0.495 |
| **total** | **$7.44** |

- Bundle 290,552 chars (+ reception 18 passages, 19,386 chars); SD dossier head 353,705 chars. **Shared Passages: 474 chars,
  one line (83:19 ~ Ps 97:9; Deut 28:1); no Related Psalms section.** Deep research loaded checked (43,334 chars).
- Essay: draft 3,499 words, 15% long sentences; the edit turn took it to 3,084 / 9% (target 2,000-2,400: the first Argon
  edit to stay this far over). Three argument headings. Verse call 22,746 out (6,128 thinking), well under 65,536.
- Citation check before the revision: 16 NOT_SUBSTRING flags (the previous guides: 0-1), mostly the checker pairing a
  quote with a neighbouring citation in a sentence that carries several, or checking a midrash/piyyut against the verse it
  comments on; after the revision 1 (Ps 40:15 quoted without יַחַד). The revision changed no citation (60 before, 60 after).
- Fact check: 261 claims, 209 supported, **36 contradicted (13.8/100)**, 16 unverifiable. Counting slips (seven Genesis
  relatives, seven warlords), absolutes (Pss 42-83 "fasted from the Name"; shir "reserved for celebration"), commentator
  overreads (Malbim's Pharaoh, Radak on En-dor, Meiri's dog for Sanhedrin's weasel), liturgy details, Zemlinsky's
  cancelled 1904 premiere (his opera's). Revision: 36/36 handled, 27 paragraphs; the S405 block-quote guard fired on 12,
  and every dropped line was the guide's own quotation re-sent unchanged (nothing lost).
- Copy editor: 9 changes; post-copy-edit citations 0 issues.
- Appendix: 32 + 19 streamed thought summaries, headed, reasoning not draft; names Gemini 4 Argon.
- Methods page: found that a full run never recorded `deep_research_checked` (fixed in `track_research_bundle`); Ps 83's
  stats patched and the DOCX/PDF re-rendered ($0): "Deep Web Research: Yes (corrected against an independent check)".
