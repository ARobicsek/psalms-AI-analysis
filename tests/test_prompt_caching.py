"""
Tests for prompt-caching pricing and the citation verifier's rolling cache breakpoint.

Session 374. Two independent things are covered here:

1. `cost_tracker.PRICING` carries BOTH Anthropic cache-write rates. The table used
   to hold only the 5-minute rate (1.25x input); a caller passing ttl="1h" is
   billed 2x and would have been reported at 1.25x -- a silent 60% under-report of
   the write, the same class of error as the Session-373 pricing audit.

2. `verify_citations_tooluse` advances a cache breakpoint through its tool-use
   loop. The two static breakpoints cover the system prompt and the commentary;
   without a rolling one, every turn re-pays full input price on the whole
   accumulated lookup history.
"""

import copy
import sys
import types
from datetime import date

import pytest

from src.utils.cost_tracker import (
    INTRO_PRICING,
    PRICING,
    CostTracker,
    price_tokens,
    resolve_pricing,
)


# ---------------------------------------------------------------------------
# 1. Pricing
# ---------------------------------------------------------------------------

def test_every_row_carries_both_cache_write_rates():
    for name, row in PRICING.items():
        assert "cache_write" in row, f"{name} missing the 5-minute write rate"
        assert "cache_write_1h" in row, f"{name} missing the 1-hour write rate"


def test_anthropic_multipliers_are_1_25x_and_2x():
    """Anthropic's documented multipliers, asserted against each row's own input
    price so a future price change can't drift the cache rows out of step."""
    for name, row in PRICING.items():
        if name.startswith("gemini") or row["cache_write"] == 0:
            continue  # non-Anthropic, or caching not applicable
        assert row["cache_write"] == pytest.approx(1.25 * row["input"]), name
        assert row["cache_write_1h"] == pytest.approx(2.00 * row["input"]), name


def test_one_hour_write_is_priced_at_2x_not_1_25x():
    t = CostTracker()
    t.add_usage("claude-opus-5", cache_write_1h_tokens=1_000_000)
    assert t.get_total_cost() == pytest.approx(10.00)  # not 6.25


def test_five_minute_write_path_unchanged():
    t = CostTracker()
    t.add_usage("claude-opus-5", cache_write_tokens=1_000_000)
    assert t.get_total_cost() == pytest.approx(6.25)


def test_existing_callers_cost_the_same_as_before():
    """No caller passes the new argument yet; their totals must not move."""
    t = CostTracker()
    t.add_usage("claude-haiku-4-5-20251001", input_tokens=50_000, output_tokens=3_000,
                cache_read_tokens=120_000, cache_write_tokens=16_000)
    expected = (50_000 / 1e6 * 1.00 + 3_000 / 1e6 * 5.00
                + 120_000 / 1e6 * 0.10 + 16_000 / 1e6 * 1.25)
    assert t.get_total_cost() == pytest.approx(expected)


def test_row_without_the_1h_rate_falls_back_to_2x_not_free():
    """A model row added later without the 1-hour key must not price it at zero --
    an unpriced write is the under-report this row exists to prevent."""
    import src.utils.cost_tracker as ct
    ct.PRICING["_test-model"] = {"input": 5.0, "output": 25.0, "thinking": 25.0,
                                 "cache_read": 0.5, "cache_write": 6.25}
    try:
        t = CostTracker()
        t.add_usage("_test-model", cache_write_1h_tokens=1_000_000)
        assert t.get_total_cost() == pytest.approx(10.00)
    finally:
        del ct.PRICING["_test-model"]


def test_new_field_is_reported():
    t = CostTracker()
    t.add_usage("claude-opus-5", cache_write_1h_tokens=1234)
    assert t.to_dict()["claude-opus-5"]["cache_write_1h_tokens"] == 1234
    assert "Cache Write Tokens (1h): 1,234" in t.get_summary()


# ---------------------------------------------------------------------------
# 1b. Session 377 pricing audit
# ---------------------------------------------------------------------------

def test_every_model_the_pipeline_can_select_is_priced():
    """The models named as a DEFAULT_MODEL anywhere in the pipeline, plus the two
    swap candidates the A/B docs discuss. A missing row reports $0.00, not an error."""
    for model in ("claude-opus-5", "claude-opus-4-8", "claude-sonnet-4-6",
                  "claude-sonnet-5", "claude-fable-5", "claude-haiku-4-5",
                  "gpt-5.1", "gpt-5.4", "gpt-5.6-terra", "gemini-3.1-pro-preview"):
        assert resolve_pricing(model) is not None, f"{model} would be billed at $0.00"


