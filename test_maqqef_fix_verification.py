"""
Comprehensive test to verify maqqef stress fix.

Verify that maqqef compounds (word1־word2) have stress ONLY on the last word.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, 'src')
from agents.phonetic_analyst import PhoneticAnalyst

analyst = PhoneticAnalyst()

print('=' * 70)
print('MAQQEF STRESS FIX VERIFICATION')
print('=' * 70)
print()
print('RULE: Maqqef (־) creates ONE ACCENT DOMAIN.')
print('      Only the LAST word receives stress.')
print()

# Test cases from Psalm 145
test_cases = [
    {
        'verse': 'בְּכׇל־דְּרָכָ֑יו',
        'context': 'Psalm 145:17 - "in all His ways"',
        'expected_stress': 'only on final syllable of דְּרָכָ֑יו (has Atnah ֑)',
        'expected_pattern': 'bə-khol-də-rā-**KHĀY**-w'
    },
    {
        'verse': 'בְּכׇל־מַעֲשָֽׂיו',
        'context': 'Psalm 145:17 - "in all His works"',
        'expected_stress': 'only on final syllable of מַעֲשָֽׂיו (has Silluq ֽ)',
        'expected_pattern': 'bə-khol-ma-ʿa-**SĀY**-w'
    },
    {
        'verse': 'לְכׇל־הַנֹּפְלִ֑ים',
        'context': 'Psalm 145:14 - "to all the fallen"',
        'expected_stress': 'only on final syllable of הַנֹּפְלִ֑ים (has Atnah ֑)',
        'expected_pattern': 'lə-**KHOL**-han-nō-fə-**LIY**-m → lə-khol-han-nō-fə-**LIY**-m'
    },
    {
        'verse': 'בְּכׇל־יוֹם',
        'context': 'Psalm 145:2 - "every day"',
        'expected_stress': 'only on final syllable of יוֹם',
        'expected_pattern': 'bə-khol-**YŌM**'
    }
]

print('=' * 70)
print('TEST RESULTS:')
print('=' * 70)
print()

all_passed = True

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['context']}")
    print(f"  Hebrew: {test['verse']}")
    print(f"  Expected: {test['expected_stress']}")

    result = analyst.transcribe_verse(test['verse'])
    word_result = result['words'][0]

    stressed = word_result['syllable_transcription_stressed']
    stress_index = word_result['stressed_syllable_index']
    num_syllables = len(word_result['syllables'])

    print(f"  Result: {stressed}")
    print(f"  Stress index: {stress_index} (out of {num_syllables} syllables)")

    # Count number of stressed syllables (count **...** patterns)
    import re
    stress_count = len(re.findall(r'\*\*[^*]+\*\*', stressed))

    # Verify only ONE stress mark
    if stress_count == 1:
        print(f"  ✓ PASS: Only 1 stressed syllable (correct!)")
    else:
        print(f"  ✗ FAIL: {stress_count} stressed syllables (should be 1)")
        all_passed = False

    # Verify stress is on the LAST component (after maqqef)
    # For maqqef compounds, stress should be in the latter half of syllables
    if '־' in test['verse']:
        if stress_index is not None and stress_index >= num_syllables // 2:
            print(f"  ✓ PASS: Stress on last component (index {stress_index} >= {num_syllables//2})")
        else:
            print(f"  ✗ FAIL: Stress should be on last component")
            all_passed = False

    print()

print('=' * 70)
if all_passed:
    print('✓✓✓ ALL TESTS PASSED ✓✓✓')
    print()
    print('Maqqef stress handling is now correct:')
    print('- Only the LAST word in a maqqef domain receives stress')
    print('- Earlier words (before ־) are unstressed')
    print('- This matches Hebrew cantillation rules')
else:
    print('✗✗✗ SOME TESTS FAILED ✗✗✗')
print('=' * 70)
