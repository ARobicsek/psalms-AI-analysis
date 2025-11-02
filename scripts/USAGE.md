# Liturgical Librarian - Usage Guide

## Quick Start Scripts

### 1. Re-index All 150 Psalms

This rebuilds the entire `psalms_liturgy_index` table with corrected data.

```bash
python scripts/reindex_all_psalms.py
```

**Duration**: ~30-60 minutes for all 150 Psalms
**Output**: Progress printed to console and saved to `logs/reindex_all_psalms.log`

**What it does**:
- Clears existing corrupted index data for each Psalm
- Re-indexes with fixed context extraction (character-based, ~300 chars)
- Deduplicates overlapping phrase matches
- Stores matches with proper `liturgy_context` field

### 2. Analyze Psalm 1 (Simple Output)

Run liturgical analysis on Psalm 1 and save clean results.

```bash
python scripts/run_psalm1_analysis.py
```

**Duration**: ~30 seconds
**Output**: `output/psalm1_liturgy_analysis.txt` (clean, formatted results)

**What it does**:
- Queries Psalm 1 matches from database
- Runs LLM validation to filter false positives
- Generates Haiku summaries for each phrase
- Saves formatted output with prayer contexts

### 3. Analyze Psalm 1 (Verbose Debug Log)

Capture all LLM prompts and responses for debugging.

```bash
python scripts/record_llm_session.py
```

**Duration**: ~30 seconds
**Output**: `logs/psalm1_full_prompts_log.txt` (includes all prompts/responses)

**What it does**:
- Same as above, but with `verbose=True`
- Logs every LLM prompt sent
- Logs every LLM response received
- Useful for debugging prompt quality and LLM behavior

### 4. Verify Database Quality

Check if database has been properly re-indexed.

```bash
python scripts/check_indexer_version.py
```

**What it checks**:
- Average context length (~300 chars = good, ~200 chars = old corrupted data)
- Whether phrases exist in their `liturgy_context` (should be 100%, not 60%)
- Total match count and psalm coverage

### 5. Investigate False Positives

Debug specific false positive cases.

```bash
python scripts/investigate_false_positives.py
```

**What it does**:
- Examines specific matches from database
- Checks if phrases actually exist in the liturgy text
- Identifies phantom matches (should be 0 after re-indexing)

---

## Deduplication Logic

**Q: Does the indexer group overlapping phrases?**

**A: Yes!** The indexer has intelligent deduplication logic.

### How it works:

For a verse with words `A-B-C-D-E-F`, the indexer:

1. **Finds all n-gram matches**:
   - `A-B` (2 words)
   - `B-C` (2 words)
   - `C-D` (2 words)
   - `A-B-C` (3 words)
   - `B-C-D` (3 words)
   - `A-B-C-D` (4 words)
   - ... and so on

2. **Groups matches by location**:
   - Groups all matches that appear at the **same position** in the same prayer
   - Example: `A-B`, `A-B-C`, `A-B-C-D` all start at position X in Prayer Y

3. **Selects the best match per location**:
   - **Priority 1**: `exact_verse` > `phrase_match` (match type)
   - **Priority 2**: Longer phrase (4 words > 3 words > 2 words)
   - **Priority 3**: Higher confidence score

4. **Result**: One match per location
   - Instead of 3 matches (`A-B`, `A-B-C`, `A-B-C-D`), keep only `A-B-C-D`
   - This prevents duplicate entries for the same quotation

### Code Location

See `src/liturgy/liturgy_indexer.py`, lines 569-656:
- Function: `_deduplicate_matches()`
- Called automatically during indexing (line 132)

### Statistics

From Session 31 testing:
- **Before deduplication**: 7,663 matches
- **After deduplication**: 3,208 matches
- **Reduction**: 58% (removed overlapping phrases)

---

## Monitoring Re-indexing Progress

While `reindex_all_psalms.py` is running, you can monitor progress:

```bash
# Check how many psalms completed
grep "✓ Indexed" logs/reindex_all_psalms.log | wc -l

# Check current psalm being processed
tail -5 logs/reindex_all_psalms.log

# Check database row count (should increase as psalms are indexed)
sqlite3 data/liturgy.db "SELECT COUNT(*) FROM psalms_liturgy_index"
```

---

## Expected Results After Re-indexing

| Metric | Before (Corrupted) | After (Fixed) |
|--------|-------------------|---------------|
| Average context length | ~225 chars | ~300 chars |
| Phrases in context | 60% | 100% |
| Phantom matches | 40% | 0% |
| LLM validation working | No (JSON bug) | Yes |
| Token cost per validation | ~82,500 tokens | ~550 tokens |

---

## Troubleshooting

### Re-indexing hangs or crashes

**Problem**: UTF-8 encoding issues in verbose output
**Solution**: Ensure `verbose=False` in `reindex_all_psalms.py` line 26

### No matches found for a Psalm

**Problem**: Psalm may have no distinctive phrases in liturgy
**Solution**: This is expected for some Psalms (rare usage)

### LLM validation not working

**Problem**: API key not set
**Solution**: Ensure `ANTHROPIC_API_KEY` in `.env` file

### High token costs

**Problem**: Using old code with 30k char contexts
**Solution**: Verify `liturgical_librarian.py` line 867 uses `match.liturgy_context` (not `hebrew_text[:30000]`)
