# Session 397 — the fact check on OpenAI Flex + compacted lookups (Ps 79)

**Input**: Ps 79's pre-copy-edit guide, rebuilt at $0 from `output/psalm_79/psalm_079_edited_*_pre_copy_edit.md`
with `commentary_formatter.py` (`psalm_079_print_ready_pre_ce.md`; all 42 sentences the production run flagged are in
it), and the production bundle `output/psalm_79/psalm_079_research_trimmed.md`. Same 6 chunks as production.

**A** = production (S396 pipeline run, standard tier, old lookups): `output/psalm_79/psalm_079_fact_check.json`.
**B** = this run (flex tier + compacted lookups): `flex_psalm_079_fact_check.json`.

| | A (production) | B (S397) |
|---|---|---|
| Cost | **$2.76** | **$1.22** (−56%) |
| Stage 1 (gpt-6-sol) | $2.60 | $1.16 |
| Lookups (stage 1) | 367 | 469 |
| Cache writes / reads (stage 1) | 511K / 3.20M | 371K / 3.16M |
| Claims | 335 | 316 |
| Contradicted / unverifiable | 29 / 13 | 25 / 8 |
| Stage-1 chunk time | 95–156 s | 79–168 s |

All B calls came back `service_tier: flex`; no 429s, no fallbacks.

## Accuracy (my read of every disagreement: `disagreements.txt`)

- Caught by both: ~13, including the Tachanun v. 8 / v. 9 adjacency (on different sentences).
- **A only, ~11 real**: Lamentations Rabbah 4:16 pairs Lev 17:13 with Ezekiel, not the psalm (B: unverifiable); the
  "defiled altar" (the psalm says temple); El Maleh lacks "on the ground"; נָוֵהוּ is the penultimate word;
  לְעִיִּים also in Jer 26:18; Alshich's alternative readings presented as his only one (×3); Sanhedrin 98a does not
  say the Messiah is bound; Malbim is not "less vindictive". Pedantic: Jeremiah's three verbs. **Likely false alarm**:
  the Ashkenaz *Avinu Malkeinu* line normally does read נְקוֹם לְעֵינֵינוּ (Sefaria's machzor text lacks it).
- **B only, ~11 real**: 1 Macc 7:17 quotes through v. 3; the Lamentations Rabbah question is about the heading, not
  v. 5; the Yom Kippur run has v. 8 without v. 9; the kinah's refrain and its doubled סביבות (×2); the Lithuanian
  selichot continue past 79:7; Ibn Ezra's "many", not "most"; Orestes alone makes the plea; one Lag BaOmer line, not
  several; the Yerushalayim transliteration. Pedantic: the credit file "may" still exist. **False alarm**: in Maariv,
  79:13 IS the last verse before ברוך ה׳ ביום.

Level on recall and precision; the spread is the run-to-run variance S386 already recorded on identical settings. The
liturgical checks did not suffer from the compacted lookups (B made more liturgical catches than A). N = 1.

## Files

`compare.py` / `diff.py` — verdict comparison by sentence; `remeasure.py` — replays a run's logged lookups at $0 and
counts the tokens they return (Ps 79: 405,577 → 225,040; Ps 78: 389,529 → 265,343).
