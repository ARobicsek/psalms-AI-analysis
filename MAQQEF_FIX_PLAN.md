# Maqqef Fix Implementation Plan

## Problem Confirmed

**Baseline Test Results**: ALL 14 test queries returned 0 results
- Even single-word queries failed (שני, שברת, הכית all returned 0)
- System is essentially non-functional for phrase searching
- Root cause: Maqqef combining makes words unsearchable

## Solution: Add Split Column + Migrate

### Step 1: Add New Column to Database

Add `word_consonantal_split` column to concordance table:

```python
# In tanakh_database.py, add migration method:
def add_split_concordance_column(self):
    """Add word_consonantal_split column for maqqef-split searching."""
    cursor = self.conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(concordance)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'word_consonantal_split' not in columns:
        logger.info("Adding word_consonantal_split column...")
        cursor.execute("""
            ALTER TABLE concordance
            ADD COLUMN word_consonantal_split TEXT
        """)
        self.conn.commit()
        logger.info("Column added successfully")
        return True
    else:
        logger.info("Column word_consonantal_split already exists")
        return False
```

### Step 2: Create Split Function in hebrew_text_processor.py

```python
def split_on_maqqef(text: str) -> str:
    """
    Replace maqqef (־) with space for searchability.

    This allows maqqef-connected morphemes to be found as individual words.

    Args:
        text: Hebrew text potentially containing maqqef

    Returns:
        Text with maqqef replaced by spaces

    Example:
        >>> split_on_maqqef("כִּֽי־הִכִּ֣יתָ")
        'כִּֽי הִכִּ֣יתָ'
    """
    return text.replace('\u05BE', ' ')

def normalize_for_search_split(text: str, level: str = 'consonantal') -> str:
    """
    Normalize for search with maqqef splitting.

    Args:
        text: Hebrew text to normalize
        level: Normalization level

    Returns:
        Normalized text with maqqefs replaced by spaces
    """
    # First split on maqqef
    text = split_on_maqqef(text)
    # Then normalize normally
    return normalize_for_search(text, level)
```

### Step 3: Populate New Column

```python
def populate_split_concordance(self):
    """Populate word_consonantal_split column with maqqef-split versions."""
    from ..concordance.hebrew_text_processor import normalize_for_search_split

    cursor = self.conn.cursor()

    # Get all concordance entries
    cursor.execute("SELECT concordance_id, word FROM concordance")
    entries = cursor.fetchall()

    logger.info(f"Populating word_consonantal_split for {len(entries)} entries...")

    batch_size = 1000
    for i in range(0, len(entries), batch_size):
        batch = entries[i:i+batch_size]

        for entry in batch:
            conc_id = entry['concordance_id']
            word = entry['word']

            # Normalize with maqqef splitting
            split_consonantal = normalize_for_search_split(word, 'consonantal')

            cursor.execute("""
                UPDATE concordance
                SET word_consonantal_split = ?
                WHERE concordance_id = ?
            """, (split_consonantal, conc_id))

        self.conn.commit()

        if (i + batch_size) % 10000 == 0:
            logger.info(f"Progress: {i + batch_size}/{len(entries)}")

    logger.info("Split concordance population complete!")
```

### Step 4: Update Concordance Search

In `src/concordance/search.py`, modify `search_word()` and `search_phrase()`:

```python
def search_word(self,
                word: str,
                level: str = 'consonantal',
                scope: str = 'Tanakh',
                limit: Optional[int] = None,
                use_split: bool = True) -> List[SearchResult]:
    """Search for a Hebrew word."""

    # ... existing code ...

    # Determine column based on use_split flag
    if use_split and level == 'consonantal':
        # Use split column for better phrase matching
        column = 'word_consonantal_split'
    elif level == 'exact':
        column = 'word'
    elif level == 'voweled':
        column = 'word_voweled'
    else:  # consonantal without split
        column = 'word_consonantal'

    # Rest of method unchanged...
```

### Step 5: Update Concordance Librarian

In `src/agents/concordance_librarian.py`:

```python
def search_with_variations(self, request: ConcordanceRequest) -> ConcordanceBundle:
    """Search concordance with automatic variations."""

    # ... existing code ...

    # Use split column for phrase searches
    results = self.search.search_phrase(
        request.query,
        level=request.level,
        scope=final_scope,
        limit=request.max_results,
        use_split=True  # NEW: use split column
    )

    # ... rest unchanged ...
```

##Step 6: Run Migration

```python
# Script: scripts/migrate_add_split_concordance.py
from src.data_sources.tanakh_database import TanakhDatabase

db = TanakhDatabase()

# Add column
db.add_split_concordance_column()

# Populate it
db.populate_split_concordance()

print("Migration complete!")
```

### Step 7: Re-run Baseline Test

After migration, run the baseline test again:

```bash
python test_concordance_baseline.py > output/debug/baseline_after_split.txt 2>&1
```

Compare `concordance_baseline_results.json` with new results.

## Expected Improvements

### Query: "הכית את"
- **Before**: 2 results (only where words appear without maqqef)
- **After**: Should find Psalm 3:8 where it's stored as:
  - Word 5: כי
  - Word 6: הכית ← NOW SEARCHABLE
  - Word 7: את ← NOW SEARCHABLE

### Query: "שבר שן"
- **Before**: 0 results (words not adjacent due to רשעים in between)
- **After**: Still 0 (words still not adjacent), but...
- Individual words now searchable: "שברת" and "שני" will each return results

### Single Word Queries
- **Before**: 0 results for all
- **After**: Should return results (e.g., "שני" should find construct forms)

## Testing Strategy

1. Save baseline results (done)
2. Implement migration
3. Run migration script
4. Re-run baseline test
5. Compare results:
   - Total matches should INCREASE or stay same (never decrease)
   - Single-word queries should now work
   - Phrase queries should improve significantly

## Files to Modify

1. `src/concordance/hebrew_text_processor.py` - Add split functions
2. `src/data_sources/tanakh_database.py` - Add migration methods
3. `src/concordance/search.py` - Update to use split column
4. `src/agents/concordance_librarian.py` - Pass use_split flag
5. `scripts/migrate_add_split_concordance.py` - NEW migration script

## Rollback Plan

If results are worse:
1. Keep both columns
2. Add `use_split` flag to ConcordanceRequest
3. Allow users to toggle between old and new behavior
4. Default to new (split) behavior

## Next Session

Continue from Step 1 above. The analysis and planning is complete - implementation is straightforward.
