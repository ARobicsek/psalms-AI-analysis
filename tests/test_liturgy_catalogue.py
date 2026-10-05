"""Session 395: the liturgy matcher, catalogue and librarian (no network, no model)."""

import sqlite3
from pathlib import Path

import pytest

from src.liturgy import verse_matcher as vm
from src.liturgy import liturgy_catalogue as lc
from src.agents import liturgy_librarian_v2 as L

ROOT = Path(__file__).resolve().parents[1]
HAVE_DBS = (ROOT / "data" / "liturgy.db").exists() and (ROOT / "database" / "tanakh.db").exists()
needs_dbs = pytest.mark.skipif(not HAVE_DBS, reason="liturgy.db / tanakh.db not present")


# -- normalisation ---------------------------------------------------------------------------

def test_zero_width_joiner_does_not_split_or_change_a_word():
    # Sefaria writes עָו‍ֹן with a ZWJ; the old index kept it and lost whole-verse matches.
    assert vm.tokenize("יְכַפֵּר עָו‍ֹן").keys == vm.tokenize("יְכַפֵּ֥ר עָוֺן֮").keys


def test_maqaf_paseq_and_punctuation_separate_words():
    assert len(vm.tokenize("וְלֹא־יַשְׁחִית ׀ וְהִרְבָּה, לְהָשִׁיב:").keys) == 4


def test_divine_name_spellings_are_one_word():
    keys = {tuple(vm.tokenize(t).keys) for t in ("יְהֹוָה", "ה'", "ה׳", "יְיָ", "יהוה")}
    assert len(keys) == 1


def test_plene_and_defective_spellings_match():
    assert vm.tokenize("אֲבוֹתֵינוּ").keys == vm.tokenize("אֲבֹתֵינוּ").keys
    assert vm.tokenize("תְּהִלּוֹת").keys == vm.tokenize("תְּהִלֹּת").keys


def test_ketiv_qere_keeps_the_qere():
    assert vm.clean_masoretic("(הושר) [הַיְשַׁ֖ר] דַּרְכֶּֽךָ") .startswith("הַיְשַׁ֖ר")
    assert "*" not in vm.clean_masoretic("מִנְּשֹֽׂא*(בספרי ספרד ואשכנז מִנְּשֽׂוֹא)׃")


def test_words_never_match_inside_longer_words():
    # S395: "ציון אשר" (78:68) was found in the header "ובא לציון אשרי".
    lit = vm.tokenize("אשרי ובא לציון אשרי יושבי ביתך").keys
    ps = vm.tokenize("צִיּוֹן אֲשֶׁר אָהֵב").keys
    assert not any(lit[i:i + 2] == ps[:2] for i in range(len(lit) - 1))


def test_distinctiveness():
    k = lambda s: vm.tokenize(s).keys  # noqa: E731
    assert not vm.is_distinctive(k("הוֹלֵךְ וְלֹא"))      # one content word
    assert not vm.is_distinctive(k("וְלֹא יִהְיוּ"))       # function words
    assert vm.is_distinctive(k("אַבִּיעָה חִידוֹת"))
    assert vm.is_distinctive(k("רוּחַ הוֹלֵךְ וְלֹא יָשׁוּב"))


# -- merging -----------------------------------------------------------------------------------

def _prayer(text):
    return vm.Prayer(1, "Book, X", "Book", "Ashkenaz", "Siddur", text, vm.tokenize(text))


def test_runs_split_by_a_small_variant_are_merged():
    p = _prayer("a")
    r1 = vm.Run(p, 0, 5, 0, 5, 5)
    r2 = vm.Run(p, 6, 10, 6, 10, 4)          # one word of variant between them
    merged = vm._merge([r1, r2])
    assert len(merged) == 1 and merged[0].matched == 9 and merged[0].gaps == 1


def test_overlapping_spans_keep_the_longest():
    p = _prayer("a")
    long_, short = vm.Run(p, 0, 8, 10, 18, 8), vm.Run(p, 2, 5, 40, 43, 3)
    assert vm._dedupe_overlaps([short, long_]) == [long_]


# -- the librarian's text handling ---------------------------------------------------------------

def test_set_aside_block_is_split_off():
    body, rows = L.split_set_aside("### v. 1\nx\n\nSET ASIDE\n- v. 2, a: idiom\n- v. 3, b: idiom")
    assert body == "### v. 1\nx" and len(rows) == 2
    assert L.split_set_aside("### v. 1\nx\n\n**SET ASIDE**\n- none")[1] == []


def test_parts_are_merged_with_one_echoes_list():
    out = L.merge_parts(["### v. 1: a\nx\n\n### Echoes in piyyut\n- e1",
                         "### v. 9: b\ny\n\n### Echoes in piyyut, selichot and other works\n- e2"])
    assert out.count("### Echoes") == 1 and out.index("v. 9") < out.index("### Echoes")
    assert out.rstrip().endswith("- e1\n- e2")


def test_headings_are_demoted_under_the_bundle_section():
    assert L.demote_headings("## v. 1\n# x\n### y") == "### v. 1\n### x\n### y"


def test_section_states_the_texts_searched():
    lib = L.LiturgicalLibrarianV2(use_llm=False)
    sec = lib._section(78, "### v. 38: x")
    assert sec.startswith("## Modern Jewish Liturgical Use (Psalm 78)") and "Not searched" in sec


def test_prompt_forbids_restriction_from_absence():
    assert "Never infer a restriction from absence" in L.SYSTEM
    assert "SET ASIDE" in L.SYSTEM


# -- against the real corpus -----------------------------------------------------------------------

