# Next Session Prompt - Psalms Project

## Quick Session Start

Continue working on the Psalms structural analysis project. This document provides context for picking up where the last session left off.

## Current Status

**Phase**: V6 Production Ready
**Version**: V6.0 - Fresh generation with Session 115 morphology fixes
**Last Session**: Session 128 - Dynamic Token Scaling for Verse Commentary (2025-11-18)

## Session 128 Summary (COMPLETE ✓)

**Objective**: Fix verse commentary length inconsistency in longer psalms
**Result**: ✓ COMPLETE - Implemented dynamic token scaling based on psalm length

**Issue Discovered**:
- User noticed Psalm 7 (18 verses) output was only ~11-12 pages (~23K characters)
- Same total length as much shorter psalms (1-6 verses)
- Verse-by-verse commentary was only ~1/3 as long per verse

**Root Cause Analysis**:
- Synthesis writer had **fixed** `max_tokens_verse = 16000` output limit regardless of psalm length
- Token budget per verse decreased proportionally with longer psalms:
  - Psalm 1 (6 verses): 16000 ÷ 6 = **2,666 tokens/verse** (~2,000 words)
  - Psalm 4 (9 verses): 16000 ÷ 9 = **1,777 tokens/verse** (~1,333 words)
  - Psalm 7 (18 verses): 16000 ÷ 18 = **888 tokens/verse** (~666 words) ❌
- Claude Sonnet 4.5 tried to cover all verses equally but was constrained by total limit
- Result: Compressed commentary for longer psalms

**Solution Implemented**:
- Added `_calculate_verse_token_limit()` method to synthesis_writer.py
- Dynamic scaling: `max(16000, num_verses * 1800)`
- Maintains ~1,800 tokens per verse for consistent depth
- Minimum floor of 16K tokens (no regression for short psalms)

**New Token Allocations**:
- Psalm 1-8 (≤8 verses): 16,000 tokens (minimum, unchanged)
- Psalm 7 (18 verses): **32,400 tokens** (doubles current limit)
- Psalm 119 (176 verses): 316,800 tokens (extreme case)

**Master Editor Capacity Verified**:
- No changes needed to master_editor.py
- GPT-5 context window: 256K tokens (plenty of room)
- Current Psalm 7 input: ~107K → After fix: ~123K ✓
- Output limit: 65K tokens (unchanged, sufficient)

**Files Modified** (4 commits):
- `src/agents/synthesis_writer.py`:
  - Added `_calculate_verse_token_limit()` method (lines 498-513)
  - Modified `write_commentary()` signature: `max_tokens_verse` now optional (line 522)
  - Added dynamic calculation logic (lines 524-539)
  - Enhanced logging to show calculated token limits
  - **Added streaming support** for both intro and verse commentary generation
- `src/agents/macro_analyst.py`:
  - Doubled max_tokens default: 16K → 32K (line 223)
  - **Added streaming support** with extended thinking
- `src/agents/micro_analyst.py`:
  - Doubled discovery max_tokens: 16K → 32K (line 461)
  - Doubled synthesis max_tokens: 4K → 8K per verse (line 554)
  - **Added streaming support** for both discovery and synthesis passes

**Impact**:
- Longer psalms now receive proportionally more tokens for verse commentary
- Maintains consistent depth (~1,800 tokens/verse) across all psalm lengths
- No regression for shorter psalms (16K minimum preserved)
- Better user experience with detailed verse analysis for longer psalms

**Session Accomplishments**:
1. ✓ Diagnosed token allocation issue through comparative analysis
2. ✓ Designed dynamic scaling algorithm with minimum floor
3. ✓ Verified master editor capacity for increased input
4. ✓ Implemented dynamic token scaling in synthesis writer
5. ✓ Doubled macro/micro analyst token limits as precaution:
   - Macro analyst: 16K → 32K
   - Micro discovery: 16K → 32K
   - Micro synthesis: 4K → 8K per verse
6. ✓ **Discovered and fixed streaming requirement**:
   - 32K token limits triggered Anthropic SDK timeout protection
   - Added streaming to macro analyst (extended thinking + text)
   - Added streaming to micro analyst (both passes)
   - Added streaming to synthesis writer (intro + verses)
7. ✓ Successfully ran complete Psalm 7 pipeline with all fixes
8. ✓ Updated all documentation

**Commits Made** (4 total):
- `80addef` - Dynamic token scaling for verse commentary
- `07856cc` - Doubled token limits for macro/micro analysts
- `4094961` - Streaming support for macro/micro analysts
- `7367cd9` - Streaming support for synthesis writer

**Verified Results**:
- ✅ Pipeline completed successfully with streaming
- ✅ Psalm 7 verse commentary significantly longer (detailed analysis observed)
- ✅ No timeout errors encountered
- ✅ All agents now scale properly for longer psalms

**Next Steps**:
- Monitor verse commentary quality in future psalm runs
- System now ready for psalms of any length (including Psalm 119 with 176 verses)

---

## Session 127 Summary (COMPLETE ✓ - VERIFIED)

**Objective**: Fix pipeline crash caused by malformed JSON from Sonnet 4.5
**Result**: ✓ COMPLETE & VERIFIED - Two fixes applied, Psalm 7 pipeline successful

**Issue Encountered (First)**:
- User ran Psalm 7 pipeline: `python scripts/run_enhanced_pipeline.py 7`
- Micro analyst discovery pass failed with: `JSONDecodeError: Unterminated string starting at: line 179 column 226`
- Error was fatal - no retry mechanism for JSON parsing failures

**Fix #1 - Retry Logic**:
- Made JSONDecodeError retryable (same as API connection errors)
- Now retries up to 3 times with exponential backoff (2s, 4s delays)
- Logs helpful warning: "JSON parsing error (attempt X/3)... Retrying with fresh request..."

**Issue Encountered (Second)**:
- Retry logic worked, but all 3 attempts failed with same error pattern
- Errors occurred at end of response (line 169-212, char 22K-23K)
- Pattern: Response getting truncated mid-JSON near 8192 token limit

**Root Cause**:
- `max_tokens=8192` was too small for discovery pass responses
- Psalm 7 discovery response: ~23KB text (~10K+ tokens with Hebrew)
- JSON getting truncated before closing properly

**Fix #2 - Increased Token Limit**:
- Increased `max_tokens` from 8192 to 16384
- Now handles longer discovery responses with extensive Hebrew text
- Added explanatory comment in code

