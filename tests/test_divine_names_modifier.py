"""The divine-names converter (src/utils/divine_names_modifier.py).

Session 398: the writer now spells every name in full and the converter alone makes the printed
guide (essay, notes, liturgy, the writer's-reasoning appendix) geniza-safe. Ps 78/79 printed
אֲדֹנָי and יָהּ unconverted; these tests pin the new names, the profane look-alikes that must be
left alone, and a few of the older conversions.
"""

import pytest

from src.utils.divine_names_modifier import DivineNamesModifier

M = DivineNamesModifier()


@pytest.mark.parametrize("before, after", [
    # Adonai, pointed (with and without cantillation, prefixed, after maqaf)
    ("וַיִּקַץ כְּיָשֵׁן ׀ אֲדֹנָי, כְּגִבּוֹר", "וַיִּקַץ כְּיָשֵׁן ׀ אֲדֹ‑נָי, כְּגִבּוֹר"),
    ("חֶרְפָּתָם אֲשֶׁר חֵרְפוּךָ אֲדֹנָֽי׃", "חֶרְפָּתָם אֲשֶׁר חֵרְפוּךָ אֲדֹ‑נָֽי׃"),
    ("וַיִּקַ֖ץ כְּיָשֵׁ֥ן ׀ אֲדֹנָ֑י", "וַיִּקַ֖ץ כְּיָשֵׁ֥ן ׀ אֲדֹ‑נָ֑י"),
    ("וְאֶל־אֲדֹנָי אֶתְחַנָּן", "וְאֶל־אֲדֹ‑נָי אֶתְחַנָּן"),
    ("לַאדֹנָי הַיְשׁוּעָה", "לַאדֹ‑נָי הַיְשׁוּעָה"),
    ("For verse 65 with אֲדֹנָי, I'll quote", "For verse 65 with אֲדֹ‑נָי, I'll quote"),
    # Adonai, unpointed and bare
    ("the pasek between יזנח and אדני, and", "the pasek between יזנח and אד‑ני, and"),
    # Yah
    ("אֶזְכּוֹר מַעַלְלֵי־יָהּ, \"I will", "אֶזְכּוֹר מַעַלְלֵי־יָ‑הּ, \"I will"),
    ("יָהּ, דַּע אֶת יִשְׂרָאֵל", "יָ‑הּ, דַּע אֶת יִשְׂרָאֵל"),
    ("בְּיָהּ שְׁמוֹ", "בְּיָ‑הּ שְׁמוֹ"),
    ("הַלְלוּ־יָהּ", "הַלְלוּ־יָ‑הּ"),
    ("הַלְלוּיָהּ", "הַלְלוּיָ‑הּ"),
    ("הללויה", "הללוי‑ה"),
    # inside curly quotes (Pss 16, 17, 18 printed these unconverted)
    ("(“אֲדֹנָי שְׁמָעָה…”)", "(“אֲדֹ‑נָי שְׁמָעָה…”)"),
    ("The address “אֵל” (“God”)", "The address “קֵל” (“God”)"),
    ("“הָאֵל הַנּוֹתֵן נְקָמוֹת לִי”", "“הָקֵל הַנּוֹתֵן נְקָמוֹת לִי”"),
    # a bolded prefix splits the word (Ps 74)
    ("**וֵ**אלֹהִים opens with", "**וֵ**אלֹקִים opens with"),
    ("the vav before אלֹהִים needs", "the vav before אלֹקִים needs"),
    # Ehyeh, as the Exod 3:14 name
    ("אֶהְיֶה אֲשֶׁר אֶהְיֶה (Exod 3:14)", "אֶ‑הְיֶה אֲשֶׁר אֶ‑הְיֶה (Exod 3:14)"),
])
def test_names_the_writer_now_spells_in_full_are_converted(before, after):
    assert M.modify_text(before) == after


@pytest.mark.parametrize("text", [
    "אֲדֹנִי הַמֶּלֶךְ",          # 'my lord' (hiriq)
    "הִנֶּה נָּא אֲדֹנַי",         # 'my lords' (patah), Gen 19:2
    "לאדני המלך",                 # prefixed and unpointed: could be 'to my lord'
    "הָיָה",                      # yod-he inside a word
    "יה",                         # unpointed yod-he, no mappiq: ambiguous
    "פִּרְיָהּ",                  # 'her fruit': yod-he with mappiq, not on a word boundary
    "וְאֶהְיֶה לָכֶם לֵאלֹקִים",   # the verb 'I will be'
])
def test_profane_look_alikes_are_left_alone(text):
    assert M.modify_text(text) == text


def test_the_split_is_a_non_breaking_hyphen():
    """An ASCII hyphen lets Word break the name across two lines (Ps 79:12 in the psalm table)."""
    assert M.modify_text("אֲדֹנָי") == "אֲדֹ\u2011נָי"
    assert "-" not in M.modify_text("אֲדֹנָי יָהּ הַלְלוּיָהּ אדני אֶהְיֶה אֲשֶׁר אֶהְיֶה")


def test_the_docx_keeps_a_converted_name_in_one_hebrew_run():
    from src.utils.document_generator import DocumentGenerator
    segs = DocumentGenerator._segment_by_script("for You, O Lord: " + M.modify_text("חֵרְפוּךָ אֲדֹנָי."))
    assert ("חֵרְפוּךָ אֲדֹ\u2011נָי", True) in segs, segs


def test_converting_twice_changes_nothing():
    text = ("אֲדֹנָי יָהּ הַלְלוּיָהּ אדני אֶהְיֶה אֲשֶׁר אֶהְיֶה "
            "יְהוָה אֱלֹהִים אֵל שַׁדַּי צְבָאוֹת")
    once = M.modify_text(text)
    assert M.modify_text(once) == once


@pytest.mark.parametrize("before, after", [
    ("יְהוָה", "ה׳"),
    ("יהוה", "ה׳"),
    ("אֲדֹנָי יֱהֹוִה", "אֲדֹ‑נָי ה׳"),
    ("אֱלֹהִים בָּאוּ גוֹיִם", "אֱלֹקִים בָּאוּ גוֹיִם"),
    ("הָאֵל הַגָּדוֹל", "הָקֵל הַגָּדוֹל"),
    ("צְבָאוֹת", "צְבָקוֹת"),
])
def test_the_older_conversions_still_hold(before, after):
    assert M.modify_text(before) == after


def test_the_preposition_el_and_names_ending_in_el_are_left_alone():
    text = "אֶל־הַגּוֹיִם יִשְׂרָאֵל"
    assert M.modify_text(text) == text
