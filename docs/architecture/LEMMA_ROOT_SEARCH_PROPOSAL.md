# Lemma/Root Concordance Search — Design Proposal (D/E)

**Status:** proposal (not implemented). Written Session 350 after the A/B/C
distinctive-root changes shipped.
**Question it answers:** "What would it take to make root-based (and 2-word
root-based) concordance search *much* smarter, and would it actually add value to
our pipeline and final product?"

---

## 1. Where we are now (after A/B/C)

Root search today is **runtime string-expansion against a surface-form column**:

- The concordance table (`database/tanakh.db`, 312,479 rows) stores only surface
  forms — `word`, `word_voweled`, `word_consonantal`, `word_consonantal_split` —
  each indexed. **There is no lemma, root, or part-of-speech column.**
- To "trace a root," `ConcordanceLibrarian.generate_phrase_variations` brute-forces
  ~50–150 prefixed/suffixed *string* variants of the query word and runs an indexed
  exact-equality lookup for each, deduplicating by verse.
- Multi-word phrases get **no** morphological expansion: exact adjacent match, then a
  "same verse, all surface words present" fallback (`search_phrase_in_verse`).
- A permissive `root_matcher.is_root_match` (subsequence-either-direction) is used in
  parts of the path and produces real false positives (`אב ~ אבד`, `פלג ~ פלגלשונם`).

A/B/C made this *work well enough* — external-match yield went from 24% to ~90% on
Psalms 54–58 — but on three known weaknesses it is papering over the lack of real
morphology:

1. **Wrong root sometimes chosen.** Selection ranks candidates by *surface*
   frequency, which conflates "rare root" with "rare inflection." It picked the rare
   verb form `אַרְחִיק` (freq 2) over the meaningful root `נדד` (freq 5) until we added a
   "prefer 3-letter forms" tie-break — a linguistic guess, not a fact.
2. **Prefixes/suffixes leak into the query.** `בְּצֵל כְּנָפֶיךָ` traces as `בצל` (with the
   ב preposition) because the bare root `צל` is 2 letters and gets filtered; we cannot
   reliably strip `ב`.
3. **Collocations and phrases still miss inflected co-occurrences.** `פַּלַּג לְשׁוֹנָם`
   cannot match its own verse as a phrase (suffix on `לשון`); `חסד אמת` only matches
   because both *surface* forms happen to appear, and would miss `חסדו ואמתו`.

> **A fourth, latent ingredient:** the project already built an ETCBC/BHSA morphology
> pipeline (`src/hebrew_analysis/morphology.py`, `cache_builder.py`) and a **Psalms-only
> surface→lemma cache** (`src/hebrew_analysis/data/psalms_morphology_cache.json`,
> 5,353 forms, CC BY-NC). **It was never wired into concordance search.** So "true root
> search" is largely an *integration* job, not a build-from-scratch.

---

## 2. The proposal

Add two persistent columns to the `concordance` table, populated **once** from BHSA,
keyed by `(book, chapter, verse, position)`:

- `lemma` — the ETCBC lexeme (`lex`): groups inflections of the *same* word.
- `root` — the ETCBC `root` feature: groups *cognate* words (noun חיים with verb חיה),
  i.e. the triliteral root a reader thinks of.

Then:

- **Root search** becomes an exact, indexed `WHERE root = ?` — suffix/prefix/binyan
  tolerant for free, no string explosion, no false positives.
- **2-word root search** = "same verse, both query lemmas/roots present, position
  difference small," matched on the `root`/`lemma` column instead of surface substrings.
- Delete the `is_root_match` subsequence matcher and the phrase-variation suppression
  hack; both exist only to compensate for missing morphology.

**Ingest source:** BHSA via Text-Fabric (already coded in `cache_builder.py`; flip
`include_all_bible=True`, additionally read `F.root`). Alternative if licensing ever
needs to be permissive (CC BY vs CC BY-NC): OSHB/morphhb, whose per-word positional IDs
map cleanly onto our `(book, chapter, verse, position)` key.

**Three gotchas (from the research pass):**
1. Cache keys retain shin/sin dots; our `word_consonantal` strips them — 21% of keys
   would silently fail to join unless normalized on ingest.
2. The existing cache stores `lex` only, not `root` — so it would *not* group חיים with
   חיה. Populate **both** columns.
