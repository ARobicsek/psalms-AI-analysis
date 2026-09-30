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


# ---------------------------------------------------------------------------
# Session 386: the staged checker (luna local → sol web / sol review)
# ---------------------------------------------------------------------------

def _srec(sentence, verdict, claim="c", **kw):
    return dict({"location": "Verse 1", "sentence": sentence, "claim": claim, "claim_type": "other",
                 "verdict": verdict, "evidence": [{"source": "x", "quote": "q", "url": None}],
                 "explanation": "", "suggested_fix": None}, **kw)


def test_needs_web_is_a_stage_one_verdict_only():
    from src.agents.fact_checker import LOCAL_SCHEMA, FINAL_SCHEMA
    enum = lambda s: s["properties"]["claims"]["items"]["properties"]["verdict"]["enum"]  # noqa: E731
    assert "needs_web" in enum(LOCAL_SCHEMA)
    assert "needs_web" not in enum(FINAL_SCHEMA)
    # validate_records normalises a stray needs_web to unverifiable unless it is allowed
    assert validate_records([_srec("s", "needs_web")])[0]["verdict"] == "unverifiable"
    from src.agents.fact_checker import VERDICTS
    assert validate_records([_srec("s", "needs_web")], allowed=VERDICTS + ("needs_web",))[0]["verdict"] == "needs_web"


def test_merge_replaces_needs_web_and_contradicted_in_guide_order():
    from src.agents.fact_checker import merge_stage_results
    local = [_srec("A.", "supported"), _srec("B.", "needs_web"), _srec("C.", "contradicted"), _srec("D.", "unverifiable")]
    web = [_srec("B.", "supported")]
    review = [_srec("C.", "supported", explanation="pedantic")]
    out = merge_stage_results(local, web, review)
    assert [r["sentence"] for r in out] == ["A.", "B.", "C.", "D."]
    assert [r["verdict"] for r in out] == ["supported", "supported", "supported", "unverifiable"]
    assert [r["stage"] for r in out] == ["local", "web", "review", "local"]
    assert out[2]["first_verdict"] == "contradicted"


def test_an_unreviewed_contradiction_never_reaches_the_copy_editor():
    """If stage 3 returns nothing for a claim, it must NOT keep stage 1's contradicted verdict."""
    from src.agents.fact_checker import merge_stage_results
    out = merge_stage_results([_srec("C.", "contradicted"), _srec("B.", "needs_web")], [], [])
    assert [r["verdict"] for r in out] == ["unverifiable", "unverifiable"]
    assert "CONTRADICTED: none." in format_copy_editor_prompt(out)


def test_every_stage_is_told_the_divine_name_convention():
    from src.agents import fact_checker as fc
    for name in ("LOCAL_INSTRUCTIONS", "WEB_INSTRUCTIONS", "REVIEW_INSTRUCTIONS"):
        assert "{divine_names}" in getattr(fc, name) and "{materiality}" in getattr(fc, name), name
    for form in ("ה׳", "אֱלֹקִים", "קֵל", "צְבָקוֹת", "שַׁקַּי", "אֱלוֹקַּ"):
        assert form in fc.DIVINE_NAMES_NOTE, form


def test_claims_block_carries_evidence_only_for_review():
    import json as _json
    from src.agents.fact_checker import claims_block
    r = _srec("S.", "contradicted", explanation="because")
    plain = _json.loads(claims_block([r]))[0]
    rev = _json.loads(claims_block([r], with_evidence=True))[0]
    assert "first_checker_evidence" not in plain and plain["n"] == 1
    assert rev["first_checker_finding"] == "because" and rev["first_checker_evidence"]


def test_search_bundle_matches_hebrew_on_consonants_and_names_the_section():
    from src.agents.fact_checker import search_bundle
    bundle = "## Lexicon\n### רֶשֶׁף [BDB]\nflame, bolt\n\n### Liturgy\nLecha Eli is said on Yom Kippur.\n"
    heb = search_bundle(bundle, "רשף")
    assert heb["matches"] == 1 and heb["passages"][0]["section"].startswith("רֶשֶׁף")
    eng = search_bundle(bundle, "lecha eli")
    assert eng["matches"] == 1 and eng["passages"][0]["section"] == "Liturgy"
    assert "error" in search_bundle("", "x") and "error" in search_bundle(bundle, " ")


