"""Session 392: Rabbi Sacks rebuilt from Sefaria (src/data_sources/sacks_index.py + the librarian's rules).

All offline: the harvest's pure parts and the librarian's selection, on hand-built data.
"""
import pytest

from src.agents import sacks_librarian as sl
from src.agents.sacks_librarian import SacksLibrarian, SacksReference, count_references_in_bundle, select
from src.data_sources import sacks_index as si
from src.data_sources.sefaria_reception import tokens

PS = {  # a tiny 'Book of Psalms' for the aligner
    1: ["אַשְׁרֵי הָאִישׁ אֲשֶׁר לֹא הָלַךְ בַּעֲצַת רְשָׁעִים וּבְדֶרֶךְ חַטָּאִים לֹא עָמָד",
        "כִּי אִם בְּתוֹרַת יְהוָה חֶפְצוֹ וּבְתוֹרָתוֹ יֶהְגֶּה יוֹמָם וָלָיְלָה"],
    23: ["מִזְמוֹר לְדָוִד יְהוָה רֹעִי לֹא אֶחְסָר",
         "בִּנְאוֹת דֶּשֶׁא יַרְבִּיצֵנִי עַל מֵי מְנֻחוֹת יְנַהֲלֵנִי",
         "נַפְשִׁי יְשׁוֹבֵב יַנְחֵנִי בְמַעְגְּלֵי צֶדֶק לְמַעַן שְׁמוֹ",
         "גַּם כִּֽי־אֵלֵךְ בְּגֵיא צַלְמָוֶת לֹא אִירָא רָע כִּי אַתָּה עִמָּדִי שִׁבְטְךָ וּמִשְׁעַנְתֶּךָ הֵמָּה יְנַחֲמֻנִי"],
}


# --- text helpers --------------------------------------------------------------------------------
def test_footnotes_with_a_nested_title_are_removed_whole():
    raw = ('torn open in a wind.”<sup class="footnote-marker">1</sup><i class="footnote"><i>Good as Gold</i> '
           '(New York: Simon &amp; Schuster, 1997), 72.</i> It is instead a drama.')
    out = si.clean(raw)
    assert "Simon" not in out and "72" not in out and "Good as Gold" not in out
    assert out.startswith("torn open in a wind.”") and out.endswith("It is instead a drama.")


def test_split_ref_handles_ranges_and_compound_titles():
    assert si.split_ref("The Koren Shalem Siddur; Ashkenaz, Weekdays, The Daily Psalm 4") == \
        ("The Koren Shalem Siddur; Ashkenaz, Weekdays, The Daily Psalm", [4])
    assert si.split_ref("Rabbi Sacks on Siddur, Shabbat, Kabbalat Shabbat 4-6")[1] == [4, 5, 6]
    assert si.split_ref("Psalms 23:4")[0] == "Psalms"


def test_the_maqaf_separates_words_before_the_niqqud_is_stripped():
    """S392: U+05BE lies inside the niqqud range, so כִּֽי־אֵלֵךְ fused into one token (also in reception)."""
    assert tokens("גַּם כִּֽי־אֵלֵךְ בְּגֵיא") == ["גמ", "כי", "אלכ", "בגיא"]


def test_search_queries_get_their_final_letters_back():
    assert [si.query_word(t) for t in tokens("גַּם כִּי אֵלֵךְ")] == ["גם", "כי", "אלך"]


def test_hebrew_lemma_is_the_comments_opening_hebrew():
    assert si.hebrew_lemma("לְדָוִד, יהוה אוֹרִי Psalm 27. A psalm of surpassing beauty") == "לְדָוִד, יהוה אוֹרִי"
    assert si.hebrew_lemma("*Psalm 23:* One of the most sublime passages") == ""


