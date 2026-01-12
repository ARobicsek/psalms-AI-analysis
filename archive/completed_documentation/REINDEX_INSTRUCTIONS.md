# Re-indexing Instructions After Session 45 Fixes

## What Was Fixed

All 5 critical indexer bugs have been fixed:

1. ✓ **Empty contexts** (was 35.1% failure rate) - Now extracts contexts correctly
2. ✓ **Duplicate phrases** - Now merges to single exact_verse when appropriate
3. ✓ **Entire chapter detection** - Now accepts near-complete verses (≥80%)
4. ✓ **Phrase-to-verse upgrades** - Automatically upgrades qualifying phrases
5. ✓ **Verse ranges** - New feature: detects consecutive verse sequences (3+)

## Test Results

**Psalm 23 (tested):**
- Empty contexts: 31.3% → **0%** ✓
- Created 5 new verse_range entries
- Better deduplication (67 → 50 matches)

## Recommended Testing Before Full Re-index

### Step 1: Test on problem Psalms

Test the fixes on Psalms with highest empty context rates:

```bash
# Test Psalm 89 (50.7% empty)
python src/liturgy/liturgy_indexer.py --psalm 89

# Test Psalm 119 (largest, 399 empty contexts)
python src/liturgy/liturgy_indexer.py --psalm 119

# Test Psalm 135 (candidate for entire_chapter detection)
python src/liturgy/liturgy_indexer.py --psalm 135
```

### Step 2: Verify results

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT psalm_chapter,
           COUNT(*) as total,
           SUM(CASE WHEN liturgy_context = '' OR liturgy_context IS NULL THEN 1 ELSE 0 END) as empty,
           ROUND(100.0 * SUM(CASE WHEN liturgy_context = '' OR liturgy_context IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) as pct
    FROM psalms_liturgy_index
    WHERE psalm_chapter IN (89, 119, 135)
    GROUP BY psalm_chapter
''')

print('Psalm  Total  Empty  Empty%')
print('-' * 40)
for ps, total, empty, pct in cursor.fetchall():
    print(f'{ps:>5} {total:>6} {empty:>6} {pct:>6}%')
"
```

**Expected:** Empty % should be 0% or near 0% for all three Psalms.

### Step 3: If tests pass, run full re-index

**IMPORTANT: Backup database first!**

```bash
# Backup current database
cp data/liturgy.db data/liturgy.db.backup_before_session45_reindex

# Run full re-index (may take 30-60 minutes)
python src/liturgy/liturgy_indexer.py --all
```

Or run in batches:
```bash
# Re-index in batches of 25 Psalms
python src/liturgy/liturgy_indexer.py --range 1-25
python src/liturgy/liturgy_indexer.py --range 26-50
python src/liturgy/liturgy_indexer.py --range 51-75
python src/liturgy/liturgy_indexer.py --range 76-100
python src/liturgy/liturgy_indexer.py --range 101-125
python src/liturgy/liturgy_indexer.py --range 126-150
```

### Step 4: Verify final results

```bash
python src/liturgy/liturgy_indexer.py --stats
```

**Expected results:**
- Empty contexts: Should drop from **35.1% to near 0%**
- New match type: **verse_range** entries should appear (100-200 total)
- Total matches: May decrease 10-20% (better consolidation)
- Confidence scores: Should improve overall

## Detailed Statistics Query

To see detailed before/after comparison:

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

print('='*60)
print('FINAL INDEX STATISTICS')
print('='*60)

cursor.execute('''
    SELECT match_type,
           COUNT(*) as total,
           SUM(CASE WHEN liturgy_context = '' OR liturgy_context IS NULL THEN 1 ELSE 0 END) as empty,
           ROUND(100.0 * SUM(CASE WHEN liturgy_context = '' OR liturgy_context IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) as pct
    FROM psalms_liturgy_index
    GROUP BY match_type
''')

print()
print('Match Type       Total    Empty   Empty%')
print('-' * 50)
for mt, total, empty, pct in cursor.fetchall():
    print(f'{mt:<15} {total:>6} {empty:>6} {pct:>6}%')

cursor.execute('''
    SELECT COUNT(*),
           SUM(CASE WHEN liturgy_context = '' OR liturgy_context IS NULL THEN 1 ELSE 0 END)
    FROM psalms_liturgy_index
''')

total, empty = cursor.fetchone()
print('-' * 50)
print(f'{'TOTAL':<15} {total:>6} {empty:>6} {round(100.0*empty/total,1):>6}%')
print()
"
```

## What Changed in the Code

### Fixed Functions:
1. `_extract_context()` - Completely rewritten with position-based algorithm
2. `_extract_exact_match()` - Updated with same algorithm
3. `_deduplicate_matches()` - Added phrase-to-verse upgrade logic
4. Chapter detection - Added near-complete verse support (≥80% overlap)
5. New feature - verse_range consolidation for consecutive verses (3+)

### No Breaking Changes:
- All existing functionality preserved
- Database schema unchanged
- Backwards compatible with existing queries
- New verse_range type is additive

## Troubleshooting

### If you see empty contexts after re-indexing:

1. Check if it's a specific Psalm:
   ```bash
   python -c "
   import sqlite3
   conn = sqlite3.connect('data/liturgy.db')
   cursor = conn.cursor()
   cursor.execute('''
       SELECT psalm_chapter, COUNT(*) as empty
       FROM psalms_liturgy_index
       WHERE liturgy_context = '' OR liturgy_context IS NULL
       GROUP BY psalm_chapter
       ORDER BY empty DESC
       LIMIT 10
   ''')
   for ps, count in cursor.fetchall():
       print(f'Psalm {ps}: {count} empty contexts')
   "
   ```

2. Re-index that specific Psalm:
   ```bash
   python src/liturgy/liturgy_indexer.py --psalm [PSALM_NUMBER]
   ```

### If re-indexing is slow:

- Normal: Full re-index takes 30-60 minutes for all 150 Psalms
- Use batches (shown above) to monitor progress
- Future optimization: Aho-Corasick algorithm (10-50x speedup)

## Questions?

See `docs/SESSION_45_INDEXER_FIXES.md` for detailed technical documentation.