**Verification**:
- ✓ Psalm 7 pipeline completed successfully after fixes
- ✓ Discovery pass handled longer response without truncation
- ✓ No JSON parsing errors occurred

**Impact**:
- Pipeline now handles longer responses without truncation
- Automatic retry for transient JSON issues
- Better resilience for complex psalms with extensive analysis
- Consistent with existing API error handling patterns

**Files Modified**:
- `src/agents/micro_analyst.py` - Two fixes:
  - Lines 494-502: Added retry logic for JSONDecodeError
  - Line 461: Increased max_tokens from 8192 to 16384

**Session Accomplishments**:
1. ✓ Diagnosed JSON parsing error (initially appeared transient)
2. ✓ Implemented retry logic for resilience
3. ✓ Discovered underlying token limit issue via retry logs
4. ✓ Doubled token limit to 16K
5. ✓ Verified fix with successful Psalm 7 pipeline run
6. ✓ Updated all documentation

**Next Steps**:
- Continue with psalm analysis work
- Monitor for any other psalms with long discovery responses
- Consider applying similar token increases to other passes if needed

---

## Session 126 Summary (COMPLETE ✓)

**Objective**: Upgrade master editor to GPT-5.1 for improved reasoning capabilities
**Result**: ✓ COMPLETE - Master Editor enhanced with GPT-5 high reasoning effort configuration

**Changes Made**:
1. **Researched GPT-5.1 Capabilities** - Investigated new OpenAI GPT-5.1 model parameters
   - Discovered `reasoning_effort` parameter (values: "none", "minimal", "low", "medium", "high")
   - GPT-5.1 defaults to `reasoning_effort="none"` (no reasoning!) - must explicitly set
   - Discovered `max_completion_tokens` parameter for output length control
   - Temperature parameter not supported in reasoning models (GPT-5/5.1)

2. **Attempted GPT-5.1 Migration** - Updated master_editor.py to use GPT-5.1
   - Set `reasoning_effort="high"` for complex editorial analysis
   - Set `max_completion_tokens=65536` (64K tokens for detailed commentary)
   - Fixed import: Added `RateLimitError` to imports from openai package

3. **Rate Limit Issue Discovered** - GPT-5.1 has restrictive token limits on current plan
   - User's GPT-5.1 limit: 30,000 tokens per minute (TPM)
   - Actual request size: 116,477 tokens (research bundle + commentary + prompts)
   - Single request exceeds entire per-minute allowance by 3.9x
   - No upgrade path available for GPT-5.1 at this time

4. **Solution: Enhanced GPT-5 Configuration** - Switched to GPT-5 with new parameters
   - Model: `gpt-5` (500K TPM limit - easily handles 116K token requests)
   - Added `reasoning_effort="high"` (GPT-5 defaults to "medium")
   - Added `max_completion_tokens=65536` (explicit output limit)
   - Both models support high reasoning effort - main difference is default behavior

**Impact**:
- **Better than before**: Now using explicit `reasoning_effort="high"` (was using defaults)
- **Within rate limits**: 116K tokens fits comfortably in 500K TPM allowance
- **Improved quality**: High reasoning effort provides deeper analytical thinking for complex editorial work
- **Explicit configuration**: max_completion_tokens ensures adequate output length for detailed commentary

**Files Modified**:
- `src/agents/master_editor.py` - Updated to GPT-5 with reasoning_effort and max_completion_tokens parameters

**Key Learning**:
- GPT-5 and GPT-5.1 both support `reasoning_effort` parameter for deep reasoning
- GPT-5.1 requires explicit `reasoning_effort` setting (defaults to "none")
- GPT-5 defaults to "medium" reasoning effort (we set to "high")
- Temperature/top_p not supported in reasoning models - use reasoning_effort instead
- Rate limits can vary significantly between model versions

**Next Steps**:
- Test enhanced GPT-5 configuration with Psalm 6 pipeline
- Monitor quality improvements from high reasoning effort
- Consider GPT-5.1 migration when higher rate limits become available

---

## Session 125 Summary (COMPLETE ✓)

**Objective**: Improve related psalms research bundle instructions with scholarly example and reduce token usage
**Result**: ✓ COMPLETE - Single comprehensive instruction with better guidance and reduced repetition

**Changes Made**:
1. **Consolidated Instructions** - Moved repetitive intro from each psalm section to appear once at top
   - Eliminated 4 repetitions of ~60-token instruction
   - Significant token savings per research bundle

2. **Enhanced Instruction with Ps 25-34 Example** - Added comprehensive scholarly framework:
   - Structural Anomaly: Shared acrostic structure (omitting Vav ו, adding Pe פ linked by פדה)
   - Call-and-Response Arc: Ps 25:22 plea → Ps 34:7,18 response → Ps 34:23 capstone
   - Shared Wisdom Theme: מִי־הָאִישׁ (mi ha-ish) rhetorical question
   - Shared Thematic Vocabulary: Fear of LORD, humble/afflicted, good
   - Actionable prompt: "Ask yourself if a similar structural, thematic, or 'call-and-response' dynamic is at play"

3. **Updated to V6 Data** - Changed default from V4 to V6 connections file

**Testing**:
- ✓ Psalm 25 lookup found 5 related psalms with Psalm 34 ranked #1 (matches example!)
- ✓ Comprehensive instruction appears once at top
- ✓ Individual psalm sections simplified (no repetition)

**Impact**:
- Better guidance: Multi-dimensional framework for evaluating connections
- Token efficiency: Net positive despite longer instruction (appears once vs. 5 times)
- User experience: Clearer organization, concrete scholarly example

**Files Modified**:
- `src/agents/related_psalms_librarian.py` - Enhanced instructions, V6 integration

**Next Steps**:
- Monitor synthesis writer's use of related psalms data with enhanced guidance
- Evaluate whether new instruction framework improves connection identification

---

## Session 124 Summary (COMPLETE ✓)

**Objective**: Update TECHNICAL_ARCHITECTURE_SUMMARY.md to reflect all pipeline changes from Sessions 105-123
**Result**: ✓ COMPLETE - Comprehensive technical architecture update completed

