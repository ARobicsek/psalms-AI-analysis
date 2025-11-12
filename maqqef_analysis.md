# Maqqef Handling Analysis

## Current System Behavior

### Raw Text from Sefaria
Psalm 3:8: `כִּֽי־הִכִּ֣יתָ אֶת־כׇּל־אֹיְבַ֣י לֶ֑חִי שִׁנֵּ֖י רְשָׁעִ֣ים שִׁבַּֽרְתָּ׃`

The text contains **3 maqqef characters (U+05BE - ־)**:
- Position 49: between כִּֽי and הִכִּ֣יתָ
- Position 63: between אֶת and כׇּל
- Position 68: between כׇּל and אֹיְבַ֣י

### Current Processing Pipeline

1. **Word Splitting** (`split_words()`)
   - Splits on whitespace only
   - Result for Psalm 3:8 position 5-6:
     - Word 5: `כִּֽי־הִכִּ֣יתָ` (ki-hikita, one maqqef inside)
     - Word 6: `אֶת־כׇּל־אֹיְבַ֣י` (et-kol-oyvai, two maqqefs inside)

2. **Consonantal Normalization** (`normalize_for_search()`)
   - Strips diacritics using range: `[\u0591-\u05C7]`
   - **Maqqef (U+05BE) falls within this range and IS REMOVED**
   - Result:
     - Word 5: `כיהכית` (ki + hikita combined, no hyphen)
     - Word 6: `אתכלאיבי` (et + kol + oyvai combined, no hyphens)

3. **Database Storage**
   - Words stored as single tokens without internal boundaries
   - Cannot search for individual morphemes like הכית or את separately

## The Problem

**Issue 2: "הכית את" search fails** because:
- `הכית` is embedded in `כיהכית` (with prefix `כי`)
- `את` is embedded in `אתכלאיבי` (with suffix `כלאיבי`)
- Phrase search looks for two adjacent standalone words, not embedded morphemes

**Issue 3: "שבר שן" search fails** because:
- Words have a word in between: `שני` (pos 8), `רשעים` (pos 9), `שברת` (pos 10)
- Also morphological mismatch (שני not שן, שברת not שבר)

## Alternative Approach: Replace Maqqef with Space

### Proposed Change
Instead of:
```python
# Current: maqqef is stripped as part of diacritics
text = re.sub(r'[\u0591-\u05C7]', '', text)
```

Do this:
```python
# Step 1: Replace maqqef with space BEFORE normalization
text = text.replace('\u05BE', ' ')  # Replace maqqef with space

# Step 2: Then strip other diacritics
text = re.sub(r'[\u0591-\u05BD\u05BF-\u05C7]', '', text)  # Skip U+05BE
```

### Result with Proposed Approach
Psalm 3:8 would split into:
- Word 5: `כי` (ki)
- Word 6: `הכית` (hikita) ← NOW SEARCHABLE!
- Word 7: `את` (et) ← NOW SEARCHABLE!
- Word 8: `כל` (kol)
- Word 9: `איבי` (oyvai)
- Word 10: `לחי` (lechi)
- etc.

**Phrase search "הכית את" would now find**: Words 6-7 as adjacent pair!

## Trade-offs

### Pros of Replacement Approach
1. ✓ Makes individual morphemes searchable
2. ✓ Improves phrase search accuracy
3. ✓ Reflects actual syntactic boundaries
4. ✓ Concordance results would be more granular and useful
5. ✓ Aligns with how users think about Hebrew words

### Cons of Replacement Approach
1. ✗ Loses prosodic information (that words are maqqef-connected)
2. ✗ Increases word count (artificial word boundaries)
3. ✗ Departs from traditional understanding of "word" in Hebrew
4. ✗ Requires rebuilding entire concordance database
5. ✗ May affect statistical analyses that rely on word counts

### Pros of Current Approach (Strip Maqqef)
1. ✓ Preserves traditional Hebrew word boundaries
2. ✓ Reflects prosodic/phonological reality
3. ✓ Accurate word counts for linguistic analysis
4. ✓ Matches cantillation practice (one accent domain)

### Cons of Current Approach (Strip Maqqef)
1. ✗ Makes phrase searching difficult
2. ✗ Cannot find individual morphemes
3. ✗ Requires complex variation generation in concordance librarian
4. ✗ Results in unexpected search failures

## Recommendation

**For a concordance system, replacing maqqef with space is better.**

### Why?
A concordance is fundamentally a **search tool**, not a linguistic analysis tool. Users want to:
- Find where specific words appear
- Search for meaningful phrases
- Discover usage patterns

The current approach optimizes for linguistic correctness but sacrifices searchability. Since your concordance librarian already tries to work around this by generating maqqef-combined variations, the system is acknowledging the problem.

### Better Solution: Replace Maqqef + Track Original Form

**Best of both worlds:**
1. Split on maqqef (replace with space)
2. Store original form in an additional column: `word_original`
3. Search uses split form, display shows original form

Database schema:
```sql
CREATE TABLE concordance (
    word TEXT,              -- Display form: כִּֽי־הִכִּ֣יתָ
    word_original TEXT,     -- Same as word (for tracking)
    word_consonantal TEXT,  -- Split form: כי, הכית (separate rows)
    maqqef_group_id INTEGER -- Links morphemes in same maqqef group
)
```

This way:
- Searches work naturally
- Original prosodic information is preserved
- Can reconstruct maqqef-connected units if needed

## Implementation Impact

### Files to Modify
1. `src/concordance/hebrew_text_processor.py` - Update `split_words()` or `normalize_for_search()`
2. `src/data_sources/tanakh_database.py` - Rebuild concordance with `build_concordance_index(force=True)`
3. `src/agents/concordance_librarian.py` - Remove maqqef-combined variation generation (no longer needed)

### Testing Needed
- Verify phrase searches now work
- Check word counts are reasonable
- Ensure no unintended side effects
- Re-run Psalm 3 concordance queries

Would you like me to implement this change?
