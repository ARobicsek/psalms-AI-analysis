# Interactive Hebrew Concordance Tool — Implementation Plan

## Overview

A standalone CLI tool (`scripts/concordance_tool.py`) that provides an interactive menu-driven interface for searching Hebrew words and phrases across the entire Tanakh. Leverages the existing 4-layer concordance search system, BDB/Klein lexicon lookups, and optional AI-powered curation via Claude.

**Key principle:** User can enter Hebrew with or without diacritics (nikud/cantillation) — the tool normalizes all input to consonantal form before searching.

---

## User Flow

```
┌─────────────────────────────────────────────────┐
│  HEBREW CONCORDANCE TOOL                        │
│                                                 │
│  Enter Hebrew word(s): שָׁמַר  (or שמר)         │
│                                                 │
│  ─── Main Menu ───                              │
│  [1] Concordance search                         │
│  [2] Lexicon lookup (BDB + Klein definitions)   │
│  [3] Both (search + definitions)                │
│  [q] Quit                                       │
│                                                 │
│  (if concordance search selected)               │
│                                                 │
│  ─── Search Scope ───                           │
│  [1] Entire Tanakh                              │
│  [2] Torah                                      │
│  [3] Prophets                                   │
│  [4] Writings                                   │
│  [5] Pick specific books...                     │
│                                                 │
│  ─── Match Mode ───                             │
│  [1] Exact consonantal match                    │
│  [2] With prefix/suffix variations              │
│  [3] Substring/root discovery                   │
│  [4] Phrase search — consecutive words           │
│  [5] Phrase search — same verse, any order       │
│                                                 │
│  ─── Result Options ───                         │
│  Max results [50]:                              │
│  [1] All matches (canonical order)              │
│  [2] Random sample                              │
│  [3] AI-curated (semantic range examples)       │
│                                                 │
│  ─── Results ───                                │
│  (formatted results with verse context)         │
│                                                 │
│  ─── Post-Results ───                           │
│  [1] Refine search (change scope/mode)          │
│  [2] New search                                 │
│  [3] Export results to markdown                 │
│  [4] AI commentary (semantic range analysis)    │
│  [5] Lexicon lookup for matched word            │
│  [q] Quit                                       │
└─────────────────────────────────────────────────┘
```

---

## Diacritics Handling

The tool must work identically whether the user types `שָׁמַר` or `שמר`.

