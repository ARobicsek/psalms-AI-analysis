# Next Session Brief — Lemma/Root-Aware Concordance (D & E)

**Written:** end of Session 350 (2026-06-02). **Prereq reading:** `docs/architecture/LEMMA_ROOT_SEARCH_PROPOSAL.md` (full design + findings), then this file.

## Where we left off (Session 350)
We made the concordance trace **distinctive single roots** instead of verbatim verse phrases, lifting external-match yield from **24% → ~90%** across Ps 54–58 (changes A/B/C, all in production). But that win rides on **runtime string-expansion against a surface-form column** — there is still **no lemma/root data** in the database. Three known weaknesses remain, all rooted in the missing morphology:
1. Root selection uses *surface* frequency, which confuses a rare inflection with a rare root (mitigated only by a "prefer 3-letter forms" heuristic, not a fact).
2. Prefixes/suffixes leak into queries (`בְּצֵל` traces as `בצל`, not the bare root `צל`).
3. Phrase/collocation matching misses genuine conjugation differences (`חסד אמת` won't catch `חסדו ואמתו`) and cross-verse spans; `is_root_match` over-matches (`אב`~`אבד`).

## The job this session: D & E — wire in true morphology
**Goal:** add persistent `lemma` and `root` columns to the `concordance` table (312K rows, `database/tanakh.db`), populated once from ETCBC/BHSA, so root search becomes an exact indexed `WHERE root = ?` and 2-word search matches on lemma (conjugation/order/affix tolerant).

**The shortcut that makes this cheap:** the project already built the ETCBC pipeline (`src/hebrew_analysis/morphology.py`, `cache_builder.py`) and a **Psalms-only** surface→lemma cache (`src/hebrew_analysis/data/psalms_morphology_cache.json`). It was never connected to search. So this is integration, not a build.

### Recommended order of work (from the proposal §4)
1. **Build full-Tanakh BHSA annotation.** `pip install text-fabric`; extend `cache_builder.py` to also read `F.root` (not just `F.lex`) and emit **per-token** `(book, chapter, verse, position) → (lemma, root)` for the whole Bible. Positional keying avoids the global-dict collisions and the shin/sin-dot join problem.
2. **Schema migration** (new `scripts/add_lemma_column.py`): `ALTER TABLE concordance ADD COLUMN lemma TEXT; ADD COLUMN root TEXT;` backfill by joining BHSA token order to our `position` ordering per verse; `CREATE INDEX idx_conc_root ON concordance(root)` (+ `lemma`). **Validate positional alignment on Psalms first** against the existing cache — this is the main risk (ETCBC tokenization vs our maqqef-split). Normalize shin/sin dots on ingest (21% of keys).
3. **Search layer** (`src/concordance/search.py`): add a `column='root'`/`'lemma'` branch to `search_word`; rewrite `_verse_contains_phrase`/`_verse_contains_all_words` to compare on `root`/`lemma`; remove `is_root_match` (`root_matcher.py`) and the phrase-variation suppression in `concordance_librarian.py`.
4. **Selection layer** (`src/concordance/root_selection.py`): replace the surface-frequency heuristic with true root frequency; retire the `COMMON_CAP` post-search heuristic in favor of exact root frequency.
5. Keep a naive fallback only for genuine cache misses; log misses to monitor coverage.

### Watch-items
- **Positional alignment** (validate on Psalms before full Tanakh) — the real hazard.
- **Lexeme vs root**: populate BOTH (`lex` groups inflections of one word; `root` groups cognates — the current cache only has `lex`, so it would NOT group חיים with חיה).
- **License**: ETCBC is CC BY-NC (fine, non-commercial). If that ever changes, OSHB/morphhb is CC BY with per-word positional IDs.

### How to validate the win
Re-run `python scripts/EXPERIMENT_concordance_eval.py 54 55 56 57 58` (reuses production Stage-1 discoveries from each `micro_v2.json`; no re-discovery needed) and compare external-yield **and match quality** against Session-350 numbers. Spot-check previously-broken cases now work: `פלג לשון` self-matches; `חסד אמת` catches `חסדו ואמתו`; `בצל כנפיך` traces `צל`/`כנף` cleanly; confirm `is_root_match` false positives are gone. Then run one psalm through the full pipeline to confirm bundle/DOCX render correctly.

### Decisions still open (ask the user)
- Render the Methods "Concordance Entries Reviewed" line as `root ⟵ source phrase` instead of the bare root? (Deferred from Session 350.)
- Should lemma search default to `root` (cognate-grouping) or `lemma` (inflection-grouping) for the writer's purposes?

## Session-350 context you may want
- Knobs as shipped: `MAX_ROOT_SEARCHES=12` (augmentation), `COMMON_CAP=60` (post-search drop), `MAX_DISPLAY_RESULTS=10` (Hebrew-only, random canon-spread sample), collocations ≤2 words and no longer expanded to the verse form.
- The concordance section now reaches the writer/synthesis in full (no trim; bundle stays under the 350K-char cap). Dropping the English gloss already roughly halved its footprint.
