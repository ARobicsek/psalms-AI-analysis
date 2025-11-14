# Top 500 Deduplication Issues and Proposed Fixes

## Issue Summary

After reviewing the top 500 connections output, four critical issues were identified:

### Issue 1: Incomplete Skipgram vs Contiguous Deduplication

**Problem**: A 4-word skipgram contains 2-word contiguous phrases as subsequences, but those phrases are not being removed during deduplication.

**Example** (Rank 500, Psalms 50-82):
- Contiguous phrase: "זמור אסף" (2 words)
- Contiguous phrase: "אמר אלה" (2 words)
- Skipgram: "מזמור לאסף אל אלהים" (4 words)

**Expected**: The skipgram should cause the "זמור אסף" phrase to be removed (since it's a subsequence of the skipgram).

**Root Cause**: Contiguous phrases use ROOT extraction (strips prefixes like מ and ל), while skipgrams use raw CONSONANTAL forms. This makes them incomparable:
- Contiguous: "זמור" and "אסף" (roots extracted from "מִזְמ֗וֹר לְאָ֫סָ֥ף")
- Skipgram: "מזמור" and "לאסף" (consonantal forms preserved)

### Issue 2: Missing Full Hebrew Text for Skipgrams

**Problem**: Skipgrams only show the matched words, not the complete phrase including gap words.

**Example**:
- Current: "מזמור לאסף אל אלהים" (shows 4 matched words)
- Needed: Full context like "מזמור לאסף [gap words] אל [gap words] אלהים"

**Why**: Users need to see the actual text to understand what's being matched.

### Issue 3: False Positive Root Matches

**Problem**: The root extraction logic is too simplistic - it just strips common prefixes/suffixes without understanding Hebrew morphology, creating many false matches.

**Examples**:

1. **Root "חי"** matches:
   - "מָ֝חִ֗יתָ" (machita, "you destroyed" from root נכה/מחה)
   - "חַיִּ֣ים" (chayim, "life" from root חיה)
   - **False match** - different roots with different meanings

2. **Root "בי"** matches:
   - "לִבִּ֑י" (libi, "my heart" from לב + suffix)
   - "בְּבֵ֣ית" (b'veit, "in the house" - just the ב preposition)
   - **False match** - preposition vs actual word

3. **Root "ית"** matches:
   - "שִׁ֘יתָ֤ה" (verb form with ית ending)
   - "בֵּ֥ית" (bayit, "house" where ית is part of the root)
   - **False match** - verb ending vs noun root

4. **Root "אול"** matches:
   - "לִשְׁא֑וֹלָה" (to Sheol)
   - "לְשָׁ֫א֥וּל" (to/for Saul)
   - **Questionable** - these are actually related (both from שאול)

5. **Root "אד"** matches:
   - "מְאֹד֮" (me'od, "very/much")
   - "אֲדֹנָ֑י" (Adonai, "Lord")
   - **False match** - completely unrelated words

6. **Root "ונ"** matches:
   - "לְשׁוֹנְךָ֣" (your tongue - has ונ inside)
   - "כּוֹנָ֗נוּ" (they established - has ונ)
   - **False match** - substring matching, not morphological analysis

**Root Cause**: The `extract_root()` method in `root_extractor.py` (lines 187-219):
```python
def extract_root(self, word: str) -> str:
    # Step 1: Normalize to consonantal
    normalized = self.normalize_word(word)
    # Step 2: Strip prefixes (max 2)
    without_prefixes = self.strip_prefixes(normalized, max_prefixes=2)
    # Step 3: Strip suffixes (max 1)
    root = self.strip_suffixes(without_prefixes, max_suffixes=1)
    return root
```

This is pure string manipulation, not linguistic analysis.

### Issue 4: Paragraph Markers Counted as Words

**Problem**: End-of-line/paragraph notation like "{פ}" is being included in word counts and potentially in phrase matching.

**Example**:
```
"consonantal": "בו {פ}",
"length": 2,
"hebrew": "בו {פ}"
```

**Expected**: "{פ}" should be filtered out before any analysis.

**Impact**: Inflates word counts, creates spurious phrase matches.

## Proposed Solutions

### Solution for Issue 1: Standardize to Root Extraction

**Option A: Convert Skipgrams to Use Root Extraction** (RECOMMENDED)
- Modify `skipgram_extractor.py` to extract roots instead of raw consonantal forms
- This makes skipgrams comparable with contiguous phrases
- Allows proper deduplication

**Changes needed**:
1. Import `RootExtractor` in `skipgram_extractor.py`
2. Use `extractor.extract_root(word)` instead of `word_consonantal`
3. Rebuild skipgram database with root-based extraction
4. Re-run V2 scoring

**Option B: Convert Contiguous Phrases to Raw Consonantal**
- Less desirable because root extraction filters out function words
- Would increase noise in matches

**Recommendation**: Option A - skipgrams should match contiguous phrase extraction methodology.

### Solution for Issue 2: Add Full Hebrew Text Reconstruction

**Approach**: When storing skipgrams, include both:
- The matched words (current)
- The full text span including gap words

**Implementation**:
1. In `skipgram_extractor.py`, track the full text span:
```python
# Get words from start_index to end_index
start_idx = combo_indices[0]
end_idx = combo_indices[-1]
full_span_words = words[start_idx:end_idx+1]
full_hebrew = ' '.join([w['hebrew'] for w in full_span_words])
```

2. Store both `pattern_hebrew` (matched words only) and `full_span_hebrew` (complete text)

3. Update top 500 output to show both forms

### Solution for Issue 3: Improve Root Extraction

**Short-term Fix**: Add filtering to remove obvious false positives:
- Exclude roots shorter than 3 characters (filters "בי", "ית", "ונ")
- Exclude common prepositions (ב, ל, כ, מ) when they appear alone
- Exclude common suffixes (ה, ים, ות) when they appear alone

**Long-term Fix** (future enhancement):
- Integrate proper Hebrew morphological analyzer (like MILA, Hebmorph, or AlephBERT)
- Use actual linguistic roots instead of string manipulation
- Would require significant research and integration work

**Recommended**: Implement short-term fix now, document long-term approach for future.

### Solution for Issue 4: Filter Paragraph Markers

**Changes needed**:

1. **In Hebrew text processing** (before any analysis):
```python
def clean_hebrew_text(text: str) -> str:
    """Remove paragraph markers and other non-word elements."""
    # Remove common markers
    text = re.sub(r'\{[^\}]+\}', '', text)  # Remove {פ}, {ס}, etc.
    text = re.sub(r'[\[\]]', '', text)  # Remove brackets
    return text.strip()
```

2. **Apply in multiple places**:
   - `root_extractor.py`: Clean text before splitting into words
   - `skipgram_extractor.py`: Clean concordance words
   - Any other text processing pipelines

3. **Rebuild databases** with cleaned text

## Implementation Plan

### Phase 1: Critical Fixes (Implement Now)

1. ✅ **Document issues** (this file)
2. **Fix paragraph markers**:
   - Add `clean_hebrew_text()` function to `root_extractor.py`
   - Apply before word splitting in all extraction
   - Update tests

3. **Improve root extraction**:
   - Add minimum length filter (>= 3 characters)
   - Add preposition/suffix exclusion list
   - Update `extract_root()` method

4. **Standardize to root-based extraction**:
   - Modify `skipgram_extractor.py` to use root extraction
   - Test on sample psalms

### Phase 2: Rebuild Data

5. **Rebuild skipgram database**:
   - Run updated extractor on all 150 psalms
   - Verify root-based patterns match contiguous

6. **Re-run V2 scoring**:
   - Execute `enhanced_scorer_skipgram_dedup_v2.py`
   - Execute `generate_top_500_skipgram_dedup_v2.py`

### Phase 3: Enhancements

7. **Add full Hebrew text to skipgrams**:
   - Modify extractor to capture full span
   - Update output format

8. **Validate results**:
   - Check rank 500 again - should contiguous be removed?
   - Review sample of root matches for false positives
   - Verify paragraph markers gone

## Testing Strategy

1. **Unit tests** for new filtering logic
2. **Integration test** on Psalms 50-82 (rank 500 example)
3. **Comparison report**: V2 current vs V2 fixed
4. **Manual review** of top 20 connections

## Migration Notes

- Current V2 files will be preserved as `*_v2.json`
- New fixed version will be `*_v3.json`
- Document differences in `V2_VS_V3_COMPARISON.md`

## Expected Impact

- **Issue 1**: Better deduplication → more accurate scores
- **Issue 2**: Better readability → easier validation
- **Issue 3**: Fewer false matches → more meaningful connections
- **Issue 4**: Accurate word counts → correct normalization

## Questions for User

1. Should we implement all fixes now, or prioritize certain issues?
2. Is the short-term root extraction fix acceptable, or wait for proper morphological analysis?
3. Should we create V3 or overwrite V2?
4. Any other filtering needs (e.g., liturgical formulas)?
