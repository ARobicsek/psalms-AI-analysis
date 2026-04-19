# Next Session Brief — Fix Pipeline Cost Accounting

**Created**: Session 326 (2026-04-18)
**Target session**: 327
**Estimated effort**: 1–2 hours of focused implementation
**Recommended model**: **Claude Sonnet 4.6** — this is mechanical plumbing work with clear patterns already present in the codebase. Opus is overkill.

---

## Why this work matters

The cost summary printed at the end of `run_enhanced_pipeline.py` and `run_si_pipeline.py` is **silently under-reporting costs**. Multiple LLM call sites either:
- Extract reasoning/thinking tokens but fail to pass them to `cost_tracker.add_usage()` (under-billing), OR
- Never call `cost_tracker.add_usage()` at all (entire cost missing from summary), OR
- Compute their own local cost without reporting to the shared tracker.

Additionally, the cost summary is only `print()`-ed to stdout — never persisted to JSON — so after-the-fact cost comparisons between runs are impossible.

---

## What's NOT broken (do not touch)

**All Claude API call sites are correct for billing.** Anthropic's `usage.output_tokens` already includes thinking tokens (billed at output rate) — confirmed via their [extended thinking docs](https://platform.claude.com/docs/en/build-with-claude/extended-thinking). The common pattern `thinking_tokens=getattr(usage, 'thinking_tokens', 0)` returns 0 (since that attribute doesn't exist on Anthropic's usage object), but billing stays accurate because thinking is folded into `output_tokens`.

Do NOT add thinking-token populations to Claude calls. That would **double-bill** the thinking cost.

Agents already correct for billing (verified):
- `src/agents/macro_analyst.py` (both GPT and Claude paths)
- `src/agents/micro_analyst.py` (Claude path — billing correct)
- `src/agents/question_curator.py` (both paths)
- `src/agents/insight_extractor.py` (both paths)
- `src/agents/liturgical_librarian.py` (GPT path correct; Claude fallback billing correct)
- `src/agents/synthesis_writer.py` (correct for Claude + Gemini)
- Master Writer (`src/agents/archive/master_editor_v2.py` `_call_claude_writer`) — Claude billing correct; `thinking_tokens=0` is intentional and fine

---

## Punch list — fixes to implement

### Fix 1: `copy_editor.py` GPT path — missing `thinking_tokens`

**File**: `src/agents/copy_editor.py`
**Line**: 691

**Current code (buggy):**
```python
self.cost_tracker.add_usage(self.model, input_tokens=input_tokens, output_tokens=output_tokens)
```

**Problem**: When `self.openai_client` is used (GPT path), line 628 extracts `response.usage.reasoning_tokens` but only stores it in a human-readable `thinking_text` string. The actual reasoning token count is never passed to the tracker. For Claude path, billing is already correct — but we need to not regress it.

**Fix**: Capture `reasoning_tokens` numerically in the GPT branch and pass them.

**Implementation**:
- Add to the GPT branch (around line 628–634): extract `reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0) or 0` and store `usage_data['thinking_tokens'] = reasoning_tokens`.
- For Claude branch: leave `thinking_tokens=0` (already correct, billing included in output_tokens).
- Update line 691 to pass `thinking_tokens=usage_data.get('thinking_tokens', 0)`.

**Verification**: After fix, run a copy editor step on any psalm with GPT-5.x; confirm cost summary now shows "Thinking Tokens" line for the model.

---

### Fix 2: `figurative_curator.py` — never logs to cost_tracker

**File**: `src/agents/figurative_curator.py` (and `src/agents/research_assembler.py` to plumb the tracker through)

**Problem**: `FigurativeCurator.__init__` does not accept a `cost_tracker`. It computes cost locally (lines 198–208) but never reports to the shared pipeline tracker. All GPT-5.4 cost (including reasoning tokens, which for GPT-5.4 with `reasoning_effort="high"` can be substantial) is missing from the pipeline summary.

**Fix**:
1. In `FigurativeCurator.__init__` (line ~130-ish): add `cost_tracker: Optional[CostTracker] = None` parameter. Store as `self.cost_tracker`.
2. In `_call_llm` after the cost calculation (around line 208): if `self.cost_tracker` is not None, call:
   ```python
   self.cost_tracker.add_usage(
       model="gpt-5.4",
       input_tokens=token_usage["input"],
       output_tokens=token_usage["output"],
       thinking_tokens=token_usage["thinking"],
   )
   ```
3. In `src/agents/research_assembler.py` line ~720: change `FigurativeCurator(verbose=False)` to `FigurativeCurator(verbose=False, cost_tracker=self.cost_tracker)`. (Confirm `ResearchAssembler` already holds `self.cost_tracker` — verified it accepts it at line 691.)
4. No changes needed in the pipeline scripts — they already pass `cost_tracker` to `ResearchAssembler`.

**Verification**: Run enhanced pipeline on any psalm; cost summary should now include a `gpt-5.4` section.

---

### Fix 3: `scripture_verifier.py` — three silent cost sites

**File**: `src/utils/scripture_verifier.py`

These are module-level functions (not methods), so they need a `cost_tracker` parameter plumbed from the pipeline:

**Sites**:
- `_filter_via_gpt` (line ~1406): GPT-5.1 with `reasoning={"effort": "medium"}`. Extracts input/output/reasoning tokens at 1446–1451, computes cost at 1453–1455, but never logs.
- `_filter_via_haiku` (line ~1306–1403): Claude Haiku 4.5. Extracts input/output at 1391–1394, computes cost at 1394. Anthropic's output_tokens includes thinking, so we just need input + output (thinking_tokens=0).
- `verify_citations_tooluse` (line ~1674): Haiku tool-use loop. Complex — multiple API calls in a loop. Accumulates tokens locally but never logs.