# --- alignment -----------------------------------------------------------------------------------
def test_a_paragraph_holding_the_whole_psalm_aligns_to_every_verse():
    al = si.PsalmAligner(PS)
    para = " ".join(PS[23])                         # the siddur prints the psalm as one paragraph
    assert al.verses_in(para) == {23: [1, 2, 3, 4]}
    assert si.classify([1, 2, 3, 4], 4, 0) == "whole"


def test_a_short_shared_phrase_is_not_a_verse():
    al = si.PsalmAligner(PS)
    assert al.verses_in("ובדרך חטאים הלך האיש") == {}       # a few words of 1:1, not a run of 60%
    assert al.verses_in("כי אם בתורת יהוה חפצו ובתורתו יהגה יומם ולילה") == {1: [2]}
    assert si.classify([2], 2, 0) == "verse"


# --- passages ------------------------------------------------------------------------------------
def test_a_passage_takes_neighbours_but_never_ends_on_a_colon():
    paras = ["Before.", "The linked paragraph quotes the psalm.", "He recalled a picture:", "The picture."]
    text, span = si.compose_passage(paras, 2, target=70)        # the quotation itself does not fit
    assert text == "Before.\n\nThe linked paragraph quotes the psalm." and span == (1, 2)
    text, _ = si.compose_passage(paras, 2, target=200)          # when it fits, the lead-in stays
    assert text.endswith("He recalled a picture:\n\nThe picture.")


def test_an_overlong_paragraph_is_cut_at_a_sentence_and_marked():
    long = ("A sentence of moderate length. " * 200).strip()
    text, _ = si.compose_passage([long], 1, hard_max=1000)
    assert text.endswith(". […]") and len(text) <= 1010


def test_books_exclude_the_liturgical_works_and_the_duplicate_editions():
    toc = [{"category": "Tanakh", "contents": [{"category": "Modern Commentary on Tanakh", "contents": [
        {"category": "Jonathan Sacks", "contents": [
            {"title": "Covenant and Conversation; Exodus; The Book of Redemption"},
            {"title": "Covenant and Conversation; Hebrew Edition"},
            {"title": "Covenant and Conversation Family Edition"}]}]}]},
        {"category": "Liturgy", "contents": [{"category": "Siddur", "contents": [{"title": "Rabbi Sacks on Siddur"}]}]},
        {"category": "Jewish Thought", "contents": [{"category": "Modern", "contents": [
            {"category": "Rabbi Lord Jonathan Sacks", "contents": [{"title": "The Great Partnership; God, Science"}]},
            {"category": "Rav Kook", "contents": [{"title": "Orot"}]}]}]}]
    assert si.book_titles(toc) == ["Covenant and Conversation; Exodus; The Book of Redemption",
                                   "The Great Partnership; God, Science"]


# --- the librarian's rules -----------------------------------------------------------------------
def _comment(ref, verses, text, lemma="", work="Rabbi Sacks on Siddur", whole_elsewhere=()):
    return {"work": work, "ref": ref, "section": "Shabbat, Kabbalat Shabbat", "lemma": lemma, "text": text,
            "verses": verses, "whole_elsewhere": list(whole_elsewhere)}


def _book(ref, verses, text, source="link", lang="en"):
    return {"work": "Studies in Spirituality", "ref": ref, "section": "Noah; X", "verses": verses,
            "source": source, "lang": lang, "text": text}


def test_a_single_verse_comment_needs_two_lemma_words_in_the_verse_or_the_psalm_named():
    data = {"psalm": 23, "verses": 4, "books": [], "liturgical": [
        _comment("A 1", [1], "Mizmor: a comment about some other prayer entirely.", lemma="מִזְמוֹר"),  # one word
        _comment("A 2", [4], "Though I walk: a comment on these words.", lemma="גַּם כִּי אֵלֵךְ"),     # two+ words
        _comment("A 3", [4], "As Psalm 23 says, a comment on a mosaic.", lemma="שׁוֹמֵעַ תְּפִלָּה"),   # named
        _comment("A 4", [4], "A comment on Psalm 19's paragraph.", lemma="גַּם כִּי אֵלֵךְ", whole_elsewhere=[19]),
    ]}
    kept = [r.ref for r in select(data, PS[23])]
    assert kept == ["A 2", "A 3"]


