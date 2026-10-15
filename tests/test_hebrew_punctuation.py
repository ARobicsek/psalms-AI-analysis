"""Session 405: modern punctuation for biblical quotations, from the accents in tanakh.db."""

from src.utils.hebrew_punctuation import punctuate_biblical_quotations as P

V8 = 'record: בַּצָּרָה קָרָאתָ וָאֲחַלְּצֶךָּ אֶעֶנְךָ בְּסֵתֶר רַעַם, "In distress you called" (v. 8).'


def test_ole_ve_yored_in_psalms_gets_a_comma_and_the_quotation_end_gets_nothing():
    # Ps 81:8: ole ve-yored on וָאֲחַלְּצֶךָּ; the quotation stops at the etnachta (רַעַם),
    # where the English sentence's own comma already stands.
    assert P(V8) == V8.replace("וָאֲחַלְּצֶךָּ אֶעֶנְךָ", "וָאֲחַלְּצֶךָּ, אֶעֶנְךָ")


def test_two_verses_get_etnachta_commas_and_a_full_stop_between_them_with_converted_names():
    s = "quotes תִּקְעוּ בַחֹדֶשׁ שׁוֹפָר בַּכֵּסֶה לְיוֹם חַגֵּנוּ כִּי חֹק לְיִשְׂרָאֵל הוּא מִשְׁפָּט לֵאלֹקֵי יַעֲקֹב, \"Blow\""
    assert P(s) == ("quotes תִּקְעוּ בַחֹדֶשׁ שׁוֹפָר, בַּכֵּסֶה לְיוֹם חַגֵּנוּ. כִּי חֹק לְיִשְׂרָאֵל הוּא, "
                    "מִשְׁפָּט לֵאלֹקֵי יַעֲקֹב, \"Blow\"")


def test_a_span_the_writer_punctuated_is_left_alone():
    header = "בַּצָּרָה קָרָאתָ וָאֲחַלְּצֶךָּ אֶעֶנְךָ בְּסֵתֶר רַעַם; אֶבְחׇנְךָ עַל־מֵי מְרִיבָה סֶלָה."
    assert P(header) == header


def test_a_cantillated_verse_is_left_alone():
    v = "יְהֹוָה֮ צַדִּ֢יק יִ֫בְחָ֥ן וְ֭רָשָׁע וְאֹהֵ֣ב חָמָ֑ס שָֽׂנְאָ֥ה נַפְשֽׁוֹ׃"
    assert P(v) == v


def test_non_biblical_and_short_spans_are_left_alone():
    sotah = "יוֹסֵף שֶׁקִּדֵּשׁ שֵׁם שָׁמַיִם בַּסֵּתֶר זָכָה וְהוֹסִיפוּ לוֹ אוֹת אַחַת"
    assert P(sotah) == sotah
    short = "וְאֹהֵב חָמָס שָׂנְאָה"   # three words: too short to trust a match
    assert P(short) == short


def test_maqaf_joined_words_and_bold_letters_still_match():
    s = "שֹׁמֵר כׇּל־עַצְמוֹתָיו אַחַת מֵהֵנָּה לֹא נִשְׁבָּרָה"          # Ps 34:21
    assert P(s) == "שֹׁמֵר כׇּל־עַצְמוֹתָיו, אַחַת מֵהֵנָּה לֹא נִשְׁבָּרָה"
    b = "שֹׁמֵר כׇּל־**עַצְמוֹתָיו** אַחַת מֵהֵנָּה לֹא נִשְׁבָּרָה"
    assert P(b) == "שֹׁמֵר כׇּל־**עַצְמוֹתָיו**, אַחַת מֵהֵנָּה לֹא נִשְׁבָּרָה"


def test_idempotent():
    assert P(P(V8)) == P(V8)


def test_a_quotation_ends_with_its_translations_end_mark():
    """Session 405: `X, "Translation."` -> `X. "Translation."` for a quotation of 3+ words."""
    from src.utils.hebrew_punctuation import end_hebrew_quotations as E
    s = 'the hinge: שְׂפַת לֹא־יָדַעְתִּי אֶשְׁמָע, "A language I did not know I hear." Ancient'
    assert E(s) == s.replace('אֶשְׁמָע, "', 'אֶשְׁמָע. "')
    cited = 'record: אֶעֶנְךָ בְּסֵתֶר רַעַם, "I answered you from the thunder" (v. 8). Yet'
    assert E(cited) == cited.replace('רַעַם, "', 'רַעַם. "')
    q = 'Amos asks הֲיִתֵּן כְּפִיר קוֹלוֹ, "does a young lion give voice?" and'
    assert E(q) == q.replace('קוֹלוֹ, "', 'קוֹלוֹ? "')
    for same in ('After חַגֵּנוּ, "our feast day," in verse 4',                          # a term
                 'says שְׁמַע עַמִּי וְאָעִידָה בָּךְ, "Hear, My people," and then',          # runs on
                 'words—וּמִצּוּר דְּבַשׁ אַשְׂבִּיעֶ**ךָ**, "I would sate **you**"—He'):  # runs on
        assert E(same) == same
    assert E(E(s)) == E(s)
