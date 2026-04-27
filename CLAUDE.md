# Psalms AI Commentary Pipeline

**Session**: 342 (2026-04-26)
**Phase**: Pipeline Production — tweaks and improvements

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.7, Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent pipeline and Hebrew concordance integration.

## Recent Work (Last 5 Sessions)
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

**Session 339 (2026-04-24)**: Surface Literary Echoes Models in DOCX + Lit Echoes Cost Subtotal in Terminal Tally
- Added Literary Echoes models to the "Models Used" section of the Methodological & Bibliographical Summary in all three renderers (`src/utils/document_generator.py`, `src/utils/combined_document_generator.py`, `src/utils/commentary_formatter.py`). Two new conditional lines render only if the corresponding `literary_echoes_pass_*` keys are present in `pipeline_stats.json`: "**Literary Echoes (Passes 1 & 2 — Generation)**" → `gemini-3.1-pro-preview` and "**Literary Echoes (Passes 3 & 4 — Verify + Reconstruct)**" → `gpt-5.4`. The tracker already recorded these keys via `track_model_for_step` in STEP 1b — the renderers just weren't reading them.
- Added a Literary Echoes subtotal to the final terminal cost tally in both `scripts/run_enhanced_pipeline.py` and `scripts/run_si_pipeline.py`. Introduced a `lit_echoes_cost` variable initialized to `0.0` before STEP 1b, populated from `lit_result.total_cost` on success, and printed after `cost_tracker.get_summary()` as "Literary Echoes subtotal (Passes 1-4): $X.XXXX" with a note that it's already included in the grand total (needed because the CostTracker aggregates by model, so lit-echoes Gemini/GPT usage gets lumped with other pipeline components that share those models).
- All five edited files parse clean via `ast.parse`. No new scripts; no change to pipeline step ordering or control flow.

**Session 338 (2026-04-23)**: Built `lit_echoes` Agent — Automated 4-Pass Literary Echoes in the Pipeline
- Built `src/agents/literary_echoes_agent.py` orchestrating the 4-pass workflow (Gemini 3.1 Pro generate → Gemini 3.1 Pro gap-fill → GPT-5.4 Responses-API with `web_search_preview` tool verify → GPT-5.4 Chat-Completions reconstruct). Rolling exclusion list scans the 4 most-recently-rendered `data/literary_echoes/*.txt` files by mtime and extracts authors via `^####\s+([^,]+),` regex, injecting them into both Pass 1 AND Pass 2 prompts as hard bans. Per-pass raw outputs + exact prompts sent + cost report saved to `output/psalm_NNN/literary_echoes/`; final copied to canonical `data/literary_echoes/psalm_NNN_literary_echoes.txt`. Created `scripts/run_literary_echoes.py` standalone runner and wired new STEP 1b (default-on, regenerate-and-overwrite, `--skip-lit-echoes` opt-out) into both `run_enhanced_pipeline.py` and `run_si_pipeline.py`.
- Prompt edits to `docs/prompts_reference/literary echoes pass {1,2} - tier override.txt`: removed Kendrick Lamar from Earned Canonical Slots and added to fully-banned list (alongside Homer/Dante/Virgil/Ovid); swapped "past Kendrick" hip-hop palette anchor to "past Jay-Z / Tupac"; added a narrow Offensive-Language Filter (three most-severe four-letter words only, historical mild scatology explicitly permitted); Pass 2 target bumped from 3-6 to 5-10 new comparisons. Pass 3 prompt got a one-line profanity-flag instruction so Pass 4 can strip. Archived the three pre-tier-override pass templates to `docs/prompts_reference/archive/`.
- Two bugs surfaced during Psalm 53 testing and fixed: (1) `gpt-5.1` at every `reasoning.effort` level self-terminated after one verse cluster on the ~30K-char Pass 4 reconstruction prompt — switched Pass 4 to `gpt-5.4` via `chat.completions` (Responses API triggered `content_filter` on the same content), net cost delta ~$0.04/psalm; (2) Pass 2 was using canonical-slot authors (Aeschylus, Paul Celan) that were on the cross-psalm exclusion list because the ban block was only injected into Pass 1 — fixed by propagating it to Pass 2 as well with explicit override of the canonical-slot allowance. Psalm 53 test run produced 7 clusters / 21 authors / 14K chars at total cost $0.945 across all 4 passes in ~10 minutes.



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
