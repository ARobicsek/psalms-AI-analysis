"""Session 391: the reception section (src/data_sources/sefaria_reception.py), offline.

The rules select on the KIND and AGE of a source, never on how interesting it looks (the author:
a selection model would overdetermine the guide). These tests pin the rules, not any one psalm."""
from src.data_sources import sefaria_reception as R

PSALM = ["למנצח על ידותון לאסף מזמור",
         "קולי אל אלהים ואצעקה קולי אל אלהים והאזין אלי",
         "קול רעמך בגלגל האירו ברקים תבל רגזה ותרעש הארץ"]


def link(ref, verse, category="Midrash", work=None, date=None):
    return {"ref": ref, "anchorRef": f"Psalms 77:{verse}", "category": category,
            "index_title": work or ref.rsplit(" ", 1)[0], "compDate": date}


def item(ref, verse, category="Midrash", date=None, he=None, en="", work=None):
    he = he or ("אמר רבי " + PSALM[verse - 1] + " זה ישראל " + ref)
    return R.analyse(link(ref, verse, category, work, date), {"he": he, "en": en}, PSALM, 77)


# --- Hebrew matching -------------------------------------------------------------------------

def test_rabbinic_spelling_prefixes_and_divine_names_still_match():
    assert R.same_word("אלהים", "אלקים")                    # divine-name spelling
    assert R.same_word("יהוה", "ה'".replace("'", ""))
    assert R.same_word("עלם", "עולם")                        # defective vs plene
    assert R.same_word("בגלגל", "שבגלגל")                    # Berakhot 59a: two prefixes deep
    assert not R.same_word("קול", "רעם")


def test_a_mislink_or_an_unfound_verse_is_dropped():
    assert R.analyse(link("X 1", 49), {"he": "anything"}, PSALM, 77) is None     # "77:49" = Ps 78's
    assert R.analyse(link("X 1", 3), {"he": "טקסט אחר לגמרי בלי הפסוק"}, PSALM, 77) is None
    assert R.analyse(link("X 1", 3), {"he": ""}, PSALM, 77) is None


def test_the_window_is_cut_around_the_quotation():
    before = " ".join(f"מילה{i}" for i in range(100))
    it = item("Long 1", 3, he=before + " כדכתיב " + PSALM[2] + " ועוד דברים")
    assert it["he"].startswith("… ") and "רעמך" in it["he"]
    assert len(it["he"].split()) < 100


def test_composition_date_orders_by_midpoint_and_shows_the_range():
    assert R.composition_date([150, 750]) == (450, "150–750")
    assert R.composition_date([1200]) == (1200, "1200")
    assert R.composition_date(None) == (R.UNDATED, "")


# --- Merging and tiers ------------------------------------------------------------------------

def test_one_passage_citing_several_verses_is_one_item():
    a, b = item("Eikhah Rabbah 1:23", 2, date=[500]), item("Eikhah Rabbah 1:23", 3, date=[500])
    heads = R.merge([a, b])
    assert len(heads) == 1 and heads[0]["verses"] == {2, 3}


def test_parallel_tellings_collapse_to_the_earliest():
    text = "אמר רבי חזקיה " + PSALM[2] + " מלמד שהיה העולם מתיירא עד שקיבלו ישראל את התורה"
    late = item("Tanchuma 5", 3, date=[500, 800], he=text)
    early = item("Mekhilta 2", 3, date=[200], he=text)
    heads = R.merge([late, early])
    assert [h["ref"] for h in heads] == ["Mekhilta 2"] and heads[0]["parallels"] == ["Tanchuma 5"]


def test_tiers():
    assert R.tier(item("Berakhot 59a", 3, "Talmud", [450, 550])) == "A"
    assert R.tier(item("Some Modern Intro to the Mishnah", 3, "Mishnah", None)) == "C"   # undated
    own = R.analyse({**link("Midrash Tehillim 77:1", 2), "index_title": "Midrash Tehillim"},
                    {"he": PSALM[1] + " אמר חבקוק"}, PSALM, 77)
    assert R.tier(own) == "A"
    assert R.tier(item("Bereshit Rabbah 1", 2, "Midrash", [400])) == "B"
    assert R.tier(item("Aggadat Bereshit 1", 2, "Midrash", None)) == "C"
    assert R.tier(item("Sefat Emet 1", 2, "Chasidut", [1870])) == "C"


# --- Selection --------------------------------------------------------------------------------

def test_tier_a_is_kept_and_a_bare_proof_text_is_not():
    talmud = item("Sanhedrin 19b", 2, "Talmud", [450, 550])
    filler = " ".join(["דברים"] * 200)
    proof = item("Midrash Long", 3, "Midrash", [400], he=filler + " שנאמר " + PSALM[2])
    kept, dropped = R.select([talmud, proof], n_verses=3)
    assert talmud in kept and proof in dropped


