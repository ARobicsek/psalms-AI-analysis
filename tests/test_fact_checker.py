"""Session 385: the evidence-based fact check, and the copy-editor changes around it.

Three guarantees are pinned here:
  1. With no fact-check report supplied, the copy editor sends EXACTLY what it
     sent before Session 385 — the same system prompt, byte for byte, and the
     same user turn. The report may only ever arrive as supplementary context.
  2. A `contradicted` verdict with no quoted evidence never reaches the copy
     editor as a licence to change the text.
  3. `_reassemble` splits intro from verses at a verse header ALONE on its line,
     not at a liturgical `**Verse 2.** …` line (the Session 383 defect).
"""

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents import copy_editor as ce  # noqa: E402
from src.agents.fact_checker import (  # noqa: E402
    REPORT_MARKER,
    bundle_commentary,
    checkable_text,
    format_copy_editor_prompt,
    format_report_markdown,
    parse_fact_check_json,
    parse_ref,
    sentence_in_guide,
    split_guide_for_checking,
    validate_records,
)

# sha256 of COPY_EDITOR_SYSTEM_PROMPT as shipped before Session 385 (verified
# against `git show HEAD:src/agents/copy_editor.py` when the fact check was
# built). Change it ONLY in a commit that deliberately edits the prompt, the
# banned-phrase list or the superlative patterns it is assembled from.
SYSTEM_PROMPT_SHA256 = "89f73882954e8717a70974b662b73f629732aca9f89b2084fa924b1876f345cf"


# ---------------------------------------------------------------------------
# 1. The copy editor's prompt without a report
# ---------------------------------------------------------------------------

def test_copy_editor_system_prompt_is_unchanged():
    got = hashlib.sha256(ce.COPY_EDITOR_SYSTEM_PROMPT.encode("utf-8")).hexdigest()
    assert got == SYSTEM_PROMPT_SHA256, (
        "COPY_EDITOR_SYSTEM_PROMPT changed. The fact-check report must travel as "
        "supplementary_prompt, never as a rule in the system prompt "
        "(docs/plans/COPY_EDITOR_TERRA_FINDINGS.md: a stricter rule backfired)."
    )
    assert "FACT-CHECK" not in ce.COPY_EDITOR_SYSTEM_PROMPT
    assert "UNVERIFIED" not in ce.COPY_EDITOR_SYSTEM_PROMPT


def test_user_message_without_report_is_the_pre_s385_message():
    body = "**Verse 1**\nSome commentary."
    legacy = (
        "Here is the commentary for Psalm 76. Apply the copy editing rules from your "
        "system prompt. Return the FULL corrected text followed by a ## Changes section."
        f"\n\n{body}"
    )
    assert ce.CopyEditor.build_user_message(body, 76) == legacy
    assert ce.CopyEditor.build_user_message(body, 76, None) == legacy
    assert ce.CopyEditor.build_user_message(body, 76, "") == legacy
    assert ce.CopyEditor.build_user_message(body, 76, "REPORT") == legacy + "\n\nREPORT"


class _FakeChat:
    """Captures the messages a chat.completions call would send."""

    def __init__(self):
        self.calls = []
        self.completions = self

    def create(self, **kw):
        self.calls.append(kw)
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5,
                                completion_tokens_details=SimpleNamespace(reasoning_tokens=0))
        msg = SimpleNamespace(content="text\n## Changes\nNo changes required.")
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=usage)


def _editor_with_fake(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ce, "copy_editor_thinking_path", lambda n, p: tmp_path / "thinking.txt")
    ed = ce.CopyEditor.__new__(ce.CopyEditor)
    ed.model = "gpt-5.4"
    ed.logger = ce.get_logger("test_copy_editor")
    ed.cost_tracker = ce.CostTracker()
    ed.anthropic_client = None
    fake = _FakeChat()
    ed.openai_client = SimpleNamespace(chat=fake)
    return ed, fake


