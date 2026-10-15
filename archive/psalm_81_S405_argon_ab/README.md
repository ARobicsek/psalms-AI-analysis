# Ps 81, Session 405: Gemini 4 Argon as the writer (arm C)

**B** = `archive/psalm_81_S404_essay_ab/B/psalm_81/` (Opus 5.5 writer and revision, S404 prompts).
**C** = `C/psalm_81/`: the same inputs, copied from B (macro, micro, research bundle, synthesis discovery, liturgy
catalogue, echoes); the same forest prompts. **`gemini-4-argon` wrote the essay and verse calls (thinking `high`)
and did the post-fact-check revision.** Fact check, citation check and copy editor are unchanged (GPT).

Run: `PSALMS_OUTPUT_ROOT=archive/psalm_81_S405_argon_ab/C python scripts/run_enhanced_pipeline.py 81 --output-dir archive/psalm_81_S405_argon_ab/C/psalm_81 --master-editor-model gemini-4-argon --skip-macro --skip-micro --reuse-synthesis-discovery --skip-lit-echoes --fact-check --writer-revision --delay 0` (log: `C/run.log`)

Guide: `Documents/Psalm study guide/Psalm 81 - C test (Gemini 4 Argon writer).docx` (+ PDF).

| | B (Opus 5.5) | C (Argon) |
|---|---|---|
| Writer cost | $2.20 (265K cache write) | **$0.90** (essay $0.52, verses $0.38; implicit cache read all 184K of dossier) |
| Dossier tokens | 265K | 184K (Gemini tokenizer) |
| Raw essay | ~1,850 words, 3 argument headings | **~3,350–3,580 words** (shape warning: cap 2,000), 3 argument headings |
| Raw verse section | 40K chars | 52K chars |
| Finished guide | ~8,800 Eng words, 785 Hebrew, 18 pp | ~11,300 Eng words, 1,332 Hebrew, 21 pp |
| Fact check | 258 claims, 14 contradicted | 285 claims, **36 contradicted**, 23 unverifiable |
| Revision | Opus, 14/14, $0.33 | Argon, 35/35 (1 outside prose), 22 paragraphs, 0 rejected, $0.44 (+ $0.11 GPT filter) |
| Copy editor | $0.35 | $0.67 |
| **Total** | **$3.99** | **$3.84** (fact check $1.54: Flex 429s fell back to standard) |

Argon's 36 contradictions are mostly real: misattributions (Yannai/Abin, Rav Chanin, Malbim, Ibn Ezra ×4, Radak,
Augustine, Meiri, Bowen for Lindley LJ), grammar (אֶשְׁמָע as "completed"), a concordance slip (הַרְנִינוּ also Ps 32:11),
a misplaced Talmud folio, Poulenc "in Paris" (Nolzay). Borderline: "three words" in v. 6c (maqaf), counted three times.

Prices: $2/$10 per MTok through 2026-11-30, then $4/$20 (`cost_tracker` row + `INTRO_PRICING`). Output cap 65,536
incl. thinking; the verse call used 32.7K (15.5K thinking).

Code (Session 405): `MasterEditor._forest_gemini` (the forest writer on a `gemini-*` model; call 1's Content is
replayed with its thought signatures), `WriterRevision._call_gemini` (the revision follows a Gemini writer),
`--master-editor-model gemini-4-argon`.

## Arm D: Argon again, on the S405 edits (writer only, not fact-checked)

