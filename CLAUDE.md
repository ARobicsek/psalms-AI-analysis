# Psalms AI Commentary Pipeline

**Session**: 352 (2026-06-02)
**Phase**: Pipeline Production — tweaks and improvements

AI-powered system generating scholarly verse-by-verse commentary for all 150 Psalms using Claude (Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 4.6), GPT (5.1, 5.4), and Gemini (2.5 Pro fallback) with multi-agent pipeline and Hebrew concordance integration.

## Recent Work (Last 5 Sessions)
**Session 352 (2026-06-02)**: Macro → Opus 4.8 (adaptive/high) + lemma-dedup of root traces
- **Task 1 — Macro agent now `claude-opus-4-8`** (was 4-6), budget-neutral (all Opus tiers priced identically; macro ≈ $0.36/psalm). Mirrored the Master Writer's **model-gated effort**: opus-4-8 → `output_config={"effort":"high"}`, opus-4-7 → `"max"`, **opus-4-6 → omit `output_config`** (older models reject it) — so this was two changes (model ID + effort `max→high`), not just an ID swap. Spots: `MacroAnalyst.DEFAULT_MODEL` + the streaming call (`src/agents/macro_analyst.py`), and the `macro_model`/`macro_mdl` defaults in `scripts/run_enhanced_pipeline.py` + `scripts/run_si_pipeline.py`.
- **Task 2 — `_augment_with_root_searches` dedups by RESOLVED LEMMA, not surface string** (`src/agents/micro_analyst.py`). After Session 351, different spellings resolve to one lemma, so the old consonantal dedup let the same lemma be traced in several bundles (Ps 59: משגב≡משגבי, נוע≡ינועו → identical verse-lists, token noise). Now each candidate root + each existing single-word pick (incl. its single-word alternates the librarian folds in) is resolved via `search._resolve_lemma`; dedup is on the lemma set, with a consonantal fallback when no lemma resolves. Verified deterministically (no LLM call) on Ps 59: **0 duplicated lemmas** across the 12 root traces; a seeded `נוע` pick correctly suppresses derived `ינועו`, freeing the cap slot for another distinct lemma. Yield unchanged (same lemma → same verses).
- **No live pipeline run this session** (Task 1 is low-risk same-family + lighter effort; no formal quality gate needed). A 1-psalm macro sanity run (~$0.36) remains available if desired. Also retired the `NEXT_SESSION_BRIEF.md` doc from the workflow (per user — session handoff now lives in this file + `IMPLEMENTATION_LOG.md`).
**Session 351 (2026-06-02)**: Lemma-Aware Concordance (D & E) — true morphology wired in
- Added a persistent **`lemma` column** to the `concordance` table (`database/tanakh.db`), populated once from ETCBC/BHSA `lex_utf8` via new `scripts/add_lemma_column.py` (**96.3% coverage**, indexed `idx_concordance_lemma`). Root traces and ≤2-word collocations now match on an exact, indexed `WHERE lemma = ?` — prefix/suffix/conjugation/word-order tolerant — via new methods in `src/concordance/search.py` (`_resolve_lemma`, `search_lemma`, `search_lemmas_in_verse`) wired into `concordance_librarian.py`. This replaces runtime string-expansion + `is_root_match` (now bypassed in production); surface path retained as fallback for cache misses.
- **Two corrections to the brief, forced by the data**: (1) BHSA `root` is only **16.9%** coverage and `None` on every target (פלג/נוד/נדד/חסד/אמת) → shipped **lemma (lex)**, not root. (2) The brief's positional join is broken (BHSA splits proclitics ב/כ/ל/מ/ו/ה into separate word nodes; only 26% positional match) → used **greedy concat-alignment** (our token = concat of consecutive BHSA tokens, assign content lemma); misses stay NULL→fallback, never wrong. Also `T.sectionFromNode` returns English book names (`2_Kings`), not Latin `F.book.v` (`Reges_II`). Full pivot recorded in `LEMMA_ROOT_SEARCH_PROPOSAL.md` (STATUS banner).
- Selection now ranks by **true lemma frequency** (`librarian.lemma_frequency`), retiring the surface-frequency "prefer 3-letter forms" hack (`root_selection.py`, `micro_analyst.py`); `COMMON_CAP` aligned 60→120 (`research_assembler.py`). Validated: `EXPERIMENT_concordance_eval.py 54-58` external yield **24% → 96%** (110/115, 0 common-dropped); spot-checks pass (`ימיש`→Exod 13:22 via lemma מוש, `חסד אמת`→Exod 34:6). Also validated **end-to-end on a full Ps 59 run** ($6.81): intertexts landed in the final prose (`שחק`+`לעג`→Ps 2:4 laughter; `שגב`→מִשְׂגָּב fortress→2 Sam 22:3; `נוע`→"wander"). Follow-ups (done in Session 352): macro→opus-4-8 (adaptive/high); dedupe augmented roots by resolved lemma.
**Session 350 (2026-06-02)**: Concordance Value-Add — Distinctive-Root Searches
- Diagnosed that concordance searches were lifting verbatim multi-word phrases from each verse; across Ps 54–58, **62% returned only the source verse (self-match), 14% nothing, only 24% any external parallel** (3-word queries: 0/12). Root cause: the agent was forbidden from searching single distinctive roots, and the override clobbered any root query into the verse phrase.
- Shipped **A** (trace distinctive single roots — prompt rewrite in `micro_analyst.py`, fixed `_override_llm_base_forms` to leave ≤2-word queries intact, new deterministic `_augment_with_root_searches` + `src/concordance/root_selection.py`), **B** (collocations capped at 2 words), **C** (self-match filtering + honest "external"/"appears only in this psalm" counts in `concordance_librarian.py`/`research_assembler.py`, post-search common-word guard `COMMON_CAP=60`). Also: random (seeded) canon-spread sampling of displayed matches; Hebrew-only result lines (dropped English gloss, ~47% token saving); no verse-form expansion of collocations. Measured yield **24% → ~90%** external (e.g. Ps 56: 0/10 → 21/23), surfacing non-obvious intertexts (`פלג`→Babel Gen 10-11, `נוד`→Cain Gen 4, `מוש`→Exod 13:22 pillar, `חסד אמת`→Exod 34:6).
- **D & E were the next session** (design in `docs/architecture/LEMMA_ROOT_SEARCH_PROPOSAL.md`; shipped in Session 351): wire the already-built but unused ETCBC/BHSA lemma data into a `lemma`/`root` column on the `concordance` table for true morphology-aware root + 2-word search. Eval/trace harnesses: `scripts/EXPERIMENT_concordance_eval.py`, `scripts/EXPERIMENT_concordance_trace.py`.
**Session 349 (2026-05-30)**: Remove JSON Dependencies from Pipeline
- Removed `psalm_function_for_RAG.json` and `ugaritic.json` data loading from `RAGManager` as they are now superseded by deep research.
- Removed Ugaritic metrics from DOCX methodological summaries in `document_generator.py` and `combined_document_generator.py`.
- Cleaned up documentation references in `CONTEXT.md` and `DEVELOPER_GUIDE.md`.
**Session 348 (2026-05-29)**: Switch Default Master Writer to Opus 4.8
- Conducted reversible experiment on Psalm 57 to compare Opus 4.8 vs 4.7 with high effort configuration.
- Permanently updated `master_editor.py`, `synthesis_discovery.py`, and runner scripts to use `claude-opus-4-8` as default.
- Added Opus 4.8 pricing to `cost_tracker.py` and updated architecture documentation.

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
