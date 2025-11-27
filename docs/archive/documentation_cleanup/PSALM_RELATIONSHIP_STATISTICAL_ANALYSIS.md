# Statistical Analysis of Psalm Relationships

## Overview

This document proposes a statistically rigorous methodology for identifying potentially related Psalms based on shared rare word roots and expressions. The goal is to programmatically detect Psalms that share uncommon vocabulary at levels that would be statistically unlikely to occur by chance.

## Executive Summary

**Objective**: Identify Psalm pairs (and n-tuples) that share statistically significant numbers of rare Hebrew word roots/expressions.

**Approach**: Multi-layered statistical analysis combining:
1. **Term Frequency Analysis** - Identify rare vs. common roots across the Psalter
2. **Root Normalization** - Use existing Hebrew text processing for root matching
3. **Statistical Significance Testing** - Hypergeometric test for shared vocabulary
4. **Multi-Psalm Extension** - Generalize to clusters of 3+ related Psalms

**Output**: Database of potential relationships with:
- Psalm pairs/groups
- Shared roots/phrases
- Statistical significance scores (p-values)
- Context for librarian agent inclusion in research packages

---

## Part 1: Theoretical Foundation

### 1.1 Statistical Framework

We model the problem as **sampling without replacement** from a finite population:

- **Population**: All word roots across the 150 Psalms (~10,000-15,000 unique roots)
- **Sample 1**: Roots in Psalm A
- **Sample 2**: Roots in Psalm B
- **Question**: Is the overlap between Sample 1 and Sample 2 larger than expected by chance?

#### Hypergeometric Distribution

For two Psalms A and B:
- Let N = total unique roots in entire Psalter
- Let K = number of unique roots in Psalm A
- Let n = number of unique roots in Psalm B
- Let k = number of shared roots between A and B

The probability of observing **exactly** k shared roots by chance is:

```
P(X = k) = C(K, k) * C(N-K, n-k) / C(N, n)
```

Where C(n,k) is the binomial coefficient "n choose k".

The **p-value** (probability of observing k or more shared roots by chance):

```
p-value = Σ P(X = i) for i = k to min(K, n)
```

**Interpretation**:
- p-value < 0.001: Highly significant relationship (very rare vocabulary shared)
- p-value < 0.01: Significant relationship
- p-value < 0.05: Potentially significant
- p-value ≥ 0.05: Likely coincidental

### 1.2 Weighted Analysis: Rare Words Matter More

Not all shared roots are equally meaningful. Sharing the word "LORD" (יהוה) is trivial; sharing "stronghold" (מעוז) is noteworthy.

We incorporate **rarity weights** using Inverse Document Frequency (IDF):

```
IDF(root) = log(N_psalms / n_psalms_containing_root)
```

**Weighted overlap score**:
```
Weighted_Score(A, B) = Σ IDF(root) for root in (A ∩ B)
```

We then compute a **normalized z-score** by comparing to the expected weighted score under random sampling:

```
z = (observed_score - expected_score) / std_dev
```

This accounts for both the **number** of shared roots and their **rarity**.

### 1.3 Extension to Multi-Psalm Clusters

For 3+ Psalms {A, B, C, ...}:

**Approach 1: Pairwise Analysis**
- Compute all pairwise relationships
- Cluster Psalms if multiple pairs are significant

**Approach 2: Core Vocabulary Analysis**
- Identify roots shared by ALL Psalms in the set
- Test significance of this "core vocabulary"

**Approach 3: Graph-Based Clustering**
- Build a graph where nodes = Psalms, edges = significant relationships
- Use community detection algorithms (e.g., Louvain method)
- Identify clusters of mutually related Psalms

For the initial implementation, we'll focus on **pairwise analysis** (Approach 1) with the ability to aggregate results into clusters.

---

## Part 2: Hebrew Text Processing Strategy

### 2.1 Root Identification

Building on the existing concordance infrastructure:

