# Skipgram Extraction Logic Investigation - Quick Reference

## Key Findings

### 1. WHERE SKIPGRAMS ARE EXTRACTED
**Primary File:** `/home/user/psalms-AI-analysis/scripts/statistical_analysis/skipgram_extractor_v4.py`
**Method:** `extract_skipgrams_with_verse()` (lines 229-320)

**Extraction Process:**
- Get psalm words from database
- Create sliding windows (5, 7, 10 words)
- Generate ALL n-word combinations within window
- Calculate gap_word_count for each combination
- Apply quality filters
- Store patterns with gap_word_count value

---

## 2. HOW gap_word_count IS CALCULATED

**Formula:** `gap_word_count = (last_idx - first_idx + 1) - n`

**Examples:**
```
Contiguous: word1 word2 word3 word4 (indices 0-3, n=4)
  gap = (3-0+1) - 4 = 0 ✗ Should NOT be skipgram

Skipgram: word1 [gap] word2 word3 (indices 0,2,3, n=3)
  gap = (3-0+1) - 3 = 1 ✓ True skipgram

Skipgram: word1 [gap1] word2 [gap2] word3 (indices 0,2,4, n=3)
  gap = (4-0+1) - 3 = 2 ✓ True skipgram
```

**Key Rule:** gap_word_count=0 means ALL words are CONSECUTIVE (no gaps)

---

## 3. WHERE SKIPGRAMS ARE STORED

**Database:** `/home/user/psalms-AI-analysis/data/psalm_relationships.db`
**Table:** `psalm_skipgrams`
**Schema:**
```
- skipgram_id (PRIMARY KEY)
- psalm_number
- pattern_roots (TEXT)
- pattern_hebrew (TEXT)
- full_span_hebrew (TEXT)
- pattern_length (INTEGER)
- verse (INTEGER)
- first_position (INTEGER)
- gap_word_count (INTEGER) ← THE PROBLEM FIELD
- content_word_count
- content_word_ratio
- pattern_category
```

---

## 4. THE CRITICAL ISSUE: gap_word_count=0 PATTERNS

**Problem Statement:**
38.29% of skipgrams (5,285 out of 13,804) have gap_word_count=0, making them CONTIGUOUS phrases, not true skipgrams.

**Distribution:**
```
gap=0 (Contiguous):   5,285 patterns (38.29%) ✗ INCORRECT
gap=1:                3,349 patterns (24.26%) ✓ Correct
gap=2:                2,786 patterns (20.18%) ✓ Correct
gap=3:                2,230 patterns (16.15%) ✓ Correct
gap=4+:                 154 patterns (1.12%) ✓ Correct
─────────────────────────────────────────────
TOTAL:               13,804 patterns
```

**Why It's Wrong:**
- By definition, skipgrams REQUIRE gaps between matched words
- gap_word_count=0 means no gaps exist
- These should be in a separate "contiguous_phrases" collection
- Mixing them skews the pattern statistics and analysis

**Examples of Incorrect gap=0 "Skipgrams":**
1. Pattern: `ציל יהוה עזר חוש` (4 words)
   - All 4 words consecutive (no gaps)
   - Stored as skipgram incorrectly

2. Pattern: `כל אשר חפץ עש` (4 words)
   - All 4 words consecutive (no gaps)
   - Stored as skipgram incorrectly

3. Pattern: `צור יזוב מים` (3 words)
   - All 3 words consecutive (no gaps)
   - Stored as skipgram incorrectly

---

## 5. WHY THESE PATTERNS ARE INCLUDED

**Root Cause:** The extraction algorithm uses Python's `combinations()` function to generate ALL possible n-word selections within the window, regardless of whether they're contiguous or non-contiguous.

**Example:**
```python
# For a 3-word window ["A", "B", "C"] and n=2
combinations([0,1,2], 2) produces:
  (0,1) → A B → gap=0 [Contiguous] ✗
  (0,2) → A C → gap=1 [Skipgram] ✓
  (1,2) → B C → gap=0 [Contiguous] ✗

All three are generated and stored, even the contiguous ones!
```

**Why No Filtering?**
The quality filtering in `_should_keep_pattern()` checks:
- ✓ Content word count
- ✓ Pattern stoplist
- ✗ gap_word_count requirement

The code even RECOGNIZES gap_word_count=0 patterns as "contiguous":
```python
is_contiguous = (gap_word_count == 0)  # Line 130
```
But then still stores them if they pass other filters!

---

## 6. WHAT NEEDS TO BE FIXED

**The Solution:** Add a simple check to skip patterns with gap_word_count=0

