# Psalms AI Commentary Pipeline - Quick Reference

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude AI (Sonnet 4.5, Haiku 4.5) with multi-agent framework and Hebrew concordance integration.

## Essential Documentation

**Start Here:**
- `README.md` - Project overview, installation, usage
- `docs/session_tracking/PROJECT_STATUS.md` - Current phase, tasks, metrics (Session 181)
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` - Technical specifications, schemas
- `docs/guides/DEVELOPER_GUIDE.md` - Development workflow, coding standards

## Recent Major Changes (Last 5 Sessions)

**Session 209 (2025-12-11)**: Deep Web Research Integration
- Added support for incorporating Gemini Deep Research outputs into research bundles
- New directory: `data/deep_research/` for storing psalm-specific deep research files
- Files named: `psalm_NNN_deep_research.txt` (e.g., `psalm_017_deep_research.txt`)
- Auto-trimming: Deep research removed first if bundle exceeds character limits
- Pipeline stats and docx summary now track "Deep Web Research: Yes/No"

**Session 182 (2025-12-08)**: Lexical Insight Prompt Fix
- Fixed concordance searches returning 0 results for phrases like "פקד לילה" and "צל כנפים"
- Root cause: LLM extracting conceptual/base forms instead of exact verse forms
- Improved `DISCOVERY_PASS_PROMPT` with concrete wrong/right examples
- Added phrase-level morphological variation guidance (person, number, tense, prefix)

**Session 181 (2025-12-08)**: Comprehensive Codebase Cleanup
- Archived 326 files into organized subdirectories (debugging, experiments, session docs)
- Created CLAUDE.md for token-efficient session startup (80% token reduction)
- Reorganized docs/ into logical subdirectories (architecture, guides, features, session_tracking)
- Root directory reduced from 145+ files → 30 files (79% reduction)

**Session 180 (2025-12-07)**: Phrase Search Fixes (Word Order + Maqqef)
- Fixed word order differences: phrases now found regardless of word sequence
- Fixed maqqef (־) concatenation bug: now properly replaced with space
- New `_extract_all_phrase_forms_from_verse()` extracts all phrase variations
- Guarantees every phrase search finds its source verse

**Session 179 (2025-12-07)**: Figurative Vehicle Search Fix
- Removed morphological variants from vehicle searches (tent → ~~living~~)
- Added exact match prioritization in research assembler
- Vehicle concepts now treated as hierarchical tags, not inflected words

**Session 176 (2025-12-07)**: Phrase Substring Matching Fix
- Implemented substring matching for multi-word phrases
- Preserved exact matching for single words
- Fixed source verse always appearing in phrase search results

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
