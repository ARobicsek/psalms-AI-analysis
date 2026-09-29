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
        if name.startswith("gpt-"):
            # Session 388: OpenAI (GPT-5.6+) has ONE write rate, 1.25x, whatever the retention.
            assert row["cache_write_1h"] == pytest.approx(row["cache_write"]), name
        else:
            assert row["cache_write_1h"] == pytest.approx(2.00 * row["input"]), name


# Session 388. OpenAI's prompt-caching guide (read 2026-09-29): "Cache writes cost 1.25x
# the standard, uncached input-token rate" for GPT-5.6 and later; earlier models carry
# "no additional cache-write charge". A GPT-5.6+ row with cache_write 0 under-reports
# nearly every first-sight input token by 20% (a live probe: 7,466 of 7,469 were writes).
OPENAI_MODELS_BILLING_CACHE_WRITES = ("gpt-5.6-terra", "gpt-6-sol", "gpt-6-luna")


def test_openai_5_6_plus_rows_bill_cache_writes_older_rows_do_not():
    for name in OPENAI_MODELS_BILLING_CACHE_WRITES:
        assert PRICING[name]["cache_write"] == pytest.approx(1.25 * PRICING[name]["input"]), name
    for name in ("gpt-5.1", "gpt-5.4"):
        assert PRICING[name]["cache_write"] == 0.0, name


def test_gpt_6_sol_is_priced_at_its_standard_rate():
    """Session 388, regression. S384 encoded $2/$10 as a promo through 2026-11-21 over an
    assumed $4/$20; OpenAI's page lists $2/$10 as gpt-6-sol's STANDARD price and the
    promo note belongs to GPT-5.6 Sol. Pinned after the old expiry date."""
    r = resolve_pricing("gpt-6-sol", on_date=date(2026, 12, 1))
    assert (r["input"], r["cache_read"], r["output"]) == (2.00, 0.20, 10.00)
    assert "gpt-6-sol" not in INTRO_PRICING