def test_whole_psalm_comments_come_first_and_reprints_merge():
    words = "the psalm is a meditation on trust and on the shepherd who leads through the dark valley"
    data = {"psalm": 23, "verses": 4, "books": [], "liturgical": [
        _comment("Mahzor 9", [1, 2, 3, 4], words + " said at the close of the day.", work="Rabbi Sacks on Yom Kippur Mahzor"),
        _comment("Siddur 3", [1, 2, 3, 4], words + " said at the close of Shabbat."),
        _comment("Siddur 7", [2, 3], "A different comment on two verses, about green pastures and still waters."),
    ]}
    refs = select(data, PS[23])
    assert [r.ref for r in refs] == ["Siddur 3", "Siddur 7"]
    assert refs[0].scope == "whole" and refs[0].also == ["Mahzor 9"]


def test_book_passages_are_capped_per_verse_english_and_linked_first():
    books = [_book(f"S {i}", [4], f"Essay number {i} has entirely different words {'x' * i} about courage.",
                   source="search" if i == 0 else "link", lang="he" if i == 1 else "en") for i in range(7)]
    books.append(_book("S v1", [1], "The Lord is my shepherd, a unique essay on animals and their care."))
    refs = select({"psalm": 23, "verses": 4, "liturgical": [], "books": books}, PS[23])
    v4 = [r.ref for r in refs if r.verses == [4]]
    assert len(v4) == sl.BOOKS_PER_VERSE
    assert "S 1" not in v4 and "S 0" not in v4             # the Hebrew translation and the search find wait
    assert "S v1" in [r.ref for r in refs]


def test_the_budget_stops_the_book_passages():
    abc = "abcdefghijklmnopqrstuvwxyz"
    books = [_book(f"S {i}", [i % 4 + 1], " ".join(abc[i] + abc[j % 26] + abc[j // 26 % 26] for j in range(400)))
             for i in range(12)]                     # distinct texts (identical ones would merge as reprints)
    refs = select({"psalm": 23, "verses": 4, "liturgical": [], "books": books}, PS[23], max_chars=5000)
    assert sum(len(r.text) for r in refs) <= 5000 and len(refs) >= 2


def test_the_section_format_keeps_the_counter_and_labels_translations_and_search_finds():
    refs = [SacksReference("prayer book", "Rabbi Sacks on Siddur", "Shabbat, Se'uda Shelishit for Shabbat",
                           "Rabbi Sacks on Siddur, Shabbat, Se'uda Shelishit for Shabbat 3", [1, 2, 3, 4], "whole", "Text."),
            SacksReference("book", "The Great Partnership; God", "I; Finding God", "The Great Partnership; God, I; Finding God 72",
                           [4], "verse", "טקסט בעברית.", "search", lang="he")]
    md = SacksLibrarian().format_for_research_bundle(refs, 23)
    assert md.startswith("## Rabbi Jonathan Sacks on Psalm 23\n")
    assert count_references_in_bundle(md) == 2
    assert "Koren Siddur, Se'uda Shelishit for Shabbat (on the whole psalm)" in md
    assert "Hebrew translation (Maggid)" in md and "phrase search" in md
    assert "Chief Rabbi" in md and len(md.split("\n\n")[1]) < 500          # one short introduction, not a biography


def test_a_sefaria_failure_omits_the_section_instead_of_failing(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("Sefaria is down")
    monkeypatch.setattr(si, "harvest_psalm", boom)
    assert SacksLibrarian().get_psalm_references(23) == []


def test_a_question_mark_in_a_title_is_escaped_in_the_url():
    assert "%3F" in si._quote("Essays in Ethics; A Weekly Reading, Vayikra; What Do We Sacrifice?")
