# Ps 82, Session 406: Opus 5.5 vs Gemini 4 Argon as the writer

**A** = production `output/psalm_82/` (full pipeline, Opus 5.5 writer and revision). Log: `A_run.log`.
**B** = `B/psalm_82/`: A's inputs copied (macro, micro_v2, research_v2, synthesis_discovery, liturgy_catalogue,
liturgy_set_aside, `echoes/`); **gemini-4-argon** wrote the essay + verse calls and did the post-fact-check revision.
Both on the S405 prompts (incl. the few-absolutes line: its first run). Fact check, citation check, copy editor unchanged.

Run B: `PSALMS_OUTPUT_ROOT=archive/psalm_82_S406_opus_argon_ab/B python scripts/run_enhanced_pipeline.py 82 --output-dir archive/psalm_82_S406_opus_argon_ab/B/psalm_82 --master-editor-model gemini-4-argon --skip-macro --skip-micro --reuse-synthesis-discovery --skip-lit-echoes --fact-check --writer-revision --delay 0` (log `B/run.log`).

Guides: `Documents/Psalm study guide/Psalm 82 - A test (Opus 5.5).docx` and `Psalm 82 - B test (Gemini 4 Argon).docx` (+ PDFs), 14 pp each.

| | A (Opus 5.5) | B (Argon) |
|---|---|---|
| Writer | $0.90 (essay read 216K from SD's cache; cache exact) | $0.87 (essay $0.47, edit $0.15, verses $0.25) |
| Essay edit turn | not triggered | triggered: draft 2,838 words / 16% long → 2,618 / 3% |
| Fact check | 168 claims, **21 contradicted (12.5/100)**, $0.52 | 205 claims, **23 contradicted (11.2/100)**, $0.83 |
| Revision | Opus 21/21, 14 ¶, $0.33 | Argon 23/23, 19 ¶, $0.43; 1 block quote dropped by the S405 guard (P52; prose fix kept) |
| Copy editor | $0.31 (1 citation flag: Rashi's lead-in עַל דֶּרֶךְ joined to Exod 23:8, harmless) | $0.32 (citations clean) |
| Writer-onward cost | $2.12 | $2.55 |
| Full run | **$7.22** (SD $2.60, echoes $0.93, micro + bundle, macro) | (shared stages paid in A) |

Shape of the copy-edited guide (one script for all four, `measure.py` here: words of English;
sentence length in whitespace tokens incl. Hebrew; so not the S405 table's numbers):

| | 81 B Opus | 81 D Argon | 82 A Opus | 82 B Argon |
|---|---|---|---|---|
| Essay words / mean sentence / 40+ | 1,859 / 17.5 / 4% | 2,375 / 23.2 / 6% | 1,855 / 17.5 / 5% | 2,241 / 24.2 / 9% |
| Notes words / mean sentence / 40+ | 5,463 / 18.5 / 7% | 6,061 / 32.3 / 33% | 3,024 / 17.6 / 4% | 3,457 / 30.7 / 26% |
| Hebrew words (essay + notes) | 586 | 753 | 418 | 583 |
| "The introduction showed…" in notes | 0 | 5 | 2 | 1 |
| Absolutes per 1,000 words (raw writer output) | 8.0 | 8.4 | 8.2 | 9.1 |

Contradictions: the same families in both arms; about half SHARED (so upstream, the dossier): the LXX of Deut 32:8
read as "sons of God" (it is "angels of God"), Avot 3's three as a court (a study group), Reish Lakish's
no-children line taken as the Talmud's conclusion, Irenaeus as the first, "נִצָּב alone" marks the singular, Radak's
"perhaps" dating made definite. A-only: Ps 94/Wednesday liturgy slips, Alshich on Selah, baraita for mishnah,
Malbim's verse. B-only: far-association errors (the Mozilla/Microsoft/Google CA revocation, Yassib in the Keret
epic), root slip (יַצֵּב from יצב, not נצב), commentator overreads (Rashi, Meiri, Malbim), Levi read into Halevi/Radak.

Findings: Argon's error rate fell to Opus's level here (Ps 81: 2.5-3x), but the absolutes count did not fall, so the
cause is not shown to be the new line (shorter psalm, 8 v.; one run). Argon's notes stay long-sentenced (26% vs 4%).
