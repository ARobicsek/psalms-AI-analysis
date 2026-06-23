# Dossier Prompt-Cache + Keepalive Plan (SHELVED)

**Created**: Session 359 (2026-06-23)
**Status**: 🟡 **SHELVED — analyzed, designed, validated-on-paper, NOT implemented.** Shelved by user decision over two concerns (see "Why shelved"). This doc has everything needed to pick it up later without re-deriving anything.
**Theme**: Cost reduction — "A1" from the Session-359 cost-reduction menu.
**Touches**: `src/agents/master_editor.py`, `src/agents/synthesis_discovery.py` only.
**Estimated net savings**: ~**$0.30–0.45/psalm** (~5–7% of the ~$6/psalm total), no other quality cost *except* the writer-reorder risk below.

---

## The goal (what "A1" was)

The Synthesis Discovery sidecar and the Master Writer are two back-to-back **Opus** calls that each separately ingest the **same ~130–180k-token research dossier** (psalm text + macro + micro + research bundle + phonetics + analytical framework). Today we pay full Opus input price for that dossier **twice**, and **prompt caching is completely unused** (every `psalm_*_cost.json` shows `cache_read_tokens: 0` / `cache_write_tokens: 0`).

Idea: cache the shared dossier on the first call (Synthesis) and read it cheaply on the second (Writer). Anthropic cache read = 0.1× input; cache write = 1.25× input.

---

## The blocker that kills the naive version

Anthropic prompt caching is **prefix-based** with a **5-minute (300s) default TTL** (only other option: 1-hour). The cache is **written at the *start*** of the Synthesis call (when it processes the prefix) and would be **read when the Writer call begins** — and the Writer only starts *after* Synthesis fully completes. So the write→read gap ≈ **the entire Synthesis Discovery duration.**

Measured Synthesis Discovery durations (from `logs/`, `master_editor_v2` logger, `[SYNTHESIS-DISCOVERY psalm N] done in Ns`):

| Psalm | Duration(s) | Input tokens |
|------|-------------|--------------|
| 58 | 254 / 466 | ~162k |
| 59 | 226 / 287 | ~180k |
| 60 | 297 / 346 | ~203k |
| 61 | 330 | 127k |
| 62 | 303 | 145k |
| 63 | 326 | 144k |
| 64 | 310 | 137k |

The recent runs (61–64, current v2 synthesis prompt, `effort=high`, ~16–20k output tokens) are **consistently 303–330s — just over the 300s TTL.** So with the naive approach the cache **expires before the Writer reads it** → the Writer re-pays full price → and we've wasted the 0.25× write premium on Synthesis.

Naive-version expected value with current timings ≈ **break-even to −$0.16/psalm.** The 1-hour TTL doesn't help either (write premium 2.0× ⇒ ~−$0.07/psalm for a single downstream read). **Do not ship the naive version.**

---

## The fix: keepalive ping during Synthesis (this is the plan)

**Key fact: a cache *read* refreshes the TTL.** Each hit resets the 5-minute clock. So fire a cheap "keepalive" read of the dossier prefix *while Synthesis is still running*, and the cache stays alive until the Writer is ready.

Three calls share **one byte-identical cached dossier block** (content block 1, with `cache_control: {"type": "ephemeral"}`); they differ only in the instructions that follow it:

1. **Synthesis Discovery** (T0): processes dossier → **writes** cache (1.25×). Runs ~310s.
2. **Keepalive ping(s)** on a background thread: re-send the same dossier prefix + a trivial `"reply: ok"` with `max_tokens=1`. This is a **cache read** (0.1×, ~$0.07) that **resets the TTL**. Fire ~every 250s, **starting ~120s in** (after Synthesis has surely written the cache — see race note).
3. **Master Writer** (T0+~315s): reads the still-alive cache (0.1×) on the dossier; pays full price only on its own rules/insights/observations tail.

### Economics (dossier S ≈ 130–180k tokens; Opus input $5/M, write $6.25/M, read $0.50/M)

- No cache: `2·S·$5/M` ≈ **$1.30/psalm** on the duplicated dossier.
- Keepalive: synthesis write (`1.25·S·$5/M` ≈ $0.81) + 1–2 pings (`0.1·S·$5/M` ≈ $0.07 each) + writer read (`0.1·S·$5/M` ≈ $0.07) ≈ **$0.95–1.01**.
- **Net savings ≈ $0.30–0.45/psalm**, and it now hits reliably whether Synthesis runs 250s or 466s.
  - General formula for net savings on the shared block: `(0.65 − 0.1·k_pings) · S · $5/M`, where `k_pings` is the number of keepalive reads (typically 1–2).

### Two things to get right

1. **Double-write race.** If a ping fires *before* Synthesis finishes writing the cache, the ping itself pays the write premium (wasteful). Mitigation: first ping no earlier than **~120s** in (Synthesis processes its ~130k prefix in well under a minute); space pings ~250s apart. All observed durations (226–466s) are covered by 1–2 pings.
2. **Writer prompt reorder (the residual quality risk).** Prefix caching *requires* the dossier to be the **leading** block, so the Master Writer prompt must move its `### YOUR INPUTS` dossier from the middle to the front, RULES/TASK/CHECKLIST following. Information is identical and "context-first, instructions-last" is generally robust (arguably *better*) for Opus — but this is the most heavily-tuned prompt in the project, so output is **not** guaranteed byte-identical.

