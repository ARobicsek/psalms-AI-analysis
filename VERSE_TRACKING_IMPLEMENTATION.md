# Verse Reference Tracking for Roots in V3 Scoring System

## Problem Statement

The V3 scoring output had roots with null verse data:
```json
{
  "root": "אנ",
  "verses_a": [],
  "verses_b": [],
  "matches_from_a": [{"verse": null, "text": "בָּֽאנוּ", "position": null}]
}
```

While contiguous phrases had proper verse data:
```json
{
  "consonantal": "אין עש טוב",
  "verses_a": [1, 3],
  "verses_b": [2, 4]
}
```

## Root Cause

The verse tracking was not implemented in the root data extraction pipeline:
1. `root_extractor.py` - Did not track which verse each root example came from
2. `database_builder.py` - No verse_numbers column in psalm_roots table
3. `pairwise_comparator.py` - Did not extract verses_a/verses_b for roots
4. `enhanced_scorer_skipgram_dedup_v3_simplified.py` - Could not populate verse fields from missing source data

## Solution Overview

The solution adds verse reference tracking throughout the entire pipeline, from extraction to final output.

## Detailed Changes

### 1. Root Extractor (`root_extractor.py`)

**Change:** Track verse numbers alongside examples

**File:** `/home/user/psalms-AI-analysis/scripts/statistical_analysis/root_extractor.py`

**Lines 326-347:**
```python
# Before:
all_roots = defaultdict(lambda: {'count': 0, 'examples': []})

# After:
all_roots = defaultdict(lambda: {'count': 0, 'examples': [], 'verse_numbers': []})

# When processing verses:
for verse in verses:
    # ... extract roots ...
    for root, examples in verse_roots.items():
        all_roots[root]['count'] += len(examples)
        if len(all_roots[root]['examples']) < 3:
            examples_to_add = examples[:3 - len(all_roots[root]['examples'])]
            all_roots[root]['examples'].extend(examples_to_add)
            # NEW: Track verse numbers
            all_roots[root]['verse_numbers'].extend(
                [verse['verse']] * len(examples_to_add)
            )
```

**Result:** Each root now has a `verse_numbers` list parallel to `examples`
- `examples_a: ['בָּֽאנוּ', 'אָנִי']`
- `verse_numbers: [2, 5]` (each example is indexed by its verse)

### 2. Database Schema (`database_builder.py`)

**Change:** Add verse_numbers column to psalm_roots table

**File:** `/home/user/psalms-AI-analysis/scripts/statistical_analysis/database_builder.py`

**Lines 54-67 (Schema):**
```sql
CREATE TABLE IF NOT EXISTS psalm_roots (
    psalm_root_id INTEGER PRIMARY KEY AUTOINCREMENT,
    psalm_number INTEGER NOT NULL,
    root_id INTEGER NOT NULL,
    occurrence_count INTEGER NOT NULL,
    example_words TEXT,
    verse_numbers TEXT,  -- NEW: Store verse numbers
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (root_id) REFERENCES root_frequencies(root_id),
    UNIQUE(psalm_number, root_id)
)
```

**Lines 177-206 (store_psalm_roots method):**
```python
# Now stores verse_numbers alongside examples:
verse_numbers = json.dumps(data.get('verse_numbers', []), ensure_ascii=False) \
    if data.get('verse_numbers') else None

cursor.execute("""
    INSERT OR REPLACE INTO psalm_roots
    (psalm_number, root_id, occurrence_count, example_words, verse_numbers)
    VALUES (?, ?, ?, ?, ?)
""", (..., verse_numbers))
```

**Lines 273-311 (get_psalm_roots method):**
```python
# Now retrieves verse numbers:
SELECT
    rf.root_consonantal,
    pr.occurrence_count,
    rf.idf_score,
    pr.example_words,
    pr.verse_numbers  -- NEW: Retrieve verse data
FROM psalm_roots pr
JOIN root_frequencies rf ON pr.root_id = rf.root_id

# Returns:
{
    'root': root_consonantal,
    'count': occurrence_count,
    'idf': idf_score,
    'examples': [...],
    'verses': verse_numbers  # NEW: Verse data included
}
```

