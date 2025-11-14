# V3 Quick Start Guide

## TL;DR

```bash
cd /home/user/psalms-AI-analysis

# Step 1: Generate V3 scores (takes ~3-4 minutes)
python3 scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v3_simplified.py

# Step 2: Generate top 500 export (takes ~10 seconds)
python3 scripts/statistical_analysis/generate_top_500_skipgram_dedup_v3.py

# Step 3: View results
head -100 data/analysis_results/top_500_connections_skipgram_dedup_v3.json
```

## What's New in V3?

**Verse-level details for all matches**

Before (V2):
- "Phrase X appears in both psalms"
- "It's in verses [1, 3] and [2, 4]"

Now (V3):
- "Phrase X appears in Psalm 14 verses 1 and 3"
- "Here's the actual Hebrew text for each occurrence"
- "In Psalm 14:1 it appears as: אֵ֣ין עֹֽשֵׂה טֽוֹב׃"
- "In Psalm 14:3 it appears as: אֵ֣ין עֹֽשֵׂה טֽוֹב׃"

## Example Output

### Rank 1: Psalms 14-53 (Score: 894.95)

**Sample Phrase**:
```json
{
  "consonantal": "אין עש טוב",
  "hebrew": "אֵ֣ין עֹֽשֵׂה טֽוֹב׃",
  "length": 3,
  "verses_a": [1, 3],
  "verses_b": [2, 4],
  "matches_from_a": [
    {"verse": 1, "text": "אֵ֣ין עֹֽשֵׂה טֽוֹב׃"},
    {"verse": 3, "text": "אֵ֣ין עֹֽשֵׂה טֽוֹב׃"}
  ],
  "matches_from_b": [
    {"verse": 2, "text": "אֵ֣ין עֹֽשֵׂה טֽוֹב׃"},
    {"verse": 4, "text": "אֵ֣ין עֹֽשֵׂה טֽוֹב׃"}
  ]
}
```

## Output Files

**enhanced_scores_skipgram_dedup_v3.json** (92.75 MB)
- All 11,001 psalm relationships with verse details
- Complete deduplication statistics
- Verse-level information for every match

**top_500_connections_skipgram_dedup_v3.json** (9.38 MB)
- Top 500 strongest connections
- Ranked by final_score
- Easy to browse and analyze

## Quick Analysis

### View Rank 1 (Psalms 14-53)

```python
import json

with open('data/analysis_results/top_500_connections_skipgram_dedup_v3.json', 'r') as f:
    top_500 = json.load(f)

rank1 = top_500[0]
print(f"Rank 1: Psalms {rank1['psalm_a']}-{rank1['psalm_b']}")
print(f"Score: {rank1['final_score']:.2f}")
print(f"Contiguous phrases: {len(rank1['deduplicated_contiguous_phrases'])}")
print(f"Roots: {len(rank1['deduplicated_roots'])}")

# Show first phrase with verse details
if rank1['deduplicated_contiguous_phrases']:
    phrase = rank1['deduplicated_contiguous_phrases'][0]
    print(f"\nPhrase: {phrase['hebrew']}")
    print(f"Length: {phrase['length']} words")
    print(f"Appears in Psalm {rank1['psalm_a']} verses: {phrase['verses_a']}")
    print(f"Appears in Psalm {rank1['psalm_b']} verses: {phrase['verses_b']}")
    
    # Show Hebrew text for each match
    print("\nMatches in Psalm", rank1['psalm_a'])
    for match in phrase['matches_from_a']:
        print(f"  Verse {match['verse']}: {match['text']}")
```

### Find Specific Psalm Pair

```python
def find_pair(top_500, psalm_a, psalm_b):
    for entry in top_500:
        if entry['psalm_a'] == psalm_a and entry['psalm_b'] == psalm_b:
            return entry
    return None

# Example: Find Psalms 50-82 (should be in top 500)
entry = find_pair(top_500, 50, 82)
if entry:
    print(f"Psalms 50-82: Rank {entry['rank']}, Score {entry['final_score']:.2f}")
else:
    print("Not in top 500")
```

