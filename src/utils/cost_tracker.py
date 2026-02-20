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
    cache_read_tokens: int = 0  # Anthropic cache reads
    cache_write_tokens: int = 0  # Anthropic cache writes
    call_count: int = 0

    def add_usage(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        thinking_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0
    ):
        """Add usage from a single API call."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.thinking_tokens += thinking_tokens
        self.cache_read_tokens += cache_read_tokens
        self.cache_write_tokens += cache_write_tokens
        self.call_count += 1


# Pricing as of November 2025 (per million tokens)
PRICING = {
    # Claude Opus 4.5 (released Nov 24, 2025)
    "claude-opus-4-5": {
        "input": 5.00,
        "output": 25.00,
        "thinking": 25.00,  # Thinking tokens charged at output rate
        "cache_read": 0.50,  # 10% of input price
        "cache_write": 6.25,  # 25% markup on input
    },
    # Claude Opus 4.6 (released Feb 2026) - Adaptive thinking model
    "claude-opus-4-6": {
        "input": 5.00,
        "output": 25.00,
        "thinking": 25.00,  # Adaptive thinking charged at output rate
        "cache_read": 0.50,  # 10% of input price
        "cache_write": 6.25,  # 25% markup on input
    },
    # Claude Sonnet 4.6 (released Feb 2026) - Adaptive thinking, same pricing as Sonnet 4.5
    "claude-sonnet-4-6": {
        "input": 3.00,
        "output": 15.00,
        "thinking": 15.00,  # Thinking tokens charged at output rate
        "cache_read": 0.30,  # 10% of input price
        "cache_write": 3.75,  # 25% markup on input
    },
    # Claude Sonnet 4.5
    "claude-sonnet-4-5": {
        "input": 3.00,
        "output": 15.00,
        "thinking": 15.00,  # Thinking tokens charged at output rate
        "cache_read": 0.30,  # 10% of input price
        "cache_write": 3.75,  # 25% markup on input
    },
    # Claude Haiku 4 (for liturgical librarian fallback)
    "claude-haiku-4": {
        "input": 1.00,
        "output": 5.00,
        "thinking": 5.00,
        "cache_read": 0.10,
        "cache_write": 1.25,
    },
    # GPT-5 (OpenAI)
    "gpt-5": {
        "input": 1.25,
        "output": 10.00,
        "thinking": 10.00,  # Reasoning tokens charged at output rate
        "cache_read": 0.0,  # Not applicable
        "cache_write": 0.0,  # Not applicable
    },
    # GPT-5.1 (OpenAI) - Same pricing as GPT-5
    "gpt-5.1": {
        "input": 1.25,
        "output": 10.00,
        "thinking": 10.00,  # Reasoning tokens charged at output rate
        "cache_read": 0.0,  # Not applicable
        "cache_write": 0.0,  # Not applicable
    },
    # Gemini 2.5 Pro (Google)
    "gemini-2.5-pro": {
        "input": 3.00,
        "output": 12.00,
        "thinking": 12.00,  # Extended thinking charged at output rate
        "cache_read": 0.30,  # 10% of input (approximate)
        "cache_write": 3.75,  # 25% markup (approximate)
    },
    # Gemini 3.0 Pro (Google)
    "gemini-3-pro-preview": {
        "input": 2.00,
        "output": 12.00,
        "thinking": 12.00,  # Thinking tokens charged at output rate
        "cache_read": 0.0,  # Not applicable yet
        "cache_write": 0.0,  # Not applicable yet
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

    def add_usage(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        thinking_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0
    ):
        """
        Add usage from a single API call.

        Args:
            model: Model identifier (e.g., "claude-opus-4-5", "gpt-5")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            thinking_tokens: Number of extended thinking tokens (Claude/Gemini)
            cache_read_tokens: Number of cache read tokens (Anthropic only)
            cache_write_tokens: Number of cache write tokens (Anthropic only)
        """
        if model not in self.usage_by_model:
            self.usage_by_model[model] = ModelUsage(model_name=model)

        self.usage_by_model[model].add_usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens
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
            "cache_write": 0.0
        })

        # Calculate costs (pricing is per million tokens)
        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]
        thinking_cost = (usage.thinking_tokens / 1_000_000) * pricing["thinking"]
        cache_cost = (
            (usage.cache_read_tokens / 1_000_000) * pricing["cache_read"] +
            (usage.cache_write_tokens / 1_000_000) * pricing["cache_write"]
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

            if usage.cache_read_tokens > 0 or usage.cache_write_tokens > 0:
                lines.append(f"  Cache Read Tokens: {usage.cache_read_tokens:,}")
                lines.append(f"  Cache Write Tokens: {usage.cache_write_tokens:,}")

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
                "costs": costs
            }
        result["total_cost"] = self.get_total_cost()
        return result
