# V3 Migration Guide: Text Cleaning and Root-Based Skipgrams

## Overview

V3 fixes three critical issues in the Psalm similarity analysis system:

1. **Paragraph markers** like `{פ}` and `{ס}` were being counted as words
2. **Skipgrams used consonantal forms** while contiguous phrases used roots (preventing proper deduplication)
3. **Full Hebrew text missing** from skipgrams (only showed matched words, not gap words)

## What Changed

### 1. Text Cleaning (`text_cleaning.py`)

**NEW FILE**: Utility to remove paragraph markers and non-word elements.

```python
from text_cleaning import clean_hebrew_text, clean_word_list

# Clean text before processing
cleaned = clean_hebrew_text("אַשְׁרֵי הָאִישׁ {פ}")  # → "אַשְׁרֵי הָאִישׁ"

# Clean word lists
words = ['אַשְׁרֵי', 'הָאִישׁ', '{פ}', 'כִּי']
cleaned = clean_word_list(words)  # → ['אַשְׁרֵי', 'הָאִישׁ', 'כִּי']
```

**What it removes:**
- `{פ}` (Petucha - open paragraph marker)
- `{ס}` (Setuma - closed paragraph marker)
- `׀` (Paseq - separating mark)
- Any other bracket-enclosed Hebrew markers

### 2. Root Extractor (`root_extractor.py`)

**UPDATED**: Now uses text cleaning before root extraction.

**Changes:**
- Calls `clean_hebrew_text()` before splitting words
- Calls `clean_word_list()` after splitting to remove any remaining markers
- Ensures `{פ}` never becomes a "word" in analysis

**Impact:** 165 paragraph markers in Psalms database are now filtered out.

### 3. Skipgram Extractor (`skipgram_extractor.py`)

**UPDATED**: Major changes to methodology and data structure.

**Changes:**
- **Uses ROOT extraction** instead of consonantal forms (consistent with contiguous phrases)
- **Captures full Hebrew text span** including gap words between matched words
- Returns 3-tuple instead of tuple: `(pattern_roots, pattern_hebrew, full_span_hebrew)`

**Example:**

```python
# Old V2 (consonantal):
('מזמור', 'לאסף', 'אל')  # Just consonantal forms

# New V3 (root-based with full spans):
(
    'זמור אסף אל',                    # roots (stripped prefixes/suffixes)
    'מִזְמ֗וֹר לְאָ֫סָ֥ף אֵ֤ל',        # matched words only
    'מִזְמ֗וֹר לְאָ֫סָ֥ף אֵ֤ל אֱֽלֹהִ֡ים'  # full span (includes gap words)
)
```

### 4. Database Schema (`psalm_skipgrams` table)

**UPDATED**: New columns to support full span storage.

**Old V2 Schema:**
```sql
CREATE TABLE psalm_skipgrams (
    skipgram_id INTEGER PRIMARY KEY,
    psalm_number INTEGER,
    pattern_consonantal TEXT,  -- consonantal forms
    pattern_length INTEGER,
    occurrence_count INTEGER
)
```

**New V3 Schema:**
```sql
CREATE TABLE psalm_skipgrams (
    skipgram_id INTEGER PRIMARY KEY,
    psalm_number INTEGER,
    pattern_roots TEXT,          -- NEW: root forms (not consonantal)
    pattern_hebrew TEXT,         -- NEW: matched words only
    full_span_hebrew TEXT,       -- NEW: complete text span
    pattern_length INTEGER,
    occurrence_count INTEGER,
    created_at TIMESTAMP
)
```

## Migration Process

### Step 1: Backup Existing Data

The migration script automatically backs up your existing `psalm_skipgrams` table to `psalm_skipgrams_v2_backup`.

### Step 2: Run Migration

```bash
cd scripts/statistical_analysis
python3 migrate_skipgrams_v3.py
```

**What it does:**
1. Backs up existing data to `psalm_skipgrams_v2_backup`
2. Drops old `psalm_skipgrams` table
3. Creates new V3 schema
4. Re-extracts all skipgrams for 150 Psalms using root-based methodology
5. Verifies data integrity

**Time estimate:** 5-10 minutes for all 150 Psalms (~1.9M skipgrams)

### Step 3: Verify Results

The migration script automatically verifies:
- Total skipgram count
- Distribution by length (2-word, 3-word, 4-word)
- No paragraph markers in data
- All 150 Psalms represented

## Testing

Run comprehensive tests to verify all fixes:

```bash
cd scripts/statistical_analysis
python3 test_v3_fixes.py
```

**Tests:**
1. Paragraph markers removed from word lists
2. Root extraction works correctly
3. Skipgrams use roots (not consonantal)
4. Full Hebrew spans captured correctly
5. Deduplication example (Psalm 50 "מזמור לאסף")

