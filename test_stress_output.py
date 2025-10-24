"""
Test the enhanced PhoneticAnalyst with stress detection on Psalm 145:7-13.
This will output the verses with stressed syllables in **BOLD CAPS**.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'c:/Users/ariro/OneDrive/Documents/Psalms/src')

from agents.phonetic_analyst import PhoneticAnalyst

# Test verses from Psalm 145
verses = [
    (7, "זֵ֣כֶר רַב־טוּבְךָ֣ יַבִּ֑יעוּ וְצִדְקָתְךָ֥ יְרַנֵּֽנוּ׃"),
    (8, "חַנּ֣וּן וְרַח֣וּם יְהֹוָ֑ה אֶ֥רֶךְ אַ֝פַּ֗יִם וּגְדׇל־חָֽסֶד׃"),
    (9, "טוֹב־יְהֹוָ֥ה לַכֹּ֑ל וְ֝רַחֲמָ֗יו עַל־כׇּל־מַעֲשָֽׂיו׃"),
    (10, "יוֹד֣וּךָ יְ֭הֹוָה כׇּל־מַעֲשֶׂ֑יךָ וַ֝חֲסִידֶ֗יךָ יְבָרְכֽוּכָה׃"),
    (11, "כְּב֣וֹד מַלְכוּתְךָ֣ יֹאמֵ֑רוּ וּגְבוּרָתְךָ֥ יְדַבֵּֽרוּ׃"),
    (12, "לְהוֹדִ֤יעַ ׀ לִבְנֵ֣י הָ֭אָדָם גְּבוּרֹתָ֑יו וּ֝כְב֗וֹד הֲדַ֣ר מַלְכוּתֽוֹ׃"),
    (13, "מַֽלְכוּתְךָ֗ מַלְכ֥וּת כׇּל־עֹלָמִ֑ים וּ֝מֶֽמְשַׁלְתְּךָ֗ בְּכׇל־דּ֥וֹר וָדֹֽר׃"),
]

def test_verses():
    """Test stress detection on all verses."""
    analyst = PhoneticAnalyst()

    print("=" * 80)
    print("STRESS-AWARE PHONETIC TRANSCRIPTIONS - Psalm 145:7-13")
    print("=" * 80)
    print()

    for verse_num, hebrew_text in verses:
        print(f"## Verse {verse_num}")
        print(f"**Hebrew:** {hebrew_text}")

        # Transcribe the verse
        result = analyst.transcribe_verse(hebrew_text)

        # Build the stressed transcription from individual words
        word_transcriptions = []
        for word_data in result['words']:
            # Use the stressed version if available, otherwise use regular
            if 'syllable_transcription_stressed' in word_data:
                word_transcriptions.append(word_data['syllable_transcription_stressed'])
            else:
                word_transcriptions.append(word_data.get('syllable_transcription', ''))

        stressed_transcription = ' '.join(word_transcriptions)

        print(f"**Phonetic (with stress):** {stressed_transcription}")
        print()

        # Show detailed word-by-word analysis
        print("Word-by-word breakdown:")
        for i, word_data in enumerate(result['words'], 1):
            hebrew_word = word_data.get('word', '')
            regular = word_data.get('syllable_transcription', '')
            stressed = word_data.get('syllable_transcription_stressed', '')
            stress_level = word_data.get('stress_level', 0)

            stress_desc = ""
            if stress_level == 2:
                stress_desc = " (PRIMARY STRESS)"
            elif stress_level == 1:
                stress_desc = " (secondary stress)"

            print(f"  {i}. {hebrew_word:20s} → {stressed:30s}{stress_desc}")

        print()
        print("-" * 80)
        print()

if __name__ == '__main__':
    test_verses()
