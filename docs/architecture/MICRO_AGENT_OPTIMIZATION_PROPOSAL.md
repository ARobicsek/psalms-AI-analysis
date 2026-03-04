# Micro Agent Optimization Proposal

**Session 284 (2026-03-04) — Cost Investigation & Redesign Options**

---

## The Problem

Running Psalm 22 through the pipeline cost >$6 total, with Sonnet 4.6 alone accounting for $3+. Investigation revealed this was caused by **3 retries** of Stage 1 (Discovery Pass), where the JSON output was truncated each time because the 70% thinking / 30% text budget split didn't leave enough room for the ~25K tokens of text output the model needed.

Each failed attempt still costs full price. Two-thirds of the Sonnet 4.6 bill was wasted.

---

## Current Micro Agent Architecture

### Two-Stage Process (both Sonnet 4.6)

**Stage 1: Discovery Pass** — `max_tokens=65,536`
- Input: macro analysis + psalm text (Hebrew/English/LXX) + RAG context
- Thinking: budgeted at 70% (~45,875 tokens) for psalms >25 verses
- Output: ~76-85K chars of JSON per verse (observations, lexical_insights with phrase/variants/notes, figurative_analysis, thesis_connection, poetic_features, lxx_insights, puzzles)

**Stage 2: Research Request Generation** — `max_tokens=16,384`
- Input: entire Stage 1 output (~76-85K chars)
- Output: structured research requests (lexicon words, concordance queries, figurative searches, commentary requests)

### What Consumes the Micro Output

| Consumer | What it receives | Status |
|----------|-----------------|--------|
| **Stage 2** (Research Requests) | Full discoveries JSON | Active — drives research assembly |
| **Insight Extractor** | Full `to_markdown()` | **SKIPPED by default** (since Session 280) |
| **Question Curator** | `interesting_questions` only | **SKIPPED by default** (since Session 280) |
| **Master Writer** | `commentary` truncated to 500 chars + `interesting_questions` + `phonetic_transcription` (separate section) | Active |

### Key Finding: Dead Fields

With Insight Extractor and Question Curator skipped by default, the consumers that actually use the micro output are:

1. **Stage 2** — needs `lexical_insights` (phrase + variants) and `figurative_analysis` to generate research requests. Also uses `observations` for context.
2. **Master Writer** — needs `commentary` (but truncates to 500 chars!), `interesting_questions`, and `phonetic_transcription`.

Fields that are **generated but unused** in the default pipeline:
- `thesis_connection` / `macro_relation` — not used by Stage 2, not sent to Writer
- `poetic_features` — not used downstream
- `lxx_insights` — not used downstream
- `puzzles` — not used downstream
- Full-length `commentary` beyond 500 chars — truncated by Writer
- `thematic_threads` / `overall_patterns` — not used by Writer
- `synthesis_notes` / `research_priorities` — not used downstream

### Additional Bug Found

`_get_psalm_text()` in `master_editor_v2.py` (line 2254) and the Insight Extractor pipeline code (line 557-558) try to read `hebrew_text` and `english_text` from micro JSON — **but those fields don't exist in the VerseCommentary schema**. The result is empty strings. The psalm text section sent to the Writer likely contains only phonetic transcriptions with blank Hebrew/English fields, falling back to the database-sourced text.

### Phonetic Transcription Clarification

The `phonetic_transcription` field is **programmatically generated** by `PhoneticAnalyst.transcribe_verse()` — not by the LLM. It's stored in the micro JSON purely as a data shuttle to get it to the Master Writer and Insight Extractor. The LLM does NOT generate this; it costs zero LLM tokens.

---

## Proposed Optimizations

### Option A: Slim the Discovery Schema (Low risk, high impact)

**Rationale**: The biggest cost driver isn't the model choice — it's the **retries caused by output truncation**. The LLM tries to produce ~85K chars of JSON but only has budget for ~60K chars of text output. Slimming the schema prevents retries.

**Changes**:
1. Remove from the discovery prompt's output schema:
   - `thesis_connection` / `macro_relation` (unused)
   - `poetic_features` (unused)
   - `lxx_insights` (unused)
   - `puzzles` (unused, can be folded into `observations`)
2. Instruct the model to keep `observations` (which becomes `commentary`) to 1-2 sentences max — it gets truncated to 500 chars anyway
3. Keep `lexical_insights` (critical for Stage 2) and `figurative_elements` (critical for Stage 2)
4. Keep `interesting_questions` (used by Writer)
5. Keep `overall_patterns` / `thematic_threads` — useful context even if not directly consumed

