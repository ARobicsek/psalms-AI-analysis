# Psalms AI Commentary Pipeline

**Session**: 316 (2026-03-18)
**Phase**: Pipeline Production — tweaks and improvements

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent pipeline and Hebrew concordance integration.

## Recent Work (Last 5 Sessions)

**Session 316 (2026-03-18)**: Session Management Overhaul
- Restructured session management: CLAUDE.md is now single startup doc for both Claude Code and Gemini
- Archived IMPLEMENTATION_LOG sessions 241-299; moved feature docs to FEATURE_ARCHIVE.md
- Created Claude Code persistent memory; slimmed PROJECT_STATUS.md to stable reference

**Session 315 (2026-03-18)**: Divine Name Normalization & Citation Difference Accuracy
- Added reverse divine name mappings to citation verifier (El/Eli/Shaddai/Eloah patterns)
- Added NFC Unicode normalization; fixed `_describe_difference()` annotation stripping
- Psalm 42: 4 to 3 issues (eliminated false positive)

**Session 314 (2026-03-17)**: GPT Filter Default, End-to-End Citation Fix Verified
- Made `--gpt-filter` default in all pipeline/verifier scripts; added `--no-gpt-filter`
- Fixed standalone verifier `--fix` bug; full end-to-end test on Psalm 41 passed ($0.53)

**Session 313 (2026-03-17)**: Citation Verifier — GPT-5.1 Judge, Precise Difference Hints
- Fixed `_describe_difference()` with greedy word alignment; added doubled-word detection
- Added `--gpt-filter` flag: GPT-5.1 achieves 5/5 real errors kept, 0 false positives

**Session 312 (2026-03-17)**: Haiku Tool-Use Citation Verifier Architecture
- Built `verify_citations_tooluse()` with prompt caching ($0.04/psalm)
- Regex verifier outperforms tool-use in accuracy and cost; integrated as optional `--tooluse-verify`

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
