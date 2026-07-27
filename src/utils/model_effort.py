"""
Single source of truth for the Anthropic `output_config.effort` level used by the
three deep-reasoning Claude agents (Macro Analyst, Synthesis Discovery, Master
Writer).

Before Session 367 each of those three modules carried its own copy of the same
`if "opus-4-7" in model ... elif "opus-4-8" in model ...` ladder. That is a silent
trap: a model string matching no branch falls through with NO `output_config` at
all and runs at whatever the API default happens to be, with nothing in the logs
to say so. Adding claude-opus-5 to three separate ladders would have repeated it.

Effort rationale:
  opus-4-7  -> "max"   (historical; Session 325 set it when 4.7 shipped)
  opus-4-8  -> "high"  (Session ~360; "max" showed diminishing returns)
  opus-5    -> "high"  (Session 367; deliberately matched to 4.8 so the A/B
                        isolates the model, not the effort setting. Anthropic's
                        migration guidance suggests sweeping xhigh/high/medium
                        once the like-for-like comparison is settled.)
  anything else -> None (older models such as Opus 4.6 reject output_config)
"""

from typing import Optional

# Longest/most-specific keys first so substring matching cannot mis-hit.
_EFFORT_BY_MODEL_SUBSTRING = (
    ("opus-4-7", "max"),
    ("opus-4-8", "high"),
    ("opus-5", "high"),
)


def effort_for(model: str) -> Optional[str]:
    """Return the effort level for `model`, or None if it takes no output_config.

    None is a meaningful answer (Opus 4.6 and earlier 400 on output_config), so
    callers should omit the key entirely rather than passing None to the API.
    """
    if not model:
        return None
    for needle, effort in _EFFORT_BY_MODEL_SUBSTRING:
        if needle in model:
            return effort
    return None


def apply_effort(stream_kwargs: dict, model: str, logger=None) -> dict:
    """Set stream_kwargs['output_config'] for `model`, mutating and returning it.

    Logs when a model gets no effort setting, so a future model string that
    matches nothing is visible in the run log instead of silently defaulting.
    """
    effort = effort_for(model)
    if effort is not None:
        stream_kwargs["output_config"] = {"effort": effort}
    elif logger is not None:
        logger.info(
            f"[effort] {model} matched no known effort tier; omitting "
            f"output_config and using the API default."
        )
    return stream_kwargs


__all__ = ["effort_for", "apply_effort"]
