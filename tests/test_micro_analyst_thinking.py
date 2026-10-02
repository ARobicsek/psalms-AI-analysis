"""Session 394: the micro analyst's request shapes on Sonnet 5.5 vs Sonnet 4.6, $0 (no API).

Sonnet 5.5 rejects thinking budgets (400) and treats an omitted `thinking` as adaptive ON, so
both stages need different requests than 4.6; and at effort max it once thought through all
128K tokens and wrote nothing, so an empty or cut-off answer must step effort DOWN, not repeat.
"""
import json
import logging
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.agents.micro_analyst import MicroAnalystV2
from src.utils.cost_tracker import CostTracker

DISCOVERIES = {"verse_discoveries": [{"verse_number": 1, "observations": "x"}],
               "interesting_questions": ["a", "b", "c"]}


class _Stop(Exception):
    pass


class FakeStream:
    def __init__(self, text, stop_reason="end_turn"):
        self.text, self.stop_reason = text, stop_reason

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __iter__(self):
        if self.text:
            yield SimpleNamespace(type="content_block_delta",
                                  delta=SimpleNamespace(type="text_delta", text=self.text))

    def get_final_message(self):
        return SimpleNamespace(stop_reason=self.stop_reason, stop_details=None,
                               usage=SimpleNamespace(input_tokens=10, output_tokens=20))


def make_agent(model, replies):
    """A MicroAnalystV2 with no DB, RAG or network: `replies` feed successive stream calls."""
    agent = object.__new__(MicroAnalystV2)
    agent.model = model
    agent.logger = logging.getLogger("test_micro")
    agent.cost_tracker = CostTracker()
    agent.commentary_mode = "all"
    agent.db = SimpleNamespace(get_psalm=lambda n: SimpleNamespace(verses=[1]))
    agent.rag_manager = SimpleNamespace(get_rag_context=lambda n: {},
                                        format_for_prompt=lambda ctx, include_framework=False: "")
    agent._format_psalm_with_lxx = lambda psalm, ctx: "TEXT"
    calls = []
    queue = list(replies)

    def stream(**kw):
        calls.append(kw)
        reply = queue.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    agent.client = SimpleNamespace(messages=SimpleNamespace(stream=stream))
    return agent, calls


MACRO = SimpleNamespace(to_markdown=lambda include_working_notes=False: "MACRO")


def test_default_model_is_sonnet_55():
    assert MicroAnalystV2.DEFAULT_MODEL == "claude-sonnet-5-5"
    assert "max" not in MicroAnalystV2.ADAPTIVE_EFFORT_LADDER


def test_stage1_sonnet55_adaptive_xhigh(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    agent, calls = make_agent("claude-sonnet-5-5", [FakeStream(json.dumps(DISCOVERIES))])
    assert agent._discovery_pass(1, MACRO, {}) == DISCOVERIES
    kw = calls[0]
    assert kw["thinking"] == {"type": "adaptive"}
    assert kw["output_config"] == {"effort": "xhigh"}
    assert kw["max_tokens"] == 128000


def test_stage1_sonnet46_unchanged(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    agent, calls = make_agent("claude-sonnet-4-6", [FakeStream(json.dumps(DISCOVERIES))])
    agent._discovery_pass(1, MACRO, {})
    kw = calls[0]
    assert kw["thinking"] == {"type": "enabled", "budget_tokens": 32768}
    assert kw["output_config"] == {"effort": "max"}
    assert kw["max_tokens"] == 65536


def test_stage1_empty_then_cut_off_steps_effort_down(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    agent, calls = make_agent("claude-sonnet-5-5", [
        FakeStream("", stop_reason="max_tokens"),        # thought through every token
        FakeStream("", stop_reason="end_turn"),          # empty for another reason
        FakeStream(json.dumps(DISCOVERIES)),
    ])
    assert agent._discovery_pass(1, MACRO, {}) == DISCOVERIES
    assert [c["output_config"]["effort"] for c in calls] == ["xhigh", "high", "medium"]
    assert all(c["thinking"] == {"type": "adaptive"} for c in calls)


def test_stage1_refusal_is_not_retried(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    agent, calls = make_agent("claude-sonnet-5-5", [FakeStream("", stop_reason="refusal")])
    with pytest.raises(RuntimeError, match="declined"):
        agent._discovery_pass(1, MACRO, {})
    assert len(calls) == 1


@pytest.mark.parametrize("model,thinking,effort", [
    ("claude-sonnet-5-5", {"type": "between_tools"}, "high"),
    ("claude-sonnet-4-6", None, None),
])
def test_stage2_thinking_off(model, thinking, effort):
    agent, calls = make_agent(model, [_Stop()])
    with pytest.raises(_Stop):
        agent._generate_research_requests(DISCOVERIES, 1)
    kw = calls[0]
    assert kw.get("thinking") == thinking
    assert (kw.get("output_config") or {}).get("effort") == effort
    assert kw["max_tokens"] == 32768
