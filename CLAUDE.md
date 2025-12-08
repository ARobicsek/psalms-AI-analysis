# Psalms AI Commentary Pipeline - Quick Reference

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude AI (Sonnet 4.5, Haiku 4.5) with multi-agent framework and Hebrew concordance integration.

## Essential Documentation

**Start Here:**
- `README.md` - Project overview, installation, usage
- `docs/session_tracking/PROJECT_STATUS.md` - Current phase, tasks, metrics (Session 179)
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` - Technical specifications, schemas
- `docs/guides/DEVELOPER_GUIDE.md` - Development workflow, coding standards

## Recent Major Changes (Last 5 Sessions)

**Session 179 (2025-12-07)**: Figurative Vehicle Search Fix
- Removed morphological variants from vehicle searches (tent → ~~living~~)
- Added exact match prioritization in research assembler
- Vehicle concepts now treated as hierarchical tags, not inflected words

**Session 176 (2025-12-07)**: Phrase Substring Matching Fix
- Implemented substring matching for multi-word phrases
- Preserved exact matching for single words
- Fixed source verse always appearing in phrase search results

**Session 175 (2025-12-07)**: Performance Fix
- Eliminated exponential query growth for phrase searches
- No variations for phrases, only exact forms
- Reduced "גור באהל" from 824 → 5 queries

**Session 174 (2025-12-06)**: Maqqef Handling Enhancement
- Improved word boundary detection with maqqef (־)
- Fixed compound word matching in concordance searches

**Session 173 (2025-12-06)**: Enhanced Phrase Extraction
- Added exact form preservation in micro analyst
- Fallback extraction from verse text when LLM fails

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
- `output/psalm_*/` - Generated commentary (production)
- `archive/` - Organized historical files (debugging, experiments, session docs)
- `scripts/utilities/` - Helper scripts (canonicalizer, score generation)

## Find Specific Information

**Architecture & Design:**
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` - Complete technical specs
- `docs/architecture/CONTEXT.md` - Quick reference guide
- `docs/architecture/analytical_framework_for_RAG.md` - RAG system design

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

**Phase**: Phase 4 - Production Commentary Generation
**Completed**: Psalms 1-14, 20, 8, 97, 145 (all phases)
**Next Up**: Psalms 16-21
**Last Updated**: Session 181 (2025-12-08)

## Common Tasks

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
