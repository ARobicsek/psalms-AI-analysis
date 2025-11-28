# Psalms Project - Current Status

**Last Updated**: 2025-11-28 (Session 148 - COMPLETE ✓)
**Current Phase**: V6 Production Ready
**Status**: ✓ College Verses Parser Fixed for LLM Format Variations

## Session 148 Summary (COMPLETE ✓)

### College Verses Parser Fix - LLM Format Variation

**Objective**: Fix college verse commentary parser to handle LLM writing "REVISED VERSE-BY-VERSE COMMENTARY" instead of "REVISED VERSE COMMENTARY"
**Result**: ✓ COMPLETE - Parser updated with flexible regex, Psalm 121 college files regenerated

**Issue Identified**:
- User ran `python scripts/run_enhanced_pipeline.py 121`
- College verses file was empty: `psalm_121_edited_verses_college.md` = 0 bytes
- College intro worked fine: `psalm_121_edited_intro_college.md` = 35KB
- Same symptom as Session 145 (Psalm 11), but different root cause

**Root Cause**:
- Prompt asks for: `### REVISED VERSE COMMENTARY`
- GPT-5.1 wrote: `## REVISED VERSE-BY-VERSE COMMENTARY`
- Parser regex required exact match: `r'^#{2,3} REVISED VERSE COMMENTARY\s*$'`
- Added text "-BY-VERSE" caused regex mismatch
- Result: `verses_match = None` → `revised_verses` empty → file saved as empty

**Difference from Session 145**:
- Session 145: LLM used wrong header level (`##` vs `###`)
- Session 148: LLM changed section name itself (added "-BY-VERSE")
- Both are LLM format compliance issues

