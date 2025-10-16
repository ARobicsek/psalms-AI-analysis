# Day 3 Implementation Plan

## Overview
Expand concordance scope to entire Tanakh and build Hebrew text processing system with phrase search support.

## Tasks

### 1. Full Tanakh Download (~23,000 verses)
**Extend Sefaria Client:**
- Add `fetch_book()` method to sefaria_client.py
- Support all Tanakh books (Torah, Prophets, Writings)
- Handle variable chapter/verse structures

**Extend Database:**
- Add `download_tanakh()` method to tanakh_database.py
- Store all books in existing schema
- Track download progress with logging

**Books to Download:**
```
Torah (5 books):
- Genesis, Exodus, Leviticus, Numbers, Deuteronomy

Prophets (8 books):
- Joshua, Judges, Samuel I & II, Kings I & II, Isaiah, Jeremiah, Ezekiel
- The Twelve: Hosea, Joel, Amos, Obadiah, Jonah, Micah, Nahum, Habakkuk,
  Zephaniah, Haggai, Zechariah, Malachi

Writings (11 books):
- Psalms (already have), Proverbs, Job
- Song of Songs, Ruth, Lamentations, Ecclesiastes, Esther
- Daniel, Ezra, Nehemiah, Chronicles I & II
```

**Estimated time:** 5-7 minutes download (rate-limited)

### 2. Hebrew Text Processing Utilities
**Create:** `src/concordance/hebrew_text_processor.py`

**Core Functions:**
```python
def strip_cantillation(text: str) -> str:
    """Remove cantillation marks (U+0591-U+05C7)"""

def strip_vowels(text: str) -> str:
    """Remove vowels/niqqud (U+05B0-U+05BC)"""

def strip_consonantal(text: str) -> str:
    """Strip both cantillation AND vowels, keep consonants only"""

def normalize_for_search(text: str, level: str) -> str:
    """
    Normalize Hebrew text at specified level.

    Args:
        text: Hebrew text to normalize
        level: 'exact' | 'voweled' | 'consonantal' | 'lemma'

    Returns:
        Normalized text ready for search/comparison
    """
```

**Unicode Ranges to Handle:**
- Hebrew letters: U+05D0 to U+05EA
- Vowels (niqqud): U+05B0 to U+05BC
- Cantillation (te'amim): U+0591 to U+05C7
- Maqqef (hyphen): U+05BE
- Geresh/Gershayim: U+05F3, U+05F4

### 3. Concordance Database Schema
**Create:** Table for concordance indices

```sql
CREATE TABLE concordance (
    concordance_id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,           -- Original word with all diacritics
    word_consonantal TEXT,         -- Consonants only
    word_voweled TEXT,             -- Consonants + vowels (no cantillation)
    book_name TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    position INTEGER NOT NULL,     -- Word position in verse (0-indexed)

    FOREIGN KEY (book_name, chapter, verse)
        REFERENCES verses(book_name, chapter, verse)
);

-- Indices for fast search
CREATE INDEX idx_concordance_consonantal ON concordance(word_consonantal);
CREATE INDEX idx_concordance_voweled ON concordance(word_voweled);
CREATE INDEX idx_concordance_exact ON concordance(word);
CREATE INDEX idx_concordance_reference ON concordance(book_name, chapter, verse);
```

### 4. Phrase Search Support
**Add to concordance system:**

```python
def search_phrase(phrase: str, level: str = 'consonantal') -> List[Dict]:
    """
    Search for multi-word Hebrew phrases.

    Args:
        phrase: Hebrew phrase (space-separated words)
        level: Normalization level for matching

    Returns:
        List of matches with context

    Example:
        search_phrase("יְהוָה רֹעִי", level='consonantal')
        # Finds "The LORD is my shepherd" in Psalm 23:1
    """
```

**Implementation approach:**
1. Split phrase into words
2. Normalize each word at specified level
3. Search for sequential word matches in concordance
4. Return verses containing the complete phrase

### 5. Testing
**Test cases:**
- Single word search (consonantal): שמר → all forms of "guard/keep"
- Single word search (voweled): אֵל vs אֶל (God vs to/toward)
- Phrase search: "יְהוָה רֹעִי" → Psalm 23:1
- Cross-book search: Find word across Torah vs Prophets vs Writings
- Performance: Search speed with 23k verses

## Deliverables
1. ✅ Full Tanakh downloaded (~23k verses in database)
2. ✅ `hebrew_text_processor.py` with normalization functions
3. ✅ Concordance database schema created
4. ✅ Phrase search capability working
5. ✅ Test suite demonstrating all search modes
6. ✅ Documentation updated in IMPLEMENTATION_LOG.md

## Estimated Time
- Tanakh download: 30 min (code + download)
- Hebrew processor: 1 hour
- Concordance schema: 1 hour
- Phrase search: 1 hour
- Testing: 30 min
**Total: ~4 hours**

## Notes
- Sefaria API structure may vary by book (Torah vs Writings)
- Some books use different chapter/verse notation
- Need to handle books without chapter divisions (e.g., Obadiah)
- Consider memory usage with 23k verses in concordance table
- Phrase search with consonantal matching gives VERY flexible results

## Success Criteria
- [ ] All Tanakh books downloaded successfully
- [ ] Can search for שמר and find all guard/keep instances
- [ ] Can distinguish אֵל (God) from אֶל (to/toward)
- [ ] Can find phrase "יְהוָה רֹעִי" in Psalm 23:1
- [ ] Search completes in <100ms for single word
- [ ] Phrase search completes in <500ms
- [ ] Database size reasonable (<50 MB)
