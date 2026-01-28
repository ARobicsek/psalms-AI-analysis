# Psalms Project Status

**Last Updated**: 2026-01-28 (Session 249)

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
- **Current Session**: 249
- **Active Features**: Master Editor V2, Gemini 2.5 Pro Fallback, Deep Web Research Integration, Special Instruction Pipeline, Converse with Editor, Priority-Based Figurative Trimming, Figurative Curator, Refined Reader Questions, Hook-First Introductions, RTL Hebrew Text Formatting, Model Tracking, SI Pipeline Engagement Sync, Insight Quality Rules (✅ Phase 1-2c Complete), Insight Extractor (✅ Integrated), College Editor Insights (✅ Integrated), Master Writer Pipeline (✅ Default Standard)

---

## Current System State

### Pipeline Phases

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Text Extraction | ✅ Complete | All Tanakh text extracted and stored in SQLite |
| Phase 2: Macro Analysis | ✅ Complete | All psalms analyzed for themes and structure |
| Phase 3: Micro Analysis | ✅ Complete | Verse-by-verse phrase extraction complete |
| Phase 3b: Question Curation | ✅ Complete | LLM-curated reader questions from analysis |
| Phase 3c: Insight Extraction | ✅ Complete | Curates high-value insights from research bundle (Step 2c) |
| Phase 4: Research Assembly | ✅ Complete | Optimizing figurative language search and trimming |
| Phase 5: Synthesis Generation | ✅ Complete | Commentary generation with Gemini fallback |
| Phase 6: Editing and Publication | ✅ Complete | Master Editor V2, DOCX generation |

### Active Features
- **Master Editor V2**: Restructured prompt with explicit Deep Research guidance (default)
- **Insight Extractor**: Dedicated agent (Claude Opus 4.5) to curate "aha!" moments from research
- **Research Trimmer**: Dedicated utility for intelligent context window management
- **Gemini 2.5 Pro Fallback**: Handles large psalms (51+ verses) without content loss
- **Deep Web Research Integration**: Supports Gemini Deep Research outputs
- **Strategic Verse Grouping**: Prevents truncation in long psalms with pacing guidance
- **Pipeline Skip Logic**: New `--resume` flag for automatic step detection
- **Figurative Curator**: LLM-enhanced agent that transforms raw figurative concordance data into curated insights using Gemini 3 Pro
- **Questions for the Reader**: LLM-curated questions appear before Introduction to prime reader engagement

### Known Limitations
- Large psalms may require Gemini fallback (additional cost)
- Deep research must be manually prepared via Gemini browser interface
- Figurative Curator adds ~$0.30-0.50 per psalm to processing cost
- Questions for Reader adds ~$0.01-0.02 per psalm (Gemini Flash)
- Insight Extractor adds ~$0.50-1.00 per psalm (Claude Opus 4.5)

---

## Recent Work Summary

### Session 249 (2026-01-28): Model Updates & Methodology Reporting
- **Question Curator**: Switched from Gemini Flash to Claude Opus 4.5 for higher quality reader questions.
- **Methodology**: Updated DOCX generation to explicitly report "Question Generation" models and fixed "Date Produced" bug.
- **Pipeline**: Refactored pipeline tracking to ensure completion date is recorded before document generation.

### Session 248 (2026-01-28): Master Writer Refactoring & SI Pipeline Parity
- **Refactoring Main**: Promoted `run_enhanced_pipeline_TEST.py` (Master Writer) to default `run_enhanced_pipeline.py`. Preserved legacy flow in `run_enhanced_pipeline_with_synthesis.py`.
- **Refactoring SI**: Updated `run_si_pipeline.py` to use Master Writer architecture. Created `run_si_pipeline_with_synthesis.py` for legacy SI flow.
- **Agent Update**: Updated `MasterEditorSI` to support both Editor (Legacy) and Writer (New) modes with special instructions.
- **Outcome**: Full architectural parity achieved between main and SI pipelines, with "Master Writer" (single-pass) now the default standard.

### Session 247 (2026-01-27): Pipeline Input Completeness & Reader Questions
- **Bug Fix**: Closed input gaps — old pipeline now receives `{curated_insights}`, new pipeline now receives `{psalm_text}`, college edition now saves refined reader questions.
- **Feature**: All four prompts (main/college × editor/writer) now receive `{reader_questions}`, have hook-to-questions instructions, and validate that questions are elegantly addressed in the output.
- **Plumbing**: Updated both pipeline scripts to pass `reader_questions_file` and `insights_file` to college methods.

