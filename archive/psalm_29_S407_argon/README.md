# Ps 29, Session 407: Gemini 4 Argon as the writer, on the new deep research

Production `output/psalm_29/` (S401, Opus 5.5, 2026-10-10) is untouched. This run: `psalm_29/` here.

**Inputs**: macro, micro_v2, liturgy catalogue / set-aside and `echoes/` copied from production (no upstream code
changed since S401: commits S402–S405 touch only the writer, revision, DOCX and pricing). **Changed input**: the
author's new deep research (`data/deep_research/psalm_029_deep_research.txt` + `_check.txt`, 2026-10-16). The cleaner
cut off at its $0.10 cap (24K-char check); re-run with `drc.clean(29, max_cost=0.30)`: Sonnet 5.5, $0.11, 21/21 edits
applied, 2 checker quotations withheld. Its section was spliced into the copied bundle in place of the old one
(24.7K → 51.8K chars; bundle 350K). Synthesis discovery re-ran on the new bundle (the author's choice).

Run: `PSALMS_OUTPUT_ROOT=archive/psalm_29_S407_argon python scripts/run_enhanced_pipeline.py 29 --output-dir
archive/psalm_29_S407_argon/psalm_29 --master-editor-model gemini-4-argon --skip-macro --skip-micro --skip-lit-echoes
--fact-check --writer-revision --delay 0` (log `run.log`).

| Stage | Cost |
|---|---|
| Deep research cleanup (outside the pipeline) | $0.11 |
| Synthesis discovery (Opus 5.5) | $1.81 |
| Writer, Argon (essay $0.56, edit $0.12, verses $0.22) | $0.90 |
| Citation filter | $0.03 |
| Fact check: 219 claims, **20 contradicted (9.1/100)**, 17 unverifiable | $0.91 |
| Revision, Argon: 20/20 handled, 17 ¶; P35's 3 block-quote lines dropped by the S405 guard | $0.28 |
| Copy editor: 5 changes, no citation mismatches | $0.48 |
| **Total** | **$4.51** |

Essay: draft 2,802 words / 14% long sentences → after the edit turn 2,516 / 9% (target 2,000–2,400).
Guide: `Documents/Psalm study guide/Psalm 29 - Argon.docx` (+ PDF).
