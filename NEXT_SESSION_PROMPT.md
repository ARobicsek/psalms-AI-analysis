# Session 37 Handoff - Research Assembler Integration

## Previous Session (Session 36) Completed ✅

Successfully implemented **Full Psalm Detection with Verse-Level Analysis** AND **LLM Validation to Filter False Positives**:

### What Was Accomplished

**Major Enhancement** (~300 lines added/modified in `liturgical_librarian.py`):
- Implemented **verse-by-verse analysis** of hebrew_text to detect actual psalm content
- Added `_get_psalm_verses()`, `_check_verses_in_prayer()`, `_normalize_hebrew_for_comparison()` methods
- Completely rewrote `_verify_full_psalm_matches()` with intelligent verse detection
- Added `_generate_full_psalm_summary()` and `_generate_full_psalm_llm_summary()` methods
- Enhanced LLM prompts to include verse coverage information

**Key Improvements**:

1. **Verse-Level Detection** ✅
   - OLD: Filtered ALL 8 potential full psalm matches (too aggressive)
   - NEW: Checks actual Hebrew text to find which verses are present
   - Example: "verses 1, 3-6 (83%)" or "verses 1-4 (67%)"
   - Distinguishes full recitations (80%+) from partial (30-79%)

2. **Intelligent Full Psalm Summaries** ✅
   - LLM analyzes verse coverage patterns
   - Reports: "Full recitation in Kiddush, Third Meal; Partial (v. 1-4) in Daytime Kiddush"
   - Consolidated all full psalm entries into ONE result (no duplicates)
   - Example: "Psalm 23 is recited in full (verses 1, 3-6) across five major liturgical contexts..."

3. **Hebrew Text Analysis** ✅
   - Normalizes Hebrew text (removes nikud, cantillation)
   - Matches verse text with 70% accuracy threshold
   - Handles text variations between editions
   - Reports exact verses found: "verses 1, 3-6" (missing verse 2)

**Testing Results** (Psalm 23:3):
- **Before**: 0 full psalm entries (all 8 filtered out)
- **After**: 1 consolidated full psalm entry with 8 occurrences across 7 contexts
- Correctly identified: Full recitations (100%, 83%) vs. Partial (67%)
- LLM summary accurately describes verse usage patterns
- Output saved: `logs/psalm23_verse3_session36.txt`

**Testing Results** (Full Psalm 23):
- 10 distinct results (1 full psalm + 9 phrase excerpts)
- Full psalm entry: 33 occurrences across 13 contexts
- LLM summary: "Psalm 23 is recited in full (verses 1, 3-6)... Partial recitations of verses 1-4 appear in daytime Kiddush..."
- Output saved: `logs/psalm23_full_session36.txt`

---

### THEN: Added LLM Validation Pass (~300 lines added)

**New Implementation**:
- Added `ValidationResult` dataclass to store validation results
- Added `_count_meaningful_hebrew_words()` to filter single-letter phrases
- Added `_validate_phrase_match_with_llm()` - validates individual matches against target psalm
- Added `_validate_phrase_groups_with_llm()` - batch validation of all phrase groups
- Integrated validation into `find_liturgical_usage_by_phrase()` pipeline (step 4.5)

**Validation Logic**:
1. **Phrase Length Filter**: Automatically filter phrases with <2 meaningful Hebrew words
2. **LLM Validation**: For each phrase group, sample 1-2 representatives and ask LLM:
   - Is this really from the target psalm?
   - Or is it from a different psalm/context with the same words?
   - Provide liturgical context quote and translation for valid matches
3. **Filtering Decisions**:
   - High confidence rejection (≥70%): Filter out entire phrase group
   - Medium confidence rejection (50-69%): Keep but add warning note
   - Low confidence/valid: Keep without note

**Testing Results** (Full Psalm 23 with LLM Validation):
- **Before Validation**: 10 phrase groups
- **After Validation**: **2 phrase groups** ✅
- **Filtered out**:
  - `"יָמִֽים׃ פ"` - single letter (phrase length filter)
  - `"אַ֤ךְ ׀ ט֤וֹב"` - false positive from Shalom Aleichem (LLM detected different context)
  - `"לְדָוִ֑ד יְהֹוָ֥ה"` - **Psalm 20**, not Psalm 23 (LLM detected wrong psalm) ✅
  - `"לְאֹ֣רֶךְ יָמִֽים"` - **Psalm 93**, not Psalm 23 (LLM detected quote from different psalm) ✅
  - Other minor phrase excerpts
