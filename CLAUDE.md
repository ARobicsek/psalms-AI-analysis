# Psalms AI Commentary Pipeline - Quick Reference

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude AI (Sonnet 4.5, Haiku 4.5) with multi-agent framework and Hebrew concordance integration.

## Essential Documentation

**Start Here:**
- `README.md` - Project overview, installation, usage
- `docs/session_tracking/PROJECT_STATUS.md` - Current phase, tasks, metrics (Session 181)
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` - Technical specifications, schemas
- `docs/guides/DEVELOPER_GUIDE.md` - Development workflow, coding standards

## Recent Major Changes (Last 5 Sessions)

**Session 258 (2026-02-12)**: Token Reduction Phase B
- B1: Related psalms default to no full texts (`include_full_text=False`), saving ~13K chars
- B2: BDB lexicon entries truncated to ~500 chars max (from ~2,400 avg), saving ~21K chars
- B3: Compact markdown formatting: merged lexicon headers, inline concordance results, compact commentary
- B4: Added telegraphic writing instructions to macro/micro analyst prompts for denser AI output
- Updated preamble text in related_psalms_librarian to reflect no-full-text default

**Session 257 (2026-02-12)**: Token Reduction Phase A
- Removed 10,724 chars of static commentator biographical essays from research bundle (replaced with dates only)
- Fixed analytical framework duplication bug: was embedded in research bundle AND passed separately to Master Writer
- Added `include_working_notes=False` to strip 26,845 chars from micro analyst input
- Total savings: ~45K tokens per psalm across all consumers

**Session 256 (2026-02-12)**: Prompt Overhaul Phase 1 Completion & Opus 4.6 Upgrade
- Migrated V3 prompt logic to `master_editor.py`, archived legacy editors
- Upgraded InsightExtractor and QuestionCurator to claude-opus-4-6

**Session 255 (2026-02-11)**: Prompt Overhaul Phase 1 - V3 Editor
- Created `master_editor_v3.py` with 9 key prompt changes
- Fixed MicroAnalyst JSON truncation (increased output tokens to 65k)

**Session 254 (2026-02-09)**: Opus 4.6 Bug Fixes + Model Tracking
- Fixed adaptive thinking JSON parsing in micro_analyst
- Added model tracking for skipped pipeline steps

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