def test_system_message_is_identical_with_and_without_a_report(tmp_path, monkeypatch):
    ed, fake = _editor_with_fake(tmp_path, monkeypatch)
    records = validate_records([{
        "location": "Verse 4", "sentence": "S.", "claim": "c", "claim_type": "count_or_uniqueness",
        "verdict": "contradicted", "evidence": [{"source": "Ps 78:48", "quote": "לָרְשָׁפִים", "url": None}],
        "explanation": "e", "suggested_fix": "f"}])
    ed._call_editor("BODY", 76)
    ed._call_editor("BODY", 76, supplementary_prompt=format_copy_editor_prompt(records))
    (sys0, user0), (sys1, user1) = [c["messages"] for c in fake.calls]
    assert sys0 == sys1 == {"role": "system", "content": ce.COPY_EDITOR_SYSTEM_PROMPT}
    assert user0["content"] == ce.CopyEditor.build_user_message("BODY", 76)
    assert user1["content"].startswith(user0["content"] + "\n\n")
    assert REPORT_MARKER in user1["content"] and REPORT_MARKER not in user0["content"]


def test_echoed_fact_check_report_is_stripped():
    text = ("Intro para.\n\n" + REPORT_MARKER + " — …):\n1. something\n\n"
            "**Verse 1**\nBody.\n## Changes\n1. [7] x")
    out = ce.CopyEditor._strip_echoed_supplementary(text)
    assert REPORT_MARKER not in out
    assert "**Verse 1**" in out and "Intro para." in out


# ---------------------------------------------------------------------------
# 3. The intro / verses split
# ---------------------------------------------------------------------------

def _zones(intro, verses):
    return [
        {"type": "protected", "label": "intro_header", "content": "## Introduction\n"},
        {"type": "editable", "label": "intro_body", "content": intro},
        {"type": "protected", "label": "psalm_section", "content": "---\n## Psalm 76\n...\n---\n## Verse-by-Verse Commentary\n"},
        {"type": "editable", "label": "verses_body", "content": verses},
    ]


def test_reassemble_ignores_a_liturgical_verse_line():
    intro = ("Essay.\n---LITURGICAL-SECTION-START---\n#### Key verses\n"
             "**Verse 2.** In Nusach Sefard, the line is sung.\n"
             "**Verse 8.** In the Yom Kippur service…\n#### Practical Kabbalah\nText.\n")
    verses = "**Verse 1**\nCommentary one.\n**Verses 2–3**\nCommentary two.\n"
    ed = ce.CopyEditor.__new__(ce.CopyEditor)
    ed.logger = ce.get_logger("test_copy_editor")
    out = ed._reassemble(_zones(intro, verses), intro + verses)
    head, tail = out.split("## Verse-by-Verse Commentary\n")
    assert "**Verse 2.** In Nusach Sefard" in head
    assert "Practical Kabbalah" in head
    assert tail == verses


def test_reassemble_accepts_a_range_header_first():
    intro = "Essay.\n"
    verses = "**Verses 1–2**\nCommentary.\n"
    ed = ce.CopyEditor.__new__(ce.CopyEditor)
    ed.logger = ce.get_logger("test_copy_editor")
    out = ed._reassemble(_zones(intro, verses), intro + verses)
    assert out.split("## Verse-by-Verse Commentary\n")[1] == verses


def test_standalone_header_pattern():
    pat = ce.CopyEditor.STANDALONE_VERSE_HEADER
    assert pat.search("**Verse 1**")
    assert pat.search("**Verses 3-4**  ")
    assert pat.search("**Verses 3 – 4**")
    assert not pat.search("**Verse 2.** In Nusach Sefard")
    assert not pat.search("**Verse 9** is the most liturgically mobile verse")
    assert not pat.search("**Verse 2's** imagery")


# ---------------------------------------------------------------------------
# 2. Report parsing, validation and formatting
# ---------------------------------------------------------------------------

def _rec(verdict, evidence=None, **kw):
    r = {"location": "Verse 4", "sentence": "The only other plural use of the noun is Song 8:6.",
         "claim": "Song 8:6 is the only other plural", "claim_type": "count_or_uniqueness",
         "verdict": verdict, "evidence": evidence or [], "explanation": "why",
         "suggested_fix": None}
    r.update(kw)
    return r


