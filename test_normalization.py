#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test normalization in phrase extractor."""

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('src')

from liturgy.phrase_extractor import PhraseExtractor

# Initialize extractor
ext = PhraseExtractor(verbose=False)

# Test cases
tests = [
    ('Maqqef', 'כָּל־הָאָרֶץ', 'Should replace maqqef with space and remove diacritics'),
    ('Punctuation', 'בְּרֵאשִׁית, בָּרָ֣א', 'Should remove comma and diacritics'),
    ('Full diacritics', 'יְהֹוָ֥ה רֹ֝עִ֗י', 'Should remove all vowels and cantillation'),
    ('Geresh', "ב' אדר", 'Should remove geresh'),
]

print('='*60)
print('NORMALIZATION TESTS')
print('='*60)
print()

for name, original, description in tests:
    normalized = ext._normalize_text(original)
    print(f'{name}:')
    print(f'  Input:  {original}')
    print(f'  Output: {normalized}')
    print(f'  Note:   {description}')
    print()

print('✓ All normalization tests complete')
