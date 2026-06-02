# Next Session Brief — Macro → Opus 4.8 (adaptive/high) + lemma-dedup

**Written:** end of Session 351 (2026-06-02). Both tasks came out of Session 351's Ps 59
end-to-end validation run + a cost analysis of the macro/micro agents.
(Per user, the micro agent **stays on claude-sonnet-4-6** — the earlier gpt-5.4 idea is dropped.)

## Prior session (351) — DONE, for context
D & E lemma-aware concordance shipped: a **`lemma`** column on `concordance` (96.3%
coverage, from ETCBC/BHSA `lex_utf8` via greedy concat-alignment), root traces + ≤2-word
collocations now match on an exact indexed `WHERE lemma = ?`. Eval yield **24%→96%**.
Full detail: `IMPLEMENTATION_LOG.md` (Session 351); `LEMMA_ROOT_SEARCH_PROPOSAL.md` STATUS
banner. DB backup: `database/tanakh.db.pre_lemma_bak`.

---

## Task 1 — Macro agent: `claude-opus-4-6` → `claude-opus-4-8` (adaptive, effort=HIGH)

**Cost:** budget-neutral. All Opus tiers (4-5/4-6/4-7/4-8) are priced identically ($5/$25 per
1M in/out); macro avg ≈ 4.7K in / 13.4K out ⇒ **~$0.36/psalm before and after** (Session-351
analysis of Ps 54–58 `psalm_0NN_cost.json`). Only variable: if 4.8 emits a longer macro JSON
(~$0.025 per +1K out). **Micro stays claude-sonnet-4-6 (no change).**

**Params — match the Master Writer exactly = adaptive + effort `"high"` (NOT max).** Confirmed:
`MasterEditorV2._call_claude_writer` runs Opus 4.8 with `thinking={"type":"adaptive"}` and
`output_config={"effort":"high"}` — gated by model: opus-4-7 → `"max"`, **opus-4-8 → `"high"`**
(`src/agents/archive/master_editor_v2.py:2243-2249`). The macro **currently** runs adaptive +
effort **`"max"`** (`src/agents/macro_analyst.py:344-348`), so this is **two changes**, not just a
model-ID swap: the model ID **and** dropping effort `max → high` for 4.8.

**Change spots:**
- **Model default** → `claude-opus-4-8`: `MacroAnalyst.DEFAULT_MODEL` (`src/agents/macro_analyst.py:199`).
- **Effort** `max → high`: the `output_config={"effort":"max"}` in the macro streaming call
  (`macro_analyst.py:347-348`). Best to mirror the Master Writer's **model-gated** pattern so it's
  robust to the model arg: opus-4-8 → `"high"`, and note opus-4-6 historically did **not** accept
  `output_config` at all, so gate the param by model rather than passing it unconditionally (the
  current code passes it always — fine for 4-6 today only because the API tolerates it).
- **Pipeline defaults**: `macro_model="claude-opus-4-6"` at `scripts/run_enhanced_pipeline.py:301`
  and the `macro_mdl = ... else "claude-opus-4-6"` fallback (~line 1157); `scripts/run_si_pipeline.py:301`.

Low risk (same family, *lighter* effort than today). A 1-psalm sanity run is cheap but no formal
quality gate is needed.

---

## Task 2 — Dedupe augmented root traces by RESOLVED LEMMA

**Problem (observed in the Session-351 Ps 59 run):** `_augment_with_root_searches`
(`src/agents/micro_analyst.py` ~line 1283) dedups added distinctive-root queries against
existing ones **by consonantal string** (`existing = {to_consonantal(req.query) for ...}`).
After the Session-351 lemma work, multiple *different surface strings resolve to the same
lemma*, so the same lemma gets traced in several separate bundles → the concordance section
repeats identical verse-lists under different headers (token noise for the writer/synthesis).
Seen on Ps 59:
- lemma **משגב** traced 3×: via `שגב` (which folds in sibling lemma משגב) + standalone `משגב` + `משגבי`
- lemma **נוע** traced 2×: via `נוע` + `ינועו`

**Fix:** dedupe on the **resolved lemma**, not the surface string.
- Resolve each candidate root's lemma with `self.research_assembler.concordance_librarian.search._resolve_lemma(...)`.
- Build the `existing` / `seen_roots` sets from resolved **lemmas** (note: a query can fold in
  multiple sibling lemmas — see the librarian's single-word path — so dedupe against the full set).
- Also dedupe the LLM's own primary picks against the augmented roots by lemma (a primary pick
  and an augmented root can collide on lemma, as `שגב`/`משגב` did).
- Keep the naive consonantal fallback for queries whose lemma doesn't resolve.

**Acceptance:** re-run `python scripts/EXPERIMENT_concordance_trace.py 59` (or `_eval.py`) and
confirm no two bundles trace the same lemma; the concordance section / bundle char-count shrinks;
external-match yield is unchanged. Inspect `output/psalm_59/` from the Session-351 run for the
before-state.

**Files:** `src/agents/micro_analyst.py` (`_augment_with_root_searches`), plus the search/librarian
helpers from Session 351 (`src/concordance/search.py` `_resolve_lemma`).
