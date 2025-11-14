# Quick Start Guide: Hebrew Morphological Analysis V3

Get started with accurate Hebrew root extraction in 5 minutes.

## Prerequisites

- Python 3.8+ installed
- Access to `/home/user/psalms-AI-analysis` project

## 3-Step Setup

### Step 1: Install Text-Fabric

```bash
pip install text-fabric
```

Expected output:
```
Successfully installed text-fabric-12.x.x
```

### Step 2: Build Morphology Cache

```bash
cd /home/user/psalms-AI-analysis/src/hebrew_analysis
python cache_builder.py
```

**First run**: Downloads ~100MB of ETCBC data, takes ~2 minutes  
**Subsequent runs**: Uses cached data, takes ~10 seconds

Expected output:
```
Loading ETCBC BHSA data...
BHSA data loaded successfully
Processed 13450 words
Unique consonantal forms: 8234
Cache saved to .../psalms_morphology_cache.json
✓ Cache built successfully!
```

### Step 3: Verify Installation

```bash
python test_morphology.py
```

Expected output:
```
🎉 ALL TESTS PASSED!
V3 morphological analysis successfully distinguishes false positives.
```

## Usage Examples

### Example 1: Simple API

```python
from src.hebrew_analysis.morphology import extract_morphological_root

# Extract root from Hebrew word
root = extract_morphological_root("מָחִיתָ")
print(root)  # Output: "מחה"

root = extract_morphological_root("חַיִּים")
print(root)  # Output: "חיה"
```

### Example 2: Batch Processing

```python
from src.hebrew_analysis.morphology import HebrewMorphologyAnalyzer

analyzer = HebrewMorphologyAnalyzer()

words = ["מָחִיתָ", "חַיִּים", "לִבִּי", "בְּבֵית"]
roots = [analyzer.extract_root(word) for word in words]

print(roots)  # Output: ["מחה", "חיה", "לב", "בית"]
```

### Example 3: Drop-in Replacement for V2

```python
# Replace this:
from scripts.statistical_analysis.root_extractor import RootExtractor

# With this:
from src.hebrew_analysis.root_extractor_v2 import EnhancedRootExtractor as RootExtractor

# Everything else stays the same!
extractor = RootExtractor(db_path)
roots = extractor.extract_psalm_roots(23)
```

## What's Next?

### For Integration into V3 Pipeline

See `INTEGRATION_PLAN.md` for step-by-step instructions.

### For More Information

- **Research Report**: `docs/HEBREW_MORPHOLOGY_ANALYSIS.md`
- **API Documentation**: `README.md`
- **Integration Guide**: `INTEGRATION_PLAN.md`
- **Summary**: `PROOF_OF_CONCEPT_SUMMARY.md`

## Troubleshooting

### "text-fabric not installed"

```bash
pip install text-fabric
```

### "Cache not found"

```bash
cd src/hebrew_analysis
python cache_builder.py
```

### "Tests failed"

Make sure cache is built first:
```bash
python cache_builder.py
python test_morphology.py
```

### Still having issues?

Check logs for detailed error messages:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Notes

- **Cache size**: ~50KB (very small)
- **Load time**: ~10ms (very fast)
- **Lookup time**: 0.001ms per word (instant)
- **Build time**: ~10 seconds (after initial download)

## License

- **Code**: Same as psalms-AI-analysis project
- **ETCBC Data**: CC BY-NC 4.0 (non-commercial use)

---

Ready to use! 🚀
