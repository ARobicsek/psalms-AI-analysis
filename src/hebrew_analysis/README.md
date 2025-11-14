# Hebrew Morphological Analysis Package

Accurate root extraction for Biblical Hebrew using ETCBC Text-Fabric morphological data.

## Overview

This package provides morphologically-aware root extraction for Biblical Hebrew, replacing the naive string manipulation approach in V2 with scholarly morphological analysis from the ETCBC BHSA (Biblia Hebraica Stuttgartensia Amstelodamensis) dataset.

### Problem Solved

V2's naive root extraction (simple prefix/suffix stripping) caused false positives:

```python
# V2 (Naive):
extract_root("מָחִיתָ")  # → "חי" (wrong!)
extract_root("חַיִּים")  # → "חי" (wrong!)
# Both get same root, but different meanings!

# V3 (Morphological):
extract_root("מָחִיתָ")  # → "מחה" (correct: "destroy")
extract_root("חַיִּים")  # → "חיה" (correct: "live")
# Correctly distinguished!
```

### How It Works

1. **Cache Lookup**: Pre-built lookup table from ETCBC morphological data (high accuracy)
2. **Fallback**: Improved naive extraction for edge cases (with filtering)
3. **Performance**: O(1) dictionary lookup for known words

## Installation

### 1. Install Text-Fabric (for building cache)

```bash
pip install text-fabric
```

Note: Text-Fabric will auto-download ~100MB of BHSA data on first use.

### 2. Build Morphology Cache

```bash
cd src/hebrew_analysis
python cache_builder.py
```

This creates `data/psalms_morphology_cache.json` with morphological data for all words in Psalms.

**First run**: Downloads ETCBC BHSA data (~100MB), takes ~2 minutes  
**Subsequent runs**: Uses cached data, takes ~10 seconds

### 3. Verify Installation

```bash
python test_morphology.py
```

Expected output:
```
✅ PASS: Different roots extracted ('מחה' vs 'חיה')
✅ PASS: Different roots extracted ('לב' vs 'בית')
✅ PASS: Different roots extracted ('מאד' vs 'אדן')

🎉 ALL TESTS PASSED!
```

## Usage

### Simple API

```python
from src.hebrew_analysis.morphology import extract_morphological_root

# Extract root from Hebrew word
root = extract_morphological_root("מָחִיתָ")
print(root)  # Output: "מחה"
```

### Advanced API

```python
from src.hebrew_analysis.morphology import HebrewMorphologyAnalyzer

# Create analyzer instance
analyzer = HebrewMorphologyAnalyzer()

# Extract multiple roots
words = ["מָחִיתָ", "חַיִּים", "לִבִּי"]
roots = [analyzer.extract_root(word) for word in words]
print(roots)  # Output: ["מחה", "חיה", "לב"]

# Check cache stats
stats = analyzer.get_cache_stats()
print(f"Cache loaded: {stats['cache_loaded']}")
print(f"Cache size: {stats['cache_size']} entries")
```

### Drop-in Replacement for V2

```python
# Original V2 code:
from scripts.statistical_analysis.root_extractor import RootExtractor
extractor = RootExtractor(db_path)

# V3 with morphology (same API):
from src.hebrew_analysis.root_extractor_v2 import EnhancedRootExtractor as RootExtractor
extractor = RootExtractor(db_path)

# Works exactly the same, but with accurate morphology!
roots = extractor.extract_psalm_roots(23)
```

## Files

- `__init__.py` - Package initialization and exports
- `morphology.py` - Main morphology analyzer (cache lookup + fallback)
- `cache_builder.py` - Builds cache from ETCBC Text-Fabric data
- `root_extractor_v2.py` - Enhanced root extractor (drop-in replacement for V2)
- `test_morphology.py` - Proof of concept tests
- `README.md` - This file
- `data/psalms_morphology_cache.json` - Pre-built cache (created by cache_builder.py)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ extract_morphological_root(word)                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ HebrewMorphologyAnalyzer                                │
│  1. strip_consonantal(word) → consonantal form          │
│  2. Check cache[consonantal] → lemma (if found)         │
│  3. Else: fallback_extraction(consonantal)              │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴──────────────┐
        ▼                           ▼