**Normalization Strategy** (using existing `hebrew_text_processor.py`):
1. **Split on maqqef** - Handle hyphenated words (כִּֽי־הִכִּ֣יתָ → כי + הכית)
2. **Consonantal normalization** - Strip vowels and cantillation (הִכִּ֣יתָ → הכית)
3. **Prefix stripping** - Remove common prefixes (ה, ו, ב, כ, ל, מ)
4. **Suffix stripping** - Remove pronominal suffixes (י, ך, ו, ה, נו, כם, הם, etc.)

**Example**:
- Raw: `וּמֵהַר־קָדְשׁוֹ` (and from His holy mountain)
- After maqqef split: `ומהר` + `קדשו`
- After consonantal: `ומהר` + `קדשו`
- After prefix strip: `הר` + `קדש`
- After suffix strip: `הר` + `קדש`
- **Roots identified**: הר (mountain), קדש (holy)

**Root Equivalence Classes**:
We'll leverage the existing `ConcordanceLibrarian` prefix/suffix variation logic to create equivalence classes:
- All variations of a root (with different prefixes/suffixes) map to the same canonical form
- Example: `מלך`, `המלך`, `ומלך`, `למלך`, `מלכי`, `מלכו` → `מלך`

### 2.2 Phrase Detection

Beyond single roots, we need to detect meaningful **multi-word expressions**:

**N-gram Extraction** (n=2, 3):
- Extract all 2-word and 3-word sequences from each Psalm
- Normalize each word to consonantal root form
- Filter by frequency: keep n-grams that appear in ≤ 10 Psalms (rare phrases)

**Example Phrases**:
- `הר קדש` (holy mountain) - 2-gram
- `מה רבו צרי` (how many are my foes) - 3-gram
- `ה' רעי` (LORD my shepherd) - 2-gram

**Significance Testing**:
Apply the same hypergeometric test to phrase overlap, weighted by phrase rarity.

### 2.3 Handling Ambiguity

**Challenge**: Hebrew consonantal roots can be ambiguous.
- `שמר` could be "guard" or "keep" or "preserve"
- `דבר` could be "word" or "thing" or "speak"

**Solution**: Accept this ambiguity as part of the method.
- We're testing statistical co-occurrence, not semantic analysis
- If two Psalms share ambiguous roots, that's still a lexical relationship
- The synthesis agent/master editor will make final semantic judgments

**Trade-off**: Some false positives (unrelated Psalms sharing common roots) vs. missing true relationships (overly strict matching)
- We err on the side of **inclusion** (lower threshold) since human agents do final filtering

---

## Part 3: Implementation Architecture

### 3.1 File Structure

New files to create (in separate directory to avoid modifying existing code):

```
/scripts/statistical_analysis/
├── __init__.py
├── root_extractor.py          # Extract and normalize roots from Psalms
├── frequency_analyzer.py      # Compute root frequencies and IDF scores
├── pairwise_comparator.py     # Compare all Psalm pairs for significance
├── phrase_analyzer.py         # Detect and analyze shared phrases
├── cluster_detector.py        # Group related Psalms into clusters
├── database_builder.py        # Create and populate relationships database
└── report_generator.py        # Generate reports for librarian consumption

/data/
└── psalm_relationships.db     # New SQLite database for relationships

/tests/statistical_analysis/
├── test_root_extraction.py
├── test_significance.py
└── test_known_relationships.py  # Validate on known related Psalms
```

### 3.2 Database Schema

**New database**: `/data/psalm_relationships.db`

