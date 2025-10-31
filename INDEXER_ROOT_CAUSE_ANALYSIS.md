# Liturgy Indexer Root Cause Analysis

## Executive Summary

This document provides detailed root cause analysis for 5 critical issues in the liturgy indexer implementation (`src/liturgy/liturgy_indexer.py`).

---

## Issue #1: Empty liturgical_context Fields

### Root Cause

**Location:** `_extract_context()` method (lines 513-566)

**Problem:** The sliding window approach fails when the original phrase contains punctuation marks like paseq (׀) that:
1. Count as separate "words" in the original text
2. Get removed during normalization  
3. Create a word count mismatch

**Code Analysis:**
```python
# Line 535-536: Uses normalized phrase word count
normalized_phrase_words = normalized_phrase.split()
phrase_length = len(normalized_phrase_words)  # WRONG when paseq present!
```

**Example (index_id 26037):**
- Original phrase: `׀ לֹ֥א הָלַךְ֮` (3 words when split)
- Normalized: `לא הלך` (2 words - paseq removed!)
- Window uses length=2 but needs 3
- Result: No match, returns empty string

### Recommended Fix

Use ORIGINAL phrase word count:
```python
# Line 535-536: Replace with
phrase_words = phrase.split()
phrase_length = len(phrase_words)  # Use original length
```

### Edge Cases
- Multiple paseq marks
- Standalone paragraph markers (פ, ס)
- Maqqef-connected words

---

## Issue #2: Multiple Phrase Entries Instead of Single Verse

### Root Cause

**Location:** Deduplication logic (lines 777-800)

**Problem:** Overlapping phrases from the SAME verse aren't consolidated into a full verse match.

**Example (Psalm 1:3 in prayer 626):**
- Index 26039: 10-word phrase (first part)
- Index 26040: 2-word phrase (end part)
- Should be: ONE exact_verse match

**Why:** Phrase extraction creates overlapping n-grams that both match, but deduplication doesn't check if they combine to form a complete verse.

### Recommended Fix

After line 775, add verse consolidation:
```python
verse_phrase_groups = defaultdict(list)
for match in deduplicated:
    key = (match['psalm_chapter'], match['psalm_verse_start'], 
           match['psalm_verse_end'], match['prayer_id'])
    verse_phrase_groups[key].append(match)

final = []
for (ps_ch, v_start, v_end, pray_id), matches in verse_phrase_groups.items():
    if len(matches) > 1 and v_start == v_end:
        # Get full verse and check if present
        # If yes, create exact_verse match
        # If no, keep individual phrases
    else:
        final.extend(matches)
```

---

## Issue #3: Missed Entire Chapter Detection

### Root Cause

**Location:** Chapter detection (lines 802-875)

**Problem:** Requires ALL verses be exact_verse (line 823):
```python
exact_verse_matches = [m for m in matches if m['match_type'] == 'exact_verse']
```

**Example (Psalm 135 in prayer 832):**
- Verses 2,4-20: exact_verse ✓
- Verses 1,3,21: phrase_match ✗ (missing Hallelujah)
- Result: Not detected as entire_chapter

**Why partial matches:**
- Verse 1: Missing `הללו יה` at start
- Verse 3: Only 3-word fragment (`כי טוב יהוה`)
- Verse 21: Missing `הללו יה` at end

### Recommended Fix

Relax requirement to include high-quality phrase matches:
```python
# Count verses that are MOSTLY present
verse_coverage = {}
for m in matches:
    verse_num = m['psalm_verse_start']
    if m['psalm_verse_start'] == m['psalm_verse_end']:
        if verse_num not in verse_coverage or m['match_type'] == 'exact_verse':
            verse_coverage[verse_num] = m

if len(verse_coverage) == total_verses:
    # Create entire_chapter
```

---

## Issue #4: Phrase When Full Verse Present

### Root Cause

Same as Issue #3 - phrase extraction creates partial matches before full verse detection.

**Examples:**
- Psalm 150:1 (prayer 35): 5-word phrase instead of full verse
- Psalm 145:1 (prayer 888): phrase instead of exact_verse

### Recommended Fix

Same as Issues #2 and #3:
1. Search full verses FIRST
2. Upgrade near-complete phrases
3. Enhanced deduplication

---

## Issue #5: No Consecutive Verse Detection

### Root Cause

**Location:** Not implemented!

**Current:** Psalm 6:2-11 in prayer 73 = 10 separate entries
**Expected:** Single "Psalm 6:2-11" verse range

This is a FEATURE REQUEST.

### Recommended Fix

Add after chapter detection (line 875):
```python
# Detect consecutive sequences (3+ verses)
for (psalm_ch, prayer_id), matches in chapter_prayer_groups.items():
    matches.sort(key=lambda m: m['psalm_verse_start'])
    
    i = 0
    while i < len(matches):
        # Find consecutive run
        j = i + 1
        while j < len(matches) and matches[j]['psalm_verse_start'] == matches[j-1]['psalm_verse_end'] + 1:
            j += 1
        
        if j - i >= 3:  # Minimum 3 for range
            # Create verse_range match
            i = j
        else:
            i = j
```

### Configuration

Add parameter: `consolidate_verse_ranges: bool = True`

---

## Implementation Priority

1. Issue #1 - Simple, high impact
2. Issue #2 - Medium complexity
3. Issue #4 - Related to #2
4. Issue #3 - Medium complexity  
5. Issue #5 - Feature enhancement

## Testing

Test with:
- Psalm 1 (Issues #1, #2)
- Psalm 6 (Issue #5)
- Psalm 135 (Issue #3)
- Psalms 145, 150 (Issue #4)

Verify:
- No empty contexts
- Verse ranges consolidated
- Chapters detected
- No duplicate phrases

---

**Prepared:** 2025-10-30
**Files analyzed:** 
- src/liturgy/liturgy_indexer.py
- data/liturgy.db
- database/tanakh.db
