# Next session (406) — start here

Session 405 (record: `IMPLEMENTATION_LOG.md` Session 405; `archive/psalm_81_S405_argon_ab/README.md`) made Gemini 4
Argon a possible writer (`--master-editor-model gemini-4-argon`: the same two forest calls, and Argon revises after
the fact check) and ran Ps 81 on it twice. The author preferred Argon's C to Opus's B ("more interesting information
… explanations a lot clearer") but found the essay too long and ponderous, essay ideas repeated in the notes, and
Hebrew quotations unpunctuated. Built: `forest_writer.S405_EDITS` (the engaging teacher; clear sentences; punctuate
the Hebrew; explanations, not quotations, are spent; few superlatives and absolutes), an essay editing turn
(`essay_edit_request`), and modern punctuation for biblical quotations at DOCX time (`hebrew_punctuation.py`). All
apply to Opus too.

## 1. The author's read of Ps 81 arm D (so far)

`Documents/Psalm study guide/Psalm 81 - D test (Argon, S405 edits).docx`, beside B (Opus) and C (Argon, pre-S405),
all three finished the same way. The author on D's essay: "it's great", with three small things, all fixed in the
same session in code: inline Hebrew quotations without an end mark, three quotations printed twice (Argon's
revision), and periods drawn at the Hebrew's right/start or on the next line. Measured before the read: essay 2,565
words, 6% long sentences; notes 25% long (Opus 3%); **41 fact-check contradictions of 247** (C 36/285, B 14/258),
most in the notes. The few-absolutes line was added after D and is un-run. Ask for the rest of the read (the notes).

## 2. Likely next: Ps 82, Opus 5.5 vs Argon

The author: "very likely the next step will be to run ps 82 with opus 5.5 vs argon. but let me read first."
- Ps 82's deep research: check `data/deep_research/psalm_082_deep_research.txt` and `_check.txt` exist and the
  cleanup ran.
- Cheapest correct order: one full Opus run to production `output/psalm_82/` (macro, echoes, micro, SD, writer, fact
  check, revision, copy edit), then the Argon arm on the SAME inputs in an arm folder: copy macro, micro_v2,
  research_v2, synthesis_discovery, liturgy_catalogue, liturgy_set_aside and `echoes/` (as for C and D), then
  `PSALMS_OUTPUT_ROOT=<arm root> … --master-editor-model gemini-4-argon --skip-macro --skip-micro
  --reuse-synthesis-discovery --skip-lit-echoes --fact-check --writer-revision`. About $9–10 + $3.5.
- Compare: fact-check contradictions per 100 claims (the few-absolutes line's first test), long-sentence shares,
  essay edit triggered or not (Opus should rarely trigger it), the notes' "The introduction showed …" formula.

## 3. The DOCX changes reach every guide on its next render

Session 405's Hebrew-punctuation work runs at DOCX time, so re-rendering an older guide ($0, `run_docx_only.py N --pdf`) changes it:
biblical quotations gain commas/full stops from their accents (sweep: 305 marks in 69 of 84 guides), quotations of 3+
words followed by a sentence-closing translation end with that mark instead of a comma (1,698 edits in 58 guides), the
mark is drawn at the Hebrew's end (inline and in a 6+-word quotation's own line), and wrapped quotations leave no stray
`*)` or `(`. All sampled changes were correct. Offer the author a batch re-render of the finished guides if they want the
printed ones to match; nothing was re-rendered except Ps 81's C and D.

## 4. Watch on any run

- Argon's revision returning block quotes with a paragraph: `writer_revision.apply_changes` now drops them and logs a
  rejection; the revision report (`psalm_NNN_writer_revision.md`, *Rejected by code*) shows if it recurs.
- The essay edit: does Argon reach 2,000–2,400 (D: 2,615)? Does Opus ever trigger it?
- Argon's notes: long sentences, and several far associations packed into one paragraph (D, vv. 10–11).
- Argon's output cap (65,536 incl. thinking) on a long psalm: Ps 81's verse call used 32.7K in C. Before Pss 89,
  104–107, 119 on Argon, check the verse call's output against it.
- Flex 429s on the fact check (C fell back to standard: $1.54).

## 5. Carried

The whole 405 handoff (`NEXT_SESSION_PROMPT_session_405.md`): the S404 essay checks (argument not tour; first
sentences make the argument; the notes take what the essay set aside) and the 404/403 handoffs it carried.
Production `output/psalm_81/` is still arm A (S402).