```sql
-- Root frequency data
CREATE TABLE root_frequencies (
    root_id INTEGER PRIMARY KEY,
    root_consonantal TEXT UNIQUE NOT NULL,
    total_occurrences INTEGER NOT NULL,     -- Total times root appears
    psalm_count INTEGER NOT NULL,           -- Number of Psalms containing root
    idf_score REAL NOT NULL                 -- log(150 / psalm_count)
);

-- Roots in each Psalm
CREATE TABLE psalm_roots (
    psalm_root_id INTEGER PRIMARY KEY,
    psalm_number INTEGER NOT NULL,
    root_id INTEGER NOT NULL,
    occurrence_count INTEGER NOT NULL,      -- Times root appears in this Psalm
    example_words TEXT,                     -- JSON: Example Hebrew words with this root
    FOREIGN KEY (root_id) REFERENCES root_frequencies(root_id)
);

-- Phrases in each Psalm
CREATE TABLE psalm_phrases (
    phrase_id INTEGER PRIMARY KEY,
    psalm_number INTEGER NOT NULL,
    phrase_consonantal TEXT NOT NULL,       -- Normalized phrase
    phrase_hebrew TEXT NOT NULL,            -- Original Hebrew (one example)
    phrase_length INTEGER NOT NULL,         -- Number of words (2 or 3)
    occurrence_count INTEGER NOT NULL,
    verse_references TEXT                   -- JSON: List of verses where phrase appears
);

-- Pairwise Psalm relationships
CREATE TABLE psalm_relationships (
    relationship_id INTEGER PRIMARY KEY,
    psalm_a INTEGER NOT NULL,
    psalm_b INTEGER NOT NULL,
    shared_root_count INTEGER NOT NULL,
    total_roots_a INTEGER NOT NULL,
    total_roots_b INTEGER NOT NULL,
    hypergeometric_pvalue REAL NOT NULL,
    weighted_overlap_score REAL NOT NULL,
    z_score REAL NOT NULL,
    is_significant BOOLEAN NOT NULL,        -- p-value < 0.01
    shared_roots_json TEXT NOT NULL,        -- JSON: List of shared roots with IDF scores
    shared_phrases_json TEXT,               -- JSON: List of shared phrases (if any)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (psalm_a < psalm_b)               -- Ensure A < B to avoid duplicates
);

-- Multi-Psalm clusters
CREATE TABLE psalm_clusters (
    cluster_id INTEGER PRIMARY KEY,
    psalm_numbers TEXT NOT NULL,            -- JSON: List of Psalm numbers
    cluster_size INTEGER NOT NULL,
    core_vocabulary_json TEXT NOT NULL,     -- JSON: Roots shared by ALL Psalms
    avg_pairwise_pvalue REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast queries
CREATE INDEX idx_relationships_psalm_a ON psalm_relationships(psalm_a);
CREATE INDEX idx_relationships_psalm_b ON psalm_relationships(psalm_b);
CREATE INDEX idx_relationships_significance ON psalm_relationships(is_significant);
CREATE INDEX idx_psalm_roots_psalm ON psalm_roots(psalm_number);
CREATE INDEX idx_psalm_roots_root ON psalm_roots(root_id);
```

### 3.3 Processing Pipeline

**Step 1: Root Extraction** (`root_extractor.py`)
```python
For each Psalm 1-150:
    1. Load Hebrew text from tanakh.db
    2. Split into words (handle maqqef)
    3. Normalize each word to consonantal form
    4. Strip common prefixes and suffixes
    5. Extract 2-grams and 3-grams
    6. Store in psalm_roots and psalm_phrases tables
```

**Step 2: Frequency Analysis** (`frequency_analyzer.py`)
```python
1. Count total occurrences of each root across all Psalms
2. Count how many Psalms contain each root
3. Compute IDF scores: log(150 / psalm_count)
4. Update root_frequencies table
5. Identify "rare" roots (appear in < 10 Psalms)
```

**Step 3: Pairwise Comparison** (`pairwise_comparator.py`)
```python
For each pair of Psalms (A, B) where A < B:
    1. Retrieve roots for Psalm A and B
    2. Compute intersection (shared roots)
    3. Run hypergeometric test:
        - N = total unique roots in Psalter
        - K = unique roots in A
        - n = unique roots in B
        - k = shared roots
        - p-value = scipy.stats.hypergeom.sf(k-1, N, K, n)
    4. Compute weighted overlap score (sum of IDF scores)
    5. Compute z-score for weighted score
    6. If p-value < 0.01 OR z-score > 3.0:
        - Mark as significant
        - Store in psalm_relationships table
```

**Step 4: Phrase Analysis** (`phrase_analyzer.py`)
```python
For each significant relationship in psalm_relationships:
    1. Retrieve phrases for both Psalms
    2. Find phrase matches (exact consonantal match)
    3. Append phrase data to shared_phrases_json
    4. Update relationship record
```

