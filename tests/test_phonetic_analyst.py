"""
Tests for PhoneticAnalyst: syllabification, stress placement, and the accent
classification the stress depends on.

Every Hebrew string here is real Masoretic text with its cantillation intact --
without the te'amim there is nothing to place the stress from, and the analyst
falls back to the default ultima guess.
"""
import unicodedata
import unittest

from src.agents.phonetic_analyst import PhoneticAnalyst


def nfd(text):
    return unicodedata.normalize('NFD', text)


class PhoneticAnalystTestCase(unittest.TestCase):
    def setUp(self):
        self.analyst = PhoneticAnalyst()

    def stressed(self, word):
        return self.analyst._transcribe_word(nfd(word))['syllable_transcription_stressed']

    def source(self, word):
        return self.analyst._transcribe_word(nfd(word))['stress_source']

    def syllables(self, word):
        return self.analyst._transcribe_word(nfd(word))['syllable_transcription']


class TestStressFromAccents(PhoneticAnalystTestCase):
    """The accent's glyph position is evidence only for impositive accents."""

    def test_mahpakh_beats_the_tsinnorit_beside_it(self):
        # Ps 70:5. U+0598 on the yod is the tsinnorit, a helper tick that marks
        # nothing; the mahpakh on the sin is the accent. Unicode names U+0598
        # "ZARQA", and taking that at face value put the stress on the first
        # syllable: YA-siy-su.
        self.assertEqual(self.stressed('יָ֘שִׂ֤ישׂוּ'), 'yā-SIY-sū')
        self.assertEqual(self.source('יָ֘שִׂ֤ישׂוּ'), 'accent')

    def test_tsinnorit_with_a_zinor_partner_is_the_prose_zarqa(self):
        # Gen 2:23. Same codepoint, opposite job: with only a zinor beside it
        # (which is postpositive), U+0598 does carry the stress.
        self.assertEqual(self.stressed('וַיֹּ֘אמֶר֮'), 'way-YŌ'"'"'-mer')
        self.assertEqual(self.source('וַיֹּ֘אמֶר֮'), 'tsinnorit')

    def test_meteg_does_not_steal_the_stress(self):
        # Gen 1:8. U+05BD here is a meteg on the first letter; the tifcha on the
        # qof is the accent. Rating U+05BD as a primary accent moved the stress
        # onto the meteg in 4,313 words of the Tanakh.
        self.assertEqual(self.stressed('לָֽרָקִ֖יעַ'), 'lā-rā-QIY-aʿ')

    def test_silluq_is_read_as_the_accent(self):
        # The same U+05BD IS the accent on the verse-final word, which is what
        # the sof pasuq identifies.
        self.assertEqual(self.stressed('הָאָֽרֶץ׃'), 'hā-\'Ā-rets')
        self.assertEqual(self.source('הָאָֽרֶץ׃'), 'accent')

    def test_doubled_postpositive_stresses_the_inner_copy(self):
        # Pashta is written on the last letter and copied onto the stressed
        # syllable when the stress is not final; the old rule took the rightmost
        # mark and so always landed on the last letter.
        self.assertEqual(self.stressed('הַמֶּ֙לֶךְ֙'), 'ham-ME-lekh')
        self.assertEqual(self.source('הַמֶּ֙לֶךְ֙'), 'doubled')

    def test_single_postpositive_means_final_stress(self):
        # Only one copy written means no copy was needed: the stress IS final.
        # Checked without the lexicon, since the convention is what is under test
        # (with it, this form is resolved by lookup to the same syllable).
        bare = PhoneticAnalyst(stress_lexicon={})
        result = bare._transcribe_word(nfd('וְיַחְפְּרוּ֮'))
        self.assertEqual(result['syllable_transcription_stressed'], 'wə-yaḥ-pə-RŪ')
        self.assertEqual(result['stress_source'], 'ultima-by-convention')