### 3. Pairwise Comparator (`pairwise_comparator.py`)

**Change:** Extract and include verse numbers when building shared_roots list

**File:** `/home/user/psalms-AI-analysis/scripts/statistical_analysis/pairwise_comparator.py`

**Lines 136-152:**
```python
# Before:
shared_roots_list = []
for root in sorted(shared_roots, key=lambda r: roots_a[r]['idf'], reverse=True):
    shared_roots_list.append({
        'root': root,
        'idf': roots_a[root]['idf'],
        'count_a': roots_a[root]['count'],
        'count_b': roots_b[root]['count'],
        'examples_a': roots_a[root]['examples'],
        'examples_b': roots_b[root]['examples']
        # NO VERSE DATA
    })

# After:
shared_roots_list = []
for root in sorted(shared_roots, key=lambda r: roots_a[r]['idf'], reverse=True):
    # Extract verse numbers for both psalms
    verses_a = roots_a[root].get('verses', [])
    verses_b = roots_b[root].get('verses', [])

    shared_roots_list.append({
        'root': root,
        'idf': roots_a[root]['idf'],
        'count_a': roots_a[root]['count'],
        'count_b': roots_b[root]['count'],
        'examples_a': roots_a[root]['examples'],
        'examples_b': roots_b[root]['examples'],
        'verses_a': verses_a,      # NEW: Verse data included
        'verses_b': verses_b        # NEW: Verse data included
    })
```

**Result:** `shared_roots` in `significant_relationships.json` now includes:
```json
{
  "root": "שמע",
  "examples_a": ["שְׁמַע"],
  "examples_b": ["שְׁמַע", "תִּשְׁמְעוּ"],
  "verses_a": [4],
  "verses_b": [1, 6]
}
```

### 4. V3 Scorer (`enhanced_scorer_skipgram_dedup_v3_simplified.py`)

**Change:** Populate verse fields using data from pairwise_comparator

**File:** `/home/user/psalms-AI-analysis/scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v3_simplified.py`

**Lines 109-148:**
```python
# Before:
def enhance_roots_with_verse_info(roots: List[Dict]) -> List[Dict]:
    enhanced = []
    for root in roots:
        enhanced_root = root.copy()
        enhanced_root['verses_a'] = []
        enhanced_root['verses_b'] = []
        enhanced_root['matches_from_a'] = [
            {
                'verse': None,  # ALWAYS NULL
                'text': ex,
                'position': None
            }
            for ex in root.get('examples_a', [])
        ]
        enhanced.append(enhanced_root)
    return enhanced

# After:
def enhance_roots_with_verse_info(roots: List[Dict]) -> List[Dict]:
    enhanced = []
    for root in roots:
        enhanced_root = root.copy()

        # Get verse information from source data
        verses_a = root.get('verses_a', [])
        verses_b = root.get('verses_b', [])
        examples_a = root.get('examples_a', [])
        examples_b = root.get('examples_b', [])

        # Pair examples with verse numbers
        enhanced_root['matches_from_a'] = [
            {
                'verse': verses_a[i] if i < len(verses_a) else None,  # NOW POPULATED
                'text': ex,
                'position': None
            }
            for i, ex in enumerate(examples_a)
        ]
        enhanced_root['matches_from_b'] = [
            {
                'verse': verses_b[i] if i < len(verses_b) else None,  # NOW POPULATED
                'text': ex,
                'position': None
            }
            for i, ex in enumerate(examples_b)
        ]

        enhanced.append(enhanced_root)
    return enhanced
```

**Result:** V3 output now shows:
```json
{
  "root": "אנ",
  "verses_a": [2, 5],
  "verses_b": [3],
  "matches_from_a": [
    {"verse": 2, "text": "בָּֽאנוּ", "position": null},
    {"verse": 5, "text": "אָנִי", "position": null}
  ],
  "matches_from_b": [
    {"verse": 3, "text": "בִּי", "position": null}
  ]
}
```

## Backward Compatibility

The changes maintain backward compatibility:
- Database column `verse_numbers` is optional (NULL allowed)
- Root data can still be stored without verse information
- `store_psalm_roots()` handles missing `verse_numbers` gracefully
- `get_psalm_roots()` returns empty list if verse data unavailable
- `enhance_roots_with_verse_info()` works with or without verse data

