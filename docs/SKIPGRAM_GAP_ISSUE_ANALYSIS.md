# Skipgram Extraction Logic Investigation

## CRITICAL ISSUE FOUND: 38.29% of "Skipgrams" Have gap_word_count=0

### Executive Summary
The skipgram extraction system is storing **contiguous patterns (gap_word_count=0) as skipgrams**, which is incorrect. Skipgrams BY DEFINITION should have gaps between matched words. Patterns with no gaps are simple contiguous phrases and should be handled separately.

---

## 1. Where Skipgrams Are Extracted

### Primary File
**Location:** `/home/user/psalms-AI-analysis/scripts/statistical_analysis/skipgram_extractor_v4.py`

**Key Method:** `extract_skipgrams_with_verse()` (lines 229-320)

**Extraction Windows:**
- 2-word patterns: within 5-word window (max_gap=5)
- 3-word patterns: within 7-word window (max_gap=7)  
- 4-word patterns: within 10-word window (max_gap=10)

**Process:**
1. For each starting position `i` in the psalm text
2. Define a window from position `i` to `i+max_gap`
3. Generate ALL n-word combinations within that window using `combinations(window_indices, n)`
4. Extract roots for matched words
5. Calculate gap_word_count
6. Perform quality filtering
7. Store pattern with gap_word_count value

### Storage
**Database:** `/home/user/psalms-AI-analysis/data/psalm_relationships.db` (table: `psalm_skipgrams`)
**Schema includes:**
- `gap_word_count INTEGER NOT NULL DEFAULT 0`
- `pattern_roots TEXT`
- `pattern_hebrew TEXT`
- `full_span_hebrew TEXT`

---

## 2. How gap_word_count Is Calculated

**Location:** `skipgram_extractor_v4.py`, line 296

```python
gap_word_count = (last_idx - first_idx + 1) - n
```

**Where:**
- `last_idx` = index of last matched word in pattern
- `first_idx` = index of first matched word in pattern
- `n` = number of words in pattern (2, 3, or 4)

**Examples:**

| Scenario | Indices | Calculation | Result | Meaning |
|----------|---------|-------------|--------|---------|
| "word1 word2" consecutive | 0→1 | (1-0+1) - 2 = 0 | **0 = Contiguous** |
| "word1 [skip] word2" with 1 word between | 0→2 | (2-0+1) - 2 = 1 | 1 = One gap word |
| "word1 word2 word3 word4" all consecutive | 0→3 | (3-0+1) - 4 = 0 | **0 = Contiguous** |
| "word1 [skip1] [skip2] word2" with 2 gaps | 0→3 | (3-0+1) - 2 = 2 | 2 = Two gap words |

**Key Insight:** When gap_word_count=0, ALL matched words are consecutive with NO gaps between them.

---

## 3. Skipgram Extraction and Storage Process

**Main Flow:**

1. **Extraction** (skipgram_extractor_v4.py):
   ```
   get_psalm_words() → extract_skipgrams_with_verse() → Quality Filtering → [All patterns including gap=0]
   ```

2. **Migration to Database** (migrate_skipgrams_v4.py):
   ```
   extractor.extract_all_skipgrams() → store_psalm_skipgrams() → INSERT INTO psalm_skipgrams
   ```

3. **Scoring** (enhanced_scorer_skipgram_dedup_v4.py):
   ```
   Load from database → Deduplicate → Score → Output JSON
   ```

**Critical Issue:** No filtering occurs to EXCLUDE patterns with gap_word_count=0 during extraction or storage.

---

## 4. Why gap_word_count=0 Patterns Are Being Included

### Root Cause
The extraction algorithm uses `combinations()` to generate ALL possible n-word selections within the window, regardless of whether they form contiguous or non-contiguous patterns.

**Example for a 3-word window with n=2:**
```
Words: ["A", "B", "C"]
combinations([0,1,2], 2) produces:
  - Indices (0,1) → A B → gap_word_count = (1-0+1)-2 = 0 [CONTIGUOUS]
  - Indices (0,2) → A C → gap_word_count = (2-0+1)-2 = 1 [SKIPGRAM]
  - Indices (1,2) → B C → gap_word_count = (2-1+1)-2 = 0 [CONTIGUOUS]
```

