# Next Session Brief — Session 338: Build `lit_echoes` Agent

**Date written**: 2026-04-22 (end of Session 337)

## Context

Session 337 designed and tested a tier-override prompt system for literary echoes generation. Testing on Psalms 48, 49, 50, 52 showed dramatic within-psalm variety and aptness improvements — but surfaced a **cross-psalm repetition pattern at the second tier** (Faiz, Kabir, Saadi, Vallejo, Ibn Ezra, Douglass, Dorsey each appearing in ~2 of 3 consecutive psalm runs). Prompt-craft alone cannot solve this: the model has no memory of what it used in yesterday's psalm.

Rather than keep the manual Gemini-web workflow with a script that generates per-psalm prompts, the user (end of Session 337) chose to **incorporate the entire 4-pass literary echoes workflow into the main pipeline as a `lit_echoes` agent** using Gemini 3.1 Pro API, with a rolling N=4 exclusion list automatically built from recent psalms.

## Goal for Session 338

Build `src/agents/literary_echoes_agent.py`. Integrate into `scripts/run_enhanced_pipeline.py`. Test on at least two consecutive psalms (so the exclusion list exercises both the empty-state and populated-state paths).

## Inputs the agent needs

- Psalm number
- Full psalm text (Hebrew + English) — available from existing upstream pipeline steps
- Last 4 psalms' finalized literary echoes output files — scan `data/literary_echoes/psalm_*_literary_echoes.txt` (or wherever the finals land — confirm at session start)

## The 4-pass flow to automate

Prompt templates live in `docs/prompts_reference/`:

| Pass | Template | Purpose |
|---|---|---|
| 1 | `literary echoes pass 1 - tier override.txt` | Generation: 12-18 comparisons, `*Default bypassed:*` lines, tier palette, Earned Canonical Slot cap = 2 combined |
| 2 | `literary echoes pass 2 - tier override.txt` | Gap-fill: 3-6 more comparisons, opens with quota audit |
| 3 | `literary echoes pass 3.txt` | Verification (unchanged — pure audit, no tier-override customization) |
| 4 | `literary echoes pass 4 - tier override.txt` | Final reconstruction: strips `*Default bypassed:*` lines and Pass 2 audit block, applies Pass 3 corrections |

Per-psalm execution:

1. **Build exclusion list** — scan last 4 psalms' outputs, extract authors from `#### [Name],` lines (regex anchored to start of line), dedupe case-insensitively.
2. **Pass 1** — substitute `{NUMBER}`, inject exclusion list block, call Gemini. Save raw output.
3. **Pass 2** — send Gemini the Pass 1 output + Pass 2 prompt. Pass 2 inherits context from the attached Pass 1 document; no exclusion-list re-injection needed. Save raw output.
4. **Pass 3** — send Gemini the combined Pass 1+2 document + Pass 3 prompt. Save verification notes.
5. **Pass 4** — send Gemini all prior artifacts + Pass 4 prompt. Save final reconstruction.

## Logging requirements (user-specified)

Save each pass's raw output separately so debugging is easy. Suggested layout:

```
output/psalm_NNN/literary_echoes/
  pass_1_raw.txt
  pass_2_raw.txt
  pass_3_verification.txt
  pass_4_final.txt
  exclusion_list.txt      # authors injected this run
  gemini_prompts/
    pass_1_full.txt       # exact prompt sent (with {NUMBER} and exclusion resolved)
    pass_2_full.txt
    pass_3_full.txt
    pass_4_full.txt
```

Copy `pass_4_final.txt` to `data/literary_echoes/psalm_NNN_literary_echoes.txt` (the canonical location the next psalm's exclusion-list scan will read).

## Exclusion list injection format

Hard constraint, not soft — treat like the existing Homer/Dante/Virgil/Ovid ban. Inject into Pass 1 template immediately above `=== THE SECOND ECHO PRINCIPLE ===`:

```
=== AUTHORS USED IN LAST 4 PSALMS (DO NOT REUSE) ===

The following authors appeared in the most recent psalms in this series. None of them may appear in this document — find fresher second-tier sources.

[comma-separated list of ~40-80 authors]
```

## Design decisions to confirm at session start

1. **Gemini SDK**: `google-genai` (newer) vs `google-generativeai`. Check what existing agents use (likely there's an established pattern — maybe `figurative_curator.py` or wherever Gemini 2.5 fallback is wired).
2. **Model ID**: exact string for "Gemini 3.1 Pro" — confirm from wherever deep research integration currently calls it.
3. **Cost tracking**: hook into existing `CostTracker` — follow the pattern from an existing agent that already logs costs.
4. **Pipeline integration point**: where does `lit_echoes` run? Likely parallel with / after deep research, before Master Writer consumes the research bundle. User to confirm whether Master Writer actually uses literary echoes content, or whether it's a DOCX-only decoration.
5. **Failure behavior**: if Gemini errors (rate limit, safety refusal, timeout), should the pipeline skip + continue, retry with backoff, or halt? Suggest skip + log warning so a single psalm's echoes failure doesn't block the whole run.
6. **Streaming vs single-shot**: the four passes are strictly sequential (each needs prior output). No parallelization possible within one psalm. Across psalms, the pipeline is already per-psalm so no change there.

## Testing plan

1. Build agent, integrate into pipeline (new optional step or mandatory — user's call).
2. Run on a psalm whose literary_echoes file doesn't exist yet (e.g., Psalm 53) — exercises the empty-exclusion path.
3. Verify all per-pass logs land in expected locations.
4. Run on a psalm AFTER Psalm 53 to verify exclusion scan correctly picks up Psalm 53's authors.
5. Inspect Pass 4 final output for compliance:
   - Hebrew quota (≥1 medieval + ≥1 modern) met
   - Earned Canonical Slot count ≤ 2 combined across Pass 1 + Pass 2 contribution
   - All `*Default bypassed:*` lines stripped
   - Pass 2 audit block stripped
   - Zero Homer/Dante/Virgil/Ovid
   - ≥2 non-Anglo-European-Hebrew sources
   - ≥5 post-1850, ≥3 post-1950
6. Spot-check a random handful of quotations for factual accuracy (Pass 3 should catch most but worth human eye).

## Session 337 artifacts to reference

- `docs/prompts_reference/literary echoes pass 1 - tier override.txt` — Pass 1 template (final)
- `docs/prompts_reference/literary echoes pass 2 - tier override.txt` — Pass 2 template (final)
- `docs/prompts_reference/literary echoes pass 4 - tier override.txt` — Pass 4 template (final)
- `docs/prompts_reference/literary echoes pass 3.txt` — Pass 3 unchanged (verification is style-agnostic)

Session 337 did no code work — all outputs were prompt templates and design. Agent implementation starts fresh in Session 338.