**Major Updates**:
1. **Updated system overview**: 6-step pipeline (was 5), 8 librarians (was 7)
2. **Added V6 scoring system documentation**: Fresh statistical analysis with improved morphology
3. **Documented Related Psalms Librarian**: Integration, token optimization, V6 compatibility
4. **Added Root Extraction System section**: V6 improvements (Sessions 112-115)
5. **Expanded data storage**: V6 databases, ETCBC cache, statistical analysis files
6. **Added Pipeline Tracking section**: Comprehensive statistics, resume capability
7. **Updated output generation**: Poetic punctuation, enhanced metadata
8. **Added Recent Enhancements section**: Detailed documentation of Sessions 105-123
9. **New technical challenge**: Hebrew root extraction complexity and V6 solutions
10. **Updated performance metrics**: V6 system capabilities, token optimization
11. **Enhanced quality assurance**: Quotation verification, poetic punctuation checks
12. **Updated future enhancements**: Completed items vs. planned improvements

**Files Modified**:
- `docs/TECHNICAL_ARCHITECTURE_SUMMARY.md` - Comprehensive update reflecting Sessions 105-123

**Next Steps**:
- Technical architecture documentation now current through Session 123
- Ready for continued development or analysis work

---

## Session 123 Summary (COMPLETE ✓)

**Objective**: Review and suggest updates to "How Psalms Readers Guide works.docx" to reflect system enhancements
**Result**: ✓ COMPLETE - Comprehensive suggestions document created

**Analysis**:
- Extracted and reviewed original user guide document (October 2024)
- Analyzed 18 sessions of enhancements (Sessions 105-122)
- Identified user-facing improvements: Related Psalms (107-119), Quotations (122), Poetic Punctuation (121), Token Optimizations (118-119), V6 Morphology (115-117), Quality Filtering (111), ETCBC Cache (105)

**Suggestions Created** (in `suggested_guide_updates.md`):
1. Update librarian count (7 → 8 with Related Psalms Librarian)
2. New Stage 2.5: Related Psalms Research (explains statistical analysis, IDF scoring, top 5 limit)
3. Enhanced Stage 3: Research Assembly (notes related psalms data, IDF filtering, gap penalties)
4. Enhanced Stage 4: Synthesis Writer (highlights quotation emphasis, poetic punctuation)
5. Updated Stage 5: Editorial Review (350K character capacity)
6. New source category: Intertextual Psalm Connections (V6 database, 11,175 pairs, top 550)
7. Optional technical note: Morphological Analysis (ETCBC cache, algorithms)
8. Date correction and update notation
9. Optional example: Cross-psalm connections (Psalm 25-34)

**Design Approach**:
- Maintained original document's friendly, accessible voice
- Explained technical features in plain language with concrete examples
- Focused on user-facing enhancements that improve reader experience
- Marked certain additions as optional for user flexibility

**Files Created**:
- `suggested_guide_updates.md` - Comprehensive suggestions with specific text locations, rationales, and session references

**Next Steps**:
- User reviews suggestions document
- User selects which suggestions to incorporate
- Can assist with applying changes to Word document if desired

---

## Session 122 Summary (COMPLETE ✓)

**Objective**: Improve synthesis writer and master editor prompts to encourage more quotations from sources
**Result**: ✓ COMPLETE - Prompts now strongly emphasize showing actual quoted texts (Hebrew + English)

**Changes Implemented**:
1. ✓ **Added new section #7 to INTRODUCTION_ESSAY_PROMPT** - "SHOWS evidence through generous quotation" with specific examples
2. ✓ **Strengthened figurative language integration** - Now requires QUOTING parallels, not just citing them
3. ✓ **Enhanced liturgical context sections** - Explicitly requires quoting liturgical texts in Hebrew with English
4. ✓ **Improved comparative biblical usage** - Emphasizes showing actual texts from other passages
5. ✓ **Updated master editor MISSED OPPORTUNITIES** - New bullet point for insufficient quotations with detailed sub-bullets
6. ✓ **Strengthened figurative language assessment** - Asks whether parallels are quoted, not just cited

**Key Improvements**:
- When biblical parallels are mentioned (e.g., Ps 44:4, 89:16), prompts now require quoting 1-2 in Hebrew + English
- When liturgical usage is discussed, prompts now require showing the liturgical text itself
- When linguistic patterns are mentioned (e.g., בְּנֵי אִישׁ across psalms), prompts now require quoting examples
- Added concrete examples of WEAK vs. STRONG quotation practices throughout
- Maintained focus on not distracting from main task while emphasizing this improvement

**Files Modified**:
- `src/agents/synthesis_writer.py` - Updated INTRODUCTION_ESSAY_PROMPT and VERSE_COMMENTARY_PROMPT
- `src/agents/master_editor.py` - Updated MASTER_EDITOR_PROMPT with stronger quotation requirements

**Next Steps**:
- Test with next psalm generation to see improved quote-sharing behavior
- Monitor whether LLMs follow new quotation emphasis without getting distracted

---

## Session 121 Summary (COMPLETE ✓)

**Objective**: Embrace LLM's verse presentation by removing programmatic insertion and updating prompts
**Result**: ✓ COMPLETE - System now relies on LLM to provide verses with poetic punctuation

**Changes Implemented**:
1. ✓ **Removed programmatic verse insertion** - document_generator.py, commentary_formatter.py
2. ✓ **Updated master_editor.py prompts** - Now ENSURES LLM provides punctuated verses (3 locations)
3. ✓ **Updated synthesis_writer.py prompts** - Now ENSURES LLM provides punctuated verses (2 locations)

**Key Features**:
- LLM now provides verses with poetic punctuation (semicolons, periods, commas)
- Example: "בְּקׇרְאִי עֲנֵנִי אֱלֹקֵי צִדְקִי; בַּצָּר הִרְחַבְתָּ לִּי; חׇנֵּנִי וּשְׁמַע תְּפִלָּתִי."
- Helps readers see verse structure at a glance
- No more duplication (verse appearing twice)

**Files Modified**:
- `src/agents/master_editor.py` - Updated verse commentary instructions
- `src/agents/synthesis_writer.py` - Updated verse commentary instructions
- `src/utils/document_generator.py` - Removed programmatic verse insertion
- `src/utils/commentary_formatter.py` - Removed programmatic verse insertion

**Next Steps**:
- Test with next psalm generation to ensure LLMs follow new instructions
- Monitor quality of verse punctuation

---

## Session 120 Summary (COMPLETE ✓)

**Objective**: Clean up repository from V6 development work (Sessions 90-119)
**Result**: ✓ COMPLETE - 47 files removed, repository cleaned

**Cleanup Actions**:
- Removed all test scripts from V6 development (9 files)
- Removed all validation/check scripts (2 files)
- Removed all temporary output files (20 files)
- Removed old V4 and V5 data files (4 files, ~200MB)
- Removed old V1-V5 analysis scripts (12 files)
- Added V6 files to git tracking (5 files)

