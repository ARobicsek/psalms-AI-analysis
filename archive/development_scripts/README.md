# Development Scripts Archive

This directory contains test, validation, and analysis scripts from the development process. These scripts were used during feature development, debugging, and validation but are not part of the production system.

**Archived**: Session 120 (2025-11-16)

## Directory Structure

### `root/` (47 files)
Scripts that were in the project root directory during development:

**Analysis Scripts**:
- `analyze_issues.py` - Issue analysis tool
- `analyze_skipgram_quality.py` - Skipgram quality analyzer
- `detailed_analysis.py` - Detailed pattern analysis
- `examine_pattern_examples.py` - Pattern example examiner
- `linguistic_quality_analysis.py` - Linguistic quality assessment

**Check/Validation Scripts**:
- `check_cache_stats.py` - Cache statistics checker
- `check_canonicalization_status.py` - Canonicalization status checker
- `check_concordance.py` - Concordance validation
- `check_dedup_simple.py` - Simple deduplication checker
- `check_deduplication.py` - Deduplication validator
- `check_inline_refs.py` - Inline reference checker
- `check_issue5.py` - Issue 5 checker
- `check_psalm81_verse1.py` - Psalm 81:1 checker

**Database/Query Test Scripts**:
- `test_db_direct.py` - Direct database testing
- `test_db_query.py` - Database query testing
- `test_queries_investigation.py` - Query investigation
- `test_queries_simple.py` - Simple query tests

**Concordance Test Scripts**:
- `test_concordance_baseline.py` - Concordance baseline tests
- `test_concordance_table.py` - Concordance table tests
- `test_psalm_3_comprehensive.py` - Psalm 3 comprehensive tests
- `test_psalm_3_concordances.py` - Psalm 3 concordance tests
- `test_psalm3_verse8.py` - Psalm 3:8 specific test

**Feature Test Scripts**:
- `test_alternates_feature.py` - Alternates feature testing
- `test_bidi_solution5.py` - BiDi solution 5
- `test_bidi_solution6.py` - BiDi solution 6
- `test_bidi_solutions.py` - BiDi solutions general
- `test_divine_names_shin_sin.py` - Divine names shin/sin handling
- `test_minimal_doc.py` - Minimal document generation
- `test_phrase_search.py` - Phrase search testing
- `test_raw_verse_text.py` - Raw verse text handling
- `test_simple_search.py` - Simple search testing

**Text Processing Test Scripts**:
- `test_findings_summary.py` - Findings summary
- `test_regex_split.py` - Regex split testing
- `test_split_column.py` - Column split testing
- `test_transform_debug.py` - Transform debugging
- `test_verse_tracking_v3.py` - Verse tracking V3

**Utility Scripts**:
- `find_verse15_split.py` - Find verse 15 split issues
- `inspect_liturgical_data.py` - Liturgical data inspector
- `inspect_liturgy_db.py` - Liturgy database inspector
- `phase3_validation.py` - Phase 3 validation
- `preview_db_changes.py` - Database change previewer
- `show_search_details.py` - Search detail viewer
- `show_verse_phrases.py` - Verse phrase viewer
- `verify_fixes.py` - Fix verification
- `view_research_bundle.py` - Research bundle viewer
- `view_test_results.py` - Test results viewer
- `test_v4_3_fix.py` - V4.3 fix testing

### `statistical_analysis/` (5 files)
Test scripts from the statistical analysis module:
- `test_phrase_extraction.py` - Phrase extraction testing
- `test_v3_fixes.py` - V3 fixes validation
- `test_v3_format.py` - V3 format testing
- `test_v4_2_fix.py` - V4.2 fix validation
- `test_verse_boundary_fix.py` - Verse boundary fix testing

### `ocr_pdf/` (7 files)
OCR and PDF processing test scripts:
- `test_fullscreen_simple.py` - Fullscreen mode test
- `test_hathitrust_zoom.py` - HathiTrust zoom test
- `test_high_resolution.py` - High resolution test
- `test_margin_120px.py` - 120px margin test
- `test_margin_50px.py` - 50px margin test
- `test_narrow_window.py` - Narrow window test
- `test_pages_56_267.py` - Specific page range test

### `hebrew_analysis/` (1 file)
Hebrew analysis module test scripts:
- `test_morphology.py` - Morphology analysis testing

### `tests/` (4 files)
Unit test scripts for core modules:
- `test_macro_analyst.py` - Macro analyst unit tests
- `test_micro_analyst.py` - Micro analyst unit tests
- `test_phonetic_analyst.py` - Phonetic analyst unit tests
- `test_synthesis_writer.py` - Synthesis writer unit tests

## Total Files Archived

**64 scripts** moved to archive:
- 47 from root directory (untracked)
- 5 from statistical_analysis/ (tracked)
- 7 from scripts/ (tracked)
- 1 from src/hebrew_analysis/ (tracked)
- 4 from tests/ (tracked)

## Production System

The production system (V6) retains only:
- Core analysis modules (`src/`)
- Production scripts (`scripts/`)
- Data files (V6 versions only)
- Documentation (`docs/`)
- Configuration files

## Notes

- These scripts were essential during development for testing, validation, and debugging
- They are archived rather than deleted to preserve development history
- Most scripts are version-specific (V3, V4, V5) and were superseded by V6
- If you need to reference or reactivate any script, they are preserved here with full history
