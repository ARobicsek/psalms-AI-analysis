"""Session 390: the guide's methods page and the editors' report tell the truth about the run.

The S389 Ps 77 guide's "Methodological & Bibliographical Summary" was wrong in four places: the
echoes lines named the legacy passes and gpt-5.6-terra (stale `model_usage` keys, re-added by the
research bundle), "Fact Check: gpt-6-sol" appeared with no fact check, and "Concordance
Searches: N/A" after --skip-micro. Its editors' report described a fact checker that never ran
and gave the sum of three runs as the cost of the run.
"""
import importlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BUNDLE = """## Concordance Searches

### זנח (19 external results, auto, consonantal)
*Where it occurs: Prophets 4*

### מאן נחם (2 external results, auto, consonantal)

## Shared-Vocabulary Parallels (computed)

### Chapters in sustained dialogue with the psalm

- **Habakkuk 3** — 11 shared distinctive words

### Closest single passages

**Habakkuk 3:10** — shares זרם, תהום (from this psalm's vv. 17, 18)
text

**Psalms 18:14** — shares רעם, ברק (from this psalm's v. 19)
text

## Figurative Language Instances
"""


def _pipeline():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        return importlib.import_module("run_enhanced_pipeline")
    finally:
        sys.path.pop(0)


def test_skip_micro_parser_recovers_per_search_counts_and_the_radar():
    rs = _pipeline()._parse_research_stats_from_markdown(BUNDLE)
    assert rs["concordance_per_query"] == {"זנח": 19, "מאן נחם": 2}
    assert rs["concordance_count"] == 21
    assert rs["shared_vocabulary_count"] == 2
    from src.utils.pipeline_summary import concordance_methods_summary
    text = concordance_methods_summary({"concordance_results": {**rs["concordance_per_query"],
                                                                "total_results": 21},
                                        "shared_vocabulary_count": 2})
    assert text.startswith("2 word searches finding 21 matching verses")
    assert "2 shared-vocabulary parallels" in text


def test_v3_echo_keys_replace_stale_legacy_keys_even_after_the_bundle_re_adds_them():
    from src.utils.pipeline_summary import PipelineSummaryTracker
    p = _pipeline()
    t = PipelineSummaryTracker(77)
    t.model_usage.update({"literary_echoes_pass_1a": "gemini", "literary_echoes_pass_3": "gpt-5.6-terra"})
    p._track_echo_models(t, "v3")
    t.track_model_for_step("literary_echoes_pass_3", "gpt-5.6-terra")   # the reused bundle's copy
    p._drop_legacy_echo_keys_if_v3(t)
    assert not any(k.startswith("literary_echoes") for k in t.model_usage)
    assert t.model_usage["echoes_proposal"] == "claude-opus-5-5 + gemini-3.1-pro-preview"
    assert t.model_usage["echoes_locate"].startswith("gpt-6-luna")
    p._track_echo_models(t, "legacy")
    assert "echoes_proposal" not in t.model_usage and "literary_echoes_pass_3" in t.model_usage
    p._track_echo_models(t, None)
    assert not any("echoes" in k for k in t.model_usage)


def test_a_copy_edit_without_a_fact_check_drops_the_fact_check_line():
    src = (ROOT / "scripts" / "run_enhanced_pipeline.py").read_text(encoding="utf-8")
    i = src.index('tracker.model_usage.pop("fact_check", None)')
    assert src.index("if not skip_copy_editor and not smoke_test:") < i < src.index(
        'tracker.track_model_for_step("fact_check", fc.model)')


def test_v3_dossier_is_recognised_and_the_assembler_labels_it():
    from src.agents.echoes_v3 import assemble_writer_dossier, is_v3_dossier
    assert is_v3_dossier(assemble_writer_dossier(77, [], []))
    assert not is_v3_dossier("### Psalm 75:1 — The Plea Against Destruction\n")
    src = (ROOT / "src" / "agents" / "research_assembler.py").read_text(encoding="utf-8")
    assert "is_v3_dossier(literary_echoes_content)" in src and "methods_models()" in src