**Step 5: Cluster Detection** (`cluster_detector.py`)
```python
1. Build graph: nodes = Psalms, edges = significant relationships
2. Run community detection (networkx.algorithms.community.louvain)
3. For each cluster of size ≥ 3:
    - Compute core vocabulary (roots shared by ALL members)
    - Store in psalm_clusters table
```

**Step 6: Report Generation** (`report_generator.py`)
```python
For a given Psalm P:
    1. Query all relationships where psalm_a = P OR psalm_b = P
    2. Sort by significance (p-value ascending)
    3. Format as JSON for librarian consumption:
    {
        "psalm": P,
        "related_psalms": [
            {
                "psalm_number": Q,
                "significance": "very_high|high|moderate",
                "p_value": 0.0001,
                "shared_roots": [
                    {"root": "מעוז", "idf": 4.2, "meaning_hint": "stronghold"},
                    ...
                ],
                "shared_phrases": [
                    {"phrase": "הר קדש", "verse_in_P": "P:X", "verse_in_Q": "Q:Y"},
                    ...
                ]
            },
            ...
        ]
    }
```

---

## Part 4: Statistical Considerations

### 4.1 Multiple Testing Correction

**Problem**: We're testing 11,175 Psalm pairs (150 choose 2). At α=0.05, we'd expect ~558 false positives!

**Solution**: Bonferroni correction
- Adjusted significance threshold: α' = 0.05 / 11,175 ≈ 4.5 × 10⁻⁶
- Or use Benjamini-Hochberg FDR correction (less conservative)

**Implementation**:
```python
from scipy.stats import false_discovery_control

pvalues = [relationship['pvalue'] for relationship in all_relationships]
rejected, adjusted_pvalues = false_discovery_control(pvalues, alpha=0.05)

# Update is_significant based on adjusted_pvalues
```

### 4.2 Handling Psalm Length Variation

**Problem**: Longer Psalms naturally have more roots, inflating overlap.

**Solution**: Normalize by Psalm length
- Use **Jaccard Index**: |A ∩ B| / |A ∪ B|
- Use **overlap coefficient**: |A ∩ B| / min(|A|, |B|)
- Adjust hypergeometric parameters to account for length

**Implementation**:
- Compute both raw overlap and normalized overlap
- Use normalized overlap as a secondary filter (in addition to p-value)

### 4.3 Root Stemming Quality

**Challenge**: Our rule-based prefix/suffix stripping may make errors.

**Quality Control**:
1. **Validation Set**: Manually verify root extraction on 5-10 sample Psalms
2. **Length Heuristics**: Roots < 2 letters are likely errors (discard)
3. **Frequency Check**: Roots appearing in >100 Psalms are likely errors or too common (flag for review)

**Iterative Refinement**:
- Run initial analysis
- Review high-frequency roots
- Adjust prefix/suffix lists
- Re-run analysis

---

## Part 5: Example Walkthrough

### Sample Analysis: Psalm 23 vs. Psalm 27

**Step 1: Root Extraction**

Psalm 23 roots (partial):
- רעה (shepherd), חסר (lack), נאה (pasture), מנוח (rest), נפש (soul), דרך (way), צדק (righteousness), שמע (name), ...

Psalm 27 roots (partial):
- אור (light), ישע (salvation), מעוז (stronghold), חיים (life), פחד (fear), צרר (enemy), קרב (approach), ...

**Step 2: Shared Roots**

Shared:
- יהוה (LORD) - IDF = 0.1 (appears in ~135 Psalms, not meaningful)
- ארץ (land/earth) - IDF = 2.3 (appears in ~20 Psalms)
- בית (house) - IDF = 1.8 (appears in ~30 Psalms)

**Step 3: Statistical Test**

- N = 12,000 (total unique roots in Psalter)
- K = 80 (unique roots in Psalm 23)
- n = 90 (unique roots in Psalm 27)
- k = 12 (shared roots)
- Expected overlap = (K × n) / N = (80 × 90) / 12,000 = 0.6
- p-value from hypergeometric: P(X ≥ 12) = 10⁻⁸ (highly significant!)