**Expected impact**: Output shrinks from ~85K to ~40-50K chars. Fits comfortably in the 30% text budget. **Eliminates retries entirely** — saving 2x the per-call cost for complex psalms.

**Estimated savings**: From ~$3+ (3 retries) to ~$1.10 (single call) for Psalm 22.

### Option B: Merge Stages 1 and 2 into a Single Call (Medium risk, medium impact)

**Rationale**: Stage 2 is a reformatting task — taking discoveries and producing research requests. The model already has all the context it needs during Stage 1.

**Changes**:
1. Add research request generation to the Stage 1 prompt
2. Output schema includes both discoveries AND research requests in one JSON
3. Eliminate Stage 2 entirely

**Expected impact**: Saves the entire Stage 2 API call (~$0.15-0.25 depending on thinking).

**Risk**: Longer/more complex prompt; possible quality reduction if the model tries to do too much at once. The Stage 2 prompt contains detailed instructions about concordance search levels, figurative database format, and BDB request limits that would bloat the Stage 1 prompt.

**Recommendation**: Try Option A first. If the combined output (discoveries + research requests) still fits in budget, consider merging.

### Option C: Use Haiku 4.5 for Stage 2 (Low risk, low-medium impact)

**Rationale**: Stage 2 is a structured extraction/reformatting task. It takes discoveries and produces research requests following a well-defined schema. This doesn't need Sonnet-level reasoning.

**Changes**:
1. Stage 2 uses `claude-haiku-4-5` instead of `claude-sonnet-4-6`
2. Pricing drops from $3/$15/$15 (input/output/thinking) to $1/$5/$5

**Expected impact**: ~60-70% reduction in Stage 2 cost. Small absolute savings (~$0.10-0.15) but zero quality risk.

### Option D: Reduce Thinking Budget for Stage 1 (Low risk, medium impact)

**Rationale**: The 70% thinking budget (45,875 tokens) may be excessive. The discovery task is structured — iterate through verses, note observations. It doesn't require deep chain-of-thought reasoning for every verse.

**Changes**:
1. Reduce thinking budget from 70% to 50% of max_tokens
2. This gives ~32K tokens for thinking, ~32K for text output
3. With slimmed schema (Option A), 32K text tokens is more than enough

**Expected impact**: ~30% reduction in thinking token cost per call. Combined with Option A (no retries), significant savings.

**Risk**: Minimal. The model doesn't need 45K tokens of thinking to observe what's interesting in each verse.

### Option E: Fix the `hebrew_text`/`english_text` Bug (Zero risk, correctness fix)

**Rationale**: The `_get_psalm_text()` method and Insight Extractor pipeline code try to read `hebrew_text` and `english_text` from micro JSON, but those fields don't exist. This means the psalm text section sent to the Master Writer may have empty Hebrew/English lines.

**Changes**:
1. Either add `hebrew_text` and `english_text` to the `VerseCommentary` schema (populated from the database during `_create_micro_analysis`), OR
2. Fix `_get_psalm_text()` to always fall back to database lookup (which it may already do — needs verification)

**Impact**: Correctness improvement. No cost change.

---

## Recommended Implementation Order

1. **Option A** (slim schema) — biggest bang for buck, prevents retries
2. **Option E** (fix bug) — correctness, zero risk
3. **Option D** (reduce thinking to 50%) — pairs well with Option A
4. **Option C** (Haiku for Stage 2) — small but free savings
5. **Option B** (merge stages) — only if A+D still leave room for improvement

Options A + D + C together should reduce micro agent cost from ~$3+ (with retries) to **~$0.60-0.80** (single call, lower thinking, cheap Stage 2) — a **~75-80% reduction**.

---

## Cost Comparison Summary

| Scenario | Stage 1 calls | Stage 1 cost | Stage 2 cost | **Total Micro** |
|----------|--------------|-------------|-------------|----------------|
| **Current** (Ps 22 actual) | 3 (2 retries) | ~$3.00 | ~$0.20 | **~$3.20** |
| **Option A only** (no retries) | 1 | ~$1.00 | ~$0.20 | **~$1.20** |
| **A + D** (slim + 50% thinking) | 1 | ~$0.70 | ~$0.20 | **~$0.90** |
| **A + D + C** (+ Haiku Stage 2) | 1 | ~$0.70 | ~$0.07 | **~$0.77** |
| **A + B + D** (merge stages) | 1 | ~$0.80 | $0.00 | **~$0.80** |
