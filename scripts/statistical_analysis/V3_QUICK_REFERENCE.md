# V3 Quick Reference Card

## What's New in V3

### Three Critical Fixes
1. **Paragraph markers** (`{פ}`, `{ס}`) removed from analysis
2. **Root-based extraction** for both skipgrams AND contiguous phrases
3. **Full text spans** captured in skipgrams (matched words + gaps)

## Files Created/Updated

### New Files
| File | Purpose |
|------|---------|
| `text_cleaning.py` | Remove paragraph markers |
| `migrate_skipgrams_v3.py` | Database migration script |
| `test_v3_fixes.py` | Comprehensive test suite |
| `V3_MIGRATION_GUIDE.md` | Detailed migration guide |
| `V3_IMPLEMENTATION_SUMMARY.md` | Implementation details |
| `V3_QUICK_REFERENCE.md` | This file |

### Updated Files
| File | Changes |
|------|---------|
| `root_extractor.py` | + Text cleaning integration |
| `skipgram_extractor.py` | + Root extraction, full spans |
| `add_skipgrams_to_db.py` | + V3 schema support |

## Common Tasks

### Run All Tests
```bash
cd scripts/statistical_analysis
python3 test_v3_fixes.py
```

### Migrate Database
```bash
cd scripts/statistical_analysis
python3 migrate_skipgrams_v3.py
```

### Test Individual Components
```bash
# Text cleaning
python3 text_cleaning.py

# Root extraction
python3 root_extractor.py

# Skipgram extraction
python3 skipgram_extractor.py
```

## API Changes

### Skipgram Return Format

**V2 (Old):**
```python
skipgrams[2] = {
    ('מזמור', 'לאסף'),  # Just consonantal forms
    ...
}
```

**V3 (New):**
```python
skipgrams[2] = {
    ('זמור אסף',              # roots (space-separated)
     'מִזְמ֗וֹר לְאָ֫סָ֥ף',    # matched Hebrew
     'מִזְמ֗וֹר לְאָ֫סָ֥ף'),   # full span Hebrew
    ...
}

# Usage:
for pattern in skipgrams[2]:
    roots, matched, full_span = pattern
```

### Database Schema

**V2 Columns:**
- `pattern_consonantal` - Consonantal forms

**V3 Columns:**
- `pattern_roots` - Root forms (replaces pattern_consonantal)
- `pattern_hebrew` - Matched words only
- `full_span_hebrew` - Complete text span

**Query Example:**
```sql
-- V3 query
SELECT pattern_roots, pattern_hebrew, full_span_hebrew
FROM psalm_skipgrams
WHERE psalm_number = 50 AND pattern_length = 3
LIMIT 5;
```

## Text Cleaning Functions

```python
from text_cleaning import (
    clean_hebrew_text,
    clean_word_list,
    is_paragraph_marker
)

# Clean text
text = "אַשְׁרֵי הָאִישׁ {פ}"
cleaned = clean_hebrew_text(text)
# → "אַשְׁרֵי הָאִישׁ"

# Clean word list
words = ['word1', '{פ}', 'word2', '׀']
cleaned = clean_word_list(words)
# → ['word1', 'word2']

# Check marker
is_paragraph_marker('{פ}')  # → True
is_paragraph_marker('אלהים')  # → False
```

## Verification Checklist

After migration, verify:

- [ ] All tests pass (`python3 test_v3_fixes.py`)
- [ ] No paragraph markers in data
- [ ] Skipgrams use roots (not consonantal)
- [ ] Full spans captured correctly
- [ ] Deduplication works (Psalm 50 example)
- [ ] Database has ~1.9M skipgrams
- [ ] All 150 Psalms represented

## Common Issues

### "No such table: psalm_skipgrams"
**Solution:** Run migration script to create V3 schema

### "Migration takes too long"
**Normal:** ~5-10 minutes for 150 Psalms

### "Tests fail after migration"
**Solution:** Re-run migration, check database paths

## Statistics

### Database Size
- Total skipgrams: ~1,900,000
- 2-word: ~95,000 (5%)
- 3-word: ~350,000 (18%)
- 4-word: ~1,455,000 (77%)

### Impact
- Paragraph markers removed: 165 instances
- Methodology: Now consistent (all roots)
- Deduplication: Now possible (same forms)

## Example: Before/After

### Psalm 50:1 - "מזמור לאסף אל אלהים"

**V2:**
```
Skipgram (consonantal): "מזמור לאסף אל"
Contiguous (roots):     "זמור אסף"
Match: ✗ NO (different forms)
```

**V3:**
```
Skipgram (roots):      "זמור אסף אל"
Contiguous (roots):    "זמור אסף"
Match: ✓ YES (same forms, can deduplicate)
```

## Quick Test

```bash
# Verify everything works
cd scripts/statistical_analysis

# Should show all tests passing
python3 test_v3_fixes.py 2>&1 | grep "PASSED"

# Expected output:
#   Paragraph Markers Removed: ✓ PASSED
#   Root Extraction: ✓ PASSED
#   Skipgrams Use Roots: ✓ PASSED
#   Full Span Capture: ✓ PASSED
#   Deduplication Example: ✓ PASSED
#   ✓ ALL TESTS PASSED - V3 FIXES VERIFIED!
```

## Migration Rollback

If needed:
```sql
DROP TABLE psalm_skipgrams;
ALTER TABLE psalm_skipgrams_v2_backup RENAME TO psalm_skipgrams;
CREATE INDEX idx_skipgram_lookup ON psalm_skipgrams(pattern_consonantal, pattern_length);
```

## Documentation

- **Full Guide:** `V3_MIGRATION_GUIDE.md`
- **Implementation Details:** `V3_IMPLEMENTATION_SUMMARY.md`
- **This Reference:** `V3_QUICK_REFERENCE.md`

---

**Status:** ✓ Ready for Production  
**Tests:** 5/5 Passing  
**Updated:** 2025-11-14
