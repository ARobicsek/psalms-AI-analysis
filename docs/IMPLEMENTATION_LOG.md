# Session 58 - Fix is_unique=0 Bug + Simplify Research Bundle (2025-11-02)

**Goal**: Fix is_unique=0 filtering bug, remove extra LLM validation calls, and simplify research bundle to minimal structure.

**Status**: ✅ Complete

## Session Overview

This session made three critical improvements to the Liturgical Librarian:
1. Fixed the is_unique=0 filtering bug where non-unique phrases were appearing in output
2. Removed separate LLM validation calls - validation is now implicit in summary generation
3. Simplified the research bundle to contain ONLY phrase/verse identifiers and LLM summaries

## Problems Fixed & Solutions Implemented

### 1. is_unique=0 Filter Missing
- **Problem**: The phrase "׀ לֹ֥א הָלַךְ֮" from Psalm 1:1 appeared in the output despite having `is_unique=0` in the database. This phrase appears in other psalms and should have been filtered out.
- **Root Cause**: The `_group_by_psalm_phrase` method filtered out phrases with <2 words but did NOT filter out phrases with `is_unique=0`.
- **Fix**: Added filter for `is_unique=0` in `_group_by_psalm_phrase` method (lines 561-570), but ONLY for `phrase_match` type (not for full verses/chapters).

### 2. Extra LLM Validation Calls Removed
- **Problem**: In an earlier version, we made separate LLM calls to validate each phrase before summarization. This was wasteful and unnecessary.
- **User Requirement**: "We should NOT be making extra LLM calls for filtering purposes. The LLM should only be asked, in the context of its full analysis of the usage of a phrase, whether this usage is really from the psalm in question."
- **Fix**: Disabled `_validate_phrase_groups_with_llm` call (line 290). Validation is now implicit - the LLM naturally handles false positives during summary generation.

### 3. Research Bundle Simplified to Minimal Structure
- **Problem**: Research bundle contained raw match objects with metadata fields (occasion, service, prayer_name, etc.). User requirement was to use ONLY canonical fields and to simplify the bundle.
- **User Requirements**:
  - "We should NOT be EVER using the fields called Occasion, Service. We have CORRECT 'canonical' versions"
  - "We should ONLY be placing into the research bundle the phrase or name of chapter or verse range, and then the LLM summary for it. That's ALL."
- **Fix**:
  - Removed `full_psalm_recitations` list from bundle - only keep the summary
  - Simplified phrase groups to contain only: `phrase`, `verses`, `summary`
  - Removed all raw match data and metadata from bundle

