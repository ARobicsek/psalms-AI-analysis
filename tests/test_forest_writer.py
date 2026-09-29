"""Session 387: the two-call forest writer in production, per-stage cost, the editors' report.

The prompt texts are pinned to what the author read and approved in Sessions 384-386, and
the two-call path is exercised end to end against a fake Anthropic client ($0).
"""

import ast
import json
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.agents import forest_writer as fw  # noqa: E402
from src.utils.cost_tracker import CostTracker  # noqa: E402

TRIALS = ROOT / "archive" / "psalm_76_S384_essay_trials" / "prompts"


def _script_constant(path: Path, name: str) -> str:
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)


# ---------------------------------------------------------------------------
# The approved texts
# ---------------------------------------------------------------------------

def test_essay_instructions_for_ps76_are_the_approved_p1_text_byte_for_byte():
    inputs = (TRIALS / "inputs_block.txt").read_text(encoding="utf-8")
    assert len(fw.commentator_names(inputs)) == 11
    assert fw.essay_instructions(76, inputs) == (TRIALS / "p1_instructions.txt").read_text(encoding="utf-8")


def test_verse_instructions_are_the_s386_text_byte_for_byte():
    s385 = _script_constant(ROOT / "scripts" / "s385_two_call_writer.py", "VERSE_INSTRUCTIONS")
    assert fw.verse_instructions(13) == s385.replace("{n_verses}", "13").replace("{echo_target}", "10")
    assert "READER QUESTIONS" not in fw.VERSE_INSTRUCTIONS.upper().replace("NEVER BEGIN", "")


def test_essay_instructions_generalise_to_another_psalm():
    inputs = "### 77:2 — Rashi\nx\n### 77:3 — Radak\ny\n### 77:3 — Rashi\nz\n"
    text = fw.essay_instructions(77, inputs)
    assert "about Psalm 77:" in text and "; two traditional commentators" in text
    assert "The two traditional commentators" in text and "76" not in text and "{" not in text


def test_inputs_block_is_the_v4_prompts_inputs_section():
    from src.agents.master_editor import MASTER_WRITER_PROMPT_V4
    prompt = MASTER_WRITER_PROMPT_V4.format(
        psalm_number=77, psalm_text="### Verse 1\n**Hebrew:** א\n**English:** a\n", macro_analysis="M",
        micro_analysis="m", research_bundle="R", phonetic_section="P", curated_insights="I",
        reader_questions="Q")
    block = fw.extract_inputs_block(prompt)
    assert block.startswith("## ═") and "## YOUR INPUTS" in block and "YOUR TASK" not in block
    assert "GROUND RULES" not in block and block.rstrip().endswith("---")
    assert fw.psalm_verse_numbers(block) == [1]


def test_inputs_block_matches_the_s384_cut_of_the_saved_ps76_prompt():
    saved = ROOT / "output/psalm_76/_opus55_B/_debug/master_writer_v4_prompt_psalm_76.txt"
    if not saved.exists():
        pytest.skip("the S383 arm-B prompt is a local output, not in the repo")
    assert fw.extract_inputs_block(saved.read_text(encoding="utf-8")) == \
        (TRIALS / "inputs_block.txt").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Output checks
# ---------------------------------------------------------------------------

GOOD_REST = (f"{fw.LIT_MARKER}\n\n#### Full psalm\nRecited on Sukkot (v. 3).\n\n### VERSE COMMENTARY\n\n"
             "**Verse 1**\n\nלַמְנַצֵּחַ.\n\n> For the leader.\n\nNote.\n\n"
             "**Verses 2–3**\n\nא.\n\n> One.\n\nב.\n\n> Two.\n\nNote.\n")


def test_check_structure_accepts_a_well_formed_response():
    assert fw.check_structure(GOOD_REST, [1, 2, 3]) == []


def test_check_structure_flags_what_breaks_the_guide():
    bad = GOOD_REST.replace("Recited on Sukkot (v. 3).", "**Verse 3** is recited on Sukkot.")
    assert any("liturgical section" in p for p in fw.check_structure(bad, [1, 2, 3]))
    assert any("do not cover" in p for p in fw.check_structure(GOOD_REST, [1, 2, 3, 4]))
    assert any("marker" in p for p in fw.check_structure(GOOD_REST.replace(fw.LIT_MARKER, ""), [1, 2, 3]))
    assert any("reader-questions" in p for p in
               fw.check_structure(GOOD_REST + "\n### REFINED READER QUESTIONS\n1. x\n", [1, 2, 3]))