The author read C beside B (both better than A, so the S402–S404 prompt changes stay): Argon preferred ("more
interesting information … explanations a lot clearer"), but the essay too long with ponderous sentences, repetition
from the essay into the notes, and Hebrew quotations without punctuation. S405 changes: `forest_writer.S405_EDITS`
(the engaging teacher; **Clear sentences**; **Punctuate the Hebrew**; explanations, not quotations, are spent; refer
back), the essay editing turn (`essay_edit_request`: > 2,400 words or > 10% sentences of 40+ words; target
2,000–2,400), and `src/utils/hebrew_punctuation.py` at DOCX time (comma at etnachta / ole ve-yored, full stop
between verses; 84 finished guides swept: 305 marks, 25 sampled, all correct).

Run: as C with `D` for `C` and `--no-fact-check --no-writer-revision --skip-copy-editor`. Guide:
`Documents/Psalm study guide/Psalm 81 - D test (Argon, S405 edits, not fact-checked).docx` (+ PDF), 19 pp (C 21).

| raw writer output | C | D | B (Opus, final) |
|---|---|---|---|
| Essay words | 3,350 | 2,478 (draft 3,048; edit → 2,615 by its count) | 1,894 |
| Essay mean sentence / 40+ | 21.8 / 12% | 17.9 / 5% | 16.3 / 2% |
| Notes words, mean sentence / 40+ | 6,911, 32.3 / 34% | 6,863, 27.6 / 25% | 5,862, 16.2 / 3% |
| Hebrew quotations (6+ words) punctuated by the writer | 33% | 83% (code adds 1 more) | — |
| Writer cost | $0.90 | $0.86 (essay $0.51, edit $0.12, verses $0.23) | $2.20 |

Richness: of C's essay material, all but three items reappear in D, mostly moved into the notes (Moray, Rekhmire,
the LXX's "served", the golden-calf slogan, Sotah's Jehoseph, the kese debate). Lost: Malbim's "the shofar is always
a sign of trembling"; Jeremiah 11's parallel sequence and the Levites' Thursday split (both fact-check risks in C/B).
New in D: Dreikurs, Herbert's *The Collar*, Qur'an 2:93, *Babette's Feast*, Hos 13:2, the Aten hymn. Notes refer back
("The introduction showed/traced …", 6 times) and add new material. Unchecked errors seen: הַרְנִינוּ "only once
elsewhere" (C's check: also Ps 32:11), the opening's "three words before the middle of verse 6".

### D finished (same session): fact check, Argon revision, copy edit

`--skip-writer --fact-check --writer-revision` on the same folder (writer log kept as `D/run_writer.log`). Guide
replaced: `Documents/Psalm study guide/Psalm 81 - D test (Argon, S405 edits).docx` (+ PDF), 20 pp.

| finished guide | B (Opus) | C (Argon) | D (Argon, S405) |
|---|---|---|---|
| Fact check: claims / contradicted | 258 / 14 | 285 / 36 | 247 / **41** (9 essay, 32 notes + liturgy) |
| Revision | Opus 14/14 | Argon 35/35, 22 ¶ | Argon 40/40, 26 ¶, 0 rejected |
| Essay words, mean sentence, 40+ | 1,894, 16.3, 2% | 3,383, 21.7, 13% | 2,565, 18.2, 6% |
| Notes words, mean sentence, 40+ | 5,862, 16.2, 3% | 6,926, 32.8, 36% | 7,069, 28.1, 25% |
| Total cost | $3.99 | $3.84 | **$3.28** (writer $0.86, citations $0.17, fact check $1.10, revision $0.48, copy edit $0.68) |

D's contradictions: overstated precision ("every other", "only twice", "word for word", "verbatim"), misattributions
(Rav Hanin, Targum for Rashi, Arakhin, Deut 13:9), errors inside new far associations (Gondor, CFR regret, Byrd,
Gudea), repeats of C's (Poulenc in Paris, הַרְנִינוּ, the maqaf count); a few pedantic (Deut 5:29 = 5:26 Hebrew).

### After the author's read of D's essay

Three fixes (see IMPLEMENTATION_LOG S405): the revision's duplicated block quotes (D: v. 9/12/14 block, Gondor, Bartleby; C's Rilke, removed by its copy editor) — `apply_changes` now drops `>` lines; quotations end with their translation's mark (`end_hebrew_quotations`); the mark is drawn at the Hebrew's end (`_attach_hebrew_end_marks`). D's duplicates removed by hand (`*.before_dedupe.md` keep the originals); C and D re-rendered; `Documents/…/Psalm 81 - D test (Argon, S405 edits) - fixed.docx` (the original was open in Word).