def test_chunk_verses_reads_single_and_range_headers():
    from src.agents.fact_checker import chunk_verses
    assert chunk_verses("**Verse 3**\ntext\n**Verses 5–6**\nmore") == {3, 5, 6}
    assert chunk_verses("## Introduction\nNo headers here; **Verse 2.** in prose does not count.") == set()


def test_commentary_entries_can_be_scoped_to_verses():
    from src.agents.fact_checker import commentary_entries
    b = "### 76:3 — Rashi\nA\n\n### 76:4 — Rashi\nB\n\n### 76:4 — Malbim\nC\n## Next\n"
    assert "76:3" in commentary_entries(b) and "76:4 — Malbim" in commentary_entries(b)
    only4 = commentary_entries(b, {4})
    assert "76:3" not in only4 and "B" in only4 and "C" in only4


def test_quote_on_page_tolerates_pointing_and_punctuation_but_not_invention():
    from src.agents.fact_checker import quote_on_page
    page = "<p>וּמִי יַעֲמֹד לְפָנֶיךָ, וּמִי יִהְיֶה תְמוּרָתִי; וְאֵיךְ חֶשְׁבּוֹן לְךָ אֶתֵּן</p>"
    assert quote_on_page("ומי יעמד לפניך ומי יהיה תמורתי", page)
    assert quote_on_page("He spins from the bars, but there’s no cage to him",
                         "He spins from the bars, but there's no cage to him")
    assert not quote_on_page("ומי יעמד לפניך ומיד מתחיל הווידוי אשמנו בגדנו", page)
    # under five words: exact (normalised) match only, no shingle tolerance
    assert quote_on_page("a short", "this is a short page")
    assert not quote_on_page("a shorter one", "this is a short page")


def test_gather_schema_asks_for_sources_not_verdicts():
    from src.agents.fact_checker import GATHER_SCHEMA_STRICT, GATHER_INSTRUCTIONS
    item = GATHER_SCHEMA_STRICT["properties"]["claims"]["items"]["properties"]
    assert "verdict" not in item and "sources" in item
    assert "do NOT give verdicts" in GATHER_INSTRUCTIONS


# ---------------------------------------------------------------------------
# Session 388: free lookups (liturgy.db, Septuagint, helpful failures)
# ---------------------------------------------------------------------------

