# Skipgram gap_word_count=0 Issue - Fix Implementation Guide

## Issue Summary
38.29% of "skipgrams" have gap_word_count=0, meaning they are contiguous patterns with NO GAPS. This violates the definition of skipgrams, which should have gaps between matched words.

- Current: 5,285 contiguous patterns incorrectly stored as skipgrams
- Target: Remove all gap_word_count=0 patterns from skipgram extraction

---

## File 1: skipgram_extractor_v4.py

### Location & Current Code
File: /home/user/psalms-AI-analysis/scripts/statistical_analysis/skipgram_extractor_v4.py
Method: extract_skipgrams_with_verse() (lines 229-320)
Problematic Section: Lines 293-320

### The Fix

**Location: Line 297-298 in extract_skipgrams_with_verse()**

**Current Code (BROKEN):**
```
296:    gap_word_count = (last_idx - first_idx + 1) - n
297:
298:    # V5: Check quality filters before adding
299:    should_keep, reason = self._should_keep_pattern(pattern_roots, gap_word_count)
300:
301:    if should_keep:
302:        # Store skipgram...
```

**Fixed Code:**
```
296:    gap_word_count = (last_idx - first_idx + 1) - n
297:
298:    # CRITICAL FIX: Skip contiguous patterns (gap_word_count=0)
299:    # Skip-grams BY DEFINITION must have gaps between matched words.
300:    # Patterns with no gaps should be handled by contiguous phrase extractor.
301:    if gap_word_count == 0:
302:        continue  # Skip this pattern entirely
303:
304:    # V5: Check quality filters before adding
305:    should_keep, reason = self._should_keep_pattern(pattern_roots, gap_word_count)
306:
307:    if should_keep:
308:        # Store skipgram...
```

### Key Change
Add these 5 lines after calculating gap_word_count:

    if gap_word_count == 0:
        continue

This prevents patterns with NO gaps (contiguous phrases) from being treated as skipgrams.

---

## File 2: Update Statistics in __init__

**Location:** lines 84-89

**Current:**
    self.stats = {
        'total_extracted': 0,
        'filtered_by_content': 0,
        'filtered_by_stoplist': 0,
        'kept': 0
    }

**Fixed:**
    self.stats = {
        'total_extracted': 0,
        'filtered_by_gap_requirement': 0,  # NEW: Track contiguous patterns skipped
        'filtered_by_content': 0,
        'filtered_by_stoplist': 0,
        'kept': 0
    }

---

## File 3: Update Statistics Reporting

**File:** migrate_skipgrams_v4.py
**Lines:** 210-216

**Add this line after total_extracted:**
    logger.info(f"  Filtered by gap requirement (contiguous): {extractor.stats.get('filtered_by_gap_requirement', 0):,}")

---

## Testing & Verification

### Before Running Migration
1. Backup current database:
   cp /home/user/psalms-AI-analysis/data/psalm_relationships.db \
      /home/user/psalms-AI-analysis/data/psalm_relationships.db.backup

### After Code Changes
1. Run migration:
   cd /home/user/psalms-AI-analysis/scripts/statistical_analysis
   python3 migrate_skipgrams_v4.py

2. Expected output should show something like:
   Filtered by gap requirement (contiguous): 280000+ patterns

3. Verify the database:
   python3 << 'EOF'
   import sqlite3
   db = sqlite3.connect('/home/user/psalms-AI-analysis/data/psalm_relationships.db')
   c = db.cursor()
   c.execute("SELECT COUNT(*) FROM psalm_skipgrams WHERE gap_word_count = 0")
   gap_zero = c.fetchone()[0]
   if gap_zero == 0:
       print("SUCCESS: No contiguous patterns in skipgrams!")
   else:
       print(f"FAILURE: Still {gap_zero} contiguous patterns")
   db.close()
   EOF

---

## Expected Impact

### Skipgram Count Changes
Before: 13,804 total skipgrams
After: 8,519 total skipgrams
Removed: 5,285 contiguous patterns (38.29%)

### Distribution After Fix
gap=1: 3,349 patterns
gap=2: 2,786 patterns  
gap=3: 2,230 patterns
gap=4+: 154 patterns
Total: 8,519 (only true skipgrams)

### Quality Improvements
- Skipgrams collection now contains ONLY patterns with gaps
- Contiguous patterns clearly separated
- Scoring more accurate
- Terminology consistent with linguistic definition

---

## Rollback Plan

If needed:
    cp /home/user/psalms-AI-analysis/data/psalm_relationships.db.backup \
       /home/user/psalms-AI-analysis/data/psalm_relationships.db
    git checkout skipgram_extractor_v4.py
    python3 migrate_skipgrams_v4.py

---

## Files to Modify

1. skipgram_extractor_v4.py
   - Add gap_word_count check (lines 298-302)
   - Update statistics (lines 84-89)

2. migrate_skipgrams_v4.py  
   - Add statistics reporting for gap filtering

---

## References

Analysis Document: /home/user/psalms-AI-analysis/docs/SKIPGRAM_GAP_ISSUE_ANALYSIS.md
Root Cause: Combinatorial extraction includes contiguous patterns
Fix Type: Early filtering (skip generation of gap=0 patterns)
Risk: Low (only removes incorrect patterns)
