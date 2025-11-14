# Next Session Prompt - Psalms Project

## Quick Session Start

Continue working on the Psalms structural analysis project. This document provides context for picking up where the last session left off.

## Current Status

**Phase**: V4.2 Root Extraction & Gap Penalty - TESTING NEEDED  
**Version**: V4.2 with ETCBC morphology cache and gap penalty  
**Last Session**: Session 105 - Root Extraction & Gap Penalty (2025-11-14)

## Session 105 Summary (IN PROGRESS)

**Completed**:
- ✓ Built ETCBC morphology cache (5,353 entries from Psalms)
- ✓ Fixed cache builder for Hebrew consonantal forms
- ✓ Improved fallback root extraction (3-letter minimum)
- ✓ Implemented 10% gap penalty per word (max 50%)
- ✓ Root extraction: 80% improvement on test cases

**Pending**:
- ⏳ Re-run V4.2 migration with improved root extraction  
- ⏳ Re-run V4.2 scoring with gap penalty  
- ⏳ Validate results and spot-check examples

## Next Steps

### Option 1: Complete V4.2 Re-Migration (Recommended)

Run full migration with improved root extraction and gap penalty:

```bash
# 1. Re-migrate all psalm pairs (will use new ETCBC cache)
python3 scripts/statistical_analysis/skipgram_migration_v4.py

# 2. Re-score with gap penalty
python3 scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v4.py

# 3. Spot-check improvements
# Check Ps 31/41 and Ps 22/119 for better root matching
```

**Expected Time**: ~2-3 hours for full migration + scoring  
**Expected Result**: Better root matching, reduced false positives, gap penalty applied

### Option 2: Spot-Test Before Full Migration

Test on a few psalm pairs first to verify improvements:

```bash
# Test individual pairs
python3 scripts/statistical_analysis/test_single_pair.py 31 41
python3 scripts/statistical_analysis/test_single_pair.py 22 119
```

## Key Improvements This Session

### 1. ETCBC Morphology Cache
- **Built**: 5,353 morphological mappings from Psalms
- **Source**: ETCBC BHSA 2021 scholarly database
- **Location**: `src/hebrew_analysis/data/psalms_morphology_cache.json`
- **Impact**: Accurate root extraction for most Psalms words

### 2. Improved Fallback Root Extraction  
- **Change**: Require 3 letters after prefix stripping (was 2)
- **Impact**: Prevents over-stripping like "שוא" → "וא"
- **Result**: 80% improvement on test cases

### 3. Gap Penalty for Skipgrams
- **Formula**: `value = base * (1.0 - min(0.1 * gap_count, 0.5))`
- **Impact**: Contiguous phrases valued higher than gappy skipgrams
- **Example**: 3-word pattern with 2 gap words: 2.0 → 1.6 points

## Files Modified This Session

**Core Changes**:
- `src/hebrew_analysis/cache_builder.py` - ETCBC API fixes
- `src/hebrew_analysis/morphology.py` - Fallback extraction improvements
- `scripts/statistical_analysis/skipgram_extractor_v4.py` - Added gap_word_count
- `scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v4.py` - Gap penalty

**New Files**:
- `src/hebrew_analysis/data/psalms_morphology_cache.json` - ETCBC morphology cache

## Important Notes

1. **ETCBC Cache Coverage**: Cache only includes words that appear in Psalms. Words from other books will use fallback extraction.

2. **Gap Penalty is Modest**: 10% per gap word, max 50%. Won't eliminate distant patterns, just reduces their weight.

3. **Root Extraction Fallback**: For words not in cache (rare forms, other books), falls back to improved naive extraction.

4. **Migration Required**: Need to re-run migration for root extraction improvements to take effect.

## Questions for User

Before proceeding with full migration:
1. Should we run full migration now, or test on specific psalm pairs first?
2. Are there specific psalm pairs you want to verify for improvements?
3. Is the 10% gap penalty appropriate, or would you prefer different values?

## Reference

- **Project Docs**: `/docs/`
- **Implementation Log**: `/docs/IMPLEMENTATION_LOG.md` (Session 105)
- **Database**: `/data/psalm_relationships.db`
- **Scripts**: `/scripts/statistical_analysis/`

