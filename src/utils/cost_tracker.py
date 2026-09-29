"""
Cost Tracking Utility for Pipeline

Tracks API usage and costs across all models used in the pipeline:
- Claude Opus 4.6
- Claude Opus 4.5
- Claude Sonnet 4.5
- GPT-5
- Gemini 2.5 Pro

Usage:
    tracker = CostTracker()
    tracker.add_usage("claude-opus-4-5", input_tokens=1000, output_tokens=500, thinking_tokens=2000)
    print(tracker.get_summary())

Author: Claude (Anthropic)
Date: 2025-11-25
"""

import logging
from datetime import date
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ModelUsage:
    """Track usage for a specific model."""
    model_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0  # Only for Claude models with extended thinking
    cache_read_tokens: int = 0  # Anthropic cache reads (0.1x input, either TTL)
    cache_write_tokens: int = 0  # Anthropic 5-minute cache writes (1.25x input)
    cache_write_1h_tokens: int = 0  # Anthropic 1-hour cache writes (2x input)
    call_count: int = 0

    def add_usage(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        thinking_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        cache_write_1h_tokens: int = 0
    ):
        """Add usage from a single API call."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.thinking_tokens += thinking_tokens
        self.cache_read_tokens += cache_read_tokens
        self.cache_write_tokens += cache_write_tokens
        self.cache_write_1h_tokens += cache_write_1h_tokens
        self.call_count += 1


# Pricing as of November 2025 (per million tokens)
#
# CACHE ROWS (Anthropic): prompt caching has two TTLs and they are priced
# differently, so there are two write rows:
#   "cache_write"     5-minute TTL, 1.25x base input
#   "cache_write_1h"  1-hour TTL,   2.00x base input
#   "cache_read"      either TTL,   0.10x base input  (a read also refreshes the
#                                                      TTL at no extra charge)
# Nothing in the pipeline requests the 1-hour TTL today, so "cache_write_1h" is
# unused-but-correct. It exists because the table previously carried ONLY the
# 5-minute rate: any future caller passing ttl="1h" would have been billed 2x and
# reported at 1.25x, a silent 60% under-report of the write. Sizing note for
# whoever wires up caching: the 1-hour TTL only pays off from THREE reuses of the
# cached prefix onward -- for a single downstream read it is a net loss
# (2.0 + 0.1 = 2.1x vs 2.0x uncached).
PRICING = {
    # Claude Opus 4.5 (released Nov 24, 2025)
    "claude-opus-4-5": {
        "input": 5.00,
        "output": 25.00,
        "thinking": 25.00,  # Thinking tokens charged at output rate
        "cache_read": 0.50,  # 10% of input price
        "cache_write": 6.25,  # 25% markup on input
        "cache_write_1h": 10.00,
    },
    # Claude Opus 4.6 (released Feb 2026) - Adaptive thinking model
    "claude-opus-4-6": {
        "input": 5.00,
        "output": 25.00,
        "thinking": 25.00,  # Adaptive thinking charged at output rate
        "cache_read": 0.50,  # 10% of input price
        "cache_write": 6.25,  # 25% markup on input
        "cache_write_1h": 10.00,
    },
    # Claude Opus 4.7 (released Apr 2026) - New tokenizer, same per-token pricing
    "claude-opus-4-7": {
        "input": 5.00,
        "output": 25.00,
        "thinking": 25.00,  # Thinking tokens charged at output rate
        "cache_read": 0.50,  # 10% of input price
        "cache_write": 6.25,  # 25% markup on input
        "cache_write_1h": 10.00,
    },
    # Claude Opus 4.8
    "claude-opus-4-8": {
        "input": 5.00,
        "output": 25.00,
        "thinking": 25.00,
        "cache_read": 0.50,
        "cache_write": 6.25,
        "cache_write_1h": 10.00,
    },
    # Claude Opus 5 - PRODUCTION WRITER since Session 373. Same per-token price as
    # Opus 4.8 ($5/$25, verified 2026-08-03), so the cost difference is entirely
    # output VOLUME: Anthropic folds thinking into billed output, and Opus 5 emits
    # more of it. Measured writer-stage-only on Psalm 72, identical dossier:
    #   Opus 4.8   200,441 in / 22,544 out  = $1.57
    #   Opus 5     201,221 in / 38,556 out  = $1.97   (1.71x output tokens)
    # => +$0.40 per psalm, ~7% of a full ~$5.85 run. Session 368 measured +$0.59 on
    # Ps 71 under the OLD prompt (1.99x output), so the delta moves with the prompt.
    "claude-opus-5": {
        "input": 5.00,
        "output": 25.00,
        "thinking": 25.00,
        "cache_read": 0.50,
        "cache_write": 6.25,
        "cache_write_1h": 10.00,
    },
    # Claude Opus 5.5. Session 383: added for the Ps 76 all-Opus A/B; NOT production.
    # 20% cheaper than Opus 5 on both axes ($4/$20, verified on Anthropic's pricing
    # page 2026-09-24). Its CACHE READ IS A SECOND EXCEPTION to the 0.1x rule:
    # $0.20/MTok = 0.05x input, footnoted by Anthropic -- so it is named in
    # test_prompt_caching.CACHE_READ_MULTIPLIER_EXCEPTIONS alongside Fable 5.1.
    # Writes are the standard 1.25x / 2x.
    "claude-opus-5-5": {
        "input": 4.00,
        "output": 20.00,
        "thinking": 20.00,
        "cache_read": 0.20,
        "cache_write": 5.00,
        "cache_write_1h": 8.00,
    },
    # Claude Sonnet 5. WIRED BUT NOT FIRING: literary_echoes_agent.SECOND_GEN_MODEL
    # names it and the second generator is off by default (that module documents the
    # nine configurations that do not work). It appears in NO saved cost JSON across
    # 33 runs. The row exists because its ABSENCE was the Session-377 bug: an unknown
    # model fell back to an all-zeros row, so the shelved Sonnet-5 micro A/B
    # (SONNET5_MICRO_AB_FINDINGS.md) would have scored its cost arm at $0.00.
    #
    # Session 382: CORRECTED from $3.00/$15.00, and this one was WRONG ON THE DAY IT
    # WAS READ, not merely latent. The $2/$10 launch price, announced as introductory
    # through 2026-08-31, was made PERMANENT on 2026-08-10 and the scheduled
    # 2026-09-01 increase was CANCELLED -- Anthropic's platform pricing page carries
    # an explicit note saying so (verified 2026-09-17). This row held the durable
    # $3/$15 behind an INTRO_PRICING override that expired 2026-08-31, so from
    # 2026-09-01 until this fix resolve_pricing() returned $3/$15: a 50% over-report
    # on both axes. See INTRO_PRICING below for why "self-healing" failed here.
    #
    # For whoever revisits that A/B: Sonnet 5 is now PERMANENTLY 33% cheaper on output
    # than Sonnet 4.6 ($10 vs $15), which is the axis the micro analyst spends 89% of
    # its money on. The old comment here warned that a decision made on promo
    # economics "unmakes itself on 2026-09-01". That is no longer true -- the promo
    # became the price, so the cost argument for that swap is now permanent.
    "claude-sonnet-5": {
        "input": 2.00,
        "output": 10.00,
        "thinking": 10.00,
        "cache_read": 0.20,
        "cache_write": 2.50,
        "cache_write_1h": 4.00,
    },
    # Claude Fable 5. NOT USED IN PRODUCTION -- present for the same reason as the
    # Sonnet 5 row: an unpriced model must never report $0.
    "claude-fable-5": {
        "input": 10.00,
        "output": 50.00,
        "thinking": 50.00,
        "cache_read": 1.00,  # 10% of input -- Fable 5, unlike Fable 5.1 below
        "cache_write": 12.50,
        "cache_write_1h": 20.00,
    },
    # Claude Fable 5.1. NOT USED IN PRODUCTION -- added in Session 382 for the same
    # reason as the two rows above: an unpriced model must never report $0.
    #
    # THE CACHE READ IS THE TRAP, AND IT BREAKS A RULE THIS FILE ENCODES EVERYWHERE
    # ELSE. Fable 5.1 and Mythos 5.1 are the ONLY models that do not price a cache hit
    # at 0.1x input: theirs is 0.025x, i.e. $0.25/MTok against a $10 input, and
    # Anthropic's pricing page carries it as an explicit footnote. Session 377's
    # test_cached_input_is_never_free asserts cache_read == 0.10 * input on EVERY row,
    # so writing this row CORRECTLY makes that test fail. The fix belongs in the test
    # (a named exception set), never in the row -- a $1.00 here would be a 4x
    # over-report dressed up as passing. Verified 2026-09-17.
    "claude-fable-5-1": {
        "input": 10.00,
        "output": 50.00,
        "thinking": 50.00,
        "cache_read": 0.25,  # 0.025x input -- NOT 10%. See above.
        "cache_write": 12.50,
        "cache_write_1h": 20.00,
    },
    # Claude Sonnet 4.6 (released Feb 2026) - Adaptive thinking, same pricing as Sonnet 4.5
    "claude-sonnet-4-6": {
        "input": 3.00,
        "output": 15.00,
        "thinking": 15.00,  # Thinking tokens charged at output rate
        "cache_read": 0.30,  # 10% of input price
        "cache_write": 3.75,  # 25% markup on input
        "cache_write_1h": 6.00,
    },
    # Claude Sonnet 4.5
    "claude-sonnet-4-5": {
        "input": 3.00,
        "output": 15.00,
        "thinking": 15.00,  # Thinking tokens charged at output rate
        "cache_read": 0.30,  # 10% of input price
        "cache_write": 3.75,  # 25% markup on input
        "cache_write_1h": 6.00,
    },
    # Claude Haiku 4 (for liturgical librarian fallback)
    "claude-haiku-4": {
        "input": 1.00,
        "output": 5.00,
        "thinking": 5.00,
        "cache_read": 0.10,
        "cache_write": 1.25,
        "cache_write_1h": 2.00,
    },
    # Claude Haiku 4.5 (for citation verifier false-positive filter).
    # Session 373: CORRECTED from $0.80/$4.00 — that was 20% under the real rate and
    # had been under-reporting every citation-verifier run. Checked against the live
    # models overview on 2026-08-03: Haiku 4.5 is $1 / input MTok, $5 / output MTok.
    # The alias and the dated ID are the same model; both are listed so a call made
    # either way is priced.
    "claude-haiku-4-5-20251001": {
        "input": 1.00,
        "output": 5.00,
        "thinking": 5.00,
        "cache_read": 0.10,   # 10% of input
        "cache_write": 1.25,  # 25% markup on input (5-minute TTL)
        "cache_write_1h": 2.00,
    },
    "claude-haiku-4-5": {
        "input": 1.00,
        "output": 5.00,
        "thinking": 5.00,
        "cache_read": 0.10,
        "cache_write": 1.25,
        "cache_write_1h": 2.00,
    },
    # GPT-5 (OpenAI). Legacy row -- nothing in the pipeline selects this model today.
    # Session 377: cache_read CORRECTED from 0.0 along with gpt-5.1/gpt-5.4.
    "gpt-5": {
        "input": 1.25,
        "output": 10.00,
        "thinking": 10.00,  # Reasoning tokens charged at output rate
        "cache_read": 0.125,  # 10% of input
        "cache_write": 0.0,  # OpenAI does not charge for cache writes
        "cache_write_1h": 0.00,
    },
    # GPT-5.1 (OpenAI) - Same pricing as GPT-5.
    # Session 377: cache_read CORRECTED from 0.0. OpenAI caches automatically on any
    # prompt prefix >= 1024 tokens and bills the hit at 10% of input; the old 0.0
    # with its "Not applicable" comment would have priced a cached token at ZERO the
    # moment a caller started passing cache_read_tokens -- silent under-report, the
    # opposite direction from the Session-373 audit but the same shape.
    # NO long-context tier on this model (verified on OpenAI's pricing page
    # 2026-08-07): gpt-5.1 is short-context-only pricing.
    "gpt-5.1": {
        "input": 1.25,
        "output": 10.00,
        "thinking": 10.00,  # Reasoning tokens charged at output rate
        "cache_read": 0.125,  # 10% of input (OpenAI automatic prefix caching)
        "cache_write": 0.0,  # OpenAI does not charge for cache writes
        "cache_write_1h": 0.00,
    },
    # GPT-5.4 (OpenAI) - the copy editor, pinned here by COPY_EDITOR_TERRA_FINDINGS.
    # Session 377: cache_read CORRECTED from 0.0 (see the gpt-5.1 note above).
    # CAVEAT -- OpenAI now tiers this model by PROMPT LENGTH and we encode only the
    # cheap tier, exactly like the gemini-3.1-pro row below:
    #     short context  $2.50 in / $0.25 cached / $15.00 out   <- encoded
    #     long context   $5.00 in / $0.50 cached / $22.50 out   <- NOT encoded
    # Session 382 -- THE BOUNDARY IS NOW KNOWN and the old guess here was wrong in the
    # cautious direction. The threshold is the 272K context figure itself, not "well
    # below" it: past 272K input on a single request the input rate doubles AND the
    # output rate goes 1.5x for the whole session. The encoded long-context figures
    # above are confirmed correct. Our only caller is the copy editor at ~29K input
    # tokens (Ps 73), an order of magnitude under the boundary, so the cheap tier is
    # correct today with a wide margin. CostTracker accumulates per-model TOTALS and has
    # no per-call prompt length, so a tier cannot be applied here without pricing at
    # the call site -- if a caller ever approaches the boundary, that is the work.
    "gpt-5.4": {
        "input": 2.50,
        "output": 15.00,
        "thinking": 15.00,  # Reasoning tokens charged at output rate
        "cache_read": 0.25,  # 10% of input
        "cache_write": 0.0,  # OpenAI does not charge for cache writes
        "cache_write_1h": 0.00,
    },
    # GPT-5.6 Terra (OpenAI, GA 2026-07-09) - the mid "durable capability tier".
    # Session 373: CORRECTED from $2.50/$15.00. The old note claimed Terra was
    # "priced IDENTICALLY to gpt-5.4, so the Session-367 swap is cost-neutral by
    # construction" — that was true at GA and is no longer: checked against OpenAI's
    # live pricing page on 2026-08-03, Terra is $2.00 / $12.00, i.e. 20% cheaper input
    # and output than gpt-5.4. We had been OVER-reporting every Terra call by ~25%.
    # Terra is our heaviest non-Anthropic spender (figurative curator + literary echoes
    # passes 3-4 + insight/question curation), so this moved real numbers: on the Ps 72
    # run it reported $1.3273 where the true cost was ~$1.06.
    # Session 377 -- two updates to this row:
    #  (a) the "not yet wired up" note on cache_read was STALE. It has been wired
    #      since Session 374: literary_echoes_agent._record passes cached tokens and
    #      the Ps 73 run priced 96,347 of them at $0.0193.
    #  (b) CAVEAT, same shape as gpt-5.4 and gemini-3.1-pro -- Terra now has a
    #      long-context tier and we encode only the cheap one:
    #          short context  $2.00 in / $0.20 cached / $12.00 out   <- encoded
    #          long context   $4.00 in / $0.40 cached / $18.00 out   <- NOT encoded
    #      Terra is our heaviest non-Anthropic spender, but it spends across MANY
    #      SMALL calls, not one big one: echoes Pass 3 is one call per entry (~14K
    #      input each, 350K summed over 20 calls on Ps 73). The tier is per REQUEST,
    #      so summed volume never trips it -- only a single oversized prompt would.
    # Session 388: cache WRITES are billed at 1.25x input from GPT-5.6 on (OpenAI's
    # prompt-caching guide and pricing table, read 2026-09-29; the table has a "cache
    # writes" column: $2.50 for Terra). OpenAI has one write rate whatever the
    # retention, so cache_write_1h carries the same figure. Callers report the split
    # with openai_usage.split_input_tokens.
    "gpt-5.6-terra": {
        "input": 2.00,
        "output": 12.00,
        "thinking": 12.00,  # Reasoning tokens charged at output rate
        "cache_read": 0.20,  # 10% of input; wired up since Session 374
        "cache_write": 2.50,  # 1.25x input (GPT-5.6+), Session 388
        "cache_write_1h": 2.50,  # OpenAI has no separate long-retention write rate
    },
    # GPT-6 Sol (OpenAI, launched 2026-09-22). Session 388: CORRECTED from an assumed
    # durable $4/$20 behind a $2/$10 "promo" through 2026-11-21. OpenAI's pricing table
    # (read 2026-09-29) lists gpt-6-sol at $2.00 / $0.20 cached / $2.50 cache writes /
    # $10.00 as STANDARD, with no expiry; the only promo footnote on the page reads
    # "GPT-5.6 Sol's promotional pricing is available at least through November 21,
    # 2026" -- a different model, listed at $4/$20. S384 had pinned that note to the
    # wrong Sol, so every "at durable rates" figure since (the Ps 77 report's $11.17)
    # doubled the fact check for no reason. Long-context tier (> 272K input tokens:
    # $4 / $0.40 / $5.00 / $15) NOT encoded; stage-1 calls stay well under it.
    "gpt-6-sol": {
        "input": 2.00,
        "output": 10.00,
        "thinking": 10.00,  # reasoning tokens billed as output
        "cache_read": 0.20,  # 10% of input
        "cache_write": 2.50,  # 1.25x input (GPT-5.6+), Session 388
        "cache_write_1h": 2.50,  # OpenAI has no separate long-retention write rate
    },
    # GPT-6 Luna (OpenAI). Session 386: added for the fact checker's cost work. Verified
    # on OpenAI's pricing page 2026-09-28 as STANDARD pricing (no promo note): $0.10
    # input / $0.01 cached / $0.50 output; long-context tier $0.20 / $0.02 / $0.75 NOT
    # encoded (same threshold shape as gpt-6-sol). Web search is billed on top at
    # $10 / 1k calls + search content tokens at these rates. Session 388: cache writes
    # $0.125 (1.25x), per the same table.
    "gpt-6-luna": {
        "input": 0.10,
        "output": 0.50,
        "thinking": 0.50,  # reasoning tokens billed as output
        "cache_read": 0.01,  # 10% of input
        "cache_write": 0.125,  # 1.25x input (GPT-5.6+), Session 388
        "cache_write_1h": 0.125,
    },
    # Gemini 3.8 Flash (Google). Session 386: the fact checker's web-evidence gatherer.
    # Verified on Google's pricing page 2026-09-28: "$0.75 through December 31, 2026.
    # $1.50 starting January 1, 2027" input, "$3.75 ... $7.50" output (thinking included),
    # context caching "$0.075 ... $0.15". THIS ROW IS THE 2027 PRICE; the 2026 price is an
    # INTRO_PRICING override below. Grounding with Google Search: 5,000 free requests a
    # month across Gemini 3.x, then $14 / 1,000; retrieved content is NOT billed as input.
    "gemini-3.8-flash": {
        "input": 1.50,
        "output": 7.50,
        "thinking": 7.50,  # "Output price (including thinking tokens)"
        "cache_read": 0.15,  # 10% of input
        "cache_write": 0.0,  # Google bills caching by storage-time, not a write multiplier
        "cache_write_1h": 0.00,
    },
    # Gemini 2.5 Pro (Google). Session 382: CORRECTED from $3.00/$12.00 with
    # cache_read $0.30 and cache_write $3.75. Those were never Google's rates -- the
    # two marked "(approximate)" were Anthropic-shaped guesses (10% and a 25% write
    # markup) applied to a vendor that prices neither way. The real input rate is 40%
    # of what we carried, i.e. the row OVER-stated input by 140%. Verified against
    # Google's live pricing page 2026-09-17.
    #
    # LATENT: the only caller is synthesis_writer's liturgical-librarian path, and the
    # model appears in NO saved cost JSON across 33 runs, so no reported figure moves.
    # CAVEAT -- tiered by prompt length, cheap tier encoded (same shape as the
    # gemini-3.1-pro row below):
    #     <= 200k tokens   $1.25 in / $0.125 cached / $10.00 out   <- encoded
    #     >  200k tokens   $2.50 in / $0.25  cached / $15.00 out   <- NOT encoded
    "gemini-2.5-pro": {
        "input": 1.25,
        "output": 10.00,
        "thinking": 10.00,  # Extended thinking charged at output rate
        "cache_read": 0.125,  # 10% of input
        # 0, not a markup: Google prices context caching by storage-time, not by a
        # per-token write multiplier, so NEITHER Anthropic cache-write row has a
        # Gemini analogue. Matches how gemini-3.1-pro-preview is encoded below.
        "cache_write": 0.00,
        "cache_write_1h": 0.00,
    },
    # Gemini 3.1 Pro (Google). Verified against Google's live pricing page 2026-08-03.
    # CAVEAT — Google tiers this model by PROMPT LENGTH and we only encode the cheap
    # tier: $2.00/$12.00 for prompts <=200k tokens, $4.00/$18.00 above it. Our only
    # caller is literary echoes passes 1-2 (~16k input tokens on Ps 72), so the low
    # tier is correct today; a Gemini call that ever crossed 200k input would be
    # under-reported by 2x on input and 1.5x on output.
    # Session 377: cache_read CORRECTED from 0.0 -- Google prices a cached-input hit
    # at $0.20/MTok (10% of input), and 0.0 would have priced it free.
    "gemini-3.1-pro-preview": {
        "input": 2.00,
        "output": 12.00,
        "thinking": 12.00,  # Thinking tokens charged at output rate
        "cache_read": 0.20,  # 10% of input (implicit/explicit context caching)
        "cache_write": 0.0,  # Google bills caching by storage-time, not a write multiplier
        "cache_write_1h": 0.00,
    },
}


# ---------------------------------------------------------------------------
# Time-limited introductory pricing
# ---------------------------------------------------------------------------
# A row above holds the DURABLE rates -- what the model costs once any promotional
# period is over. A model currently on introductory pricing gets an entry here with
# the temporary rates and the last date they apply.
#
# Why this direction and not the other: encode the promo rate in the row and the
# table silently goes wrong on the day the promo ends, and stays wrong until someone
# notices -- which is precisely how "priced IDENTICALLY to gpt-5.4... cost-neutral by
# construction" survived six weeks in Session 373. Encode the durable rate and the
# override simply STOPS APPLYING on its own. The failure mode is self-healing.
INTRO_PRICING = {
    # Gemini 3.8 Flash (Session 386): the 2026 price, per Google's page read 2026-09-28
    # ("through December 31, 2026"). When it expires, RE-CHECK the durable row.
    "gemini-3.8-flash": {
        "through": date(2026, 12, 31),
        "rates": {"input": 0.75, "output": 3.75, "thinking": 3.75, "cache_read": 0.075},
    },
    # (Session 388: the gpt-6-sol entry that stood here from S384 was a mix-up with
    # GPT-5.6 Sol's promotion; $2/$10 is gpt-6-sol's standard price -- see its row.)
    # WAS EMPTY from Session 382 until Session 384, and that emptiness was a finding.
    #
    # Claude Sonnet 5's $2/$10 was announced as introductory through 2026-08-31. On
    # 2026-08-10 Anthropic made it the STANDARD price and cancelled the scheduled
    # 2026-09-01 increase, so the promo rate is now simply the row above and there is
    # nothing left to override. Verified 2026-09-17: no Claude model is on
    # introductory pricing today.
    #
    # KEEP THIS MECHANISM, BUT KNOW WHAT IT MISSED. The design note above reasons
    # about ONE failure mode -- "the promo ends and the table stays cheap" -- which an
    # expiry date heals by itself. The event that actually occurred was the mirror
    # image: THE PROMO BECAME THE PRICE. Against that, the self-healing direction
    # heals INTO the wrong number and then sits there silently, which is exactly what
    # happened between 2026-09-01 and this fix, when resolve_pricing("claude-sonnet-5")
    # returned the stale durable $3/$15.
    #
    # So an expiring override is only half a safeguard. The other half is a calendar
    # obligation: WHEN AN EXPIRY PASSES, RE-CHECK THE DURABLE ROW -- do not assume the
    # listed price resumed. An expiry that fires unattended is indistinguishable from
    # one that fired correctly.
}


_ZERO_ROW = {
    "input": 0.0,
    "output": 0.0,
    "thinking": 0.0,
    "cache_read": 0.0,
    "cache_write": 0.0,
    "cache_write_1h": 0.0,
}


def resolve_pricing(model: str, on_date: Optional[date] = None) -> Optional[Dict[str, float]]:
    """Rates for `model` on `on_date` (default: today), or None if unpriced.

    Returning None rather than a zero row is deliberate. `PRICING.get(model, zeros)`
    used to swallow an unknown model and report $0.00 for it -- the same silent-loss
    shape as the discarded writer thinking (S376), the truncated echoes dossiers
    (S374), and the eaten quotation marks (S373). The caller is now forced to decide
    what to do about a model it cannot price.
    """
    row = PRICING.get(model)
    if row is None:
        return None
    promo = INTRO_PRICING.get(model)
    if promo and (on_date or date.today()) <= promo["through"]:
        return {**row, **promo["rates"]}
    return row


def price_tokens(
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    thinking_tokens: int = 0,
    cached_input_tokens: int = 0,
    on_date: Optional[date] = None,
    cache_write_tokens: int = 0,
) -> float:
    """Cost of one call, priced from the single table above.

    TOKEN CONTRACT -- every argument is DISJOINT, matching what `CostTracker`
    expects, because costs are SUMMED:
        input_tokens         fresh (uncached) input only
        cached_input_tokens  input served from cache, priced at cache_read
        cache_write_tokens   input written to the cache, priced at cache_write
                             (OpenAI GPT-5.6+: see openai_usage.split_input_tokens)
        output_tokens        visible output, EXCLUDING reasoning
        thinking_tokens      reasoning only
    See `src/utils/openai_usage.py` for why the OpenAI split is not optional.

    Exists so that no module has to keep its own copy of the NUMBERS. Session 374
    removed one such duplicate from literary_echoes_agent.py; Session 377 removed a
    second from figurative_curator.py, which had been carrying gpt-5.4's $2.50/$15.00
    for a model that costs $2.00/$12.00.
    """
    rates = resolve_pricing(model, on_date)
    if rates is None:
        raise KeyError(
            f"{model!r} has no row in cost_tracker.PRICING -- add one before "
            f"pricing calls against it (an unpriced model must not report $0)"
        )
    return (
        input_tokens / 1_000_000 * rates["input"]
        + output_tokens / 1_000_000 * rates["output"]
        + thinking_tokens / 1_000_000 * rates["thinking"]
        + cached_input_tokens / 1_000_000 * rates["cache_read"]
        + cache_write_tokens / 1_000_000 * rates["cache_write"]
    )


def _price_usage(model: str, d: Dict[str, int], on_date: Optional[date] = None) -> float:
    """Cost of a usage delta (CostTracker field names) at the rates of `on_date`."""
    p = resolve_pricing(model, on_date) or _ZERO_ROW
    return (d.get("input_tokens", 0) * p["input"] + d.get("output_tokens", 0) * p["output"]
            + d.get("thinking_tokens", 0) * p["thinking"] + d.get("cache_read_tokens", 0) * p["cache_read"]
            + d.get("cache_write_tokens", 0) * p["cache_write"]
            + d.get("cache_write_1h_tokens", 0) * p.get("cache_write_1h", 2.0 * p["input"])) / 1_000_000


class CostTracker:
    """
    Track API usage and costs across all models in the pipeline.

    Example:
        tracker = CostTracker()
        tracker.add_usage("claude-sonnet-4-5", input_tokens=1000, output_tokens=500)
        tracker.add_usage("gpt-5", input_tokens=2000, output_tokens=800)
        print(tracker.get_summary())
    """

    def __init__(self):
        self.usage_by_model: Dict[str, ModelUsage] = {}
        self.events: List[Dict[str, str]] = []
        # Models seen that have no row in PRICING. Non-empty => every total is a floor.
        self.unpriced_models: set = set()
        # Session 387: money that is not tokens (OpenAI's $10 per 1,000 web searches),
        # and per-stage deltas recorded by the pipeline. Both are in every total.
        self.charges: List[Dict] = []
        self.stages: List[Dict] = []
        self.notes: List[str] = []   # free-text caveats for the cost report (e.g. unrecorded spend)
        self._attempt = 1

    # -- non-token charges and per-stage accounting (Session 387) ----------------
    def load_dict(self, d: Dict) -> None:
        """Continue a saved psalm_NNN_cost.json (a resumed or partial re-run). Earlier stages
        keep their records and are marked with the attempt they belonged to, so a stage that
        runs again is shown twice rather than silently replacing the money already spent."""
        for model, row in d.items():
            if not isinstance(row, dict) or "input_tokens" not in row:
                continue
            u = self.usage_by_model.setdefault(model, ModelUsage(model_name=model))
            for f in self._USAGE_FIELDS:
                setattr(u, f, getattr(u, f) + int(row.get(f, 0) or 0))
        self.events += list(d.get("events", []))
        self.charges += list(d.get("charges", []))
        prev = max([s.get("attempt", 1) for s in d.get("stages", [])] or [0])
        self._attempt = prev + 1
        self.stages += [dict(s, attempt=s.get("attempt", 1)) for s in d.get("stages", [])]
        self.notes += list(d.get("notes", []))

    def add_charge(self, label: str, usd: float, model: Optional[str] = None, detail: str = ""):
        """A fee billed per call rather than per token, e.g. web search. Counted in
        get_total_cost(), so a stage's cost delta includes it."""
        self.charges.append({"label": label, "usd": float(usd), "model": model, "detail": detail})

    _USAGE_FIELDS = ("call_count", "input_tokens", "output_tokens", "thinking_tokens",
                     "cache_read_tokens", "cache_write_tokens", "cache_write_1h_tokens")

    def snapshot(self) -> Dict:
        """The tracker's state now, for record_stage()."""
        return {"usage": {m: {f: getattr(u, f) for f in self._USAGE_FIELDS}
                          for m, u in self.usage_by_model.items()},
                "n_charges": len(self.charges)}

    def record_stage(self, name: str, since: Dict) -> Dict:
        """Record what was spent since `since` (a snapshot()) as one pipeline stage: per
        model, the token counts and the cost at today's rates, plus the cost at the
        DURABLE rates wherever an introductory price was applied (INTRO_PRICING)."""
        models = {}
        for m, u in self.usage_by_model.items():
            before = since["usage"].get(m, {})
            d = {f: getattr(u, f) - before.get(f, 0) for f in self._USAGE_FIELDS}
            if not any(d.values()):
                continue
            row = dict(d, cost_usd=round(_price_usage(m, d), 6))
            promo = INTRO_PRICING.get(m)
            if promo and date.today() <= promo["through"]:
                row["promo_through"] = promo["through"].isoformat()
                row["cost_usd_at_durable_rates"] = round(_price_usage(m, d, date.max), 6)
            models[m] = row
        charges = self.charges[since["n_charges"]:]
        stage = {"stage": name, "attempt": self._attempt, "models": models, "charges": charges,
                 "cost_usd": round(sum(r["cost_usd"] for r in models.values())
                                   + sum(c["usd"] for c in charges), 6)}
        self.stages.append(stage)
        return stage

    def log_event(self, agent_name: str, event_type: str, message: str):
        """Log a pipeline event (e.g., error, retry)."""
        self.events.append({
            "agent": agent_name,
            "type": event_type,
            "message": message
        })

    def add_usage(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        thinking_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        cache_write_1h_tokens: int = 0
    ):
        """
        Add usage from a single API call.

        Args:
            model: Model identifier (e.g., "claude-opus-4-5", "gpt-5")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            thinking_tokens: Number of extended thinking tokens (Claude/Gemini)
            cache_read_tokens: Number of cache read tokens (Anthropic only)
            cache_write_tokens: Number of 5-MINUTE cache write tokens (Anthropic only)
            cache_write_1h_tokens: Number of 1-HOUR cache write tokens (Anthropic only)

        NOTE on splitting the two write figures: Anthropic's
        `usage.cache_creation_input_tokens` is the SUM of both TTLs. If a caller
        ever requests ttl="1h", read the split off
        `usage.cache_creation.ephemeral_5m_input_tokens` /
        `.ephemeral_1h_input_tokens` and pass them separately -- passing the summed
        field as `cache_write_tokens` would price 1-hour writes at the 5-minute
        rate. Callers that never request the 1-hour TTL can keep passing the summed
        field, which is what every caller does today.
        """
        if model not in self.usage_by_model:
            self.usage_by_model[model] = ModelUsage(model_name=model)

        self.usage_by_model[model].add_usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            cache_write_1h_tokens=cache_write_1h_tokens
        )

    def calculate_cost(self, model: str) -> Dict[str, float]:
        """
        Calculate cost breakdown for a specific model.

        Returns:
            Dictionary with cost breakdown:
                - input_cost: Cost of input tokens
                - output_cost: Cost of output tokens
                - thinking_cost: Cost of thinking tokens
                - cache_cost: Cost of cache operations
                - total_cost: Total cost
        """
        if model not in self.usage_by_model:
            return {
                "input_cost": 0.0,
                "output_cost": 0.0,
                "thinking_cost": 0.0,
                "cache_cost": 0.0,
                "total_cost": 0.0
            }

        usage = self.usage_by_model[model]
        # An unknown model used to fall back to an all-zeros row and report $0.00 in
        # silence. It now still returns zeros -- raising here would destroy the cost
        # report of a run that has already been paid for -- but it says so, loudly
        # and in the summary, so the instrument reports its own death.
        pricing = resolve_pricing(model)
        if pricing is None:
            if model not in self.unpriced_models:
                self.unpriced_models.add(model)
                logger.warning(
                    "UNPRICED MODEL %r -- no row in cost_tracker.PRICING. Its tokens "
                    "are being reported at $0.00, so every total below is a FLOOR, "
                    "not the real cost. Add a row.", model
                )
            pricing = _ZERO_ROW

        # A model row that predates the 1-hour rate falls back to the documented
        # 2x-input multiplier rather than to zero -- an unpriced write is exactly
        # the silent under-report this row was added to prevent.
        cache_write_1h_rate = pricing.get("cache_write_1h", 2.0 * pricing.get("input", 0.0))

        # Calculate costs (pricing is per million tokens)
        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]
        thinking_cost = (usage.thinking_tokens / 1_000_000) * pricing["thinking"]
        cache_cost = (
            (usage.cache_read_tokens / 1_000_000) * pricing["cache_read"] +
            (usage.cache_write_tokens / 1_000_000) * pricing["cache_write"] +
            (usage.cache_write_1h_tokens / 1_000_000) * cache_write_1h_rate
        )

        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "thinking_cost": thinking_cost,
            "cache_cost": cache_cost,
            "total_cost": input_cost + output_cost + thinking_cost + cache_cost
        }

    def get_total_cost(self) -> float:
        """Calculate total cost across all models, plus non-token charges."""
        total = 0.0
        for model in self.usage_by_model.keys():
            total += self.calculate_cost(model)["total_cost"]
        return total + sum(c["usd"] for c in self.charges)

    def get_summary(self) -> str:
        """
        Generate a detailed cost summary.

        Returns:
            Formatted string with cost breakdown by model
        """
        if not self.usage_by_model:
            return "No API usage recorded."

        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("PIPELINE COST SUMMARY")
        lines.append("=" * 80)

        grand_total = 0.0

        for model in sorted(self.usage_by_model.keys()):
            usage = self.usage_by_model[model]
            costs = self.calculate_cost(model)

            lines.append(f"\n{model.upper()}")
            lines.append("-" * 80)
            lines.append(f"  API Calls: {usage.call_count}")
            lines.append(f"  Input Tokens: {usage.input_tokens:,}")
            lines.append(f"  Output Tokens: {usage.output_tokens:,}")

            if usage.thinking_tokens > 0:
                lines.append(f"  Thinking Tokens: {usage.thinking_tokens:,}")

            if (usage.cache_read_tokens > 0 or usage.cache_write_tokens > 0
                    or usage.cache_write_1h_tokens > 0):
                lines.append(f"  Cache Read Tokens: {usage.cache_read_tokens:,}")
                lines.append(f"  Cache Write Tokens (5m): {usage.cache_write_tokens:,}")
                if usage.cache_write_1h_tokens > 0:
                    lines.append(f"  Cache Write Tokens (1h): {usage.cache_write_1h_tokens:,}")

            lines.append(f"  Input Cost: ${costs['input_cost']:.4f}")
            lines.append(f"  Output Cost: ${costs['output_cost']:.4f}")

            if costs['thinking_cost'] > 0:
                lines.append(f"  Thinking Cost: ${costs['thinking_cost']:.4f}")

            if costs['cache_cost'] > 0:
                lines.append(f"  Cache Cost: ${costs['cache_cost']:.4f}")

            lines.append(f"  TOTAL: ${costs['total_cost']:.4f}")
            grand_total += costs['total_cost']

        if self.charges:
            lines.append("\nNON-TOKEN CHARGES")
            lines.append("-" * 80)
            by_label: Dict[str, float] = {}
            for c in self.charges:
                by_label[c["label"]] = by_label.get(c["label"], 0.0) + c["usd"]
            for label, usd in sorted(by_label.items()):
                lines.append(f"  {label}: ${usd:.4f}")
                grand_total += usd

        lines.append("\n" + "=" * 80)
        if self.unpriced_models:
            lines.append(f"GRAND TOTAL: ${grand_total:.4f}   *** FLOOR, NOT ACTUAL ***")
            lines.append(
                "  UNPRICED MODELS (reported at $0.00): "
                + ", ".join(sorted(self.unpriced_models))
            )
            lines.append("  Add a row to cost_tracker.PRICING for each.")
        else:
            lines.append(f"GRAND TOTAL: ${grand_total:.4f}")
        lines.append("=" * 80 + "\n")

        if self.events:
            lines.append("\n" + "=" * 80)
            lines.append("PIPELINE EVENTS & RETRIES")
            lines.append("=" * 80)
            for event in self.events:
                lines.append(f"  [{event['agent']}] {event['type']}: {event['message']}")
            lines.append("=" * 80 + "\n")

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Export usage data as dictionary for JSON serialization."""
        result = {}
        for model, usage in self.usage_by_model.items():
            costs = self.calculate_cost(model)
            result[model] = {
                "call_count": usage.call_count,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "thinking_tokens": usage.thinking_tokens,
                "cache_read_tokens": usage.cache_read_tokens,
                "cache_write_tokens": usage.cache_write_tokens,
                "cache_write_1h_tokens": usage.cache_write_1h_tokens,
                "costs": costs
            }
        result["total_cost"] = self.get_total_cost()
        result["events"] = self.events
        # Only emitted when non-empty, so every existing cost JSON keeps its shape.
        # Its presence means total_cost is a floor: some model was billed at $0.00.
        if self.unpriced_models:
            result["unpriced_models"] = sorted(self.unpriced_models)
        # Session 387, same rule: only when present, so older cost JSONs keep their shape.
        if self.charges:
            result["charges"] = self.charges
        if self.stages:
            result["stages"] = self.stages
        if self.notes:
            result["notes"] = self.notes
        return result
