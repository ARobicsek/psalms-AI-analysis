# Ps 81, Session 404: the essay as an argument (A/B)

**A** = production `output/psalm_81/` (S402 run, 2026-10-12): forest writer before S404, then fact check, writer revision, copy edit.
**B** = `B/psalm_81/`: the writer only (essay call + verse call) on `forest_writer.S404_ESSAY_EDITS`, same inputs
(415,722 chars, synthesis discovery reused). **Not fact-checked, revised or copy-edited.** B's prompts also carry
S403 (Greek words transliterated), which postdates A.

Run: `PSALMS_OUTPUT_ROOT=archive/psalm_81_S404_essay_ab/B python scripts/run_enhanced_pipeline.py 81 --output-dir archive/psalm_81_S404_essay_ab/B/psalm_81 --skip-macro --skip-micro --reuse-synthesis-discovery --skip-lit-echoes --no-fact-check --no-writer-revision --skip-copy-editor --delay 0`

Cost: $2.20 (essay $1.49, a full 265K cache write with no synthesis-discovery warm-up; verses $0.71).

| | A (raw essay call) | B |
|---|---|---|
| English words | ~2,150 | ~1,900 |
| Headings | 6, one per stretch of verses | 3, one per argument step |
| Thesis | end of para 1, last para | para 1, carried through |

B wrote its headings as `##` (DOCX Heading 2, the level of "Introduction"); `forest_writer.assemble` now demotes essay
subheadings to `###`, and B's markdown was fixed by hand before the DOCX re-render.

Unverified in B, likely fact-check catches: the Levites "on Rosh Hashanah" beginning at v. 7 (A's check: the
Thursday case); "the proper name … spoken only by God when he introduces himself" (it recurs in v. 16).

## Finished (same session)

`--skip-writer --fact-check --writer-revision` on the same folder, then the title and a one-line A/B note added to
the DOCX, saved as `Documents/Psalm study guide/Psalm 81 - B test (S404 essay prompt).docx` (+ PDF).
Fact check 258 claims, 14 contradicted (A: 276 / 14), all 14 handled by the writer revision, including both
suspected above (C7 the divine name in v. 16; C20 the Thursday Rosh Hashanah). Copy editor $0.35.
**Arm B total $3.99** (writer $2.20, citations $0.12, fact check $1.00, revision $0.33, copy editor $0.35).
