# Session 391 — Sefaria probe (records)

The measurements behind `docs/plans/S391_SEFARIA_EVALUATION.md`. All $0 (Sefaria's public API, 2026-10-01).

| File | What it is |
|---|---|
| `sweep.py` | `/api/links/Psalms.N` for all 150 psalms (the raw result was 40 MB and is NOT kept) |
| `links_by_category.json` | that sweep reduced to link counts per psalm per category |
| `fetch.py` | v3 text fetch (Hebrew + default English) used by the others |
| `harvest.py` | PROTOTYPE reception harvest for one psalm (drops commentary/reference/anthologies; windows around the quotation) — Ps 77: 162 passages |
| `sacks_lit.py` | downloads Rabbi Sacks's siddur / Rosh HaShana / Yom Kippur / haggadah commentary (1.38M chars; NOT kept — Koren CC-BY-NC text) |
| `sacks_liturgical_alignment.json` | PROTOTYPE alignment of those comments to psalms (incipit match + "Psalm N" mentions); unvetted, has false positives |
| `hsearch.py` | Hebrew phrase search (`/api/search-wrapper`, `naive_lemmatizer`) across Sacks's works, for quotations Sefaria never linked |

Notes: `sacks_lit.py` as written misses nodes with no English title (the Siddur's Shabbat section); the session re-fetched those by `key`. The window logic in `harvest.py` falls back to the segment's start when it cannot find a "Psalms N:V" string, so its windows are an upper bound on size, not a production cut.
