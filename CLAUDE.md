# Psalms AI Commentary Pipeline

**Session**: 336 (2026-04-21)
**Phase**: Pipeline Production — tweaks and improvements

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.7, Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent pipeline and Hebrew concordance integration.

## Recent Work (Last 5 Sessions)

**Session 336 (2026-04-21)**: Stabilize Aptos Fonts and Methodology Summary for DOCX
- Fixed 
un_docx_only.py pointing to an outdated filename summary.json, restoring compiling of the Methodology page on manual regenerations.
- Replaced ambiguous spacing logic in inline verse blocks with an explicit is_verse_header parameter passed from the top-down parsing logic.
- Ensured long standalone quotes reliably use default Times New Roman while true primary verses reliably render in Aptos.

**Session 335 (2026-04-21)**: Completely Fix Hebrew Verse Punctuation Alignment in DOCX
- Discovered that the _is_hebrew_dominant check was missing in _add_paragraph_with_soft_breaks, causing short verses without sof-pasuq (like Ps 51:1,4) to be routed to the fallback processing which left trailing punctuation outside the LRO block and therefore visually rendered on the wrong side.
- Propagated the _is_hebrew_dominant logic to _add_paragraph_with_soft_breaks in document_generator.py and combined_document_generator.py formatting methods to ensure proper RLM/LRO handling for all short verses.

**Session 334 (2026-04-21)**: Fix Hebrew Verse Punctuation Alignment in DOCX
- Resolved a Word BiDi rendering issue where trailing punctuation on verses erroneously appeared on the visual right edge for both long block quotes and short inline verses.
- Added explicit RLM (`\u200F`) injection to `_add_hebrew_block_paragraph` for multi-line blocks, and updated nested format parsing to properly apply `_is_hebrew_dominant` logic for short inline verses, ensuring full LRO reversal.
- Added `scripts/run_docx_only.py` to allow isolated regeneration of Word documents without re-running earlier pipeline steps.

**Session 333 (2026-04-21)**: Verified Psalm 51 Pipeline Fixes
- Monitored the end-to-end re-run of the Psalm 51 pipeline (`--skip-macro`) to confirm the previous session's fixes were successful.
- Verified that the Master Writer completed commentary for all 21 verses without truncation, confirming the `max_tokens` increase to 128K provided sufficient reasoning budget.
- Confirmed the Figurative Curator initialized properly, eliminating the 82K character input bloat from raw instances and successfully restoring the per-vehicle breakdown in the DOCX methodology section.

**Session 332 (2026-04-21)**: Fix Psalm 51 Pipeline — Curator Bug, Token Limit, Input Bloat
- Diagnosed Psalm 51 truncation (Master Writer stopped mid-verse-8): `max_tokens=64000` in `master_editor_v2.py` was consumed by adaptive thinking + max effort, leaving insufficient budget for 21-verse commentary. Fixed: bumped to `128000`
- Found and fixed a Session 327 regression in `research_assembler.py:720` — `FigurativeCurator(cost_tracker=self.cost_tracker)` referenced an unset attribute (`self.cost_tracker` never assigned; should use local param `cost_tracker`). The `try/except` silently disabled the curator for ALL runs since April 18, causing raw figurative data (118K chars) to replace curated output (36K chars), bloating the Master Writer prompt by ~82K chars and leaving `figurative_parallels_reviewed` empty
- Both fixes verified via code analysis; Psalm 51 re-run triggered from this session to validate full 21-verse output, curator activation, and figurative breakdown population

**: Opus 4.7 Prompt Polish — Parenthetical Translations + Stray Quotes Around Hebrew
- Diagnosed why Opus 4.7 wrapped every English translation in parens (e.g., `אַל־יֶחֱרַשׁ ("let Him not be silent")`): the Master Writer prompt's "CORRECT examples" at `master_editor.py:60-63` put English in parens, and Opus 4.7 pattern-matched on them literally (Opus 4.6 inferred intent better); rewrote Rule 1 with a new Parentheses Rule offering three acceptable patterns (FLOWING, apposition, whole-unit parenthetical) and explicit INCORRECT examples — same rule applied to Greek/Aramaic/Latin translations
- Fixed a related bug surfaced in Psalm 50: Opus 4.7 wraps long Hebrew citations in straight quotes (`"רָם וְנִשָּׂא..."`) which orphan visually when BiDi line-wrapping sets the Hebrew on its own line in DOCX; added `CopyEditor._strip_quotes_around_source_text` static method that strips matched-pair quotes around pure Hebrew/Greek spans (no Latin letters between) and wired it into `edit_commentary` step 7b — after diff generation so the copy-edit diff stays clean
- Prompt changes applied to production `master_editor.py:MASTER_WRITER_PROMPT_V4` (auto-propagates to `master_editor_si.py` via `.replace()`); matching fixes applied to archived `master_editor_v2.py` prompts for consistency; regex verified against 5 test cases (strips Hebrew/Greek spans, leaves mixed-script and Pattern-B Hebrew+English untouched)

**: Concordance Entries Breakdown in DOCX Methods Section
- Added per-query breakdown to "Concordance Entries Reviewed" line (matching format of "Figurative Concordance Matches Reviewed") — now shows total count + each search term with its result count in parentheses
- All concordance search terms run through `DivineNamesModifier` before display, ensuring divine names are properly modified in the methods section
- Updated all 3 formatters: `document_generator.py`, `combined_document_generator.py`, `commentary_formatter.py`; backward-compatible with legacy stats files that only have `total_results`


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