**File:** `/home/user/psalms-AI-analysis/scripts/statistical_analysis/skipgram_extractor_v4.py`
**Location:** Lines 297-302 in `extract_skipgrams_with_verse()`
**Change:** 3 lines of code

**Current Code:**
```python
gap_word_count = (last_idx - first_idx + 1) - n
# V5: Check quality filters before adding
should_keep, reason = self._should_keep_pattern(pattern_roots, gap_word_count)
```

**Fixed Code:**
```python
gap_word_count = (last_idx - first_idx + 1) - n

# CRITICAL FIX: Skip contiguous patterns (gap_word_count=0)
if gap_word_count == 0:
    continue  # Skip this pattern entirely

# V5: Check quality filters before adding
should_keep, reason = self._should_keep_pattern(pattern_roots, gap_word_count)
```

---

## 7. EXPECTED IMPACT

### Data Changes
```
Before Fix:  13,804 total skipgrams (includes 5,285 contiguous)
After Fix:    8,519 total skipgrams (only true skipgrams)
Removed:      5,285 patterns (38.29% reduction)
```

### Quality Improvements
- ✓ Skipgrams collection now definitionally correct
- ✓ Only patterns with gaps (gap>0) stored as skipgrams
- ✓ Contiguous patterns clearly separated
- ✓ Scoring more accurate (fewer false positives)

### Downstream Effects
- Psalm pair scores will be LOWER (fewer patterns counted)
- Rankings may SHIFT (expected - fixing incorrect counting)
- Gap penalty (if implemented) becomes meaningful
- Statistics more interpretable

---

## 8. FILTERING LOGIC SUMMARY

Current filtering in `_should_keep_pattern()`:
```
Pattern → Content word check → Stoplist check → Return (pass/fail)
```

Issue: NO check for gap_word_count > 0

Recommended enhancement:
```
Pattern → Gap requirement check → Content word check → Stoplist check → Return
```

The gap requirement should be:
- **For skipgrams:** gap_word_count > 0 (required)
- **For contiguous phrases:** gap_word_count = 0 (by definition)

---

## 9. IMPLEMENTATION CHECKLIST

- [ ] Add gap check in skipgram_extractor_v4.py (line 297-302)
- [ ] Update statistics tracking in __init__
- [ ] Update statistics reporting in migrate_skipgrams_v4.py
- [ ] Backup current database
- [ ] Run migration: `python3 migrate_skipgrams_v4.py`
- [ ] Verify no gap_word_count=0 in results
- [ ] Generate new scoring output
- [ ] Document results

---

## 10. KEY FILES & LOCATIONS

**Code Files:**
- `/home/user/psalms-AI-analysis/scripts/statistical_analysis/skipgram_extractor_v4.py`
  - Lines 296: gap_word_count calculation
  - Lines 298-301: Quality filtering
  - Lines 130: Contiguous pattern recognition
  - Lines 229-320: Main extraction method

- `/home/user/psalms-AI-analysis/scripts/statistical_analysis/migrate_skipgrams_v4.py`
  - Lines 178-229: Migration process
  - Lines 210-216: Statistics reporting

**Database:**
- `/home/user/psalms-AI-analysis/data/psalm_relationships.db`
  - Table: psalm_skipgrams
  - Field: gap_word_count

**Data Files:**
- `/home/user/psalms-AI-analysis/data/analysis_results/enhanced_scores_skipgram_dedup_v5.json`
  - Contains 13,804 skipgrams (current, includes gap=0)

---

## 11. RISK ASSESSMENT

**Risk Level:** LOW

**Why it's low-risk:**
- Only removes patterns that violate the definition of skipgrams
- No changes to scoring algorithm
- Backward compatible with existing code
- Easy to rollback if needed
- Clear, simple fix

**Testing plan:**
1. Verify database has no gap_word_count=0
2. Verify count reduction matches expected 38.29%
3. Spot-check a few patterns manually
4. Compare scoring output before/after

---

## 12. DOCUMENTATION FILES

**Quick References:**
- This file: SKIPGRAM_INVESTIGATION_FINDINGS.md (overview)
- SKIPGRAM_ISSUE_SUMMARY.txt (executive summary)

**Detailed Analysis:**
- /docs/SKIPGRAM_GAP_ISSUE_ANALYSIS.md (11KB comprehensive analysis)
- /docs/SKIPGRAM_GAP_FIX_IMPLEMENTATION.md (5KB implementation guide)

---

## NEXT STEPS

1. Review this investigation
2. Approve the fix (3 lines of code)
3. Implement changes
4. Run migration
5. Verify results
6. Generate new output
7. Document completion

The fix is ready to implement when approved.