**Fix strategy**:
1. Add optional `cost_tracker: Optional[Any] = None` parameter to these three functions (and to the public `filter_false_positives` wrapper that dispatches to them).
2. Inside each, after the API call, if `cost_tracker` is provided, call `cost_tracker.add_usage(...)` with the appropriate model name:
   - GPT path: `model="gpt-5.1"`, include `thinking_tokens=reasoning_tokens`
   - Haiku path: `model="claude-haiku-4-5-20251001"`, `thinking_tokens=0`
   - Tool-use path: accumulate across all loop iterations, log once per iteration or aggregated at the end
3. In the pipeline callers:
   - `scripts/run_enhanced_pipeline.py` line 793: `filter_false_positives(citation_issues, commentary_text=verify_text, model=filter_model, cost_tracker=cost_tracker)`
   - `scripts/run_enhanced_pipeline.py` line 807: `verify_citations_tooluse(..., cost_tracker=cost_tracker)`
   - `scripts/run_si_pipeline.py`: matching change (grep for same function calls)

**Verification**: Run enhanced pipeline with default flags; cost summary should now include `gpt-5.1` (citation filter) section. Run with `--tooluse-verify` flag; confirm Haiku usage appears.

---

### Fix 4: Persist cost summary to JSON

**Files**: `scripts/run_enhanced_pipeline.py` (line ~944), `scripts/run_si_pipeline.py` (line ~928)

**Current**: `print(cost_tracker.get_summary())` — stdout only.

**Fix**: Before the `print(...)`, also write the structured data to disk:

```python
import json
cost_file = output_path / f"psalm_{psalm_number:03d}_cost.json"
cost_file.write_text(
    json.dumps(cost_tracker.to_dict(), indent=2, ensure_ascii=False),
    encoding='utf-8'
)
logger.info(f"Cost data saved to {cost_file.name}")
```

**Note**: `output_path` is already defined earlier in each script (look for `output_path = Path(...)`). `cost_tracker.to_dict()` already exists in `src/utils/cost_tracker.py:321` — no changes needed there.

**Verification**: Run pipeline on any psalm; confirm `output/psalm_{N}/psalm_{N}_cost.json` is created and contains input/output/thinking breakdowns per model.

---

### Fix 5 (optional but recommended): Claude thinking visibility in Master Writer

**File**: `src/agents/archive/master_editor_v2.py` `_call_claude_writer` (lines ~2121–2167)

**Not a billing bug** — purely for observability. The Master Writer was set to max effort in Session 325, so thinking will be substantial. Currently we have no visibility into how much of output_tokens was thinking.

**Pattern to copy**: `src/agents/copy_editor.py:647–686` already does this — it iterates the stream looking for `thinking_delta` events and accumulates `thinking_text`, then logs `len(thinking_text) // 4` as an estimated token count.

**Fix**: Switch `messages.stream(**stream_kwargs)` to iterate events manually (like copy_editor does), capture thinking chars, and add an INFO log line after completion: `"Master Writer used ~{N} thinking tokens (included in the {output_tokens} output total)"`.

**Do NOT** pass this as `thinking_tokens=...` to `add_usage()` — that would double-bill.

---

## Implementation sequence (recommended)

1. **Fix 4 first** (cost persistence) — tiny change, immediately gives you before/after comparison data for subsequent fixes.
2. **Fix 1** (copy_editor GPT path) — single-file change, easy to verify.
3. **Fix 2** (figurative_curator) — requires two-file plumbing but well-scoped.
4. **Fix 3** (scripture_verifier) — largest change; do last because it touches both pipelines.
5. **Fix 5** (optional Master Writer visibility) — only if you have time and want the observability.

After each fix, run a quick test:
```bash
python scripts/run_enhanced_pipeline.py 1 --resume
```
(Psalm 1 is small; `--resume` skips completed steps. Just ensures the pipeline still boots.)

---

## Files expected to be modified

- `src/agents/copy_editor.py` (Fix 1)
- `src/agents/figurative_curator.py` (Fix 2)
- `src/agents/research_assembler.py` (Fix 2 plumbing)
- `src/utils/scripture_verifier.py` (Fix 3)
- `scripts/run_enhanced_pipeline.py` (Fix 3 plumbing + Fix 4)
- `scripts/run_si_pipeline.py` (Fix 3 plumbing + Fix 4)
- `src/agents/archive/master_editor_v2.py` (Fix 5, optional)

Commit as **Session 327** with message: `Session 327: Fix pipeline cost accounting for GPT/Gemini thinking tokens`.

---

## How I found this (context for continuity)

Session 325: Set Master Writer max effort on Opus 4.7. User asked to compare Psalm 50 cost old-vs-new, which revealed the pipeline only logs char-based token estimates, not actual API counts.

Session 326 (this session): Audit of every LLM call site reachable from `run_enhanced_pipeline.py` and `run_si_pipeline.py`. Web-verified that Claude's `output_tokens` already includes thinking (so Claude call sites billing `thinking_tokens=0` are NOT bugs), but GPT/Gemini expose reasoning tokens separately (so missing `thinking_tokens` params ARE billing bugs). Full audit notes in the IMPLEMENTATION_LOG Session 326 entry.