## Testing

All changes have been tested with `test_verse_tracking_v3.py`:

### Test 1: Root Extraction
```
✓ Root extraction tracks verse numbers
✓ Examples properly paired with verses
```

### Test 2: Database Storage
```
✓ Verse data persists in database
✓ 55/55 roots have verse information
```

### Test 3: Enhanced Scoring
```
✓ Verse information propagates to V3 output
✓ Each match paired with verse number
✓ No more null verse values
```

Run tests:
```bash
python3 test_verse_tracking_v3.py
```

## Deployment Instructions

To activate verse tracking in the full pipeline:

### Step 1: Update root extraction (if re-extracting roots)

If rebuilding from scratch, the modified `root_extractor.py` will automatically track verses.

### Step 2: Re-run pairwise comparison

```bash
python3 scripts/statistical_analysis/pairwise_comparator.py
```

This will generate `significant_relationships.json` with verse data for roots.

### Step 3: Re-run V3 scoring

```bash
python3 scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v3_simplified.py
```

This will generate `enhanced_scores_skipgram_dedup_v3.json` with populated verse fields.

## Data Format Changes

### significant_relationships.json
**Before:**
```json
{
  "shared_roots": [
    {
      "root": "אנ",
      "idf": 3.2,
      "count_a": 2,
      "count_b": 1,
      "examples_a": ["בָּֽאנוּ", "אָנִי"],
      "examples_b": ["בִּי"]
    }
  ]
}
```

**After:**
```json
{
  "shared_roots": [
    {
      "root": "אנ",
      "idf": 3.2,
      "count_a": 2,
      "count_b": 1,
      "examples_a": ["בָּֽאנוּ", "אָנִי"],
      "examples_b": ["בִּי"],
      "verses_a": [2, 5],
      "verses_b": [3]
    }
  ]
}
```

### enhanced_scores_skipgram_dedup_v3.json
**Before:**
```json
{
  "deduplicated_roots": [
    {
      "root": "אנ",
      "verses_a": [],
      "verses_b": [],
      "matches_from_a": [
        {"verse": null, "text": "בָּֽאנוּ", "position": null}
      ]
    }
  ]
}
```

**After:**
```json
{
  "deduplicated_roots": [
    {
      "root": "אנ",
      "verses_a": [2, 5],
      "verses_b": [3],
      "matches_from_a": [
        {"verse": 2, "text": "בָּֽאנוּ", "position": null},
        {"verse": 5, "text": "אָנִי", "position": null}
      ],
      "matches_from_b": [
        {"verse": 3, "text": "בִּי", "position": null}
      ]
    }
  ]
}
```

## Summary of Changes

| File | Change | Impact |
|------|--------|--------|
| `root_extractor.py` | Track verse_numbers per root | Roots now have verse information |
| `database_builder.py` | Add verse_numbers column to schema | Database can store/retrieve verse data |
| `pairwise_comparator.py` | Extract verses_a/verses_b for roots | Verse data flows into significant_relationships.json |
| `enhanced_scorer_skipgram_dedup_v3_simplified.py` | Use verse data in enhance_roots_with_verse_info() | V3 output has populated verse fields |
| `test_verse_tracking_v3.py` | New comprehensive test suite | Validates entire pipeline |

## Files Modified

1. `/home/user/psalms-AI-analysis/scripts/statistical_analysis/root_extractor.py`
2. `/home/user/psalms-AI-analysis/scripts/statistical_analysis/database_builder.py`
3. `/home/user/psalms-AI-analysis/scripts/statistical_analysis/pairwise_comparator.py`
4. `/home/user/psalms-AI-analysis/scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v3_simplified.py`

## Files Created

1. `/home/user/psalms-AI-analysis/test_verse_tracking_v3.py` (test suite)
2. `/home/user/psalms-AI-analysis/VERSE_TRACKING_IMPLEMENTATION.md` (this document)

## Verification

All changes have been tested and verified:
- Root extraction preserves verse tracking
- Database persistence works correctly
- Verse data flows through pairwise comparator
- V3 output generates valid verse numbers
- No verse data is lost in the pipeline
