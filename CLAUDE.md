# Psalms AI Commentary Pipeline - Quick Reference

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent framework and Hebrew concordance integration.

## Essential Documentation

**Start Here:**
- `README.md` - Project overview, installation, usage
- `docs/session_tracking/PROJECT_STATUS.md` - Current phase, tasks, metrics (Session 305)
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` - Technical specifications, schemas
- `docs/guides/DEVELOPER_GUIDE.md` - Development workflow, coding standards

## Recent Major Changes (Last 5 Sessions)

**Session 306 (2026-03-15)**: Fix Displaced Liturgical Content Recovery in DOCX
- Fixed DOCX bug where liturgy section was interrupted by spurious "Verse-by-Verse Commentary" / "Verse 9" headers (Psalm 42)
- Replaced flawed `< 100` char threshold and position-0 regex heuristics with standalone verse header detection
- Applied to both `run_enhanced_pipeline.py` and `run_si_pipeline.py`

**Session 305 (2026-03-15)**: Remove Auto-Skip-If-Exists Behavior
- Removed implicit "skip if output exists" checks in Steps 2b, 2c, 5b — steps now always run and overwrite unless explicitly skipped
- Fixed Step 5c gating so DOCX-only runs work with `--skip-copy-editor` (extracts from existing copy-edited file)
- Applied to both `run_enhanced_pipeline.py` and `run_si_pipeline.py`

**Session 304 (2026-03-15)**: Copy Editor Output Readability
- Replaced unified diff with word-level diff showing ~12 words of context, changed words bolded, nearby changes merged
- Updated prompt to request numbered changes with verse location and WHY rationale
- Added cross-reference links between changes and diff files; fixed `_count_changes` bug

**Session 303 (2026-03-15)**: BiDi DOCX Fix — LRM Insertion
- Implemented LRM (U+200E) insertion after Hebrew+punctuation in all 5 DOCX code paths
- Fixes Word scrambling Hebrew word order with colons/semicolons between Hebrew segments
- Regenerated Psalm 40 and 22 DOCX successfully

**Session 302 (2026-03-15)**: Copy Editor Critical Reading Stance
- Added "CRITICAL READING STANCE" meta-reasoning preamble; strengthened categories 6, 9d, 9f with concrete self-tests
- Re-ran Psalm 40: now catches all 5 target issues (was 2/5), 17 total changes
- Documented LRM-based BiDi DOCX fix plan in `docs/session_tracking/BIDI_FIX_NOTES_SESSION_301.md`

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
**Active**: Unified Writer V4, Copy Editor (9-category), Opus 4.6 Master Writer, Sonnet 4.6 Micro, GPT-5.4 Figurative Curator, GPT-5.1 Liturgical Librarian
**Last Updated**: Session 306 (2026-03-15)

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