class TestStressLexicon(PhoneticAnalystTestCase):
    """Dehi, geresh muqdam and ole are prepositive: no positional evidence."""

    def test_dehi_word_resolved_from_the_lexicon(self):
        # Ps 70:4, the case that started this. Dehi sits on the yod whatever the
        # stress, so the analyst used to guess the ultima: ya-shu-VU. Ten other
        # occurrences of the form accent the shin.
        self.assertEqual(self.stressed('יָ֭שׁוּבוּ'), 'yā-SHŪ-vū')
        self.assertEqual(self.source('יָ֭שׁוּבוּ'), 'lexicon')

    def test_more_dehi_words(self):
        self.assertEqual(self.stressed('לָ֭מָּה'), 'LĀM-māh')
        self.assertEqual(self.stressed('בֹּ֭קֶר'), 'BŌ-qer')
        self.assertEqual(self.stressed('תַּ֭חַת'), 'TA-ḥath')

    def test_lexicon_never_overrides_a_real_accent(self):
        # A word whose accent settles the position must not be looked up.
        self.assertEqual(self.source('בׇּשְׁתָּ֑ם'), 'accent')

    def test_missing_lexicon_degrades_to_the_ultima_default(self):
        bare = PhoneticAnalyst(stress_lexicon={})
        result = bare._transcribe_word(nfd('יָ֭שׁוּבוּ'))
        self.assertEqual(result['stress_source'], 'ultima-default')
        self.assertEqual(result['stressed_syllable_index'], 2)


class TestSyllabification(PhoneticAnalystTestCase):
    """Phantom syllables used to appear at the end of words, and drag the
    stress back onto themselves."""

    def test_hiriq_yod_is_one_long_vowel(self):
        # Was 'e-lo-hiy-M: the yod became a consonant and the mem a syllable.
        self.assertEqual(self.stressed('אֱלֹהִ֑ים'), "'e-lō-HIYM")
        self.assertEqual(self.stressed('תָ֭מִיד'), 'thā-MIYDH')
        self.assertEqual(self.syllables('רַבִּים֮'), 'rab-biym')

    def test_tsere_and_segol_yod(self):
        self.assertEqual(self.syllables('מְבַ֫קְשֶׁ֥יךָ'), 'mə-vaq-shey-khā')
        self.assertEqual(self.syllables('אֹ֝הֲבֵ֗י'), "'ō-ha-vēy")

    def test_word_final_consonant_cluster_stays_in_one_syllable(self):
        # Was ro'-SH / 'e-LAYW-w, with the trailing cluster split off.
        self.assertEqual(self.syllables('רֹ֣אשׁ'), "rō'sh")
        self.assertEqual(self.syllables('אֵלָיו֙'), "'ē-lāyw")

    def test_word_final_shewa_is_silent(self):
        # Was le-hith-hal-le-KHE, which both invented a syllable and moved the
        # stress off the last one.
        self.assertEqual(self.stressed('לְ֭הִֽתְהַלֵּךְ'), 'lə-hith-hal-LĒKH')

    def test_second_of_two_shewas_is_vocal(self):
        # Was we-yis-MHU, with an unpronounceable onset cluster.
        self.assertEqual(self.stressed('וְיִשְׂמְח֨וּ'), 'wə-yis-mə-ḤŪ')

    def test_furtive_patah_precedes_its_consonant(self):
        self.assertEqual(self.syllables('רֽוּחַ'), 'rū-aḥ')

    def test_furtive_patah_is_never_stressed_by_the_default(self):
        bare = PhoneticAnalyst(stress_lexicon={})
        result = bare._transcribe_word(nfd('רוּחַ'))  # unaccented -> default applies
        self.assertEqual(result['syllable_transcription_stressed'], 'RŪ-aḥ')