### Session 246 (2026-01-27): Fix Methodology Section Accounting & Insight Model Tracking
- **Bug Fix**: Fixed stale "Master Editor Prompt Size" in Methodology section — print-ready formatter was reading pre-update JSON (298,295 vs correct 291,290).
- **Bug Fix**: Old pipeline now reports actual prompt size (`len(prompt)`) instead of raw input concatenation.
- **Feature**: Insight Extractor model now tracked and displayed in Methodology section across both pipelines and all output formats.

### Session 245 (2026-01-27): Master Writer Experiment (No Synthesis Writer)
- **Objective**: Eliminated "Synthesis Writer" step in favor of a single-pass "Master Writer" to reduce information loss.
- **Implementation**: Created `scripts/run_enhanced_pipeline_TEST.py` and implemented `MasterEditor.write_commentary()` with new definitive prompts.
- **Fixes**: Resolved `gpt-4o` API compatibility issues; fixed "Master Editor Prompt Size" discrepancy (stale stats).
- **Outcome**: Test pipeline fully functional. Master Writer now generates Introduction, Verse Commentary, and College Edition directly from research.
- **Code Review**: Reviewed junior dev's `run_enhanced_pipeline_TEST.py` — a single-pass pipeline that replaces two-pass (SynthesisWriter → MasterEditor) with a direct "Master Writer" approach.
- **Prompt Enrichment**: Enriched `MASTER_WRITER_PROMPT` and `COLLEGE_WRITER_PROMPT` with critical guidance from synthesis writer (11 Items of Interest, WEAK/STRONG examples, Translation Test, blurry words, Torah Temimah references).
- **Infrastructure Fixes**: Fixed 16 code issues (output path, argparse flags, hardcoded model, dead imports, combined doc gen, rate limit handling, progress output, UTF-8 encoding).
- **Design**: All changes to `master_editor.py` are additive-only — both old and new pipelines coexist seamlessly.

### Session 244 (2026-01-26): Fixing College Edition Crash & Insight Attribution
- **College Edition Fix**: Resolved `NameError` crash by ensuring `curated_insights` is properly formatted string before prompt injection.
- **Model Attribution**: Integrated "Insights Extraction" model tracking into pipeline stats.
- **Documentation**: Updated both `DocumentGenerator` and `CombinedDocumentGenerator` to display the Insight model in the Methodology summary.

### Session 243 (2026-01-26): Insight Quality Improvements — College Editor & Pipeline Flags (Phase 4)
- **Enhanced College Prompt**: Updated `COLLEGE_EDITOR_PROMPT_V2` in `master_editor.py` to prioritize `{curated_insights}` "aha!" moments.
- **Pipeline Controls**: Added `--skip-insights` flag to `run_enhanced_pipeline.py` for better execution control.
- **Integration**: Plumbed insights file through `MasterEditor` execution path for college edition.
- **Outcome**: College edition integration partially complete; pending final variable formatting fix in `_perform_college_review`.

### Session 242 (2026-01-26): Insight Quality Improvements — Pipeline Integration (Phase 2b-2c)
- **Executed Phase 2b**: Integrated `InsightExtractor` into `run_enhanced_pipeline.py` (Step 2c).
- **Executed Phase 2c**: Updated `SynthesisWriter` to consume `curated_insights` and inject them into the prompt.
- **Refactoring**: Created `src/utils/research_trimmer.py` to centralize and improve trimming logic; removed duplicate code from synthesis writer.
- **Outcome**: Full pipeline is now running with the new Insight Extractor (verified on Psalm 30).

### Session 241 (2026-01-26): Insight Quality Improvements — Execution (Phase 1 & 2a)
- **Executed Phase 1**: Implemented 5 "Insight Quality Rules" (A-E) in `synthesis_writer.py` and enhanced `master_editor.py` with Flow Rule, Blurry Photo Check, and Reader Transformation criterion.
- **Executed Phase 2a**: Created `src/agents/insight_extractor.py` (Claude Opus 4.5) to curate research bundles for high-value insights.
- **Outcome**: Prompts are now rigorous against "fluff"; new agent is ready for pipeline integration (Phase 2b).

