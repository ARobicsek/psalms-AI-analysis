"""Session 393: deep-research cleanup against an independent check (no API calls)."""
import os
import time
from types import SimpleNamespace

import pytest

from src.agents import deep_research_cleaner as drc

REPORT = """## TOP FINDINGS

* **Old Deluder**: Ps 78:4-7 was the warrant for the 1647 Act.
* **Midpoint**: Ps 78:38 is the middle verse (Kiddushin 30a).

## 4. JEWISH PRACTICE

* Ma'ariv opens with v. 38 (Berakhot 4b).
"""

CHECK = "### 1. Old Deluder\n* **Verdict:** **WRONG** -- the Act cites no psalm.\n"

EDITS = """## Changes
1. [WRONG] **Top findings**: Old Deluder claim deleted.
<<<FIND
* **Old Deluder**: Ps 78:4-7 was the warrant for the 1647 Act.
===
>>>
2. [WRONG] **Jewish practice**: source corrected.
<<<FIND
* Ma'ariv opens with v. 38 (Berakhot 4b).
===
* Ma'ariv opens with v. 38 (Tur OC 237). [corrected by check]
>>>
3. [WRONG] **Nowhere**: a claim that is not in the report.
<<<FIND
this sentence is not in the report
===
x
>>>
"""


NO_CHANGES = "## Changes\nNo changes required."


class FakeClient:
    """Answers pass 1 with replies[0], the sweep with replies[1], and so on."""

    def __init__(self, replies=(EDITS, NO_CHANGES), n_in=12000, out=900, stop="end_turn"):
        self.calls = []
        outer = self
        replies = list(replies)

        class Messages:
            def count_tokens(self, **kw):
                return SimpleNamespace(input_tokens=n_in)

            def create(self, **kw):
                outer.calls.append(kw)
                reply = replies[min(len(outer.calls), len(replies)) - 1]
                return SimpleNamespace(content=[SimpleNamespace(type="text", text=reply)],
                                       usage=SimpleNamespace(input_tokens=n_in, output_tokens=out),
                                       stop_reason=stop)

        self.messages = Messages()


def _write(tmp_path, psalm=78, check=True):
    p = drc.paths(psalm, tmp_path)
    p.raw.write_text(REPORT, encoding="utf-8")
    if check:
        p.check.write_text(CHECK, encoding="utf-8")
    return p


def _age(path, seconds):
    t = time.time() - seconds
    os.utime(path, (t, t))


def test_demote_headings_puts_shallowest_at_level_three():
    out = drc.demote_headings("# A\n## B\n### C\ntext ## not a heading\n")
    assert out == "### A\n#### B\n##### C\ntext ## not a heading\n"
    assert drc.demote_headings("### A\n#### B\n") == "### A\n#### B\n"
    assert drc.demote_headings("no headings") == "no headings"


def test_output_budget_keeps_total_under_the_cap():
    for model in (drc.MODEL, drc.FALLBACK_MODEL, "gpt-6-luna"):
        price = drc.resolve_pricing(model)
        n_in = 15000
        b = drc.output_budget(n_in, max_cost=0.10, model=model)
        assert 0 < b <= drc.MAX_OUTPUT_TOKENS
        assert (n_in * price["input"] + b * price["output"]) / 1e6 <= 0.10
    assert drc.output_budget(200_000, max_cost=0.10) == 0  # input alone is over the cap


def test_default_is_one_sonnet_pass_at_low_effort(tmp_path):
    p = _write(tmp_path)
    client = FakeClient()
    r = drc.clean(78, tmp_path, client=client)
    assert r.status == "cleaned" and r.model == drc.MODEL == "claude-sonnet-5-5"
    text = p.clean.read_text(encoding="utf-8")
    assert "Old Deluder" not in text
    assert "(Tur OC 237). [corrected by check]" in text
    assert "Kiddushin 30a" in text  # untouched
    assert r.stats["applied"] == 2 and r.stats["not_found"] == 1
    log = p.log.read_text(encoding="utf-8")
    assert "NOT APPLIED" in log and "$" in log and "No sweep" in log
    assert len(client.calls) == 1
    assert client.calls[0]["model"] == drc.MODEL and client.calls[0]["system"] == drc.SYSTEM_PROMPT
    assert client.calls[0]["output_config"] == {"effort": "low"}
    assert r.cost < 0.10