def test_cached_input_is_never_free():
    """Session 377: gpt-5.1, gpt-5.4 and gemini-3.1-pro carried cache_read = 0.0 with
    a 'Not applicable' comment. All three vendors bill a cache hit at 10% of input,
    so 0.0 would price a cached token at nothing the moment a caller wired it up."""
    for name, row in PRICING.items():
        if row["input"] == 0:
            continue
        assert row["cache_read"] == pytest.approx(0.10 * row["input"]), (
            f"{name}: cache_read {row['cache_read']} is not 10% of input {row['input']}"
        )


def test_unpriced_model_is_reported_not_swallowed():
    t = CostTracker()
    t.add_usage("claude-opus-9-imaginary", input_tokens=1_000_000, output_tokens=500_000)
    assert t.get_total_cost() == 0.0            # still zero -- but now it SAYS so
    assert "claude-opus-9-imaginary" in t.unpriced_models
    assert "*** FLOOR, NOT ACTUAL ***" in t.get_summary()
    assert t.to_dict()["unpriced_models"] == ["claude-opus-9-imaginary"]


def test_priced_run_carries_no_unpriced_marker():
    """The key is absent on a normal run, so every existing cost JSON keeps its shape."""
    t = CostTracker()
    t.add_usage("claude-opus-5", input_tokens=1000, output_tokens=100)
    assert "unpriced_models" not in t.to_dict()
    assert "FLOOR" not in t.get_summary()


def test_sonnet_5_intro_pricing_expires_on_its_own():
    """The row holds the DURABLE rates and INTRO_PRICING overrides them until the
    promo ends. Encoding it the other way round is what goes silently stale."""
    promo_end = INTRO_PRICING["claude-sonnet-5"]["through"]
    during = resolve_pricing("claude-sonnet-5", on_date=promo_end)
    after = resolve_pricing("claude-sonnet-5", on_date=date(promo_end.year, 9, 1))
    assert (during["input"], during["output"]) == (2.00, 10.00)
    assert (after["input"], after["output"]) == (3.00, 15.00)
    assert after == PRICING["claude-sonnet-5"]   # no override left to apply


def test_intro_rates_keep_the_anthropic_cache_multipliers():
    for name, promo in INTRO_PRICING.items():
        r = promo["rates"]
        assert r["cache_write"] == pytest.approx(1.25 * r["input"]), name
        assert r["cache_write_1h"] == pytest.approx(2.00 * r["input"]), name
        assert r["cache_read"] == pytest.approx(0.10 * r["input"]), name


def test_price_tokens_matches_the_tracker_on_the_same_call():
    """The helper that replaced figurative_curator's private table must agree with
    the run total, which is the whole point of there being one table."""
    args = dict(input_tokens=12_345, output_tokens=678, thinking_tokens=910)
    t = CostTracker()
    t.add_usage("gpt-5.6-terra", **args)
    assert price_tokens("gpt-5.6-terra", **args) == pytest.approx(t.get_total_cost())


def test_price_tokens_refuses_an_unpriced_model():
    """Unlike the tracker (which must not destroy a paid-for run's report), the
    single-call helper has no reason to return a wrong number."""
    with pytest.raises(KeyError):
        price_tokens("gpt-9-imaginary", input_tokens=100)


def test_figurative_curator_no_longer_carries_its_own_rates():
    """Session 377 removed a duplicate table that said $2.50/$15.00 for a model
    costing $2.00/$12.00. Re-adding one is how this bug came back twice already."""
    import inspect
    import src.agents.figurative_curator as fc
    source = inspect.getsource(fc)
    assert "GPT54_INPUT_COST_PER_M" not in source
    assert "COST_PER_M = " not in source


# ---------------------------------------------------------------------------
# 2. Rolling cache breakpoint in the citation verifier's tool-use loop
# ---------------------------------------------------------------------------

class _Blk:
    def __init__(self, type, name=None, id=None, input=None):
        self.type, self.name, self.id, self.input = type, name, id, input


class _Usage:
    input_tokens = 10
    output_tokens = 5
    cache_read_input_tokens = 0
    cache_creation_input_tokens = 0