3. Coverage is Psalms-only today; rebuild for the full Tanakh (cross-Tanakh search is
   the common case — `פלג` hit Genesis/Chronicles).

---

## 3. Does it add value to *our* pipeline and product? (honest assessment)

A/B/C already gets ~90% external yield, so the win here is **not raw recall** — it is:

| Benefit | Why it matters to the final commentary |
|---|---|
| **Correct root every time** | Removes the surface-frequency guesswork (#1, #2 above). The writer/synthesis get the root the verse is actually built on, not a rare inflection or a prefix-laden stem. Directly improves the *quality* of the intertexts surfaced. |
| **Precision — no false positives** | `is_root_match` currently can feed junk parallels (`אב`~`אבד`) into the bundle. For a *scholarly* product whose copy editor already hunts false Hebrew claims, eliminating a whole class of spurious matches protects credibility and saves copy-editor corrections. |
| **2-word collocations that actually work** | `חסד אמת` would catch `חסדו ואמתו`; `פלג לשון` would self-match and find true cognate pairings. The collocation path goes from "lucky surface hits" to reliable. |
| **Exact distinctiveness gating** | The current `COMMON_CAP=60` post-search heuristic (and the `[2,120]` selection window) become unnecessary — true root frequency tells us precisely how distinctive a word is, so we keep the genuinely rare and drop the common with no tuning. |
| **Token efficiency** | Fewer junk/duplicate matches and exact frequency gating mean we can show *fewer, better* results per search (see token-cost note), reducing the research-bundle growth A/B/C introduced. |

**Where it does *not* help:** the headline recall win is already banked by A/B/C; if we
only cared about "find more parallels," this would be optional. The case for it is
**precision, correctness, and removing brittle heuristics** — which for a scholarship
product that ships to readers is arguably more important than recall.

**Net:** worth doing as a focused follow-up (est. 1–2 days), *after* A/B/C is validated
in production. It is the principled version of what A/B/C approximates.

---

## 4. Ranked implementation steps

1. **Build full-Tanakh BHSA annotation.** `pip install text-fabric`; extend
   `cache_builder.py` to emit per-token `(book, chapter, verse, position) → (lemma, root)`
   for the whole Bible (not a global form→lemma dict — positional keying eliminates the
   296 collisions and the shin/sin-dot join problem). Normalize shin/sin dots.
2. **Schema migration.** `ALTER TABLE concordance ADD COLUMN lemma TEXT; ADD COLUMN root TEXT;`
   backfill by joining BHSA token order to our `position` ordering per verse; add
   `CREATE INDEX idx_conc_root ON concordance(root)` (and `lemma`). One-off script
   `scripts/add_lemma_column.py`. **Validate positional alignment on Psalms first**
   against the existing cache (the main risk: ETCBC tokenization vs our maqqef-split).
3. **Search layer.** Add a `column='root'`/`'lemma'` branch to `search_word`; rewrite
   `_verse_contains_phrase` / `_verse_contains_all_words` to compare on `root`/`lemma`;
   remove `is_root_match` and the phrase-variation suppression.
4. **Selection layer.** Replace the surface-frequency heuristic in
   `src/concordance/root_selection.py` with true root frequency; drop the `COMMON_CAP`
   heuristic in favor of exact root frequency.
5. **Keep a naive fallback** only for genuine cache misses (defective/foreign spellings);
   log misses to monitor coverage.

**Files touched:** `src/hebrew_analysis/cache_builder.py`, new `scripts/add_lemma_column.py`,
`src/data_sources/tanakh_database.py` (schema), `src/concordance/search.py`,
`src/agents/concordance_librarian.py`, `src/concordance/root_selection.py`.

**Risks:** positional alignment (validate on Psalms), shin/sin normalization, license
(CC BY-NC fine for non-commercial; OSHB if that changes).

---

## 5. Sources
- openscriptures/morphhb (OSHB) — CC BY 4.0
- ETCBC/bhsa — CC BY-NC 4.0; `lex_utf8` + `root` features
- In-repo: `src/hebrew_analysis/INTEGRATION_PLAN.md` (prior rollout plan),
  `src/hebrew_analysis/data/psalms_morphology_cache.json` (existing Psalms cache)