- **Kept**:
  - `"למען שמו"` (Psalm 23:3) - 78 occurrences (validated as genuine)
  - Full Psalm 23 - 33 occurrences (consolidated, verified by verse analysis)
- Output saved: `logs/psalm23_validated_session36.txt`

**Success Metrics**:
- ✅ Filtered out single-letter phrases automatically
- ✅ Detected and filtered Psalm 20 masquerading as Psalm 23
- ✅ Detected and filtered Psalm 93 phrases
- ✅ Filtered false positives from unrelated contexts
- ✅ Kept genuine matches with high accuracy
- **Result**: **80% reduction in false positives** (10 → 2 phrases)

---

## This Session (Session 37) Tasks

### Primary Goal
**Integrate Liturgical Librarian into Research Assembler Pipeline**

All technical issues from Session 35 are now SOLVED:

**CRITICAL BUG**: Full psalm detection too aggressive
- Problem: `_verify_full_psalm_matches()` filtered out ALL full psalm matches for Psalm 23:3
- Expected: Some contexts DO have full psalm recitations (e.g., Third Meal, specific Zemirot)
- Result: No "Full Psalm 23" entry appears in output
- Root cause: Verification logic too strict (context length < 500, verse span < 3)
- Fix needed: Improve heuristics or check actual Hebrew text content

**Missing Feature**: LLM not analyzing Hebrew text context
- Problem: LLM only sees aggregated metadata, not actual `hebrew_text` field
- Impact: Can't distinguish if phrase is in Amidah body vs. adjacent text
- Example: Metadata says "Amidah" but full Psalm 23 is actually AFTER Amidah in same prayer document
- Fix needed: Pass `hebrew_text` snippets to LLM for context verification

### Key Objectives

1. **Fix Full Psalm Detection** 🔧
   - Review `_verify_full_psalm_matches()` logic
   - Test with known full psalm recitations (Third Meal, Ashkenaz Shabbat)
   - Consider checking for consecutive verse markers in `liturgy_context`
   - Balance: Catch true full psalms while still filtering false positives

2. **Add LLM Context Analysis** 🔧
   - Pass `hebrew_text` field (or excerpt) to LLM
   - Update `_generate_phrase_llm_summary()` to include text analysis
   - Have LLM verify WHERE in the prayer text the phrase/psalm appears
   - Example prompt addition: "Here is the Hebrew text context: [excerpt]. Verify where the phrase appears within this text."

3. **Test Fixes**
   - Run Psalm 23 full chapter (not just verse 3)
   - Verify full psalm entries appear for known contexts
   - Verify LLM correctly identifies phrase locations within prayers

### Files to Review

- `src/agents/liturgical_librarian.py` - Main file with all changes
  - Lines 237-364: `find_liturgical_usage_by_phrase()` method
  - Lines 897-930: `_verify_full_psalm_matches()` - **NEEDS FIX**
  - Lines 773-863: `_generate_phrase_llm_summary()` - Needs `hebrew_text` integration
- `logs/psalm23_verse3_deduplicated.txt` - Current output (no full psalm entries)
- `logs/one_phrase_example.txt` - Raw data example showing hebrew_text field

### Testing Commands

```bash
# Test current behavior (shows the bug)
python src/agents/liturgical_librarian.py 23 --verses 3

# Test full chapter after fixes
python src/agents/liturgical_librarian.py 23

# Test with verbose to see filtering decisions
python src/agents/liturgical_librarian.py 23 --verbose
```

### Success Criteria

1. ✅ Full psalm recitations correctly identified (not filtered out)
2. ✅ LLM receives and analyzes `hebrew_text` context
3. ✅ Output distinguishes phrase-in-prayer vs. phrase-adjacent-to-prayer
4. ✅ False positive filtering still works (Amidah metadata mislabeling caught)
5. ✅ Test output includes both full psalm AND phrase entries where appropriate

---

## Context for Next Developer

### Project Status
- **Phase**: Liturgical Librarian Phase 6 complete, moving to testing/optimization
- **Pipeline**: 4-pass system (MacroAnalyst → MicroAnalyst → SynthesisWriter → MasterEditor)
- **Current capability**: Can generate verse-by-verse commentary for all 150 Psalms
- **Database**:
  - `data/liturgy.db` - Contains ~1,113 prayers, phrase-level index for some Psalms
  - `database/tanakh.db` - Canonical Hebrew text
  - Phase 4 index complete for Psalm 23, partial coverage for others

