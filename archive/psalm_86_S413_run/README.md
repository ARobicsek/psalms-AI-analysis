# Psalm 86 — Session 413 run

Command: `python scripts/run_enhanced_pipeline.py 86` (all defaults: Gemini 4 Argon writer + revision, Opus 5.5 SD and macro,
fact check on). Exit 0. Guide: `output/psalm_86/`, copied to `Documents/Psalm study guide/Psalm 86.docx` (+ PDF, 20 pp).
Log: `run.log` here (local only; `*.log` is not committed). The first run on the S412 changes (no register in the
writer's dossier; STEP 5a⅝ repeat check).

## Cost: $7.94

| stage | cost |
|---|---|
| deep research cleanup (Sonnet 5.5, pre-flight) | $0.105 |
| macro (Opus 5.5) | $0.285 |
| echoes v3 | $1.15 |
| micro + research bundle | $1.74 |
| synthesis discovery (Opus 5.5) | $2.03 |
| writer (Argon: essay $0.46, edit $0.11, verses $0.24) | $0.805 |
| citation verification | $0.050 |
| echo repeat check (STEP 5a⅝) | $0.004 |
| fact check (flex) | $0.993 |
| writer revision (Argon) | $0.331 |
| copy editor (gpt-5.4) | $0.447 |

## The S412 checks

- **Dossier**: opens "Every entry has already been checked against what the guides to other psalms in this collection
  used"; no `### Already used in this collection` block; 41 entries, all distinct (no duplicate after
  `merge_retrieved_twins`); 54K chars. Echoes: 0 dropped as already used.
- **Bundle 303,740 chars** (Ps 85: 361K, Ps 84: 363K); the writer's essay call read 168K Gemini tokens (recent psalms
  ~184–205K). No trimming.
- **Writer's thinking**: no "verifying source material / permissible" pass over the echoes. The only "already used"
  reasoning is the verse call avoiding what its own essay used.
- **STEP 5a⅝**: `[echoes] repeat check: 23 works in the guide to Ps 86, 0 already used in another guide`, 0.4¢;
  `psalm_086_echo_repeats.json` = `{"repeats": []}`.
- **Additions from memory**: 23 of the 41 dossier entries appear in the guide, and the repeat check counted 23 works, so
  ~0–1 additions (Pss 81–84: 3–4 a guide). Name-match count, loose; the next run's register entry for Ps 86 settles it.
- **Shimush Tehillim** present in the guide. **Sound Patterns**: none (expected; next on Ps 90).

## What else happened

- **Cleaner pre-flight**: Sonnet alone, one pass, 10.5¢ on the long (30K) check; `deep_research_checked` True.
- **Rashi's pinned Hebrew** unavailable again (fourth psalm running), fell back to "Vocalized Edition".
- **Shared Passages** present (86:14 ~ 54:5, 86:15 ~ Exod 34:6 and its echoes, 86:6 ~ 130:2); the guide argues from the
  54:5 borrowing (זָרִים → זֵדִים, "they did not set God" → "You") and from Exod 34:6.
- **Essay**: 2,860 → **2,614 words** after the edit turn, 10% → 7% long (counter ~7% high). Argon's edit-turn thinking
  guessed its essay at ~1,800 words against the counter's 2,836.
- **Gemini cache**: edit turn read 168K; **verse call HIT** (read 181K, $0.24). Two hits since Ps 84's miss.
- **Citation check**: 8 candidates, GPT-5.1 kept 0.
- **Fact check**: 240 claims, **24 contradicted (10.0/100)**, 14 unverifiable — the lowest of Pss 83–86. Commentators given
  readings they don't hold (Radak ×3, Alshich on Saul's men, Minchat Shai's paseq, Rashi's second reading, Ibn Ezra/Radak
  on Ps 16); absolutes ("always *Ahavah Rabbah*", "all three rites", the name "replaced in every adaptation"); counts (v. 7
  "six words", the Exod 18:9 list, παράνομοι as Ps 119's "standard" rendering); R. Tanchum's wineskin given to R. Tanchuma
  (and so to Siddur Rashi); KTU 1.14 column; FRE 801(d)(2) "binds". Revision 24/24 in 17 paragraphs; block-quote guard
  on 3 (P14, P40, P48); all 70 quotation lines identical before and after, P14's prose fix kept.
- **Copy editor**: 8 FIND/REPLACE edits (19 diff hunks; the editors' report counts 18); no citation mismatches.

## Found, then fixed at the author's request ("please fix the items you found")

- **Qamats qatan was missing from the whole concordance.** `hebrew_text_processor.CANTILLATION_RANGE` ran
  `׃-ׇ`, and U+05C7 is QAMATS QATAN, a vowel, so the voweled level stripped it: `tanakh.db`
  `concordance.word_voweled` held it in 0 of 312,479 tokens (the 130:2 `אזְנֶיךָ` the 413 prompt asked about;
  `_span_words` was innocent). Fixed: the range ends at U+05C6 and `VOWEL_RANGE` carries U+05C7; the consonantal level
  (full `֑-ׇ`) still drops it. The database (gitignored) was repaired in place: the 7,421 rows whose `word`
  has the mark were recomputed, each differing from before ONLY by the restored mark; backup
  `database/tanakh_pre_S413_qamats_qatan.db` (ignored by `*.db`). Voweled SEARCH is unchanged in effect (a query with
  plain qamats for a qamats-qatan word matched nothing before and still does). Sound Patterns reads `verses.hebrew`,
  unaffected. `tests/test_hebrew_text_processor.py` (+3). Ps 86's Shared Passages now prints אׇזְנֶיךָ.
- **Rashi's pin**: Sefaria RENAMED "Sefaria vocalized edition" to "Vocalized Edition"; the text is byte-identical (Pss 29,
  76 cached under the old title vs today's). `PINNED_VERSIONS["Rashi"]` re-pinned; a live fetch loads with no fallback.
  The cache is keyed on the pinned titles, so old files refetch on their own (same text).
- **The `---` glued to the last verse paragraph**: `CopyEditor._split_changes` rstrips the corrected text, so the verse
  body lost its closing newline and `_reassemble` glued the protected `---` + methods zone onto it (many psalms; the
  DOCX was never affected). `_reassemble` now gives each edited zone back its own trailing whitespace; test in
  `tests/test_fact_checker.py`. Ps 86's copy-edited markdown patched by hand; older psalms left as they are.

- **Stray `**` in the DOCX** (the author's Ps 85 screenshot, `ה**וֹדוּ`; also Ps 83 `כֵּן**`): the DOCX printed literal `**` in a lifted Hebrew line (the author's screenshot, Ps 85: `ה**וֹדוּ`; also Ps 83 `כֵּן**`): `document_generator._split_long_hebrew_block` counted a bare `**` INSIDE a word as a word break (`**י**וֹמָם` = 2 words), so a 4-word acrostic reached the 6-word lift threshold, and the match began after the opening `**`, leaving the block an odd number of markers. Now emphasis inside a word is part of it, a separator needs a real separator character, and a bold opening just before the match joins the block. Sweep of every guide: 3 of 5,826 Hebrew lines change (Pss 81, 83, 85). Pss 83 and 85 re-rendered and copied to Documents.

**585 tests pass** (+5). The Ps 86 DOCX is unchanged by all four (none reaches its text).