**Repository State**:
- Clean working directory with only V6 system files
- 42 net files removed
- ~200MB disk space freed
- All test/validation artifacts removed
- Ready for production use

**Files Now Tracked**:
- `data/analysis_results/psalm_patterns_v6.json`
- `data/analysis_results/enhanced_scores_v6.json`
- `data/analysis_results/top_550_connections_v6.json`
- `scripts/statistical_analysis/extract_psalm_patterns_v6.py`
- `scripts/statistical_analysis/generate_v6_scores.py`
- `scripts/statistical_analysis/generate_top_550_v6.py`

**Next Steps**:
- V6 system production-ready with clean repository
- Ready for future analysis or feature work

---

## Session 119 Summary (COMPLETE ✓)

**Objective**: Continue token optimization by reducing # of matching psalms and filtering low-value roots
**Result**: ✓ COMPLETE - Additional 30-40% reduction; 50-60% total reduction from Sessions 118-119

**Optimizations Implemented**:
1. ✓ **Reduced max matching psalms** - 8 → 5 (top connections by score)
2. ✓ **Filtered low-IDF roots** - Only display roots with IDF >= 1 (excludes common words)

**Impact**:
- Reduced psalm sections by 37.5% (3 fewer psalms shown)
- Filtered 20-40% of roots (varies by psalm pair)
- Better focus on strongest, most distinctive connections
- Total token reduction: ~50-60% across Sessions 118-119

**Files Modified**:
- `src/agents/related_psalms_librarian.py` - Max psalms limit & IDF filtering

**Next Steps**:
- V6 system ready for production with highly optimized research bundles
- Monitor synthesis quality impact

---

## Session 118 Summary (COMPLETE ✓)

**Objective**: Optimize related psalms display in research bundles for maximum token efficiency
**Result**: ✓ COMPLETE - 30-40% token reduction achieved while improving clarity

**Optimizations Implemented**:
1. ✓ **Removed IDF scores** from root displays (~10 chars/root saved)
2. ✓ **Compact occurrence format** - "(1 occurrence(s))" → "(×1)" (~13 chars saved per)
3. ✓ **Removed "Consonantal:" prefix** - Eliminated redundant label (~14 chars/phrase)
4. ✓ **Simplified psalm references** - "In Psalm X" → "Psalm X" (~3 chars each)
5. ✓ **Smart context extraction for roots** - Show matched word ±3 words instead of full verse
6. ✓ **Reordered sections** - Phrases FIRST → Skipgrams SECOND → Roots THIRD (by IDF)
7. ✓ **Full verse context for phrases/skipgrams** - Show complete verse (100-char limit)
8. ✓ **V6 data compatibility** - Fixed skipgram display to use `full_span_hebrew` field
9. ✓ **Pipeline updated** - research_assembler.py now uses V6 connections file

**Key Features**:
- Created `_remove_nikud()` method for consonantal matching
- Created `_extract_word_context()` to show matched word ±3 words
- Matched roots now always visible in displayed context
- Roots sorted by IDF descending (best matches first)
- Token savings: ~30-40% reduction in related psalms section

**Files Modified**:
- `src/agents/related_psalms_librarian.py` - Core formatting optimizations
- `src/agents/research_assembler.py` - Updated to use V6 connections file

**Next Steps**:
- V6 system ready for production with optimized token-efficient display
- Related psalms section now maximally compact while retaining clarity
- Ready for psalm analysis with cost-effective research bundles

---

## Session 117 Summary (COMPLETE ✓)

**Objective**: Execute V6 clean regeneration plan with fresh patterns and Session 115 morphology
**Result**: ✓ COMPLETE - V6 fully generated with all user-reported errors fixed

**V6 Generation Complete**:
1. ✓ **Fresh Pattern Extraction** - Generated [psalm_patterns_v6.json](../data/analysis_results/psalm_patterns_v6.json) (39.67 MB)
   - 11,170 psalm pairs with patterns
   - 2,738 unique roots with IDF scores
   - Fresh extraction using Session 115 morphology fixes

2. ✓ **V6 Scoring** - Generated [enhanced_scores_v6.json](../data/analysis_results/enhanced_scores_v6.json) (107.97 MB)
   - 11,170 scored psalm pairs
   - Fresh roots + phrases from V6 patterns
   - V5 skipgrams from database (correct)
   - Full Hebrew text in all matches arrays

3. ✓ **Top 550 Connections** - Generated [top_550_connections_v6.json](../data/analysis_results/top_550_connections_v6.json) (13.35 MB)
   - Score range: 19908.71 to 211.50
   - Top connection: Psalms 14-53 (nearly identical)

**Validation Results** - ALL PASSED ✓:
- `שִׁ֣יר חָדָ֑שׁ` → "שיר חדש" ✓ (was "יר חדש" in V5)
- `וּמִשְׁפָּ֑ט` → "שפט" ✓ (was "פט" in V5)
- `שָׁמַ֣יִם` → "שמים" ✓ (was "מים" in V5)
- `שִׁנָּ֣יו` → "שן" ✓ (was "ני" in V5)
- `בְּתוּל֣וֹת` → "בתולה" ✓ (was "תול" in V5)

**Files Created**:
- `scripts/statistical_analysis/extract_psalm_patterns_v6.py` - Fresh pattern extractor
- `scripts/statistical_analysis/generate_v6_scores.py` - V6 scoring with Hebrew text in matches
- `scripts/statistical_analysis/generate_top_550_v6.py` - V6 top connections generator
- `data/analysis_results/psalm_patterns_v6.json` - Fresh patterns (39.67 MB)
- `data/analysis_results/enhanced_scores_v6.json` - V6 scores (107.97 MB)
- `data/analysis_results/top_550_connections_v6.json` - V6 top 550 (13.35 MB)

**Key Features**:
- Completely fresh generation - no V3/V4/V5 dependency
- Session 115 morphology fixes applied throughout
- Full Hebrew text in matches arrays (phrases and roots)
- Skipgrams from V5 database (correct, with quality filtering)
- Gap penalty and content word bonus applied
- IDF filtering and rare root bonus

**Next Steps**:
- V6 system ready for production use
- All known root extraction errors fixed
- Ready for analysis or integration into pipeline

---

## Session 116 Summary (COMPLETE ✓)

**Objective**: Investigate V5 root extraction errors and create clean V6 regeneration plan
**Result**: ✓ COMPLETE - Identified issue (V5 reuses old V4 roots) and created V6 plan

