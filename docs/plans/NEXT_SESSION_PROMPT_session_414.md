# Next session (414) — start here

Session 413 (record: `IMPLEMENTATION_LOG.md` Session 413; `archive/psalm_86_S413_run/README.md`): **Ps 86** ran end to
end on all defaults ($7.94, exit 0), guide at `Documents/Psalm study guide/Psalm 86.docx` (+ PDF, 20
pp). It was the first run on the S412 changes, and **every S412 check passed**: no register in the dossier or the
writer's thinking, STEP 5a⅝ logged 23 works / 0 repeats (0.4¢), Shimush present, no duplicate echo entries, ~0–1
writer additions from memory (Pss 81–84: 3–4). Bundle 304K (Ps 85: 361K). Fact check 24/240 (10.0/100), the lowest of
Pss 83–86. Ps 87 is next (check its deep research is on disk: `data/deep_research/psalm_087_*`).

## 0. Fixed in S413 after the run (the author: "please fix the items you found")

- **Qamats qatan** is back in the concordance (`CANTILLATION_RANGE` used to strip U+05C7; 7,421 `word_voweled` rows
  repaired in place, backup `database/tanakh_pre_S413_qamats_qatan.db`). **On a new machine** `tanakh.db` is rebuilt
  from code, which is now right; on this one, delete the backup once a run or two look normal.
- **Rashi** re-pinned to "Vocalized Edition" (a Sefaria rename; text identical). The fallback WARNING should be gone
  from the next run's log; if it fires again, Sefaria changed something else.
- **The copy editor no longer glues the closing `---`** to the last verse paragraph of the copy-edited markdown.
- **No more literal `**` in lifted Hebrew lines** (Pss 83, 85 re-rendered and copied to Documents).
- **Sound Patterns** still unseen live; the next psalm with one is **Ps 90** (90:2). Read how the writer used it and
  whether it overclaimed.

## 1. The author's read of Pss 83, 85 and 86

**S412 update**: Ps 84, the author: "I thought it was really good"; its two points (the writer filtering echoes in its
reasoning; 84:12's rhymes) were handled in S412.

Ask for Pss 83, 85 and 86 (Ps 84 given: "really good"). Known already:
- **Essay length after the edit turn**: Ps 83 3,084, Ps 84 2,444, Ps 85 2,641, Ps 86 2,614 counted (~7% high). The edit turn stays as
  the author likes it (memory `essay-edit-turn-keep`).
- **Fact check**: Ps 83 13.8/100, Ps 84 12.8, Ps 85 12.0, Ps 86 10.0; all handled by the revision. Ps 85's lead category was
  commentator readings misassigned or inverted (Radak's ויש מפרשים reading as his own; Malbim's chesed/emet →
  tzedek/shalom inverted; Ezekiel's dry bones given to three commentators, only Rashi); then absolutes (נשאת עון "only
  here and 32:5", also Ezek 4:5). Ps 86's: commentators given readings they don't hold (Radak ×3, Alshich,
  Minchat Shai), absolutes ("always *Ahavah Rabbah*", "all three rites"), counts; R. Tanchum's wineskin given to R. Tanchuma.
- Practical Kabbalah present on Pss 84 and 85; Shimush Tehillim present on Ps 86.

## 2. Offered, not built (carried)

- **The citation checker's pairing** (`STEP 5a½`): Ps 85's one kept flag was again a whole rabbinic passage (the
  midrash where Israel and God each say "the returning is yours") checked against one verse it quotes (Mal 3:7); 0 after
  the revision. Plus the S410 ketiv/qere case. Offer; do not build unasked.
- **Re-render the methods page of Pss 29, 81, 82** ($0): set `research.deep_research_checked` in each
  `psalm_NNN_pipeline_stats.json` where the bundle loaded the clean file, then `run_docx_only.py N --pdf`.
- **Shimush Tehillim** (author chose nothing): present on Pss 84, 85; raise only if it goes missing again.
- **`--skip-micro` never refreshes a bundle's deep research** (a `replace_deep_research_section` would close it).

## 3. Watch on the next runs

- **Gemini implicit cache on the verse call**: Pss 85 and 86 HIT (read 197K, 181K); Ps 84's miss looks like a one-off. Keep reading the
  `[forest] verses:` line; investigate only on a second miss.
- **The revision's block-quote guard**: 4 of 21 revised paragraphs on Ps 85, 3 of 17 on Ps 86 (all 70 quotation lines checked identical), 6 of 17 on Ps 84,
  12 of 27 on Ps 83. The log says "rejected Pnn: dropped N block-quote line(s)"; earlier checks found the prose fixes
  kept and the original quotations intact. Spot-check one if a count is large.
- **OpenAI flex 429s** ("Flex processing is temporarily unavailable") hit the echoes locator on Ps 85; the S397 retry
  and standard-tier fallback absorbed them. Only a concern if a stage fails or the standard-tier share grows.
- Shared Passages on a doublet psalm (Ps 86 had shared lines only, used well: the 54:5 borrowing) (108, 96, 105, 106, 115, 135, 136):
  a doublet must lead the section and the guide name it.
- The 65,536 cap on long psalms' verse calls (Ps 85: 22.5K out); re-check the `gemini-4-argon` price row after
  2026-11-30.

## 4. Carried

The 410 prompt §4 (the 407 handoff: shared-dossier errors; the batch re-render offer).
