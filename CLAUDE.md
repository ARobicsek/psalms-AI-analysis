# Psalms AI Commentary Pipeline - Quick Reference

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude AI (Sonnet 4.5, Haiku 4.5) with multi-agent framework and Hebrew concordance integration.

## Essential Documentation

**Start Here:**
- `README.md` - Project overview, installation, usage
- `docs/session_tracking/PROJECT_STATUS.md` - Current phase, tasks, metrics (Session 289)
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` - Technical specifications, schemas
- `docs/guides/DEVELOPER_GUIDE.md` - Development workflow, coding standards

## Recent Major Changes (Last 5 Sessions)

**Session 289 (2026-03-08)**: Session Management Cleanup
- Restructured session docs to cut startup context from ~150KB to ~20KB (~85% token savings)
- Added Quick Context section to PROJECT_STATUS (replaces need to read CLAUDE.md separately)
- Rewrote SESSION_PROMPTS.md with tiered loading: only PROJECT_STATUS required at startup

**Session 288 (2026-03-07)**: Copy Editor Expansion — 9-Category Taxonomy
- Expanded copy editor from 6 to 9 error categories
- Added Rule 3b (Don't Over-Label Hebrew Grammar) to Master Writer prompt

**Session 287 (2026-03-05)**: Fix SI Pipeline Auto-Detection & Research Trimming
- Implemented auto-detection of special instruction files
- Added `research_trimmed.md` artifact generation

**Session 286 (2026-03-04)**: Fix Divine Names Modifier for Eli
- Added specific regex pattern for `אֵלִי` ("My God") in Psalm 22:2

**Session 285 (2026-03-04)**: Micro Agent Optimization
- Slimmed discovery schema, reduced thinking budget 70%→50%, ~75% micro cost reduction
- Fixed 5 bugs across master_editor, pipeline scripts, and insight extractor

## Quick Commands

```bash
# Process single psalm
python main.py --psalm 23

# Process range
python main.py --psalms 1-10

# Check costs (dry run)
python main.py --psalm 119 --dry-run

# View cost report
python scripts/cost_report.py
```

## Key Directories

- `src/agents/` - AI agent implementations (macro, micro, synthesis, editors)
- `src/concordance/` - 4-layer Hebrew search system
- `database/` - SQLite databases (tanakh.db, psalm_relationships.db)
- `data/deep_research/` - Gemini Deep Research outputs (psalm_NNN_deep_research.txt)
- `output/psalm_*/` - Generated commentary (production)
- `archive/` - Organized historical files (debugging, experiments, session docs)
- `scripts/utilities/` - Helper scripts (canonicalizer, score generation)

## Find Specific Information

**Architecture & Design:**
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` - Complete technical specs
- `docs/architecture/CONTEXT.md` - Quick reference guide
- `docs/architecture/analytical_framework_for_RAG.md` - RAG system design
- `docs/architecture/TOKEN_REDUCTION_PHASE_B.md` - **NEXT UP**: Ready-to-implement token reduction tasks (Wins 2, 4, 6, 9)

**Features:**
- `docs/features/PHRASE_EXTRACTION_FIX.md` - Exact phrase preservation
- `docs/features/PHONETIC_SYSTEM.md` - Phonetic transcription system
- `docs/features/FIGURATIVE_LIBRARIAN_FILTERING_DETAILED.md` - Search filtering

**Development:**
- `docs/guides/DEVELOPER_GUIDE.md` - Coding standards, workflow
- `docs/guides/OPERATIONAL_GUIDE.md` - Day-to-day operations
- `docs/guides/PHONETIC_DEVELOPER_GUIDE.md` - Phonetic system usage

**Session History:**
- `docs/session_tracking/IMPLEMENTATION_LOG.md` - Development journal
- `docs/session_tracking/NEXT_SESSION_PROMPT.md` - Next steps planning
- `archive/session_documentation/` - Historical session summaries

## Current Status

**Phase**: Pipeline Production — tweaks and improvements
**Active**: Unified Writer V4, Copy Editor (9-category), Opus 4.6 Master Writer, Sonnet 4.6 Micro
**Last Updated**: Session 289 (2026-03-08)

## Common Tasks

**Add Deep Research:** Save Gemini Deep Research output to `data/deep_research/psalm_NNN_deep_research.txt`
**Research a fix:** Check `archive/debugging/` for similar past issues organized by date
**Review experiments:** Check `archive/experimental_outputs/` for test psalm runs
**Update docs:** Maintain this section's "Recent Major Changes" after significant work
**Add utility:** Place in `scripts/utilities/` and document in DEVELOPER_GUIDE

## File Organization Rules

- **Production code:** `src/`, `main.py`, `scripts/utilities/`
- **Experimental/test:** Use during session, archive immediately after
- **Archive after 1 session:** Test scripts, debug outputs, temp files
- **Never commit:** `*.log`, `*_output.txt`, temp analysis files (in .gitignore)

---
*For full project overview, see README.md. For current work, see docs/session_tracking/PROJECT_STATUS.md.*