def test_contradicted_without_quoted_evidence_is_downgraded():
    recs = validate_records([
        _rec("contradicted", [{"source": "memory", "quote": "", "url": None}], suggested_fix="x"),
        _rec("contradicted", [], suggested_fix="x"),
        _rec("contradicted", [{"source": "Ps 78:48", "quote": "לָרְשָׁפִים", "url": None}], suggested_fix="x"),
    ])
    assert [r["verdict"] for r in recs] == ["unverifiable", "unverifiable", "contradicted"]
    assert "downgraded" in recs[0]["notes"][0]
    prompt = format_copy_editor_prompt(recs)
    assert "CONTRADICTED (1):" in prompt


def test_invalid_verdict_and_claim_type_are_normalised():
    recs = validate_records([_rec("probably wrong", claim_type="gossip")])
    assert recs[0]["verdict"] == "unverifiable"
    assert recs[0]["claim_type"] == "other"


def test_parse_fact_check_json_tolerates_fences_and_prose():
    payload = {"claims": [_rec("supported")]}
    assert len(parse_fact_check_json(json.dumps(payload))) == 1
    assert len(parse_fact_check_json("```json\n" + json.dumps(payload) + "\n```")) == 1
    assert len(parse_fact_check_json("Here you go:\n" + json.dumps(payload))) == 1
    assert len(parse_fact_check_json(json.dumps([_rec("supported")]))) == 1


def test_sentence_in_guide_ignores_markdown_and_quote_style():
    guide = "Rashi says *“we find no enemy falling”* at Jerusalem.\nNext line."
    assert sentence_in_guide("Rashi says \"we find no enemy falling\" at Jerusalem.", guide)
    assert not sentence_in_guide("Something the guide never says.", guide)


def test_copy_editor_prompt_carries_the_three_rules_and_evidence():
    recs = validate_records([
        _rec("contradicted", [{"source": "Psalms 78:48", "quote": "וּמִקְנֵיהֶם לָרְשָׁפִים", "url": "https://www.sefaria.org/Psalms_78:48"}],
             suggested_fix="The form רִשְׁפֵי recurs only in Song 8:6."),
        _rec("supported", [{"source": "x", "quote": "y", "url": None}], claim="Herodotus 2.141 mice"),
        _rec("unverifiable", claim="a date"),
    ])
    p = format_copy_editor_prompt(recs)
    assert REPORT_MARKER in p
    assert "ONLY where an item below is marked CONTRADICTED" in p
    assert "Do NOT correct any other factual claim from memory" in p
    assert "### UNVERIFIED" in p
    assert "וּמִקְנֵיהֶם לָרְשָׁפִים" in p and "Suggested fix:" in p
    assert "SUPPORTED (1)" in p and "Herodotus 2.141 mice" in p
    assert "UNVERIFIABLE (1)" in p
    assert format_copy_editor_prompt([]) == ""


def test_report_markdown_groups_by_verdict():
    recs = validate_records([_rec("supported"), _rec("contradicted", [{"source": "s", "quote": "q", "url": None}], suggested_fix="f")])
    md = format_report_markdown(recs, {"psalm": 76, "model": "m", "effort": "high"})
    assert md.index("## Contradicted (1)") < md.index("## Supported (1)")
    assert "Suggested fix: f" in md


# ---------------------------------------------------------------------------
# Guide preparation and lookups
# ---------------------------------------------------------------------------

GUIDE = """# Commentary on Psalm 76
---
## Introduction
Opening paragraph.
## Who Holds the Verbs
Second section.
---LITURGICAL-SECTION-START---
#### Key verses
**Verse 2.** A liturgical line.
---
## Psalm 76
1. לַמְנַצֵּחַ	For the leader
---
## Verse-by-Verse Commentary
**Verse 1**
Note one.
**Verses 2–3**
Note two.
---
## Methodological & Bibliographical Summary
Stats.
"""


def test_checkable_text_drops_psalm_text_and_methods():
    t = checkable_text(GUIDE)
    assert "Opening paragraph." in t and "Note two." in t
    assert "For the leader" not in t
    assert "Stats." not in t


