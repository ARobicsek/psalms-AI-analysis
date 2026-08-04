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

from typing import Dict, Optional
from dataclasses import dataclass, field


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
    # GPT-5 (OpenAI)
    "gpt-5": {
        "input": 1.25,
        "output": 10.00,
        "thinking": 10.00,  # Reasoning tokens charged at output rate
        "cache_read": 0.0,  # Not applicable
        "cache_write": 0.0,  # Not applicable
        "cache_write_1h": 0.00,
    },
    # GPT-5.1 (OpenAI) - Same pricing as GPT-5
    "gpt-5.1": {
        "input": 1.25,
        "output": 10.00,
        "thinking": 10.00,  # Reasoning tokens charged at output rate
        "cache_read": 0.0,  # Not applicable
        "cache_write": 0.0,  # Not applicable
        "cache_write_1h": 0.00,
    },
    # GPT-5.4 (OpenAI)
    "gpt-5.4": {
        "input": 2.50,
        "output": 15.00,
        "thinking": 15.00,  # Reasoning tokens charged at output rate
        "cache_read": 0.0,  # Not applicable
        "cache_write": 0.0,  # Not applicable
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
    "gpt-5.6-terra": {
        "input": 2.00,
        "output": 12.00,
        "thinking": 12.00,  # Reasoning tokens charged at output rate
        "cache_read": 0.20,  # 90% off cached input (not yet wired up)
        "cache_write": 0.0,  # Not applicable
        "cache_write_1h": 0.00,
    },
    # Gemini 2.5 Pro (Google)
    "gemini-2.5-pro": {
        "input": 3.00,
        "output": 12.00,
        "thinking": 12.00,  # Extended thinking charged at output rate
        "cache_read": 0.30,  # 10% of input (approximate)
        "cache_write": 3.75,  # 25% markup (approximate)
        # 0, not 2x input: Google prices context caching by storage-time, not by a
        # write multiplier, so the Anthropic 1-hour row has no Gemini analogue.
        "cache_write_1h": 0.00,
    },
    # Gemini 3.1 Pro (Google). Verified against Google's live pricing page 2026-08-03.
    # CAVEAT — Google tiers this model by PROMPT LENGTH and we only encode the cheap
    # tier: $2.00/$12.00 for prompts <=200k tokens, $4.00/$18.00 above it. Our only
    # caller is literary echoes passes 1-2 (~16k input tokens on Ps 72), so the low
    # tier is correct today; a Gemini call that ever crossed 200k input would be
    # under-reported by 2x on input and 1.5x on output.
    "gemini-3.1-pro-preview": {
        "input": 2.00,
        "output": 12.00,
        "thinking": 12.00,  # Thinking tokens charged at output rate
        "cache_read": 0.0,  # Not applicable yet
        "cache_write": 0.0,  # Not applicable yet
        "cache_write_1h": 0.00,
    },
}


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
        pricing = PRICING.get(model, {
            "input": 0.0,
            "output": 0.0,
            "thinking": 0.0,
            "cache_read": 0.0,
            "cache_write": 0.0,
            "cache_write_1h": 0.0
        })

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
        """Calculate total cost across all models."""
        total = 0.0
        for model in self.usage_by_model.keys():
            total += self.calculate_cost(model)["total_cost"]
        return total

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

        lines.append("\n" + "=" * 80)
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
        return result
