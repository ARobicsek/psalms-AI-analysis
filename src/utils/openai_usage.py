"""
Reasoning-token extraction for OpenAI usage objects (Session 367 fix).

The bug this exists to prevent: `getattr(response.usage, "reasoning_tokens", 0)`
returns 0 on EVERY OpenAI response, because the field does not live on the usage
object. It is nested one level down, under a key whose name depends on which API
produced the response:

    chat.completions.create -> usage.completion_tokens_details.reasoning_tokens
    responses.create        -> usage.output_tokens_details.reasoning_tokens

Because the flat lookup fails silently (getattr default 0) rather than raising,
the pipeline reported `thinking_tokens: 0` for every GPT agent for a long time
while literary_echoes_agent.py — the one module that read the nested path —
correctly reported ~10.9K reasoning tokens per Ps-68 run.

Cost impact: none. OpenAI already counts reasoning tokens inside
`completion_tokens`/`output_tokens`, and CostTracker prices thinking and output
at the same per-token rate for every model we use, so run totals were always
right. Only the reported output-vs-thinking split was wrong.

Use `split_output_tokens(response.usage)` at any site that feeds CostTracker.

CRITICAL — why the split matters. OpenAI counts reasoning tokens INSIDE
`completion_tokens`/`output_tokens`, but CostTracker.calculate_cost ADDS
`output_cost` and `thinking_cost` together. So passing the raw completion count
as `output_tokens` AND the reasoning count as `thinking_tokens` bills the
reasoning tokens twice. The correct call is:

    non_thinking, reasoning = split_output_tokens(response.usage)
    tracker.add_usage(model, input_tokens=...,
                      output_tokens=non_thinking, thinking_tokens=reasoning)

Because our models price output and thinking identically, this keeps the TOTAL
byte-for-byte identical to the old (thinking=0) behaviour while making the
reported split correct. literary_echoes_agent.py already did this by hand via
its `non_think = out_tok - think_tok` line; this helper generalises it.

Anthropic is the opposite case and needs no helper: its SDK already folds
thinking into `output_tokens`, and our Claude call sites deliberately pass
`thinking_tokens=0` to avoid the same double-count.
"""

from typing import Any, Tuple

# Both nesting keys, so one helper serves chat.completions and responses.
_DETAIL_KEYS = ("completion_tokens_details", "output_tokens_details")


def _get(obj: Any, name: str) -> Any:
    """Attribute or mapping access — SDK objects use attributes, some test
    doubles and cached JSON payloads use dicts."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def reasoning_tokens(usage: Any) -> int:
    """Return reasoning/thinking tokens from an OpenAI usage object, or 0.

    Checks both nested detail shapes, then falls back to a flat attribute so a
    future SDK that promotes the field keeps working. Never raises.
    """
    if usage is None:
        return 0
    for key in _DETAIL_KEYS:
        value = _get(_get(usage, key), "reasoning_tokens")
        if value:
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0
    flat = _get(usage, "reasoning_tokens")
    try:
        return int(flat) if flat else 0
    except (TypeError, ValueError):
        return 0


def split_output_tokens(usage: Any) -> Tuple[int, int]:
    """Split an OpenAI completion count into (non_thinking_output, reasoning).

    The two returned values sum to the raw completion/output token count, so
    feeding them to CostTracker as output_tokens/thinking_tokens produces the
    same total as before while reporting an accurate split.
    """
    reasoning = reasoning_tokens(usage)
    total = _get(usage, "completion_tokens")
    if total is None:
        total = _get(usage, "output_tokens")
    try:
        total = int(total) if total else 0
    except (TypeError, ValueError):
        total = 0
    # Guard against a malformed response reporting more reasoning than output,
    # which would otherwise hand CostTracker a negative output count.
    if reasoning > total:
        return 0, total
    return total - reasoning, reasoning


__all__ = ["reasoning_tokens", "split_output_tokens"]