@needs_dbs
def test_ps78_38_is_found_in_every_rite_and_its_main_places():
    units = lc.build_units(78)
    u = next(u for u in units if u.verses == (38, 38))
    labels = " | ".join(p.label for p in u.places.values())
    for place in ("Uva LeTzion", "Yehi Chevod", "Hodu", "Barchu"):
        assert place in labels, place
    rites = {h.prayer.nusach for p in u.places.values() for h in p.hits}
    assert {"Ashkenaz", "Sefard", "Edot_HaMizrach", "Chabad"} <= rites


@needs_dbs
def test_ps78_false_positives_are_gone():
    hits = vm.find_hits(78)
    texts = {" ".join(vm.load_psalm(78).keys[h.ps_start:h.ps_end]) for h in hits}
    ps = vm.load_psalm(78)
    zion = " ".join(vm.tokenize("צִיּוֹן אֲשֶׁר").keys)
    assert zion not in texts
    # 78:5's "אשר צוה את אבותינו" in the prayers is 1 Kings 8:57-58
    v5 = [h for h in vm.find_hits(78, keep_dropped=True) if h.verses_touched == (5,) and h.matched == 4]
    assert v5 and all(h.dropped and "Kings" in h.parallel for h in v5)


@needs_dbs
def test_selichot_days_collapse_to_one_place():
    # Ps 89:6 is in the opening of every day's selichot: one place, not one per day.
    u = next(u for u in lc.build_units(89) if u.verses == (6, 6))
    biggest = max(u.places.values(), key=lambda p: len(p.hits))
    assert sum(1 for h in biggest.hits if h.prayer.book.startswith("Selichot Nusach Polin")) >= 10


@needs_dbs
def test_one_side_of_shared_context_does_not_merge_places():
    # 78:38 + Ps 20:10 is both the end of Yehi Chevod and the verses before Barchu.
    u = next(u for u in lc.build_units(78) if u.verses == (38, 38))
    yehi = next(p for p in u.places.values() if p.label.startswith("Yehi Chevod"))
    assert not any("Maariv" in h.prayer.ref for h in yehi.hits)


def test_a_refrain_is_kept_under_both_verses():
    # S395 recall check: 46:8 = 46:12 lost one of the two; a tie on the same prayer span keeps both.
    p = _prayer("a")
    a, b = vm.Run(p, 0, 9, 50, 59, 9), vm.Run(p, 0, 9, 90, 99, 9)
    kept = vm._dedupe_overlaps([a, b])
    assert len(kept) == 2 and kept[0].same_words_at == (90,) and kept[1].same_words_at == (50,)


@needs_dbs
def test_recall_of_the_old_index_on_a_refrain_psalm():
    hits = vm.find_hits(46)
    verses = {v for h in hits for v in h.verses_full + h.verses_touched}
    assert {8, 12} <= verses          # 46:12 is 46:8 plus one word: found as part of v. 12


# -- a reused bundle gets the new section (the author: a re-run must overwrite the old one) -----

_OLD_BUNDLE = ("## Commentaries\n\nx\n\n## Modern Jewish Liturgical Use (Psalm 78)\n\nold summary\n\n"
               "### Phrase-Level Liturgical Usage\n\n#### Phrase: a\n\nold\n\n---\n\n"
               "## Rabbinic and Later Reception\n\nrec\n\n## Research Summary\n\n"
               "- **Liturgical prayers (aggregated)**: 20\n- **Liturgical total occurrences**: 89\n"
               "- **Liturgical Librarian**: gpt-5.1\n")


def test_old_liturgy_section_is_replaced_in_place():
    new = L.LiturgicalLibrarianV2(use_llm=False)._section(78, "### v. 38: x")
    out = L.replace_liturgy_section(_OLD_BUNDLE, new)
    assert "Phrase-Level" not in out and "old summary" not in out
    assert out.index("## Commentaries") < out.index(L.V2_MARKER) < out.index("## Rabbinic and Later Reception")
    assert L.liturgy_section_is_current(out) and not L.liturgy_section_is_current(_OLD_BUNDLE)


def test_a_bundle_without_a_liturgy_section_gets_one_before_reception():
    out = L.replace_liturgy_section("## A\n\nx\n\n## Rabbinic and Later Reception\n\nr\n", "## Modern Jewish Liturgical Use (Psalm 1)\n\nnew")
    assert out.index("new") < out.index("## Rabbinic")


def test_refresh_updates_the_summary_lines_and_leaves_a_current_section_alone(monkeypatch):
    calls = []

    class Fake(L.LiturgicalLibrarianV2):
        def find_liturgical_usage_aggregated(self, n, min_confidence=0.75):
            calls.append(n)
            self._markdown[n] = self._section(n, "### v. 38: x")
            return [L.LiturgyUnitSummary("v. 38", 86, 6), L.LiturgyUnitSummary("v. 49", 18, 5)]

        @property
        def active_model(self):
            return "claude-opus-5-5"

    monkeypatch.setattr(L, "LiturgicalLibrarianV2", Fake)
    monkeypatch.delenv("PSALMS_LITURGY", raising=False)
    out, changed = L.refresh_bundle_liturgy(_OLD_BUNDLE, 78)
    assert changed and "**Liturgical Librarian**: claude-opus-5-5" in out
    assert "(aggregated)**: 2" in out and "occurrences**: 104" in out
    again, changed2 = L.refresh_bundle_liturgy(out, 78)
    assert not changed2 and again == out and calls == [78]
    monkeypatch.setenv("PSALMS_LITURGY", "legacy")
    assert L.refresh_bundle_liturgy(_OLD_BUNDLE, 78) == (_OLD_BUNDLE, False)