**Investigation Results**:
1. ✓ **Morphology.py Session 115 fixes ARE working correctly** - Tested and verified
2. ✓ **V5 database pattern_roots ARE correct** - Database has good roots in skipgrams table
3. ✗ **V5 JSON deduplicated_roots ARE incorrect** - Reused from old V4 file (Nov 14, before fixes)
4. ✗ **V5 JSON contiguous phrases ARE incorrect** - Also reused from old V4 file

**Root Cause**:
- `enhanced_scorer_skipgram_dedup_v4.py` line 712 loads existing V4 file
- V4 file was generated Nov 14, before Nov 15 morphology fixes
- V5 reuses V4's `deduplicated_roots` and `deduplicated_contiguous_phrases`
- Result: V5 has correct skipgrams but incorrect roots/phrases

**User-Reported Errors** (all from old V4 data):
- `שִׁ֣יר חָדָ֑שׁ` → "יר חדש" ✗ (should be "שיר חדש")
- `וּמִשְׁפָּ֑ט` → "פט" ✗ (should be "שפט")
- `שָׁמַ֣יִם` → "מים" ✗ (should be "שמים")
- `שִׁנָּ֣יו` → "ני" ✗ (should be "שן")
- `בְּתוּל֣וֹת` → "תול" ✗ (should be "בתולה")

**Solution**: Create V6 - fresh generation from ground up, no dependency on V3/V4/V5

**Files Modified**:
- `docs/NEXT_SESSION_PROMPT.md` - Updated with V6 plan
- `docs/IMPLEMENTATION_LOG.md` - Session 116 entry

**Next Steps**:
- Execute V6 regeneration plan (see below)
- All data will be fresh with Session 115 morphology fixes

---

## Session 115 Summary (COMPLETE ✓)

**Objective**: Fix all remaining root extraction issues discovered in V5 output
**Result**: ✓ COMPLETE - Implemented three major fixes: hybrid stripping, plural protection, final letter normalization

**Fixes Applied**:
1. ✓ **Hybrid Stripping Approach** - Adaptive strategy based on word structure
   - Prefix-first for simple prefixes (ב, ל, מ, etc.): `בשמים` → `שמים` ✓
   - Suffix-first for ש-words (protects ש-roots): `שקרים` → `שקר` ✓
   - Detects word patterns and chooses optimal stripping order
   - File: `src/hebrew_analysis/morphology.py` lines 193-259

2. ✓ **Plural Ending Protection** - Stricter minimums for ים/ות endings
   - Prevents over-stripping of dual/plural nouns
   - `שמים` → `שמים` ✓ (dual noun "heavens", not שם + plural)
   - `שקרים` → `שקר` ✓ (plural "falsehoods", strips correctly)
   - File: `src/hebrew_analysis/morphology.py` lines 207-220

3. ✓ **Final Letter Normalization** - Converts to proper final forms (ך ם ן ף ץ)
   - After suffix stripping, normalizes ending letters
   - `שמך` → `שם` ✓ (מ → ם final mem)
   - `שניו` → `שן` ✓ (נ → ן final nun)
   - File: `src/hebrew_analysis/morphology.py` lines 261-272

**Impact**:
- 93.75% test pass rate (15/16 comprehensive tests passing)
- All user-reported problem cases fixed
- Better handling of common Hebrew words: שמים (heavens), שם (name), שן (tooth)
- Improved verb root extraction: שנא (hate), שמר (guard), שמע (hear), שפט (judge)
- More accurate prefix/suffix combinations: בשמים (in the heavens), משפט (judgment)

**Database Changes**:
- 335,720 skipgrams (better deduplication with improved root extraction)
- Score range: 1060.10 to 167.52
- Top connection: Psalms 14-53 (1060.10)

**Files Modified**:
- `src/hebrew_analysis/morphology.py` - Three comprehensive fixes
- `data/psalm_relationships.db` - Regenerated (130 MB, 335,720 skipgrams)
- `data/analysis_results/enhanced_scores_skipgram_dedup_v5.json` - Regenerated (53.30 MB)
- `data/analysis_results/top_550_connections_skipgram_dedup_v5.json` - Regenerated (5.58 MB)
- Documentation files updated

**Next Steps**:
- Verify fixes in actual V5 output (recommended first step)
- V5 system production-ready for analysis
- All major root extraction issues resolved

## Session 114 Summary (COMPLETE ✓)

**Objective**: Fix remaining root extraction issues with ש-initial roots - SUPERSEDED BY SESSION 115
**Note**: Session 114's suffix-first fix was a good start but incomplete. Session 115 implemented comprehensive solution.

## Session 113 Summary (COMPLETE ✓)

**Objective**: Fix critical V5 issues - root extraction over-stripping and skipgram contamination
**Result**: ✓ COMPLETE - 2 major fixes applied, V5 system now working correctly

**Bugs Fixed**:
1. ✓ **Skipgram Contamination** - Excluded gap_word_count=0 patterns
   - 38.29% of "skipgrams" were contiguous (gap=0) - now eliminated
   - Database: 378,836 → 337,243 true skipgrams (11% reduction)
   - File: `skipgram_extractor_v4.py` lines 298-302

2. ✓ **Root Extraction Over-Stripping** - Adaptive ש-prefix handling
   - Session 112's 4-letter check insufficient for multi-prefix cases
   - Now requires 5+ letters for ש when another prefix already stripped
   - Fixes: "ומשנאיו" → "שנא" ✓ (not "נא"), "בשיר" → "שיר" ✓ (not "יר")
   - File: `morphology.py` lines 208-211

**Impact**:
- Pure skipgram data (all patterns have gap ≥ 1)
- Accurate root extraction for multi-prefix words
- No duplicate patterns between contiguous and skipgram lists
- Proper stoplist filtering now active

**Files Modified**:
- `src/hebrew_analysis/morphology.py` - Adaptive ש-stripping
- `scripts/statistical_analysis/skipgram_extractor_v4.py` - Exclude gap=0
- `data/psalm_relationships.db` - Regenerated (129 MB, 337,243 skipgrams)
- `data/analysis_results/enhanced_scores_skipgram_dedup_v5.json` - Regenerated (51.18 MB)
- `data/analysis_results/top_550_connections_skipgram_dedup_v5.json` - Regenerated (5.36 MB)
- Documentation files updated

**Next Steps**:
- V5 system ready for production use
- All known critical bugs fixed
- Ready for analysis or further feature development

## Session 112 Summary (COMPLETE ✓)

