# Next session (413) — start here

Session 412 (record: `IMPLEMENTATION_LOG.md` Session 412; `archive/S412_echoes_register_and_rhyme/README.md`) ran no
psalm. It answered the author's two points on the Ps 84 guide: **the writer no longer reads the used-works register**
(its dossier was always checked against it; a new STEP 5a⅝ checks the finished draft for repeats, ~0.4¢, and sends any
to the copy editor to cut), and a **Sound Patterns** bundle section flags verses where 3+ words rhyme (4 in the
Psalter, at chance level, so the note warns the writer not to claim the sound chose the words). Ps 86 is still next,
and is the first run on both changes.

## 0. Check on Ps 86 (the first run on the S412 changes)

- **The writer's thinking** has no "verifying source material / permissible" pass over the echoes; the dossier opens
  "… already been checked against what the guides to other psalms in this collection used" and has no
  `### Already used in this collection` block (a fresh run writes the new dossier; a reused bundle is stripped at load,
  log line "Stripped the legacy used-works register").
- **STEP 5a⅝** logs `[echoes] repeat check: N works … M already used in another guide`; `psalm_086_echo_repeats.json`
  is written. A repeat should be rare (0 on Pss 77–85); if one appears, read the copy editor's change log to see that it
  cut the quotation and its framing and mended the join, and the editors' report's "Echoes repeated" table.
- **Writer additions from memory**: watch whether the count changes now that the list is gone (Pss 81–84: 3–4 a guide).
- **Shimush Tehillim** present (it is exempt from the register now).
- **No duplicate entry** in `output/psalm_86/echoes/entries.json` vs the dossier (`merge_retrieved_twins`).
- **Sound Patterns**: none for Ps 86 (expected). The next psalm with one is **Ps 90** (90:2); then read how the writer
  used the line, and whether it overclaimed.

---

*Carried from the 412 prompt (unchanged; S412 did not run Ps 86):*

Session 411 (record: `IMPLEMENTATION_LOG.md` Session 411; `archive/psalm_85_S411_run/README.md`): **Ps 85** ran end to
end on all defaults ($7.96, exit 0, no code changed), guide at `Documents/Psalm study guide/Psalm 85.docx` (+ PDF).
**Ps 86's deep research and check are on disk** (`data/deep_research/psalm_086_*`, 2026-10-30; the check is long,
30K, so watch the cleaner pre-flight). Ps 86 has a Shared Passages section (no doublet): 86:14 ~ Ps 54:5, 86:15 ~
Exod 34:6 (and Ps 103:8, Joel 2:13, Jonah 4:2, Ps 145:8), 86:6 ~ Ps 130:2. Small find: the 130:2 line prints
`אזְנֶיךָ` without the aleph's qamats (`_span_words` joins BHSA tokens; check whether the token or the join drops the mark
before trusting the quotation).

## 1. The author's read of Pss 83, 84 and 85

**S412 update**: Ps 84, the author: "I thought it was really good"; its two points (the writer filtering echoes in its
reasoning; 84:12's rhymes) were handled in S412. Pss 83 and 85 still to ask.

Ask for all three (none given yet). Known already:
- **Essay length after the edit turn**: Ps 83 3,084, Ps 84 2,444, Ps 85 2,641 counted (~7% high). The edit turn stays as
  the author likes it (memory `essay-edit-turn-keep`).
- **Fact check**: Ps 83 13.8/100, Ps 84 12.8, Ps 85 12.0; all handled by the revision. Ps 85's lead category was
  commentator readings misassigned or inverted (Radak's ויש מפרשים reading as his own; Malbim's chesed/emet →
  tzedek/shalom inverted; Ezekiel's dry bones given to three commentators, only Rashi); then absolutes (נשאת עון "only
  here and 32:5", also Ezek 4:5).
- Practical Kabbalah present on Pss 84 and 85.

## 2. Offered, not built (carried)

- **Rashi's pinned Hebrew version** is gone from Sefaria: the fallback to "Vocalized Edition" has now fired on Pss 83,
  84, 85. Offer the re-pin: compare the two editions on a few psalms, update `commentary_librarian.PINNED_VERSIONS`,
  clear `data/sefaria_cache/commentary/`.
- **The citation checker's pairing** (`STEP 5a½`): Ps 85's one kept flag was again a whole rabbinic passage (the
  midrash where Israel and God each say "the returning is yours") checked against one verse it quotes (Mal 3:7); 0 after
  the revision. Plus the S410 ketiv/qere case. Offer; do not build unasked.
- **Re-render the methods page of Pss 29, 81, 82** ($0): set `research.deep_research_checked` in each
  `psalm_NNN_pipeline_stats.json` where the bundle loaded the clean file, then `run_docx_only.py N --pdf`.
- **Shimush Tehillim** (author chose nothing): present on Pss 84, 85; raise only if it goes missing again.
- **`--skip-micro` never refreshes a bundle's deep research** (a `replace_deep_research_section` would close it).

## 3. Watch on the next runs

- **Gemini implicit cache on the verse call**: Ps 85 HIT (read 197K); Ps 84's miss is now one in four. Keep reading the
  `[forest] verses:` line; investigate only on a second miss.
- **The revision's block-quote guard**: 4 of 21 revised paragraphs on Ps 85 (P42 dropped 15 lines), 6 of 17 on Ps 84,
  12 of 27 on Ps 83. The log says "rejected Pnn: dropped N block-quote line(s)"; earlier checks found the prose fixes
  kept and the original quotations intact. Spot-check one if a count is large.
- **OpenAI flex 429s** ("Flex processing is temporarily unavailable") hit the echoes locator on Ps 85; the S397 retry
  and standard-tier fallback absorbed them. Only a concern if a stage fails or the standard-tier share grows.
- Shared Passages on Ps 86 (shared lines, no doublet) and later on a doublet psalm (108, 96, 105, 106, 115, 135, 136):
  a doublet must lead the section and the guide name it.
- The 65,536 cap on long psalms' verse calls (Ps 85: 22.5K out); re-check the `gemini-4-argon` price row after
  2026-11-30.

## 4. Carried

The 410 prompt §4 (the 407 handoff: shared-dossier errors; the batch re-render offer).
