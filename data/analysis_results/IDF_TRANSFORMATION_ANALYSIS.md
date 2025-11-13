# IDF Score Distribution Analysis: Linear vs Exponential Transformation

## Executive Summary

**Current situation**: The IDF score distribution shows significant bunching at the high end (50th-95th percentiles all at 5.0106).

**Exponential transformation result**: Switching from linear IDF to e^IDF makes **almost no difference**:
- Current method (linear IDF): **11,001** significant relationships (100.0%)
- Exponential method (e^IDF): **11,000** significant relationships (99.99%)
- Only **1 pair** changes: Psalms 131 & 150 (goes from significant to non-significant)

## The Bunching Problem

From `root_statistics.json`:
```json
{
  "total_roots": 3327,
  "avg_idf": 4.333,
  "min_idf": 0.041,
  "max_idf": 5.011,
  "idf_percentiles": {
    "25th": 3.912,
    "50th": 5.011,    ← BUNCHED
    "75th": 5.011,    ← BUNCHED
    "90th": 5.011,    ← BUNCHED
    "95th": 5.011     ← BUNCHED
  }
}
```

**Interpretation**: Over half of all roots (50th percentile and above) have the maximum IDF score of 5.011. This represents **hapax legomena** - roots that appear in only one psalm each.

**Why this happens**:
- IDF = log(N / df) where N = 150 psalms, df = document frequency
- For hapax legomena: IDF = log(150/1) = 5.0106
- Since we have 1,558 hapax legomena (47% of all roots), half the distribution is bunched at max IDF

## Why Exponential Transformation Doesn't Help

### The Math

Current method calculates weighted score:
```
weighted_score = Σ IDF(root_i) for shared roots
```

Exponential method would calculate:
```
weighted_score = Σ e^IDF(root_i) for shared roots
```

### The Problem

Exponential transformation **amplifies** differences rather than spreading them out:

| IDF Score | Linear | Exponential (e^IDF) | Ratio |
|-----------|--------|---------------------|-------|
| 0.041 (common) | 0.04 | 1.04 | - |
| 3.912 (25th percentile) | 3.91 | 50.0 | 48x larger |
| 5.011 (hapax legomenon) | 5.01 | 150.0 | 145x larger |

**Result**: Rare words become **vastly** more dominant with exponential weighting, but this doesn't solve the bunching problem - it makes it worse!

## Why So Few Relationships Change

The significance test uses **two criteria** (line 134 of pairwise_comparator.py):
```python
is_significant = (pvalue < 0.01) or (z_score > 3.0)
```

The **hypergeometric p-value** is based on the **count** of shared roots, NOT the weighted score:
- N = total roots in Psalter (3,327)
- K = roots in Psalm A
- n = roots in Psalm B
- k = shared roots count

This count-based test is identical for both methods, so most relationships maintain the same significance.

Only relationships that:
1. Have p-value close to the 0.01 threshold, AND
2. Depend on the z-score (weighted) criterion

...will change. This is very rare.

## The One Difference: Psalms 131 & 150

| Metric | Current Method | Exponential Method |
|--------|---------------|-------------------|
| Shared roots | 2 | 2 |
| p-value | 0.0146 | 0.0146 (same) |
| z-score | **3.40** ✓ | **0.34** ✗ |
| Weighted score | 2.48 | 9.76 |
| **Significant?** | **YES** (z > 3.0) | **NO** (p > 0.01 AND z < 3.0) |

**Why the z-score drops with exponential**:
- With exponential, the expected weighted score increases dramatically
- The variance in exponential IDF scores is much larger
- This causes the observed score to be LESS unusual relative to expectation
- Result: z-score drops from 3.40 to 0.34

## Current Method Statistics

### Overall Distribution
- Total pairs compared: 11,175
- Significant relationships: 11,001 (98.4%)
- Non-significant: 174 (1.6%)