class _Resp:
    def __init__(self, content, stop_reason="tool_use"):
        self.content, self.stop_reason, self.usage = content, stop_reason, _Usage()


def _lookup(tid, verse):
    return _Blk("tool_use", "lookup_verse", tid,
                {"book": "Genesis", "chapter": 1, "verse": verse})


class _FakeVerse:
    def __init__(self, n):
        self.hebrew, self.reference = f"verse text {n}", f"Genesis 1:{n}"


class _FakeDB:
    def __init__(self, *a, **kw): pass
    def get_verse(self, book, ch, v): return _FakeVerse(v)
    def get_psalm(self, n): return None
    def close(self): pass


@pytest.fixture
def tooluse_transcript(monkeypatch):
    """Run the real loop against a scripted client.

    Returns `.requests` (a deep copy of `messages` as each turn sent it) and
    `.live` (a reference to the list the loop keeps mutating, so state appended
    after the final request is still inspectable).
    """
    sent = []
    live = []
    script = [
        _Resp([_lookup("t1", 1), _lookup("t2", 2)]),
        _Resp([_lookup("t3", 3), _lookup("t4", 4)]),
        _Resp([_lookup("t5", 5)]),
        _Resp([_Blk("tool_use", "report_citations", "t6",
                    {"citations": [], "total_found": 0})]),
    ]

    class _Msgs:
        def create(self, **kw):
            sent.append(copy.deepcopy(kw["messages"]))
            live[:] = [kw["messages"]]  # same object the loop keeps appending to
            return script[len(sent) - 1]

    class _Anthropic:
        def __init__(self, **kw):
            self.messages = _Msgs()

    stub = types.ModuleType("anthropic")
    stub.Anthropic = _Anthropic
    monkeypatch.setitem(sys.modules, "anthropic", stub)

    import src.data_sources.tanakh_database as tdb
    monkeypatch.setattr(tdb, "TanakhDatabase", _FakeDB)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "stub")

    from src.utils.scripture_verifier import verify_citations_tooluse
    verify_citations_tooluse("Some commentary text.", psalm_number=71, haiku_filter=False)
    return types.SimpleNamespace(requests=sent, live=live[0])


def _breakpoints(messages):
    """(count of breakpoints in `messages`, index of the message holding the
    rolling one)."""
    total, rolling_at = 0, None
    for i, m in enumerate(messages):
        if not isinstance(m["content"], list):
            continue
        for b in m["content"]:
            if isinstance(b, dict) and "cache_control" in b:
                total += 1
                if b.get("type") == "tool_result":
                    rolling_at = i
    return total, rolling_at


def test_breakpoint_count_stays_within_the_api_limit(tooluse_transcript):
    """The API allows 4; the system prompt holds one that `messages` can't see."""
    for turn, messages in enumerate(tooluse_transcript.requests, 1):
        total, _ = _breakpoints(messages)
        assert total + 1 <= 4, f"turn {turn} would send {total + 1} breakpoints"


def test_first_turn_has_only_the_static_breakpoint(tooluse_transcript):
    total, rolling_at = _breakpoints(tooluse_transcript.requests[0])
    assert (total, rolling_at) == (1, None)


def test_rolling_breakpoint_advances_and_never_duplicates(tooluse_transcript):
    for turn, messages in enumerate(tooluse_transcript.requests[1:], start=2):
        total, rolling_at = _breakpoints(messages)
        assert total == 2, f"turn {turn}: expected static + exactly one rolling, got {total}"
        assert rolling_at == len(messages) - 1, (
            f"turn {turn}: rolling breakpoint stale at message {rolling_at}")
        newest = messages[-1]["content"]
        assert "cache_control" in newest[-1]
        assert all("cache_control" not in b for b in newest[:-1])


def test_final_turn_results_are_not_marked(tooluse_transcript):
    """Marking the final turn would pay a cache write for an entry no request ever
    reads. The loop breaks after report_citations, so those results never appear in
    any request -- they are only visible on the live message list."""
    final_results = tooluse_transcript.live[-1]
    assert final_results["role"] == "user"
    assert all("cache_control" not in b for b in final_results["content"]), (
        "the final turn's tool_results were marked; that write is never read")

    # ...and the breakpoint that IS live is the one from the previous turn.
    total, _ = _breakpoints(tooluse_transcript.live)
    assert total == 2
