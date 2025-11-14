# Hebrew Morphology V3 Integration Plan

## Overview

This document outlines the step-by-step plan for integrating morphological analysis into the V3 statistical analysis pipeline.

## Current State (V2)

**Root Extraction**: Naive string manipulation
- Location: `scripts/statistical_analysis/root_extractor.py`
- Method: Strip common prefixes (ה, ו, ב, כ, ל, מ, ש) and suffixes (י, ך, ו, ה, etc.)
- Problem: False positives (e.g., "חי" matches both מָחִיתָ and חַיִּים)

**Usage**:
- `root_extractor.py` → Used by frequency_analyzer, pairwise_comparator
- `skipgram_extractor.py` → Currently uses raw consonantal (inconsistent with root extraction)

## Target State (V3)

**Root Extraction**: Morphologically-aware
- Location: `src/hebrew_analysis/morphology.py`
- Method: ETCBC cache lookup + improved fallback
- Benefit: Accurate roots, fewer false positives

## Integration Steps

### Phase 1: Setup and Validation (Week 1)

#### Step 1.1: Install Dependencies

```bash
cd /home/user/psalms-AI-analysis
pip install text-fabric
```

**Verification**:
```bash
python -c "import tf; print(f'Text-Fabric {tf.__version__} installed')"
```

**Expected output**: `Text-Fabric 12.x.x installed`

#### Step 1.2: Build Morphology Cache

```bash
cd src/hebrew_analysis
python cache_builder.py
```

**First run**: Downloads BHSA data (~100MB), takes ~2 minutes  
**Subsequent runs**: ~10 seconds

**Verification**:
```bash
ls -lh data/psalms_morphology_cache.json
```

**Expected output**: `~50KB` file created

#### Step 1.3: Run Proof of Concept Tests

```bash
python test_morphology.py
```

**Expected output**:
```
✅ PASS: Different roots extracted ('מחה' vs 'חיה')
✅ PASS: Different roots extracted ('לב' vs 'בית')
✅ PASS: Different roots extracted ('מאד' vs 'אדן')

🎉 ALL TESTS PASSED!
```

**If tests fail**: Cache may not be built correctly. Check logs.

### Phase 2: Code Integration (Week 1-2)

#### Step 2.1: Update root_extractor.py

**Option A: Minimal Change (Recommended for V3)**

Replace the `extract_root()` method:

```python
# In scripts/statistical_analysis/root_extractor.py

# Add import at top
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from hebrew_analysis.morphology import extract_morphological_root

class RootExtractor:
    # ... existing code ...
    
    def extract_root(self, word: str) -> str:
        """
        Extract the root form of a Hebrew word using morphological analysis.
        
        V3: Uses ETCBC morphological data for accuracy.
        """
        if not word or not word.strip():
            return ''
        
        # Use morphological extraction
        root = extract_morphological_root(word)
        
        # Quality check: minimum length
        if len(root) < 2:
            return self.normalize_word(word)
        
        return root
```

**Testing**:
```bash
cd scripts/statistical_analysis
python root_extractor.py
```

**Expected**: Psalm 23 analysis with morphological roots.

**Option B: Full Replacement (Alternative)**

Use the enhanced extractor directly:

```python
# In scripts where RootExtractor is used:

# Old:
from scripts.statistical_analysis.root_extractor import RootExtractor

# New:
from src.hebrew_analysis.root_extractor_v2 import EnhancedRootExtractor as RootExtractor
```

#### Step 2.2: Update skipgram_extractor.py

**Current Issue**: Skipgrams use raw consonantal, contiguous phrases use root extraction.

**Fix**: Make skipgrams use root extraction too.

```python
# In scripts/statistical_analysis/skipgram_extractor.py

# Add import
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from hebrew_analysis.morphology import extract_morphological_root

class SkipgramExtractor:
    # In extract_skipgrams() method:
    
    # Old:
    word_consonantal = word['consonantal']
    
    # New:
    word_consonantal = extract_morphological_root(word['hebrew'])
```

**Testing**:
```bash
cd scripts/statistical_analysis
python skipgram_extractor.py
```

#### Step 2.3: Update Other Analysis Scripts

Check if these scripts need updates:

- `frequency_analyzer.py` → Uses RootExtractor (automatically updated if Step 2.1 done)
- `pairwise_comparator.py` → Uses RootExtractor (automatically updated)
- `enhanced_scorer.py` → Uses roots from database (rebuild needed)

