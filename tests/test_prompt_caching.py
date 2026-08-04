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

import pytest

from src.utils.cost_tracker import PRICING, CostTracker


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
