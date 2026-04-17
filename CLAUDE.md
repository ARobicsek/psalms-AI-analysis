# Psalms AI Commentary Pipeline

**Session**: 324 (2026-04-17)
**Phase**: Pipeline Production — tweaks and improvements

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.7, Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent pipeline and Hebrew concordance integration.

## Recent Work (Last 5 Sessions)

**Session 324 (2026-04-17)**: Upgrade Master Writer to Claude Opus 4.7
- Changed Master Writer default model from `claude-opus-4-6` to `claude-opus-4-7` in both pipeline scripts
- Added `claude-opus-4-7` pricing entry to cost_tracker.py; updated all documentation (architecture, scriptReferences, How to Run)
- Macro Analyst remains on Opus 4.6; DOCX methodology page picks up model dynamically — no code change needed there

**Session 323 (2026-04-14)**: Master Editor Outline Prompt Documentation
- Archived the experimental paragraph outline mapping prompt into `docs/archive/deprecated/OLD_master_editor_paragraph_outline_prompt.md`
- Reverted the uncommitted test modifications from `src/agents/master_editor.py` so they don't persist in the pipeline

**Session 322 (2026-04-09)**: ASCII Hyphen BiDi Fix for DOCX Hebrew Processing
- Added ASCII hyphen (U+002D) support to `_split_into_grapheme_clusters`, `_reverse_bare_hebrew_segments`, and `_reverse_primarily_hebrew_line`
- Psalm 47 verse headers no longer lose maqqaf-hyphens; inline multi-word Hebrew with hyphens no longer garbled

**Session 321 (2026-04-09)**: Ellipsis BiDi Fix in DOCX Hebrew Block Detection
- Added Unicode ellipsis (`…`, U+2026) to separator regexes in both `_split_long_hebrew_block` and `_reverse_bare_hebrew_segments`
- Psalm 49 Selichot quotation (10 Hebrew words split by `…`) now correctly detected as a long block and rendered as standalone RTL paragraph

**Session 320 (2026-03-29)**: DOCX Formatting Fixes for Psalms 44, 49, and 50
- Fixed `_extract_sections_from_copy_edited` to use a flexible regex for "Key Verses" header, correctly restoring displaced liturgical content in Psalm 44.
- Expanded `_split_long_hebrew_block` regex to support punctuation like `!`, `?`, `—`, `׃`, and `׀` inside Hebrew blocks.
- Prevented 14-word and punctuation-heavy Hebrew block quotes in Psalms 49 and 50 from being improperly split.

## Quick Commands

```bash
python scripts/run_enhanced_pipeline.py 23          # Process single psalm
python scripts/run_enhanced_pipeline.py 23 --resume  # Resume from last step
python scripts/run_si_pipeline.py 19                 # Special Instruction pipeline
python scripts/run_copy_editor.py 36 37 38           # Standalone copy editor
python scripts/run_scripture_verifier.py 41          # Standalone citation verifier
python scripts/converse_with_editor.py 21            # Chat with Master Editor
```

## Key Directories

- `src/agents/` — AI agent implementations (macro, micro, synthesis, editors, copy editor)
- `src/concordance/` — 4-layer Hebrew search system
- `database/` — SQLite databases (tanakh.db, psalm_relationships.db)
- `data/deep_research/` — Gemini Deep Research outputs
- `data/special_instructions/` — Author directive files for SI pipeline
- `output/psalm_*/` — Generated commentary (production)
- `scripts/` — Pipeline runners and utilities

## Reference Docs (read only when needed)

- `docs/session_tracking/scriptReferences.md` — All scripts with descriptions
- `docs/session_tracking/PROJECT_STATUS.md` — Pipeline phases, active features, databases
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — Detailed session history (300+)
- `docs/session_tracking/FEATURE_ARCHIVE.md` — Detailed docs for completed features
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` — Full system architecture
- `docs/architecture/TOKEN_REDUCTION_PHASE_B.md` — Ready-to-implement token reduction tasks

## File Organization Rules

- **Production code:** `src/`, `main.py`, `scripts/`
- **Experimental/test:** Use during session, archive immediately after
- **Archive after 1 session:** Test scripts, debug outputs, temp files → `archive/`
- **Never commit:** `*.log`, `*_output.txt`, temp analysis files (in .gitignore)

## End-of-Session Checklist

1. **Update this file (CLAUDE.md)**: Increment session number (line 3), replace oldest of 5 recent entries
2. **Update IMPLEMENTATION_LOG.md**: Add detailed session entry at top
3. **Update scriptReferences.md**: If scripts were created or significantly changed
