# Psalm 84 — Session 410 run

Command: `python scripts/run_enhanced_pipeline.py 84` (all defaults: Gemini 4 Argon writer + revision, Opus 5.5 SD and macro,
fact check on). Exit 0. Guide: `output/psalm_84/`, copied to `Documents/Psalm study guide/Psalm 84.docx` (+ PDF, 20 pp).
Log: `run.log` here (local only; `*.log` is not committed).

## Cost: $8.32

| stage | cost |
|---|---|
| deep research cleanup (Sonnet 5.5, pre-flight) | $0.144 |
| macro (Opus 5.5) | $0.280 |
| echoes v3 | $0.877 |
| micro + research bundle | $1.615 |
| synthesis discovery (Opus 5.5) | $2.326 |
| writer (Argon: essay $0.49, edit $0.09, verses $0.66) | $1.243 |
| citation verification | $0.073 |
| fact check (flex) | $0.969 |
| writer revision (Argon) | $0.366 |
| copy editor (gpt-5.4) | $0.428 |

## What happened

- **Cleaner pre-flight**: Sonnet on its own, 14¢, under the $0.20 cap; `deep_research_checked` recorded True.
- **Bundle**: 362,830 chars after reception (24 of 252 passages, 20.6K). **No Shared Passages section** (Ps 84 shares
  nothing; confirmed with the standalone module) and no Related Psalms. Sacks: 9 aligned comments, all on Ashrei (84:5
  opens it), dropped by the S392 mosaic rule as about Ps 145: correct. One Sefaria 504 on Mesillat Yesharim 7:21,
  recovered on the third try. Rashi's pinned Hebrew version unavailable, fell back to "Vocalized Edition" (as on Ps 83).
- **Essay**: draft 2,548 words / 16% long sentences; after the edit turn **2,444 / 6%** (counter ~7% high, so ~2,280):
  inside the target, unlike Ps 83's 3,084.
- **Gemini implicit cache MISSED on the verse call** (205K in, cache read 0; Pss 29 and 83 read 180–200K there): ≈ $0.38
  extra. No code changed since S409; treated as Google's best-effort cache. Watch for a repeat.
- **Practical Kabbalah subsection present** (Shimush Tehillim, Hebrew + translation); the fact check caught an added
  "bodily odor" in it, revised.
- **Fact check**: 235 claims, **30 contradicted (12.8/100)**, 7 unverifiable. Mostly source handling: composite Talmud
  quotations (Menachot 53a, Shabbat 30a + Makkot's speaker formula), Ibn Balaam vs Ibn Ezra, Rav vs R. Levi merged,
  Radak's conditional reading made plain, Rashi's מורה reading cut short; text slips (84:5 quoted as בְּבֵיתֶךָ; v. 6's
  בָךְ overlooked); absolutes (swifts' "only" resting place, "regularly", "all rites"); a far association's fact (OSPF
  routers). Revision 28/28 in 17 paragraphs, $0.37; the block-quote guard fired on 6 of them (prose fixes kept). The 2
  outside prose went to the copy editor, which fixed the Menachot and Shabbat 30a quotations.
- **Citation checks**: pre-revision 1 flag, Proverbs 26:2 quoted in its ketiv לֹא (translated consistently): sound, and
  the re-check after the revision dropped it, so it was never "corrected" to the qere. Post-copy-edit 1 flag: a false
  pairing (the Shabbat 30a quotation checked against 1 Kings 3:4 nearby, a word clipped at its prefix); the text is intact.
- **Copy editor**: 11 changes (superlatives, a Herodotus overgeneralisation, the two quotations).