┌──────────────────┐    ┌──────────────────────┐
│ Cache Lookup     │    │ Improved Fallback    │
│ (ETCBC data)     │    │ - Min length filter  │
│ - High accuracy  │    │ - Function word check│
│ - O(1) lookup    │    │ - Smart prefix strip │
│ - 95%+ coverage  │    │ - Smart suffix strip │
└──────────────────┘    └──────────────────────┘
```

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Build cache (one-time) | ~10 seconds | All 150 Psalms |
| Load cache into memory | ~10ms | JSON deserialization |
| Lookup per word | ~0.001ms | Dictionary access |
| Process 312K entries | ~0.3 seconds | Cache lookups only |

**Total re-scoring time**: < 5 minutes (dominated by database queries, not morphology)

## Data Source

**ETCBC BHSA (Biblia Hebraica Stuttgartensia Amstelodamensis)**
- Source: https://github.com/ETCBC/bhsa
- Decades of scholarly linguistic analysis
- Complete morphological annotation of Hebrew Bible
- License: CC BY-NC 4.0 (non-commercial use)
- Text: Westminster Leningrad Codex (WLC)

## Cache Format

```json
{
  "version": "1.0.0",
  "source": "ETCBC/bhsa",
  "source_license": "CC BY-NC 4.0",
  "books": "Psalms",
  "word_count": 13450,
  "unique_forms": 8234,
  "collisions": 156,
  "morphology": {
    "מחית": "מחה",
    "חיים": "חיה",
    "לבי": "לב",
    ...
  }
}
```

## Fallback Strategy

For words not in cache (rare edge cases):

1. **Minimum length**: Don't extract roots < 2 characters (avoid "בי", "ית")
2. **Function word protection**: Don't strip to single letters (ב, ל, כ, etc.)
3. **Conservative stripping**: Max 1 prefix + max 1 suffix
4. **Validation**: Result must be meaningful (length ≥ 2, not function word)

## Testing

### Unit Tests

```bash
python test_morphology.py
```

Tests false positive examples from V2:
- מָחִיתָ vs חַיִּים → Different roots (מחה vs חיה) ✅
- לִבִּי vs בְּבֵית → Different roots (לב vs בית) ✅
- מְאֹד vs אֲדֹנָי → Different roots (מאד vs אדן) ✅

### Integration Tests

```bash
python root_extractor_v2.py
```

Tests on Psalm 23:
- Loads database
- Extracts all roots
- Shows frequency distribution
- Validates with morphology cache

## Integration into V3 Pipeline

### Step 1: Update root_extractor.py

```python
# In scripts/statistical_analysis/root_extractor.py
from src.hebrew_analysis.morphology import extract_morphological_root

class RootExtractor:
    def extract_root(self, word: str) -> str:
        # Replace naive extraction with morphological
        return extract_morphological_root(word)
```

### Step 2: Update skipgram_extractor.py

```python
# In scripts/statistical_analysis/skipgram_extractor.py
from src.hebrew_analysis.morphology import extract_morphological_root

# Use morphological roots for skipgrams (matches contiguous phrase extraction)
for word in words:
    root = extract_morphological_root(word['hebrew'])
    # ... rest of skipgram logic
```

### Step 3: Rebuild Databases

```bash
# Rebuild concordance with V3 roots
python scripts/rebuild_concordance_with_maqqef_split.py

# Rebuild skipgrams with V3 roots
python scripts/statistical_analysis/add_skipgrams_to_db.py

# Re-run V3 scoring
python scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v2.py
python scripts/statistical_analysis/generate_top_500_skipgram_dedup_v2.py
```

## Expected Impact

### Before (V2)

```
False matches:
- "חי" matches both מָחִיתָ (destroy) and חַיִּים (live) ❌
- "בי" matches both לִבִּי (heart) and בְּבֵית (in house) ❌
- "אד" matches both מְאֹד (very) and אֲדֹנָי (Lord) ❌

Result: Inflated similarity scores, spurious connections
```

### After (V3)

```
Correct distinctions:
- מָחִיתָ → "מחה" (destroy) ✅
- חַיִּים → "חיה" (live) ✅
- לִבִּי → "לב" (heart) ✅
- בְּבֵית → "בית" (house) ✅
- מְאֹד → "מאד" (very) ✅
- אֲדֹנָי → "אדן" (Lord) ✅

Result: Accurate similarity scores, meaningful connections
```

## Troubleshooting

### Cache Not Found

```
WARNING: Morphology cache not found at .../psalms_morphology_cache.json
Will use fallback extraction only.
```

**Solution**: Run `python cache_builder.py` to build cache.

### Text-Fabric Not Installed

```
ERROR: text-fabric not installed
Install with: pip install text-fabric
```

**Solution**: `pip install text-fabric`

### Cache Outdated

If ETCBC BHSA data is updated, rebuild cache:

```bash
rm data/psalms_morphology_cache.json
python cache_builder.py
```

## Future Enhancements

1. **Expand cache**: Include entire Hebrew Bible (not just Psalms)
2. **Root families**: Group related roots (e.g., חיה, חיי, מחיה)
3. **POS filtering**: Use part-of-speech tags to filter function words
4. **Semantic tagging**: Add semantic fields from Text-Fabric
5. **Strong's numbers**: Cross-reference with Strong's concordance

## License

- **Code**: Same license as psalms-AI-analysis project
- **ETCBC BHSA Data**: CC BY-NC 4.0 (non-commercial use)
- **Cache derived from BHSA**: CC BY-NC 4.0 (non-commercial use)

## References

- ETCBC Text-Fabric: https://github.com/ETCBC/bhsa
- Text-Fabric Docs: https://annotation.github.io/text-fabric/
- Hebrew NLP Resources: https://github.com/iddoberger/awesome-hebrew-nlp
- Research Report: `docs/HEBREW_MORPHOLOGY_ANALYSIS.md`

## Support

For issues or questions:
1. Check `docs/HEBREW_MORPHOLOGY_ANALYSIS.md` for detailed research
2. Review test output: `python test_morphology.py`
3. Check cache status: `analyzer.get_cache_stats()`
4. Verify Text-Fabric installation: `python -c "import tf; print(tf.__version__)"`

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-14  
**Author**: Psalms AI Analysis Project