def test_echoes_methods_lines_v3_wins_and_legacy_labels_are_unchanged():
    from src.utils.pipeline_summary import echoes_methods_lines
    v3 = echoes_methods_lines({"echoes_proposal": "A + B", "echoes_locate": "L",
                               "literary_echoes_pass_3": "gpt-5.6-terra"})
    assert v3 == ["**Echoes & Resonances (Proposal; the Master Writer selects)**: A + B",
                  "**Echoes & Resonances (Locating Sources)**: L"]
    legacy = echoes_methods_lines({"literary_echoes_pass_1": "g", "literary_echoes_pass_3": "t"})
    assert legacy == ["**Literary Echoes (Passes 1-2 — Generation)**: g",
                      "**Literary Echoes (Pass 3 — Source Verification)**: t"]
    assert echoes_methods_lines({}) == []


def test_the_three_renderers_share_one_echoes_implementation():
    for gen in ("document_generator.py", "combined_document_generator.py", "commentary_formatter.py"):
        text = (ROOT / "src" / "utils" / gen).read_text(encoding="utf-8")
        assert "echoes_methods_lines(" in text, gen
        assert "Pass 3 — Source Verification" not in text, gen


def test_docx_concordance_label_keeps_the_description(tmp_path):
    from docx import Document
    from src.utils.document_generator import DocumentGenerator
    gen = DocumentGenerator.__new__(DocumentGenerator)
    gen.document = Document()
    gen.document.styles.add_style("SummaryText", 1)   # 1 = paragraph style
    gen._add_summary_paragraph("**Concordance Searches**: 22 word searches finding 514 matching verses; "
                               "20 shared-vocabulary parallels (זנח (19); מאן נחם (2))")
    texts = [p.text for p in gen.document.paragraphs]
    assert texts[0] == ("Concordance Searches: 22 word searches finding 514 matching verses; "
                        "20 shared-vocabulary parallels")
    assert re.search(r"זנח\s—\s19", texts[1])


def _report_dir(tmp_path, with_fc: bool):
    stages = [{"stage": "copy editor", "attempt": 1, "cost_usd": 0.5, "models": {}, "charges": []},
              {"stage": "literary echoes", "attempt": 2, "cost_usd": 1.2, "models": {}, "charges": []},
              {"stage": "copy editor", "attempt": 2, "cost_usd": 0.4, "models": {}, "charges": []}]
    (tmp_path / "psalm_077_cost.json").write_text(json.dumps({"total_cost": 2.1, "stages": stages}),
                                                  encoding="utf-8")
    (tmp_path / "psalm_077_print_ready.md").write_text("guide", encoding="utf-8")
    (tmp_path / "psalm_077_copy_edited.md").write_text("guide", encoding="utf-8")
    if with_fc:
        (tmp_path / "psalm_077_fact_check.json").write_text(
            json.dumps({"claims": [{"id": "C1", "verdict": "supported", "claim": "x", "sentence": "guide"}]}),
            encoding="utf-8")


def test_editors_report_without_a_fact_check_says_so_and_costs_this_run(tmp_path):
    from src.utils.editors_report import build_markdown
    _report_dir(tmp_path, with_fc=False)
    md = build_markdown(77, tmp_path)
    assert "Two things checked or changed it" in md and "No fact check ran" in md
    assert "fact checker" not in md.split("## What it cost")[0].replace("No fact check", "")
    assert "## Claims the fact checker" not in md and "Appendix: every lookup" not in md
    assert "| Cost of this run (run 2 in this psalm's cost file) | $1.60 |" in md
    assert "| … all 2 recorded runs of this psalm together | $2.10 |" in md
    assert "| … copy editor | $0.400 |" in md          # the LATEST copy editor, not the first


def test_editors_report_with_a_fact_check_keeps_its_sections(tmp_path):
    from src.utils.editors_report import build_markdown
    _report_dir(tmp_path, with_fc=True)
    md = build_markdown(77, tmp_path)
    assert "Three things checked or changed it" in md
    assert "## Claims the fact checker supported" in md and "Appendix: every lookup" in md
