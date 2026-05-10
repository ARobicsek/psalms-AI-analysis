# Psalms AI Commentary Pipeline

**Session**: 344 (2026-05-10)
**Phase**: Pipeline Production — tweaks and improvements

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.7, Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent pipeline and Hebrew concordance integration.

## Recent Work (Last 5 Sessions)
**Session 344 (2026-05-10)**: Improve Wit + Literary Echoes Context in Master Writer Prompt
- Added RULE 13 (WIT — DRY, GENTLE, SPARING) to `MASTER_WRITER_PROMPT_V4` in `src/agents/master_editor.py`, anchored to Ps 48 "real-estate listing" and Ps 52 "one does not easily worship" as gold-standard examples; added explicit AVOID list (stand-up voice, knowing winks, exclamation-point jokes) plus matching FINAL VALIDATION CHECKLIST entry. The new RULE flows automatically through `MasterEditorSI` since the SI agent injects into the same V4 template.
- Restructured item 12 (Cross-Cultural Literary Echoes) into a four-step pattern: set up the trigger → frame the source itself with date and historical/biographical/thematic context (not just author + work title) → quote 3-6 lines original + English → unfold the resonance across 3-5 sentences. Explicit length permission (4-8 sentences per echo) plus three new checklist items (depth, source framing, basics).
- Relaxed quotation cap from 2-4 lines → 4-8 lines (tight cluster) and analysis cap from EXACTLY 2-3 sentences → 3-5 sentences in `docs/prompts_reference/literary echoes pass 1 - tier override.txt` and `pass 2 - tier override.txt`, giving the master writer richer raw scaffolding. Verified on Psalm 53: v1 had 2 thin echoes; v2 yields 7 well-contextualized echoes (Lorca, Stevens, Hardy, Auden, Miller, Akhmatova, Farrokhzad) with 4-6 line source quotations and dry observational wit ("the world's most polite recruiting pitch"; "their hearts speak the same sentence; only their footnotes differ").

**Session 343 (2026-05-05)**: Fix Resume-Mode Literary Echoes Model Tracking
- Fixed a data persistence issue where Literary Echoes models were missing from the Methodological Summary when the pipeline was resumed and Step 1b was skipped.
- Updated `run_enhanced_pipeline.py` and `run_si_pipeline.py` to register the models into the tracker during skip logic, and updated the markdown parser to recover them.
- Updated `ResearchAssembler` to permanently store the models in the `research_v2.md` bundle. Verified fix via mock resume on Psalm 53.

**Session 342 (2026-04-26)**: API Quota Guard — Fail-Fast on Billing Exhaustion
- Built `src/utils/api_guard.py`: centralized utility that distinguishes permanent quota/billing errors (OpenAI `insufficient_quota`, Anthropic `credit balance too low`, Google `RESOURCE_EXHAUSTED`) from transient rate limits. Includes `halt_on_quota()` which saves partial costs, prints a clear halt message, plays 3 descending beeps (Windows), and exits with code 2.
- Modified all 7 `except` blocks in both `run_enhanced_pipeline.py` and `run_si_pipeline.py` to call `halt_on_quota()` before falling through to non-fatal handling. Replaced the hand-coded `openai.RateLimitError` catch in Step 4 with the unified utility. Created `scripts/test_api_guard.py` (8 unit tests, all pass).

**Session 341 (2026-04-26)**: Investigate Psalm 67 Pipeline + Fix Resume-Mode Literary Echoes
- Investigated why Psalm 67's pipeline cost was lower than expected ($2.43). Diagnosed three OpenAI `429 insufficient_quota` failures: Literary Echoes passes 3-4, Scripture Citation Verifier, and Copy Editor all failed non-fatally. Core pipeline (Macro, Micro, Master Writer) ran successfully.
- Fixed `--resume` mode in `run_enhanced_pipeline.py` to auto-skip Literary Echoes when `data/literary_echoes/psalm_NNN_literary_echoes.txt` already exists, preventing expensive regeneration on resume. Full fresh runs still regenerate as intended.

**Session 340 (2026-04-25)**: Evaluated GPT-5.5 Pro for Master Editor
- Created and executed a test harness (`scripts/run_master_editor_gpt5_5_test.py`) to run the `gpt-5.5-pro` model as the Master Editor for Psalm 51 using the OpenAI Responses API.
- Fixed a Unicode encode error (`[OK]` replacement) and successfully generated a commentary docx using `DocumentGenerator` as fallback.
- Determined that `gpt-5.5-pro` with high reasoning effort provides insufficient quality improvement over Claude Opus 4.7 to justify the dramatic cost increase (~$12 vs ~$2 per psalm), largely due to the massive invisible thinking token consumption on the ~200k context window.

## Quick Commands

```bash
python scripts/run_enhanced_pipeline.py 23          # Process single psalm
python scripts/run_enhanced_pipeline.py 23 --resume  # Resume from last step
python scripts/run_si_pipeline.py 19                 # Special Instruction pipeline
python scripts/run_literary_echoes.py 53             # Standalone 4-pass literary echoes (default: regenerate)
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