def test_split_input_tokens_responses_and_chat_shapes():
    from src.utils.openai_usage import split_input_tokens
    responses = {"input_tokens": 7469,
                 "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 7466}}
    assert split_input_tokens(responses) == (3, 0, 7466)
    hit = {"input_tokens": 7469, "input_tokens_details": {"cached_tokens": 7466, "cache_write_tokens": 0}}
    assert split_input_tokens(hit) == (3, 7466, 0)
    chat = {"prompt_tokens": 1000, "prompt_tokens_details": {"cached_tokens": 600}}
    assert split_input_tokens(chat) == (400, 600, 0)          # older model: no writes field
    assert split_input_tokens(None) == (0, 0, 0)
    assert sum(split_input_tokens(responses)) == 7469


def test_a_cache_write_is_billed_at_1_25x_on_gpt_6_sol():
    t = CostTracker()
    t.add_usage("gpt-6-sol", input_tokens=0, cache_write_tokens=1_000_000)
    assert t.get_total_cost() == pytest.approx(2.50)
    assert price_tokens("gpt-6-sol", cache_write_tokens=1_000_000) == pytest.approx(2.50)


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
    for model in ("claude-opus-5-5", "claude-opus-5", "claude-opus-4-8", "claude-sonnet-4-6",
                  "claude-sonnet-5", "claude-fable-5", "claude-haiku-4-5",
                  "gpt-5.1", "gpt-5.4", "gpt-5.6-terra", "gemini-3.1-pro-preview"):
        assert resolve_pricing(model) is not None, f"{model} would be billed at $0.00"


# Models whose cache hit is NOT 0.1x input. Anthropic prices a hit on Fable 5.1 and
# Mythos 5.1 at 0.025x ($0.25/MTok against a $10 input) and footnotes it explicitly as
# the sole exception; every other model on every vendor we use is 0.1x.
#
# This is an EXCEPTION SET, not a relaxed assertion, and the distinction is the point.
# Session 377 wrote the 10% rule as a universal law because it was one at the time;
# Session 382 added a correct claude-fable-5-1 row and the test failed. The tempting
# fix -- drop the assert to "cache_read > 0" -- would have restored green while giving
# up the check that caught the original bug. So the multiplier stays asserted exactly,
# and a model that departs from it has to be NAMED here with its real multiplier.
#
# Session 383: Opus 5.5 is the second exception -- a hit is 0.05x ($0.20 against $4),
# also footnoted on the pricing page. "The sole exception" above was true for 29 days.
CACHE_READ_MULTIPLIER_EXCEPTIONS = {
    "claude-fable-5-1": 0.025,
    "claude-opus-5-5": 0.05,
}


def test_cached_input_is_never_free():
    """Session 377: gpt-5.1, gpt-5.4 and gemini-3.1-pro carried cache_read = 0.0 with
    a 'Not applicable' comment. All three vendors bill a cache hit at a fraction of
    input, so 0.0 would price a cached token at nothing the moment a caller wired it
    up. Session 382: the fraction is 0.10 everywhere except the models named in
    CACHE_READ_MULTIPLIER_EXCEPTIONS above."""
    for name, row in PRICING.items():
        if row["input"] == 0:
            continue
        mult = CACHE_READ_MULTIPLIER_EXCEPTIONS.get(name, 0.10)
        assert row["cache_read"] == pytest.approx(mult * row["input"]), (
            f"{name}: cache_read {row['cache_read']} is not {mult:.3%} of input "
            f"{row['input']}"
        )


def test_no_model_is_on_expired_introductory_pricing():
    """Session 382: the Sonnet 5 promo was made PERMANENT rather than expiring, so the
    durable row went stale and resolve_pricing() silently returned $3/$15 for 17 days.
    An override that has already expired can no longer affect any price, so its only
    remaining effect is to make a stale durable row LOOK deliberate. Leaving one in the
    table is therefore never correct -- either it still applies, or the durable row it
    was hiding has to be re-verified and the entry removed."""
    today = date.today()
    stale = {m: p["through"] for m, p in INTRO_PRICING.items() if p["through"] < today}
    assert not stale, (
        f"expired introductory pricing still in the table: {stale}. Re-verify each "
        f"model's DURABLE row against the vendor's live pricing page before deleting "
        f"the entry -- the promo may have become the standard price."
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


def test_intro_pricing_override_expires_on_its_own(monkeypatch):
    """Session 377's test of this mechanism was written against the live Sonnet 5
    promo. Session 382 removed that entry -- the promo was made permanent rather than
    expiring -- so the test is now run against a SYNTHETIC model.

    That is the durable shape. A test that reaches into INTRO_PRICING for a specific
    real model asserts two things at once: that the override mechanism works, and that
    a particular promotion is still running. The second is a fact about Anthropic's
    price list, it changes without warning, and when it changed this test failed for a
    reason that had nothing to do with the mechanism it was written to protect."""
    model = "claude-testmodel-1"
    promo_end = date(2026, 8, 31)
    monkeypatch.setitem(PRICING, model, {
        "input": 3.00, "output": 15.00, "thinking": 15.00,
        "cache_read": 0.30, "cache_write": 3.75, "cache_write_1h": 6.00,
    })
    monkeypatch.setitem(INTRO_PRICING, model, {
        "through": promo_end,
        "rates": {"input": 2.00, "output": 10.00, "thinking": 10.00,
                  "cache_read": 0.20, "cache_write": 2.50, "cache_write_1h": 4.00},
    })

    during = resolve_pricing(model, on_date=promo_end)
    after = resolve_pricing(model, on_date=date(2026, 9, 1))
    assert (during["input"], during["output"]) == (2.00, 10.00)
    assert (after["input"], after["output"]) == (3.00, 15.00)
    assert after == PRICING[model]   # no override left to apply


def test_sonnet_5_is_priced_at_its_permanent_rate():
    """Session 382, regression. Sonnet 5's $2/$10 stopped being a promotion on
    2026-08-10 and became the standard price; the scheduled $3/$15 increase was
    cancelled. Between 2026-09-01 and the fix, this table returned the stale durable
    $3/$15 on every date. Pinned on a date AFTER the old expiry so that reintroducing
    an override, or restoring the old durable row, fails here."""
    r = resolve_pricing("claude-sonnet-5", on_date=date(2026, 9, 1))
    assert (r["input"], r["output"]) == (2.00, 10.00)
    assert r == PRICING["claude-sonnet-5"], "no override should apply to Sonnet 5"
    # The cost argument that outlived the promo: cheaper on output than Sonnet 4.6,
    # which is the axis the micro analyst spends 89% of its money on.
    assert r["output"] < PRICING["claude-sonnet-4-6"]["output"]


def test_intro_rates_keep_the_anthropic_cache_multipliers():
    """Session 384: vendor-aware. The first non-Anthropic promo broke the old
    assumption that every promo carries Anthropic's 1.25x / 2x write markups. The
    write multipliers are checked on Claude promos only; the 10% cache read on every
    promo. (Session 388: the only non-Anthropic promo left is Gemini's, which bills
    caching by storage-time, so the cache_write == 0 branch still holds.)"""
    for name, promo in INTRO_PRICING.items():
        r = {**PRICING[name], **promo["rates"]}
        if name.startswith("claude-"):
            assert r["cache_write"] == pytest.approx(1.25 * r["input"]), name
            assert r["cache_write_1h"] == pytest.approx(2.00 * r["input"]), name
        else:
            assert r["cache_write"] == 0.0 and r["cache_write_1h"] == 0.0, name
        mult = CACHE_READ_MULTIPLIER_EXCEPTIONS.get(name, 0.10)
        assert r["cache_read"] == pytest.approx(mult * r["input"]), name


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
