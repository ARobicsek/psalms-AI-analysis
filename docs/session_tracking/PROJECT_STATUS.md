# Psalms Project Status

**Last Updated**: 2025-12-30 (Session 229)

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Current System State](#current-system-state)
3. [Recent Work Summary](#recent-work-summary)
4. [Feature Documentation](#feature-documentation)
5. [Session History](#session-history)
6. [Reference Materials](#reference-materials)

---

## Executive Summary

### Current Phase: Pipeline Production
Continuing with tweaks and improvements to the psalm readers guide generation pipeline.

### Progress Summary
- **Current Session**: 229
- **Active Features**: Master Editor V2, Gemini 2.5 Pro Fallback, Deep Web Research Integration, Special Instruction Pipeline, Converse with Editor, Priority-Based Figurative Trimming, Figurative Curator (✅ Active), Tribal Blessings Analyzer (✅ NEW)

---

## Current System State

### Pipeline Phases

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Text Extraction | ✅ Complete | All Tanakh text extracted and stored in SQLite |
| Phase 2: Macro Analysis | ✅ Complete | All psalms analyzed for themes and structure |
| Phase 3: Micro Analysis | ✅ Complete | Verse-by-verse phrase extraction complete |
| Phase 4: Research Assembly | ✅ Complete | Optimizing figurative language search and trimming |
| Phase 5: Synthesis Generation | ✅ Complete | Commentary generation with Gemini fallback |
| Phase 6: Editing and Publication | ✅ Complete | Master Editor V2, DOCX generation |

### Active Features
- **Master Editor V2**: Restructured prompt with explicit Deep Research guidance (default)
- **Gemini 2.5 Pro Fallback**: Handles large psalms (51+ verses) without content loss
- **Deep Web Research Integration**: Supports Gemini Deep Research outputs
- **Strategic Verse Grouping**: Prevents truncation in long psalms with pacing guidance
- **Pipeline Skip Logic**: New `--resume` flag for automatic step detection
- **Figurative Curator**: LLM-enhanced agent that transforms raw figurative concordance data into curated insights using Gemini 3 Pro (fully integrated)

### Known Limitations
- Large psalms may require Gemini fallback (additional cost)
- Deep research must be manually prepared via Gemini browser interface
- Figurative Curator adds ~$0.30-0.50 per psalm to processing cost

---

### Session 229 (2025-12-30): Tribal Blessings Analyzer for Genesis 49
- **NEW Feature**: Created standalone analysis system for Genesis 49 tribal blessings
  - `src/agents/tribal_curator.py` - Adapted FigurativeCurator for non-Psalm passages
  - `scripts/tribal_blessings_analyzer.py` - CLI script for running analysis
- **Capabilities**:
  - Analyzes figurative language for each of the 12 tribes in Genesis 49
  - Searches figurative concordance for vehicles AND tribe-as-target patterns
  - Uses 3-iteration refinement approach with Gemini 3 Pro
  - Generates 1000-2000 word scholarly insights per tribe
  - Includes reception history, cultural impact, and 5+ biblical parallels
  - Supports deep research file integration
- **Output**: Individual tribe markdown files + combined summary in `output/genesis_49/`
- **Design**: Generalizable `PassageAnalysisConfig` pattern for future use on other passages (Deut 33, Numbers 23-24, etc.)

### Session 228 (2025-12-29): Figurative Stats Formatting & Model Tracking
- **Feature**: Added programmatic tracking of LLM models used in the Methods section of Word documents.
  - Exposed `active_model` property in `LiturgicalLibrarian` and `FigurativeCurator`.
  - Updated `ResearchAssembler` to capture models in the `ResearchBundle`.
  - Updated pipeline and document generators to extract and display these models.
- **Fixed**: Incorrect figurative statistics parsing when resuming pipeline by updating `scripts/run_enhanced_pipeline.py`.
- **Formatted**: Updated Word document generators to use inline formatting for figurative matches and renamed label to "**Figurative Concordance Matches Reviewed**".
- **Resolved**: Enabled generation of College/Combined documents when skipping AI steps, decoupling document generation from analysis logic.

### Session 227 (2025-12-29): Figurative Curator - Testing & Finalization
- **Verified Integration**: Confirmed Psalm 23 run produced expected curated output
- **Cost Tracking**: Added `gemini-3-pro-preview` pricing and integrated curator costs into pipeline stats
- **Methods Section**: Updated main and combined DOCX generators to list all figurative parallels reviewed by the curator
- **Documentation**: Marked integration complete

### Session 226 (2025-12-29): Figurative Curator - Production Integration
- Created production module [src/agents/figurative_curator.py](src/agents/figurative_curator.py) with all core functionality
- Modified trimming logic to skip curator output (checks for "(Curated)" marker in section header)
- Fully integrated curator into research assembler with automatic curation and formatted markdown output
- **Blocker**: google-genai package missing in venv (resolved by user before Session 227)

### Session 225 (2025-12-29): Figurative Curator - Comprehensive Output Improvements
- Improved Phase 2 prompt to require 4-5 insights (not 3) and curated examples for ALL vehicles
- Added explicit requirements: 5-15 examples PER vehicle, title imagery analysis, appropriate structure_type
- Ps 22 now produces: 5 insights, 15 vehicle groups, 75 curated examples, correct "descent_ascent" structure
- Updated integration guide with 3 critical reminders: remove trimming, add cost tracking, update Methods section

### Session 223 (2025-12-28): Divine Names Modifier - שְׁדּי vs שַׁדַּי Fix
- Fixed incorrect replacement of שְׁדּי (*shadei* = "breasts") with שְׁקֵי in Psalm 22:10
- Added vowel check to require PATACH (U+05B7) or KAMATZ (U+05B8) under shin for divine name
- Words with SHEVA (U+05B0) under shin (like שְׁדּי) are now correctly excluded

---

## Feature Documentation

### Core Features

#### Master Editor V2 (Session 215) ✅
Completely restructured prompt that is now the default. Key improvements:
- Ground Rules section with unmissable Hebrew+English requirement
- Explicit Deep Research guidance for cultural afterlife and reception history
- "Aha! Moment" focus creating insights that couldn't exist before LLMs
- ~40% reduction in repeated instructions

Usage: `python scripts/run_enhanced_pipeline.py 126` (default)
Old prompt: `python scripts/run_enhanced_pipeline.py 126 --master-editor-old`

#### Gemini 2.5 Pro Fallback (Session 211) ✅
Automatic switching to Gemini for large psalms when research bundle exceeds limits:
- Trimming priority: Related Psalms → Figurative Language → switch to Gemini
- Gemini processes with 1M token context (vs Claude's 200K)
- GPT-5.1 Master Editor remains unchanged
- Cost tracking integrated

#### Strategic Verse Grouping (Session 212) ✅
Prevents truncation in long psalms through intelligent grouping:
- 2-4 thematically related verses can be grouped
- Pacing guidance ensures equal treatment
- No "remaining verses" truncation notes

#### Figurative Curator (Sessions 224-227) ✅ Integrated & Active
LLM-enhanced agent that transforms raw figurative concordance data into curated insights using Gemini 3 Pro:
- **Fully integrated into research assembler** (Session 226)
- Executes searches against figurative language database (50 results/search initial, 30 follow-up)
- Iteratively refines searches (up to 3 iterations) based on gap analysis
- Curates 5-15 examples per vehicle with Hebrew text
- Synthesizes 4-5 prose insights (100-150 words each) for commentary writers
- Adapts structure_type to psalm pattern (journey, descent_ascent, contrast, etc.)
- Cost: ~$0.30-0.50 per psalm

**Integration Status (Session 227)**:
- ✅ Production module created: `src/agents/figurative_curator.py`
- ✅ Trimming logic updated to skip curator output
- ✅ Fully integrated into `ResearchAssembler` with markdown formatting
- ✅ Cost tracking implemented
- ✅ Word doc Methods section updated to list parallels reviewed

Test script: `python scripts/test_figurative_curator.py --psalm 22`
Integration guide: `docs/guides/FIGURATIVE_CURATOR_INTEGRATION.md`

### Research Integration

#### Deep Web Research (Session 209) ✅
Support for manually prepared Gemini Deep Research outputs:
- Store in `data/deep_research/psalm_NNN_deep_research.txt`
- Auto-loads into research bundle
- Included after Concordance in priority

#### Phrase Search Optimization (Sessions 180, 182) ✅
- Fixed word order differences (Session 180)
- Fixed maqqef (־) concatenation bug (Session 180)
- Fixed conceptual vs exact form extraction (Session 182)

### Interactive Tools

#### Converse with Editor (Session 221) ✅
Multi-turn conversation with the Master Editor (GPT-5.1) about a completed psalm commentary:
- Load commentary, research bundle sections, and analysis files
- Interactive context selection with character counts
- Streaming API responses for real-time feedback
- Cost tracking with $1 threshold warnings
- Transcript saving to markdown files

Usage:
```bash
python scripts/converse_with_editor.py 21
python scripts/converse_with_editor.py 21 --edition college
```

Commands during conversation:
- `quit` - Exit and show cost summary
- `save` - Save transcript to markdown file

### Pipeline Features

#### Special Instruction Pipeline (Session 220) ✅
Author-directed commentary revisions without altering standard pipeline:
- Extends `MasterEditorV2` via inheritance (`MasterEditorSI` class)
- Special instruction prompts with "SPECIAL AUTHOR DIRECTIVE" section
- All outputs use `_SI` suffix (never overwrites originals)
- Generates three .docx documents: Main SI, College SI, Combined SI
- Separate pipeline stats tracking (`_SI.json`)

Usage:
```bash
# Create instruction file
echo "Focus on theme of divine refuge..." > data/special_instructions/special_instructions_Psalm_019.txt

# Run SI pipeline
python scripts/run_si_pipeline.py 19
```

#### Skip Logic & Resume (Session 219) ✅
- Fixed skip flags to NEVER run specified steps
- Added `--resume` flag for automatic step detection
- Improved dependency checking

#### Research Bundle Trimming (Session 211) ✅
Progressive trimming strategy:
1. Trim Related Psalms (remove full texts)
2. Remove Related Psalms entirely
3. Trim Figurative Language to 75%
4. Trim Figurative Language to 50%
5. Switch to Gemini 2.5 Pro

Never trimmed: Lexicon, Commentaries, Liturgical, Sacks, Scholarly Context, Concordance, Deep Web Research

### Document Generation

#### Main DOCX Verse Commentary (Session 213) ✅
Fixed missing verse-by-verse commentary in main DOCX:
- Updated regex to handle `**Verses X-Y**` format with en dashes
- Added support for verse ranges
- Both main and combined DOCX now complete

#### Pipeline Stats Tracking (Session 214) ✅
Fixed stats showing zeros when skipping steps:
- Fixed lexicon count regex
- Added verse count tracking from database
- Stats JSON always complete

---

## Session History

### Sessions 200-228: Full Details

#### Session 228 (2025-12-29): Figurative Stats Formatting & Model Tracking
**Objective**: Fix incorrect figurative statistics when resuming the pipeline and improve document formatting/generation logic.

**Problems Identified**:
- "Figurative Language Instances Reviewed" showed incorrect/incomplete counts when skipping micro-analysis (resume mode) due to outdated parsing logic.
- Pipeline prevented generation of College/Combined DOCX files when `--skip-college` was used, even if the source files existed.
- User requested specific formatting change for figurative stats (inline list vs newline) and label change.
- Models used for liturgical librarian and figurative curator were not documented in the Methods section.

**Solutions Implemented**:
1. Updated `scripts/run_enhanced_pipeline.py` to correctly parse the new "Figurative Language Insights (Curated)" section from markdown.
2. Decoupled document generation from AI generation in the pipeline script; docs now generate if files exist, regardless of skip flags.
3. Modified `src/utils/document_generator.py` and `src/utils/combined_document_generator.py` to use inline format `(vehicle (count); ...)` and renamed label to "**Figurative Concordance Matches Reviewed**".
4. Implemented programmatic model tracking:
   - Exposed `active_model` property in `LiturgicalLibrarian` and `FigurativeCurator`.
   - Updated `ResearchAssembler` to capture models in the `ResearchBundle`.
   - Updated pipeline and document generators to extract and display these models.

**Files Modified**:
- `scripts/run_enhanced_pipeline.py` - Updated stats parsing and document generation logic.
- `src/utils/document_generator.py` - Updated formatting and label.
- `src/utils/combined_document_generator.py` - Updated formatting and label.
- `src/agents/liturgical_librarian.py` - Exposed active model.
- `src/agents/figurative_curator.py` - Exposed active model.
- `src/agents/research_assembler.py` - Captured models in bundle.

#### Session 227 (2025-12-29): Figurative Curator - Testing & Finalization
**Objective**: Verify Figurative Curator integration, implement cost tracking, and update document generation.

**Problems Identified**:
- Cost tracking was missing for the new Gemini 3 Pro model used by the curator.
- The "Methods" section in the generated Word documents didn't reflect the comprehensive figurative analysis performed by the curator.

**Solutions Implemented**:
1. Added `gemini-3-pro-preview` pricing to `CostTracker`.
2. Updated `ResearchStats` to track "Figurative Parallels Reviewed" (raw count of search results considered).
3. Integrated curator cost tracking into the main pipeline script.
4. Updated both main and combined document generators to list reviewed figurative parallels in the Methodological Summary.

**Files Modified**:
- `src/utils/cost_tracker.py` - Added Gemini 3 Pro pricing
- `src/utils/pipeline_summary.py` - Added `figurative_parallels_reviewed` field
- `scripts/run_enhanced_pipeline.py` - Integrated curator cost tracking
- `src/utils/document_generator.py` - Updated summary generation
- `src/utils/combined_document_generator.py` - Updated summary generation
- `docs/guides/FIGURATIVE_CURATOR_INTEGRATION.md` - Marked integration complete

#### Session 226 (2025-12-29): Figurative Curator - Production Integration
**Objective**: Integrate Figurative Curator from test script into main pipeline production workflow

**Solutions Implemented**:
1. **Created production module** `src/agents/figurative_curator.py`:
   - Extracted FigurativeCurator class from test script
   - Removed test-specific code (argparse, sample requests, output formatting)
   - Kept core curator functionality with Gemini 3 Pro integration
   - Added tanakh_db_path parameter for flexible database location

2. **Modified trimming logic** in `src/agents/synthesis_writer.py` (lines 969-1018):
   - Added checks for curator output markers: "(Curated)" or "Curated Insights" in section header
   - Skip figurative trimming steps 3 & 4 when curator output detected
   - Logs: "Figurative Language is curated output - skipping trimming (pre-optimized by LLM)"
   - Preserves pre-curated data integrity (5-15 examples per vehicle already optimized)

3. **Fully integrated curator into research assembler** `src/agents/research_assembler.py`:
   - Added imports: FigurativeCurator, FigurativeCuratorOutput, FigurativeSearchRequest
   - Added `figurative_curator_output` field to ResearchBundle dataclass
   - Added `use_figurative_curator` parameter to ResearchAssembler.__init__ (default: True)
   - Curator initialization with graceful fallback if API key missing
   - Convert FigurativeRequest → FigurativeSearchRequest and call curator.curate()
   - Log curator results: insights count, examples count, vehicles count, cost
   - Pass curator output to ResearchBundle

4. **Formatted curator output in research bundle markdown**:
   - Section header: "## Figurative Language Insights (Curated)" (enables trimming skip)
   - Search summary with iterations and total results reviewed
   - **Figurative Parallels Reviewed** list (vehicle: count format) for Methods section
   - Prose insights with titles and verse addresses
   - Curated examples grouped by vehicle with Hebrew text and selection rationale

**Blocker Encountered**:
- Curator initialization failed with "google-genai package not installed" error
- **Root Cause**: Package installed in global Python but not in virtual environment (venv)
- **Solution**: Ran `pip install google-genai` in activated virtual environment
- **Impact**: Integration testing delayed until Session 227

**Pending for Session 227**:
- [ ] Test integration on Psalm 23 (run enhanced pipeline with curator)
- [ ] Fix any bugs discovered during testing
- [ ] Add curator cost to pipeline cost tracking
- [ ] Update Word doc Methods section to extract parallels reviewed list
- [ ] Update FIGURATIVE_CURATOR_INTEGRATION.md to mark integration complete

**Files Modified**:
- `src/agents/figurative_curator.py` - NEW: Production module (extracted from test script)
- `src/agents/synthesis_writer.py` - Skip trimming for curator output (lines 969-1018)
- `src/agents/research_assembler.py` - Full curator integration with markdown formatting

**Environment Requirements**:
- Added dependency: `google-genai` package (install in venv with `pip install google-genai`)
- Requires `GEMINI_API_KEY` in `.env` file

#### Session 225 (2025-12-29): Figurative Curator - Comprehensive Output Improvements
**Objective**: Improve Figurative Curator output quality to produce thorough, comprehensive analysis

**Problems Identified**:
- Only 3 insights produced (expected 4-5)
- Only 5 vehicle groups with curated examples (out of 16 searched)
- Only 15 total curated examples (should be 5-15 PER vehicle)
- Title imagery ("hind of the dawn" in Ps 22) not analyzed despite 28 results
- Structure type defaulted to "journey" when actual pattern was descent/contrast

**Solutions Implemented**:
1. Added explicit vehicle count tracking: "you have {N} vehicles with results - provide examples for ALL of them"
2. Added "CRITICAL REQUIREMENTS" sections with specific output targets
3. Added title imagery requirement: "If the psalm has a TITLE with figurative language... you MUST analyze that vehicle thoroughly"
4. Expanded structure_type options (added descent, descent_ascent, lament_structure)
5. Added warning: "Do NOT default to 'journey' just because it's the example"
6. Added final checklist for LLM to verify completeness before responding

**Results**:
- Ps 22 now produces: 5 insights, 15 vehicle groups, 75 curated examples
- Structure correctly identified as "descent_ascent"
- Title "hind" imagery fully analyzed with 5 examples
- Cost increased slightly (~$0.45 vs ~$0.30) but output quality significantly improved

**Integration Reminders Added to Guide**:
1. Remove figurative trimming logic from research assembler (curator output is pre-curated)
2. Add curator cost to pipeline cost tracking
3. Update Word doc Methods section to list all results reviewed (e.g., "**hind**: 28; **roaring**: 42...")

**Files Modified**:
- `scripts/test_figurative_curator.py` - Improved Phase 2 prompt with explicit requirements
- `docs/guides/FIGURATIVE_CURATOR_INTEGRATION.md` - Added critical integration reminders, updated testing checklist

#### Session 223 (2025-12-28): Divine Names Modifier - שְׁדּי vs שַׁדַּי Fix
**Objective**: Fix divine names modifier incorrectly replacing שְׁדּי (breasts) with שְׁקֵי

**Problem Identified**:
- Psalm 22:10 contains מַבְטִיחִי עַל־שְׁדּי אִמִּי ("made me secure on my mother's breasts")
- Divine names modifier was replacing שְׁדּי with שְׁקֵי, treating it as the divine name שַׁדַּי
- Existing regex checked for SHIN dot vs SIN dot but not the vowel under the shin

**Root Cause Analysis**:
- Divine name שַׁדַּי has PATACH (ַ U+05B7) or KAMATZ (ָ U+05B8) under shin
- Word שְׁדּי (breasts) has SHEVA (ְ U+05B0) under shin
- The regex needed to check vowels, not just shin/sin distinction

**Solution Implemented**:
1. Added positive lookahead `(?=[\u0591-\u05C7]*[\u05B7\u05B8])` requiring PATACH or KAMATZ
2. Words with SHEVA under the shin are now correctly excluded from modification
3. Added comprehensive test cases including Psalm 22:10 phrase

**Files Modified**:
- `src/utils/divine_names_modifier.py` - Added vowel check to `_modify_el_shaddai()` regex (line 175)
- `archive/development_scripts/root/test_divine_names_shin_sin.py` - Added SHIN+SHEVA test cases

**Test Cases Added**:
- שְׁדּי → שְׁדּי (breasts with SHEVA - NOT modified)
- עַל־שְׁדּי אִמִּי → עַל־שְׁדּי אִמִּי (Psalm 22:10 phrase - NOT modified)
- שַׁדַּי → שַׁקַּי (divine name with PATACH - modified)

#### Session 222 (2025-12-26): Priority-Based Figurative Language Sorting and Trimming
**Objective**: Implement priority-based sorting and trimming for figurative language results

**Problems Identified**:
- Figurative results not sorted by priority within top 20 shown
- Trimming removed arbitrary instances rather than lowest-priority ones
- MicroAnalyst prompt prescribed arbitrary "simple words first" order instead of letting LLM decide

**Solutions Implemented**:
1. Updated `RESEARCH_REQUEST_PROMPT` in `micro_analyst.py` to inform LLM about term order = priority
2. Added `term_priority: Optional[int]` to `FigurativeInstance` dataclass
3. Modified `_priority_search()` in `figurative_librarian.py` to tag instances with term index
4. Added priority grouping with randomization in `_filter_figurative_bundle()` in `research_assembler.py`
5. Simplified `trim_figurative_by_ratio()` in `synthesis_writer.py` to take first N instances (priority-ordered)

**Key Design Decisions**:
- LLM decides priority order based on its analysis (no prescribed phrase vs word order)
- Within same term priority, instances are randomized for variety
- No hard-coded book preferences (removed Psalms prioritization)
- Backward compatible with `hasattr()` checks for existing instances

**Files Modified**:
- `src/agents/micro_analyst.py` - Updated prompt with priority/truncation awareness
- `src/agents/figurative_librarian.py` - Added `term_priority` attribute and tagging
- `src/agents/research_assembler.py` - Added priority sorting with randomization
- `src/agents/synthesis_writer.py` - Simplified trimming to respect priority order

#### Session 221 (2025-12-23): Converse with Editor Script
**Objective**: Create interactive CLI tool for multi-turn conversation with Master Editor about completed psalm commentary

**Problems Identified**:
- Need to discuss editorial decisions, ask follow-up questions, explore alternative interpretations
- Standard pipeline produces commentary but offers no way to interrogate the editor's choices

**Solutions Implemented**:
1. Created `scripts/converse_with_editor.py` implementing full plan from `docs/plans/CONVERSE_WITH_EDITOR_PLAN.md`
2. Interactive context selection showing character counts for each section
3. Core materials always included (psalm text, edited intro/verses, assessment)
4. Optional inclusion of macro/micro analysis and research bundle sections
5. Streaming API responses with GPT-5.1 for real-time feedback
6. Cost tracking with usage summary and $1 threshold warnings
7. Transcript saving to markdown files in psalm output directory

**Key Features**:
- Argument parsing: psalm number (1-150), optional `--edition main|college`
- Research bundle parsing into named sections (Lexicon, Concordance, etc.)
- System prompt positions LLM as "the editor who wrote this commentary"
- Handles both `psalm_N` and `psalm_NNN` directory naming conventions

**Files Created**:
- `scripts/converse_with_editor.py` - Complete interactive conversation script

**Usage**:
```bash
python scripts/converse_with_editor.py 21
python scripts/converse_with_editor.py 21 --edition college
```

#### Session 220 (2025-12-22): Special Instruction Pipeline Implementation
**Objective**: Create supplementary pipeline for author-directed commentary revisions

**Problems Identified**:
- Need for "V2" rewrites based on specific thematic ideas without altering standard pipeline
- Author wants ability to inject overriding instructions into Master Editor generation

**Solutions Implemented**:
1. Created `src/agents/master_editor_si.py` extending `MasterEditorV2` via inheritance
2. Added `MASTER_EDITOR_PROMPT_SI` and `COLLEGE_EDITOR_PROMPT_SI` with "SPECIAL AUTHOR DIRECTIVE" section
3. Created `scripts/run_si_pipeline.py` for dedicated SI workflow
4. All outputs use `_SI` suffix (never overwrites original files)
5. Copies original pipeline stats to new `_SI.json` file
6. Generates three .docx documents: Main SI, College SI, Combined SI

**Key Design Constraints**:
- NO modifications to `scripts/run_enhanced_pipeline.py` or `src/agents/master_editor.py`
- Uses "SI" naming convention throughout
- Strict input validation (exits if analysis files missing)

**Files Created**:
- `src/agents/master_editor_si.py` - Extended Master Editor with SI prompts
- `scripts/run_si_pipeline.py` - Dedicated SI pipeline script
- `data/special_instructions/` - Directory for author instruction files

**Usage**:
```bash
# Create instruction file
echo "Focus on theme of divine refuge..." > data/special_instructions/special_instructions_Psalm_019.txt

# Run SI pipeline
python scripts/run_si_pipeline.py 19
```

**Output Files** (all in `output/psalm_NNN/`):
- `psalm_NNN_edited_intro_SI.md`
- `psalm_NNN_edited_verses_SI.md`
- `psalm_NNN_assessment_SI.md`
- `psalm_NNN_edited_intro_college_SI.md`
- `psalm_NNN_edited_verses_college_SI.md`
- `psalm_NNN_assessment_college_SI.md`
- `psalm_NNN_pipeline_stats_SI.json`
- `psalm_NNN_commentary_SI.docx`
- `psalm_NNN_commentary_college_SI.docx`
- `psalm_NNN_commentary_combined_SI.docx`

#### Session 219 (2025-12-21): Pipeline Skip Logic Fix & Resume Feature
**Objective**: Fix skip flags being ignored and add resume functionality

**Problems Identified**:
- Skip flags used OR condition: `elif not skip_step OR not file_exists()`
- Users surprised when explicit skip commands were ignored

**Solutions Implemented**:
1. Fixed skip logic to simple condition: `elif not skip_step:`
2. Added `--resume` flag for automatic step detection
3. Added dependency checking for skipped steps
4. Updated help documentation

**Files Modified**:
- `scripts/run_enhanced_pipeline.py` - Fixed skip logic, added resume feature

#### Session 218 (2025-12-21): Prioritized Figurative Language Search & Output Simplification
**Objective**: Fix figurative language search dominated by random matches

**Problems Identified**:
- Priority vehicle terms not getting precedence
- Output cluttered with unnecessary statistics

**Solutions Implemented**:
1. Implemented `_priority_search` for sequential term processing
2. Removed "Core pattern" and "Top 3" sections
3. Simplified to list up to 20 instances directly
4. Updated `.gitignore` to exclude `output/` and `logs/`

**Files Modified**:
- `src/agents/figurative_librarian.py` - Priority search logic
- `src/agents/research_assembler.py` - Simplified output
- `.gitignore` - Added output and logs directories

#### Session 217 (2025-12-13): Sections Trimmed Duplication Fix
**Objective**: Fix duplicate entries when sections trimmed multiple times

**Problems Identified**:
- "Related Psalms, Figurative Language (trimmed to 75%), Figurative Language (trimmed to 50%)"
- `_sections_removed` list accumulating without replacement

**Solutions Implemented**:
1. Intelligent section replacement logic
2. Handle Related Psalms format changes
3. Prevent duplicates before adding

**Files Modified**:
- `src/agents/synthesis_writer.py` - Enhanced section tracking (lines 1027-1051)

#### Session 216 (2025-12-13): Figurative Language Counting Fix
**Objective**: Fix figurative language count showing 0 when skipping steps

**Problems Identified**:
- Regex looking for outdated dash-prefixed format
- Actual format: `**Psalms 126:1** (simile) - confidence: 0.90`

**Solutions Implemented**:
1. Updated regex to match actual markdown format
2. Added `re.MULTILINE` flag
3. Count unique verse references appropriately

**Files Modified**:
- `scripts/run_enhanced_pipeline.py` - Fixed figurative language regex (lines 86-89)

#### Session 215 (2025-12-13): Master Editor V2 Prompt Restructure
**Objective**: Restructure prompt for better Deep Research utilization

**Problems Identified**:
- ~440 lines with accumulated cruft
- Hebrew+English rule repeated 15+ times
- Deep Research not explicitly surfaced

**Solutions Implemented**:
1. Created restructured prompt with clear organization
2. Explicit Deep Research guidance section
3. "Aha! Moment" focus framing
4. Made V2 the default
5. Fixed liturgical section formatting

**Results**:
- A/B testing on Psalm 126 showed significantly better output
- Richer integration of research materials
- More provocative section headers

**Files Modified**:
- `src/agents/master_editor.py` - NEW V2 prompt
- `src/agents/master_editor_old.py` - Old prompt preserved
- `scripts/run_enhanced_pipeline.py` - V2 default, `--master-editor-old` flag
- `src/utils/document_generator.py` - Liturgical marker handling
- `src/utils/combined_document_generator.py` - Liturgical extraction fix

#### Session 214 (2025-12-11): Pipeline Stats Tracking Fix
**Objective**: Fix zeros in DOCX methods section when skipping steps

**Problems Identified**:
- Verse count, LXX texts, phonetic transcriptions, lexicon entries showing 0
- Stats JSON not populated when steps skipped

**Solutions Implemented**:
1. Fixed lexicon count regex to match `### עַנְוָה` format
2. Added verse count tracking from database when `--skip-macro`

**Files Modified**:
- `scripts/run_enhanced_pipeline.py` - Fixed lexicon regex, added verse tracking

#### Session 213 (2025-12-11): Main DOCX Verse-by-Verse Commentary Fix
**Objective**: Fix missing verse commentary in main DOCX

**Problems Identified**:
- Main document generator regex only matched `**Verse X**`
- Actual files use `**Verses X-Y**` with en dashes

**Solutions Implemented**:
1. Copied working regex from combined document generator
2. Enhanced pattern for all formats (single, ranges, descriptions)
3. Added range support with start/end tracking

**Results**:
- Psalm 18: 39 verse headings successfully parsed
- Both main and combined DOCX now complete

**Files Modified**:
- `src/utils/document_generator.py` - Updated `_parse_verse_commentary()` method

#### Session 212 (2025-12-11): Psalm 18 Pipeline Fixes + Strategic Verse Grouping
**Objective**: Fix multiple issues with 51-verse psalm processing

**Problems Fixed**:
1. JSON truncation in MicroAnalyst (max_tokens too low)
2. Max tokens exceeding 64K limit (51 × 1800 = 91,800)
3. Missing trimmed research file (sections overwritten)
4. N/A in bibliographical summary
5. DOCX markdown heading format
6. Combined DOCX verse range merging

**Strategic Verse Grouping Feature**:
- Updated prompts with pacing guidance
- College Editor changed from "NEVER combine" to strategic grouping
- Equal treatment for all verses, no rushing

**Files Modified**:
- `src/agents/micro_analyst.py` - Increased max_tokens
- `src/agents/synthesis_writer.py` - 64K cap, sections accumulation
- `src/agents/master_editor.py` - Pacing guidance
- `src/utils/document_generator.py` - Markdown heading handling
- `src/utils/combined_document_generator.py` - Range-aware matching
- `scripts/run_enhanced_pipeline.py` - Stats extraction

#### Session 211 (2025-12-11): Gemini 2.5 Pro Fallback + Improved Trimming Strategy
**Objective**: Prevent critical content loss in large psalms

**Problems Identified**:
- Session 210's aggressive trimming removed Liturgical Usage, Sacks, RAG
- Over-trimming beyond necessary

**Solutions Implemented**:
1. New trimming strategy preserving critical content
2. Increased character limits (350K intro, 300K verse commentary)
3. Gemini 2.5 Pro fallback with 1M token context
4. Enhanced stats tracking

**Key Benefit**: Never trim Lexicon, Commentaries, Liturgical, Sacks, RAG, Concordance, Deep Research

**Files Modified**:
- `src/agents/synthesis_writer.py` - New trimming, Gemini fallback
- `src/utils/pipeline_summary.py` - Added sections_trimmed
- `src/utils/document_generator.py` - Added to bibliographical summary
- `scripts/run_enhanced_pipeline.py` - Track synthesis model

#### Session 210 (2025-12-11): Token Limit Fix (Superseded by Session 211)
*Note: Aggressive trimming approach replaced by Gemini fallback in Session 211*

#### Session 209 (2025-12-11): Deep Web Research Integration + Progressive Trimming Fix
**Objective**: Add support for Gemini Deep Research outputs

**Completed**:
1. Deep Web Research Feature:
   - Created `data/deep_research/` directory
   - File naming: `psalm_NNN_deep_research.txt`
   - Auto-loads into research bundle

2. Progressive Trimming Rewrite:
   - Fixed Psalm 18 token overflow (211,252 tokens)
   - Progressive reduction: 75% → 50% → 25% → remove
   - Trimming order: Related Psalms → Figurative → Concordance → Deep Research

**Files Modified**:
- `src/agents/research_assembler.py` - Added deep research loading
- `src/agents/synthesis_writer.py` - Rewrote trimming logic
- Document generators - Added deep research status
- Pipeline tracking - Added deep research metrics

#### Sessions 204-208 (2025-12-10): Thematic Parallels Feature - DISCONTINUED
**Summary**: Implemented and evaluated RAG-based thematic search. Discontinued after testing showed 80% cost reduction with 1-verse chunks, but feature not useful for synthesis.

**Artifacts Preserved**: `docs/archive/discontinued_features/`

#### Session 182 (2025-12-08): Lexical Insight Prompt Fix
**Problem**: Concordance searches for "פקד לילה" and "צל כנפים" returned 0 results
**Solution**: Modified `DISCOVERY_PASS_PROMPT` with concrete examples for exact form extraction

#### Session 181 (2025-12-08): Comprehensive Codebase Cleanup
- Archived 326 files into organized subdirectories
- Created CLAUDE.md for token efficiency
- Root directory: 145+ → 30 files (79% reduction)

### Sessions 1-199: Concise Summaries

#### Sessions 176-180 (2025-12-07): Phrase Search Fixes Trilogy
- **Session 180**: Fixed word order differences and maqqef (־) concatenation
- **Session 179**: Removed morphological variants from vehicle searches
- **Session 176**: Implemented substring matching for multi-word phrases

#### Sessions 150-175: Pipeline Optimization Phase
- Performance improvements for phrase searches
- Enhanced figurative language filtering
- Database query optimization
- Cost tracking and reporting features

#### Sessions 100-149: Feature Expansion Period
- Added phonetic transcription system
- Implemented Rabbi Sacks commentary integration
- Created combined document generation
- Added liturgical usage tracking

#### Sessions 50-99: Core Pipeline Development
- Built multi-agent framework
- Implemented macro/micro analysis
- Created research assembly system
- Added figurative language librarian

#### Sessions 1-49: Project Foundation
- Initial text extraction from Sefaria
- Database schema design
- Basic analysis pipeline
- Early commentary generation attempts

---

## Reference Materials

### Quick Commands
```bash
# Process single psalm
python main.py --psalm 23

# Process range
python main.py --psalms 1-10

# Resume from last completed step
python scripts/run_enhanced_pipeline.py 23 --resume

# Special Instruction pipeline (V2 rewrite with author notes)
python scripts/run_si_pipeline.py 19

# Converse with Master Editor about completed psalm
python scripts/converse_with_editor.py 21

# Test Figurative Curator (in testing, not yet integrated)
python scripts/test_figurative_curator.py --psalm 22

# Check costs (dry run)
python main.py --psalm 119 --dry-run
```

### Directory Structure
- `src/agents/` - AI agent implementations
- `src/concordance/` - 4-layer Hebrew search system
- `database/` - SQLite databases
- `data/deep_research/` - Gemini Deep Research outputs
- `data/special_instructions/` - Author directive files for SI pipeline
- `output/psalm_*/` - Generated commentary
- `archive/` - Historical files organized by date


### Database Status
- Location: `database/tanakh.db`
- Size: ~50MB
- Books: All 39 books of Tanakh
- Verses: 23,145 verses
- Indexed for fast full-text search

---

## Notes
- **Master Editor V2 is now the default** with explicit Deep Research guidance
- Use `--master-editor-old` flag for original prompt
- Deep Web Research feature ready for production use
- Gemini 2.5 Pro fallback handles large psalms without content loss
- Strategic verse grouping prevents truncation in long psalms
- **Figurative Curator in testing** - produces 4-5 insights, 5-15 examples per vehicle, adaptive structure types
- Pipeline running smoothly with all major fixes implemented

### Documentation Maintenance
- **Session Documentation Prompts**: See `docs/session_tracking/SESSION_DOCUMENTATION_PROMPT.md` for:
  - **Session START Prompt**: Establish context and goals before beginning work
  - **Session END Prompt**: Update documentation structure after completion
- Use these prompts to maintain consistent session workflow and documentation