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


# --- Session 391: "Rabbi Jonathan Sacks References Reviewed" -------------------------------------

_RUNNERS = ("run_enhanced_pipeline.py", "run_si_pipeline.py")  # S394: the TEST and *_with_synthesis runners were archived


def test_sacks_count_ignores_mentions_outside_the_sacks_section():
    """Ps 77 (S390, --skip-micro) printed 4: the old regex counted 'Rabbi Sacks' / 'Jonathan Sacks'
    anywhere in the bundle, its own Research Summary line included. Ps 77 has no Sacks excerpt."""
    bundle = (BUNDLE
              + "\n## Cross-Cultural Literary Echoes\n\n### Rabbi Jonathan Sacks, *Covenant and Conversation*\n"
                "Rabbi Sacks writes ... as Jonathan Sacks put it ...\n\n"
                "## Research Summary\n\n- **Rabbi Sacks references**: 0\n")
    assert _pipeline()._parse_research_stats_from_markdown(bundle)["sacks_count"] == 0


def test_sacks_count_is_the_number_of_excerpts_in_a_real_sacks_section():
    # S392: built offline (the librarian now harvests Sefaria; sacks_on_psalms.json is gone)
    from src.agents.sacks_librarian import SacksLibrarian, SacksReference, count_references_in_bundle
    lib = SacksLibrarian()
    refs = [SacksReference("prayer book", "Rabbi Sacks on Siddur", "Shabbat, Se'uda Shelishit for Shabbat",
                           "Rabbi Sacks on Siddur, Shabbat, Se'uda Shelishit for Shabbat 3", list(range(1, 7)),
                           "whole", "*Psalm 23:* One of the most sublime passages in all religious literature.")]
    refs += [SacksReference("book", "Studies in Spirituality", f"Essay {i}", f"Studies in Spirituality, Essay {i} 4",
                            [4], "verse", f"Rabbi Sacks quotes it ({i}): “You are with me” (Ps. 23:4).", "link")
             for i in range(1, 10)]
    bundle = (BUNDLE + "\n" + lib.format_for_research_bundle(refs, 23) + "\n---\n\n"
              + "## Related Psalms\n\nRabbi Sacks again\n\n## Research Summary\n\n"
                f"- **Rabbi Sacks references**: {len(refs)}\n")
    assert count_references_in_bundle(bundle) == len(refs)
    assert _pipeline()._parse_research_stats_from_markdown(bundle)["sacks_count"] == len(refs)
    # The old count (name mentions anywhere) was wrong both ways: 4 for 0 on Ps 77, 9 for 10 here.
    assert len(re.findall(r'### [^#\n]+Sacks|Rabbi Sacks|Jonathan Sacks', bundle)) != len(refs)


def test_every_runner_counts_sacks_with_the_shared_function():
    for name in _RUNNERS:
        text = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert "count_references_in_bundle(markdown_content)" in text, name
        assert "Rabbi Sacks|Jonathan Sacks" not in text, name


def test_verse_count_falls_back_to_the_psalm_text_when_the_stats_hold_zero():
    """S392: a --skip-macro run into a fresh folder recorded verse_count 0 (only the macro step set
    it), so the print-ready methods page said 'Psalm Verses Analyzed: 0' and 0 LXX verses."""
    from src.utils.commentary_formatter import CommentaryFormatter
    text = {n: {"hebrew": "א", "english": "a"} for n in range(1, 14)}
    for stats in ({"analysis": {"verse_count": 0}}, {}):
        out = CommentaryFormatter()._format_bibliographical_summary(stats, fallback_verse_count=len(text))
        assert "**Psalm Verses Analyzed**: 13" in out
        assert "**LXX (Septuagint) Verses Reviewed**: 13" in out
    kept = CommentaryFormatter()._format_bibliographical_summary({"analysis": {"verse_count": 21}}, 13)
    assert "**Psalm Verses Analyzed**: 21" in kept


def test_both_pipelines_record_the_verse_count_outside_the_macro_step():
    for runner in ("run_enhanced_pipeline.py", "run_si_pipeline.py"):
        src = (ROOT / "scripts" / runner).read_text(encoding="utf-8")
        head, _, _ = src.partition("elif not skip_macro:")
        assert "if not tracker.analysis.verse_count:" in head, runner