def test_check_essay():
    assert fw.check_essay("\n### INTRODUCTION ESSAY\n\nText.") == []
    assert fw.check_essay("# Psalm 77\n\nText.")
    assert fw.check_essay("### INTRODUCTION ESSAY\nx\n### VERSE COMMENTARY\n")


def test_replayable_keeps_thinking_signatures_and_drops_extras():
    content = [{"type": "thinking", "thinking": "t", "signature": "sig", "extra": 1},
               {"type": "text", "text": "essay", "citations": None}]
    assert fw.replayable(content) == [{"type": "thinking", "thinking": "t", "signature": "sig"},
                                      {"type": "text", "text": "essay"}]


# ---------------------------------------------------------------------------
# The two calls, end to end, against a fake client
# ---------------------------------------------------------------------------

class _Block(SimpleNamespace):
    def to_dict(self):
        return dict(vars(self))


def _msg(text, thinking, usage):
    return SimpleNamespace(content=[_Block(type="thinking", thinking=thinking, signature="sig-" + thinking),
                                    _Block(type="text", text=text)],
                           usage=SimpleNamespace(cache_creation=None, **usage), stop_reason="end_turn")


class _FakeClient:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []
        self.messages = self

    def stream(self, **kw):
        self.calls.append(kw)
        reply = self.replies.pop(0)

        class _S:
            def __enter__(s):
                return s

            def __exit__(s, *a):
                return False

            def get_final_message(s):
                return reply
        return _S()

    def create(self, **kw):  # keep-alive
        raise AssertionError("no keep-alive expected in a fast test")


def test_forest_writer_two_calls_end_to_end(tmp_path, monkeypatch):
    import src.utils.debug_paths as dp
    from src.agents.master_editor import MASTER_WRITER_PROMPT_V4, MasterEditor

    monkeypatch.chdir(tmp_path)
    (tmp_path / "output" / "debug").mkdir(parents=True)
    monkeypatch.setattr(dp, "OUTPUT_ROOT", tmp_path / "output")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")

    ed = MasterEditor(main_model="claude-opus-5-5", cost_tracker=CostTracker())
    assert ed.writer_mode == "forest"
    psalm_text = "".join(f"### Verse {n}\n**Hebrew:** א\n**English:** e\n\n" for n in (1, 2, 3))
    prompt = MASTER_WRITER_PROMPT_V4.format(
        psalm_number=77, psalm_text=psalm_text, macro_analysis="M", micro_analysis="m",
        research_bundle="### 77:2 — Rashi\nx\n", phonetic_section="P", curated_insights="I",
        reader_questions="Q")
    essay = "### INTRODUCTION ESSAY\n\nThe essay."
    fake = _FakeClient([
        _msg(essay, "essay thoughts", dict(input_tokens=10, output_tokens=5000,
                                           cache_creation_input_tokens=180000, cache_read_input_tokens=0)),
        _msg(GOOD_REST, "verse thoughts", dict(input_tokens=6000, output_tokens=40000,
                                               cache_creation_input_tokens=0, cache_read_input_tokens=180000)),
    ])
    ed.anthropic_client = fake
    res = ed._call_forest_writer("claude-opus-5-5", prompt, 77, "master_writer_v4")

    c1, c2 = fake.calls
    assert c1["output_config"] == {"effort": "high"} and c1["thinking"]["display"] == "summarized"
    assert c2["messages"][0] == c1["messages"][0], "call 2 must open with call 1's exact first turn"
    assert c1["messages"][0]["content"][-1]["cache_control"] == {"type": "ephemeral"}
    assert c2["messages"][1]["content"][0] == {"type": "thinking", "thinking": "essay thoughts",
                                               "signature": "sig-essay thoughts"}
    assert "LITURGY AND VERSE COMMENTARY" in c2["messages"][2]["content"][0]["text"]
    assert "YOUR TASK: WRITE THE COMMENTARY" not in json.dumps(c1["messages"], ensure_ascii=False)

    assert res["introduction"].startswith("The essay.") and fw.LIT_MARKER in res["introduction"]
    assert res["verse_commentary"].startswith("**Verse 1**")
    tel = res["writer_telemetry"]
    assert tel["structure_problems"] == [] and [c["label"] for c in tel["calls"]] == ["essay", "verses"]
    u = ed.cost_tracker.usage_by_model["claude-opus-5-5"]
    assert (u.cache_write_tokens, u.cache_read_tokens, u.output_tokens) == (180000, 180000, 45000)

    out = tmp_path / "output" / "psalm_77"
    assert (out / "psalm_077_master_writer_v4_forest_essay_thinking.txt").read_text(encoding="utf-8") == "essay thoughts"
    assert (out / "psalm_077_master_writer_v4_forest_verses_thinking.txt").read_text(encoding="utf-8") == "verse thoughts"
    assert json.loads((out / "psalm_077_forest_essay_call.json").read_text(encoding="utf-8"))["verse_call_done"]