def test_at_most_two_classical_midrashim_per_verse_earliest_first():
    ms = [item(f"Midrash {d}", 2, "Midrash", [d]) for d in (900, 200, 500, 400)]
    for i, m in enumerate(ms):            # make them distinct passages (no parallel collapse)
        m["shingles"] = {(str(i),)}
    kept, _ = R.select(ms, n_verses=3)
    assert sorted(k["date"] for k in kept) == [200, 400]


def test_convergence_keeps_the_earliest_later_reader_and_names_the_rest():
    later = [item(f"{w} 1", 3, "Chasidut", [d], work=w) for w, d in
             (("Toldot Yaakov Yosef", 1780), ("Tzofnat Paneach", 1782), ("Ben Porat Yosef", 1770))]
    for i, m in enumerate(later):
        m["shingles"] = {(str(i),)}
    kept, _ = R.select(later, n_verses=3)
    lead = [k for k in kept if k["also"]]
    assert len(lead) == 1 and lead[0]["work"] == "Ben Porat Yosef"
    assert lead[0]["also"] == ["Toldot Yaakov Yosef", "Tzofnat Paneach"]


def test_the_budget_is_per_verse_and_capped():
    big = [item(f"Talmud {i}", 2, "Talmud", [450], en="x" * 900) for i in range(10)]
    for i, m in enumerate(big):
        m["shingles"] = {(str(i),)}
    kept, _ = R.select(big, n_verses=1, per_verse_chars=2000)
    assert sum(len(k["he"]) + len(k["en"]) for k in kept) <= 2000
    kept, _ = R.select(big, n_verses=176, per_verse_chars=1400, max_chars=3000)    # Ps 119
    assert sum(len(k["he"]) + len(k["en"]) for k in kept) <= 3000
    assert R.PER_VERSE_CHARS == 1400 and R.SECTION_MAX_CHARS == 40000


# --- Rendering and insertion ------------------------------------------------------------------

def test_render_is_neutral_and_labelled():
    it = item("Sanhedrin 19b:16", 2, "Talmud", [450, 550], en="Jacob sired them and Joseph sustained them")
    it["parallels"] = ["Bereshit Rabbah 84:5"]
    it["tier"] = "A"
    md = R.render(77, [it], 5)
    assert md.startswith(R.SECTION_HEADER)
    assert "### Verse 2 — Sanhedrin 19b:16 (Talmud, c. 450–550)" in md
    assert "*Also told in: Bereshit Rabbah 84:5.*" in md
    assert "**English:** Jacob sired them" in md
    assert "1 of 5 located passages" in md
    for word in ("important", "significant", "illuminat", "key insight"):
        assert word not in md.lower()
    assert R.render(77, [], 0) == ""


def test_insert_section_goes_after_commentaries_and_replaces_an_old_one():
    bundle = ("## Traditional Commentaries\n\nRashi\n\n## Liturgical Usage\n\nx\n\n"
              "## Related Psalms\n\ny\n\n## Research Summary\n\nz\n")
    sec = R.SECTION_HEADER + "\n\nfirst\n"
    once = R.insert_section(bundle, sec)
    assert once.index(R.SECTION_HEADER) < once.index("## Related Psalms")
    assert once.index("## Liturgical Usage") < once.index(R.SECTION_HEADER)
    twice = R.insert_section(once, R.SECTION_HEADER + "\n\nsecond\n")
    assert twice.count(R.SECTION_HEADER) == 1 and "second" in twice and "first" not in twice
    assert R.insert_section(bundle, "") == bundle


def test_section_headings_are_invisible_to_the_writer_and_checker_patterns():
    """The forest writer counts commentators from `### ch:v — Name` and finds the psalm's verses from
    `### Verse N`; the fact checker reads commentary entries the same way. The reception section's
    headings must match none of them (else arm B's prompt would say "nineteen commentators")."""
    import re
    from src.agents import forest_writer as fw
    from src.agents.fact_checker import _COMMENTARY_SECTION
    it = item("Sanhedrin 19b:16", 2, "Talmud", [450, 550])
    it2 = item("Eikhah Rabbah 1:23", 3, "Midrash", [500])
    it2["verses"] = {1, 2, 3}
    md = R.render(77, [it, it2], 2)
    assert fw.commentator_names(md) == []
    assert not re.search(r"^### Verse (\d+)\s*$", md, re.M)
    assert not _COMMENTARY_SECTION.search(md)
