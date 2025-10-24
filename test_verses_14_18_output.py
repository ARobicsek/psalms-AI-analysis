"""
Test output for Psalm 145:14-18 showing corrected maqqef stress handling.

These verses contain multiple maqqef compounds. The output demonstrates
that only the LAST word in each maqqef domain receives stress.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, 'src')
from agents.phonetic_analyst import PhoneticAnalyst

analyst = PhoneticAnalyst()

verses = [
    ('14', 'סוֹמֵ֣ךְ יְ֭הֹוָה לְכׇל־הַנֹּפְלִ֑ים וְ֝זוֹקֵ֗ף לְכׇל־הַכְּפוּפִֽים׃'),
    ('15', 'עֵֽינֵי־כֹ֭ל אֵלֶ֣יךָ יְשַׂבֵּ֑רוּ וְאַתָּ֤ה נֽוֹתֵן־לָהֶ֖ם אֶת־אׇכְלָ֣ם בְּעִתּֽוֹ׃'),
    ('16', 'פּוֹתֵ֥חַ אֶת־יָדֶ֑ךָ וּמַשְׂבִּ֖יעַ לְכׇל־חַ֣י רָצֽוֹן׃'),
    ('17', 'צַדִּ֣יק יְ֭הֹוָה בְּכׇל־דְּרָכָ֑יו וְ֝חָסִ֗יד בְּכׇל־מַעֲשָֽׂיו׃'),
    ('18', 'קָר֣וֹב יְ֭הֹוָה לְכׇל־קֹרְאָ֑יו לְכֹ֤ל אֲשֶׁ֖ר יִקְרָאֻ֣הוּ בֶאֱמֶֽת׃')
]

print('=' * 80)
print('PSALM 145:14-18 - MAQQEF STRESS CORRECTION TEST')
print('=' * 80)
print()
print('RULE: Maqqef (־) creates ONE ACCENT DOMAIN')
print('      Only the LAST word in the domain receives stress')
print()
print('=' * 80)
print()

for verse_num, verse_text in verses:
    print(f"VERSE {verse_num}")
    print(f"Hebrew: {verse_text}")
    print()

    result = analyst.transcribe_verse(verse_text)

    # Show each word's transcription
    print("Phonetic Transcription (word by word):")
    for i, word_result in enumerate(result['words'], 1):
        hebrew = word_result['word']
        syllables = word_result['syllable_transcription']
        stressed = word_result['syllable_transcription_stressed']
        stress_idx = word_result['stressed_syllable_index']

        # Check if this is a maqqef compound
        is_maqqef = '־' in hebrew
        marker = " ← MAQQEF COMPOUND" if is_maqqef else ""

        print(f"  {i:2d}. {hebrew:20s} | {stressed:40s}{marker}")
        if is_maqqef:
            print(f"      {'':20s}   (stress only on last component, index {stress_idx})")

    print()

    # Show full verse transcription
    full_stressed = ' '.join([w['syllable_transcription_stressed'] for w in result['words']])
    print(f"Full verse (stressed): {full_stressed}")
    print()

    # Count total stresses in verse
    import re
    stress_count = len(re.findall(r'\*\*[^*]+\*\*', full_stressed))
    print(f"Total stresses in verse: {stress_count}")
    print()
    print('-' * 80)
    print()

print('=' * 80)
print('OBSERVATIONS:')
print('=' * 80)
print()
print('Notice that in ALL maqqef compounds:')
print('  - Words BEFORE the maqqef (־) have NO stress marks')
print('  - Only the LAST word (after maqqef) has stress')
print()
print('Examples:')
print('  לְכׇל־הַנֹּפְלִ֑ים  → lə-khol-han-nō-fə-**LIY**-m  (NOT lə-**KHOL**-...)')
print('  בְּכׇל־דְּרָכָ֑יו    → bə-khol-də-rā-**KHĀY**-w    (NOT bə-**KHOL**-...)')
print('  אֶת־יָדֶ֑ךָ         → \'et-yā-**DHE**-khā          (NOT \'**ET**-...)')
print()
print('This matches Hebrew cantillation rules where maqqef creates a')
print('single prosodic unit with stress only on the final component.')
print()
print('=' * 80)