def test_forest_writer_refuses_effort_max(monkeypatch):
    from src.agents.master_editor import MasterEditor
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    ed = MasterEditor(main_model="claude-opus-4-7", cost_tracker=CostTracker())  # opus-4-7 maps to max
    with pytest.raises(ValueError, match="effort max"):
        ed._call_forest_writer("claude-opus-4-7", "irrelevant", 77, "master_writer_v4")


def test_writer_mode_is_validated(monkeypatch):
    from src.agents.master_editor import MasterEditor
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    with pytest.raises(ValueError):
        MasterEditor(main_model="claude-opus-5-5", writer_mode="one-call")


def test_opus_defaults_are_opus_5_5():
    from src.agents.macro_analyst import MacroAnalyst
    from src.agents.synthesis_discovery import DEFAULT_MODEL
    from src.utils.model_effort import effort_for
    assert MacroAnalyst.DEFAULT_MODEL == DEFAULT_MODEL == "claude-opus-5-5"
    assert effort_for("claude-opus-5-5") == "high"  # its API default is medium
    src = (ROOT / "scripts" / "run_enhanced_pipeline.py").read_text(encoding="utf-8")
    assert 'master_editor_model: str = "claude-opus-5-5"' in src and 'default="claude-opus-5-5"' in src


# ---------------------------------------------------------------------------
# Cost: non-token charges and per-stage records
# ---------------------------------------------------------------------------

def test_charges_are_in_every_total():
    t = CostTracker()
    t.add_usage("claude-opus-5-5", input_tokens=1_000_000)
    base = t.get_total_cost()
    t.add_charge("web search", 0.13, model="gpt-6-luna", detail="13 searches")
    assert t.get_total_cost() == pytest.approx(base + 0.13)
    assert t.to_dict()["charges"][0]["usd"] == 0.13
    assert "NON-TOKEN CHARGES" in t.get_summary()


def test_cost_json_shape_is_unchanged_without_charges_or_stages():
    t = CostTracker()
    t.add_usage("claude-opus-5-5", input_tokens=10)
    assert "charges" not in t.to_dict() and "stages" not in t.to_dict()


def test_record_stage_is_a_delta_and_flags_promo_prices(monkeypatch):
    import src.utils.cost_tracker as ct
    t = CostTracker()
    t.add_usage("gpt-6-sol", input_tokens=500_000)
    snap = t.snapshot()
    t.add_usage("gpt-6-sol", input_tokens=1_000_000, output_tokens=100_000)
    t.add_usage("claude-opus-5-5", output_tokens=1_000_000)
    t.add_charge("web search", 0.05)
    monkeypatch.setattr(ct, "date", SimpleNamespace(today=lambda: date(2026, 10, 1), max=date.max))
    st = t.record_stage("fact check", snap)
    sol = st["models"]["gpt-6-sol"]
    assert sol["input_tokens"] == 1_000_000 and sol["call_count"] == 1
    assert sol["cost_usd"] == pytest.approx(2.0 + 1.0)          # promo $2 / $10
    assert sol["promo_through"] == "2026-11-21"
    assert sol["cost_usd_at_durable_rates"] > sol["cost_usd"]
    assert "promo_through" not in st["models"]["claude-opus-5-5"]
    assert st["cost_usd"] == pytest.approx(sol["cost_usd"] + st["models"]["claude-opus-5-5"]["cost_usd"] + 0.05)


