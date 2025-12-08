# Filtering Strategies Comparison: Figurative Librarian vs Concordance Librarian

This document compares how the Figurative Librarian and Concordance Librarian prevent overwhelming result sets by applying intelligent filtering strategies.

## Overview

Both librarians face the challenge of preventing too many matches when searching large databases. However, they employ different approaches tailored to their specific data structures and search patterns.

## Concordance Librarian Filtering Strategy

### 1. **Smart Scoping Based on Word Frequency**
- **When Applied**: Before search execution
- **How It Works**:
  - Always searches full Tanakh first to get accurate counts
  - If results exceed `auto_scope_threshold` (default: 30), applies intelligent filtering
  - Common words → Limited to key books (Genesis, Psalms, Proverbs)
  - Rare words → Full Tanakh scope

```python
# From line 665-710 in concordance_librarian.py
if use_post_search_filtering and phrase_results_count > request.auto_scope_threshold:
    # Priority book ordering for common phrases
    priority_books = [
        # Torah (Foundational books)
        'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
        # Psalms and Wisdom
        'Psalms', 'Proverbs', 'Job',
        # Major Prophets
        'Isaiah', 'Jeremiah', 'Ezekiel',
        # ... etc
    ]
```

### 2. **Priority-Based Book Ordering**
- **When Applied**: During post-search filtering
- **Strategy**:
  - First pass: Collect results from priority books in order
  - Second pass: Fill remaining slots with results from other books
  - Ensures representation from foundational texts first

### 3. **Maximum Results Per Variation**
- **Parameter**: `max_results` (default: 50)
- **Applied**: To each variation searched
- **Effect**: Prevents any single variation from dominating results

### 4. **Verse Deduplication**
- **Method**: Uses `(book, chapter, verse)` tuple as unique key
- **Purpose**: Prevents same verse from appearing multiple times across different variations

### 5. **Source Psalm Inclusion Guarantee**
- **Feature**: If `source_psalm` is specified, ensures Psalms is included in scope
- **Reasoning**: The current psalm being analyzed should always be included in results

## Figurative Librarian Filtering Strategy

### 1. **Pre-Search WHERE Clause Filtering** (Applied in SQL before execution)
- **Book/Scope Filters**:
  - Single book (`request.book`) or multiple books (`request.books`)
  - Chapter and verse range restrictions
- **Figurative Type Filters**:
  - Simile, metaphor, personification, idiom, hyperbole, metonymy
  - Combined with OR logic (any matching type included)
- **Hierarchical Metadata Filters**:
  - Target filtering: `f.target LIKE ? COLLATE NOCASE`
  - Vehicle filtering: Complex pattern matching with morphological variants
  - Ground filtering: `f.ground LIKE ? COLLATE NOCASE`
  - Posture filtering: `f.posture LIKE ? COLLATE NOCASE`
- **Text Content Filter**:
  - Searches within `figurative_text` OR `explanation` fields

### 2. **Randomized Result Ordering with Hard Limit**
- **When Applied**: During query execution
- **Method**: `ORDER BY RANDOM() LIMIT {request.max_results}`
- **Default Limit**: 500 results (configurable per request)
- **Purpose**: Ensures unbiased sampling from all matches

```python
# From line 575 in figurative_librarian.py
query += f" ORDER BY RANDOM() LIMIT {request.max_results}"
```

### 3. **Morphological Variant Generation for Vehicle Searches**
- **Feature**: `_get_morphological_variants()` generates English word forms
- **Variations Generated**: base, ing, ed, s, er, ers (and doubled consonant forms)
- **Applied**: Only to single-word vehicle searches, not phrases
- **Purpose**: Catches different morphological forms without separate searches

### 4. **Complex Vehicle Pattern Matching**
- **When vehicle_search_terms provided**: Uses sophisticated word-boundary patterns
- **Patterns Include**: `% term %`, `% term"%`, `%"term %`, `%"term"%`, etc.
- **Purpose**: Precise matching within descriptive JSON arrays while avoiding false positives

### 5. **Bundle Creation with Instance Objects**
- **Result Processing**: All database rows converted to `FigurativeInstance` objects
- **Bundle Limit**: Enforced by SQL LIMIT, not post-processing
- **No Deduplication**: Multiple instances from same verse allowed (different figurative types)

## Key Differences

| Aspect | Concordance Librarian | Figurative Librarian |
|--------|----------------------|---------------------|
| **Primary Strategy** | Smart scoping based on frequency | Randomized sampling |
| **Default Max Results** | 50 per variation | 500 total |
| **Filtering Timing** | Post-search (after counting) | Pre-search (in SQL WHERE) |
| **Result Selection** | Priority-based book ordering | Random selection |
| **Deduplication** | Verse-level deduplication | No explicit deduplication |
| **Scope Adaptation** | Dynamic based on result count | Fixed scope specified in request |
| **Variation Handling** | Generates Hebrew prefix/suffix variations | Generates English morphological variants |

## Strategic Rationale

### Concordance Librarian
- **Challenge**: Hebrew words/phrases can appear thousands of times
- **Solution**: Intelligent filtering that prioritizes theologically significant books
- **Approach**: Conservative - ensures foundational texts are represented first

### Figurative Librarian
- **Challenge**: Figurative language is inherently rarer and more distributed
- **Solution**: Random sampling to get diverse representation
- **Approach**: Liberal - allows more results since the dataset is naturally constrained

## Effectiveness Assessment

### Concordance Librarian Strengths:
1. **Frequency-Aware**: Adapts scope based on actual word/phrase frequency
2. **Theologically Prioritized**: Ensures representation from key biblical books
3. **Controlled Growth**: Prevents exponential result growth with variations
4. **Source Inclusion**: Guarantees current psalm appears in results

### Figurative Librarian Strengths:
1. **Unbiased Sampling**: Random selection avoids systematic biases
2. **Higher Threshold**: 500 result limit accommodates the figurative language database size
3. **Hierarchical Filtering**: Multiple dimensions reduce search space efficiently
4. **Flexible Matching**: Case-insensitive partial matching increases recall without explosion

## Potential Improvements

### For Concordance Librarian:
1. Could implement semantic clustering to group similar verses
2. Might benefit from book result quotas to ensure balanced representation
3. Could add user-configurable priority book lists

### For Figurative Librarian:
1. Could implement confidence-based sorting in addition to randomization
2. Might benefit from book-aware randomization to ensure broad representation
3. Could add figurative-type quotas for balanced results

## Conclusion

Both librarians employ appropriate filtering strategies for their domains:
- The Concordance Librarian uses conservative, intelligent filtering to handle potentially massive result sets from common Hebrew words
- The Figurative Librarian uses more permissive filtering with randomization to handle the inherently sparser figurative language database

The contrasting approaches reflect the different natures of their data and search requirements, with each optimized for its specific use case.