### Session 240 (2026-01-26): Insight Quality Improvements — Planning & Documentation
- **Objective**: Transform commentary from data aggregation to interpretive synthesis
- **Reviewed**: `docs/archive/implementation_notes/insights_improvement.md` — diagnosis of "fluff problem" with concrete before/after examples
- **Planned**: Two-phase approach: (1) Add 5 Insight Quality Rules (A-E) to all 6 prompts across synthesis_writer.py, master_editor.py, and master_editor_si.py; (2) Create new Insight Extractor agent (Claude Opus 4.5) for pre-synthesis filtering
- **Documented**: Detailed execution plan with exact insertion points, text blocks, and verification checklist at `docs/archive/implementation_notes/insights_improvement_execution_plan.md`
- **Status**: Plan approved, implementation deferred to Session 241 (context limit reached)

### Session 239 (2026-01-25): Fix RTL Italic Processing & Punctuation Loss in Docx
- **Bug Fix (Italic RTL)**: Added RTL processing to all 8 italic code paths across both document generators — previously italic text had zero RTL handling while bold and plain text did.
- **Bug Fix (Regex)**: Fixed broken tokenizer regex in `_reverse_primarily_hebrew_line()` — double-backslash escapes (`\\[\\]`) closed the character class prematurely, silently dropping all punctuation (`;`, `.`).
- **New Methods**: `_is_hebrew_dominant()` (broader Hebrew detection) and `_process_text_rtl()` (consolidated RTL helper).
- **Verification**: Psalm 30 docx regenerated; both issues resolved (word order + punctuation).

### Session 238 (2026-01-23): Divine Names Modifier Markdown Fix
- **Bug Fix**: Fixed `DivineNamesModifier` to correctly detect and modify divine names (e.g., אֵל → קֵל) when wrapped in markdown formatting (italics/bold).
- **Verification**: Confirmed fix handles `*אֵל הַכָּבוֹד*` correctly.
- **Impact**: Ensures consistent divine name modification in generated commentary regardless of formatting.

### Session 237 (2026-01-12): Codebase Cleanup and Archiving
- **Archived**: Moved 40+ obsolete scripts and documentation files to `archive/` structure
- **Data Cleanup**: Archived ~450MB of unused Hirsch/Thematic data (large files excluded from git)
- **Refactoring**: Decoupled and removed `HirschLibrarian` from `ResearchAssembler`; archived `hirsch_librarian.py`
- **Verification**: Confirmed all production pipelines remain functional

### Session 236 (2026-01-12): Session Management System Cleanup
- Archived obsolete `NEXT_SESSION_PROMPT.md` and `SESSION_DOCUMENTATION_PROMPT.md` to archive folder
- Created new streamlined `SESSION_PROMPTS.md` with copy-paste start/end templates
- Consolidated session history: moved sessions 200-235 from PROJECT_STATUS to `IMPLEMENTATION_LOG.md`

### Session 235 (2026-01-12): SI Pipeline Engagement Improvements Sync
- Synchronized `MasterEditorSI` prompts with Session 234 improvements (hook-first, Stage 4 refined questions)
- Added question extraction logic to `run_si_pipeline.py` for both main and college editions
- Fixed regex to handle both `##` and `###` question headings; all 3 SI docx formats now show questions before essays

### Session 234 (2026-01-11): Engagement Improvements - Hook-First Intros & Refined Questions
- Integrated hook-first opening instructions and unique findings surfacing into `synthesis_writer.py`
- Added Stage 4 refined question generation to `master_editor.py` for both main and college editions
- Pipeline now extracts and saves refined questions; all 3 docx formats display questions before essays

### Session 233 (2026-01-11): RTL Display Fixes - Verse References and Hebrew Punctuation
- Fixed verse reference reversal (e.g., `(26:6–7)` displayed as `(7–26:6)`) with LRO/PDF wrapping
- Fixed Hebrew trailing punctuation floating to far left with RLM anchoring
- Applied fixes to all code paths in both document generators

### Session 232 (2026-01-10): Model Name Tracking - Single Source of Truth Pattern
- **Objective**: Investigate pipeline model usage discrepancy between Psalm 26 and 27; implement robust model tracking.
- **Investigation Findings**:
  - Pipeline stats JSON showed different model names: Psalm 26 had `claude-3-5-sonnet-20241022` while Psalm 27 had `claude-sonnet-4-5` for macro/micro analysis.
  - Log files confirmed BOTH runs actually used `claude-sonnet-4-5` - the discrepancy was a metadata recording artifact, not an actual processing difference.
  - Root cause: Hardcoded fallback model names in `run_enhanced_pipeline.py` used outdated model identifiers when skip flags were active.