Both contiguous and skipgram combinations are extracted and stored.

### Why Not Filtered?
**Quality Filtering** (lines 298-301) checks `_should_keep_pattern()` which:
- ✅ Filters by content word count
- ✅ Filters by pattern stoplist
- ❌ **DOES NOT filter by gap_word_count**

The code even RECOGNIZES gap_word_count=0 patterns as "contiguous":
```python
# Line 130 in _should_keep_pattern()
is_contiguous = (gap_word_count == 0)

# Line 133 - Uses separate stoplist for contiguous patterns
stoplist = self.stoplist_contiguous if is_contiguous else self.stoplist_skipgrams
```

But then still KEEPS them if they pass other filters.

---

## 5. Current Data Statistics

### Distribution in V5 Output
**Total Skipgrams in Database:** 13,804 patterns

| gap_word_count | Count | Percentage | Issue |
|---|---|---|---|
| **0** | **5,285** | **38.29%** | ❌ **Contiguous (should not be skipgrams)** |
| 1 | 3,349 | 24.26% | ✅ True skipgrams |
| 2 | 2,786 | 20.18% | ✅ True skipgrams |
| 3 | 2,230 | 16.15% | ✅ True skipgrams |
| 4+ | 154 | 1.12% | ✅ True skipgrams (rare) |

### Examples of Problematic gap_word_count=0 "Skipgrams"

1. **Pattern:** `ציל יהוה עזר חוש` (4 words)
   - Matched: `לְהַצִּילֵ֑נִי יְ֝הֹוָ֗ה לְעֶזְרָ֥תִי חֽוּשָׁה׃`
   - Full span: Same (no gaps!) = **Completely contiguous**
   - Length: 4, Gap: 0, Span words: 4

2. **Pattern:** `צור יזוב מים` (3 words)
   - Matched: `צ֨וּר וַיָּז֣וּבוּ מַיִם֮`
   - Full span: Identical = **All consecutive**
   - Length: 3, Gap: 0, Span words: 3

3. **Pattern:** `כל אשר חפץ עש` (4 words)
   - Matched: `כֹּ֖ל אֲשֶׁר חָפֵ֣ץ עָשָֽׂה׃`
   - Full span: Identical = **No gaps**
   - Length: 4, Gap: 0, Span words: 4

---

## 6. Filtering Logic Analysis

### Current Quality Filtering (_should_keep_pattern method, lines 108-161)

```python
def _should_keep_pattern(self, pattern_roots: str, gap_word_count: int) -> Tuple[bool, str]:
    # 1. Check stoplist (knows about contiguous vs skipgram)
    is_contiguous = (gap_word_count == 0)
    stoplist = self.stoplist_contiguous if is_contiguous else self.stoplist_skipgrams
    
    # 2. Check content word count
    if is_contiguous:
        min_content = 1  # Require ≥1 content word
    else:
        # Skipgrams: require ≥1 content word for 2-word, ≥2 for 3+ word
        if pattern_length == 2:
            min_content = 1
        else:
            min_content = 2
    
    # 3. Return True if passes filters
    # ❌ PROBLEM: Doesn't have an option to REJECT contiguous patterns entirely
```

### What's Missing
**NO filtering to EXCLUDE gap_word_count=0 patterns** - The code only applies filtering that is permissive of them.

**Two possible approaches:**

#### Option A: Skip extraction of gap_word_count=0 patterns
```python
# In extract_skipgrams_with_verse() - Skip contiguous patterns entirely
if gap_word_count == 0:
    continue  # Skip this pattern entirely
```

#### Option B: Reject in filtering
```python
# In _should_keep_pattern() - Add explicit check
if gap_word_count == 0:
    self.stats['filtered_by_gap_requirement'] += 1
    return False, "Contiguous pattern (requires gap)"
```

---

## 7. What Needs To Be Fixed

### IMMEDIATE FIX (Option A - Recommended)

**File:** `skipgram_extractor_v4.py`, in `extract_skipgrams_with_verse()` method