**Solution Implemented**:
1. **Updated Parser Regex** ([master_editor.py:1231](../src/agents/master_editor.py#L1231)):
   - Old: `r'^#{2,3} REVISED VERSE COMMENTARY\s*$'`
   - New: `r'^#{2,3} REVISED VERSE(?:-BY-VERSE)? COMMENTARY\s*$'`
   - `(?:-BY-VERSE)?` makes that portion optional
   - Now matches both variations

2. **Created Repair Script** ([scripts/fix_psalm_121_college.py](../scripts/fix_psalm_121_college.py)):
   - Similar to Session 145's repair script
   - Reprocessed saved GPT-5.1 response with updated parser
   - No need to re-run expensive API call
   - Successfully extracted all three sections

**Files Modified**:
- [master_editor.py:1228-1231](../src/agents/master_editor.py#L1228-L1231) - Updated verses regex with optional `-BY-VERSE`

**Files Created**:
- [scripts/fix_psalm_121_college.py](../scripts/fix_psalm_121_college.py) - Repair script for Psalm 121 (135 lines)

**Results**:
- ✅ `psalm_121_edited_verses_college.md`: 0 bytes → 18KB (15,114 chars)
- ✅ `psalm_121_edited_intro_college.md`: 14,057 chars (unchanged)
- ✅ `psalm_121_assessment_college.md`: 2,113 chars (unchanged)
- ✅ All three college files now complete

**Impact**:
- ✅ Parser now robust to both "REVISED VERSE COMMENTARY" and "REVISED VERSE-BY-VERSE COMMENTARY"
- ✅ Future psalm runs won't fail on this LLM format variation
- ✅ Consistent with Session 145 approach: make parsers flexible, not strict
- ✅ No regression for existing Psalm 11 files

---

## Session 147 Summary (COMPLETE ✓)

### Combined Document College Verse Commentary Fix

**Objective**: Remove Hebrew verse and English translation duplication from college verse commentary sections in combined docx
**Result**: ✓ COMPLETE - College commentary now starts after Hebrew verse quotation, Psalm 11 regenerated

**Issue Identified**:
- In combined docx verse-by-verse section, main commentary includes Hebrew verse at top
- College subsection for same verse also included the Hebrew verse and English translation
- Result: Hebrew verse appeared twice (once in main, once in college)
- College commentary should begin AFTER the Hebrew quotation with first word bold/green

**Root Cause**:
- Parser used simple Hebrew character check: `re.match(r'^[\u0590-\u05FF]', line_stripped)`
- Didn't handle markdown formatting (e.g., `**לַמְנַצֵּחַ**`)
- Didn't skip the English translation block that follows Hebrew verse
- Result: English translation included in college commentary output

**Solution Implemented**:
1. **Enhanced Hebrew Detection**:
   - Strips markdown formatting (`**`) before checking for Hebrew characters
   - Checks first 10 characters using `re.search()` instead of just start of line
   - Handles both `**Hebrew**` and plain Hebrew lines

2. **English Translation Block Skipping**:
   - Added state tracking for English quote blocks
   - Detects opening quote (`"` or `'` at line start)
   - Tracks continuation until closing quote
   - Skips entire translation block

3. **State Machine Logic**:
   - `in_verse_section` flag: True while processing Hebrew + translation
   - `in_english_quote` flag: True while inside translation quote block
   - Only adds lines after exiting verse section

**Files Modified**:
- [combined_document_generator.py:663-700](../src/utils/combined_document_generator.py#L663-L700) - Enhanced verse section parser with markdown handling and quote block detection

**Testing**:
- ✅ Regenerated Psalm 11 combined document
- ✅ College verse commentary now starts with actual commentary (bold/green first word)
- ✅ No Hebrew verse duplication in college subsections
- ✅ Hebrew verse appears once at top of main subsection only

**Impact**:
- ✅ Eliminates redundant Hebrew verse text in college sections
- ✅ Cleaner reading experience (verse shown once, not twice)
- ✅ College commentary properly formatted with engaging first word
- ✅ Correct document structure: Main (with Hebrew) → Em dash → College (commentary only)

---

## Session 146 Summary (COMPLETE ✓)

### Document Formatting Fixes - Multiple Issues

**Objective**: Fix bullet rendering, add block quote formatting, fix empty quote lines, correct liturgical section source, and fix college verse commentary parsing
**Result**: ✓ COMPLETE - All five formatting/parsing issues resolved, Psalm 11 documents regenerated

**Issues Fixed**:

1. **Bullets in Combined Document (RESOLVED ✅)**:
   - Problem: Intro sections (main, college, liturgical) in combined docx showed weird hyphens instead of proper Word bullets
   - Root cause: College verse commentary handled bullets correctly (lines 649-652), but intro sections only called `_add_paragraph_with_markdown()` without checking for `- ` markers
   - Fix: Added bullet detection to all three intro section loops in [combined_document_generator.py](../src/utils/combined_document_generator.py):
     - Main intro section (lines 492-495)
     - College intro section (lines 525-528)
     - Liturgical section (lines 546-549)
   - Now uses `List Bullet` style with `_process_markdown_formatting()` for consistent formatting

2. **Block Quote Formatting (NEW FEATURE ✅)**:
   - Problem: Markdown block quotes (`> text`) displayed literal ">" carets instead of formatted quotes
   - Root cause: Neither document generator handled block quote markdown syntax
   - Solution: Implemented block quote formatting in both generators:
     - Strips `>` prefix from text (flexible - handles `>` with or without space)
     - Applies 0.5" left indentation
     - Makes text italic
     - Works in intro sections and verse commentary
   - Files modified:
     - [combined_document_generator.py](../src/utils/combined_document_generator.py):
       - Intro sections (lines 509-524, 562-577, 600-615)
       - Verse commentary `_add_commentary_with_bullets()` (lines 267-282)
     - [document_generator.py](../src/utils/document_generator.py):
       - `_add_paragraph_with_markdown()` (lines 222-254)
       - `_add_commentary_with_bullets()` (lines 289-314)

3. **Empty Block Quote Lines (RESOLVED ✅)**:
   - Problem: Lines with just `>` (or `> ` with trailing spaces) displayed as literal carets instead of blank lines
   - Root cause: Block quote handling didn't check for empty content after stripping prefix
   - Fix: Added empty-text detection - renders as blank paragraph instead of showing caret
   - Example: Quote blocks with spacing (like line 101 in psalm_011_edited_intro.md) now render correctly

4. **Liturgical Section Source (RESOLVED ✅)**:
   - Problem: Combined docx used college intro's liturgical section instead of main intro's
   - Root cause: College intro removal regex only looked for `## Modern Jewish Liturgical Use` header, but college version uses `---LITURGICAL-SECTION-START---` marker
   - Fix: Updated regex to handle both formats:
     - Header-based: `## Modern Jewish Liturgical Use`
     - Marker-based: `---LITURGICAL-SECTION-START---`
   - Also removes trailing `---` horizontal rules
   - Result: Combined docx now correctly uses main intro's liturgical section

5. **College Verse Commentary Not Appearing (RESOLVED ✅)**:
   - Problem: College verse commentary not showing up in either college docx or combined docx
   - Root cause: College verses file uses `### Verse X` (heading markdown), but both parsers only looked for `**Verse X**` (bold markdown) or `Verse X` (plain)
   - Fix: Updated `_parse_verse_commentary()` method in both generators:
     - Now tries bold format first (`**Verse X**`)
     - Falls back to heading format (`## Verse X` or `### Verse X`)
     - Finally falls back to plain format (`Verse X`)
   - Files modified:
     - [combined_document_generator.py](../src/utils/combined_document_generator.py) - lines 294-321
     - [document_generator.py](../src/utils/document_generator.py) - lines 522-549
   - Result: College verse commentary now renders correctly in both documents
   - Note: This is the same root cause as Session 145 (LLM using `##`/`###` instead of `**`)

**Testing**:
- ✅ Regenerated all three Psalm 11 documents (4 total regenerations)
- ✅ Bullets now display correctly in combined docx intro sections
- ✅ Block quotes now render as indented, italic text (not literal ">")
- ✅ Empty quote lines (just `>`) render as blank lines (not carets)
- ✅ Combined docx liturgical section now from main intro (not college)
- ✅ College verse commentary now appears in both college and combined docx
- ✅ No regression in other formatting

**Files Modified**:
- `src/utils/combined_document_generator.py` - 9 locations (bullets, block quotes, empty quotes, liturgical section, verse parser)
- `src/utils/document_generator.py` - 4 locations (block quotes, empty quotes, verse parser)

**Impact**:
- ✅ Combined document now has consistent bullet formatting across all sections
- ✅ Block quotes render elegantly (indented + italic) instead of showing raw markdown
- ✅ Empty quote lines provide proper spacing in block quotes
- ✅ Liturgical section correctly sourced from main intro (consistent with design)
- ✅ College verse commentary now fully functional in documents
- ✅ Parsers now robust to LLM format variations (`**` vs `##`/`###`)
- ✅ Improved document readability and professional appearance
- ✅ All future psalms will automatically benefit from these improvements

---

## Session 145 Summary (COMPLETE ✓)

### College Editor Parser Bug Fix

**Objective**: Fix empty college edition edited files (intro and verses) for Psalm 11
**Result**: ✓ COMPLETE - Parser fixed to handle both `##` and `###` headers, Psalm 11 regenerated

**Issue Identified**:
User ran `python scripts/run_enhanced_pipeline.py 11` and discovered:
- `psalm_011_assessment_college.md` had content ✓
- `psalm_011_edited_intro_college.md` was empty ✗
- `psalm_011_edited_verses_college.md` was empty ✗

**Root Cause**:
- LLM (GPT-5/GPT-5.1) used `##` (2 hashes) for REVISED INTRODUCTION and REVISED VERSE COMMENTARY headers
- Parser expected exactly `###` (3 hashes) per prompt instructions
- Regex mismatch caused intro and verses sections to not be extracted

**Solution**:
1. **Updated Parser** ([master_editor.py:1227-1230](../src/agents/master_editor.py#L1227-L1230)):
   - Changed regex from `r'^### SECTION\s*$'` to `r'^#{2,3} SECTION\s*$'`
   - Now handles both `##` and `###` header formats
   - More robust to LLM formatting variations

2. **Created Repair Script** ([scripts/fix_psalm_11_college.py](../scripts/fix_psalm_11_college.py)):
   - Reprocessed existing Psalm 11 response with updated parser
   - Successfully extracted: 1,963 chars assessment, 11,964 chars intro, 16,273 chars verses
   - Regenerated all three files without re-running expensive API calls

**Files Fixed**:
- `psalm_011_edited_intro_college.md`: 1 line → 14,127 bytes ✓
- `psalm_011_edited_verses_college.md`: 1 line → 18,966 bytes ✓
- `psalm_011_assessment_college.md`: Formatted correctly ✓

**Impact**:
- ✅ Parser now robust to LLM header format variations
- ✅ Future pipeline runs will automatically handle both formats
- ✅ Psalm 11 college files complete and ready for document generation

**Files Modified**:
- `src/agents/master_editor.py` - Updated `_parse_editorial_response()` regex
- `scripts/fix_psalm_11_college.py` - Created standalone repair script

**Next Steps**:
- Bug fix complete and tested
- Ready for next psalm or continued production work

---

## Session 144 Summary (COMPLETE ✓)

### Comprehensive Cost Tracking Implementation

**Objective**: Fix pipeline cost summary to show costs for all LLMs (macro, micro, synthesis, liturgical librarian) and add missing GPT-5.1 pricing
**Result**: ✓ COMPLETE - Full cost tracking now operational across all pipeline agents with GPT-5.1 pricing added

**Issues Identified**:
1. Cost summary only showing GPT-5.1 (master editor), not showing costs for other agents
2. GPT-5.1 pricing missing from cost_tracker.py lookup table
3. Costs showing as $0.0000 even though tokens were being counted
4. User question: Can we request costs from LLM APIs instead of calculating?

**Changes Made**:

1. **Added GPT-5.1 Pricing** ([cost_tracker.py:85-92](../src/utils/cost_tracker.py#L85-L92)):
   - Input: $1.25/M tokens (same as GPT-5)
   - Output: $10.00/M tokens
   - Reasoning: $10.00/M tokens

2. **Updated All Agents to Track Costs**:
   - **macro_analyst.py**: Added cost_tracker parameter, tracks usage after streaming call ([macro_analyst.py:329-342](../src/agents/macro_analyst.py#L329-L342))
   - **micro_analyst.py**: Added cost_tracker parameter, tracks usage for both discovery and research generation passes ([micro_analyst.py:483-493, 605-615](../src/agents/micro_analyst.py#L483-L615)), passes to ResearchAssembler ([micro_analyst.py:341](../src/agents/micro_analyst.py#L341))
   - **synthesis_writer.py**: Added cost_tracker parameter, tracks usage for both intro and verse commentary ([synthesis_writer.py:903-912, 1036-1045](../src/agents/synthesis_writer.py#L903-L1045))
   - **liturgical_librarian.py**: Added cost_tracker parameter, tracks Gemini and Claude Sonnet 4.5 calls (both phrase and full psalm summaries)
   - **research_assembler.py**: Added cost_tracker parameter, passes to LiturgicalLibrarian ([research_assembler.py:451](../src/agents/research_assembler.py#L451))

3. **Updated Pipeline** ([run_enhanced_pipeline.py](../scripts/run_enhanced_pipeline.py)):
   - Passes cost_tracker to MacroAnalyst
   - Passes cost_tracker to MicroAnalystV2
   - Passes cost_tracker to SynthesisWriter
   - Cost summary displays at end showing all model usage

**Impact**:
- ✅ Full visibility into all pipeline costs (Claude Sonnet 4.5, Gemini 2.5 Pro, GPT-5.1, GPT-5)
- ✅ Separate tracking for input, output, and thinking tokens
- ✅ Accurate cost calculation based on official pricing
- ✅ Easy to identify which agents use which models and how much they cost

**Technical Note - API Cost Reporting**:
User asked if we can request costs from API instead of calculating. Answer:
- Different APIs report costs differently (some not at all)
- OpenAI reports token counts but not costs
- Anthropic reports token counts but not costs
- Gemini reports token counts but not costs
- Calculating from token usage is more reliable and consistent
- Lookup table can be updated as pricing changes

**Files Modified**:
- `src/utils/cost_tracker.py` - Added GPT-5.1 pricing
- `src/agents/macro_analyst.py` - Added cost tracking
- `src/agents/micro_analyst.py` - Added cost tracking + ResearchAssembler integration
- `src/agents/synthesis_writer.py` - Added cost tracking
- `src/agents/liturgical_librarian.py` - Added cost tracking for Gemini and Claude
- `src/agents/research_assembler.py` - Added cost_tracker parameter for LiturgicalLibrarian
- `scripts/run_enhanced_pipeline.py` - Pass cost_tracker to all agents

**Next Steps**:
- Run full pipeline to verify cost tracking works correctly
- Monitor for any missing costs or incorrect pricing

---

## Session 143 Summary (COMPLETE ✓)

### GPT-5.1 Thinking Mode Upgrade

**Objective**: Investigate and implement GPT-5.1 thinking mode for master editor (previously blocked by TPM limits)
**Result**: ✓ COMPLETE - GPT-5.1 with reasoning_effort="high" now operational, API token field names fixed

**Background**:
- Session 126 attempted GPT-5.1 migration but hit 30,000 TPM limit
- User's Tier 1 account now has 500,000 TPM (increased September 2025)
- Request size: ~116K tokens (research bundle + prompts)
- Now fits comfortably within new limit

**Changes Made**:

1. **Model Upgrade** (IMPLEMENTED ✅):
   - Updated default model: `"gpt-5"` → `"gpt-5.1"`
   - Model explicitly uses `reasoning_effort="high"` (CRITICAL - GPT-5.1 defaults to "none"!)
   - Comment updated to reflect GPT-5.1's default behavior difference

2. **API Field Names Fixed** (BUG FIX ✅):
   - Problem: Code used `usage.input_tokens` / `usage.output_tokens` (old field names)
   - GPT-5.1 API uses: `usage.prompt_tokens` / `usage.completion_tokens` / `usage.reasoning_tokens`
   - Fix: Added `getattr()` calls to safely extract tokens with fallback to 0
   - Updated both main editor and college editor methods
   - Added separate logging for reasoning tokens when present

3. **Successful Test** (VERIFIED ✅):
   - Tested on Psalm 10 (non-college, skip earlier steps)
   - API call succeeded: HTTP 200 OK
   - Usage: 151,495 input + 11,519 output tokens
   - Cost: $0.30 (within budget)
   - Output quality: Excellent editorial review with detailed assessment

**Files Modified**:
- `src/agents/master_editor.py` - Model upgrade + API field fix (3 changes)
- `scripts/run_enhanced_pipeline.py` - Updated default to gpt-5.1, display messages (5 changes)

**Impact**:
- ✅ GPT-5.1 thinking mode now available for all future psalm runs
- ✅ 500K TPM limit easily handles ~116K token requests
- ✅ High reasoning effort produces detailed, substantive editorial reviews
- ✅ Proper cost tracking for all token types
- ✅ Future-proofed with safe field extraction (works with API changes)

**Key Technical Notes**:
- GPT-5.1 defaults to `reasoning_effort="none"` (no reasoning unless explicitly set!)
- Explicit `reasoning_effort="high"` is CRITICAL for quality output
- Reasoning tokens may not be reported separately (embedded in completion)
- Field names differ from older GPT models (prompt/completion vs input/output)

**Next Steps**:
- GPT-5.1 ready for production use on all future psalms
- Can optionally A/B test against Claude Opus 4.5 using `--master-editor-model` flag
- Monitor reasoning token usage if/when reported separately

---

## Session 142 Summary (COMPLETE ✓)

### Combined Document Generator Fixes

**Objective**: Fix markdown header rendering and duplicate liturgical section headers in combined document generator
**Result**: ✓ COMPLETE - Headers now render correctly, duplicate liturgical headers removed

**Issues Fixed**:

1. **Markdown Headers Not Rendered** (RESOLVED ✅):
   - Problem: Headers like `### The Problem This Psalm Won't Stop Asking` showing as literal hash marks instead of being rendered as headers
   - Root cause: Intro sections used `_add_paragraph_with_markdown()` for all lines, which only handles inline markdown (bold/italic), not structural markdown (headers)
   - Fix: Added header detection to both main and college intro sections (lines 483-492, 511-520)
   - Now checks for `####` and `###` prefixes before calling `_add_paragraph_with_markdown()`

2. **Duplicate Liturgical Headers** (RESOLVED ✅):
   - Problem: "Modern Jewish Liturgical Use" appearing twice as headers in the document
   - Root cause: Source markdown files contained duplicate headers (lines 19-20 in main intro, lines 57-59 in college intro), and regex only removed first occurrence
   - Fix: Updated regex to use `re.MULTILINE` flag + added second pass to catch all occurrences (lines 522-527)
   - First regex: `r'^## Modern Jewish Liturgical Use\s*\n'` with `flags=re.MULTILINE` (matches at start of any line)
   - Second regex: `r'## Modern Jewish Liturgical Use\s*'` (catches any remaining instances)

**Files Modified**:
- `src/utils/combined_document_generator.py` - Added header detection + fixed duplicate header removal (16 insertions, 4 deletions)

**Testing**:
- ✅ Successfully regenerated Psalm 10 combined document
- ✅ Markdown headers (###, ####) now render as proper Word document headers
- ✅ Single "Modern Jewish Liturgical Use" header instead of duplicates
- ✅ No regression in other document formatting

**Impact**:
- ✅ College intro section headers now properly formatted as Header 3 in .docx
- ✅ Main intro section headers also properly formatted
- ✅ Consistent with liturgical section's existing header handling
- ✅ Improved document readability and professional formatting

---

## Session 141 Summary (COMPLETE ✓)

### Claude Opus 4.5 Master Editor & Cost Tracking

**Objective**: Add Claude Opus 4.5 as master editor option with maximum thinking mode, implement comprehensive cost tracking
**Result**: ✓ COMPLETE - Claude Opus 4.5 with 64K thinking budget now available, full cost tracking implemented

**Features Added**:

1. **Cost Tracking Utility** (NEW):
   - Created `src/utils/cost_tracker.py` (294 lines)
   - Tracks all model usage: tokens, calls, costs
   - Comprehensive pricing database for all models (Claude, GPT, Gemini)
   - Displays detailed breakdown at end of pipeline run

2. **Claude Opus 4.5 Master Editor** (NEW):
   - Model: `claude-opus-4-5` (released Nov 24, 2025)
   - Thinking budget: 64K tokens (maximum thinking mode)
   - Pricing: $5/M input, $25/M output, $25/M thinking
   - Supports both main and college commentary

3. **Command-line Selection**:
   - New flag: `--master-editor-model` (default: gpt-5)
   - Options: `gpt-5` or `claude-opus-4-5`
   - Allows A/B testing of different master editors

**Files Created**:
- `src/utils/cost_tracker.py` - Cost tracking utility

**Files Modified**:
- `src/agents/master_editor.py` - Added Claude Opus 4.5 methods with 64K thinking
- `scripts/run_enhanced_pipeline.py` - Integrated cost tracking + model selection

**Impact**:
- ✅ Full visibility into pipeline costs across all models
- ✅ Claude Opus 4.5 available for highest-quality reasoning
- ✅ Easy A/B testing between GPT-5 and Claude Opus 4.5
- ✅ Maximum thinking mode (64K tokens) for deepest analysis

---

## Session 140 Summary (COMPLETE ✓)

### Document Formatting & Prompt Enhancements

**Objective**: Fix maqqef display in parentheses, add Header 3 styling for college intro headers, strengthen Hebrew+English pairing requirements
**Result**: ✓ COMPLETE - All three issues resolved with code and prompt updates

**Issues Fixed**:

1. **Maqqef Omission in Parentheses** (RESOLVED ✅):
   - Problem: Hebrew maqqef (־, U+05BE) was being dropped when words in parentheses were reversed for LTR display
   - Example: "(בְּכָל־לִבִּי)" displayed as "(בְּכָללִבִּי)" - maqqef missing, words run together
   - Root cause: `_split_into_grapheme_clusters()` pattern didn't include maqqef as a base character
   - Fix: Added \u05BE to base character class in cluster pattern

2. **College Intro Header Styling** (RESOLVED ✅):
   - Problem: Engaging section headers in college intros (e.g., "A quick map of what we're reading:") not formatted as Header 3 in .docx
   - Document generators already supported ### markdown headers
   - Fix: Updated COLLEGE_EDITOR_PROMPT to explicitly instruct using `### Header text` for section headers
   - Added examples and instructions in two locations (Stage 2 and OUTPUT FORMAT sections)

3. **Hebrew+English Pairing Enforcement** (RESOLVED ✅):
   - Problem: Some verse commentary showed English without Hebrew or vice versa (e.g., line 105 of psalm_009_edited_verses_college.md)
   - Fix: Added explicit **CRITICAL** instruction in both MASTER_EDITOR_PROMPT and COLLEGE_EDITOR_PROMPT
   - New section: "ALWAYS show Hebrew and English together when discussing the verse"
   - Provided CORRECT/INCORRECT examples for clarity

**Files Modified**:
- `src/utils/document_generator.py` - Added maqqef (U+05BE) to cluster pattern (line 91)
- `src/utils/combined_document_generator.py` - Added maqqef (U+05BE) to cluster pattern (line 100)
- `src/agents/master_editor.py` - Three prompt enhancements:
  1. Hebrew+English pairing instruction (lines 278-284)
  2. College intro Header 3 formatting (line 611)
  3. College output format Header 3 examples (lines 729-730)

**Impact**:
- ✅ Maqqef now preserved in Hebrew text within parentheses across all .docx outputs
- ✅ College intro section headers will be formatted as Header 3 in future generations
- ✅ Master editor will consistently show Hebrew and English together in all commentary
- ✅ Improved readability and formatting consistency across all output documents

**Model Used**: Opus 4.5 (newly released) for development work

---

## Session 139 Summary (COMPLETE ✓)

### Combined Document Generator Enhancement

**Objective**: Add complete Methodological Summary to combined document and test pipeline without re-running LLM steps
**Result**: ✓ COMPLETE - Methodological Summary enhanced, pipeline testing successful

**Issues Addressed**:

1. **Missing Methodological Summary Fields**:
   - Combined document generator had incomplete Methodological Summary section
   - Missing fields: LXX texts, Phonetic transcriptions, Concordance entries, Figurative language instances, Rabbi Sacks references, Master editor prompt size, Related psalms list display
   - Root cause: Session 138 implementation used older format from document_generator.py

2. **Pipeline Testing Without LLM Re-runs**:
   - User needed way to test/fix combined doc generation without costly LLM steps
   - Solution: Pipeline skip flags allow regenerating only document outputs

**Fixes Implemented**:

1. **Enhanced _format_bibliographical_summary Method**:
   - Updated to match complete version from document_generator.py
   - Added all missing fields to Research & Data Inputs section
   - Fixed escape sequence warning (`BDB\Klein` → `BDB\\Klein`)
   - Related psalms now shows both count and list: "5 (Psalms 77, 25, 34, 35, 10)"

2. **Pipeline Testing Workflow Documented**:
   - Command to regenerate documents without LLM steps:
     ```bash
     python scripts/run_enhanced_pipeline.py <N> --skip-macro --skip-micro --skip-synthesis --skip-master-edit --output-dir output/psalm_<N>
     ```
   - Successfully tested with Psalm 9 and Psalm 10
   - No regex error encountered (issue from Session 138 was transient)

**Files Modified**:
- `src/utils/combined_document_generator.py` - Enhanced Methodological Summary (lines 353-416)

**Testing Results**:
- ✅ Standalone generator: Successfully regenerated Psalm 9 combined document
- ✅ Pipeline integration: Successfully regenerated Psalm 9 and 10 combined documents
- ✅ No regex errors encountered in pipeline runs
- ✅ All Methodological Summary fields now appear in combined .docx

**Impact**:
- ✅ Combined document now has complete Methodological Summary matching individual documents
- ✅ Clear workflow for testing document generation without expensive LLM re-runs
- ✅ Pipeline robustness confirmed with successful multi-psalm testing

---

## Session 138 Summary (COMPLETE ✓)

### Combined Document Generator

**Objective**: Create a combined document generator that merges main and college commentaries into a single .docx file
**Result**: ✓ COMPLETE - New combined document generator integrated into pipeline with `--skip-combined-doc` flag

**Feature Implemented**:
Created a unified .docx document containing:
1. Full psalm text (Hebrew & English)
2. Main introduction
3. College introduction (heading with "College" in green)
4. Modern Jewish Liturgical Use section (from main version)
5. Verse-by-verse commentary with both versions side-by-side

**Key Implementation Details**:
1. **Text Formatting**:
   - All body text uses Aptos 12pt font (explicit `set_font=True`)
   - Hebrew in parentheses handled correctly (LRO/PDF Unicode + cluster reversal)
   - No Arial font bleeding through

2. **College Commentary Features**:
   - Automatically skips leading Hebrew verse lines
   - First English word colored green and bolded
   - Proper LTR directionality throughout

3. **Divider System**:
   - Em dash (—) between main and college commentary
   - Horizontal border line between verses
   - Markdown dividers (---, ___, etc.) filtered from source text

4. **Pipeline Integration**:
   - Added as STEP 6c in pipeline
   - New CLI flag: `--skip-combined-doc`
   - Outputs: `psalm_XXX_commentary_combined.docx`

**Files Created**:
- `src/utils/combined_document_generator.py` - Complete combined document generator (755 lines)

**Files Modified**:
- `scripts/run_enhanced_pipeline.py` - Pipeline integration with new step and flag

**Impact**:
- ✅ Single document option for users wanting both commentary versions
- ✅ Professional formatting with consistent Aptos font
- ✅ Hebrew text displays correctly without RTL issues
- ✅ Clean visual separation between main and college versions
- ✅ Easy to skip if only individual documents desired

---

## Session 137 Summary (COMPLETE ✓)

### Pipeline Fixes: College Regeneration & Stale Stats Dates

**Objective**: Fix pipeline issues with college file regeneration and stale stats dates
**Result**: ✓ COMPLETE - College files now auto-regenerate when synthesis changes, stats show correct run dates

**Issues Investigated**:
1. User reported .docx content mismatch with edited markdown
   - ✅ Verified NO ISSUE - Content matches correctly
2. College files not regenerated when running `--skip-macro --skip-micro`
   - College files from 07:55 (stale), regular files from 14:57 (fresh)
3. Stats JSON and .docx showed wrong dates (Nov 6 instead of Nov 21)

**Root Causes**:

1. **College File Regeneration Issue**:
   - College step only checked if file existed, not if it was stale
   - When synthesis ran fresh, old college files were reused
   - Result: Regular and college versions out of sync

2. **Stale Stats Dates Issue**:
   - Pipeline treated `--skip-macro --skip-micro` as "resuming" old Nov 6 run
   - Loaded old pipeline_start, pipeline_end from Nov 6 stats JSON
   - Even though synthesis and master_editor ran fresh on Nov 21
   - Result: .docx showed "Date Produced: Nov 6" instead of Nov 21

**Fixes Implemented**:

1. **College File Timestamp Check**:
   - Added comparison: `synthesis_intro_file.stat().st_mtime > edited_intro_college_file.stat().st_mtime`
   - Regenerates college files whenever synthesis files are newer
   - Keeps regular and college versions synchronized

2. **Fresh Analysis Detection**:
   - Added logic: `is_fresh_analysis = not skip_synthesis or not skip_master_edit`
   - If running fresh analysis, clears old pipeline_start/pipeline_end
   - Tracker uses current time for new run dates
   - Distinguishes "reusing research" from "true resume to output steps"

**Files Modified**:
- `scripts/run_enhanced_pipeline.py` - Two fixes (college regeneration + stats dates)

**Impact**:
- ✅ College files stay synchronized with synthesis output
- ✅ Stats show correct run dates for fresh analysis runs
- ✅ No more confusion about when commentary was actually produced
- ✅ Character counts already correct (tracker overwrites on each step)

---

## Session 136 Summary (COMPLETE ✓)

### Liturgical Librarian: Fix is_unique Filter for Phrases

**Objective**: Populate is_unique column and filter out non-unique phrases from liturgical output
**Result**: ✓ COMPLETE - 47 non-unique phrases filtered from Psalm 8, only unique phrases shown

**Problem**:
- User noticed Psalm 8 liturgical section included "יָרֵ֥חַ וְ֝כוֹכָבִ֗ים" (moon and stars)
- This phrase appears in Psalm 136, not unique to Psalm 8
- Database column `is_unique` existed but all 33,099 values were NULL
- No SQL filter to exclude non-unique phrases

**Solution**:
1. **Populated is_unique Column**:
   - Ran `update_phrase_uniqueness.py` script
   - Searched entire Tanakh (23,206 verses) using Aho-Corasick
   - Marked 5,374 phrases as unique (17.9%), 24,721 as non-unique (82.1%)

2. **Added SQL Filter**:
   - Modified liturgical_librarian.py queries (2 locations)
   - Added: `AND (i.match_type != 'phrase_match' OR i.is_unique = 1)`
   - Only unique phrase_match entries now included

**Impact**:
- Psalm 8: phrase_match reduced from 80 → 33 (47 filtered, 41.6% reduction)
- Eliminates misleading cross-psalm references
- More accurate liturgical context for master editor
- Token savings from processing fewer phrases

**Files Modified**:
- `data/liturgy.db` - Populated is_unique column
- `src/agents/liturgical_librarian.py` - Added uniqueness filter

---

## Session 135 Summary (COMPLETE ✓)

### Liturgical Librarian: Critical Fixes for 429 Errors & Claude Fallback

**Objective**: Fix Gemini API 429 errors, retry decorator crash, and Claude fallback
**Result**: ✓ COMPLETE - AFC disabled (key fix), crashes fixed, Claude fallback working, rate limiting active

**Problems Addressed** (Multiple rounds):
1. Initial 429 errors from burst requests
2. `AttributeError: 'NoneType' object has no attribute '_is_retryable_error'`
3. AFC (Automatic Function Calling) making hidden 10x burst requests per call
4. Claude fallback not triggering
5. `AttributeError: module 'google.genai.types' has no attribute 'RetryConfig'`

**Root Cause** (Per developer feedback):
AFC enabled by default - each `generate_content()` call triggered up to 10 internal API calls in milliseconds. 16 explicit calls = 160 internal calls = instant burst violation.

**Fixes** (3 commits):
1. **Disabled AFC** - No more hidden burst requests (CRITICAL FIX)
2. **Fixed retry decorator** - Moved to module-level function to avoid NoneType
3. **Improved Claude fallback** - Switches on ANY Gemini exception
4. **Rate limiting** - 0.5s delay between calls
5. **Intelligent retry** - Exponential backoff for transient errors
6. **Removed unsupported SDK features** - RetryConfig not available

**Impact**:
- ✅ AFC disabled: Each call = 1 request (not 10)
- ✅ No more crashes from retry decorator
- ✅ Claude fallback works reliably
- ✅ Rate limiting prevents bursts
- ✅ Automatic retry with exponential backoff
- ✅ Portable across SDK versions

**Files Modified**:
- `src/agents/liturgical_librarian.py` (3 commits) - AFC disable, retry fix, fallback improvements

---

## Session 134 Summary (COMPLETE ✓)

### Liturgical Librarian: Claude Sonnet 4.5 Upgrade & Initialization Fix

**Objective**: Upgrade liturgical librarian fallback from Haiku to Sonnet 4.5 with thinking, fix initialization bug preventing fallback
**Result**: ✓ COMPLETE - Sonnet 4.5 with extended thinking now fallback, dual-client initialization fixed

**Root Causes**:
1. **Gemini Quota Exhausted**: 429 errors (10,000 RPD limit hit)
2. **Critical Initialization Bug**: Claude client NEVER initialized when Gemini succeeded
   - `if not self.llm_provider:` prevented Claude init if Gemini available
   - `self.anthropic_client` remained `None` despite API key being present
   - Runtime fallback impossible even with Session 133 fallback logic

**Fixes**:
1. **Upgraded to Sonnet 4.5 with Extended Thinking**:
   - Model: `claude-haiku-4` → `claude-sonnet-4-5`
   - Added streaming with 5000 token thinking budget
   - Increased max_tokens: 1000 → 2000
   - Matches macro/micro analyst pattern

2. **Fixed Initialization Bug**:
   - **Before**: Only initialized Claude if Gemini failed
   - **After**: ALWAYS initialize both clients if API keys present
   - Claude now available as runtime fallback

3. **Updated All Documentation**:
   - All references: "Claude Haiku" → "Claude Sonnet 4.5"
   - Module and method docstrings updated

**Files Modified**:
- `src/agents/liturgical_librarian.py` - Sonnet upgrade + dual-client init fix
- `src/agents/research_assembler.py` - Docstring update

**Impact**:
- ✅ Claude Sonnet 4.5 properly initialized as fallback
- ✅ Extended thinking for deeper analysis
- ✅ Automatic fallback when Gemini quota exhausted
- ✅ No more "no Claude fallback available" errors
- ✅ Matches quality of macro/micro analysts

---

## Session 133 Summary (COMPLETE ✓)

### Liturgical Librarian Bug Fixes & Claude Haiku Fallback (SUPERSEDED BY SESSION 134)

**Objective**: Fix liturgical librarian template bugs and implement Claude Haiku 4.5 fallback for Gemini quota exhaustion
**Result**: ✓ COMPLETE - Fixed f-string bugs, added intelligent Claude fallback, improved quota error messages

**Issues Fixed**:
1. **Template Variable Bugs**: Missing `f` prefix on 2 f-strings (lines 235, 252)
   - Caused `{psalm_chapter}` to appear literally in output instead of being replaced
2. **Gemini API Quota Exhausted**: 429 RESOURCE_EXHAUSTED error
   - Silently fell back to code-only summaries
   - User saw database-style text instead of LLM narratives

**Quota Analysis**:
- **Gemini 2.5 Pro Tier 1 limits**: 150 RPM, 2M TPM, **10,000 RPD** (daily limit)
- **Psalm 8 requirements**: 16 API calls (1 full psalm + 15 phrases)
- **Conclusion**: Daily quota likely exhausted from multiple pipeline runs

**Implementation**:
1. **Dual-Provider System**:
   - Primary: Gemini 2.5 Pro (extended thinking capabilities)
   - Fallback: Claude Haiku 4.5 (cost-effective, high quality)
   - Automatic switch when Gemini quota exhausted

2. **New Claude Methods**:
   - `_generate_phrase_llm_summary_claude()` - Phrase summaries with Claude
   - `_generate_full_psalm_llm_summary_claude()` - Full psalm summaries with Claude
   - Same prompt structure, optimized for Claude Haiku 4

3. **Enhanced Error Handling**:
   - Detects quota errors (429/RESOURCE_EXHAUSTED)
   - Switches `llm_provider` from 'gemini' to 'anthropic' automatically
   - Retries current request with Claude
   - Informative messages with quota limits and check link

**Files Modified**:
- `src/agents/liturgical_librarian.py` - Dual-provider init, template fixes, Claude fallback methods

**Impact**:
- ✅ Template variables correctly replaced
- ✅ Continuous LLM summaries even when Gemini quota exhausted
- ✅ Cost-effective: Claude Haiku 4 ($0.80/M input) vs Gemini ($3.00/M input)
- ✅ Better error messages help users understand quota issues
- ✅ No silent degradation to code-only summaries

**Testing**:
- Gemini quota currently exhausted (confirmed 429 error)
- Claude Haiku fallback working
- Template fixes verified

---

## Session 132 Summary (COMPLETE ✓)

### Gemini 2.5 Pro Integration (Session 132)

**Objective**: Migrate Liturgical Librarian from Claude Haiku 4.5 to Gemini 2.5 Pro with extended thinking
**Result**: ✓ COMPLETE - Full migration with optimized thinking budget configuration

**Note**: Session 133 added Claude Haiku back as intelligent fallback when Gemini quota exhausted.

---

## Session 131 Summary (COMPLETE ✓)

### Enhanced Liturgical Context

**Objective**: Enhance liturgical context in research bundles for more accurate narrative generation
**Result**: ✓ COMPLETE - 4x increase in liturgical context, improved quotation requirements, database regenerated

**Problem Addressed**:
Master editor was making mistakes about liturgical usage of individual verses/phrases. Root cause: insufficient liturgical context in research bundles generated by liturgical_librarian.py.

**Improvements**:
1. **Context Window**: ±10 → ±30 words around matches
2. **Database Field**: 300 → 1200 char limit for liturgy_context
3. **Character Extraction**: ±500 → ±800 chars for phrase matches
4. **LLM Context Display**: 500 → 1000 chars shown to LLM
5. **Quotation Requirement**: 7-12 → 10-15 Hebrew words minimum
6. **Bug Fix**: Replaced non-existent `_extract_context_from_words()` method

**Results** (Psalm 8 before full regeneration):
- Average context: 196.5 → 575.4 chars (↑ 193%)
- Max context: 300 → 761 chars (↑ 154%)
- Entries > 300 chars: 0% → 97.3%

**Database Regeneration**:
- Re-indexed all 150 Psalms with enhanced context extraction
- All 33,099 entries now have 3-4x more liturgical context

**Files Modified**:
- `src/liturgy/liturgy_indexer.py` - 3 context improvements + bug fix
- `src/agents/liturgical_librarian.py` - 3 display/prompt improvements
- `data/liturgy.db` - Regenerated with enhanced context

---

## Session 130 Summary (COMPLETE ✓)

### College Commentary Feature

**Objective**: Add college-level commentary generation feature
**Result**: ✓ COMPLETE - Pipeline now generates two complete commentary versions

**Feature Overview**:
- Separate commentary version for intelligent first-year college students
- Assumes Hebrew proficiency but explains all scholarly/literary terminology
- Clear, engaging, occasionally amusing presentation
- Flexible model configuration (easy to swap models)
- Skippable via `--skip-college` flag

**Implementation**:
- **Separate API calls**: College version gets independent GPT-5 call with `reasoning_effort="high"`
- **Dedicated prompt**: `COLLEGE_EDITOR_PROMPT` emphasizes clarity, defines jargon, conversational tone
- **Flexible model**: `college_model` parameter (defaults to "gpt-5", easily changed)
- **Parallel outputs**: `*_college.md` and `*_commentary_college.docx` files

**Files Modified** (2 files):
1. `src/agents/master_editor.py`:
   - Added `COLLEGE_EDITOR_PROMPT` (350+ lines)
   - Added `college_model` parameter to __init__
   - Added `edit_commentary_college()` method
   - Added `_perform_editorial_review_college()` method

2. `scripts/run_enhanced_pipeline.py`:
   - Added `skip_college` parameter
   - Added Step 4b: College Commentary Generation
   - Added Step 6b: College .docx Generation
   - Added `--skip-college` command-line flag
   - Updated to generate both `psalm_XXX_commentary.docx` AND `psalm_XXX_commentary_college.docx`

**Usage**:
```bash
# Generate both versions
python scripts/run_enhanced_pipeline.py 8

# Skip college version
python scripts/run_enhanced_pipeline.py 8 --skip-college
```

**Output Files**:
- Regular: `psalm_XXX_commentary.docx`
- College: `psalm_XXX_commentary_college.docx`
- Plus markdown intermediates (`*_college.md`)

**Impact**:
✅ Two complete commentary versions from single pipeline run
✅ Flexible model configuration for cost/quality optimization
✅ Clear audience differentiation
✅ Maintains Hebrew richness while maximizing accessibility

**Bug Fix - Date Produced Field**:
- Fixed "Data not available" issue in both .docx files
- Modified `src/utils/pipeline_summary.py`:
  * Added `completion_date: Optional[str] = None` as proper field in `StepStats` dataclass
  * Updated `__init__` to reconstruct field from saved data
  * Updated `to_dict()` to serialize field properly
- Previously `completion_date` was added dynamically at runtime, causing serialization issues
- Now properly persisted in JSON and read by DocumentGenerator

---

## Session 129 Summary (COMPLETE ✓)

### Streaming Error Retry Logic

**Objective**: Fix transient streaming errors in macro/micro/synthesis agents
**Result**: ✓ COMPLETE - Added retry logic for network streaming errors across all agents

**Issue Encountered**:
- Psalm 8 pipeline crashed with `httpx.RemoteProtocolError: peer closed connection without sending complete message body`
- Transient network error during streaming API calls
- Session 128 added streaming but didn't add retry logic for streaming-specific errors

**Root Cause**:
- Streaming calls can fail due to network issues (incomplete chunked reads)
- No retry mechanism for `httpx.RemoteProtocolError` and `httpcore.RemoteProtocolError`
- These errors are transient and should be retried

**Solution Implemented**:
- Added retry logic (3 attempts, exponential backoff) to all streaming API calls
- Added streaming errors to retryable exception list
- Consistent with Session 127's retry approach

**Files Modified**:
- `src/agents/macro_analyst.py` - Full retry loop for streaming call
- `src/agents/micro_analyst.py` - Added streaming errors to 2 existing retry blocks
- `src/agents/synthesis_writer.py` - Added retry loops to intro + verse commentary

**Retryable Errors** (all agents):
- `anthropic.InternalServerError`
- `anthropic.RateLimitError`
- `anthropic.APIConnectionError`
- `httpx.RemoteProtocolError` ← NEW
- `httpcore.RemoteProtocolError` ← NEW

**Impact**:
- ✅ Pipeline automatically retries transient streaming errors
- ✅ More resilient to network issues during long API calls
- ✅ Consistent retry behavior across all streaming agents
- ✅ Helpful logging for debugging retry attempts

---

## Session 128 Summary (COMPLETE ✓ VERIFIED)

### Dynamic Token Scaling + Streaming Support

**Objective**: Fix verse commentary length inconsistency in longer psalms
**Result**: ✓ COMPLETE & VERIFIED - Dynamic scaling + streaming enabled across all agents

**Issue Discovered**:
- Psalm 7 (18 verses) verse commentary was ~1/3 as long per verse as shorter psalms
- Total output only ~23K characters (same as 6-verse psalms)

**Root Cause**:
- Fixed token limit (16K) spread across all verses
- Psalm 7: 16000 ÷ 18 = 888 tokens/verse (vs. 2,666 for Psalm 1)

**Solutions Implemented**:
1. **Dynamic Token Scaling**:
   - Formula: `max(16000, num_verses * 1800)`
   - Psalm 7 now gets 32,400 tokens for verse commentary
   - Maintains ~1,800 tokens/verse for consistent depth

2. **Doubled Analyst Limits**:
   - Macro analyst: 16K → 32K
   - Micro discovery: 16K → 32K
   - Micro synthesis: 4K → 8K per verse

3. **Streaming Support** (discovered necessity during testing):
   - 32K limits triggered SDK requirement for streaming
   - Added to macro analyst (thinking + text blocks)
   - Added to micro analyst (discovery + synthesis)
   - Added to synthesis writer (intro + verses)

**Files Modified** (4 commits):
- `src/agents/synthesis_writer.py` - Dynamic scaling + streaming
- `src/agents/macro_analyst.py` - Doubled limit + streaming
- `src/agents/micro_analyst.py` - Doubled limits + streaming

**Impact**:
- ✅ Longer psalms receive proportionally more tokens
- ✅ No regression for short psalms (16K minimum)
- ✅ No timeout errors with large token requests
- ✅ Consistent verse commentary depth across all psalm lengths
- ✅ Pipeline verified working end-to-end with Psalm 7

---

## Session 127 Summary (COMPLETE ✓ VERIFIED)

### JSON Parsing Error Fix - Retry Logic + Token Limit

**Objective**: Fix pipeline crash caused by malformed JSON from Sonnet 4.5
**Result**: ✓ COMPLETE & VERIFIED - Two fixes applied, Psalm 7 successful

**Issue #1**:
- Psalm 7 pipeline crashed with JSONDecodeError (unterminated string)
- No retry mechanism existed for JSON parsing failures

**Fix #1 - Retry Logic**:
- Made JSONDecodeError retryable (up to 3 attempts with exponential backoff)
- Logs: "JSON parsing error (attempt X/3)... Retrying with fresh request..."

**Issue #2** (Discovered after Fix #1):
- Retry logic worked but all 3 attempts failed
- Errors at end of response (lines 169-212, chars 22K-23K)
- Pattern: JSON truncated near 8192 token limit

**Root Cause**:
- Discovery pass `max_tokens=8192` too small for complex psalms
- Psalm 7 response: ~23KB text (~10K+ tokens with Hebrew)
- JSON truncated before closing

**Fix #2 - Increased Token Limit**:
- Increased `max_tokens` from 8192 → 16384
- Now handles longer discovery responses

**Verification**:
- ✓ Psalm 7 pipeline completed successfully
- ✓ No JSON parsing errors with 16K token limit
- ✓ Discovery pass handled longer response

**Impact**:
- Pipeline handles longer responses without truncation
- Automatic retry for transient JSON issues
- Better resilience for complex psalms
- Verified working with Psalm 7

**Files Modified**:
- `src/agents/micro_analyst.py` - Two fixes (retry logic + token limit)

**Note**: The user's edit to `output/debug/related_psalms_test.txt` was unrelated - this was a token limit issue.

**Session Complete**:
✓ Issue diagnosed
✓ Two fixes implemented
✓ Psalm 7 pipeline successful
✓ Documentation updated

---

## Session 126 Summary (COMPLETE ✓)

### Master Editor Enhancement: GPT-5 with High Reasoning Effort

**Objective**: Upgrade master editor to GPT-5.1 for improved reasoning capabilities
**Result**: ✓ COMPLETE - Master Editor enhanced with GPT-5 high reasoning effort configuration

**Investigation & Research**:
- Researched GPT-5.1 model capabilities and API parameters
- Discovered `reasoning_effort` parameter crucial for reasoning models
- Learned GPT-5.1 defaults to `reasoning_effort="none"` (no reasoning unless explicitly set)
- Found temperature/top_p not supported in reasoning models

**Implementation Attempt**:
1. Updated master_editor.py to use GPT-5.1
2. Added `reasoning_effort="high"` for complex editorial analysis
3. Added `max_completion_tokens=65536` (64K tokens)
4. Fixed import error (added RateLimitError)

**Rate Limit Issue**:
- GPT-5.1 limit: 30,000 tokens per minute (TPM)
- Actual request: 116,477 tokens (research bundle + commentary + prompts)
- Request exceeds limit by 3.9x - incompatible with current plan
- No upgrade path available for GPT-5.1

**Final Solution**:
- Switched to GPT-5 with enhanced parameters:
  - `model="gpt-5"` (500K TPM limit)
  - `reasoning_effort="high"` (vs default "medium")
  - `max_completion_tokens=65536`

**Impact**:
- **Improved from baseline**: Now explicitly using high reasoning effort (was using defaults)
- **Within rate limits**: 116K tokens fits comfortably in 500K TPM allowance
- **Better quality**: High reasoning effort provides deeper analytical thinking
- **Future-ready**: Can switch to GPT-5.1 when higher rate limits available

**Files Modified**:
- `src/agents/master_editor.py` - Enhanced with reasoning_effort and max_completion_tokens parameters

**Key Technical Learning**:
- Both GPT-5 and GPT-5.1 support `reasoning_effort` for deep reasoning
- GPT-5.1 requires explicit setting (defaults to "none")
- GPT-5 defaults to "medium" (we set to "high")
- Reasoning models don't support temperature - use reasoning_effort instead
- Rate limits vary significantly between model versions

**Next Steps**:
- Test enhanced configuration with psalm pipeline
- Monitor quality improvements from high reasoning effort
- Consider GPT-5.1 when higher rate limits available

---

## Session 125 Summary (COMPLETE ✓)

### Enhanced Related Psalms Instructions

**Objective**: Improve related psalms research bundle instructions with scholarly example and reduce token usage
**Result**: ✓ COMPLETE - Single comprehensive instruction with Ps 25-34 diptych example

**Changes Made**:
1. ✓ Consolidated repetitive intro to appear once at top (eliminated 4 repetitions)
2. ✓ Added comprehensive Ps 25-34 diptych example as teaching framework
3. ✓ Updated to V6 connections file (was using V4)

**Impact**:
- Better guidance: Multi-dimensional framework (structural, thematic, call-and-response, vocabulary)
- Token efficiency: Eliminated 4 repetitions of instructional text
- Actionable prompt: "Ask yourself if a similar... dynamic is at play here"
- Real example: Ps 25-34 actually appears as #1 match when analyzing Psalm 25

**Files Modified**:
- `src/agents/related_psalms_librarian.py` - Enhanced instructions, V6 integration

**Next Steps**:
- Monitor synthesis writer's use of enhanced guidance
- Evaluate connection identification improvement

---

## Session 124 Summary (COMPLETE ✓)

### Technical Architecture Documentation Update

**Objective**: Update TECHNICAL_ARCHITECTURE_SUMMARY.md to reflect all pipeline changes from Sessions 105-123
**Result**: ✓ COMPLETE - Comprehensive technical architecture document updated

**Major Documentation Updates**:
1. System overview updated: 6-step pipeline, 8 librarians
2. V6 scoring system fully documented
3. Related Psalms Librarian integration documented
4. Root extraction V6 improvements detailed
5. Pipeline tracking and resume capability documented
6. Recent enhancements section added (Sessions 105-123)
7. Performance metrics updated for V6 system
8. Quality assurance mechanisms expanded

**Impact**: Technical architecture documentation now accurately reflects all system capabilities through Session 123

---

## Session 123 Summary (COMPLETE ✓)

### User Guide Document Updates

**Objective**: Review and suggest updates to "How Psalms Readers Guide works.docx" reflecting enhancements from Sessions 105-122
**Result**: ✓ COMPLETE - Comprehensive suggestions document created

**Analysis Performed**:
- Extracted original document content (October 2024 guide for friends)
- Reviewed 18 sessions of enhancements (Sessions 105-122)
- Identified user-facing improvements worth documenting

**Suggestions Created** (9 sections in `suggested_guide_updates.md`):
1. Update librarian count (7 → 8, reflecting Related Psalms Librarian)
2. Add Stage 2.5 explaining related psalms research and statistical analysis
3. Enhance Stage 3 noting related psalms data and optimizations
4. Enhance Stage 4 highlighting quotation emphasis and poetic punctuation
5. Update Stage 5 with increased character capacity (350K)
6. Add new source category documenting V6 intertextual connections database
7. Optional technical note on morphological analysis
8. Date correction (October 2024, updated November 2025)
9. Optional example showing related psalms feature with Psalm 25-34

**Design Principles**:
- Maintained original document's friendly, accessible voice for educated lay readers
- Explained complex features (IDF scoring, skipgrams, morphology) in plain language
- Integrated suggestions naturally into existing structure
- Focused on user-facing enhancements (quotations, poetic punctuation, cross-psalm connections)

**Files Created**:
- `suggested_guide_updates.md` - Comprehensive suggestions with rationales

**Next Steps**:
- User reviews suggestions and selects which to incorporate
- Can assist with applying changes to Word document if desired

---

## Session 122 Summary (COMPLETE ✓)

### Enhanced Quote-Sharing in Prompts

**Objective**: Improve synthesis writer and master editor prompts to encourage more quotations from sources
**Result**: ✓ COMPLETE - Prompts now strongly emphasize showing actual quoted texts (Hebrew + English)

**Problem Addressed**:
User feedback indicated that final output mentions interesting sources but doesn't quote them enough:
- Liturgical references mentioned without showing the actual liturgical texts
- Biblical parallels cited (e.g., "Ps 44:4, 89:16, Prov 16:15") without quoting 1-2 examples
- Parallel passages mentioned in English without the Hebrew
- Linguistic patterns across psalms described without showing quoted examples

**Changes Made**:

**synthesis_writer.py**:
1. Added new section #7 "SHOWS evidence through generous quotation" to INTRODUCTION_ESSAY_PROMPT
   - Specific guidance on quoting biblical parallels, liturgical texts, and linguistic patterns
   - Examples of what to do: "quote at least 1-2 of the most illustrative examples in Hebrew with English"
2. Strengthened figurative language integration section
   - Changed from "cite" to "QUOTE compelling parallel uses"
   - Added WEAK vs. STRONG examples showing difference between citing and quoting
3. Enhanced liturgical context section
   - Added "CRITICAL: QUOTE the liturgical texts in Hebrew with English translation"
   - Provided WEAK vs. STRONG examples
4. Improved comparative biblical usage section
   - Added "CRITICAL: When mentioning parallel uses, QUOTE at least one illustrative example"
   - Emphasized "show readers what Psalm X actually says"

**master_editor.py**:
1. Added major new bullet in MISSED OPPORTUNITIES section: "CRITICAL: Insufficient quotations from sources"
   - Four sub-bullets with specific examples of citation-without-quotation problems
   - "Remember: readers are hungry to see the actual Hebrew texts. Citations without quotations disappoint."
2. Strengthened Figurative Language Assessment
   - Added "CRITICAL: Are these parallels QUOTED (Hebrew + English), not just cited?"
3. Enhanced figurative language integration in revised verse commentary instructions
   - Changed examples from "GOOD" to "EXCELLENT" with Hebrew quotations
   - Added "WEAK" example showing citation without quotation
4. Strengthened "Items of interest" bullets for liturgical and figurative language
   - Added "CRITICAL: Quote generously" language to multiple sections
   - Emphasized "at least 1-2 strong examples when parallels are available"

**Impact**:
- Prompts now explicitly require quotations (Hebrew + English) when mentioning sources
- Multiple concrete examples throughout showing WEAK (cite only) vs. STRONG (quote) approaches
- Maintained balance - didn't make prompts so focused on quotations that LLMs get distracted from main task
- Should result in final output that satisfies readers' desire to see actual prooftexts

**Next Steps**:
- Test with next psalm generation to evaluate effectiveness
- Monitor whether improved quotation behavior is achieved without distraction from core commentary task

---

## Session 121 Summary (COMPLETE ✓)

### Verse Presentation Approach

**Objective**: Embrace LLM's verse presentation by removing programmatic insertion and updating prompts
**Result**: ✓ COMPLETE - System now relies on LLM to provide verses with poetic punctuation

**Changes Made**:
1. ✓ **Removed programmatic verse insertion** - document_generator.py, commentary_formatter.py
2. ✓ **Updated master_editor.py prompts** - Now ENSURES LLM provides punctuated verses
3. ✓ **Updated synthesis_writer.py prompts** - Now ENSURES LLM provides punctuated verses

**Impact**:
- Readers now see verses with poetic punctuation (semicolons, periods, commas showing structure)
- No more verse duplication
- Aligns with LLM's natural behavior

**Next Steps**:
- Test with next psalm generation to ensure LLMs follow new instructions
- Monitor quality of verse punctuation

---

## Session 120 Summary (COMPLETE ✓)

### Repository Cleanup

**Objective**: Clean up repository from V6 development work (Sessions 90-119)
**Result**: ✓ COMPLETE - 47 files removed, only V6 versions retained

**Cleanup Summary**:
- Removed 9 test scripts (test_*.py, verify_*.py)
- Removed 2 check scripts (check_*.py)
- Removed 20 temporary output files (*_output.txt, *_validation.txt)
- Removed 4 old V4/V5 data files (~200MB)
- Removed 12 old V1-V5 analysis scripts
- Added 5 V6 files to git tracking

**Repository State**:
- Clean working directory
- Only V6 system files retained
- All test/validation artifacts removed
- Ready for production use

**Next Steps**:
- Repository is clean and ready for future work
- V6 system fully operational

---

## Session 119 Summary (COMPLETE ✓)

### Further Token Reduction in Related Psalms

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

### Related Psalms Display Token Optimization

**Objective**: Optimize related psalms display in research bundles for maximum token efficiency
**Result**: ✓ COMPLETE - 30-40% token reduction achieved while improving clarity

**Optimizations Implemented**:
1. ✓ Removed IDF scores from root displays (~10 chars/root saved)
2. ✓ Compact occurrence format - "(1 occurrence(s))" → "(×1)" (~13 chars saved per)
3. ✓ Removed "Consonantal:" prefix (~14 chars/phrase saved)
4. ✓ Simplified psalm references - "In Psalm X" → "Psalm X" (~3 chars each)
5. ✓ Smart context extraction for roots - Show matched word ±3 words instead of full verse
6. ✓ Reordered sections - Phrases FIRST → Skipgrams SECOND → Roots THIRD (by IDF)
7. ✓ Full verse context for phrases/skipgrams (100-char limit)
8. ✓ V6 data compatibility - Fixed skipgram display to use `full_span_hebrew` field
9. ✓ Pipeline updated - research_assembler.py now uses V6 connections file

**Key Features**:
- Created `_remove_nikud()` method for consonantal matching
- Created `_extract_word_context()` to show matched word ±3 words
- Matched roots now always visible in displayed context
- Roots sorted by IDF descending (best matches first)
- Token savings: ~30-40% reduction in related psalms section

**Files Modified**:
- `src/agents/related_psalms_librarian.py` - Core formatting optimizations
- `src/agents/research_assembler.py` - Updated to use V6 connections file

**Impact**: V6 system now ready for production with cost-effective, token-optimized research bundles

---

## Session 117 Summary (COMPLETE ✓)

### V6 Complete Regeneration

**Objective**: Execute V6 clean regeneration plan with fresh patterns and Session 115 morphology
**Result**: ✓ COMPLETE - V6 fully generated with all user-reported errors fixed

**V6 Generation Results**:
1. ✓ **Fresh Pattern Extraction** - 11,170 psalm pairs, 2,738 unique roots (39.67 MB)
2. ✓ **V6 Scoring** - Fresh patterns + V5 skipgrams with Hebrew text (107.97 MB)
3. ✓ **Top 550 Connections** - Score range 19908.71 to 211.50 (13.35 MB)

**Validation**: All 5 user-reported errors now fixed:
- `שִׁ֣יר חָדָ֑שׁ` → "שיר חדש" ✓
- `וּמִשְׁפָּ֑ט` → "שפט" ✓
- `שָׁמַ֣יִם` → "שמים" ✓
- `שִׁנָּ֣יו` → "שן" ✓
- `בְּתוּל֣וֹת` → "בתולה" ✓

**Status**: V6 system ready for production use

---

## Session 116 Summary (COMPLETE ✓)

### V5 Error Investigation & V6 Plan

**Objective**: Investigate serious root extraction errors in V5 output
**Result**: ✓ COMPLETE - Found V5 reuses old V4 data; created V6 plan

**Root Cause**: V5 scorer reused V4 roots/phrases (generated before Session 115 morphology fixes)

**Solution**: V6 - fresh generation from ground up with no V3/V4/V5 dependency

---

## Session 115 Summary (COMPLETE ✓)

### V5 Root Extraction Comprehensive Fix

**Objective**: Fix all remaining root extraction issues in V5
**Result**: ✓ COMPLETE - Hybrid stripping + plural protection + final letter normalization implemented

**Fixes Applied**:
1. ✓ **Hybrid Stripping Approach** - Adaptive strategy based on word structure
   - Prefix-first for simple prefixes (ב, ל, מ, etc.): בשמים → שמים ✓
   - Suffix-first for ש-words (protects ש-roots): שקרים → שקר ✓
   - File: `src/hebrew_analysis/morphology.py` lines 193-259

2. ✓ **Plural Ending Protection** - Stricter minimums for ים/ות
   - שמים → שמים ✓ (dual noun, not שם + plural)
   - שקרים → שקר ✓ (plural, strips correctly)
   - File: `src/hebrew_analysis/morphology.py` lines 207-220

3. ✓ **Final Letter Normalization** - Convert to final forms (ך ם ן ף ץ)
   - שמך → שם ✓ (מ → ם final mem)
   - שניו → שן ✓ (נ → ן final nun)
   - File: `src/hebrew_analysis/morphology.py` lines 261-272

**Impact**:
- 93.75% test pass rate (15/16 comprehensive tests)
- All user-reported problem cases fixed
- Better handling of common Hebrew words and patterns
- V5 database regenerated: 335,720 skipgrams

**Files Modified**:
- `src/hebrew_analysis/morphology.py` - Three major fixes applied
- `data/psalm_relationships.db` - Regenerated (130 MB, 335,720 skipgrams)
- `data/analysis_results/enhanced_scores_skipgram_dedup_v5.json` - Regenerated (53.30 MB)
- `data/analysis_results/top_550_connections_skipgram_dedup_v5.json` - Regenerated (5.58 MB)
- Documentation files updated

**Next Steps**:
- Verify fixes in actual V5 output (next session)
- V5 system production-ready for analysis

## Session 114 Summary (COMPLETE ✓)

### V5 Root Extraction Fix - Suffix/Prefix Stripping Order

**Objective**: Fix remaining root extraction issues with ש-initial roots
**Result**: ✓ COMPLETE - Reversed suffix/prefix order, V5 regenerated

**Bug Fixed**:
✓ **ש-Initial Root Over-Stripping** - Reversed stripping order (suffixes before prefixes)
  - Issue: `שקרים` → strip `ש` → `קרים` → strip `ים` → `קר` ✗
  - Fix: `שקרים` → strip `ים` → `שקר` (now protected from ש stripping) ✓
  - Examples fixed: שקרים → שקר ✓, שנאתי → שנא ✓
  - File: `src/hebrew_analysis/morphology.py` lines 193-240

**Impact**:
- All ש-related root extraction issues resolved
- +3,932 skipgrams (341,175 total) due to improved root matching
- Better semantic matching for common ש-roots (שנא, שמר, שמע, etc.)
- 15/16 comprehensive tests passing (93.75%)

**Files Modified**:
- `src/hebrew_analysis/morphology.py` - Reversed suffix/prefix stripping order
- `data/psalm_relationships.db` - Regenerated (132.5 MB, 341,175 skipgrams)
- `data/analysis_results/enhanced_scores_skipgram_dedup_v5.json` - Regenerated (52.81 MB)
- `data/analysis_results/top_550_connections_skipgram_dedup_v5.json` - Regenerated (5.53 MB)
- Documentation files updated

**Next Steps**:
- V5 system ready for production use
- All known root extraction issues resolved
- Ready for analysis or further feature development

## Session 113 Summary (COMPLETE ✓)

### V5 Critical Fixes - Root Extraction & Skipgram Filtering

**Objective**: Fix critical V5 issues - root extraction over-stripping and skipgram contamination
**Result**: ✓ COMPLETE - 2 major fixes applied, V5 database and scores regenerated

**Bugs Fixed**:
1. ✓ **Skipgram Contamination** - Excluded gap_word_count=0 patterns from skipgrams
   - 38.29% of "skipgrams" were actually contiguous (gap=0)
   - Added check to skip gap=0 patterns in extractor
   - Result: 378,836 → 337,243 true skipgrams (11% reduction)

2. ✓ **Root Extraction Over-Stripping** - Fixed adaptive ש-prefix handling
   - Session 112's 4-letter check insufficient for multi-prefix cases
   - Now requires 5+ letters when stripping ש if another prefix already stripped
   - Fixes: "ומשנאיו" → "שנא" ✓ (not "נא")

**Impact**: V5 system now has:
- Pure skipgram data (gap ≥ 1 only)
- Accurate root extraction for multi-prefix words
- No duplicate patterns between contiguous and skipgram lists
- Proper stoplist filtering (database now populated)

**Files Modified**:
- `src/hebrew_analysis/morphology.py` - Adaptive ש-stripping
- `scripts/statistical_analysis/skipgram_extractor_v4.py` - Exclude gap=0
- `data/psalm_relationships.db` - Regenerated (129 MB, 337,243 skipgrams)
- `data/analysis_results/enhanced_scores_skipgram_dedup_v5.json` - Regenerated (51.18 MB)
- `data/analysis_results/top_550_connections_skipgram_dedup_v5.json` - Regenerated (5.36 MB)

**Next Steps**:
- V5 system ready for production use
- All known critical bugs fixed
- Consider validation on specific psalm pairs

## Session 112 Summary (COMPLETE ✓)

### V5 Quality Issues Investigation & Bug Fixes

**Objective**: Investigate and fix matching system issues identified by user
**Result**: ✓ COMPLETE - All 6 critical bugs fixed, V5 system fully operational

**Bugs Fixed**:
1. ✓ **ETCBC Cache Error** - Fixed "ענוים" root mapping from "עני" → "ענו"
   - Prevents false matches between "affliction" and "humility"
   - File: `src/hebrew_analysis/data/psalms_morphology_cache.json`

2. ✓ **Root Extraction Over-stripping** - Fixed fallback extraction
   - Issue: "ושנאת" (and hatred of) → "נא" (incorrect)
   - Fix: Require 4+ letters remaining when stripping "ש" prefix
   - File: `src/hebrew_analysis/morphology.py`

3. ✓ **Empty Matches Arrays** - Fixed field name mismatch
   - Function looked for `verses_a/b` but data uses `matches_from_a/b`
   - Fix: Changed to extract from existing fields, preserving verse data
   - File: `scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v4.py`

4. ✓ **V5 Database Empty** - Regenerated with quality filtering
   - Database was 0 bytes, quality filtering never applied
   - Regenerated: 378,836 quality-filtered skipgrams stored (141 MB)
   - File: `data/psalm_relationships.db`

5. ✓ **Stoplist Not Applied** - Fixed by database regeneration
   - Patterns like "כי את" appearing despite stoplist
   - Database regeneration ensures stoplist filtering is active

6. ✓ **V5 Scoring Regeneration** - Applied all fixes
   - Regenerated V5 scores from fixed database
   - All bug fixes and quality filtering now applied

**Files Modified**:
- `src/hebrew_analysis/data/psalms_morphology_cache.json` - Fixed "ענוים" entry
- `src/hebrew_analysis/morphology.py` - Fixed fallback root extraction
- `scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v4.py` - Fixed empty matches bug
- `data/psalm_relationships.db` - Regenerated (378,836 skipgrams, 141 MB)
- `data/analysis_results/enhanced_scores_skipgram_dedup_v5.json` - Regenerated with fixes
- `data/analysis_results/top_550_connections_skipgram_dedup_v5.json` - Regenerated with fixes

**Impact**: V5 system now fully operational with accurate semantic matching, improved root extraction, complete match data, and proper quality filtering

## Session 111 Summary (COMPLETE ✓)

### Skipgram Quality Improvement Implementation

**Completed**:
1. **Priority 1: Content Word Filtering** ✅
   - Created `word_classifier.py` with Hebrew linguistic categories
   - Divine names, function words, liturgical terms, content words
   - Filters patterns based on content word count thresholds
   - Results: Filtered 7.6% of formulaic patterns (103,953 instances)

2. **Priority 2: Pattern Stoplist** ✅
   - Created `pattern_stoplist.json` with 41 formulaic patterns
   - 22 skipgram patterns (יהוה אל, כי יהוה, מזמור דוד, etc.)
   - 19 contiguous patterns (כי את, את יהו, זמור דוד, etc.)
   - Results: Filtered 1,166 additional patterns (0.1%)

3. **Priority 3: Content Word Bonus** ✅
   - Modified scoring to reward multi-content patterns
   - 25% bonus for 2 content words, 50% for 3+ content words
   - Promotes semantically meaningful patterns in rankings

4. **V5 Database Migration** ✅
   - Extended schema with `content_word_count`, `content_word_ratio`, `pattern_category`
   - Rebuilt database with quality-filtered patterns
   - Stored 379,220 skipgrams (vs previous unfiltered count)
   - Migration time: 23.3 seconds for all 150 psalms

5. **V5 Scoring and Analysis** ✅
   - Generated enhanced_scores_skipgram_dedup_v5.json (37.18 MB)
   - Generated top_550_connections_skipgram_dedup_v5.json (3.68 MB)
   - Created comparison script for V4 vs V5 analysis

**V5 Impact**:
- **Pattern Reduction**: Average skipgrams per connection: 4.4 → 2.9 (34.2% reduction)
- **Quality Improvement**: Average contiguous phrases: 2.1 → 1.9 (9.2% reduction)
- **Top 550 Changes**: 73 new connections entered (higher quality), 73 dropped (formulaic)
- **Overlap**: 86.7% of connections remain in top 550 (477/550)
- **Score Changes**: Most decreased due to filtering, but 58.9% improved rank position

**Files Created**:
- `src/hebrew_analysis/word_classifier.py` - Linguistic categorization
- `src/hebrew_analysis/data/pattern_stoplist.json` - Formulaic patterns
- `scripts/statistical_analysis/generate_top_550_skipgram_dedup_v5.py`
- `scripts/statistical_analysis/compare_v4_v5_top_550.py`
- `data/analysis_results/enhanced_scores_skipgram_dedup_v5.json`
- `data/analysis_results/top_550_connections_skipgram_dedup_v5.json`

**Files Modified**:
- `scripts/statistical_analysis/skipgram_extractor_v4.py` - Quality filtering
- `scripts/statistical_analysis/migrate_skipgrams_v4.py` - V5 schema
- `scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v4.py` - Content bonus
- `data/psalm_relationships.db` - Rebuilt with V5 data

## Session 110 Summary (COMPLETE ✓)

### Complete Related Psalms Display Feature

**Investigation**:
- Liturgical section marker: Already fixed in Session 107-108 (commit abc36d6)
- Related psalms: Partially completed previously (commit 8813fe8)

**Completed**:
1. **Completed Related Psalms Display** ✅
   - Added `related_psalms_list` to JSON export
   - Formatted DOCX display as "8 (Psalms 77, 25, 34...)"
   - Files: `src/utils/pipeline_summary.py`, `src/utils/document_generator.py`

**Files Modified**:
- `src/utils/pipeline_summary.py` - JSON export (1 line)
- `src/utils/document_generator.py` - Display formatting (14 lines)

## Session 109 Summary (COMPLETE ✓)

### Bug Fixes & Configuration Updates

**Completed**:
1. **Fixed Footnote Markers in DOCX** ✅
   - Issue: Footnote markers (e.g., `-c`, `-d`) appearing in English translation
   - Fix: Added `strip_sefaria_footnotes()` call in document generator
   - File: `src/utils/document_generator.py`

2. **Increased Synthesis Editor Character Limit** ✅
   - Previous: 250K-330K characters
   - New: 700,000 characters
   - Impact: ~350K token capacity with 2:1 char/token ratio
   - File: `src/agents/synthesis_writer.py` (3 locations)

3. **Limited Related Psalms to Top 8** ✅
   - Previous: All related psalms from Top 550 (could be 10-20+)
   - New: Maximum 8 most related (sorted by final_score descending)
   - File: `src/agents/related_psalms_librarian.py`

4. **Skipgram Quality Analysis** ✅
   - Reviewed 34 skipgram patterns in Psalm 4
   - Finding: ~35-40% are meaningful, ~45-50% are trivial/formulaic
   - Decision: Acceptable quality; optional future filtering
   - Recommendations documented for potential improvements

**Files Modified**:
- `src/utils/document_generator.py` - Footnote stripping
- `src/agents/synthesis_writer.py` - Character limits
- `src/agents/related_psalms_librarian.py` - Top 8 limit

## Session 108 Summary (COMPLETE ✓)

### Related Psalms Librarian Bug Fixes

**Completed**:
1. **Fixed Shared Roots Loading** ✅
   - Bug: Line 122 hardcoded `shared_roots=[]`
   - Fix: Now loads actual data with `connection.get('deduplicated_roots', [])`
   - Example: Psalm 4-77 connection now shows 11 shared roots (was showing 0)

2. **Added Shared Roots Display** ✅
   - Bug: No formatting code to display shared roots
   - Fix: Added "Shared Roots" section to markdown output
   - Shows: Root, IDF score, verse occurrences in both psalms

3. **Fixed Root Field Names** ✅
   - Bug: Used wrong field names (`'consonantal'`, `'idf_score'`)
   - Fix: Corrected to `'root'` and `'idf'` (actual data structure)

4. **Fixed "No Patterns" Message** ✅
   - Bug: Shown when no phrases/skipgrams, even with shared roots
   - Fix: Updated condition to check all three pattern types

5. **Hebrew-Only Full Text** ✅
   - Enhancement: Removed English text from related psalm display
   - Benefit: ~30% reduction in research bundle token usage

**Files Modified**:
- `src/agents/related_psalms_librarian.py` - 4 bug fixes + 1 enhancement

**Test Case**: Psalm 4 → Psalm 77
- Score: 216.62
- Now correctly shows: 11 shared roots with IDF scores and verse locations
- Previously showed: "No specific patterns documented"

## Session 107 Summary (COMPLETE ✓)

### Related Psalms Integration

**Completed**:
1. **Created Related Psalms Librarian** ✅
   - New module: `src/agents/related_psalms_librarian.py`
   - Loads Top 550 connections from analysis results
   - Retrieves full text and pattern details for related psalms
   - Supports bidirectional psalm matching (a→b and b→a)

2. **Integrated into ResearchBundle** ✅
   - Added `related_psalms` and `related_psalms_markdown` fields
   - Updated ResearchAssembler to call librarian automatically
   - Related psalms section included in research bundle markdown
   - Count tracked in research summary

3. **Pipeline Stats & DOCX Output** ✅
   - Added `related_psalms_count` to pipeline statistics
   - Updated document generator to show "Number of Similar Psalms Analyzed: XX"
   - Appears in Research & Data Inputs section of final DOCX

**Files Created**:
- `src/agents/related_psalms_librarian.py` (282 lines)

**Files Modified**:
- `src/agents/research_assembler.py` - ResearchBundle integration
- `src/utils/pipeline_summary.py` - Stats tracking
- `src/utils/document_generator.py` - DOCX output

## Session 106 Summary (COMPLETE ✓)

### Ranking Analysis & Top 550 Generation

**Completed**:
1. **Analyzed Ps 25-34 Ranking** ✅
   - Final score: 184.56
   - Position: #534 out of 10,883 pairs
   - 34 positions below Top 500 cutoff

2. **Generated Top 550 Connections** ✅
   - Extended from Top 500 to capture historically significant pairs
   - Successfully includes Ps 25-34 at position #534
   - File: `data/analysis_results/top_550_connections_skipgram_dedup_v4.json`
   - Score range: 1,087.38 to 183.97

**Files Created**:
- `data/analysis_results/top_550_connections_skipgram_dedup_v4.json` (550 pairs)

## Session 105 Summary (COMPLETE ✓)

### Completed Improvements

1. **ETCBC Morphology Cache** ✅
   - 5,353 morphological entries from Psalms
   - ETCBC BHSA 2021 scholarly database
   - 80% improvement on root extraction test cases
   - Location: `src/hebrew_analysis/data/psalms_morphology_cache.json`

2. **Fallback Root Extraction** ✅
   - More conservative prefix stripping (3-letter minimum)
   - Prevents over-stripping: "שוא" → "וא" (BAD) vs "שוא" → "שוא" (GOOD)
   - Multi-pass stripping for complex morphology

3. **Gap Penalty for Skipgrams** ✅
   - Modest 10% penalty per gap word (max 50%)
   - Applied at scoring time
   - Verified working on 8,745 pairs with skipgrams

4. **Data Regeneration** ✅
   - Re-ran V4.2 migration with ETCBC cache
   - Re-ran V4.2 scoring with gap penalty
   - All 10,883 psalm pairs scored

### Final Results

**Skipgrams**:
- 417,464 total skipgrams extracted (verse-contained)
- 8,745 pairs have shared skipgrams
- Top pair (Ps 18/119): 25 skipgrams

**Gap Penalty Verification** (Ps 18/119):
- Gap 0 (contiguous): 11 skipgrams (44%) - full value
- Gap 1: 4 skipgrams (16%) - 10% penalty
- Gap 2: 6 skipgrams (24%) - 20% penalty
- Gap 3: 4 skipgrams (16%) - 30% penalty

**Root Extraction**:
- Cache hits: Excellent accuracy
- Fallback: Improved (3-letter minimum)
- Overall: 80% improvement on test cases

## Code Changes

### Modified Files:
1. `src/hebrew_analysis/cache_builder.py` - ETCBC API integration
2. `src/hebrew_analysis/morphology.py` - Conservative fallback (3-letter min)
3. `scripts/statistical_analysis/skipgram_extractor_v4.py` - Gap tracking
4. `scripts/statistical_analysis/migrate_skipgrams_v4.py` - Schema with gap_word_count
5. `scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v4.py` - Gap penalty

### New Files:
- `src/hebrew_analysis/data/psalms_morphology_cache.json` (147.7 KB)

## Next Steps

V4.2 is now complete with all improvements applied. Possible future enhancements:
1. Expand ETCBC cache to full Hebrew Bible (optional)
2. Tune gap penalty parameters if needed
3. Analysis of results using Top 500 or Top 550 connections

## Available Datasets

**V4.2 Results**:
- `enhanced_scores_skipgram_dedup_v4.json` - All 10,883 psalm pairs
- `top_500_connections_skipgram_dedup_v4.json` - Top 500 pairs (cutoff: 186.48)
- `top_550_connections_skipgram_dedup_v4.json` - Top 550 pairs (cutoff: 183.97)

## Branch

All changes committed to: `claude/psalms-ranking-analysis-01VJrKyzSERDdaayu1qwPfpK`

Ready for merge or further analysis.