def _tiny_liturgy_db(tmp_path):
    import sqlite3
    db = tmp_path / "liturgy.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE prayers (sefaria_ref TEXT, source_text TEXT, nusach TEXT, occasion TEXT, "
                "service TEXT, section TEXT, prayer_name TEXT, canonical_prayer_name TEXT, "
                "sequence_order INTEGER, hebrew_text TEXT, english_text TEXT)")
    rows = [
        ("Machzor Yom Kippur Ashkenaz, Neilah; Concluding Service, Ashrei, Ashrei", "Machzor Yom Kippur Ashkenaz",
         "Ashkenaz", None, "Neilah", None, "Ashrei", "Ashrei", 12, "אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ", ""),
        ("Machzor Yom Kippur Ashkenaz, Neilah; Concluding Service, Sanctification of the Day, Sanctification of the Day",
         "Machzor Yom Kippur Ashkenaz", "Ashkenaz", None, "Neilah", None, "Sanctification of the Day",
         "Sanctification of the Day", 16,
         "יְהֹוָה יְהֹוָה אֵל רַחוּם וְחַנּוּן. אֶזְכְּרָה אֱלֹהִים וְאֶהֱמָיָה בִּרְאוֹתִי כָּל עִיר", ""),
        ("Machzor Yom Kippur Ashkenaz, Neilah; Concluding Service, Avinu Malkenu, Avinu Malkenu",
         "Machzor Yom Kippur Ashkenaz", "Ashkenaz", None, "Neilah", None, "Avinu Malkenu", "Avinu Malkenu", 18,
         "אָבִינוּ מַלְכֵּנוּ", ""),
        ("Siddur Sefard, Fast Days, Selichot for Taanit Esther, Selichot for Taanit Esther", "Siddur Sefard",
         "Sefard", None, None, None, "Selichot for Taanit Esther", "Fast of Esther Selichot", 3, "סְלַח לָנוּ", ""),
    ]
    con.executemany("INSERT INTO prayers VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    return db


def test_search_liturgy_hebrew_phrase_gives_passage_and_neighbours(tmp_path):
    from src.agents.fact_checker import search_liturgy
    r = search_liturgy("אזכרה אלהים ואהמיה", _tiny_liturgy_db(tmp_path))   # consonants only, like Ps 77:4
    assert r["matches"] == 1
    hit = r["prayers"][0]
    assert "Sanctification of the Day" in hit["ref"] and "אֶזְכְּרָה" in hit["text"]
    assert (hit["before"], hit["after"]) == ("Ashrei", "Avinu Malkenu")


def test_search_liturgy_by_name_ignores_apostrophes_and_falls_back_to_best_partial(tmp_path):
    from src.agents.fact_checker import search_liturgy
    db = _tiny_liturgy_db(tmp_path)
    assert search_liturgy("Ne'ilah", db)["matches"] == 3
    r = search_liturgy("Ta'anit Esther", db)
    assert r["matches"] == 1 and r["prayers"][0]["before"] == ""      # filed under no service
    part = search_liturgy("Neilah Kaddish", db)                        # no prayer has both
    assert part["matches"] == 3 and "partial" in part


def test_get_text_answers_a_liturgy_ref_from_disk_without_the_network(tmp_path, monkeypatch):
    from src.agents import fact_checker as fc
    db = _tiny_liturgy_db(tmp_path)
    monkeypatch.setattr(fc, "_sefaria_text", lambda *a, **k: pytest.fail("network used"))
    ref = "Machzor Yom Kippur Ashkenaz, Neilah; Concluding Service, Avinu Malkenu, Avinu Malkenu"
    out = fc.lookup_text(ref, liturgy_db=db)
    assert out["source"].startswith("liturgy.db") and out["hebrew"] == "אָבִינוּ מַלְכֵּנוּ"


def test_failed_get_text_says_what_to_do_instead(monkeypatch):
    from src.agents import fact_checker as fc
    def boom(*a, **k):
        raise ValueError("404")
    monkeypatch.setattr(fc, "_sefaria_text", boom)
    monkeypatch.setattr(fc, "_liturgy_rows", lambda db=None: [])
    monkeypatch.setattr(fc, "sefaria_suggestions", lambda name, limit=6: ["Likkutei Tefillot"])
    assert "get_lxx" in fc.lookup_text("Septuagint Psalms 76:11")["error"]
    assert "search_liturgy" in fc.lookup_text("Machzor Yom Kippur Ashkenaz, Neilah")["error"]
    assert "Likkutei Tefillot" in fc.lookup_text("Likkutei Tefilot 1:92")["error"]
    monkeypatch.setattr(fc, "sefaria_suggestions", lambda name, limit=6: [])
    assert "needs_web" in fc.lookup_text("The Silver Platter")["error"]


def test_a_missing_commentary_entry_reads_as_no_entry(monkeypatch):
    import requests
    from src.agents import fact_checker as fc
    def not_found(*a, **k):
        raise requests.HTTPError(response=SimpleNamespace(status_code=404))
    monkeypatch.setattr(fc, "_sefaria_text", not_found)
    err = fc.lookup_commentary("Rashi", "Psalms 77:21")["error"]
    assert err.startswith("no entry") and "Rashi" in err


def test_lookup_lxx_uses_greek_numbering_and_aligns_brenton(monkeypatch):
    from src.agents import fact_checker as fc
    from src.data_sources import lxx_brenton
    monkeypatch.setattr(lxx_brenton, "chapter", lambda code, ch: {})     # no Brenton Greek: Bolls lemmas
    calls = []
    grk = [{"verse": i, "text": f"g{i}"} for i in range(1, 22)]            # heading = verse 1
    eng = [{"verse": i, "text": f"e{i}"} for i in range(1, 21)]            # Brenton: heading unnumbered
    def get(url, timeout=0):
        calls.append(url)
        return SimpleNamespace(json=lambda: grk if "/LXX/" in url else eng)
    monkeypatch.setattr(fc.requests, "get", get)
    out = fc.lookup_lxx("Psalms 77:11")
    assert all("/19/76/" in u for u in calls)                              # MT 77 = LXX 76
    assert (out["greek"], out["english_brenton"]) == ("g11", "e10")
    assert out["greek_form"].startswith("LEMMAS")
    assert "error" in fc.lookup_lxx("Jeremiah 10:1")                        # chapters differ in the Greek


def test_lookup_lxx_prefers_brentons_inflected_greek(monkeypatch):
    """Session 390: Bolls's Greek is lemmas; Brenton's Greek (same numbering) is the real text."""
    from src.agents import fact_checker as fc
    from src.data_sources import lxx_brenton
    monkeypatch.setattr(lxx_brenton, "chapter",
                        lambda code, ch: {i: f"G{i}" for i in range(1, 22)} if (code, ch) == ("PSA", 76) else {})
    calls = []
    eng = [{"verse": i, "text": f"e{i}"} for i in range(1, 21)]
    def get(url, timeout=0):
        calls.append(url)
        return SimpleNamespace(json=lambda: eng)
    monkeypatch.setattr(fc.requests, "get", get)
    out = fc.lookup_lxx("Psalms 77:11")
    assert (out["greek"], out["english_brenton"]) == ("G11", "e10")
    assert out["greek_form"].startswith("Brenton") and all("/LXXE/" in u for u in calls)


def test_the_new_lookups_are_offered_and_routed():
    from src.agents.fact_checker import FUNCTION_TOOLS, LOCAL_INSTRUCTIONS, FactChecker
    names = {t["name"] for t in FUNCTION_TOOLS}
    assert {"search_liturgy", "get_lxx"} <= names
    assert "search_liturgy" in LOCAL_INSTRUCTIONS and "get_lxx" in LOCAL_INSTRUCTIONS
    fcx = FactChecker.__new__(FactChecker)
    fcx.db_path = None
    assert "error" in fcx._run_tool("search_liturgy", {"query": ""}, "")


def test_shared_evidence_puts_the_psalm_first_when_asked(monkeypatch):
    from src.agents import fact_checker as fc
    monkeypatch.setattr(fc, "psalm_text", lambda p, db: "**77:2** קוֹלִי\nMy voice")
    ev = fc.shared_evidence("No citations here.", "", None, psalm=77)
    assert ev.startswith("## PSALM 77 ITSELF") and "קוֹלִי" in ev
    assert "PSALM 77" not in fc.shared_evidence("No citations here.", "", None)


# ---------------------------------------------------------------------------
# Session 388: the copy editor's edits mode
# ---------------------------------------------------------------------------

_GUIDE = ("## Introduction\nIn 1773, on the edge of despair, Cowper wrote a hymn.\n\n"
          "**Verse 2**\nThe voice cries “to God” — twice.\n1. A numbered line in the guide.\n")


def test_apply_edit_list_applies_verbatim_and_loose_matches_and_reports_failures():
    resp = ("## Changes\n"
            "1. [FACT-CHECK] **Introduction**: Cowper was not yet depressed — per the report.\n"
            "<<<FIND\nIn 1773, on the edge of despair, Cowper wrote a hymn.\n===\n"
            "In 1773, on the edge of a relapse, Cowper wrote a hymn.\n>>>\n"
            "2. [7] **Verse 2**: Straight quotes and a hyphen in the FIND still match.\n"
            "<<<FIND\nThe voice cries \"to God\" - twice.\n===\nThe voice cries “to God” — two times.\n>>>\n"
            "3. [9] **Verse 2**: A FIND that is not in the text.\n"
            "<<<FIND\nNothing like this exists.\n===\nx\n>>>\n")
    text, changes, st = ce.apply_edit_list(_GUIDE, resp)
    assert "edge of a relapse" in text and "two times" in text
    assert (st["changes"], st["edits"], st["applied"], st["loose"], st["not_found"]) == (3, 3, 2, 1, 1)
    assert "<<<FIND" not in changes and changes.startswith("## Changes")
    assert "3. [9]" in changes and "NOT APPLIED" in changes.split("3. [9]")[1]
    assert "NOT APPLIED" not in changes.split("3. [9]")[0]
    assert "1. A numbered line in the guide." in text                    # untouched


def test_apply_edit_list_deletion_ambiguity_and_numbered_lines_inside_a_find():
    doubled = _GUIDE + "The voice cries “to God” — twice.\n"
    resp = ("## Changes\n1. [9] **Verse 2**: Cut the numbered aside.\n"
            "<<<FIND\n1. A numbered line in the guide.\n\n===\n>>>\n"
            "2. [9] **Verse 2**: Ambiguous.\n<<<FIND\nThe voice cries “to God” — twice.\n===\nX\n>>>\n")
    text, changes, st = ce.apply_edit_list(doubled, resp)
    assert st["changes"] == 2                                   # the "1." inside the FIND is not a change
    assert "A numbered line" not in text and st["ambiguous"] == 1
    assert text.count("twice") == 2


def test_apply_edit_list_no_changes():
    text, changes, st = ce.apply_edit_list(_GUIDE, "## Changes\nNo changes required.")
    assert text == _GUIDE and "No changes required." in changes and st["changes"] == 0


def test_edits_mode_user_message_puts_the_format_last_and_full_mode_is_unchanged():
    full = ce.CopyEditor.build_user_message("BODY", 77, "REPORT")
    assert full == ce.CopyEditor.build_user_message("BODY", 77, "REPORT", edit_mode="full")
    assert "EDIT_LIST" not in full and "<<<FIND" not in full
    edits = ce.CopyEditor.build_user_message("BODY", 77, "REPORT", edit_mode="edits")
    assert edits.index("BODY") < edits.index("REPORT") < edits.index("<<<FIND")
    assert "Do NOT return the corrected text" in edits


def test_edits_mode_falls_back_when_the_model_returns_the_full_text():
    ed = ce.CopyEditor.__new__(ce.CopyEditor)
    ed.logger = SimpleNamespace(info=lambda *a: None, warning=lambda *a: None)
    full_reply = _GUIDE.replace("twice", "two times") + "\n## Changes\n1. [9] **Verse 2**: reworded.\n"
    assert ed._from_edit_list(_GUIDE, full_reply) == full_reply
    assert ed.last_edit_stats == {"fallback": "full text returned"}


def test_pointing_regression_refuses_a_fix_the_masoretic_text_contradicts():
    # a toy Masoretic stream: 77:17's dehiq dagesh after רָאוּךָ, and ordinary מַיִם elsewhere
    mt = " " + " ".join(ce._pointed_words("רָ֘א֤וּךָ מַּ֨יִם ׀ אֱֽלֹהִ֗ים | וַיִּקְווּ מַיִם")) + " "
    find = "רָאוּךָ מַּיִם אֱלֹקִים"
    assert ce.pointing_regression(find, "רָאוּךָ מַיִם אֱלֹקִים", mt)             # the S388 Ps 77 case
    assert ce.pointing_regression("רָאוּךָ מַיִם", "רָאוּךָ מַּיִם", mt) is None   # a fix TOWARD the MT
    assert ce.pointing_regression(find, "the waters saw You", mt) is None          # not a pointing edit
    assert ce.pointing_regression(find, "רָאוּךָ מַיִם", "") is None               # no database: no opinion


def test_apply_edit_list_marks_a_refused_edit():
    resp = "## Changes\n1. [5] **Verse 2**: Pointing.\n<<<FIND\ntwice\n===\nthrice\n>>>\n"
    text, changes, st = ce.apply_edit_list(_GUIDE, resp, guard=lambda f, r: "the MT has the original")
    assert text == _GUIDE and st["refused"] == 1 and "NOT APPLIED: the MT has the original" in changes