### Phase 3: Database Rebuild (Week 2)

#### Step 3.1: Backup Current Data

```bash
cd /home/user/psalms-AI-analysis
mkdir -p backups/v2
cp -r database backups/v2/
cp -r outputs backups/v2/
```

#### Step 3.2: Rebuild Concordance with V3 Roots

```bash
# This will use the updated root_extractor.py
python scripts/rebuild_concordance_with_maqqef_split.py
```

**Expected**: New concordance table with V3 roots.

**Verification**:
```bash
sqlite3 database/statistical_analysis.db "SELECT COUNT(*) FROM concordance_v3"
```

**Expected output**: ~312,000 entries

#### Step 3.3: Rebuild Skipgrams with V3 Roots

```bash
cd scripts/statistical_analysis
python add_skipgrams_to_db.py
```

**Expected**: Skipgrams now use morphological roots (consistent with contiguous).

**Verification**:
```bash
sqlite3 database/statistical_analysis.db "SELECT COUNT(*) FROM skipgrams_v3"
```

#### Step 3.4: Re-run V3 Scoring

```bash
# Full pipeline
python enhanced_scorer_skipgram_dedup_v2.py
python generate_top_500_skipgram_dedup_v2.py
```

**Expected**: New scoring with accurate morphology.

**Verification**:
```bash
ls -lh outputs/top_500_skipgram_dedup_v2.json
```

### Phase 4: Validation (Week 2-3)

#### Step 4.1: Compare V2 vs V3 Results

Create comparison script:

```python
# scripts/statistical_analysis/compare_v2_v3.py

import json

# Load V2 results
with open('outputs/top_500_v2.json') as f:
    v2_results = json.load(f)

# Load V3 results
with open('outputs/top_500_skipgram_dedup_v2.json') as f:
    v3_results = json.load(f)

# Compare top 20
print("Top 20 Connections Comparison:")
print("=" * 80)
for i in range(20):
    v2 = v2_results[i]
    v3 = v3_results[i]
    print(f"\nRank {i+1}:")
    print(f"  V2: Psalms {v2['psalm1']}-{v2['psalm2']}, Score: {v2['score']:.4f}")
    print(f"  V3: Psalms {v3['psalm1']}-{v3['psalm2']}, Score: {v3['score']:.4f}")
```

#### Step 4.2: Validate False Positive Fixes

Check that false positive examples are now handled correctly:

```python
# scripts/statistical_analysis/validate_false_positives.py

from src.hebrew_analysis.morphology import extract_morphological_root

test_cases = [
    ("מָחִיתָ", "חַיִּים"),  # Should be different roots
    ("לִבִּי", "בְּבֵית"),    # Should be different roots
    ("מְאֹד", "אֲדֹנָי"),    # Should be different roots
]

for word1, word2 in test_cases:
    root1 = extract_morphological_root(word1)
    root2 = extract_morphological_root(word2)
    
    status = "✅ PASS" if root1 != root2 else "❌ FAIL"
    print(f"{status}: {word1} → {root1}, {word2} → {root2}")
```

#### Step 4.3: Manual Review

Spot-check top 100 connections:
- Do the shared roots make sense linguistically?
- Are there still obvious false positives?
- Has recall improved (finding more meaningful connections)?

### Phase 5: Performance Optimization (Week 3)

#### Step 5.1: Profile Performance

```python
import cProfile
import pstats

cProfile.run('extractor.extract_psalm_roots(23)', 'profile_stats')
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative').print_stats(20)
```

**Expected bottlenecks**: Database queries (not morphology)

#### Step 5.2: Optimize if Needed

If morphology is a bottleneck:

1. **Pre-load cache**: Load once at startup
2. **Batch processing**: Process multiple words at once
3. **Parallel processing**: Use multiprocessing for large datasets

#### Step 5.3: Memory Profiling

```python
from memory_profiler import profile

@profile
def extract_all_psalms():
    for i in range(1, 151):
        extractor.extract_psalm_roots(i)
```

**Expected memory**: ~100MB (cache + database connections)

### Phase 6: Documentation and Cleanup (Week 3)

#### Step 6.1: Update Documentation

