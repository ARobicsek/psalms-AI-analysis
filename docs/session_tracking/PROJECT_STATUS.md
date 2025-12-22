# Psalms Project Status

**Last Updated**: 2025-12-21 (Session 219)

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Current System State](#current-system-state)
3. [Recent Work Summary](#recent-work-summary)
4. [Feature Documentation](#feature-documentation)
5. [Session History](#session-history)
6. [Reference Materials](#reference-materials)

---

## Executive Summary

### Current Phase: Pipeline Production - Complete Psalms 1-14, 8, 15-21
Continuing with verse-by-verse commentary generation using the established pipeline.

### Progress Summary
- **Completed Psalms**: 1-14, 15, 20, 8, 97, 145 (18 total)
- **Next Psalms**: 16-21
- **Current Session**: 219
- **Active Features**: Master Editor V2, Gemini 2.5 Pro Fallback, Deep Web Research Integration

---

## Current System State

### Pipeline Phases

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Text Extraction | ✅ Complete | All Tanakh text extracted and stored in SQLite |
| Phase 2: Macro Analysis | ✅ Complete | All psalms analyzed for themes and structure |
| Phase 3: Micro Analysis | ✅ Complete | Verse-by-verse phrase extraction complete |
| Phase 4: Research Assembly | 🟠 In Progress | Optimizing figurative language search and trimming |
| Phase 5: Synthesis Generation | ✅ Complete | Commentary generation with Gemini fallback |
| Phase 6: Editing and Publication | ✅ Complete | Master Editor V2, DOCX generation |

### Active Features
- **Master Editor V2**: Restructured prompt with explicit Deep Research guidance (default)
- **Gemini 2.5 Pro Fallback**: Handles large psalms (51+ verses) without content loss
- **Deep Web Research Integration**: Supports Gemini Deep Research outputs
- **Strategic Verse Grouping**: Prevents truncation in long psalms with pacing guidance
- **Pipeline Skip Logic**: New `--resume` flag for automatic step detection

### Known Limitations
- Figurative language search prioritization needs refinement
- Large psalms may require Gemini fallback (additional cost)
- Deep research must be manually prepared via Gemini browser interface

---

## Recent Work Summary

### Session 219 (2025-12-21): Pipeline Skip Logic Fix & Resume Feature
- Fixed skip flags being ignored when output files didn't exist
- Added `--resume` flag for automatic step detection
- Improved dependency checking for skipped steps

### Session 218 (2025-12-21): Prioritized Figurative Language Search
- Implemented priority-based search for vehicle terms
- Simplified research bundle output format
- Fixed git ignore for output and logs directories

### Session 217 (2025-12-13): Sections Trimmed Duplication Fix
- Fixed duplicate entries when sections upgraded (75% → 50%)
- Implemented intelligent section replacement logic
- Cleaner DOCX output showing final trimming state

### Session 216 (2025-12-13): Figurative Language Counting Fix
- Fixed regex pattern for parsing figurative language instances
- Stats now correctly populated when using skip flags
- Tested on Psalms 126, 18, and 8

### Session 215 (2025-12-13): Master Editor V2 Prompt Restructure
- Complete restructure of Master Editor prompt (now default)
- Explicit Deep Research guidance integration
- Reduced redundancy by ~40%
- Better "aha! moment" focus

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

### Pipeline Features

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

### Sessions 200-219: Full Details

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

# Check costs (dry run)
python main.py --psalm 119 --dry-run
```

### Directory Structure
- `src/agents/` - AI agent implementations
- `src/concordance/` - 4-layer Hebrew search system
- `database/` - SQLite databases
- `data/deep_research/` - Gemini Deep Research outputs
- `output/psalm_*/` - Generated commentary
- `archive/` - Historical files organized by date

### Pipeline Status by Psalm
**Completed (All Phases)**: 1-14, 15, 20, 8, 97, 145
**In Progress**: 16-21
**Remaining**: 22-150

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
- Pipeline running smoothly with all major fixes implemented

### Documentation Maintenance
- **Session Documentation Prompts**: See `docs/session_tracking/SESSION_DOCUMENTATION_PROMPT.md` for:
  - **Session START Prompt**: Establish context and goals before beginning work
  - **Session END Prompt**: Update documentation structure after completion
- Use these prompts to maintain consistent session workflow and documentation