class TestGemination(PhoneticAnalystTestCase):
    """Dagesh forte doubles the letter; dagesh lene and mappiq do not."""

    def test_dagesh_forte_doubles(self):
        self.assertEqual(self.syllables('אַ֑תָּה'), "'at-tāh")
        self.assertEqual(self.syllables('שַׁבָּ֑ת'), 'shab-bāth')
        self.assertEqual(self.syllables('צַדִּיקִֽים׃'), 'tsad-diy-qiym')

    def test_dagesh_lene_does_not_double(self):
        # The pe follows a syllable closed by a silent shewa, so its dagesh is
        # lene: mish-pat, not mish-ppat.
        self.assertEqual(self.syllables('מִשְׁפָּ֑ט'), 'mish-pāt')

    def test_word_initial_dagesh_does_not_double(self):
        # Gen 3:14. A conjunctive dagesh can open a word; doubling it produced
        # the impossible onset "zzo'th".
        self.assertEqual(self.syllables('זֹּאת֒'), "zō'th")

    def test_mappiq_does_not_double(self):
        # Was hal-lu-yah-h, with the mappiq he geminated into its own syllable.
        self.assertEqual(self.syllables('הַ֥לְלוּ־יָֽהּ׃'), 'hal-lū-yāh')

    def test_shewa_under_a_geminated_letter_is_vocal(self):
        # The dagesh-forte rule has to be tested before the short-vowel rule,
        # which would otherwise call this shewa silent: was tid-FEN-nu.
        self.assertEqual(self.stressed('תִּדְּפֶ֥נּוּ'), 'tid-də-FEN-nū')

    def test_geminated_waw_is_not_a_shureq(self):
        # Vav + dagesh is a shureq only with no vowel of its own; with one it is
        # a doubled consonantal waw. Was ha-uh.
        self.assertEqual(self.syllables('חַוָּ֑ה'), 'ḥaw-wāh')

    def test_stress_on_a_geminated_letter_lands_on_the_second_copy(self):
        # The accent on the bet belongs to the syllable the second copy opens.
        self.assertEqual(self.stressed('רַבִּ֥ים'), 'rab-BIYM')


class TestVerseLevel(PhoneticAnalystTestCase):
    def test_paseq_and_section_markers_are_dropped(self):
        # The paseq contributed an empty word (a stray double space in the
        # output) and {פ} was transcribed as a phantom "F".
        verse = 'יָ֘שִׂ֤ישׂוּ וְיִשְׂמְח֨וּ ׀ בְּךָ֗ אֱלֹהִ֑ים׃ {פ}'
        words = self.analyst.transcribe_verse(verse)['words']
        self.assertEqual([w['syllable_transcription'] for w in words],
                         ['yā-siy-sū', 'wə-yis-mə-ḥū', 'bə-khā', "'e-lō-hiym"])

    def test_ketiv_qere_reads_the_qere(self):
        verse = 'וְ֝חוּשָׁ֗ה (חישה) [חֽוּשָׁה׃]'
        words = self.analyst.transcribe_verse(verse)['words']
        self.assertEqual(len(words), 2)
        self.assertEqual(words[1]['syllable_transcription'], 'ḥū-shāh')

    def test_maqqef_compound_is_one_accent_domain(self):
        result = self.analyst._transcribe_word(nfd('עַל־עֵ֣קֶב'))
        self.assertEqual(result['syllable_transcription_stressed'], 'ʿal-ʿĒ-qev')

    def test_full_verse_is_stable(self):
        # Ps 70:4 end to end.
        verse = 'יָ֭שׁוּבוּ עַל־עֵ֣קֶב בׇּשְׁתָּ֑ם הָ֝אֹמְרִ֗ים הֶ֘אָ֥ח ׀ הֶאָֽח׃'
        got = ' '.join(w['syllable_transcription_stressed']
                       for w in self.analyst.transcribe_verse(verse)['words'])
        self.assertEqual(
            got,
            "yā-SHŪ-vū ʿal-ʿĒ-qev bosh-TĀM hā-'ō-mə-RIYM "
            "he-'ĀḤ he-'ĀḤ")


class TestAccentTables(PhoneticAnalystTestCase):
    def test_every_cantillation_mark_is_classified(self):
        # A mark missing from the tables is silently ignored, which is how dehi,
        # segolta, zinor, qarney para, atnah hafukh and merkha kefula used to
        # fall through to the ultima default with nothing in the logs.
        marks = {chr(c) for c in range(0x0591, 0x05AF)} | {'ֽ'}
        self.assertEqual(marks - set(PhoneticAnalyst._ALL_ACCENTS), set())

    def test_classifications_are_disjoint(self):
        groups = [PhoneticAnalyst._POSITION_RELIABLE,
                  PhoneticAnalyst._POSTPOSITIVE,
                  PhoneticAnalyst._PREPOSITIVE,
                  frozenset([PhoneticAnalyst._METEG, PhoneticAnalyst._TSINNORIT])]
        total = sum(len(g) for g in groups)
        self.assertEqual(total, len(PhoneticAnalyst._ALL_ACCENTS))


if __name__ == '__main__':
    unittest.main()
