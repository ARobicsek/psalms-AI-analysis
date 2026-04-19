# Psalms AI Commentary Pipeline

**Session**: 326 (2026-04-18)
**Phase**: Pipeline Production — tweaks and improvements

> **⚠ NEXT-SESSION PRIORITY**: Read [`docs/session_tracking/NEXT_SESSION_BRIEF.md`](docs/session_tracking/NEXT_SESSION_BRIEF.md) first. It contains the full implementation plan for fixing pipeline cost-accounting bugs (Session 327 work).

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.7, Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent pipeline and Hebrew concordance integration.

## Recent Work (Last 5 Sessions)

**Session 326 (2026-04-18)**: Audit of Pipeline Cost Accounting — Plan for Session 327
- Audited every LLM call site reachable from `run_enhanced_pipeline.py` / `run_si_pipeline.py`; verified via Anthropic docs that Claude's `output_tokens` already includes thinking tokens (billing correct as-is)
- Identified 5 silent billing bugs (GPT/Gemini `reasoning_tokens` not logged): `copy_editor.py`, `figurative_curator.py` (never logs), `scripture_verifier.py` (3 sites: GPT filter, Haiku filter, tool-use verifier); also: cost summary is never persisted to JSON
- Full implementation plan written to `docs/session_tracking/NEXT_SESSION_BRIEF.md`; recommended Sonnet 4.6 for Session 327 (mechanical plumbing work, clear patterns already in the codebase)

**Session 325 (2026-04-18)**: Master Writer on Opus 4.7 — Max Effort
- Confirmed via Anthropic docs that Opus 4.7 removed `budget_tokens` (400 error if set); adaptive is the only thinking mode, with a new `effort` param replacing fixed budgets
- Added `output_config={"effort": "max"}` to the Claude writer streaming call in `src/agents/archive/master_editor_v2.py`, gated by `"opus-4-7" in model_id` so Opus 4.6 callers are unaffected
- Rationale: Master Writer is long-form, high-stakes synthesis where quality matters more than latency/cost — max effort sits above xhigh and is the top capability tier

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

- **`docs/session_tracking/NEXT_SESSION_BRIEF.md` — Hit-the-ground-running plan for the upcoming session (check here first if present)**
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
