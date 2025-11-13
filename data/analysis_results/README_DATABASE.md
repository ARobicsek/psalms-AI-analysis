# Database Regeneration Guide

## Skip-Gram Database

The `data/psalm_relationships.db` file contains skip-gram patterns and is too large to commit to GitHub (~360MB after skip-gram extraction).

### To Regenerate Locally

If you need to regenerate the skip-gram data, run:

```bash
# Extract skip-grams for all 150 psalms (~45 seconds)
python scripts/statistical_analysis/add_skipgrams_to_db.py

# Rescore all 11,001 psalm pairs (~6.5 minutes)
python scripts/statistical_analysis/rescore_all_pairs.py

# Generate top 100 connections report
python scripts/statistical_analysis/generate_top_connections.py
```

### Database Contents

The database includes:
- **root_frequencies**: 3,327 unique Hebrew roots with IDF scores
- **psalm_roots**: 13,886 psalm-root mappings
- **psalm_phrases**: 63,669 contiguous phrases (2-3 words)
- **psalm_skipgrams**: 1,935,965 skip-gram patterns (2-4 words) ⚠️ LARGE TABLE
- **psalm_relationships**: 11,001 significant psalm pair relationships

### Output Files (Committed)

The following analysis results ARE committed and available:
- `enhanced_scores_full.json` (6.4MB) - All 11,001 enhanced scores
- `top_100_connections.json` (638KB) - Top 100 psalm connections
- `TOP_100_CONNECTIONS_REPORT.md` (11KB) - Human-readable report
- `psalm_word_counts.json` (2.4KB) - Word counts for all 150 psalms

These files contain the complete analysis results and can be used without regenerating the database.