def test_long_report_falls_back_to_haiku_with_the_sweep(tmp_path):
    _write(tmp_path)
    client = FakeClient(n_in=35000)  # leaves Sonnet < MIN_SINGLE_PASS_OUTPUT under $0.10
    r = drc.clean(78, tmp_path, client=client)
    assert r.status == "cleaned" and r.model == drc.FALLBACK_MODEL
    assert [c["model"] for c in client.calls] == [drc.FALLBACK_MODEL] * 2
    assert client.calls[1]["system"] == drc.SWEEP_PROMPT
    assert "output_config" not in client.calls[0]


def test_sweep_fixes_what_pass_one_missed(tmp_path):
    p = _write(tmp_path)
    p.raw.write_text(REPORT + "\n## 6. AFTERLIFE\n\n* Puritans cited Ps 78:4-7 for the 1647 Act.\n", encoding="utf-8")
    sweep = """## Changes
1. [WRONG] **Afterlife**: the body repeats the Old Deluder claim.
<<<FIND
* Puritans cited Ps 78:4-7 for the 1647 Act.
===
>>>
"""
    client = FakeClient(replies=(EDITS, sweep))
    r = drc.clean(78, tmp_path, client=client, model=drc.FALLBACK_MODEL)
    text = p.clean.read_text(encoding="utf-8")
    assert "1647" not in text
    sent = client.calls[1]["messages"][0]["content"]
    assert "Old Deluder" not in sent.split("</REPORT>")[0]  # the sweep reads the corrected report
    assert "Pass 2" in p.log.read_text(encoding="utf-8")


def test_two_passes_never_exceed_the_cap(tmp_path):
    _write(tmp_path)
    client = FakeClient(n_in=15000, out=900)
    r = drc.clean(78, tmp_path, client=client, max_cost=0.10, model=drc.FALLBACK_MODEL)
    price = drc.resolve_pricing(drc.FALLBACK_MODEL)
    first_worst = (15000 * price["input"] + client.calls[0]["max_tokens"] * price["output"]) / 1e6
    first_actual = (15000 * price["input"] + 900 * price["output"]) / 1e6
    second_worst = (15000 * price["input"] + client.calls[1]["max_tokens"] * price["output"]) / 1e6
    assert first_worst <= 0.05 + 1e-9                     # pass 1 may use at most half
    assert first_actual + second_worst <= 0.10 + 1e-9     # the sweep gets only what is left
    assert r.cost <= 0.10


def test_openai_model_uses_responses_and_bills_reasoning(tmp_path):
    p = _write(tmp_path)
    calls = []

    class Responses:
        def create(self, **kw):
            calls.append(kw)
            usage = SimpleNamespace(input_tokens=10000, output_tokens=1500,
                                    input_tokens_details=SimpleNamespace(cached_tokens=0, cache_write_tokens=0),
                                    output_tokens_details=SimpleNamespace(reasoning_tokens=500))
            return SimpleNamespace(output_text=EDITS, usage=usage, status="completed")

    class Tracker:
        def __init__(self):
            self.seen = []

        def add_usage(self, **kw):
            self.seen.append(kw)

    tracker = Tracker()
    r = drc.clean(78, tmp_path, client=SimpleNamespace(responses=Responses()), model="gpt-6-luna",
                  cost_tracker=tracker)
    assert r.status == "cleaned" and "Old Deluder" not in p.clean.read_text(encoding="utf-8")
    assert calls[0]["instructions"] == drc.SYSTEM_PROMPT and calls[0]["reasoning"] == {"effort": "low"}
    assert tracker.seen[0]["output_tokens"] == 1000 and tracker.seen[0]["thinking_tokens"] == 500
    assert 0 < r.cost < 0.01