**Step 4: Weighted Score**

Weighted_Score = Σ IDF(shared_roots) = 0.1 + 2.3 + 1.8 + ... = 28.5

Compare to expected score under random sampling: 5.2 (with std dev 2.1)
z-score = (28.5 - 5.2) / 2.1 = 11.1 (extremely significant!)

**Step 5: Phrase Analysis**

Shared phrase: `בית יהוה` (house of the LORD)
- Psalm 23:6: "I will dwell in the house of the LORD"
- Psalm 27:4: "That I may dwell in the house of the LORD"

**Conclusion**: Psalms 23 and 27 are statistically highly related (p < 10⁻⁸), sharing rare vocabulary including the significant phrase "house of the LORD."

---

## Part 6: Integration with Existing Pipeline

### 6.1 Librarian Agent Consumption

The `report_generator.py` produces JSON output that the **Librarian Agent** can consume:

**Workflow**:
1. User requests analysis of Psalm P
2. Librarian queries `psalm_relationships.db` for Psalm P
3. Librarian retrieves:
   - All significantly related Psalms (p < 0.01)
   - Shared roots/phrases with IDF scores
   - Significance levels (p-values)
4. Librarian includes related Psalms **in their entirety** in research package
5. Librarian provides structured metadata about relationships

**Example Report Format**:
```json
{
    "psalm_of_interest": 23,
    "related_psalms_summary": {
        "total_significant_relationships": 8,
        "very_high_significance": [27, 121],  // p < 0.001
        "high_significance": [42, 63],        // 0.001 ≤ p < 0.01
        "moderate_significance": [84, 91]     // 0.01 ≤ p < 0.05
    },
    "detailed_relationships": [
        {
            "related_psalm": 27,
            "p_value": 0.00000001,
            "z_score": 11.1,
            "shared_root_count": 12,
            "shared_roots": [
                {
                    "root": "בית",
                    "idf_score": 1.8,
                    "appears_in_23": ["23:6"],
                    "appears_in_27": ["27:4"],
                    "example_context_23": "...בְּבֵית יְהוָה לְאֹרֶךְ יָמִים...",
                    "example_context_27": "...שִׁבְתִּי בְּבֵית יְהוָה..."
                },
                ...
            ],
            "shared_phrases": [
                {
                    "phrase_consonantal": "בית יהוה",
                    "phrase_hebrew": "בֵית יְהוָה",
                    "phrase_english": "house of the LORD",
                    "idf_score": 2.5,
                    "verses_in_23": ["23:6"],
                    "verses_in_27": ["27:4", "27:6"]
                }
            ],
            "unlikelihood_description": "extremely unlikely by chance (p = 1 in 100 million)",
            "relationship_note": "Both Psalms emphasize dwelling in God's presence and the theme of divine protection"
        }
    ]
}
```

### 6.2 Synthesis Agent Instructions

Update synthesis agent prompt to include:

```
When the research package includes "related_psalms" data:
1. Read the full text of all related Psalms
2. Analyze the shared vocabulary and phrases
3. Consider whether the relationship is:
   - Thematic (similar theological themes)
   - Lexical (shared rare vocabulary by coincidence)
   - Intertextual (one Psalm quoting/referencing another)
   - Compositional (same author or liturgical context)
4. Decide whether to comment on the relationship in your essay
5. If commenting, provide specific textual evidence from both Psalms
```

---

## Part 7: Validation Strategy

### 7.1 Known Related Psalms (Ground Truth)

Use scholarly consensus on related Psalms to validate the method:

**Test Cases**:
1. **Psalms 42-43**: Universally recognized as originally one Psalm (should have p-value ≈ 0)
2. **Psalms of Ascent (120-134)**: Liturgical collection (should show cluster)
3. **Davidic Psalms**: May show thematic/lexical similarities
4. **Hallelujah Psalms (146-150)**: Liturgical group with shared structure

