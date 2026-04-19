# Psalms AI Commentary Pipeline

**Session**: 330 (2026-04-19)
**Phase**: Pipeline Production — tweaks and improvements

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.7, Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent pipeline and Hebrew concordance integration.

## Recent Work (Last 5 Sessions)

**Session 330 (2026-04-19)**: Concordance Entries Breakdown in DOCX Methods Section
- Added per-query breakdown to "Concordance Entries Reviewed" line (matching format of "Figurative Concordance Matches Reviewed") — now shows total count + each search term with its result count in parentheses
- All concordance search terms run through `DivineNamesModifier` before display, ensuring divine names are properly modified in the methods section
- Updated all 3 formatters: `document_generator.py`, `combined_document_generator.py`, `commentary_formatter.py`; backward-compatible with legacy stats files that only have `total_results`

**Session 328 (2026-04-18)**: Fix Displaced-Liturgical-Content Recovery for Opus 4.7 Headers
- Diagnosed a Psalm 50 DOCX bug where "Key verses" liturgical entries (bold `**Verse N** (...) appears in...`) showed up under "Verse-by-Verse Commentary" instead of the Modern Jewish Liturgical Use section; confirmed Master Writer output is correct — the Copy Editor displaces them, and a recovery routine in the pipeline was silently failing due to a case-sensitive regex
- Opus 4.7 faithfully emits `#### Key verses` (lowercase, per prompt at `master_editor.py:255`), but the detection regex `####\s*Key Verse` in `_extract_sections_from_copy_edited` was case-sensitive — so the recovery branch never fired on Opus 4.7 output (it worked on Opus 4.6's `#### Key Verses and Phrases` purely by substring luck)
- Fixed three call sites (`run_enhanced_pipeline.py:226`, `run_si_pipeline.py:229`, `copy_editor.py:818`) to use `####\s*Key\s+[Vv]erse` regex, re-extracted + regenerated Psalm 50 DOCX (recovery moved 2,888 chars back to the intro); all three sites now handle both old and new header variants

**Session 327 (2026-04-18)**: Fix Pipeline Cost Accounting + Master Writer Thinking Visibility
- Fixed 4 billing bugs: `copy_editor.py` GPT path passes `reasoning_tokens`; `figurative_curator.py` logs to `cost_tracker`; `scripture_verifier.py` all 3 call sites log; `research_assembler.py` passes tracker to `FigurativeCurator`; both pipelines persist cost to `psalm_NNN_cost.json`
- Fix 5: `master_editor_v2.py` `_call_claude_writer` switched to event-based stream iteration; now logs `~N thinking tokens (included in M output total)` after each Master Writer run
- All 5 fixes from the Session 326 audit plan implemented; `thinking_tokens=0` in `add_usage()` kept intentional — Anthropic folds thinking into `output_tokens`

**Session 326 (2026-04-18)**: Audit of Pipeline Cost Accounting — Plan for Session 327
- Audited every LLM call site reachable from `run_enhanced_pipeline.py` / `run_si_pipeline.py`; verified via Anthropic docs that Claude's `output_tokens` already includes thinking tokens (billing correct as-is)
- Identified 5 silent billing bugs (GPT/Gemini `reasoning_tokens` not logged): `copy_editor.py`, `figurative_curator.py` (never logs), `scripture_verifier.py` (3 sites: GPT filter, Haiku filter, tool-use verifier); also: cost summary is never persisted to JSON
- Full implementation plan written to `docs/session_tracking/NEXT_SESSION_BRIEF.md`; recommended Sonnet 4.6 for Session 327 (mechanical plumbing work, clear patterns already in the codebase)

**Session 325 (2026-04-18)**: Master Writer on Opus 4.7 — Max Effort
- Confirmed via Anthropic docs that Opus 4.7 removed `budget_tokens` (400 error if set); adaptive is the only thinking mode, with a new `effort` param replacing fixed budgets
- Added `output_config={"effort": "max"}` to the Claude writer streaming call in `src/agents/archive/master_editor_v2.py`, gated by `"opus-4-7" in model_id` so Opus 4.6 callers are unaffected
- Rationale: Master Writer is long-form, high-stakes synthesis where quality matters more than latency/cost — max effort sits above xhigh and is the top capability tier


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