# ---------------------------------------------------------------------------
# The editors' report: parsing
# ---------------------------------------------------------------------------

CHANGES = """## Changes
*For exact before/after text, see [x](x).*

1. [FACT-CHECK] [7] **Verse 12**: Changed "will vow" to "are told to vow."
Why: The report showed נִדְרוּ is an imperative.

2. [8, 10] **Introduction**: Removed a stem name.
Why: Jargon.

3. [7] **Verse 5**: Changed "seven centuries" to "more than a millennium."
Why: Chronology.

### UNVERIFIED
- Verse 3: the claim about Byron's date; I could not confirm it.
"""


def test_parse_change_log():
    from src.utils.editors_report import is_factual, parse_change_log
    entries, unverified = parse_change_log(CHANGES)
    assert [e["n"] for e in entries] == [1, 2, 3]
    assert entries[0]["fact_check_tagged"] and entries[0]["categories"] == ["7"]
    assert entries[0]["location"] == "Verse 12" and entries[0]["why"].startswith("The report")
    assert [is_factual(e) and not e["fact_check_tagged"] for e in entries] == [False, False, True]
    assert unverified == ["Verse 3: the claim about Byron's date; I could not confirm it."]


def test_outcome_for_a_contradicted_claim():
    from src.utils.editors_report import outcome_for, parse_change_log
    entries, _ = parse_change_log(CHANGES)
    rec = {"location": "Verse 12", "sentence": "Worshipers will vow and pay their vows.",
           "claim": "Verse 12 predicts that worshipers will vow", "suggested_fix": "are told to vow"}
    kept = outcome_for(rec, "Intro.\n\nWorshipers will **vow** and pay their vows.\n", entries)
    assert kept["unchanged"] and kept["status"].startswith("NOT changed")
    fixed = outcome_for(rec, "Intro.\n\nWorshipers are told to vow and pay their vows.\n", entries)
    assert not fixed["unchanged"] and "[FACT-CHECK] change #1" in fixed["status"]
    assert fixed["now_reads"].startswith("Worshipers are told")


def test_lookup_summaries():
    from src.agents.fact_checker import _web_action, summarize_tool_result
    assert summarize_tool_result("search_tanakh", {"count": 2, "refs": ["Psalms 78:48", "Song of Songs 8:6"]}) \
        == "2 verse(s): Psalms 78:48, Song of Songs 8:6"
    assert summarize_tool_result("get_text", {"error": "no text"}) == "ERROR: no text"
    assert summarize_tool_result("search_research", {"matches": 4, "passages": [
        {"section": "Rashi", "text": "a  b"}]}).startswith("4 match(es) in the research bundle (in: Rashi)")
    act = _web_action(SimpleNamespace(action=SimpleNamespace(type="search", query="Herodotus 2.141 mice")))
    assert act == {"type": "search", "query": "Herodotus 2.141 mice"}


def test_writer_reasoning_parts_prefers_the_two_forest_captures(tmp_path, monkeypatch):
    import src.utils.debug_paths as dp
    from src.utils.document_generator import writer_reasoning_parts
    monkeypatch.setattr(dp, "OUTPUT_ROOT", tmp_path)
    d = tmp_path / "psalm_77"
    d.mkdir()
    (d / "psalm_077_master_writer_v4_thinking.txt").write_text("both", encoding="utf-8")
    assert writer_reasoning_parts(77) == [("The writer", "both")]
    (d / "psalm_077_master_writer_v4_forest_essay_thinking.txt").write_text("e", encoding="utf-8")
    (d / "psalm_077_master_writer_v4_forest_verses_thinking.txt").write_text("v", encoding="utf-8")
    assert [h for h, _ in writer_reasoning_parts(77)] == ["The essay call", "The liturgy and verse-commentary call"]


# ---------------------------------------------------------------------------
# Fact checker robustness (Session 387: Ps 77's verses 10-15 answer was cut off)
# ---------------------------------------------------------------------------