**Validation Metrics**:
- **Recall**: Do we detect known relationships?
- **Precision**: Are our novel detections plausible?
- **False Positive Rate**: How many "unrelated" Psalms are flagged?

### 7.2 Manual Review Sample

Randomly sample 20 detected relationships and manually verify:
1. Check Hebrew text for actual shared vocabulary
2. Consult commentaries for known thematic connections
3. Assess whether relationship is meaningful or coincidental

**Success Criteria**:
- ≥80% of detected relationships are plausible upon manual review
- All known related Psalms have p < 0.01

---

## Part 8: Computational Complexity

### 8.1 Time Complexity

- Root extraction: O(N × V) where N = 150 Psalms, V = avg verses per Psalm ≈ 17
  - ~2,500 verses total, ~1-2 seconds per verse → 1-2 hours total

- Frequency analysis: O(R) where R = unique roots ≈ 12,000
  - ~1 second

- Pairwise comparison: O(N² × R) = O(150² × 12,000) ≈ 270 million operations
  - With optimized Python + NumPy: ~10-30 minutes

- Phrase analysis: O(P²) where P = total phrases ≈ 50,000
  - ~1-5 minutes

**Total estimated runtime**: 2-3 hours for full analysis of all 150 Psalms

### 8.2 Space Complexity

- Root database: ~12,000 roots × 100 bytes = 1.2 MB
- Psalm-root mappings: ~150 Psalms × 100 roots × 50 bytes = 750 KB
- Relationships: ~11,175 pairs × 500 bytes = 5.6 MB
- Total database size: ~10-20 MB

**Conclusion**: Computationally feasible on standard hardware.

---

## Part 9: Implementation Roadmap

### Phase 1: Foundation (Week 1)
- ✓ Create project structure and database schema
- ✓ Implement root_extractor.py with Hebrew normalization
- ✓ Validate root extraction on 10 sample Psalms
- ✓ Unit tests for normalization logic

### Phase 2: Analysis Core (Week 2)
- ✓ Implement frequency_analyzer.py
- ✓ Implement pairwise_comparator.py with hypergeometric test
- ✓ Validate on known related Psalms (42-43)
- ✓ Tune significance thresholds

### Phase 3: Enhanced Features (Week 3)
- ✓ Implement phrase_analyzer.py for n-grams
- ✓ Implement cluster_detector.py
- ✓ Multiple testing correction (FDR)
- ✓ Performance optimization

### Phase 4: Integration (Week 4)
- ✓ Implement report_generator.py
- ✓ Create librarian integration interface
- ✓ Full validation on all 150 Psalms
- ✓ Documentation and user guide

---

## Part 10: Open Questions and Future Enhancements

### Open Questions
1. **Minimum Psalm length**: Should we exclude very short Psalms (e.g., Psalm 117 with 2 verses)?
2. **Directional relationships**: Does it matter if Psalm A quotes B vs. B quotes A?
3. **Acrostic Psalms**: Do alphabetical acrostics (e.g., Psalm 119) artificially inflate vocabulary?

### Future Enhancements
1. **Semantic analysis**: Use word embeddings to detect semantic similarity beyond lexical overlap
2. **Syntactic patterns**: Detect similar grammatical structures (e.g., parallelism patterns)
3. **Topic modeling**: Use LDA or BERTopic to identify thematic clusters
4. **Temporal analysis**: If Psalm dates are available, test if related Psalms are contemporaneous
5. **Cross-biblical analysis**: Extend to Pentateuch, Prophets, etc.

---

## Conclusion

This proposal provides a statistically rigorous, computationally feasible, and hermeneutically sound approach to identifying related Psalms. By combining:
- Robust Hebrew text processing (leveraging existing infrastructure)
- Sound statistical methodology (hypergeometric testing + IDF weighting)
- Conservative multiple testing correction
- Human expert validation (synthesis agent review)

We can provide valuable insights to guide deeper scholarly analysis, while being transparent about the probabilistic nature of the findings.

**Next Step**: Review this proposal, make adjustments, and proceed to implementation Phase 1.