**Objective**: Investigate and fix matching system issues identified by user
**Result**: ✓ COMPLETE - All 6 critical bugs fixed

**Bugs Fixed**:
1. ✓ **ETCBC Cache Error** - Fixed "ענוים" root mapping (עני → ענו)
2. ✓ **Root Extraction Over-stripping** - Fixed fallback to require 4+ letters when stripping "ש"
3. ✓ **Empty Matches Arrays** - Fixed field name mismatch (verses_a/b → matches_from_a/b)
4. ✓ **V5 Database Empty** - Regenerated with 378,836 quality-filtered skipgrams (141 MB)
5. ✓ **Stoplist Not Applied** - Fixed by database regeneration (now active)
6. ✓ **V5 Scoring** - Regenerated with all fixes applied

**Impact**: V5 system now fully operational with:
- Accurate semantic matching (fixed cache errors)
- Improved root extraction (no over-stripping)
- Complete verse-level match data (fixed empty arrays)
- Proper quality filtering (database regenerated correctly)

**Files Modified**:
- `src/hebrew_analysis/data/psalms_morphology_cache.json` - Fixed "ענוים" entry
- `src/hebrew_analysis/morphology.py` - Fixed fallback root extraction
- `scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v4.py` - Fixed empty matches bug
- `data/psalm_relationships.db` - Regenerated (378,836 skipgrams, 141 MB)
- `data/analysis_results/enhanced_scores_skipgram_dedup_v5.json` - Regenerated with fixes
- `data/analysis_results/top_550_connections_skipgram_dedup_v5.json` - Regenerated with fixes
- Documentation files updated

**Next Steps**:
- V5 system ready for production use
- Consider validation testing to verify bug fixes
- Ready for analysis or further feature development

## Session 111 Summary (COMPLETE ✓)

**Completed**:
- ✓ Implemented Priority 1: Content word filtering (removed 7.6% of formulaic patterns)
- ✓ Implemented Priority 2: Pattern stoplist (removed high-frequency noise patterns)
- ✓ Implemented Priority 3: Content word bonus in scoring (25-50% boost for 2+ content words)
- ✓ Generated V5 database with 379,220 quality-filtered skipgrams
- ✓ Generated top 550 V5 connections with improved signal-to-noise ratio
- ✓ Compared V5 to V4: 86.7% overlap, 34.2% reduction in avg skipgrams per connection
- ✓ Updated all session documentation

**Key Changes**:
- Created `src/hebrew_analysis/word_classifier.py` - Hebrew linguistic categorization
- Created `src/hebrew_analysis/data/pattern_stoplist.json` - Formulaic pattern list
- Modified `scripts/statistical_analysis/skipgram_extractor_v4.py` - Quality filtering
- Modified `scripts/statistical_analysis/migrate_skipgrams_v4.py` - V5 schema with content metadata
- Modified `scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v4.py` - Content word bonus
- Generated `data/analysis_results/enhanced_scores_skipgram_dedup_v5.json` - V5 scores
- Generated `data/analysis_results/top_550_connections_skipgram_dedup_v5.json` - V5 top 550

**V5 Impact**:
- Average skipgrams per connection: 4.4 → 2.9 (34.2% reduction)
- Average contiguous phrases: 2.1 → 1.9 (9.2% reduction)
- 73 new connections entered top 550 (higher quality patterns)
- 73 connections dropped from top 550 (formulaic patterns filtered)

## Session 110 Summary (COMPLETE ✓)

**Investigation**:
- ✓ Liturgical section marker already fixed in Session 107-108
- ✓ Related psalms partially completed in previous session

**Completed**:
- ✓ Completed related psalms display feature
- ✓ Added `related_psalms_list` to JSON export
- ✓ Updated DOCX formatting to show list
- ✓ Updated all session documentation

**Key Changes**:
- `pipeline_summary.py` now exports `related_psalms_list` to JSON (completes commit 8813fe8)
- `document_generator.py` displays "8 (Psalms 77, 25, 34...)" instead of just count or "N/A"
- Future DOCX generations will show which psalms were used for comparative analysis

## Session 109 Summary (COMPLETE ✓)

**Completed**:
- ✓ Fixed footnote markers in DOCX English translation
- ✓ Increased synthesis editor character limit to 700,000
- ✓ Limited related psalms to top 8 (sorted by final_score)
- ✓ Analyzed skipgram quality (~35-40% meaningful, ~45-50% trivial)
- ✓ Updated all session documentation

**Key Changes**:
- DOCX now strips footnote markers from English text (`document_generator.py`)
- Research bundles can now include up to 700K characters (~350K tokens)
- Related psalms limited to 8 strongest connections for manageability
- Skipgram quality assessed; current system acceptable but could be improved

## Session 108 Summary (COMPLETE ✓)

**Completed**:
- ✓ Fixed shared roots loading (was hardcoded to empty array)
- ✓ Added shared roots display section to markdown output
- ✓ Fixed root field names ('root' and 'idf' vs incorrect names)
- ✓ Fixed "No patterns" message to check all three pattern types
- ✓ Changed to Hebrew-only full text (~30% token reduction)
- ✓ Tested with Psalm 4→77 (11 roots now display correctly)
- ✓ Updated all session documentation

**Key Fix**: Psalm 77 connection to Psalm 4 (score 216.62, 11 shared roots) now displays all root patterns correctly instead of showing "No specific patterns documented"

## Session 107 Summary (COMPLETE ✓)

**Completed**:
- ✓ Created Related Psalms Librarian module
- ✓ Integrated related psalms into ResearchBundle
- ✓ Updated pipeline stats tracking
- ✓ Modified DOCX generator to show similar psalms count
- ✓ Tested with Psalm 25 (found 10 related psalms including Ps 34)
- ✓ Updated all session documentation

## Session 106 Summary (COMPLETE ✓)

