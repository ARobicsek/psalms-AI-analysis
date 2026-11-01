"""Session 412: rhyme clusters (src/concordance/sound_patterns.py)."""

from pathlib import Path

import pytest

from src.concordance import sound_patterns as sp

DB = Path(__file__).parent.parent / "database" / "tanakh.db"
needs_db = pytest.mark.skipif(not (DB.exists() and DB.stat().st_size > 1_000_000), reason="no tanakh.db")


def test_the_rhyme_is_the_last_closed_syllable_without_vowel_letters():
    assert sp.rhyme_key("וּמָגֵן") == sp.rhyme_key("חֵן") == sp.rhyme_key("יִתֵּן") == "e-נ"
    assert sp.rhyme_key("כַּצָּמֶר") == sp.rhyme_key("יְפַזֵּר") == "e-ר"
    assert sp.rhyme_key("אֱלֹהִים") == "i-מ"                 # the plural, left out as grammar
    assert sp.rhyme_key("יְהוָה") is None                    # open syllable
    assert sp.rhyme_key("רוּחַ") == "u-ח"                    # furtive patah


def test_grammar_function_words_and_repeats_do_not_make_a_cluster():
    # plurals rhyme for free
    assert sp.clusters(sp.verse_words("חַטָּאִים רְשָׁעִים לֵצִים")) == {}
    # the preposition אֶל is a function word; אֵל 'God' is not
    assert sp.clusters(sp.verse_words("יַחֵל יִשְׂרָאֵל אֶל־יְהוָה")) == {}
    assert list(sp.clusters(sp.verse_words("וַתְּחוֹלֵל אֶרֶץ וְתֵבֵל אַתָּה אֵל"))) == ["e-ל"]
    # one word three times (with prefixes) is repetition, not rhyme
    assert sp.clusters(sp.verse_words("אֵל הָאֵל וְאֵל")) == {}


@needs_db
def test_four_verses_in_the_psalter_and_84_12_is_one():
    flagged = {(p, v) for p in range(1, 151) for v in sp.compute_sound_patterns(p, DB)[1]}
    assert flagged == {(78, 24), (84, 12), (90, 2), (147, 16)}
    md, verses = sp.compute_sound_patterns(84, DB)
    assert verses == [12] and md.startswith(sp.SECTION_HEADER)
    assert "וּמָגֵן · חֵן · יִתֵּן" in md and "*-en*" in md
    assert "do not claim the sound chose the words" in md
    assert sp.compute_sound_patterns(23, DB) == ("", [])


@needs_db
def test_a_reused_bundle_gets_the_section_once_after_shared_passages():
    bundle = ("## Shared-Vocabulary Parallels\n\nradar\n\n---\n\n## Shared Passages (computed)\n\nlines\n\n---\n\n"
              "## Figurative Language Insights\n\nfig\n")
    out, changed = sp.refresh_bundle_sound_patterns(bundle, 84, DB)
    assert changed and out.index("## Shared Passages") < out.index(sp.SECTION_HEADER) < out.index("## Figurative")
    assert sp.refresh_bundle_sound_patterns(out, 84, DB) == (out, False)
    assert sp.refresh_bundle_sound_patterns(bundle, 23, DB) == (bundle, False)
    no_shared = "## Shared-Vocabulary Parallels\n\nradar\n\n---\n\n## Figurative Language Insights\n\nfig\n"
    out2, _ = sp.refresh_bundle_sound_patterns(no_shared, 84, DB)
    assert out2.index("radar") < out2.index(sp.SECTION_HEADER) < out2.index("## Figurative")