# -- Session 393: deep research cleaned against an independent check --------------------------

def test_checked_deep_research_is_detected_and_reported():
    from src.agents.research_assembler import DEEP_RESEARCH_CHECKED_NOTE
    from src.agents.deep_research_cleaner import demote_headings
    from src.utils.pipeline_summary import DEEP_RESEARCH_CHECKED_MARKER, deep_research_methods_value
    assert DEEP_RESEARCH_CHECKED_MARKER in DEEP_RESEARCH_CHECKED_NOTE
    body = demote_headings("## TOP FINDINGS\n\n1. one\n\n## 4. JEWISH PRACTICE\n\n* two\n")
    bundle = ("## Deep Web Research\n\n" + DEEP_RESEARCH_CHECKED_NOTE + body
              + "\n\n---\n\n## Cross-Cultural Literary Echoes\n\nx\n")
    for runner in ("run_enhanced_pipeline", "run_si_pipeline"):
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            mod = importlib.import_module(runner)
        finally:
            sys.path.pop(0)
        rs = mod._parse_research_stats_from_markdown(bundle)
        assert rs["deep_research_checked"] is True, runner
        assert rs["deep_research_chars"] > len(DEEP_RESEARCH_CHECKED_NOTE) + 30, runner  # the whole section
    assert deep_research_methods_value({"deep_research_included": True, "deep_research_checked": True}) \
        == "Yes (corrected against an independent check)"
    assert deep_research_methods_value({"deep_research_included": True}) == "Yes"
    assert deep_research_methods_value({"deep_research_available": True}) == "No (available but not included)"


def test_the_three_renderers_share_one_deep_research_implementation():
    for rel in ("src/utils/commentary_formatter.py", "src/utils/combined_document_generator.py",
                "src/utils/document_generator.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "deep_research_methods_value(research_data)" in text, rel
        assert 'deep_research_str = "No (removed for space)"' not in text, rel


# --- Session 394: reception + Targum on the methods page; reader questions gone -------------------

def test_reception_and_targum_lines_appear_only_when_the_run_had_them():
    from src.utils.pipeline_summary import reception_methods_lines
    assert reception_methods_lines({}) == []          # an older psalm's page is unchanged
    lines = dict(reception_methods_lines({"reception_passages": 41, "reception_chars": 44201,
                                          "targum_verses": 72, "targum_english_verses": 0}))
    assert lines["Rabbinic and Later Reception (Sefaria)"].startswith("41 passages (44,201 characters)")
    assert lines["Targum (Aramaic)"] == "72 verses given to the writer, Aramaic only"
    assert dict(reception_methods_lines({"targum_verses": 6, "targum_english_verses": 6})) == \
        {"Targum (Aramaic)": "6 verses given to the writer, 6 with English"}


def test_the_three_renderers_share_one_reception_implementation_and_print_no_questions():
    for rel in ("src/utils/commentary_formatter.py", "src/utils/combined_document_generator.py",
                "src/utils/document_generator.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "reception_methods_lines(research_data)" in text, rel
        assert "Questions for the Reader" not in text and "Question Generator" not in text, rel


def test_both_pipelines_record_reception_and_targum_for_the_methods_page():
    text = (ROOT / "scripts" / "run_enhanced_pipeline.py").read_text(encoding="utf-8")
    assert "tracker.research.reception_passages = rstats['kept']" in text
    assert "tracker.research.targum_verses = len(_tv)" in text
    for runner in ("run_enhanced_pipeline.py", "run_si_pipeline.py"):
        src = (ROOT / "scripts" / runner).read_text(encoding="utf-8")
        assert "QuestionCurator" not in src and "reader_questions_file" not in src, runner


def test_document_generator_options_are_keyword_only():
    """S394 removed the 6th positional argument (a reader-questions file); a caller still
    passing one must fail, not have it read as the appendix."""
    import inspect
    from src.utils.document_generator import DocumentGenerator
    params = inspect.signature(DocumentGenerator.__init__).parameters
    assert "reader_questions_path" not in params
    assert params["appendix_parts"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["compact"].kind is inspect.Parameter.KEYWORD_ONLY