**Current code (line 296-319):**
```python
gap_word_count = (last_idx - first_idx + 1) - n

# V5: Check quality filters before adding
should_keep, reason = self._should_keep_pattern(pattern_roots, gap_word_count)

if should_keep:
    # Store skipgram
    skipgrams.append({...})
```

**Fixed code:**
```python
gap_word_count = (last_idx - first_idx + 1) - n

# CRITICAL: Skip contiguous patterns (gap_word_count=0)
# These should be handled by contiguous phrase extraction, not skipgrams
if gap_word_count == 0:
    continue  # Skip this pattern entirely

# V5: Check quality filters before adding
should_keep, reason = self._should_keep_pattern(pattern_roots, gap_word_count)

if should_keep:
    # Store skipgram
    skipgrams.append({...})
```

### SECONDARY FIX (Option B - Belt and Suspenders)

Add explicit check in `_should_keep_pattern()` to document intent:

```python
def _should_keep_pattern(self, pattern_roots: str, gap_word_count: int) -> Tuple[bool, str]:
    if not self.enable_quality_filtering:
        return True, "Filtering disabled"

    self.stats['total_extracted'] += 1

    # CRITICAL: Reject contiguous patterns (should be in contiguous_phrases, not skipgrams)
    if gap_word_count == 0:
        self.stats['filtered_by_gap_requirement'] += 1
        return False, "Contiguous pattern - not a skipgram (requires gap_word_count > 0)"

    # ... rest of filtering logic
```

### TERTIARY FIX (Migration cleanup)

After code fix, regenerate database:
```python
# In migrate_skipgrams_v4.py
migrator = SkipgramMigrationV4()
migrator.backup_old_data()
migrator.drop_old_table()
migrator.create_new_schema()
migrator.migrate_all_psalms()  # Will now skip gap_word_count=0 patterns
```

---

## 8. Expected Impact of Fix

### Reduction in Skipgrams
- **Before:** 13,804 skipgrams total
- **After:** ~8,519 skipgrams (removes 5,285 contiguous patterns)
- **Reduction:** 38.29% fewer patterns (but more accurate)

### Quality Improvement
- ✅ Skipgrams collection will contain ONLY true skipgrams (gap_word_count > 0)
- ✅ Contiguous phrases clearly separated into their own collection
- ✅ Scoring more accurate (no false positives from contiguous phrases mixed into skipgrams)
- ✅ Terminology consistent with linguistic definition

### Implementation Checklist
- [ ] Add gap_word_count > 0 check in extraction (line ~297)
- [ ] Add statistics tracking for filtered gap_word_count=0 patterns
- [ ] Backup existing data
- [ ] Regenerate psalm_skipgrams table
- [ ] Regenerate V5 scoring output
- [ ] Verify final skipgram count matches expected reduction
- [ ] Update documentation

---

## Summary Table

| Aspect | Current | Fixed |
|--------|---------|-------|
| **gap_word_count=0 in skipgrams** | 5,285 (38.29%) | 0 (0%) |
| **True skipgrams (gap>0)** | 8,519 | 8,519 |
| **Definition accuracy** | Incorrect (includes contiguous) | Correct (skipgrams only) |
| **Filtering logic** | Incomplete (no gap check) | Complete |

---

## References

### Files Involved
1. `/home/user/psalms-AI-analysis/scripts/statistical_analysis/skipgram_extractor_v4.py` - Extraction logic
2. `/home/user/psalms-AI-analysis/scripts/statistical_analysis/migrate_skipgrams_v4.py` - Database migration
3. `/home/user/psalms-AI-analysis/data/psalm_relationships.db` - Data storage

### Code Locations
- Gap calculation: Line 296
- Quality filtering: Lines 298-301, 108-161
- Contiguous pattern recognition: Line 130
- Extraction loop: Lines 229-320

### Data Files
- V5 Output: `/home/user/psalms-AI-analysis/data/analysis_results/enhanced_scores_skipgram_dedup_v5.json`
- V4 Output: `/home/user/psalms-AI-analysis/data/analysis_results/enhanced_scores_skipgram_dedup_v4.json`
