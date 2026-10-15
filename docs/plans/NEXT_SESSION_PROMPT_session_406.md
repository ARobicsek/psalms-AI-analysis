# Next session (406) — start here

Session 405 (record: `IMPLEMENTATION_LOG.md` Session 405; `archive/psalm_81_S405_argon_ab/README.md`) made Gemini 4
Argon a possible writer (`--master-editor-model gemini-4-argon`: the same two forest calls, and Argon revises after
the fact check) and ran Ps 81 on it twice. The author preferred Argon's C to Opus's B ("more interesting information
… explanations a lot clearer") but found the essay too long and ponderous, essay ideas repeated in the notes, and
Hebrew quotations unpunctuated. Built: `forest_writer.S405_EDITS` (the engaging teacher; clear sentences; punctuate
the Hebrew; explanations, not quotations, are spent; few superlatives and absolutes), an essay editing turn
(`essay_edit_request`), and modern punctuation for biblical quotations at DOCX time (`hebrew_punctuation.py`). All
apply to Opus too.

## 1. First: the author's read of Ps 81 arm D

`Documents/Psalm study guide/Psalm 81 - D test (Argon, S405 edits).docx`, beside B (Opus) and C (Argon, pre-S405),
all three finished the same way. What I told the author to expect: essay much clearer (2,565 words, 6% long
sentences), notes only partly (25% long vs Opus 3%), nearly nothing lost, notes refer back, but **41 fact-check
contradictions of 247** (C 36/285, B 14/258), most in the notes. The few-absolutes line was added after D and is
un-run.

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

## 3. Watch on any run

- The essay edit: does Argon reach 2,000–2,400 (D: 2,615)? Does Opus ever trigger it?
- Argon's notes: long sentences, and several far associations packed into one paragraph (D, vv. 10–11).
- Argon's output cap (65,536 incl. thinking) on a long psalm: Ps 81's verse call used 32.7K in C. Before Pss 89,
  104–107, 119 on Argon, check the verse call's output against it.
- Flex 429s on the fact check (C fell back to standard: $1.54).

## 4. Carried

The whole 405 handoff (`NEXT_SESSION_PROMPT_session_405.md`): the S404 essay checks (argument not tour; first
sentences make the argument; the notes take what the essay set aside) and the 404/403 handoffs it carried.
Production `output/psalm_81/` is still arm A (S402).
