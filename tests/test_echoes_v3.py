"""Echoes v3 (Session 388): the pure helpers, at $0."""

from src.agents.echoes_v3 import (
    PROPOSE_SCHEMA, RETRIEVE_LIT_SCHEMA, _loose, assemble_markdown, budgets, build_pool,
    entry_status, extract_json, pool_for_judge,
)


def test_budgets_follow_the_authors_rates():
    b = budgets(21)
    assert b["final_literature"] == 16          # ~0.75 echoes per verse (S384)
    assert b["final_beyond"] == 13              # 'plenty' beyond literature (S388)
    assert b["final_far"] == 8                  # the far lane (S388 v3.1)
    assert budgets(3)["final_literature"] == 8  # floors for short psalms


def test_extract_json_takes_the_last_fenced_block_and_falls_back_to_braces():
    assert extract_json('thinking {not json}\n```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('prefix {"b": 2} suffix') == {"b": 2}


def test_pool_hides_the_proposer_and_resolves_moves():
    props = {"m1": {"moves": [{"id": "M1", "verses": "1:1", "move": "walks, stands, sits"}],
                    "candidates": [{"work": "W1", "creator": "A", "move_id": "M1"}, {"work": ""}]},
             "m2": {"moves": [], "candidates": [{"work": "W2", "creator": "B", "move_id": ""}]}}
    pool = build_pool(props)
    assert [c["id"] for c in pool] == ["C01", "C02"]           # the empty candidate is dropped
    assert {c["psalm_move"] for c in pool} == {"walks, stands, sits", ""}
    shown = pool_for_judge(pool)
    assert "m1" not in shown and "m2" not in shown and "_source" not in shown


def test_status_needs_the_original_on_its_page():
    assert entry_status({"retrieved": {"found": False}}) == "not_found"
    assert entry_status({"retrieved": {"found": True, "check_main": "quote found on the page"}}) == "verified"
    assert entry_status({"retrieved": {"found": True, "check_main": "quote NOT found on the page"}}) == "unconfirmed"
    assert entry_status({"retrieved": {"found": True, "check_main": "page could not be fetched or read"}}) \
        == "page_unreadable"


def test_an_unconfirmed_text_is_never_quoted():
    entries = [
        {"lane": "literature", "use": True, "verses": "77:4", "move": "comfort refused",
         "status": "verified", "candidate": {"creator": "Poet", "work": "Good", "locus": "l. 1-4"},
         "retrieved": {"original": "line one\nline two", "original_url": "https://x", "public_domain": "yes"}},
        {"lane": "literature", "use": True, "verses": "77:3", "move": "m",
         "status": "unconfirmed", "candidate": {"creator": "Other", "work": "Bad", "locus": "st. 2"},
         "retrieved": {"original": "INVENTED TEXT"}},
        {"lane": "beyond", "use": False, "verses": "77:5", "status": "verified",
         "candidate": {"work": "Alternate"}, "retrieved": {"quote": "unused"}},
    ]
    md = assemble_markdown(77, entries)
    assert "> line one" in md and "public domain" in md
    assert "INVENTED TEXT" not in md and "*Text not confirmed*" in md
    assert "Alternate" not in md
    assert md.index("77:3") < md.index("77:4")       # verse order


def test_schemas_are_strict_for_openai_and_loosened_for_gemini():
    for schema in (PROPOSE_SCHEMA, RETRIEVE_LIT_SCHEMA):
        assert "additionalProperties" not in str(_loose(schema))
    item = PROPOSE_SCHEMA["properties"]["candidates"]["items"]
    assert set(item["required"]) == set(item["properties"])   # strict mode requires every key


# -- $0 extraction (the page, not the model, supplies the text) --------------------------

from src.agents.echoes_v3 import extract_passage, html_to_lines, usable  # noqa: E402

COWPER_RPO = """<html><body><nav>Menu 1 2 3</nav><h1>Light Shining out of Darkness</h1>
<div class="poem"><span>God moves in a mysterious way</span><br/>
<span>His wonders to perform;</span><br/>
<span>He plants his footsteps in the sea,</span><br/>
<span>And rides upon the storm.</span>&nbsp;4<br/><br/>
<span>Deep in unfathomable mines</span><br/>
5<br/><span>Of never failing skill</span><br/>
<span>He treasures up his bright designs,</span><br/>
<span>And works his sov'reign will.</span>&nbsp;8</div></body></html>"""


def test_line_numbers_are_removed_and_the_stanza_break_kept():
    lines = html_to_lines(COWPER_RPO)
    text = extract_passage(lines, "God moves in a mysterious way", "And works his sovereign will", 8)
    assert text.split("\n") == ["God moves in a mysterious way", "His wonders to perform;",
                                "He plants his footsteps in the sea,", "And rides upon the storm.", "",
                                "Deep in unfathomable mines", "Of never failing skill",
                                "He treasures up his bright designs,", "And works his sov'reign will."]


def test_a_title_that_repeats_the_first_line_is_not_quoted_twice():
    html = ("<h2>I know that He exists</h2><p>I know that He exists.<br>Somewhere – in Silence –<br>"
            "He has hid his rare life<br>From our gross eyes.</p><p>Related: I know that He exists</p>")
    text = extract_passage(html_to_lines(html), "I know that He exists.", "From our gross eyes.", 4)
    assert text.startswith("I know that He exists.\nSomewhere") and text.endswith("gross eyes.")


def test_prose_is_cut_at_the_first_and_last_words():
    para = ("Long before. It is Rachel of old weeping for her children, and will not be comforted "
            "because they are not. Such is the lot set on earth for you mothers. And do not be comforted. "
            "Something else afterwards that is not wanted.")
    text = extract_passage(html_to_lines(f"<p>{para}</p>"), "It is Rachel of old weeping",
                           "And do not be comforted.", 3)
    assert text.startswith("It is Rachel") and text.endswith("do not be comforted.")


def test_without_the_first_line_nothing_is_extracted():
    assert extract_passage(html_to_lines("<p>Some other poem<br>entirely</p>"), "No worst, there is none") is None


def test_only_page_text_counts_for_literature():
    assert usable({"lane": "literature", "status": "verified"})
    assert usable({"lane": "literature", "status": "translation_only"})
    assert not usable({"lane": "literature", "status": "page_unreadable"})
    assert usable({"lane": "beyond", "status": "page_unreadable"})


def test_page_furniture_is_not_a_passage():
    from src.agents.echoes_v3 import plausible_passage
    assert not plausible_passage("وَٱلضُّحَىٰ\nوَٱلضُّحَىٰ\nBy the morning brightness\nTafsirs\nLeçons\nRéflexions",
                                 "وَٱلضُّحَىٰ")
    assert not plausible_passage("By the morning brightness\nTafsirs\nLeçons\nRéflexions",
                                 "By the morning brightness", anchored_end=False)
    assert not plausible_passage("Afterkseeingkthiskuniversalkform,kwhichkIkhavekneverkseenkbefore")
    celan = ("Niemand knetet uns wieder aus Erde und Lehm,\nniemand bespricht unsern Staub.\nNiemand.\n\n"
             "Gelobt seist du, Niemand.\nDir zulieb wollen\nwir blühn.\nDir\nentgegen.")
    assert plausible_passage(celan, "Niemand knetet uns wieder aus Erde und Lehm,")


# -- v3.1: two judges, the used-works filter, one locus per entry ---------------------------

from src.agents.echoes_v3 import filter_used, merge_judges, same_work, _retrieve_item  # noqa: E402

B = {"final_literature": 2, "alt_literature": 1, "final_beyond": 1, "alt_beyond": 1, "final_far": 1, "alt_far": 1}


def _pool():
    return [{"id": "C01", "lane": "literature", "creator": "A", "work": "One"},
            {"id": "C02", "lane": "literature", "creator": "B", "work": "Two"},
            {"id": "C03", "lane": "literature", "creator": "C", "work": "Three"},
            {"id": "C04", "lane": "literature", "creator": "Yehuda Halevi", "work": "Tziyon", "jewish": True},
            {"id": "C05", "lane": "far", "creator": "", "work": "Kelvin wake"}]


def test_both_judges_picks_come_first_and_single_picks_interleave():
    j = {"claude-opus-5-5": {"literature": [{"id": "C01"}, {"id": "C02"}], "far": [{"id": "C05"}]},
         "gemini-3.1-pro-preview": {"literature": [{"id": "C03"}, {"id": "C02"}],
                                    "literature_alternates": [{"id": "C04"}]}}
    out = merge_judges(j, _pool(), B)
    lit = [s["id"] for s in out if s["lane"] == "literature" and s["role"] == "final"]
    assert lit[0] == "C02"                       # chosen by both
    assert set(lit[1:3]) == {"C01", "C03"}       # the union may pass one judge's budget (x1.35)
    assert "C04" in lit                          # no Jewish finalist, so the Jewish alternate is promoted
    far = [s for s in out if s["lane"] == "far"]
    assert far[0]["chosen_by"] == {"claude-opus-5-5": "finalist #1"}


def test_a_fixable_error_travels_to_the_locator():
    j = {"claude-opus-5-5": {"far": [{"id": "C05", "retrieve": "the wake angle"}],
                             "ratings": [{"id": "C05", "fix": "The angle is constant, about 19.5 degrees."}]}}
    sel = next(s for s in merge_judges(j, _pool(), B) if s["id"] == "C05")
    item = _retrieve_item(_pool()[4], sel, "far")
    assert "19.5" in item["correction"] and item["retrieve"] == "the wake angle"


def test_the_judge_locus_replaces_the_proposers():
    c = {"creator": "Homer", "work": "Iliad", "locus": "Book 24, line 445", "anchor": "Hermes poured sleep"}
    item = _retrieve_item(c, {"retrieve": "Book 18, lines 203-231"}, "literature")
    assert item["retrieve"] == "Book 18, lines 203-231" and "445" not in str(item)


def test_used_works_are_filtered_by_work_not_author():
    used = [{"creator": "Paul Celan", "work": "Psalm", "psalm": 41}]
    kept, removed = filter_used([{"id": "C1", "creator": "Paul Celan", "work": "Psalm (Die Niemandsrose)"},
                                 {"id": "C2", "creator": "Paul Celan", "work": "Tenebrae"}], used)
    assert [c["id"] for c in removed] == ["C1"] and removed[0]["used_in"] == 41
    assert [c["id"] for c in kept] == ["C2"]


def test_numbered_works_and_short_titles_do_not_collide():
    assert not same_work({"creator": "Beethoven", "work": "Symphony No. 6"}, {"creator": "Beethoven", "work": "Symphony No. 9"})
    assert not same_work({"creator": "Rudyard Kipling", "work": "If"}, {"creator": "Rudyard Kipling", "work": "Recessional"})
    assert same_work({"creator": "Rudyard Kipling", "work": "If—"}, {"creator": "Rudyard Kipling", "work": "If"})


# -- v3.2: the writer mode and the bundle splice ------------------------------------------

from src.agents.echoes_v3 import assemble_writer_dossier, budgets_writer, dedupe_passages  # noqa: E402
from src.agents.research_assembler import LITERARY_ECHOES_HEADER, replace_literary_echoes_section  # noqa: E402


def test_writer_budgets_scale_with_the_psalm():
    assert budgets_writer(21) == {"propose_lit": 13, "propose_beyond": 8, "propose_far": 5}
    assert budgets_writer(6) == {"propose_lit": 8, "propose_beyond": 5, "propose_far": 3}


def test_the_same_passage_merges_but_another_passage_of_the_work_stays():
    pool = [{"id": "C1", "_source": "a", "creator": "Homer", "work": "Iliad", "locus": "Book 18, lines 203-231", "move": "m1"},
            {"id": "C2", "_source": "b", "creator": "Homer", "work": "The Iliad", "locus": "Book 24, line 445", "move": "m2"},
            {"id": "C3", "_source": "b", "creator": "Lord Byron", "work": "The Destruction of Sennacherib", "locus": "whole poem", "move": "m3"},
            {"id": "C4", "_source": "a", "creator": "Lord Byron", "work": "Destruction of Sennacherib", "locus": "stanzas 1-3", "move": "m4"}]
    kept = dedupe_passages(pool)
    assert [c["id"] for c in kept] == ["C1", "C2", "C3"]
    assert kept[2]["also"][0]["move"] == "m4"


def test_the_writer_dossier_nests_under_the_bundle_section_and_lists_the_register():
    e = {"lane": "far", "verses": "77:20", "status": "verified", "use": True,
         "candidate": {"creator": "", "work": "The watermark", "domain": "papermaking", "pattern": "seen only against the light",
                       "what": "A mark visible only when held up to light.", "move": "m", "also": []},
         "retrieved": {"quote": "A watermark is visible when held to light.", "url": "https://x", "source_title": "T"}}
    md = assemble_writer_dossier(77, [e], [{"creator": "Paul Celan", "work": "Psalm", "psalm": 41}])
    assert not any(line.startswith("## ") or line.startswith("# ") for line in md.split("\n"))
    assert "### Far associations (1)" in md and "*The pattern:* seen only against the light" in md
    assert "- Paul Celan, Psalm (used as a whole)" in md and "never repeat these" in md


def test_a_reused_bundle_gets_the_new_echoes_and_loses_all_of_the_old():
    bundle = ("## Deep Web Research\n\nDR\n\n---\n\n" + LITERARY_ECHOES_HEADER + "\n\n*old*\n\n### C1\n\nOLD ONE\n\n---\n\n"
              "### C2\n\nOLD TWO\n\n---\n\n## Research Summary\n\nstats\n")
    out = replace_literary_echoes_section(bundle, "### Literary echoes (1)\n\nNEW")
    assert "OLD ONE" not in out and "OLD TWO" not in out and "NEW" in out
    assert out.count(LITERARY_ECHOES_HEADER) == 1 and out.index("NEW") < out.index("## Research Summary")
    assert out.startswith("## Deep Web Research")
    without = replace_literary_echoes_section("## A\n\nx\n\n## Research Summary\n\ns\n", "NEW")
    assert without.index("NEW") < without.index("## Research Summary")


# --- Session 390: the register is passage-level for texts ----------------------------------------

def test_a_text_is_used_passage_by_passage_and_anything_else_as_a_whole():
    from src.agents.echoes_v3 import filter_used, same_locus
    used = [{"creator": "William Shakespeare", "work": "Hamlet", "kind": "text", "passage": "Act 3, Scene 1",
             "quote": "To be, or not to be, that is the question", "psalm": 39},
            {"creator": "J. S. Bach", "work": "The Art of Fugue", "kind": "other", "passage": "", "quote": "",
             "psalm": 77}]
    pool = [{"id": "C1", "creator": "Shakespeare", "work": "Hamlet", "locus": "3.1.56-88"},
            {"id": "C2", "creator": "William Shakespeare", "work": "Hamlet", "locus": "Act 5, Scene 2, 219-224"},
            {"id": "C3", "creator": "Johann Sebastian Bach", "work": "The Art of Fugue", "locus": "Contrapunctus 1"}]
    kept, removed = filter_used(pool, used)
    assert [c["id"] for c in kept] == ["C2"] and {c["id"] for c in removed} == {"C1", "C3"}
    assert same_locus("Canto 3, lines 1-9", "Canto 3") and not same_locus("Book 24", "Book 18")
    assert not same_locus("", "Act 1") and same_locus("the whole poem", "stanza 2")


def test_a_text_with_an_unknown_passage_is_caught_by_its_words_after_retrieval():
    from src.agents.echoes_v3 import filter_used, repeated_quotation, used_works_block
    used = [{"creator": "Gerard Manley Hopkins", "work": "I wake and feel the fell of dark", "kind": "text",
             "passage": "", "quote": "I wake and feel the fell of dark, not day.", "psalm": 43}]
    c = {"id": "C1", "creator": "G. M. Hopkins", "work": "I wake and feel the fell of dark, not day", "locus": "lines 1-8"}
    assert filter_used([c], used)[0] == [c]                    # no passage on record: kept for now
    same = {"candidate": c, "retrieved": {"original": "I wake and feel the fell of dark, not day. What hours, O what black hours"}}
    other = {"candidate": c, "retrieved": {"original": "I am gall, I am heartburn. God's most deep decree"}}
    assert repeated_quotation(same, used)["psalm"] == 43 and repeated_quotation(other, used) is None
    block = used_works_block(used)
    assert "Hopkins, I wake and feel the fell of dark" in block and "quoted: “I wake and feel" in block


def test_same_locus_reads_roman_numerals_and_compares_line_ranges():
    """Session 390, from real register pairs: 'Act V, scene ii' matched 'Act 4, scene 6' on the
    word 'scene', and Horace Odes 2.14 lines 5-8 matched lines 25-28 on the top two levels."""
    from src.agents.echoes_v3 import same_locus
    cases = [("Act V, scene ii", "Act 4, scene 6", False), ("Act 3, Scene 1, 56-88", "3.1.60", True),
             ("Canto 3", "Canto III, lines 1-9", True), ("Book 2, Ode 14, lines 25–28", "Book 2, Ode 14, lines 5–8", False),
             ("Book 24, lines 470-620", "Book 24, 600-650", True), ("Sonnet 29", "Sonnet 30", False),
             ("KTU 1.5 II", "KTU 1.5, Column I, lines 1–3", False), ("Holy Sonnet XIV", "Holy Sonnet 14", True),
             ("Canto V, lines 121-123", "Canto I, lines 22–27", False), ("Opening lines", "Epilogue, section II", False)]
    assert [(a, b) for a, b, want in cases if same_locus(a, b) != want] == []


def test_same_work_needs_more_than_one_stray_shared_word():
    from src.agents.echoes_v3 import same_work
    assert not same_work({"creator": "Hayim Nahman Bialik", "work": "Metei Midbar (The Dead of the Desert)"},
                         {"creator": "", "work": "Book of the Dead"})
    assert same_work({"creator": "", "work": "Laetoli footprints"}, {"creator": "Mary Leakey", "work": "Laetoli"})
    assert same_work({"creator": "Shakespeare", "work": "Hamlet"}, {"creator": "William Shakespeare", "work": "Hamlet"})
    assert same_work({"creator": "J. S. Bach", "work": "The Art of Fugue"},
                     {"creator": "Johann Sebastian Bach", "work": "The Art of Fugue"})


# -- S400: the locator is billed by the tier each response reports ----------------------

def test_retrieval_is_billed_per_reported_tier(monkeypatch):
    """The locator runs inside FactChecker._loop, which has defaulted to flex since S397.
    Before S400 echoes billed every locator call at the standard row; a flex call must be
    billed at `<model>@flex`, a fallback at the model's own row, the searches once."""
    from src.agents import echoes_v3, fact_checker
    from src.utils.cost_tracker import price_tokens
    flex = {"input": 1000, "cached": 0, "cache_write": 0, "output": 100, "reasoning": 200}
    std = {"input": 500, "cached": 0, "cache_write": 0, "output": 50, "reasoning": 0}
    total = {k: flex[k] + std[k] for k in flex}

    def fake_loop(self, label, model, effort, content, tools, schema, bundle, cache_key):
        return {"records": [{"n": 1, "found": True}], "usage": total, "searches": 3,
                "billed": {"gpt-6-luna@flex": flex, "gpt-6-luna": std}}

    monkeypatch.setattr(fact_checker.FactChecker, "_loop", fake_loop)
    agent = echoes_v3.EchoesV3Agent()
    monkeypatch.setattr(agent, "_client_openai", lambda: object())
    out = agent._retrieve(80, "far", [{"work": "W"}])
    assert out == [{"n": 1, "found": True}]
    rows = {c.model: c for c in agent._costs}
    assert set(rows) == {"gpt-6-luna@flex", "gpt-6-luna"}
    assert rows["gpt-6-luna@flex"].searches == 3 and rows["gpt-6-luna"].searches == 0
    want = (price_tokens("gpt-6-luna@flex", input_tokens=1000, output_tokens=100, thinking_tokens=200)
            + price_tokens("gpt-6-luna", input_tokens=500, output_tokens=50)
            + 3 * echoes_v3.WEB_SEARCH_USD_PER_CALL)
    assert abs(sum(c.usd for c in agent._costs) - want) < 1e-9