---

## Why shelved (user concerns, Session 359)

1. **Writer-reorder risk.** Reordering the crown-jewel `MASTER_WRITER_PROMPT_V4` to put the dossier first is a non-zero risk to the carefully-tuned voice. Acceptable only behind a one-psalm A/B validation gate (below), and the user preferred not to take it on now.
2. **Model-swap fragility (the bigger long-term concern).** This optimization is **coupled to both Opus calls running on the same Anthropic model**:
   - Anthropic prompt caching is **provider-specific**. If the Writer ever moves to a non-Claude model (e.g. **GPT-5.6**), there is **no shared Anthropic cache** between Synthesis (which falls back to `claude-opus-4-8`, see `run_enhanced_pipeline.py` `sd_model` logic) and the Writer — the entire mechanism is moot, and the writer-reorder would be dead weight.
   - Even swapping to a *different Claude* model: the cache is **model-specific**, so Synthesis and Writer must be pinned to the **same** Claude model for the prefix to be shared; any divergence silently disables the cache.
   - Net: the win is real today (both on `claude-opus-4-8`) but brittle against the model-routing flexibility the pipeline otherwise preserves (`--gpt-5-4-writer`, `--master-editor-model`, future GPT writers).

**Implication if revived:** gate the whole thing behind a runtime check — only enable caching + the keepalive when **Synthesis model == Writer model AND both are Anthropic Claude**; otherwise fall back to the current (un-reordered, un-cached) path. Consider keeping the dossier-first prompt structure behind a flag so a non-Claude writer can use the original ordering.

---

## Implementation shape (when revived)

1. **Shared serializer.** Extract `build_dossier_block(psalm_text, macro_text, micro_text, research_bundle, phonetic_section, analytical_framework) -> str` used by Synthesis, keepalive, and Writer, so the cached prefix is provably byte-identical. The components are *already* built by identical methods with the same 350k-char research trim in both paths (`discover_cross_verse_observations` and V2 `write_commentary`), so this is mostly a refactor, not new logic.
2. **Two-block messages.** Convert the three calls to `content=[{type:text, text: dossier_block, cache_control:{type:"ephemeral"}}, {type:text, text: <task-specific tail>}]`.
   - Synthesis tail = the `INPUTS_HEADER` preamble (reworded "below"→"above") + `SYNTHESIS_TASK`.
   - Writer tail = `MASTER_WRITER_PROMPT_V4` with the dossier placeholders removed (now reference "the dossier above") + writer-specific inputs (curated insights, reader questions, cross-verse observations) + task/output/checklist, all verbatim.
   - Keepalive tail = `"Reply with the single word: ok"`, `max_tokens=1`.
3. **`CacheKeepalive` helper.** Background thread: `start()` before the Synthesis call, `stop()` after it returns. Loop sleeps to first-ping delay (~120s), then pings every ~250s; pings are best-effort (swallow exceptions, log at warning). Create its own `anthropic.Anthropic` client instance to avoid cross-thread client concerns.
4. **Guard rails.** Disable the whole path (and skip the reorder) unless `sd_model == writer_model and "claude" in writer_model` (see "model-swap fragility").

### Validation gate (must pass before merging to `main`)

Run a recent psalm (e.g. **Ps 64**, since current output exists to diff against) both ways on a branch/worktree:
- (a) Confirm `cache_read_tokens > 0` on the Writer call and the per-psalm cost drops ~$0.30–0.45.
- (b) Confirm the keepalive fired as a **read** (cheap), not a second write (watch `cache_write_tokens`).
- (c) Eyeball/diff the Writer prose for parity with the pre-change Ps 64 output (the reorder must not degrade voice/coverage).
Roll out only if all three hold.

---

## Context snapshot (so this doc stands alone)

Per-psalm cost ~**$6** (Pss 62/63/64 = $5.83 / $6.41 / $5.67). Model-level average:

| Model | $/psalm | Role |
|------|---------|------|
| Opus 4.8 | ~$2.61 | Macro + **Synthesis Discovery** + **Master Writer** (the two duplicated-dossier calls) |
| GPT-5.4 | ~$2.16 | Literary Echoes passes 3 & 4 + Copy Editor |
| Sonnet 4.6 | ~$0.64 | Micro Analyst |
| Gemini 3.1 Pro | ~$0.41 | Literary Echoes passes 1 & 2 |
| GPT-5.1 | ~$0.16 | Citation false-positive filter |

Other menu items from the same Session-359 review (not pursued here): **A2** citation filter → Haiku (~$0.05–0.15, near-zero risk); **B1** make the no-op `ResearchTrimmer` bind / selective commentary; **B2** Copy Editor GPT-5.4→5.1; **C1** Synthesis Discovery skip/downsize (~$1.0–1.3, real quality tradeoff). The `ResearchTrimmer` is currently a **no-op** (400k-char cap never triggers on ~215k bundles → `research_v2.md` == `research_trimmed.md`).
