# Next session (411) — start here

Session 410 (record: `IMPLEMENTATION_LOG.md` Session 410; `archive/psalm_84_S410_run/README.md`): **Ps 84** ran end to
end on all defaults ($8.32, exit 0, no code changed), guide at `Documents/Psalm study guide/Psalm 84.docx` (+ PDF).
Ps 85's deep research and check are on disk (`data/deep_research/psalm_085_*`); it shares no passage (no Shared
Passages section expected).

## 1. The author's read of Pss 83 and 84

Ask for both (Ps 83's was never given). Known already:
- **Ps 84's essay landed in target** (2,444 counted, ~2,280 true, 6% long sentences); Ps 83's did not (3,084). One
  overshoot is not yet a pattern; the edit turn stays as the author likes it (memory `essay-edit-turn-keep`).
- Ps 84 fact check 30/235 contradicted (12.8/100), all handled; misquoted/composite rabbinic quotations lead.
- Ps 84 has the Practical Kabbalah subsection (Shimush Tehillim); Pss 81, 83 do not.

## 2. Offered, not built (carried from the 410 prompt)

- **Re-render the methods page of Pss 29, 81, 82** ($0): set `research.deep_research_checked` in each
  `psalm_NNN_pipeline_stats.json` where the bundle loaded the clean file, then `run_docx_only.py N --pdf`.
- **The citation checker's pairing** (`STEP 5a½`): Ps 83 had 16 pre-revision flags; Ps 84 two more false ones (a
  ketiv quotation, Prov 26:2 לֹא, flagged against the qere; a Shabbat 30a quotation checked against the neighbouring
  1 Kings 3:4 citation, with a word clipped at its prefix: ּנְךָ). Two distinct defects: quote-to-citation pairing, and
  ketiv/qere (a quotation of either form should pass). Offer; do not build unasked. Note the risk the ketiv case
  carries: a flag reaching the copy editor invites a "fix" that contradicts the translation.
- **Shimush Tehillim** (author chose nothing for now): present on Ps 84; raise only if it goes missing again.
- **`--skip-micro` never refreshes a bundle's deep research** (a `replace_deep_research_section` would close it).

## 3. Watch on the next runs

- **Gemini implicit cache on the writer's verse call**: Ps 84 read 0 of 205K (≈ $0.38 lost; Pss 29/83 read 180–200K).
  Read the `[forest] verses:` log line. If it misses again, investigate (what precedes the verse call's prefix; whether
  the essay-edit turn or a request field changed it) rather than calling it Google's best effort a second time.
- **Rashi's pinned Hebrew version** is gone from Sefaria (falls back to "Vocalized Edition", a WARNING, on Pss 83 and
  84). If the author wants the warning gone, compare the two editions on a few psalms and re-pin
  (`commentary_librarian.PINNED_VERSIONS`), then clear `data/sefaria_cache/commentary/`.
- Shared Passages on a doublet psalm (108, 96, 105, 106, 115, 135, 136): the section must lead with the DOUBLET and
  the guide name it.
- The cleaner pre-flight (Ps 84: 14¢, Sonnet alone); the 65,536 cap on long psalms' verse calls; Argon's long
  sentences; re-check the `gemini-4-argon` price row after 2026-11-30.

## 4. Carried

The 410 prompt §4 (the 407 handoff: shared-dossier errors; the revision's block-quote guard — 6 of 17 paragraphs on
Ps 84, 12 of 27 on Ps 83 — and the batch re-render offer).