### Recent Progress
- **Session 32**: Fixed liturgy phrase extraction bug
- **Session 33**: Built intelligent aggregation with LLM summaries
- **Session 34**: Integrated into ResearchAssembler pipeline
- **Session 35**: Redesigned to phrase-first grouping ✅
- **Current**: Need to fix full psalm detection and add LLM text analysis

### Liturgical Librarian Architecture (Post-Session 35)

**New Phrase-First Design**:
```python
# Preferred method (phrase-first grouping)
results = librarian.find_liturgical_usage_by_phrase(
    psalm_chapter=23,
    psalm_verses=[3],
    min_confidence=0.75,
    separate_full_psalm=True  # Separates full psalm from excerpts
)

# Each result is a PhraseUsageMatch:
# - psalm_phrase_hebrew: The actual Hebrew phrase
# - occurrence_count: How many times this phrase appears
# - prayer_contexts: List of prayer names where it appears
# - liturgical_summary: LLM-generated natural language description
```

**Key Methods**:
- `find_liturgical_usage_by_phrase()` - NEW, phrase-first (preferred)
- `find_liturgical_usage_aggregated()` - OLD, prayer-first (deprecated)
- `_verify_full_psalm_matches()` - Filters metadata false positives (currently too aggressive)
- `_merge_overlapping_phrase_groups()` - Deduplicates identical contexts

---

## Open Questions for Session 36

1. **Full Psalm Detection Heuristics**: How to distinguish true full psalms from metadata errors?
   - Current: Checks context length < 500 chars and verse span < 3
   - Problem: Too strict, filters out valid full psalms
   - Options:
     a. Check for consecutive verse text in `liturgy_context`
     b. Look for psalm opening "מזמור לדוד" in Hebrew text
     c. Have LLM analyze `hebrew_text` field to verify
   - Recommendation: Try option (c) - LLM analysis

2. **Hebrew Text Integration**: How much text to pass to LLM?
   - Full `hebrew_text` field could be very long (thousands of chars)
   - Options:
     a. Pass full text (expensive, may hit token limits)
     b. Pass 500-char window around phrase
     c. Pass first/last 200 chars + phrase context
   - Recommendation: Start with (b) - 500-char window

3. **False Positive Balance**: How aggressive should filtering be?
   - Too strict: Miss valid full psalms
   - Too loose: Include metadata errors (Amidah example)
   - Current: 8/8 filtered for Psalm 23:3 (too strict)
   - Goal: Filter ~4-5, keep ~3-4 valid ones

---

## Cost Notes (Updated)

### Session 35 Actual Costs
- Testing and refactoring: ~$0.08
- Multiple test runs with verbose output

### Production Estimates (Unchanged)
- **Per Psalm** (with LLM summaries): ~$0.025
- **All 150 Psalms**: ~$3.75
- **Note**: Adding hebrew_text analysis in Session 36 will increase per-psalm cost slightly
- **Estimated impact**: +$0.005 per psalm = +$0.75 total (~$4.50 for all 150)

---

## Next Steps

### Immediate (Session 36) - PRIORITY
1. **Fix `_verify_full_psalm_matches()` method**
   - Current logic filters ALL full psalm matches
   - Need to distinguish true full psalms from metadata errors
   - Test with Psalm 23 full chapter to verify fix

2. **Add LLM Hebrew Text Analysis**
   - Update `_generate_phrase_llm_summary()` to receive `hebrew_text` field
   - Pass 500-char window around phrase to LLM
   - Prompt LLM to verify WHERE phrase appears in prayer structure
   - Example: "Is this phrase in the Amidah blessing itself or in adjacent text?"

3. **Test Complete Solution**
   - Run Psalm 23 full chapter with fixes
   - Verify output contains:
     - Full psalm entries (where applicable)
     - Phrase entries with accurate location descriptions
     - Proper deduplication still working

### Future Sessions
1. **Phase 7**: Pipeline Integration Testing
   - Test ResearchAssembler with new phrase-first output
   - May need to update `format_for_research_bundle()` for new data structure
   - Full end-to-end test: MacroAnalyst → MicroAnalyst → SynthesisWriter

2. **Phase 8**: Index Remaining Psalms
   - Run liturgy indexer for all 150 Psalms
   - Estimated time: Several hours
   - Enables full coverage

3. **Production Deployment**
   - Generate commentaries for all 150 Psalms
   - Quality review
   - Final editing pass

---

**Session 35 completed phrase-first redesign successfully. Session 36 needs to fix full psalm detection and add hebrew_text analysis to LLM prompts.**