### 4. Confirmed Max 5 Matches Limit
- **User Question**: Does the code limit matches to 5 per group for the LLM?
- **Answer**: Yes! See [liturgical_librarian.py:715](src/agents/liturgical_librarian.py#L715) - only first 5 prioritized matches are sent to LLM for detailed analysis.

## New Research Bundle Structure

The research bundle now contains ONLY:

```json
{
  "psalm_chapter": 1,
  "full_psalm_summary": "LLM-generated scholarly narrative...",
  "phrase_groups": [
    {
      "phrase": "Hebrew phrase text",
      "verses": "1:3",
      "summary": "LLM-generated scholarly narrative..."
    }
  ]
}
```

**No metadata, no raw matches, no prayer names** - just the scholarly summaries needed for commentary generation.

## Verification Results

Test run for Psalm 1 (`python view_research_bundle.py 1`) confirmed:

- ✅ **14 non-unique phrases filtered**: Console output shows 14 `[FILTER] Non-unique phrase` messages
- ✅ **Phrase groups reduced**: From 9 groups (before fix) to 6 groups (after fix)
- ✅ **No separate LLM validation calls**: Only summary generation calls
- ✅ **Minimal bundle structure**: Only phrase/verse + summary
- ✅ **Both problematic phrases removed**:
  - "׀ לֹ֥א הָלַךְ֮" (was in output, now filtered)
  - "וְדֶרֶךְ רְשָׁעִים" (was already filtered, still filtered)

## Files Modified

1. **src/agents/liturgical_librarian.py**
   - Added `is_unique=0` filter in `_group_by_psalm_phrase` method
   - Disabled `_validate_phrase_groups_with_llm` call (line 290)
   - Simplified `generate_research_bundle` to return minimal structure (lines 195-215)
   - Removed `full_psalm_recitations` from bundle, only keep summary

2. **view_research_bundle.py** (new)
   - User-friendly script to view the exact research bundle passed to commentary agents
   - Usage: `python view_research_bundle.py [psalm_number] [--format json|text|both]`
   - Shows the minimal bundle structure with only summaries
   - Replaced the old verbose test script

3. **test_psalm_filtering.py** (created in session)
   - Test script for verifying is_unique filtering
   - Shows which phrases are filtered out

4. **RESEARCH_BUNDLE_VIEWING_GUIDE.md** (new)
   - Documentation for viewing research bundles
   - Explains the minimal bundle structure

## Technical Details

The research bundle is now truly minimal - it contains exactly what the Master Editor and Synthesis Writer need for commentary generation: scholarly LLM summaries of liturgical usage. All filtering, validation, and metadata handling happens upstream, resulting in a clean, focused bundle for downstream agents.

---

# Session 57 - Liturgical Librarian Filtering and Reasoning Fixes (2025-11-02)

**Goal**: Fix the filtering bug and enhance LLM reasoning to correctly distinguish main prayers from supplementary material.

**Status**: ✅ Complete

## Session Overview

This session successfully resolved all critical issues with the Liturgical Librarian. The filtering bug was fixed, validation was enhanced with both heuristic and LLM-based approaches, and LLM reasoning now correctly distinguishes main prayers from supplementary readings.

## Problems Fixed & Solutions Implemented

### 1. Filtering Bug - Root Cause Found and Fixed
- **Problem**: False positives were identified by validation but not removed from research bundles. The root cause was Unicode encoding errors in verbose print statements causing exceptions that made validation default to "valid".
- **Fix**:
  - Wrapped all Hebrew text printing in try-except blocks
  - Added explicit filtering in `generate_research_bundle` to exclude items marked "FILTERED:"
  - Fixed exception handling to prevent print errors from breaking validation logic

### 2. Enhanced Validation System
- **Problem**: Some false positives weren't caught by LLM validation (e.g., Psalm 146 phrases appearing in Psalm 1 search).
- **Fix**:
  - **Lowered threshold**: Changed filtering threshold from 0.7 to 0.5 for better sensitivity
  - **Heuristic pre-filter**: Added regex-based check that automatically filters phrases when Location Description explicitly mentions other psalm numbers (catches obvious cases without LLM call)
  - **Strengthened LLM prompt**: Added detailed step-by-step analysis procedure with specific examples

### 3. Improved LLM Reasoning for Main Prayer vs. Supplement
- **Problem**: LLM summaries incorrectly stated psalms were "incorporated into" prayers when they were actually recited as introductory supplements.
- **Fix**:
  - Updated both phrase and full psalm summary prompts with detailed guidance on distinguishing supplementary material
  - Added explicit pattern matching rules (e.g., "This block begins with..." = supplement, not part of main prayer)
  - **Critical**: Added Location Description data to full psalm summary prompts so LLM can analyze liturgical structure
  - Provided concrete examples of correct vs. incorrect language

### 4. Updated Field Labels
- **Problem**: "Canonical Prayer Name" was confusing - it's the main prayer in a block, not necessarily where the psalm appears.
- **Fix**: Changed display label to "Main prayer in this liturgical block" throughout output and prompts

## Verification Results

Test run for Psalm 1 (`python scripts/test_liturgical_librarian_full_output.py`) confirmed all fixes work:

- ✅ **Filtering successful**: The phrase `וְדֶ֖רֶךְ רְשָׁעִ֣ים` (from Psalm 146:9) was correctly filtered out
- ✅ **Heuristic filter active**: Console showed `[HEURISTIC FILTER] Phrase - Location Description mentions Psalms [145, 146, 149, 150] but not Psalm 1`
- ✅ **Phrase groups reduced**: From 10 to 9 (1 false positive removed)
- ✅ **Full psalm summary accurate**: Now correctly states Psalm 1 is "an introductory supplement preceding Aleinu" and "an introductory prelude to Shir HaYichud" (NOT "incorporated into" them)
- ✅ **Cost control verified**: LLM receives max 5 matches per group
- ✅ **Labels updated**: Output shows "Main prayer in this liturgical block"

## Files Modified

- [src/agents/liturgical_librarian.py](../src/agents/liturgical_librarian.py) - Core fixes for filtering, validation, and prompts
- [scripts/test_liturgical_librarian_full_output.py](../scripts/test_liturgical_librarian_full_output.py) - Updated field labels

## Next Steps

The Liturgical Librarian is now fully functional and ready for use in commentary generation. Next session should begin the commentary generation pipeline for Psalm 1.

---
# Session 56 - Liturgical Librarian Refinements (2025-11-01)

**Goal**: Achieve a successful run of the `LiturgicalLibrarian` test script and address quality concerns in the output.

**Status**: 🔄 Partially Complete (completed with additional work in Session 57)

## Session Overview

This session focused on debugging the `LiturgicalLibrarian` and responding to a detailed list of user feedback. We successfully resolved the initial `AttributeError` exceptions, leading to a successful test run. However, subsequent analysis and new feedback revealed deeper issues in the grouping, filtering, and summarization logic.

## Problems Encountered & Fixes Applied

### 1. `AttributeError` Chain Reaction
- **Problem**: A series of `AttributeError` exceptions (`_prioritize_matches_by_type`, `_validate_summary_quality`, `_check_for_misattribution`) indicated that the `LiturgicalLibrarian` class was missing several key methods.
- **Fix**: Re-implemented the missing methods to restore basic functionality. This allowed the main test script (`scripts/test_liturgical_librarian_full_output.py`) to run without crashing.

### 2. Flawed Grouping Logic
- **Problem**: The user reported that the librarian was incorrectly grouping different types of matches (e.g., `exact_verse` with `phrase_match`) and different verses together, leading to confusing summaries.
- **Fix**: Modified the grouping logic in `_group_by_psalm_phrase` to use a more specific composite key, ensuring that only identical items are grouped.

### 3. Ineffective LLM-based Filtering
- **Problem**: A key issue was identified where the LLM-based validation was correctly identifying false positives (e.g., a phrase from Psalm 146 appearing in a search for Psalm 1), but a bug was preventing the system from filtering the invalid group from the final output.
- **Fix Attempted**: Made several changes to the data flow, including modifying function return values and data structures (`PhraseUsageMatch`, `research_bundle`) to correctly propagate validation notes and filtering decisions. The issue persists and remains the top priority.

### 4. Insufficient LLM Reasoning
- **Problem**: The user noted that the LLM summaries were not nuanced enough. For example, it would state a psalm was *part of* a prayer block when it was merely a supplementary reading recited *before* it.
- **Fix**: Updated the LLM prompts for both phrase and full-psalm summaries. Renamed `Canonical Prayer Name` to `'Main prayer in this liturgical block'` and added a new instruction for the LLM to analyze the `Location Description` to determine the precise relationship between the psalm and the main prayer.

### 5. Cost-Saving Measures
- **Problem**: The user expressed concern about the cost of repeated LLM calls.
- **Fix**: As an initial cost-saving measure, the number of matches sent to the LLM for summarization was limited to a maximum of 5.

## Final Action in Session
- Multiple fixes were applied to `src/agents/liturgical_librarian.py` and `scripts/test_liturgical_librarian_full_output.py`.
- The primary bug preventing the filtering of invalid matches remains unresolved and will be the main focus of the next session.
- The session concluded with a plan to update project documentation before starting the next session.

---
# Session 55 - Debugging Liturgical Librarian (2025-11-01)

**Goal**: Debug and fix the `LiturgicalLibrarian` agent and associated test script (`scripts/test_liturgical_librarian_full_output.py`).

**Status**: 🔄 In Progress

## Session Overview

This session was dedicated to debugging a series of `AttributeError` exceptions that occurred while running the test script for the `LiturgicalLibrarian`. The errors pointed to a significant drift between the code in the test script and the implementation of the `LiturgicalLibrarian` class, likely due to a series of incomplete or reverted fixes in previous sessions.

## Problems Encountered & Fixes Applied

### 1. `anthropic.APIStatusError`: Missing API Key
- **Problem**: The script failed because the Anthropic API key was not being loaded from the `.env` file.
- **Fix**: Added `from dotenv import load_dotenv` and `load_dotenv()` to the beginning of `scripts/test_liturgical_librarian_full_output.py`.

### 2. `AttributeError: 'LiturgicalLibrarian' object has no attribute 'generate_research_bundle'`
- **Problem**: The test script was calling a method that did not exist in the `LiturgicalLibrarian` class.
- **Fix**: Re-implemented the `generate_research_bundle` method in `src/agents/liturgical_librarian.py`.

### 3. `AttributeError: 'LiturgicalLibrarian' object has no attribute '_get_db_connection'`
- **Problem**: A helper function in the test script was calling a private method that did not exist on the `LiturgicalLibrarian` class.
- **Fix**: Added the `_get_db_connection` method to the `LiturgicalLibrarian` class.

### 4. `AttributeError: 'LiturgicalMatch' object has no attribute 'psalm_phrase'`
- **Problem**: The `format_match` function in the test script was using an incorrect attribute name (`psalm_phrase` instead of `psalm_phrase_hebrew`).
- **Fix**: Corrected the attribute name in `scripts/test_liturgical_librarian_full_output.py`.

### 5. `AttributeError: 'LiturgicalLibrarian' object has no attribute '_prioritize_matches_by_type'`
- **Problem**: This method, which is crucial for sorting matches before sending them to the LLM, was missing from the `LiturgicalLibrarian` class.
- **Fix**: Added the `_prioritize_matches_by_type` method back into the class.

### 6. `AttributeError: 'LiturgicalLibrarian' object has no attribute '_merge_overlapping_phrase_groups'`
- **Problem**: Another essential method for grouping matches was missing.
- **Fix**: Added the `_merge_overlapping_phrase_groups` method back into the class.

### 7. General Code Inconsistency
- **Problem**: Repeated `replace` operations seem to have left the `src/agents/liturgical_librarian.py` file in an inconsistent state, with multiple methods being accidentally removed and then re-added.
- **Solution**: Re-wrote the entire `src/agents/liturgical_librarian.py` file to ensure all methods and the correct class structure are in place.

## Final Action in Session
- Replaced the entire content of `src/agents/liturgical_librarian.py` with a corrected version containing all necessary methods and fixes for a consistent and stable state.