## Impact on Deduplication

### The Problem

**Before V3:**
- Contiguous phrase: `"זמור אסף"` (roots: מזמור → זמור, לאסף → אסף)
- Skipgram: `"מזמור לאסף"` (consonantal: מזמור, לאסף)
- **No match** because different forms used!

**After V3:**
- Contiguous phrase: `"זמור אסף"` (roots)
- Skipgram: `"זמור אסף"` (roots)  
- **✓ Match!** Proper deduplication

### Example: Rank 500 Issue

From top 500 phrases analysis, Psalms 50-82 (Asaph collection):

**Pattern:** "מזמור לאסף אל אלהים"

**V2 behavior:**
- Skipgram: `"מזמור לאסף אל אלהים"` (consonantal)
- Contiguous: `"זמור אסף"` (roots)
- ✗ No deduplication (counted both)

**V3 behavior:**
- Skipgram: `"זמור אסף אל אלה"` (roots)
- Contiguous: `"זמור אסף"` (roots)
- ✓ Deduplication works (same root forms)

## API Changes

### SkipgramExtractor

**Old V2:**
```python
extractor = SkipgramExtractor()
skipgrams = extractor.extract_all_skipgrams(50)
# Returns: Dict[int, Set[Tuple[str, ...]]]
# Example: {2: {('מזמור', 'לאסף'), ...}}
```

**New V3:**
```python
extractor = SkipgramExtractor()
skipgrams = extractor.extract_all_skipgrams(50)
# Returns: Dict[int, Set[Tuple[str, str, str]]]
# Example: {2: {('זמור אסף', 'מִזְמ֗וֹר לְאָ֫סָ֥ף', 'מִזְמ֗וֹר לְאָ֫סָ֥ף'), ...}}

# Unpack tuples:
for pattern in skipgrams[2]:
    roots, matched_hebrew, full_span_hebrew = pattern
    print(f"Roots: {roots}")
    print(f"Matched: {matched_hebrew}")
    print(f"Full span: {full_span_hebrew}")
```

### Database Queries

**Old V2:**
```sql
SELECT pattern_consonantal
FROM psalm_skipgrams
WHERE psalm_number = 50
```

**New V3:**
```sql
SELECT pattern_roots, pattern_hebrew, full_span_hebrew
FROM psalm_skipgrams
WHERE psalm_number = 50
```

## Rollback Procedure

If you need to rollback to V2:

```sql
-- Drop V3 table
DROP TABLE psalm_skipgrams;

-- Restore from backup
ALTER TABLE psalm_skipgrams_v2_backup RENAME TO psalm_skipgrams;

-- Recreate V2 indexes
CREATE INDEX idx_skipgram_lookup 
ON psalm_skipgrams(pattern_consonantal, pattern_length);
```

## Statistics

### Database Impact

**Before V3:**
- Total skipgrams: ~1.9M
- Includes 165 paragraph markers as "words"
- Mixed methodologies (consonantal vs. roots)

**After V3:**
- Total skipgrams: ~1.9M (similar count, but different content)
- Zero paragraph markers
- Consistent root-based methodology
- Additional full span data for each skipgram

### Performance

- Migration time: ~5-10 minutes
- Database size: Similar (slight increase due to full_span_hebrew)
- Query performance: Similar (same indexes)

## Next Steps

After V3 migration:

1. **Run deduplication analysis** with consistent root forms
2. **Coordinate with Agent 1** for enhanced morphological analysis
3. **Rebuild similarity scores** with deduplicated data
4. **Update documentation** for any downstream tools

## Troubleshooting

### "No such table: psalm_skipgrams"

This is expected on fresh install. Run migration to create V3 schema.

### "Migration failed"

Check:
1. Database file exists: `data/psalm_relationships.db`
2. Tanakh database exists: `database/tanakh.db`
3. Python dependencies installed
4. Disk space available

### "Paragraph markers still found"

Re-run migration. The V3 system actively filters markers during extraction.

## Files Modified/Created

### New Files
- `scripts/statistical_analysis/text_cleaning.py` - Text cleaning utilities
- `scripts/statistical_analysis/migrate_skipgrams_v3.py` - Migration script
- `scripts/statistical_analysis/test_v3_fixes.py` - Test suite
- `scripts/statistical_analysis/V3_MIGRATION_GUIDE.md` - This guide

### Updated Files
- `scripts/statistical_analysis/root_extractor.py` - Integrated text cleaning
- `scripts/statistical_analysis/skipgram_extractor.py` - Root-based extraction + full spans
- `scripts/statistical_analysis/add_skipgrams_to_db.py` - V3 schema support

## Support

Questions or issues? See:
- Test suite: `test_v3_fixes.py`
- Migration script: `migrate_skipgrams_v3.py`
- Text cleaning tests: `python3 text_cleaning.py`