### Export Verse Lists to CSV

```python
import csv

with open('phrase_verses.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Rank', 'Psalm_A', 'Psalm_B', 'Phrase', 'Verses_A', 'Verses_B'])
    
    for entry in top_500[:50]:  # Top 50
        for phrase in entry['deduplicated_contiguous_phrases']:
            writer.writerow([
                entry['rank'],
                entry['psalm_a'],
                entry['psalm_b'],
                phrase['consonantal'],
                ','.join(map(str, phrase['verses_a'])),
                ','.join(map(str, phrase['verses_b']))
            ])

print("Saved to phrase_verses.csv")
```

## What's Maintained from V2?

All V2 features are preserved:

- **IDF filter**: Very common roots (IDF < 0.5) excluded from single root matches
- **Hierarchical deduplication**: 
  - Contiguous phrases deduplicated (remove substrings)
  - Skipgrams deduplicated (remove overlap with contiguous + subpatterns)
  - Roots deduplicated (remove those in phrases)
- **Scoring formula**: Same as V2
- **Statistics**: Complete deduplication stats for every relationship

## Differences from Original V3 Spec

**Simplified approach**: This V3 uses existing verse data from source rather than attempting complex morphological re-matching.

**Position field**: Set to `null` (can be added later if needed with full morphological matching)

**Why simplified?**:
- Original phrase extraction uses complex Hebrew morphology (prefix/suffix stripping)
- Example: "בְּנֵי" → "ני" (removes ב prefix)
- Re-matching would require replicating this exact logic
- Current approach leverages existing verse data, focuses on format enhancement

**What you get**:
- All verse-level information you need for analysis
- Actual Hebrew text for each match
- Verse numbers where matches occur
- Fast, reliable processing

**What's deferred**:
- Exact word position within verse (placeholder: null)
- Can be added later if needed for specific use cases

## Testing

Test the format on Psalms 14-53:

```bash
python3 scripts/statistical_analysis/test_v3_format.py
```

Shows:
- V3 format for contiguous phrases
- V3 format for skipgrams
- V3 format for roots
- Concordance structure from database

## Performance

**Scorer**: ~3-4 minutes for all 11,001 relationships
**Generator**: ~10 seconds for top 500
**Total**: Under 5 minutes to generate all V3 output

## File Sizes

- **Full scores**: 92.75 MB (all 11,001 relationships)
- **Top 500**: 9.38 MB (easy to work with)
- **V2 comparison**: V3 is ~2x larger (due to verse details)

## Common Questions

**Q: Why are positions null?**
A: Simplified V3 focuses on verse-level information. Exact positions would require complex morphological matching that can be added later if needed.

**Q: Can I get exact word positions?**
A: Yes, but it requires importing the root extraction logic and applying morphological stripping. See V3_DELIVERY_SUMMARY.md for details.

**Q: Are the verse lists accurate?**
A: Yes! They come directly from the original phrase extraction that created significant_relationships.json.

**Q: Why don't skipgrams have verse info?**
A: Current skipgram data doesn't include verse information in the source. This can be added when Agent 2's work is integrated.

**Q: Is V3 backward compatible?**
A: Yes! All V2 fields are present. V3 only adds new fields (matches_from_a, matches_from_b).

## Next Steps

1. **Run the scripts** to generate V3 output
2. **Browse top_500_connections_skipgram_dedup_v3.json** to see examples
3. **Write analysis scripts** using the verse-level information
4. **Export to CSV** for spreadsheet analysis
5. **Build visualizations** showing verse distribution patterns

## Support

See also:
- **V3_OUTPUT_FORMAT.md**: Complete format documentation
- **V3_DELIVERY_SUMMARY.md**: Detailed delivery overview and implementation notes