def test_clean_skips_without_check_and_when_current(tmp_path):
    _write(tmp_path, check=False)
    assert drc.clean(78, tmp_path, client=FakeClient()).status == "skipped"
    p = _write(tmp_path)
    assert drc.clean(78, tmp_path, client=FakeClient()).status == "cleaned"
    client = FakeClient()
    assert drc.clean(78, tmp_path, client=client).status == "skipped"
    assert client.calls == []
    assert drc.clean(78, tmp_path, client=client, force=True).status == "cleaned"


def test_clean_refuses_over_budget_and_writes_nothing(tmp_path):
    p = _write(tmp_path)
    client = FakeClient(n_in=500_000)
    r = drc.clean(78, tmp_path, client=client)
    assert r.status == "refused" and client.calls == [] and not p.clean.exists()


def test_cut_off_edit_list_writes_nothing(tmp_path):
    p = _write(tmp_path)
    r = drc.clean(78, tmp_path, client=FakeClient(stop="max_tokens"))
    assert r.status == "failed" and not p.clean.exists()
    assert r.cost > 0  # what was spent is still reported


def test_needs_cleaning_follows_mtimes(tmp_path):
    p = _write(tmp_path)
    assert drc.needs_cleaning(78, tmp_path)
    p.clean.write_text("clean", encoding="utf-8")
    _age(p.raw, 100)
    _age(p.check, 100)
    assert not drc.needs_cleaning(78, tmp_path)
    p.check.write_text(CHECK + "more", encoding="utf-8")  # a newer check -> clean again
    _age(p.clean, 50)
    assert drc.needs_cleaning(78, tmp_path)


def test_load_for_bundle_prefers_current_clean_and_demotes(tmp_path):
    p = _write(tmp_path, check=False)
    text, kind = drc.load_for_bundle(78, tmp_path, auto_clean=False)
    assert kind == "unchecked" and text.startswith("### TOP FINDINGS")
    p.clean.write_text("## Clean\nbody", encoding="utf-8")
    _age(p.raw, 100)
    text, kind = drc.load_for_bundle(78, tmp_path, auto_clean=False)
    assert kind == "checked" and text == "### Clean\nbody"
    assert drc.load_for_bundle(5, tmp_path, auto_clean=False) == (None, "none")


def test_load_for_bundle_runs_cleanup_when_check_is_new(tmp_path, monkeypatch):
    _write(tmp_path)
    seen = {}

    def fake_clean(psalm, directory, cost_tracker=None, **kw):
        seen["called"] = psalm
        drc.paths(psalm, directory).clean.write_text("## cleaned", encoding="utf-8")
        return drc.CleanResult("cleaned")

    monkeypatch.setattr(drc, "clean", fake_clean)
    text, kind = drc.load_for_bundle(78, tmp_path)
    assert seen["called"] == 78 and kind == "checked" and text == "### cleaned"


def test_prompt_states_the_three_verdict_rules():
    s = drc.SYSTEM_PROMPT
    assert "[corrected by check]" in s and "[unconfirmed]" in s and "ADDENDUM wins" in s
    assert "<<<FIND" in s and "## Changes" in s


def test_bundle_label_and_flag_for_checked_research():
    from src.agents import research_assembler as ra
    assert "[corrected by check]" in ra.DEEP_RESEARCH_CHECKED_NOTE
    assert "[unconfirmed]" in ra.DEEP_RESEARCH_CHECKED_NOTE
    fields = ra.ResearchBundle.__dataclass_fields__
    assert "deep_research_checked" in fields and fields["deep_research_checked"].default is False