- **Solutions Implemented**:
  1. **Added class-level constants**: `DEFAULT_MODEL` constants added to `MacroAnalyst` and `MicroAnalystV2` classes.
  2. **Updated agent `__init__` methods**: Now use `self.DEFAULT_MODEL` instead of hardcoded strings.
  3. **Updated pipeline skip logic**: References `MacroAnalyst.DEFAULT_MODEL` and `MicroAnalystV2.DEFAULT_MODEL` instead of hardcoded strings.
  4. **Corrected Psalm 26 stats**: Updated `psalm_026_pipeline_stats.json` to show correct model names.
- **Benefits**:
  - Single source of truth for model names (change once in agent class, updates everywhere).
  - No hardcoded fallbacks that can become stale.
  - Future model upgrades require only one change per agent.
- **Files Modified**:
  - `src/agents/macro_analyst.py` - Added `DEFAULT_MODEL` class constant
  - `src/agents/micro_analyst.py` - Added `DEFAULT_MODEL` class constant
  - `scripts/run_enhanced_pipeline.py` - Uses class constants for skip-step tracking
  - `output/psalm_26/psalm_026_pipeline_stats.json` - Corrected model names

### Session 231 (2026-01-08): Fixed RTL Text Rendering for Psalm 100:3
- **Objective**: Correctly render standalone Hebrew verse lines and Ketiv/Qere variants in produced .docx files (specifically Psalm 100:3).
- **Problems Fixed**:
  - Hebrew text inside square brackets `[]` (Ketiv/Qere) was not being reversed for RTL display.
  - Standalone Hebrew verse lines (like Ps 100:3) were displaying jumbled word order because the LTR paragraph setting forced LTR on the entire line.
  - Parentheses/brackets were pointing in the wrong direction after RTL reversal.
- **Solutions Implemented**:
  1. **Extended Regex Support**: Updated `hebrew_paren_pattern` to also handle `[]` brackets.
  2. **Primarily-Hebrew Line Detection**: Added `_is_primarily_hebrew()` to detect standalone verse lines (requires sof-pasuq `׃` AND <5% ASCII characters).
  3. **Full-Line Reversal**: Added `_reverse_primarily_hebrew_line()` to reverse entire verse lines while preserving word-internal grapheme order.
  4. **Bracket Mirroring**: Added logic to swap `(` ↔ `)` and `[` ↔ `]` during reversal to correct directional display.
  5. **Applied to All Generators**: Fixes implemented in both `DocumentGenerator` and `CombinedDocumentGenerator`.
- **Files Modified**:
  - `src/utils/document_generator.py`
  - `src/utils/combined_document_generator.py`

### Session 230 (2026-01-05): Questions for the Reader Feature
- **NEW Feature**: LLM-curated "Questions for the Reader" section before Introduction
  - `src/agents/question_curator.py` - Extracts questions from macro/micro analysis, uses Gemini Flash to curate 4-6 engaging questions
  - Questions placed immediately after psalm text, before Introduction in .docx output
  - MasterEditor prompt updated to verify all questions are addressed in commentary
- **Pipeline Integration**:
  - Added STEP 2b: Question Curation (after micro analysis, before synthesis)
  - DocumentGenerator and CombinedDocumentGenerator updated to render questions
  - Output: `psalm_XXX_reader_questions.json` per psalm
- **Design Decisions**:
  - Questions sourced from `research_questions` (macro) and `interesting_questions` (micro)
  - Gemini Flash for cost-effective curation (~$0.01-0.02 per psalm)
  - Style: "Engaging scholarly" - specific to the psalm, spans structure/language/theology
  - Retroactive generation for completed psalms: NOT implemented (per user request)
- **Files Created/Modified**:
  - `src/agents/question_curator.py` (NEW)
  - `src/agents/master_editor.py` (prompt + code changes)
  - `scripts/run_enhanced_pipeline.py` (STEP 2b + parameter passing)
  - `src/utils/document_generator.py` (render questions section)
  - `src/utils/combined_document_generator.py` (render questions section)

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

For **full session details**, see [IMPLEMENTATION_LOG.md](IMPLEMENTATION_LOG.md).

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