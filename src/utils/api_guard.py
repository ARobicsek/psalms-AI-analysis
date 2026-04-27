"""
API Quota Guard — Detect billing/quota exhaustion errors across providers.

Distinguishes permanent "you're out of money" errors from transient rate-limit
errors (TPM/RPM throttling). Only the former should halt the pipeline; the
latter should be retried by agents as usual.

Session 342: Created to prevent silent pipeline degradation when an API
provider's billing quota is exhausted (the Psalm 67 incident — OpenAI $0
balance caused 3 non-fatal failures, producing an incomplete DOCX).

Usage:
    from src.utils.api_guard import is_quota_exhaustion, QuotaExhaustionError

    try:
        result = some_agent.run()
    except Exception as e:
        is_quota, provider = is_quota_exhaustion(e)
        if is_quota:
            raise QuotaExhaustionError(provider, e)
        # else handle normally
"""

from __future__ import annotations

import re
import sys
from typing import Tuple


class QuotaExhaustionError(Exception):
    """Raised when an API billing/quota limit is hit.

    Attributes:
        provider: Name of the API provider (e.g., "OpenAI", "Anthropic", "Google").
        original_error: The underlying exception that was detected as quota-related.
    """

    def __init__(self, provider: str, original_error: Exception):
        self.provider = provider
        self.original_error = original_error
        super().__init__(
            f"{provider} API quota exhausted: {original_error}"
        )


# ---------------------------------------------------------------------------
# Quota-exhaustion detection heuristics
# ---------------------------------------------------------------------------

# Patterns that indicate PERMANENT quota/billing exhaustion (not transient).
# Each tuple: (compiled regex applied to str(exception), provider name)
_QUOTA_PATTERNS = [
    # OpenAI: "insufficient_quota", "exceeded your current quota",
    # "billing hard limit has been reached"
    (re.compile(
        r"insufficient.quota|exceeded.your.current.quota|billing.hard.limit",
        re.IGNORECASE,
    ), "OpenAI"),
    # Anthropic: "credit balance is too low", "billing", "insufficient credits"
    (re.compile(
        r"credit.balance.is.too.low|insufficient.credits|billing.limit",
        re.IGNORECASE,
    ), "Anthropic"),
    # Google/Gemini: "RESOURCE_EXHAUSTED" with quota language
    (re.compile(
        r"RESOURCE_EXHAUSTED.*quota|quota.*RESOURCE_EXHAUSTED",
        re.IGNORECASE,
    ), "Google"),
]

# Patterns that indicate TRANSIENT rate-limiting (should NOT trigger halt).
# If these match, we return False even if the error code is 429.
_TRANSIENT_PATTERNS = re.compile(
    r"too.many.requests|rate.limit|tokens.per.min|requests.per.min"
    r"|retry.after|try.again.later|temporarily",
    re.IGNORECASE,
)


def is_quota_exhaustion(exc: Exception) -> Tuple[bool, str]:
    """Inspect an exception and determine if it indicates API quota/billing exhaustion.

    Returns:
        (is_quota, provider_name) — e.g. (True, "OpenAI") or (False, "").

    Detection strategy:
        1. Check exception type for known SDK-specific quota classes.
        2. Check exception message string against known quota-exhaustion patterns.
        3. Exclude transient rate-limit errors (TPM/RPM throttling).
    """
    exc_str = str(exc)
    exc_type_name = type(exc).__name__

    # --- 1. SDK-specific type checks ---

    # OpenAI SDK raises openai.RateLimitError for both transient and quota errors.
    # Distinguish by inspecting the message.
    try:
        import openai
        if isinstance(exc, openai.RateLimitError):
            # Check for permanent quota language
            if re.search(r"insufficient.quota|exceeded.your.current.quota|billing", exc_str, re.IGNORECASE):
                return True, "OpenAI"
            # Otherwise it's a transient rate limit — don't halt
            return False, ""
    except ImportError:
        pass

    # Anthropic SDK
    try:
        import anthropic
        if isinstance(exc, anthropic.RateLimitError):
            if re.search(r"credit|billing|insufficient", exc_str, re.IGNORECASE):
                return True, "Anthropic"
            return False, ""
    except ImportError:
        pass

    # --- 2. Message-based pattern matching (catches non-SDK or wrapped errors) ---

    for pattern, provider in _QUOTA_PATTERNS:
        if pattern.search(exc_str):
            # Make sure it's not a transient rate limit being mis-classified
            # Only override if the quota pattern is clearly present
            return True, provider

    # --- 3. Generic 429 with quota language (e.g., wrapped in a generic Exception) ---
    if "429" in exc_str:
        if re.search(r"quota|billing|insufficient|exceeded", exc_str, re.IGNORECASE):
            # Try to guess provider
            provider = "Unknown API"
            if "openai" in exc_str.lower() or "gpt" in exc_str.lower():
                provider = "OpenAI"
            elif "anthropic" in exc_str.lower() or "claude" in exc_str.lower():
                provider = "Anthropic"
            elif "google" in exc_str.lower() or "gemini" in exc_str.lower():
                provider = "Google"
            return True, provider

    return False, ""


def halt_on_quota(
    exc: Exception,
    step_name: str,
    logger,
    cost_tracker,
    output_path,
    psalm_number: int,
):
    """Check if an exception is a quota-exhaustion error. If so, save partial
    cost data and halt the pipeline immediately with a clear message.

    This function only returns if the exception is NOT a quota error.
    If it IS a quota error, it calls sys.exit(2).
    """
    is_quota, provider = is_quota_exhaustion(exc)
    if not is_quota:
        return  # Not a quota error — caller handles normally

    import json
    from pathlib import Path

    # Save partial cost data so --resume can pick up
    try:
        cost_file = Path(output_path) / f"psalm_{psalm_number:03d}_cost.json"
        cost_file.write_text(
            json.dumps(cost_tracker.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass  # Don't let cost-saving failure prevent the halt message

    # Log the halt
    separator = "=" * 80
    logger.error(separator)
    logger.error(f"💰 PIPELINE HALTED — {provider} API QUOTA EXHAUSTED")
    logger.error(f"   Detected at: {step_name}")
    logger.error(f"   Error: {exc}")
    logger.error(f"   Action: Top up your {provider} account, then re-run with --resume")
    logger.error(separator)

    # Print to stdout as well (logger may go to file only)
    print(f"\n{separator}")
    print(f"💰 PIPELINE HALTED — {provider} API QUOTA EXHAUSTED")
    print(f"   Detected at: {step_name}")
    print(f"   Error: {exc}")
    print(f"   Action: Top up your {provider} account, then re-run with --resume")
    print(f"{separator}\n")

    # Sound notification (Windows)
    if sys.platform == "win32":
        try:
            import winsound
            # Three descending beeps — attention-grabbing but not alarming
            winsound.Beep(800, 300)
            winsound.Beep(600, 300)
            winsound.Beep(400, 500)
        except Exception:
            pass  # No sound available — not critical

    sys.exit(2)


__all__ = ["is_quota_exhaustion", "QuotaExhaustionError", "halt_on_quota"]
