# Psalms AI Commentary Pipeline

**Session**: 319 (2026-03-27)
**Phase**: Pipeline Production — tweaks and improvements

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent pipeline and Hebrew concordance integration.

## Recent Work (Last 5 Sessions)

**Session 319 (2026-03-27)**: Fix Split Block Quote Formatting in DOCX
- Fixed `_split_long_hebrew_block` regex: `**` bold markers and `/` poetry separators now allowed between Hebrew words
- Long Hebrew quotations with inline markdown are correctly extracted as unified block quotes with bold preserved
- Psalm 45 "The Logic of Therefore" and Molodowsky Yiddish quotation now render correctly

**Session 318 (2026-03-26)**: BiDi Double-Reversal Fix
- Fixed `_reverse_bare_hebrew_segments()` double-processing Hebrew already wrapped by paren/bracket handler
- Added placeholder protection for existing LRO/PDF blocks; added missing bare-segment call to soft-breaks path
- Psalm 43 `(תְּפִלָּה לִשְׁלוֹם הַמְּדִינָה)` now displays correctly in DOCX

**Session 317 (2026-03-18)**: SI Pipeline Parity Update
- Brought `run_si_pipeline.py` fully up to date with `run_enhanced_pipeline.py`
- Ported 12 improvements: concordance counting, exclude flags, macro_analysis in insights, file guards, error handling, etc.
- Fixed latent bug: insight extractor would crash if enabled (missing macro_analysis param)

**Session 316 (2026-03-18)**: Session Management Overhaul
- Restructured session management: CLAUDE.md is now single startup doc for both Claude Code and Gemini
- Archived IMPLEMENTATION_LOG sessions 241-299; moved feature docs to FEATURE_ARCHIVE.md
- Created Claude Code persistent memory; slimmed PROJECT_STATUS.md to stable reference

**Session 315 (2026-03-18)**: Divine Name Normalization & Citation Difference Accuracy
- Added reverse divine name mappings to citation verifier (El/Eli/Shaddai/Eloah patterns)
- Added NFC Unicode normalization; fixed `_describe_difference()` annotation stripping
- Psalm 42: 4 to 3 issues (eliminated false positive)
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