### Top Relationships (p-value ranking)
1. **Psalms 14 & 53**: p=1.11e-80 (virtually identical, 45 shared roots, 73 shared phrases)
2. **Psalms 60 & 108**: p=1.15e-70 (composite psalm, 54 shared roots, 82 shared phrases)
3. **Psalms 40 & 70**: p=9.16e-53 (shared passage, 38 shared roots, 40 shared phrases)
4. **Psalms 78 & 105**: p=1.91e-43 (historical narratives, 93 shared roots, 8 shared phrases)
5. **Psalms 115 & 135**: p=2.86e-40 (Hallel psalms, 38 shared roots, 46 shared phrases)

### Psalm-Level Statistics

Each psalm has significant relationships with approximately 146-149 other psalms:
- **Highest**: Psalm 18 (149 matches = 99.3% of all psalms)
- **Lowest**: Psalm 150 (77 matches = 51.3% of all psalms)
  - Psalm 150 is very short (6 verses, mostly "Hallelujah!")
  - Limited vocabulary means fewer significant matches

## Interpretation & Recommendations

### Why 98.4% of Pairs Are Significant

This is **expected and correct** for a religious poetry corpus:

1. **Common liturgical vocabulary**: All Psalms share core terms (יהו, אל, כי, על, כל)
2. **Genre consistency**: Hebrew poetry with similar themes
3. **Shared authorship**: Davidic/Levitical vocabulary patterns
4. **Moderate threshold**: p < 0.01 is appropriate but captures most relationships

### The Bunching Is Not a Bug

The bunching at IDF = 5.011 represents a **real linguistic phenomenon**:
- 1,558 roots (47%) appear in only one psalm (hapax legomena)
- These are genuinely rare and distinctive vocabulary
- They SHOULD all have the same IDF score (maximum rarity)

### Alternative Approaches

If you want to reduce the number of significant relationships or improve discrimination:

#### Option 1: More Stringent Threshold
Change p-value threshold from 0.01 to 0.001 or lower:
```python
is_significant = (pvalue < 0.001) or (z_score > 3.0)
```
**Expected result**: ~4,268 relationships (down from 11,001)

#### Option 2: Focus on Phrase Matching
Shared multi-word phrases are more distinctive than shared roots:
- Already implemented in Session 91
- 8,888 shared phrases identified
- Psalms 14 & 53 share 73 phrases (high duplication signal)
- Psalms 78 & 105 share only 8 phrases (thematic similarity, not duplication)

#### Option 3: Combine Root Count + Phrase Count
Create composite significance test:
```python
is_significant = (root_pvalue < 0.01) AND (phrase_pvalue < 0.01)
```
This would be more selective.

#### Option 4: Root Clustering
Group roots by semantic field before calculating overlap:
- Cluster synonyms/related roots together
- Weight clusters rather than individual roots
- Reduces noise from common vocabulary

#### Option 5: Accept Current Results
The 98.4% significant rate may be appropriate:
- Represents genuine linguistic connections
- Most Psalms DO share significant vocabulary
- Focus on **ranking** relationships rather than binary significance
- Use p-value and phrase count for prioritization

## Detailed Results

### Complete Psalm-by-Psalm Table
See: `data/analysis_results/idf_comparison_table.txt`

Shows all 150 psalms with their significant matches under each method.

### Summary Statistics
See: `data/analysis_results/idf_comparison_summary.json`

Contains:
- Overall counts and percentages
- Example relationships that differ between methods
- Detailed statistics for both approaches

## Conclusion

**The exponential transformation (e^IDF) does NOT solve the bunching problem.**

The distribution bunching at IDF = 5.011 represents real linguistic data (hapax legomena) and should not be "smoothed out" artificially. The exponential transformation amplifies differences but doesn't change statistical significance for 99.99% of relationships.

**Recommendation**: Keep the current linear IDF method and consider:
1. Using more stringent thresholds (p < 0.001) to identify the strongest relationships
2. Prioritizing relationships with high phrase overlap (not just root overlap)
3. Accepting the 98.4% significance rate as reflecting genuine linguistic connections in religious poetry

The phrase matching implemented in Session 91 provides much better discrimination than any IDF transformation could achieve.
