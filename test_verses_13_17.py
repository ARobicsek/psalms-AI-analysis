"""
Test stress detection on Psalm 145:13-17 with corrected algorithm.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'c:/Users/ariro/OneDrive/Documents/Psalms/src')

from agents.phonetic_analyst import PhoneticAnalyst

# Test verses 13-17
verses = [
    (13, "מַֽלְכוּתְךָ֗ מַלְכ֥וּת כׇּל־עֹלָמִ֑ים וּ֝מֶֽמְשַׁלְתְּךָ֗ בְּכׇל־דּ֥וֹר וָדֹֽר׃"),
    (14, "סוֹמֵ֣ךְ יְ֭הֹוָה לְכׇל־הַנֹּפְלִ֑ים וְ֝זוֹקֵ֗ף לְכׇל־הַכְּפוּפִֽים׃"),
    (15, "עֵֽינֵי־כֹ֭ל אֵלֶ֣יךָ יְשַׂבֵּ֑רוּ וְאַתָּ֤ה נֽוֹתֵן־לָהֶ֖ם אֶת־אׇכְלָ֣ם בְּעִתּֽוֹ׃"),
    (16, "פּוֹתֵ֥חַ אֶת־יָדֶ֑ךָ וּמַשְׂבִּ֖יעַ לְכׇל־חַ֣י רָצֽוֹן׃"),
    (17, "צַדִּ֣יק יְ֭הֹוָה בְּכׇל־דְּרָכָ֑יו וְ֝חָסִ֗יד בְּכׇל־מַעֲשָֽׂיו׃"),
]

def format_verse_output(verse_num, hebrew_text, analyst):
    """Format verse output with stress marking."""
    print(f"## Verse {verse_num}")
    print(f"**Hebrew:** {hebrew_text}")

    # Transcribe the verse
    result = analyst.transcribe_verse(hebrew_text)

    # Build the stressed transcription from individual words
    word_transcriptions = []
    for word_data in result['words']:
        if 'syllable_transcription_stressed' in word_data:
            word_transcriptions.append(word_data['syllable_transcription_stressed'])
        else:
            word_transcriptions.append(word_data.get('syllable_transcription', ''))

    stressed_transcription = ' '.join(word_transcriptions)
    print(f"**Phonetic:** {stressed_transcription}")

    # Count stresses
    primary_count = sum(1 for w in result['words'] if w.get('stress_level', 0) == 2)
    secondary_count = sum(1 for w in result['words'] if w.get('stress_level', 0) == 1)
    total_count = primary_count + secondary_count

    print(f"**Stress count:** {total_count} ({primary_count} primary + {secondary_count} secondary)")
    print()

if __name__ == '__main__':
    analyst = PhoneticAnalyst()

    print("=" * 80)
    print("STRESS-AWARE PHONETIC TRANSCRIPTIONS - Psalm 145:13-17")
    print("=" * 80)
    print()

    for verse_num, hebrew_text in verses:
        format_verse_output(verse_num, hebrew_text, analyst)
        print()
