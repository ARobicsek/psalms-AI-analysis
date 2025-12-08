#!/usr/bin/env python3
import sys
import re

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from src.concordance.hebrew_text_processor import split_words

# Test cases from Psalm 16
test_cases = [
    'טוֹבָתִי בַּל־עָלֶיךָ',        # Verse 2: "my good not apart from you"
    'קְדוֹשִׁים אֲשֶׁר־בָּאָרֶץ',  # Verse 3: "holy ones who are in the land"
]

for i, phrase in enumerate(test_cases, 1):
    print(f'\n{"=" * 80}')
    print(f'Test Case {i}: {phrase}')
    print(f'{"=" * 80}')

    # OLD METHOD (before fix)
    print('\n[OLD METHOD - Before Fix]')
    clean_old = re.sub(r'[\u0591-\u05C7]', '', phrase)
    print(f'  Result: {clean_old}')
    words_old = split_words(clean_old)
    print(f'  Split: {words_old}')
    print(f'  Number of words: {len(words_old)}')

    # NEW METHOD (after fix)
    print('\n[NEW METHOD - After Fix]')
    phrase_with_spaces = phrase.replace('\u05BE', ' ')
    clean_new = re.sub(r'[\u0591-\u05C7]', '', phrase_with_spaces)
    print(f'  Result: {clean_new}')
    words_new = split_words(clean_new)
    print(f'  Split: {words_new}')
    print(f'  Number of words: {len(words_new)}')

    # Comparison
    if len(words_old) != len(words_new):
        print(f'\n  ✅ FIX WORKS: Word count increased from {len(words_old)} to {len(words_new)}')
    else:
        print(f'\n  ⚠️ No change in word count')

print('\n' + '=' * 80)
print('SUMMARY')
print('=' * 80)
print('\nThe fix replaces maqqef (־) with space BEFORE removing vowel points.')
print('This prevents words from being concatenated when the maqqef is removed.')
