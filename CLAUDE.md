# Psalms AI Commentary Pipeline

**Session**: 355 (2026-06-08)
**Phase**: Pipeline Production — tweaks and improvements

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent pipeline and Hebrew concordance integration.

## Recent Work (Last 5 Sessions)
**Session 355 (2026-06-08)**: Post-migration path fix — figurative-language DB
- Pipeline crashed in **Step 2 (Micro Analysis)** constructing `FigurativeLibrarian`: the hardcoded OneDrive path `C:/Users/ariro/OneDrive/Documents/Bible/database/Biblical_fig_language.db` was dead after the OneDrive→C-drive repo migration. That DB lives in the **separate `bible` repo**, which was also migrated to `C:\dev\personal\bible` (now a sibling of `psalms`).
- Fix (`src/agents/figurative_librarian.py:35`): replaced the hardcoded absolute path with a **repo-relative default** — `Path(__file__).resolve().parents[2].parent / "bible" / "database" / "Biblical_fig_language.db"` — plus a `FIGURATIVE_DB_PATH` **env-var override**. Resolves to the live migrated copy (152 MB, byte-identical to the OneDrive `_Archive\Migrated repos (originals)` backup), *not* the OneDrive archive. Verified: path resolves + exists; `FigurativeLibrarian` and the full `MicroAnalystV2`→`ResearchAssembler`→`FigurativeLibrarian` chain construct cleanly.
- Swept `src/` + `scripts/` for other dead paths: **this was the only OneDrive/`C:/Users` reference in production code** (all others live in `archive/`, `scratch/`, which the pipeline never touches). Standing dependency: psalms needs the sibling `bible` repo; if the two are ever moved apart, set `FIGURATIVE_DB_PATH`. Env note: in **git bash**, activate the venv with `source venv/Scripts/activate` (the bare `C:\…\activate` path fails — bash eats the backslashes); **PowerShell** auto-resolves the venv. No scripts created/changed.
**Session 354 (2026-06-04)**: DOCX BiDi — verse-table Hebrew 13pt + final size/format tweaks
- Bumped verse-table Hebrew (top-of-DOCX psalm text table) from 12pt → **13pt** (`_format_psalm_text`, both `font.size` and `szCs`). All Hebrew now uniformly 13pt across the document.
- No new scripts. Production Ps 67 DOCX regenerated; committed and pushed to `main`.
**Session 353 (2026-06-04)**: DOCX BiDi — native RTL runs replace the reverse+LRO engine
- Fixed 3 reported Hebrew-rendering bugs in the generated DOCX (`src/utils/document_generator.py`), all from one root cause: inline Hebrew was **pre-reversed into visual order + wrapped in LEFT-TO-RIGHT OVERRIDE**. (1) garbled word order when a bold/italic marker split a phrase; (2) backwards line-wrap (end of quote on the upper line) — inherent to LRO; (3) the "Concordance Entries Reviewed" summary scrambled.
- **Fix = native RTL** (what the verse table + Arabic path already do): keep Hebrew in logical order, mark runs `w:rtl` + cs font, paragraph stays LTR; Word's bidi engine handles order/nikud/wrapping. New `_add_inline_runs` + `_segment_by_script` (glues intra-phrase spaces/maqqef and the geresh-style `ה'` apostrophe; leaves English `king's`) + `_mark_run_hebrew` replace all ~6 reverse+LRO paths. `_join_rtl_runs_across_whitespace` (post-pass) fixes the bold-split boundary space. `_add_summary_paragraph` renders a Hebrew breakdown as a native RTL paragraph. Removed ~227 lines of dead reversal methods.
- **Round 2 (3 more, on DOCX review)**: (a) verse-header verse lines were garbled (a `;` between cola swapped them) → standalone primarily-Hebrew lines now render as a **single native RTL run** (`_add_primarily_hebrew_line`), which also fixes ketiv/qere `[brackets]` + final sof-pasuq placement; (b) verse headers now **13pt**; (c) inline body Hebrew was ~11pt → set `szCs` on the Normal/BodySans/SummaryText styles (python-docx sets `w:sz` but not `w:szCs`). Also generalized the RTL-join post-pass to neutral-only runs (`;`/`:`/`,` between cola), excluding directional brackets/parens.
- **Round 3 (concordance + sizing)**: concordance breakdown reformatted to readable `root — count;` entries (each a single RTL run so it can't split across a wrap; em-dash binds count to its root — fixes the unreadable parenthesized form). All Hebrew bumped +1pt to match the Aptos English visually (body 12→**13pt**, summary 9→**10pt**), since Times New Roman Hebrew reads smaller. `run_docx_only.py` confirmed to use the new rendering.
- **Verified by rendering DOCX→PDF via Word COM + PyMuPDF size/coordinate extraction** (no LLM cost; existing markdown only): Ps 67 all issues fixed (coordinate-verified incl. `ה'` apostrophe-name and v.2 header order/size); Ps 51/9/50/18 clean for ketiv/qere `[brackets]`, block quotes, parens, smart quotes, paseq, long superscriptions, verse-header sizing. `combined_document_generator.py` left as-is (retired path) with a ⚠️ docstring flagging its outdated BiDi. Regenerate any psalm's DOCX with `python scripts/run_docx_only.py N`.
**Session 352 (2026-06-02)**: Macro → Opus 4.8 (adaptive/high) + lemma-dedup of root traces
- **Task 1 — Macro agent now `claude-opus-4-8`** (was 4-6), budget-neutral (all Opus tiers priced identically; macro ≈ $0.36/psalm). Mirrored the Master Writer's **model-gated effort**: opus-4-8 → `output_config={"effort":"high"}`, opus-4-7 → `"max"`, **opus-4-6 → omit `output_config`** (older models reject it) — so this was two changes (model ID + effort `max→high`), not just an ID swap. Spots: `MacroAnalyst.DEFAULT_MODEL` + the streaming call (`src/agents/macro_analyst.py`), and the `macro_model`/`macro_mdl` defaults in `scripts/run_enhanced_pipeline.py` + `scripts/run_si_pipeline.py`.
- **Task 2 — `_augment_with_root_searches` dedups by RESOLVED LEMMA, not surface string** (`src/agents/micro_analyst.py`). After Session 351, different spellings resolve to one lemma, so the old consonantal dedup let the same lemma be traced in several bundles (Ps 59: משגב≡משגבי, נוע≡ינועו → identical verse-lists, token noise). Now each candidate root + each existing single-word pick (incl. its single-word alternates the librarian folds in) is resolved via `search._resolve_lemma`; dedup is on the lemma set, with a consonantal fallback when no lemma resolves. Verified deterministically (no LLM call) on Ps 59: **0 duplicated lemmas** across the 12 root traces; a seeded `נוע` pick correctly suppresses derived `ינועו`, freeing the cap slot for another distinct lemma. Yield unchanged (same lemma → same verses).
- **No live pipeline run this session** (Task 1 is low-risk same-family + lighter effort; no formal quality gate needed). A 1-psalm macro sanity run (~$0.36) remains available if desired. Also retired the `NEXT_SESSION_BRIEF.md` doc from the workflow (per user — session handoff now lives in this file + `IMPLEMENTATION_LOG.md`).
**Session 351 (2026-06-02)**: Lemma-Aware Concordance (D & E) — true morphology wired in
- Added a persistent **`lemma` column** to the `concordance` table (`database/tanakh.db`), populated once from ETCBC/BHSA `lex_utf8` via new `scripts/add_lemma_column.py` (**96.3% coverage**, indexed `idx_concordance_lemma`). Root traces and ≤2-word collocations now match on an exact, indexed `WHERE lemma = ?` — prefix/suffix/conjugation/word-order tolerant — via new methods in `src/concordance/search.py` (`_resolve_lemma`, `search_lemma`, `search_lemmas_in_verse`) wired into `concordance_librarian.py`. This replaces runtime string-expansion + `is_root_match` (now bypassed in production); surface path retained as fallback for cache misses.
- **Two corrections to the brief, forced by the data**: (1) BHSA `root` is only **16.9%** coverage and `None` on every target (פלג/נוד/נדד/חסד/אמת) → shipped **lemma (lex)**, not root. (2) The brief's positional join is broken (BHSA splits proclitics ב/כ/ל/מ/ו/ה into separate word nodes; only 26% positional match) → used **greedy concat-alignment** (our token = concat of consecutive BHSA tokens, assign content lemma); misses stay NULL→fallback, never wrong. Also `T.sectionFromNode` returns English book names (`2_Kings`), not Latin `F.book.v` (`Reges_II`). Full pivot recorded in `LEMMA_ROOT_SEARCH_PROPOSAL.md` (STATUS banner).
- Selection now ranks by **true lemma frequency** (`librarian.lemma_frequency`), retiring the surface-frequency "prefer 3-letter forms" hack (`root_selection.py`, `micro_analyst.py`); `COMMON_CAP` aligned 60→120 (`research_assembler.py`). Validated: `EXPERIMENT_concordance_eval.py 54-58` external yield **24% → 96%** (110/115, 0 common-dropped); spot-checks pass (`ימיש`→Exod 13:22 via lemma מוש, `חסד אמת`→Exod 34:6). Also validated **end-to-end on a full Ps 59 run** ($6.81): intertexts landed in the final prose (`שחק`+`לעג`→Ps 2:4 laughter; `שגב`→מִשְׂגָּב fortress→2 Sam 22:3; `נוע`→"wander"). Follow-ups (done in Session 352): macro→opus-4-8 (adaptive/high); dedupe augmented roots by resolved lemma.
## Quick Commands

```bash
python scripts/run_enhanced_pipeline.py 23                             # Process single psalm (synthesis-discovery sidecar ON by default, ~+$2)
python scripts/run_enhanced_pipeline.py 23 --resume                     # Resume from last step
python scripts/run_enhanced_pipeline.py 23 --skip-synthesis-discovery   # Disable the Session-347 cross-verse synthesis sidecar
python scripts/run_si_pipeline.py 19                 # Special Instruction pipeline (synthesis-discovery sidecar ON by default)
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