**Completed**:
- ✓ Analyzed Ps 25-34 ranking position (#534)
- ✓ Generated Top 550 connections file
- ✓ Documented score distributions and cutoffs
- ✓ Updated session documentation

## Session 105 Summary (COMPLETE ✓)

**Completed**:
- ✓ Built ETCBC morphology cache (5,353 entries from Psalms)
- ✓ Fixed cache builder for Hebrew consonantal forms
- ✓ Improved fallback root extraction (3-letter minimum)
- ✓ Implemented 10% gap penalty per word (max 50%)
- ✓ Root extraction: 80% improvement on test cases
- ✓ Re-ran V4.2 migration with improved root extraction
- ✓ Re-ran V4.2 scoring with gap penalty
- ✓ Validated results and verified gap penalty working

## V6 Regeneration Plan (NEXT SESSION)

### Overview
Generate V6 completely fresh from tanakh.db and current morphology.py (Session 115 fixes). No dependency on V3/V4/V5 files.

### Why V6?
- V5 reused old V4 roots/phrases (generated before Session 115 morphology fixes)
- V5 database skipgrams are correct, but JSON deduplicated_roots/phrases are wrong
- Clean regeneration ensures all data uses fixed morphology

### V6 Generation Steps

**Step 1: Extract Fresh Roots & Phrases from All Psalms**
- Script: Create new `scripts/statistical_analysis/extract_psalm_patterns_v6.py`
- Input: `database/tanakh.db` (psalm text)
- Uses: `src/hebrew_analysis/morphology.py` (Session 115 fixes)
- Output: `data/analysis_results/psalm_patterns_v6.json`
- Contains for each psalm pair:
  - Shared roots with IDF scores and verse locations
  - Shared contiguous phrases (2-4+ words) with verse locations
  - Word counts for normalization

**Step 2: Reuse V5 Skipgram Database** (Already Correct)
- Database: `data/psalm_relationships.db` (335,720 skipgrams)
- Table: `psalm_skipgrams` with correct `pattern_roots`
- Quality filtering already applied (content words + stoplist)
- No regeneration needed - V5 skipgrams are good

**Step 3: Generate V6 Scores**
- Script: Create new `scripts/statistical_analysis/generate_v6_scores.py`
- Inputs:
  - Fresh roots/phrases from Step 1
  - V5 skipgram database from Step 2
  - Psalm word counts
- Processing:
  - Cross-pattern deduplication (phrases vs skipgrams vs roots)
  - Gap penalty for skipgrams (10% per gap word, max 50%)
  - Content word bonus (25% for 2 content words, 50% for 3+)
  - IDF filtering for roots (threshold 0.5)
  - Rare root bonus (2x for IDF >= 4.0)
- Output: `data/analysis_results/enhanced_scores_v6.json`

**Step 4: Generate V6 Top 550**
- Script: `scripts/statistical_analysis/generate_top_550_v6.py`
- Input: V6 scores from Step 3
- Output: `data/analysis_results/top_550_connections_v6.json`

### Implementation Notes

**Extraction Script Design** (Step 1):
```python
# Extract patterns for all psalm pairs
for psalm_a in range(1, 151):
    for psalm_b in range(psalm_a + 1, 151):
        # Get text from tanakh.db
        words_a = get_psalm_words(psalm_a)
        words_b = get_psalm_words(psalm_b)

        # Extract roots using Session 115 morphology
        roots_a = extract_roots_with_verses(words_a)
        roots_b = extract_roots_with_verses(words_b)

        # Find shared roots
        shared_roots = find_shared_roots(roots_a, roots_b)

        # Extract contiguous phrases
        phrases_a = extract_contiguous_phrases(words_a, 2, 6)
        phrases_b = extract_contiguous_phrases(words_b, 2, 6)

        # Find shared phrases
        shared_phrases = find_shared_phrases(phrases_a, phrases_b)

        # Store with verse tracking
```

**Key Features**:
- Uses current `HebrewMorphologyAnalyzer` with Session 115 fixes
- Tracks verse numbers for all matches
- Calculates IDF scores fresh from all 150 psalms
- No dependency on any previous version files

### Expected Results

**V6 vs V5 Differences**:
- Skipgrams: Identical (reusing V5 database)
- Contiguous phrases: FIXED (all roots extracted correctly)
- Shared roots: FIXED (all roots extracted correctly)
- Scores: Different (better accuracy with correct roots)

**Validation**:
- `שִׁ֣יר חָדָ֑שׁ` → "שיר חדש" ✓
- `וּמִשְׁפָּ֑ט` → "שפט" ✓
- `שָׁמַ֣יִם` → "שמים" ✓
- `שִׁנָּ֣יו` → "שן" ✓

### Next Session Tasks

1. Create `extract_psalm_patterns_v6.py` extraction script
2. Create `generate_v6_scores.py` scoring script
3. Create `generate_top_550_v6.py` top connections script
4. Run V6 generation pipeline
5. Validate results against user-reported errors
6. Update documentation

---

## Possible Next Actions (Legacy - V5)

V5 system has bugs in deduplicated_roots/phrases. Use V6 instead. Consider:

1. **Validate Bug Fixes** (Recommended Next Step)
   - Verify "ענוים" now correctly maps to "ענו" (not "עני")
   - Confirm "ושנאת" extracts to "שׂנא" (not "נא")
   - Check that "כי את" no longer appears in top 550 results
   - Verify matches_from_a/b arrays are populated (not empty)
   - Confirm database contains 378,836 skipgrams (not 0 bytes)

2. **Analyze V5 Quality Improvements**
   - Compare specific psalm pairs between V4 and V5
   - Investigate patterns that gained/lost significant scores
   - Validate that filtered patterns were indeed formulaic

3. **Further Quality Refinements** (Optional - Priority 4-5)
   - Implement pattern-level IDF weighting
   - Refine gap penalty based on content words
   - Tune stoplist based on V5 results

4. **Analyze Specific Psalm Connections (using V5)**
   - Investigate specific pairs from Top 550 V5
   - Look for theological/liturgical patterns
   - Compare with Hirsch commentary

5. **Statistical Analysis**
   - Study score distribution patterns in V5
   - Identify clusters of related psalms
   - Analyze by psalm genre/type

6. **Export for External Analysis**
   - Generate visualizations comparing V4 vs V5
   - Create network graphs
   - Export to spreadsheet formats

## Key Improvements - Recent Sessions

### Session 112: V5 Bug Fixes (2025-11-16)

**Critical Bug Fixes**:
1. **ETCBC Cache Error** - Fixed "ענוים" mapping (עני → ענו)
   - Prevents false semantic matches between "affliction" and "humility"
2. **Root Extraction** - Fixed over-stripping (require 4+ letters when removing "ש")
   - Fixes: "ושנאת" now → "שׂנא" (not "נא")
3. **Empty Matches Arrays** - Fixed field name mismatch
   - Preserves verse-level match data in V5 output
4. **V5 Database Empty** - Regenerated with quality filtering
   - 378,836 quality-filtered skipgrams (141 MB)
5. **Stoplist Not Applied** - Fixed by database regeneration
   - High-frequency formulaic patterns now properly filtered
6. **V5 Scoring** - Regenerated with all fixes applied

**Impact**: V5 system fully operational with accurate matching, complete data, and proper filtering

### Session 111: V5 Quality Filtering (2025-11-16)

1. **Content Word Filtering (Priority 1)**
   - Hebrew word classifier with linguistic categories
   - Filters patterns based on content word count
   - Removed 7.6% of formulaic patterns before deduplication

2. **Pattern Stoplist (Priority 2)**
   - JSON-based stoplist for high-frequency formulaic patterns
   - 22 skipgram patterns, 19 contiguous patterns
   - Targets liturgical formulas (מזמור דוד) and divine name patterns (יהוה אל)

3. **Content Word Bonus (Priority 3)**
   - 25% score bonus for patterns with 2 content words
   - 50% score bonus for patterns with 3+ content words
   - Promotes semantically meaningful patterns

4. **Database Schema (V5)**
   - Added `content_word_count`, `content_word_ratio`, `pattern_category` fields
   - Enables future analysis of pattern quality
   - 379,220 quality-filtered skipgrams stored

5. **V5 Results**
   - Average skipgrams reduced 34.2% (4.4 → 2.9 per connection)
   - Better signal-to-noise ratio
   - 73 connection changes in top 550 (higher quality patterns promoted)

### Session 106: Ranking Analysis & Top 550
- **Generated**: Top 550 connections file (extends Top 500)
- **Captures**: Ps 25-34 at position #534
- **File**: `data/analysis_results/top_550_connections_skipgram_dedup_v4.json`
- **Score Range**: 1,087.38 to 183.97

### Session 105: ETCBC Morphology & Gap Penalty

1. **ETCBC Morphology Cache**
   - 5,353 morphological mappings from Psalms
   - ETCBC BHSA 2021 scholarly database
   - 80% improvement in root extraction

2. **Improved Fallback Root Extraction**
   - Require 3 letters after prefix stripping
   - Prevents over-stripping like "שוא" → "וא"

3. **Gap Penalty for Skipgrams**
   - Formula: `value = base * (1.0 - min(0.1 * gap_count, 0.5))`
   - Contiguous phrases valued higher than gappy skipgrams

## Files Modified - Recent Sessions

### Session 112:
**Bug Fixes**:
- `src/hebrew_analysis/data/psalms_morphology_cache.json` - Fixed "ענוים" root entry
- `src/hebrew_analysis/morphology.py` - Fixed fallback root extraction (4+ letter requirement)
- `scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v4.py` - Fixed empty matches bug

**Data Regeneration**:
- `data/psalm_relationships.db` - Regenerated with 378,836 quality-filtered skipgrams (141 MB)
- `data/analysis_results/enhanced_scores_skipgram_dedup_v5.json` - Regenerated with all fixes
- `data/analysis_results/top_550_connections_skipgram_dedup_v5.json` - Regenerated with all fixes

**Documentation Updates**:
- `docs/IMPLEMENTATION_LOG.md` - Session 112 entry with bug fix details
- `docs/PROJECT_STATUS.md` - Updated to Session 112 complete
- `docs/NEXT_SESSION_PROMPT.md` - This file

### Session 111:
**New Files**:
- `src/hebrew_analysis/word_classifier.py` - Hebrew linguistic word classifier
- `src/hebrew_analysis/data/pattern_stoplist.json` - Formulaic pattern stoplist
- `scripts/statistical_analysis/generate_top_550_skipgram_dedup_v5.py` - V5 top 550 generator
- `scripts/statistical_analysis/compare_v4_v5_top_550.py` - V4 vs V5 comparison
- `data/analysis_results/enhanced_scores_skipgram_dedup_v5.json` - V5 scores (37 MB)
- `data/analysis_results/top_550_connections_skipgram_dedup_v5.json` - V5 top 550 (3.7 MB)

**Core Changes**:
- `scripts/statistical_analysis/skipgram_extractor_v4.py` - Quality filtering implementation
- `scripts/statistical_analysis/migrate_skipgrams_v4.py` - V5 schema with content metadata
- `scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v4.py` - Content word bonus scoring
- `data/psalm_relationships.db` - Rebuilt with V5 quality-filtered patterns (379,220 skipgrams)

**Documentation Updates**:
- `docs/IMPLEMENTATION_LOG.md` - Session 111 entry
- `docs/PROJECT_STATUS.md` - Updated to V5 status
- `docs/NEXT_SESSION_PROMPT.md` - This file

### Session 106:
**New Files**:
- `data/analysis_results/top_550_connections_skipgram_dedup_v4.json` - Extended top connections

**Documentation Updates**:
- `docs/IMPLEMENTATION_LOG.md` - Session 106 entry
- `docs/PROJECT_STATUS.md` - Updated current status
- `docs/NEXT_SESSION_PROMPT.md` - This file

### Session 105:
**Core Changes**:
- `src/hebrew_analysis/cache_builder.py` - ETCBC API fixes
- `src/hebrew_analysis/morphology.py` - Fallback extraction improvements
- `scripts/statistical_analysis/skipgram_extractor_v4.py` - Added gap_word_count
- `scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v4.py` - Gap penalty

**New Files**:
- `src/hebrew_analysis/data/psalms_morphology_cache.json` - ETCBC morphology cache

## Important Notes

1. **V5 vs V4 Available**:
   - V5 (current): Quality-filtered with all bugs fixed - **RECOMMENDED** (Session 112)
   - V4: Previous version without quality filtering - Available for comparison
   - Both have Top 550 connections files
   - V5 now has accurate matching, complete data, and proper filtering

2. **V5 Quality Filters**:
   - Content word filtering: Requires 1+ content words for 2-word patterns, 2+ for 3+ word skipgrams
   - Pattern stoplist: Removes 41 high-frequency formulaic patterns
   - Content word bonus: 25-50% scoring boost for multi-content patterns

3. **ETCBC Cache Coverage**: Cache includes all words from Psalms. Words from other books use improved fallback extraction.

4. **Gap Penalty Applied**: 10% per gap word (max 50%). Contiguous patterns valued higher than gappy skipgrams.

5. **All Data Current**: V5 migration and scoring complete with all improvements and bug fixes applied (Session 112).

## Reference

- **Project Docs**: `/docs/`
- **Implementation Log**: `/docs/IMPLEMENTATION_LOG.md` (Through Session 112)
- **Database**: `/data/psalm_relationships.db` (V5 - 378,836 skipgrams)
- **Scripts**: `/scripts/statistical_analysis/`