Files to update:
- `docs/DEVELOPER_GUIDE.md` → Add morphology section
- `docs/TECHNICAL_ARCHITECTURE_SUMMARY.md` → Update root extraction
- `docs/PROJECT_STATUS.md` → Mark V3 morphology complete
- `README.md` → Update with V3 features

#### Step 6.2: Create Migration Guide

`docs/V2_TO_V3_MIGRATION.md`:
- What changed
- How to update custom scripts
- Performance comparison
- Accuracy improvements

#### Step 6.3: Add Tests

Create unit tests:
```bash
mkdir tests/hebrew_analysis
touch tests/hebrew_analysis/test_morphology.py
touch tests/hebrew_analysis/test_cache_builder.py
touch tests/hebrew_analysis/test_root_extractor_v2.py
```

## Rollback Plan

If V3 morphology causes issues:

### Quick Rollback

1. Restore V2 database:
   ```bash
   cp -r backups/v2/database/* database/
   ```

2. Revert code changes:
   ```bash
   git checkout scripts/statistical_analysis/root_extractor.py
   git checkout scripts/statistical_analysis/skipgram_extractor.py
   ```

### Partial Rollback

Keep morphology but use fallback only:

```python
# In morphology.py, disable cache:
class HebrewMorphologyAnalyzer:
    def __init__(self, cache_path=None):
        self.cache = {}  # Don't load cache
        self.cache_loaded = False
```

## Success Criteria

### Must Have (Before Merging to Main)

- ✅ All 3 false positive test cases pass
- ✅ Cache builds successfully (< 1 minute)
- ✅ Integration tests pass (Psalm 23 extracts correctly)
- ✅ V3 scoring completes (< 10 minutes for all 150 Psalms)
- ✅ No regression in top 20 connections (spot-check)

### Should Have (Before Release)

- ✅ Full V2 vs V3 comparison report
- ✅ Performance benchmarks (V3 not slower than V2)
- ✅ Documentation updated
- ✅ Unit tests for morphology package

### Nice to Have (Future)

- 🔄 Expand cache to entire Hebrew Bible
- 🔄 Root family grouping (e.g., חיה, חיי, מחיה)
- 🔄 Semantic tagging integration
- 🔄 Web API for morphology service

## Timeline

| Week | Phase | Tasks | Deliverables |
|------|-------|-------|--------------|
| 1 | Setup & Integration | 1.1-2.3 | Cache built, code integrated |
| 2 | Rebuild & Validation | 3.1-4.2 | V3 database, comparison report |
| 3 | Optimization & Docs | 5.1-6.3 | Performance tuning, documentation |

**Total estimated time**: 3 weeks (assuming part-time work)

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Cache build fails | Low | High | Fallback to improved naive extraction |
| Performance regression | Medium | Medium | Profile and optimize, or use partial cache |
| Accuracy worse than V2 | Low | High | Validate with test cases, rollback if needed |
| License issues (CC BY-NC) | Low | Low | Project is non-commercial research |
| ETCBC data changes | Low | Low | Cache is versioned, can rebuild |

## Dependencies

### Required
- `text-fabric` (>= 12.0.0) - For cache building
- `json` (stdlib) - For cache storage
- `pathlib` (stdlib) - For file operations

### Optional
- `cProfile` (stdlib) - For performance profiling
- `memory_profiler` - For memory profiling
- `pytest` - For unit tests

## Questions to Resolve

1. **Cache scope**: Psalms only or entire Hebrew Bible?
   - **Decision**: Start with Psalms, expand later if needed
   - **Rationale**: Faster builds, sufficient for current use case

2. **Collision handling**: When same consonantal has multiple lemmas?
   - **Decision**: Use first occurrence (frequency-based would be better)
   - **Future**: Weight by frequency in Psalms

3. **Fallback strictness**: How aggressive should filtering be?
   - **Decision**: Conservative (minimum length = 2, function word protection)
   - **Rationale**: Prefer false negatives to false positives

4. **Integration approach**: Minimal change or full replacement?
   - **Decision**: Minimal change (Option A in Step 2.1)
   - **Rationale**: Less risk, easier testing, backwards compatible

## Contact

For questions or issues during integration:
- Review: `docs/HEBREW_MORPHOLOGY_ANALYSIS.md`
- Test: `python src/hebrew_analysis/test_morphology.py`
- Check logs: `logging.basicConfig(level=logging.DEBUG)`

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-14  
**Status**: Ready for implementation
