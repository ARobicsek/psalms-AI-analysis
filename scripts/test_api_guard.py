"""
Unit tests for src/utils/api_guard.py — API quota exhaustion detection.

Tests that is_quota_exhaustion() correctly distinguishes permanent billing
errors from transient rate-limit errors.

Session 342.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.api_guard import is_quota_exhaustion, QuotaExhaustionError


# ---------------------------------------------------------------------------
# Test helpers — lightweight exception mocks
# ---------------------------------------------------------------------------

class MockOpenAIRateLimitError(Exception):
    """Mimics openai.RateLimitError for testing without the SDK."""
    pass


class MockAnthropicRateLimitError(Exception):
    """Mimics anthropic.RateLimitError for testing without the SDK."""
    pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_openai_insufficient_quota():
    """OpenAI 429 with 'insufficient_quota' → should detect as quota."""
    exc = Exception(
        "Error code: 429 - {'error': {'message': 'You exceeded your current quota, "
        "please check your plan and billing details. For more information on this "
        "error, read the docs: https://platform.openai.com/docs/guides/error-codes/"
        "api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': "
        "'insufficient_quota'}}"
    )
    is_q, provider = is_quota_exhaustion(exc)
    assert is_q, "Should detect OpenAI insufficient_quota"
    assert provider == "OpenAI", f"Expected OpenAI, got {provider}"
    print("  ✅ test_openai_insufficient_quota")


def test_openai_billing_hard_limit():
    """OpenAI billing hard limit → should detect as quota."""
    exc = Exception(
        "Error code: 429 - billing hard limit has been reached"
    )
    is_q, provider = is_quota_exhaustion(exc)
    assert is_q, "Should detect billing hard limit"
    assert provider == "OpenAI", f"Expected OpenAI, got {provider}"
    print("  ✅ test_openai_billing_hard_limit")


def test_transient_rate_limit_not_detected():
    """Regular TPM/RPM rate limit → should NOT detect as quota."""
    exc = Exception(
        "Error code: 429 - Rate limit reached for gpt-5.4 in organization org-xxx "
        "on tokens per min (TPM): Limit 300000, Used 299500, Requested 1200. "
        "Please try again in 200ms."
    )
    is_q, provider = is_quota_exhaustion(exc)
    assert not is_q, "Should NOT detect transient rate limit as quota"
    print("  ✅ test_transient_rate_limit_not_detected")


def test_anthropic_credit_balance():
    """Anthropic credit balance error → should detect as quota."""
    exc = Exception(
        "Error code: 429 - credit balance is too low to make this request"
    )
    is_q, provider = is_quota_exhaustion(exc)
    assert is_q, "Should detect Anthropic credit balance error"
    assert provider == "Anthropic", f"Expected Anthropic, got {provider}"
    print("  ✅ test_anthropic_credit_balance")


def test_google_resource_exhausted():
    """Google RESOURCE_EXHAUSTED with quota language → should detect."""
    exc = Exception(
        "400 RESOURCE_EXHAUSTED: Quota exceeded for aiplatform.googleapis.com/generate_content_requests"
    )
    is_q, provider = is_quota_exhaustion(exc)
    assert is_q, "Should detect Google RESOURCE_EXHAUSTED quota"
    assert provider == "Google", f"Expected Google, got {provider}"
    print("  ✅ test_google_resource_exhausted")


def test_generic_non_api_error():
    """Non-API error (e.g., FileNotFoundError) → should NOT detect."""
    exc = FileNotFoundError("No such file: prompt_template.txt")
    is_q, provider = is_quota_exhaustion(exc)
    assert not is_q, "Should NOT detect file error as quota"
    print("  ✅ test_generic_non_api_error")


def test_connection_error_not_detected():
    """Network error → should NOT detect as quota."""
    exc = ConnectionError("Connection reset by peer")
    is_q, provider = is_quota_exhaustion(exc)
    assert not is_q, "Should NOT detect connection error as quota"
    print("  ✅ test_connection_error_not_detected")


def test_quota_exhaustion_error_class():
    """QuotaExhaustionError wraps original exception correctly."""
    original = Exception("insufficient_quota")
    qe = QuotaExhaustionError("OpenAI", original)
    assert qe.provider == "OpenAI"
    assert qe.original_error is original
    assert "OpenAI" in str(qe)
    assert "insufficient_quota" in str(qe)
    print("  ✅ test_quota_exhaustion_error_class")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    print("\n=== API Guard Unit Tests ===\n")
    test_openai_insufficient_quota()
    test_openai_billing_hard_limit()
    test_transient_rate_limit_not_detected()
    test_anthropic_credit_balance()
    test_google_resource_exhausted()
    test_generic_non_api_error()
    test_connection_error_not_detected()
    test_quota_exhaustion_error_class()
    print(f"\n  All 8 tests passed ✅\n")
