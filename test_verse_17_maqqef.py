"""
Test maqqef stress on Psalm 145:17 - investigate stress placement.

The user wants maqqef compounds to have stress ONLY on the last word.
Currently: בְּכׇל־דְּרָכָ֑יו has stress on BOTH כׇל AND דְּרָכָ֑יו
Desired: ONLY דְּרָכָ֑יו should be stressed (the last word in the domain)
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, 'src')
from agents.phonetic_analyst import PhoneticAnalyst

analyst = PhoneticAnalyst()

# The verse from user's selection
verse = 'צַדִּ֣יק יְ֭הֹוָה בְּכׇל־דְּרָכָ֑יו וְ֝חָסִ֗יד בְּכׇל־מַעֲשָֽׂיו׃'
print('Verse: צַדִּ֣יק יְ֭הֹוָה בְּכׇל־דְּרָכָ֑יו וְ֝חָסִ֗יד בְּכׇל־מַעֲשָֽׂיו׃')
print()

# Transcribe the full verse
result = analyst.transcribe_verse(verse)

print('=' * 70)
print('CURRENT BEHAVIOR (Session 18 implementation):')
print('=' * 70)
for word_result in result['words']:
    print(f"Word: {word_result['word']}")
    print(f"  Syllables: {word_result['syllable_transcription']}")
    print(f"  Stressed:  {word_result['syllable_transcription_stressed']}")
    print(f"  Stress index: {word_result['stressed_syllable_index']}")
    print()

print()
print('=' * 70)
print('PROBLEM IDENTIFIED:')
print('=' * 70)
print('בְּכׇל־דְּרָכָ֑יו currently shows stress on BOTH components:')
print('  bə-**KHOL**-də-rā-**KHĀW** (2 stresses)')
print()
print('USER WANTS: Only the LAST word in maqqef domain receives stress')
print('  bə-khol-də-rā-**KHĀW** (1 stress, only on last word)')
print()
print('SAME ISSUE for בְּכׇל־מַעֲשָֽׂיו:')
print('  Current: bə-**KHOL**-ma-ʿa-**SĀW**')
print('  Desired: bə-khol-ma-ʿa-**SĀW**')
print()
print()
print('=' * 70)
print('LINGUISTIC RATIONALE:')
print('=' * 70)
print('Maqqef creates ONE ACCENT DOMAIN.')
print('In Hebrew cantillation, only the FINAL word in a domain receives the')
print('main stress/accent mark. Earlier words are unstressed in that domain.')
print()
print('Example: בְּכׇל־דְּרָכָ֑יו')
print('  - בְּכׇל (be-khol) = unstressed (no accent mark in original)')
print('  - דְּרָכָ֑יו (də-rā-khāw) = stressed (has Atnah ֑)')
print('  - Domain = one prosodic unit with stress only on last word')
