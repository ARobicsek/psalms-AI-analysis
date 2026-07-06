# Sonnet 5 vs Sonnet 4.6 for the Micro Agent — A/B Findings (SHELVED)

**Session 362 (2026-07-01).** Status: **investigated, tested on Ps 65, NOT adopted.** All code
was reverted; `MicroAnalystV2.DEFAULT_MODEL` remains `claude-sonnet-4-6`. This doc preserves the
data so the decision doesn't have to be re-derived.

## Question
Should the micro agent (`src/agents/micro_analyst.py`, the only Sonnet user in the pipeline —
2 LLM calls/psalm: Stage 1 discovery + Stage 2 research-request generation) move from
Sonnet 4.6 to Sonnet 5, assuming "high or greater" thinking?

## Pricing facts (as of 2026-07-01)
- **Sonnet 4.6**: $3 / $15 per 1M (input/output). Same as Sonnet 4.5.
- **Sonnet 5**: **$3 / $15 standard**, but **intro $2 / $10 through 2026-08-31**. New tokenizer
  (Opus-4.7 family) emits ~30% more tokens for the same text *on average* — but see the empirical
  result below: on this Hebrew/Greek/structured-text workload, **input was essentially flat**, not +30%.

## Two required code changes to run Sonnet 5 at all (the migration)
These are real API breaks, not optional tuning — they're why a naive model-string swap fails:
1. **Stage 1** uses `thinking={"type":"enabled","budget_tokens":N}` (the Session-294 "reserve 50%
   for JSON" safeguard). **Sonnet 5 rejects `budget_tokens` with a 400.** Must switch to
   `thinking={"type":"adaptive"}` + `output_config.effort`, and there is **no way to hard-cap
   thinking** — you control depth only via `effort` and give extra `max_tokens` headroom (used 128K)
   so thinking + JSON both fit.
2. **Stage 2** sends **no** `thinking` config → on 4.6 that means thinking OFF; on **Sonnet 5,
   omitting `thinking` defaults to adaptive ON** (a silent output-token cost). Must set
   `thinking={"type":"disabled"}` explicitly to preserve 4.6 behavior.
- `effort` levels are `low/medium/high/xhigh/max` — **coarse**: there is no level between `xhigh`
  and `max`, which is the whole problem (see below).

## The A/B (Ps 65, macro reused, `commentary_mode="all"`, Stages 1–2 only)
Baseline = the Sonnet 4.6 last production run (`output/psalm_65/psalm_065_cost.json`,
`claude-sonnet-4-6` entry: 2 calls, 27,888 in / 45,758 out, **$0.770** at $3/$15).

| Metric | 4.6 (max, thinking capped @50%) | S5 `xhigh` (adaptive) | S5 `max` (adaptive) |
|---|--:|--:|--:|
| Input tokens | 27,888 | 27,921 (+0%) | 31,876 (+14%) |
| Output tokens | 45,758 | 27,753 (−39%) | 92,619 (+102%) |
| **Cost @ intro ($2/$10)** | — | **$0.333** | **$0.990** |
| **Cost @ standard ($3/$15)** | **$0.770** | **$0.500** | **$1.485** |
| vs 4.6 (intro / standard) | — | −57% / −35% | +29% / +93% |
| Lexical insights | 41 | 34 | **51** |
| Figurative flags | 13 | — | **27** |
| Interesting questions | 11 | 12 | **15** |
| Note prose (chars) | 20,922 | 9,809 | 13,701 |
| Chars per insight | 510 | 288 | 269 |

### Key empirical findings
- **The feared +30% tokenizer inflation did NOT materialize on input** — flat (+33 tokens) on this
  Hebrew-heavy prompt. (The +30% is an average; re-baseline with real usage, don't assume it.)
- **`effort` is a very coarse, high-leverage lever on Sonnet 5.** `xhigh` → 27.8K output;
  `max` → 92.6K output — a **3.3× swing**, mostly uncapped adaptive thinking. Because
  `budget_tokens` is gone, you cannot cap it; nothing sits between `xhigh` and `max`.
- **You cannot get cheaper AND richer at once:**
  - `xhigh` is cheaper (−35% to −57%) but **genuinely thinner** than 4.6 (34 vs 41 insights, half the note prose). This was the user's concern.
  - `max` matches/beats 4.6 on breadth (51 insights, 2× figurative, more questions) but costs **more** than 4.6 (+29% intro / +93% standard). The session-start "Sonnet 5 is cheaper" thesis **reverses** at the effort needed to preserve density.
  - 4.6 is the middle on both axes.

## Quality judgment (manual, verses 2/4/10 read side-by-side; S5 at `max` vs 4.6)
**Comparable overall. Different profiles.** Neither is a downgrade.
- **Sonnet 5 is sharper on cross-verse connective insight** (the pipeline's highest-value axis —
  what the synthesis/writer stage prizes). Catches 4.6 missed entirely:
  - v2: תְּהִלָּה (praise) vs תְפִלָּה (prayer, v3) differ only by ה/פ → phonetic near-rhyme across the verse boundary.
  - v4→v7: גָּבְרוּ ("sin overpowers") reappears as גְּבוּרָה ("God girded with might") — engineered contrastive echo.
  - v4: תְכַפְּרֵם takes sins as a *direct object* — "unusual; כפר normally takes עַל/בְּעַד with a priestly subject."
  - v10: פֶּלֶג אֱלֹהִים framed as the "X-of-God = superlative" construction w/ parallels אַרְזֵי־אֵל (Ps 80:11), הַרְרֵי־אֵל (Ps 36:7); paqadta as ironic reversal of v4's "visiting iniquity."
- **4.6 is deeper per item** — enumerates more interpretive options (3 readings of דֻּמִיָּה vs S5's 1;
  3 readings of the v4 person-shift) and carries longer cross-reference chains (Ps 22/66/116 for
  vow-payment; LXX μεθύω→wine thread into v11). ~510 vs ~269 chars/insight.
- Net: S5-`max` is a better **scout** (breadth + connections), a slightly weaker **essayist** (per-item depth).

## Decision & recommendation
- **Not adopted.** No clear win: the cheap setting (`xhigh`) is thinner; the rich setting (`max`)
  is pricier than 4.6. The `max` premium is small in absolute terms — **+$0.22/psalm (intro) or
  +$0.71/psalm (standard)**, ~$33–107 across all 150 (one-time corpus) — and arguably feeds better
  raw material to the writer, but it is *not* a cost win, which is what triggered the investigation.
- **If revisited**, two untested levers could get 4.6-level per-item depth at `xhigh`'s lower cost:
  1. A model-gated nudge to the shared `DISCOVERY_PASS_PROMPT` WRITING-DENSITY block (Sonnet 5
     follows length instructions literally and defaults terse) — must be gated so 4.6/production is unchanged.
  2. Validate end-to-end: run Ps 65 full-pipeline on S5-`max` micro and diff the **published DOCX**
     (the micro stage only feeds the writer; a blind position-debiased judge à la `evaluate_novelty_ab.py`
     would give a less subjective verdict than the manual read above).

## Reproduction notes
- The A/B used a throwaway runner (`archive/development_scripts/compare_micro_sonnet5.py`, since
  removed) that reused `output/psalm_65/psalm_065_macro.json`, ran Stages 1–2 only (Stage 3 research
  assembly is not a Sonnet call — skip it), and priced via a temporary `claude-sonnet-5` entry in
  `src/utils/cost_tracker.py` (intro $2/$10; also computed standard $3/$15).
- **Gotcha**: `MicroAnalystV2` default `db_path` is `data/tanakh.db`, but the populated DB lives at
  `database/tanakh.db` (87 MB). Pass `db_path="database/tanakh.db"` for standalone runs or you get an
  empty auto-created DB and "Psalm N not found."