def test_salvage_records_from_a_truncated_answer():
    from src.agents.fact_checker import salvage_records
    text = '{"claims": [{"n": 1, "claim": "a"}, {"n": 2, "claim": "b, with a \\"quote\\""}, {"n": 3, "claim": "cut o'
    assert [r["n"] for r in salvage_records(text)] == [1, 2]
    assert salvage_records("") == []


def _fc(tmp_tracker=None):
    from src.agents.fact_checker import FactChecker
    return FactChecker(client=object(), cost_tracker=tmp_tracker, db_path=None)


def test_a_truncated_chunk_is_rechecked_in_halves(monkeypatch):
    fc = _fc()
    chunk = {"label": "Verse 10 … Verse 15",
             "text": "".join(f"**Verse {n}**\n\n" + "x " * 400 + "\n\n" for n in range(10, 16))}
    calls = []

    def fake(psalm, ch, bundle, idx, n, evidence=""):
        calls.append(ch["label"])
        trunc = len(calls) == 1
        return {"records": [{"claim": ch["label"]}], "truncated": trunc, "usage": {}, "label": f"local {idx}"}
    monkeypatch.setattr(fc, "_local_chunk", fake)
    runs = fc._local_chunk_safe(77, chunk, "", 4, 6)
    assert len(calls) == 3 and runs[0]["superseded"] and runs[0]["records"] == []
    assert all(not r.get("truncated") for r in runs[1:])


def test_a_failed_check_still_bills_the_tracker(monkeypatch):
    fc = _fc(CostTracker())
    fc._spent = {}

    def boom(*a, **k):
        fc._spent = {"gpt-6-sol": {"usage": {"input": 1000, "cached": 0, "output": 10, "reasoning": 5},
                                   "searches": 0}}
        raise RuntimeError("chunk exploded")
    monkeypatch.setattr(fc, "_check", boom)
    with pytest.raises(RuntimeError):
        fc.check("guide", 77, "")
    assert fc.cost_tracker.usage_by_model["gpt-6-sol"].input_tokens == 1000


def test_a_resumed_run_continues_the_cost_record():
    first = CostTracker()
    snap = first.snapshot()
    first.add_usage("claude-opus-5-5", output_tokens=100_000)
    first.record_stage("master writer", snap)
    second = CostTracker()
    second.load_dict(json.loads(json.dumps(first.to_dict())))
    snap = second.snapshot()
    second.add_usage("gpt-5.4", input_tokens=10_000)
    second.record_stage("copy editor", snap)
    d = second.to_dict()
    assert [(s["stage"], s["attempt"]) for s in d["stages"]] == [("master writer", 1), ("copy editor", 2)]
    assert d["total_cost"] == pytest.approx(first.get_total_cost() + second.stages[-1]["cost_usd"])


def test_expand_sentence_restores_a_six_word_stub():
    from src.agents.fact_checker import expand_sentence
    guide = ("Intro.\n\nIn 1773, on the edge of one of the worst depressions of his life, William Cowper "
             "wrote the hymn. Next sentence.\n")
    assert expand_sentence("In 1773, on the edge of", guide) == (
        "In 1773, on the edge of one of the worst depressions of his life, William Cowper wrote the hymn.")
    assert expand_sentence("Already whole.", guide) == "Already whole."
    assert expand_sentence("Not in the guide at", guide) == "Not in the guide at"


def test_change_log_rationale_on_its_own_line():
    from src.utils.editors_report import parse_change_log
    entries, _ = parse_change_log("## Changes\n\n1. [FACT-CHECK] [7] **Introduction**: Changed a to b.  \n"
                                  "   Because the evidence says b.\n")
    assert entries[0]["what"] == "Changed a to b." and entries[0]["why"] == "Because the evidence says b."


def test_change_log_with_two_named_tags():
    from src.utils.editors_report import parse_change_log
    entries, _ = parse_change_log("## Changes\n\n14. [CITATION FIX] [FACT-CHECK] [7] **Verse 7**: Rewrote it.\n")
    e = entries[0]
    assert e["fact_check_tagged"] and e["citation_fix"] and e["categories"] == ["7"] and e["location"] == "Verse 7"
