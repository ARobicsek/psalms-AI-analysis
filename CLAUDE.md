# Psalms AI Commentary Pipeline - Quick Reference

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent framework and Hebrew concordance integration.

## Essential Documentation

**Start Here:**
- `README.md` - Project overview, installation, usage
- `docs/session_tracking/PROJECT_STATUS.md` - Current phase, tasks, metrics (Session 300)
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` - Technical specifications, schemas
- `docs/guides/DEVELOPER_GUIDE.md` - Development workflow, coding standards

## Recent Major Changes (Last 5 Sessions)

**Session 301 (2026-03-14)**: Copy Editor Prompt Hardening (9d–9g)
- Added copy editor sub-categories 9d–9g (false contrasts, overclaimed scope, opaque logic, wrong analogies)
- Re-ran copy editor for Psalm 40; auto-caught 2 of 5 identified issues
- BiDi fixes attempted but reverted due to regressions (notes in `docs/session_tracking/BIDI_FIX_NOTES_SESSION_301.md`)

**Session 300 (2026-03-13)**: Model Swap — Figurative Curator & Liturgical Librarian
- Swapped Figurative Curator from `gemini-3.1-pro-preview` → `gpt-5.4` (high reasoning)
- Swapped Liturgical Librarian from `gemini-2.5-pro` → `gpt-5.1` (high reasoning)
- Kept `gemini-2.5-pro` only for Synthesis Writer large-psalm fallback

**Session 299 (2026-03-09)**: Fixing Psalm 40 Pipeline Issues
- Hardened pipeline section extraction for displaced liturgical content
- Strengthened Master Writer liturgical prompt

**Session 298 (2026-03-09)**: Error and Retry Tracking in Cost Summary
- Added event tracking to CostTracker for pipeline retry visibility

**Session 297 (2026-03-09)**: Micro Analyst JSON Repair & Validation
- Integrated `json-repair` library with structural validation for truncated outputs

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
**Last Updated**: Session 301 (2026-03-14)

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
