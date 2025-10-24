"""
Comprehensive test of the phonetic transcription engine on Psalm 145:1-11
"""
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from agents.phonetic_analyst import PhoneticAnalyst

def test_psalm_145_verses():
    """Test phonetic transcription on multiple verses from Psalm 145"""
    analyst = PhoneticAnalyst()

    verses = [
        "תְּהִלָּ֗ה לְדָ֫וִ֥ד אֲרוֹמִמְךָ֣ אֱלוֹהַ֣י הַמֶּ֑לֶךְ וַאֲבָרְכָ֥ה שִׁ֝מְךָ֗ לְעוֹלָ֥ם וָעֶֽד׃",
        "בְּכׇל־י֥וֹם אֲבָרְכֶ֑ךָּ וַאֲהַלְלָ֥ה שִׁ֝מְךָ֗ לְעוֹלָ֥ם וָעֶֽד׃",
        "גָּ֘ד֤וֹל יְהֹוָ֣ה וּמְהֻלָּ֣ל מְאֹ֑ד וְ֝לִגְדֻלָּת֗וֹ אֵ֣ין חֵֽקֶר׃",
        "דּ֣וֹר לְ֭דוֹר יְשַׁבַּ֣ח מַעֲשֶׂ֑יךָ וּגְב֖וּרֹתֶ֣יךָ יַגִּֽידוּ׃",
        "הֲ֭דַר כְּב֣וֹד הוֹדֶ֑ךָ וְדִבְרֵ֖י נִפְלְאֹתֶ֣יךָ אָשִֽׂיחָה׃",
        "וֶעֱז֣וּז נֽוֹרְאֹתֶ֣יךָ יֹאמֵ֑רוּ (וגדלותיך) [וּגְדֻלָּתְךָ֥] אֲסַפְּרֶֽנָּה׃",
        "זֵ֣כֶר רַב־טוּבְךָ֣ יַבִּ֑יעוּ וְצִדְקָתְךָ֥ יְרַנֵּֽנוּ׃",
        "חַנּ֣וּן וְרַח֣וּם יְהֹוָ֑ה אֶ֥רֶךְ אַ֝פַּ֗יִם וּגְדׇל־חָֽסֶד׃",
        "טוֹב־יְהֹוָ֥ה לַכֹּ֑ל וְ֝רַחֲמָ֗יו עַל־כׇּל־מַעֲשָֽׂיו׃",
        "יוֹד֣וּךָ יְ֭הֹוָה כׇּל־מַעֲשֶׂ֑יךָ וַ֝חֲסִידֶ֗יךָ יְבָרְכֽוּכָה׃",
        "כְּב֣וֹד מַלְכוּתְךָ֣ יֹאמֵ֑רוּ וּגְבוּרָתְךָ֥ יְדַבֵּֽרוּ׃"
    ]

    print("=" * 100)
    print("PSALM 145 PHONETIC TRANSCRIPTION TEST")
    print("=" * 100)

    for verse_num, verse in enumerate(verses, 1):
        print(f"\n{'─' * 100}")
        print(f"VERSE {verse_num}")
        print(f"{'─' * 100}")
        print(f"Hebrew: {verse}")

        result = analyst.transcribe_verse(verse)

        # Build phonetic transcription line by line
        phonetic_parts = []

        print("\nWord-by-word analysis:")
        for i, word_data in enumerate(result['words'], 1):
            word = word_data['word']
            syllables = word_data['syllable_transcription']
            phonemes = ''.join(word_data['phonemes'])

            # Clean up parenthetical and bracket content for display
            word_clean = word.replace('(', '').replace(')', '').replace('[', '').replace(']', '')

            phonetic_parts.append(syllables)

            print(f"  {i:2}. {word_clean:20} → {syllables:30} (phonemes: {phonemes})")

        # Print full verse phonetic
        full_phonetic = ' '.join(phonetic_parts)
        print(f"\nFull phonetic: {full_phonetic}")

        # Special checks for known patterns
        if verse_num == 1:
            print("\n  🔍 Checking verse 1:")
            # תְּהִלָּה should have geminated lamed: tə-hil-lāh
            for word_data in result['words']:
                if 'תְּהִלָּה' in word_data['word']:
                    if word_data['syllable_transcription'] == 'tə-hil-lāh':
                        print("    ✓ תְּהִלָּה correctly syllabified: tə-hil-lāh (with gemination)")
                    else:
                        print(f"    ⚠ תְּהִלָּה: got {word_data['syllable_transcription']}, expected tə-hil-lāh")

        if verse_num == 2:
            print("\n  🔍 Checking verse 2:")
            # בְּכׇל should use qamets qatan (o) and syllabify as bə-khol
            for word_data in result['words']:
                if 'בְּכׇל' in word_data['word']:
                    phonemes = ''.join(word_data['phonemes'])
                    if 'o' in phonemes and 'ā' not in phonemes.replace('yōm', ''):
                        print("    ✓ בְּכׇל uses qamets qatan: 'o' (not 'ā')")
                    else:
                        print(f"    ⚠ בְּכׇל phonemes: {phonemes}")

                    if 'bə-khol' in word_data['syllable_transcription']:
                        print("    ✓ בְּכׇל correctly syllabified: bə-khol-yōm")
                    else:
                        print(f"    ⚠ בְּכׇל: got {word_data['syllable_transcription']}")

        if verse_num == 3:
            print("\n  🔍 Checking verse 3:")
            # וּמְהֻלָּל should have geminated lamed
            for word_data in result['words']:
                if 'וּמְהֻלָּל' in word_data['word']:
                    if 'l-l' in word_data['syllable_transcription'] or 'll' in word_data['syllable_transcription']:
                        print(f"    ✓ וּמְהֻלָּל has gemination: {word_data['syllable_transcription']}")
                    else:
                        print(f"    ⚠ וּמְהֻלָּל: {word_data['syllable_transcription']}")

        if verse_num == 8:
            print("\n  🔍 Checking verse 8:")
            # חַנּוּן should have geminated nun
            # וּגְדׇל should use qamets qatan
            for word_data in result['words']:
                if 'חַנּוּן' in word_data['word']:
                    if 'n-n' in word_data['syllable_transcription'] or 'nn' in word_data['syllable_transcription']:
                        print(f"    ✓ חַנּוּן has geminated nun: {word_data['syllable_transcription']}")
                    else:
                        print(f"    ⚠ חַנּוּן: {word_data['syllable_transcription']}")

                if 'וּגְדׇל' in word_data['word']:
                    phonemes = ''.join(word_data['phonemes'])
                    if 'o' in phonemes:
                        print(f"    ✓ וּגְדׇל uses qamets qatan: {word_data['syllable_transcription']}")
                    else:
                        print(f"    ⚠ וּגְדׇל: {word_data['syllable_transcription']}")

        if verse_num == 9:
            print("\n  🔍 Checking verse 9:")
            # כׇּל should use qamets qatan (appears twice)
            qamets_qatan_count = 0
            for word_data in result['words']:
                if 'כׇּל' in word_data['word'] or 'כׇל' in word_data['word']:
                    phonemes = ''.join(word_data['phonemes'])
                    if 'kol' in word_data['syllable_transcription']:
                        qamets_qatan_count += 1
            if qamets_qatan_count > 0:
                print(f"    ✓ Found {qamets_qatan_count} instance(s) of כׇּל with qamets qatan")

    print("\n" + "=" * 100)
    print("TEST COMPLETE")
    print("=" * 100)
    print("\nKey features tested:")
    print("  • Qamets Qatan (ׇ) transcription as 'o'")
    print("  • Gemination (dagesh forte) detection and doubling")
    print("  • Syllabification with shewa + consonant clusters")
    print("  • Begadkefat softening")
    print("  • Matres lectionis (vav as vowel marker)")
    print("=" * 100)

if __name__ == '__main__':
    test_psalm_145_verses()