def test_split_guide_keeps_sections_whole_and_labels_them():
    t = checkable_text(GUIDE)
    one = split_guide_for_checking(t, max_chars=100000)
    assert len(one) == 1
    many = split_guide_for_checking(t, max_chars=40)
    joined = "".join(c["text"] for c in many)
    for piece in ("Opening paragraph.", "A liturgical line.", "Note one.", "Note two."):
        assert joined.count(piece) == 1
    labels = " | ".join(c["label"] for c in many)
    assert "Liturgy" in labels and "Verse 1" in labels and "Verses 2–3" in labels
    # A liturgical `**Verse 2.**` line is not a section boundary.
    assert not any(c["label"].startswith("Verse 2.") for c in many)


def test_parse_ref():
    assert parse_ref("Ps 78:48") == ("Psalms", 78, 48, None)
    assert parse_ref("Psalms 76:5-6") == ("Psalms", 76, 5, 6)
    assert parse_ref("Song 8:6") == ("Song of Songs", 8, 6, None)
    assert parse_ref("Song of Songs 8:6") == ("Song of Songs", 8, 6, None)
    assert parse_ref("2 Kgs 19:35") == ("II Kings", 19, 35, None)
    assert parse_ref("II Kings 19:35") == ("II Kings", 19, 35, None)
    assert parse_ref("Herodotus 2.141") is None


def test_bundle_commentary_finds_the_entry():
    bundle = ("## Traditional Commentaries\n### 76:11 — Rashi\n*crux*\nRashi text here.\n"
              "### 76:11 — Radak\nRadak text.\n## Next\n")
    assert bundle_commentary(bundle, "Rashi", "Psalms 76:11") == "*crux*\nRashi text here."
    assert bundle_commentary(bundle, "radak", "76:11") == "Radak text."
    assert bundle_commentary(bundle, "Malbim", "76:11") is None


# ---------------------------------------------------------------------------
# Pipeline wiring
# ---------------------------------------------------------------------------

def test_new_citation_issues_reports_only_what_the_copy_edit_added():
    from src.utils.scripture_verifier import CitationIssue, new_citation_issues
    a = CitationIssue("יֹאמְרוּ תָמִיד", "(Ps 40:17)", "", "Verse 5", "NOT_SUBSTRING", normalized_quoted="x")
    b = CitationIssue("וְיֹאמְרוּ", "(Ps 40:17)", "", "Verse 5", "NOT_SUBSTRING", normalized_quoted="y")
    assert new_citation_issues([a], [a]) == []
    assert new_citation_issues([a], [a, b]) == [b]
    assert new_citation_issues([], [b]) == [b]


def test_combine_supplementary():
    from src.agents.fact_checker import combine_supplementary
    assert combine_supplementary(None, "") is None
    assert combine_supplementary("A\n", None) == "A"
    assert combine_supplementary("\nA", "B") == "A\n\nB"


def test_fact_check_is_off_by_default_in_the_pipeline():
    import inspect
    src = (Path(__file__).resolve().parent.parent / "scripts" / "run_enhanced_pipeline.py").read_text(encoding="utf-8")
    assert "fact_check: bool = False" in src
    assert 'parser.add_argument("--fact-check", action="store_true"' in src
    # Without the flag the copy editor gets exactly the citation report, as before.
    assert "if fact_check else citation_fix_prompt" in src
    assert "if fact_check and not smoke_test and print_ready_file.exists():" in src


def test_an_empty_or_missing_db_is_never_used(tmp_path):
    import sqlite3
    from src.agents.fact_checker import usable_db, search_tanakh
    missing = tmp_path / "nope.db"
    assert not usable_db(missing)
    assert not missing.exists()          # checking must not create it
    empty = tmp_path / "empty.db"
    con = sqlite3.connect(empty)
    con.execute("CREATE TABLE verses (book_name TEXT, chapter INT, verse INT, hebrew TEXT, english TEXT)")
    con.commit(); con.close()
    assert not usable_db(empty)
    con = sqlite3.connect(empty)
    con.execute("INSERT INTO verses VALUES ('Psalms', 78, 48, 'וּמִקְנֵיהֶם לָרְשָׁפִים', 'x')")
    con.commit(); con.close()
    assert usable_db(empty)
    r = search_tanakh("לרשפים", empty)
    assert r["count"] == 1 and r["refs"] == ["Psalms 78:48"]
