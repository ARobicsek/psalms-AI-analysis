# Next session (399) — start here

Session 398 changed no model and spent $0. Two things the author asked for after reading Pss 78–79, both now in
code (record: `IMPLEMENTATION_LOG.md` Session 398; memory `divine-names-and-hebrew-quotes`):

- **Divine names are code's job.** The writer is told to spell every name as its source does and never to avoid a
  quotation for one (`forest_writer.S398_HEBREW_EDITS`, and the V4/SI prompt). `divine_names_modifier` converts the
  printed guide, the writer's-reasoning appendix included; it now also converts Adonai (אד‑ני), Yah (י‑ה) and the
  Exod 3:14 Ehyeh, inside curly quotes, and a bolded-off prefix (**וֵ**אלֹהִים). The split is U+2011, the
  NON-BREAKING hyphen: an ASCII hyphen let Word break Ps 79:12 across two lines.
- **Hebrew with every quotation of a Hebrew source**, past the word limit: the limits count English words only.

## 1. On the next full pipeline run, check the S398 changes

- **Hebrew coverage.** Before: ~40% of 3+-word quotations sat in a sentence with no Hebrew (Ps 79 essay 20 of 52,
  Ps 78 notes 120 of 287). Re-count on the new guide (a sentence-level detector: a quotation of 3+ words, no Hebrew
  letter in its sentence; read the hits, since Goya or Owen are rightly English only). Expect the essay to run past
  2,000 words total; the English should still sit near 1,200–2,000.
- **The thinking.** Search the writer's thinking files for "divine name", "Tetragrammaton", "avoid": it should no
  longer plan around names. If it still does, read what it says before touching the prompt again.
- **The printed guide.** Open the DOCX/PDF: no full name anywhere (verse table, notes, liturgy section, appendix);
  converted names whole on one line. To sweep at $0: run `DivineNamesModifier().modify_text` over the guide's
  `edited_*.md` and thinking files and look for any name-shaped survivor (the S398 sweep left only the Aramaic
  אֱלָהִי of Dan 6:23 and the adjective האלהי, deliberately).
- The fact checker and copy editor now see full names: neither should flag or change a name's spelling.

## 2. Offered, not done

- **Re-render Pss 78 and 79** (`python scripts/run_docx_only.py 78 --pdf`, $0) so their printed אֲדֹנָי / יָהּ are
  converted; then replace the copies in `Documents/Psalm study guide/` and `G:\My Drive\` if the author wants. Any
  older guide can be re-rendered the same way.
- **The writer's repeated thinking on long psalms (the author's item 3, deferred: "leave number three for now").**
  Ps 78's verse call planned all 72 verses twice, the liturgy three times, each far association 7–10 times —
  mostly bookkeeping, little about meaning. Proposal: chunk the verse call above ~30 verses (~20–25 a call,
  continuing on the shared cache, echo targets split per chunk in code); A/B as Ps 78's verse call only (~$3–5).
  Ask the author before building.

## 3. Carried

The whole 398 handoff (`NEXT_SESSION_PROMPT_session_398.md`): on the next full run, the S397 fact check (the
`gpt-6-sol@flex` rows, fallbacks, time, catches in the usual range); its not-done items (compacting supported
records, the liturgy catalogue as a lookup, Flex for other OpenAI stages); and the 397/396/395 handoffs inside it.