**Strategy:** Normalize all user input through `normalize_for_search(text, level='consonantal')` before passing to any search method. This strips vowels (nikud) and cantillation (te'amim), leaving only consonants.

**Implementation:**
```python
from src.concordance.hebrew_text_processor import normalize_for_search, is_hebrew_text

def normalize_input(raw: str) -> str:
    """Normalize user input — works with or without diacritics."""
    return normalize_for_search(raw.strip(), level='consonantal')
```

All search methods already accept `level='consonantal'` (and it's the default), so the existing API handles this naturally. The key is to normalize the input *before* validation/display so the user sees what will actually be searched.

**Display flow:**
```
Enter Hebrew word(s): שָׁמַר
Searching for: שמר (consonantal)
```

---

## File Structure

**Single file:** `scripts/concordance_tool.py` (~400 lines)

```python
scripts/concordance_tool.py
├── Constants
│   ├── BOOK_LIST              # All 39 books from TANAKH_BOOKS for selection menu
│   └── DEFAULT_MAX_RESULTS    # 50
│
├── Input & Menus
│   ├── get_hebrew_input()     # Prompt for Hebrew, normalize, validate
│   ├── select_action()        # Concordance / Lexicon / Both
│   ├── select_scope()         # Tanakh / Torah / Prophets / Writings / specific books
│   ├── select_match_mode()    # Exact / variations / substring / phrase modes
│   ├── select_result_options()# Max results, ordering (canonical / random / AI-curated)
│   └── post_results_menu()    # Refine / new / export / AI commentary / quit
│
├── Search Execution
│   ├── execute_search()       # Dispatch to correct ConcordanceSearch method
│   ├── execute_lexicon()      # BDB + Klein lookup via BDBLibrarian
│   └── randomize_results()    # Random sampling from full result set
│
├── AI Features
│   ├── ai_curate_results()    # Claude selects representative examples
│   └── ai_commentary()       # Semantic range analysis of results
│
├── Display & Export
│   ├── display_results()      # Formatted terminal output
│   ├── display_lexicon()      # Formatted lexicon entries
│   └── export_to_markdown()   # Save results as .md file
│
└── main()                     # Entry point, main loop
```

---

## Detailed Component Specifications

### 1. Input Handling (`get_hebrew_input`)

```python
def get_hebrew_input() -> tuple[str, str, bool]:
    """
    Returns:
        (original_input, normalized_consonantal, is_multi_word)
    """
```

- Prompt user for Hebrew text
- Validate with `is_hebrew_text()` — reject if no Hebrew characters
- Normalize via `normalize_for_search(input, 'consonantal')`
- Detect multi-word input (contains spaces after normalization)
- Display: "Searching for: {normalized} (consonantal)"
- Return both original and normalized for display purposes

### 2. Scope Selection (`select_scope`)

```python
def select_scope() -> str:
    """Returns scope string compatible with ConcordanceSearch."""
```

Menu options:
1. **Entire Tanakh** → `"Tanakh"`
2. **Torah** → `"Torah"`
3. **Prophets** → `"Prophets"`
4. **Writings** → `"Writings"`
5. **Pick specific books** → sub-menu showing all 39 books grouped by category

For option 5, display books in three columns by category with numbers:
```
── Torah ──────────────    ── Prophets ────────────    ── Writings ───────────
 1. Genesis   בראשית        6. Joshua    יהושע         27. Psalms    תהלים
 2. Exodus    שמות          7. Judges    שופטים        28. Proverbs  משלי
 ...                        ...                        ...
```

User enters comma-separated numbers. Build scope string: `"Genesis,Psalms,Isaiah"`.

### 3. Match Mode Selection (`select_match_mode`)

```python
def select_match_mode(is_multi_word: bool) -> str:
    """Returns mode string: 'exact', 'variations', 'substring', 'phrase', 'phrase_loose'"""
```

For **single words**, show:
1. Exact consonantal match → `search_word()`
2. With prefix/suffix variations → `search_word_with_variations()`
3. Substring/root discovery → `search_substring()`

For **multi-word phrases**, show all five:
1-3 (same as above, applied to first word)
4. Phrase search — consecutive → `search_phrase()`
5. Phrase search — same verse → `search_phrase_in_verse()`

Default: option 2 (variations) for single words, option 4 (consecutive phrase) for multi-word.

### 4. Result Options (`select_result_options`)

```python
def select_result_options() -> tuple[int, str]:
    """Returns (max_results, selection_mode)"""
```

- Max results: prompt with default 50 (enter to accept)
- Selection mode:
  1. **Canonical order** — results as returned (by book/chapter/verse)
  2. **Random sample** — `random.sample()` from full result set
  3. **AI-curated** — Claude picks representative examples (see AI section)

### 5. Search Execution (`execute_search`)

```python
def execute_search(
    word: str,
    mode: str,
    scope: str,
    max_results: int
) -> list[SearchResult]:
```

Dispatch table:
| Mode | Method | Parameters |
|------|--------|-----------|
| `'exact'` | `search.search_word()` | `level='consonantal'` |
| `'variations'` | `search.search_word_with_variations()` | `level='consonantal'` |
| `'substring'` | `search.search_substring()` | `level='consonantal'` |
| `'phrase'` | `search.search_phrase()` | `level='consonantal'` |
| `'phrase_loose'` | `search.search_phrase_in_verse()` | `level='consonantal'` |

All use `use_split=True` (default) for maqqef awareness.

For 'exact', 'variations', 'substring': pass `limit=None` to get all results (we handle limiting/sampling ourselves to allow random/AI selection from the full set).

### 6. Lexicon Lookup (`execute_lexicon`)

```python
def execute_lexicon(word: str) -> list[LexiconEntry]:
```

- Uses `BDBLibrarian.fetch_entry(word, lexicon="scholarly")`
- Returns BDB + Klein entries
- If user entered with diacritics, try original first (better lexicon match), fall back to consonantal
- Handle Sefaria API errors gracefully (network issues, word not found)

**Display format:**
```
── BDB Dictionary ──
Headword: שָׁמַר (Strong's 8104)
Morphology: v.
Definition: to keep, watch, preserve...

── Klein Dictionary ──
Headword: שָׁמַר
Etymology: Aram. שְׁמַר, Syr. ...
Definition: to watch, guard, keep...
Derivatives: שֹׁמֵר, מִשְׁמָר, ...
```

### 7. AI Curation (`ai_curate_results`)

```python
def ai_curate_results(
    word: str,
    results: list[SearchResult],
    max_select: int
) -> list[tuple[SearchResult, str]]:
    """Returns list of (result, reason_selected) tuples."""
```

- Uses **Haiku 4.5** (`claude-haiku-4-5-20251001`) for cost efficiency
- Sends Claude a list of all matches (reference + Hebrew + English, truncated if >100)
- Prompt instructs Claude to select `max_select` examples that best illustrate the word's semantic range
- Claude returns JSON: `[{"reference": "Psalms 23:1", "reason": "..."}]`
- Match Claude's selections back to SearchResult objects
- Display results with commentary alongside each

**Prompt template:**
```
You are a Hebrew lexicography assistant. Given the Hebrew word "{word}"
and the following concordance results, select {max_select} examples that
best illustrate the word's semantic range — choose verses that show
distinctly different usages, contexts, or nuances of meaning.

For each selection, provide a brief reason (1 sentence) explaining
what this usage illustrates about the word's meaning.

Return JSON array: [{"reference": "...", "reason": "..."}]

Results:
{formatted_results}
```

### 8. AI Commentary (`ai_commentary`)

```python
def ai_commentary(word: str, results: list[SearchResult], scope: str) -> str:
    """Returns markdown commentary on the word's usage patterns."""
```

- Uses **Haiku 4.5**
- Summarizes semantic range observed in the results
- Notes distribution patterns (which books, genres, contexts)
- Identifies interesting linguistic patterns
- Returns markdown text displayed in terminal and included in exports

**Prompt template:**
```
You are a Hebrew lexicography assistant. Analyze the following concordance
results for the Hebrew word "{word}" (searched in {scope}).

Total matches: {len(results)}
{formatted_sample}

Provide a concise analysis (3-5 paragraphs) covering:
1. The word's semantic range as evidenced by these results
2. Distribution patterns across books/genres
3. Notable collocations or recurring phrases
4. Any interesting observations about usage

Write in a scholarly but accessible tone.
```

### 9. Display (`display_results`)

```python
def display_results(results: list[SearchResult], curated: bool = False):
```

Format per result:
```
[1] Psalms 23:1
    יְהוָ֥ה רֹ֝עִ֗י לֹ֣א אֶחְסָֽר
    The LORD is my shepherd; I shall not want.
    Matched: רֹ֝עִ֗י (position 2)
    [AI: Selected because this shows the word in a metaphorical pastoral context]
```

Summary line:
```
Found 47 matches for שמר in Psalms (showing 10)
```

### 10. Export (`export_to_markdown`)

```python
def export_to_markdown(
    word: str,
    results: list[SearchResult],
    scope: str,
    mode: str,
    lexicon_entries: list[LexiconEntry] | None,
    commentary: str | None
) -> str:
    """Writes .md file, returns file path."""
```

Output file: `output/concordance/search_{word}_{timestamp}.md`

Format:
```markdown
# Concordance Search: שמר

**Date:** 2026-03-07
**Scope:** Psalms
**Mode:** With variations
**Total matches:** 47 (showing 10)

## Lexicon Entries

### BDB Dictionary
...

### Klein Dictionary
...

## Results

### 1. Psalms 23:1
**Hebrew:** יְהוָ֥ה רֹ֝עִ֗י לֹ֣א אֶחְסָֽר
**English:** The LORD is my shepherd; I shall not want.
**Matched word:** רֹ֝עִ֗י (position 2)

...

## AI Commentary
(if generated)
```

---

## Dependencies (All Existing)

| Component | Import Path | Purpose |
|-----------|-------------|---------|
| `ConcordanceSearch` | `src.concordance.search` | All search methods |
| `SearchResult` | `src.concordance.search` | Result dataclass |
| `normalize_for_search` | `src.concordance.hebrew_text_processor` | Diacritics normalization |
| `is_hebrew_text` | `src.concordance.hebrew_text_processor` | Input validation |
| `TanakhDatabase` | `src.data_sources.tanakh_database` | DB connection |
| `TANAKH_BOOKS` | `src.data_sources.tanakh_database` | Book list for menus |
| `BDBLibrarian` | `src.agents.bdb_librarian` | Lexicon lookups |
| `LexiconEntry` | `src.agents.bdb_librarian` | Lexicon result dataclass |
| `anthropic` | `anthropic` | AI features (Haiku 4.5) |
| `random` | stdlib | Random sampling |
| `json` | stdlib | AI response parsing |
| `textwrap` | stdlib | Terminal formatting |
| `datetime` | stdlib | Export timestamps |

---

## Implementation Order

### Step 1: Core Loop & Input (~30 min)
- `main()` loop with quit handling
- `get_hebrew_input()` with diacritics normalization
- `select_action()` menu (concordance / lexicon / both)
- Basic terminal formatting helpers

### Step 2: Search Menus & Execution (~30 min)
- `select_scope()` with book picker sub-menu
- `select_match_mode()` with phrase detection
- `select_result_options()`
- `execute_search()` dispatch
- `display_results()` formatting

### Step 3: Lexicon Integration (~15 min)
- `execute_lexicon()` via BDBLibrarian
- `display_lexicon()` formatting
- Error handling for API failures

### Step 4: AI Features (~30 min)
- `ai_curate_results()` with Haiku 4.5
- `ai_commentary()` with Haiku 4.5
- JSON response parsing with error recovery
- Integrate into result display

### Step 5: Export & Polish (~15 min)
- `export_to_markdown()`
- Create `output/concordance/` directory
- `post_results_menu()` with all options
- Edge cases: empty results, single result, very large result sets

---

## Edge Cases to Handle

1. **No results found** — Display message, offer to broaden scope or switch to substring mode
2. **Very large result sets** (>500) — Warn user, suggest narrowing scope
3. **Lexicon not found** — Sefaria API may not have entry; display graceful message
4. **Network errors** — Lexicon lookup and AI features require network; degrade gracefully
5. **Mixed input** — User enters mix of Hebrew and English; strip non-Hebrew, warn
6. **Maqqef-connected input** — User types "כי־טוב"; normalize handles via `split_on_maqqef`
7. **AI JSON parse failure** — If Claude returns malformed JSON, fall back to canonical ordering
8. **Single-character input** — Warn that results will be very broad

---

## No Changes to Existing Code

This tool is purely additive:
- **No modifications** to `src/concordance/search.py`
- **No modifications** to `src/agents/bdb_librarian.py`
- **No modifications** to `src/data_sources/tanakh_database.py`
- **No new database tables or schema changes**
- **One new file:** `scripts/concordance_tool.py`
- **One new directory:** `output/concordance/` (created on first export)
