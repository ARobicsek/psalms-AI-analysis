"""Session 401: the writer revises its own guide after the fact check (src/agents/writer_revision.py).
Pure parts only: numbering, locating, the code guard rails, the response parser, the hand-off."""

from src.agents import writer_revision as wr

GUIDE = "\n".join([
    "# Commentary on Psalm 29",
    "---",
    "## Introduction",
    "The storm comes off the sea. Sinai was all plural voices.",          # P1
    "### The shape",
    "There are four movements, and the last is peace.",                    # P2
    "Radak reads the cedars as kings. He is right about that.",            # P3
    "#### Full psalm",
    "It opens Kabbalat Shabbat.",                                          # P4
    "## Psalm 29",
    "| 1 | מִזְמוֹר לְדָוִד | A psalm of David |",
    "## Verse-by-Verse Commentary",
    "**Verse 1**",
    "מִזְמוֹר לְדָוִד; הָבוּ לַה׳ בְּנֵי אֵלִים.",
    "> A psalm of David. Give to YHWH, sons of gods.",
    "The verb הָבוּ, \"hand it over,\" is everyday speech.",              # P5
    "> Bless the LORD, O my soul",
    "**Verse 2**",
    "הָבוּ לַה׳ כְּבוֹד שְׁמוֹ.",
    "> Give to YHWH the glory of His name.",
    "Bowing comes second.",                                                 # P6
    "## Methodological & Bibliographical Summary",
    "Models used: many.",
])


def _rec(cid, sentence, verdict="contradicted"):
    return {"id": cid, "sentence": sentence, "verdict": verdict, "location": "x", "claim": "c",
            "explanation": "e", "evidence": [{"source": "Exod 19:19", "quote": "קוֹל"}]}


def test_only_prose_in_the_writers_sections_is_numbered():
    lines, paras, shown = wr.number_paragraphs(GUIDE)
    texts = [lines[p.line] for p in paras]
    assert texts == [
        "The storm comes off the sea. Sinai was all plural voices.",
        "There are four movements, and the last is peace.",
        "Radak reads the cedars as kings. He is right about that.",
        "It opens Kabbalat Shabbat.",
        "The verb הָבוּ, \"hand it over,\" is everyday speech.",
        "Bowing comes second.",
    ]
    rendered = wr.render_for_writer(lines, paras, shown)
    assert "| 1 |" not in rendered and "Models used" not in rendered       # table and methods page left out
    assert "> A psalm of David" in rendered and "[P5] The verb" in rendered
    assert "**Verse 1**" in rendered and "[P" not in rendered.split("**Verse 1**")[1].split("\n")[1]


def test_neighbours_must_share_the_section_or_verse_note():
    lines, paras, _ = wr.number_paragraphs(GUIDE)
    ok = wr.allowed_pids([paras[1]], paras)          # P2, under "### The shape" with P3
    assert ok == {2: "flagged", 3: "neighbour"}       # P1 is in another section
    ok = wr.allowed_pids([paras[4]], paras)          # P5 in verse 1; P6 is verse 2
    assert ok == {5: "flagged"}


def test_locate_tolerates_markdown_and_curly_quotes():
    lines, paras, _ = wr.number_paragraphs(GUIDE)
    assert wr.locate("The verb *הָבוּ*, “hand it over,” is everyday speech.", lines, paras).pid == 5
    assert wr.locate("A sentence that is nowhere.", lines, paras) is None


def test_parse_and_apply_with_the_guard_rails():
    lines, paras, _ = wr.number_paragraphs(GUIDE)
    allowed = wr.allowed_pids([paras[0], paras[2]], paras)   # P1, P3 (+ P2 as P3's neighbour)
    response = "\n".join([
        "[P1]",
        "The storm comes off the sea. Sinai had both plural and singular voices.",
        "",
        "[P3] DELETE",
        "[P6]",
        "Bowing comes second, and that is the point.",           # not allowed
        "[P2]",
        "### A heading",                                         # never allowed
        "## LOG",
        "C1: fixed in P1 — Sinai has both",
        "- **C2**: kept — Radak says exactly this on v. 5",
    ])
    blocks, log = wr.parse_response(response)
    assert blocks[3] is None and blocks[1] == ["The storm comes off the sea. Sinai had both plural and singular voices."]
    assert log == {"C1": ("fixed", "in P1 — Sinai has both"), "C2": ("kept", "Radak says exactly this on v. 5")}
    text, applied, rejected = wr.apply_changes(lines, paras, blocks, allowed)
    assert [a["pid"] for a in applied] == [1, 3]
    assert sorted(r["pid"] for r in rejected) == [2, 6]
    assert "Sinai had both" in text and "Radak reads" not in text and "Bowing comes second." in text
    assert text.count("\n") == GUIDE.count("\n") - 1          # one line deleted, nothing else moved


def test_what_the_copy_editor_still_gets():
    recs = [_rec("C1", "The storm comes off the sea."), _rec("C2", "Radak reads the cedars as kings."),
            _rec("C3", "It opens Kabbalat Shabbat."), _rec("C4", "| 1 | table", "contradicted"),
            _rec("C5", "Bowing comes second.", "supported")]
    lines, paras, shown, items, unlocated = wr.plan(GUIDE, recs)
    assert [r["id"] for r, _ in items] == ["C1", "C2", "C3"] and unlocated == ["C4"]
    applied = [{"pid": 1}]
    log = {"C2": ("kept", "right"), "C3": ("fixed", "in P4")}        # C3 claims a fix it never made
    handled = wr.handled_ids(items, applied, log)
    assert handled == ["C1", "C2"]
    left = [r["id"] for r in wr.remaining_records(recs, handled)]
    assert left == ["C3", "C4", "C5"]


def test_the_prompt_carries_the_evidence_and_the_rules():
    lines, paras, shown, items, _ = wr.plan(GUIDE, [_rec("C1", "Sinai was all plural voices.")])
    u = wr.build_user_turn(29, wr.render_for_writer(lines, paras, shown), items)
    assert "C1 — in [P1]" in u and 'Evidence — Exod 19:19: "קוֹל"' in u
    assert "Rewrite the whole paragraph" in u and "Never mention the fact check" in u
    assert wr.REVISION_EFFORT != "max"


def test_a_replacement_never_carries_block_quote_lines():
    """Session 405, Ps 81 arm D: Argon returned P6 with the block quote under it, and the guide
    printed the quotation twice. Block quotes are never numbered paragraphs: drop such lines."""
    lines, paras, _ = wr.number_paragraphs(GUIDE)
    allowed = wr.allowed_pids([paras[4]], paras)                    # P5 (verse 1's note)
    blocks, _ = wr.parse_response("[P5]\nThe verb הָבוּ, \"hand it over,\" is plain speech.\n"
                                  "> Bless the LORD, O my soul\n## LOG\nC1: fixed in P5 — x")
    text, applied, rejected = wr.apply_changes(lines, paras, blocks, allowed)
    assert [a["pid"] for a in applied] == [5] and "is plain speech" in text
    assert text.count("> Bless the LORD, O my soul") == 1
    assert rejected and "block-quote" in rejected[0]["reason"]
    only_quote, _ = wr.parse_response("[P5]\n> Bless the LORD, O my soul\n## LOG")
    text, applied, rejected = wr.apply_changes(lines, paras, only_quote, allowed)
    assert applied == [] and text == GUIDE
