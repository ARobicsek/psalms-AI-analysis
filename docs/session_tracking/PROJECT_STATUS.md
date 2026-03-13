# Psalms Project Status

**Last Updated**: 2026-03-13 (Session 300)


## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Quick Context](#quick-context)
3. [Current System State](#current-system-state)
4. [Recent Work Summary](#recent-work-summary)
5. [Feature Documentation](#feature-documentation)
6. [Reference Materials](#reference-materials)

---

## Executive Summary

### Current Phase: Pipeline Production
Continuing with tweaks and improvements to the psalm readers guide generation pipeline.

### Progress Summary
- **Current Session**: 300
- **Active Features**: **Unified Writer V4**, **Opus 4.6 Master Writer**, **Sonnet 4.6 Micro Analyst**, **Adaptive Thinking (all Opus agents)**, **Copy Editor Agent (9-Category Taxonomy)**, Insight Extractor, Literary Echoes Integration, Complex Script Font Support (Arabic/CJK/Hebrew docx rendering), **GPT-5.4 Figurative Curator**, **GPT-5.1 Liturgical Librarian**

---

## Quick Context

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with a multi-agent pipeline and Hebrew concordance integration.

**Key Directories**:
- `src/agents/` — AI agent implementations (macro, micro, synthesis, editors, copy editor)
- `src/concordance/` — 4-layer Hebrew search system
- `database/` — SQLite databases (tanakh.db, psalm_relationships.db)
- `data/deep_research/` — Gemini Deep Research outputs
- `data/special_instructions/` — Author directive files for SI pipeline
- `output/psalm_*/` — Generated commentary (production)
- `scripts/` — Pipeline runners and utilities

**Quick Commands**:
```bash
python scripts/run_enhanced_pipeline.py 23          # Process single psalm
python scripts/run_enhanced_pipeline.py 23 --resume  # Resume from last step
python scripts/run_si_pipeline.py 19                 # Special Instruction pipeline
python scripts/run_copy_editor.py 36 37 38           # Standalone copy editor
python scripts/converse_with_editor.py 21            # Chat with Master Editor
```

**Find More Details**:
- `docs/session_tracking/scriptReferences.md` — All scripts with descriptions (read when looking for code)
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` — Full system architecture
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — Detailed session history

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
| Phase 6: Editing and Publication | ✅ Complete | Unified Writer V4, DOCX generation (RTL/Arabic supported) |

### Active Features
- **Unified Writer V4**: Single prompt merging Main + College editions; halves pipeline cost (default)
- **Insight Extractor**: Dedicated agent (gpt-5.4) to curate "aha!" moments from research; now uses streaming
- **Research Trimmer**: Dedicated utility for intelligent context window management
- **Gemini 2.5 Pro Fallback**: Handles large psalms (51+ verses) without content loss
- **Deep Web Research Integration**: Supports Gemini Deep Research outputs
- **Strategic Verse Grouping**: Prevents truncation in long psalms with pacing guidance
- **Pipeline Skip/Exclude Logic**: `--resume` for auto step detection; `--skip-*` to skip regeneration but use existing file; `--exclude-*` to skip regeneration AND omit existing file from writer/doc
- **Figurative Curator**: LLM-enhanced agent that transforms raw figurative concordance data into curated insights using GPT-5.4
- **Questions for the Reader**: LLM-curated questions appear before Introduction to prime reader engagement

### Known Limitations
- Large psalms may require Gemini fallback (additional cost)
- Deep research must be manually prepared via Gemini browser interface
- Figurative Curator adds ~$0.30-0.50 per psalm to processing cost
- Questions for Reader adds ~$0.01-0.02 per psalm (gpt-5.4)
- Insight Extractor adds ~$0.50-1.00 per psalm (gpt-5.4)

---

## Recent Work Summary (Last 5 Sessions)

### Session 300 (2026-03-13): Model Swap — Figurative Curator & Liturgical Librarian
- Replaced Figurative Curator model from `gemini-3.1-pro-preview` to `gpt-5.4` (high reasoning effort) for better figurative analysis quality.
- Replaced Liturgical Librarian model from `gemini-2.5-pro` to `gpt-5.1` (high reasoning effort) for cost reduction on summarization tasks.
- Kept `gemini-2.5-pro` only for Synthesis Writer large-psalm fallback (1M context window dependency).
- Updated legacy pipeline scripts, documentation, and verified DOCX model attribution tracks new models programmatically.

### Session 299 (2026-03-09): Fixing Psalm 40 Pipeline Issues
- Hardened pipeline section extraction to detect and recover liturgical content displaced by the copy editor LLM, fixing malformed DOCX outputs.
- Added structural validation for displaced content to `CopyEditor`.
- Strengthened `MASTER_WRITER_PROMPT_V4` to enforce the inclusion of all specific liturgical references found in the research bundle.

### Session 298 (2026-03-09): Error and Retry Tracking in Cost Summary
- Enhanced `CostTracker` to maintain a log of pipeline events (`log_event()`).
- Updated `get_summary()` to display a dedicated "PIPELINE EVENTS & RETRIES" section reporting which agents hit token truncations, JSON repair failures, or API timeouts.
- Injected logging hooks into the retry loops of the Micro Analyst, Macro Analyst, Insight Extractor, and Question Curator.
- Fixed `UnboundLocalError` in `_generate_research_requests()` (missing `response_text` initialization).

### Session 297 (2026-03-09): Micro Analyst JSON Repair & Validation
- Integrated the `json-repair` library into the Micro Analyst to salvage outputs that are truncated due to streaming connection drops or internal cutoff.
- Added structural validation: repaired JSON is only accepted if it contains the correct number of `verse_discoveries` (matching the database verse count) and at least 3 `interesting_questions`.
- Invalid structural repairs fall back to the existing token retry logic, preventing faulty JSON from breaking downstream pipeline agents.

### Session 296 (2026-03-09): Micro Analyst Truncation Investigation & JSON Repair Recommendation
- Investigated whether raising token limits would prevent costly micro analyst retries — **ruled out**: `max_tokens` truncation has never fired.
- Identified actual root causes: streaming connection drops (`RemoteProtocolError`) and unterminated JSON strings from mid-stream cutoffs.
- Recommended implementing JSON repair with structural validation (verse count + required sections check) for next session.



For earlier sessions, see [IMPLEMENTATION_LOG.md](IMPLEMENTATION_LOG.md).

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
LLM-enhanced agent that transforms raw figurative concordance data into curated insights using GPT-5.4:
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

**Archived Sessions**:
- Sessions 1-149: `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_1-149_2025-12-04.md`
- Sessions 150-199: `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_150-199_2026-01-12.md`
- Sessions 200+: `docs/session_tracking/IMPLEMENTATION_LOG.md`

---

## Reference Materials

See **Quick Context** section above for key directories and commands.

### Database Status
- **tanakh.db**: ~50MB, all 39 books of Tanakh, 23,145 verses, full-text indexed
- **psalm_relationships.db**: V6 skipgram patterns (130MB, 335,720 quality-filtered patterns)

### Documentation
- `docs/session_tracking/SESSION_PROMPTS.md` — Session start/end templates
- `docs/guides/DEVELOPER_GUIDE.md` — Coding standards, workflow
- `docs/guides/OPERATIONAL_GUIDE.md` — Day-to-day operations