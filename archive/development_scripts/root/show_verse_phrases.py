#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Show all phrases extracted from Psalm 1:1."""

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('src')

from liturgy.phrase_extractor import PhraseExtractor
from concordance.hebrew_text_processor import split_words, clean_hebrew_text

# Psalm 1:1 text
verse_text = "אַ֥שְֽׁרֵי־הָאִ֗ישׁ אֲשֶׁ֤ר ׀ לֹ֥א הָלַךְ֮ בַּעֲצַ֢ת רְשָׁ֫עִ֥ים וּבְדֶ֣רֶךְ חַ֭טָּאִים לֹ֥א עָמָ֑ד וּבְמוֹשַׁ֥ב לֵ֝צִ֗ים לֹ֣א יָשָֽׁב׃"

print("="*70)
print("PSALM 1:1 - COMPLETE PHRASE EXTRACTION")
print("="*70)
print()

print("ORIGINAL TEXT:")
print(verse_text)
print()

# Initialize extractor
ext = PhraseExtractor(verbose=False)

# Tokenize and normalize
words = split_words(clean_hebrew_text(verse_text))
print(f"TOKENIZED INTO {len(words)} WORDS:")
for i, word in enumerate(words, 1):
    normalized = ext._normalize_text(word)
    print(f"  {i:2}. {word:20} → {normalized}")

print()

# Now extract all phrases
from liturgy.phrase_extractor import PhraseExtractor

# Get phrases for verse 1
all_phrases = ext._extract_verse_ngrams(
    verse_num=1,
    verse_text=verse_text,
    min_length=2,
    max_length=10,
    use_cache=False
)

# Group by word count
by_word_count = {}
for phrase_data in all_phrases:
    wc = phrase_data['word_count']
    if wc not in by_word_count:
        by_word_count[wc] = []
    by_word_count[wc].append(phrase_data)

# Show all phrases by length
for wc in sorted(by_word_count.keys()):
    phrases = by_word_count[wc]
    print(f"{'='*70}")
    print(f"{wc}-WORD PHRASES ({len(phrases)} total)")
    print(f"{'='*70}")

    for i, phrase_data in enumerate(phrases, 1):
        original = phrase_data['phrase']
        normalized = phrase_data['phrase_normalized']
        freq = phrase_data['corpus_frequency']
        score = phrase_data['distinctiveness_score']
        searchable = "✓" if phrase_data['is_searchable'] else "✗"

        print(f"{i:2}. {original}")
        print(f"    Normalized: {normalized}")
        print(f"    Freq: {freq:3} | Score: {score:.3f} | Searchable: {searchable}")
        print()

# Summary
total = len(all_phrases)
searchable_count = sum(1 for p in all_phrases if p['is_searchable'])

print(f"{'='*70}")
print(f"SUMMARY")
print(f"{'='*70}")
print(f"Total phrases extracted:  {total}")
print(f"Searchable phrases:       {searchable_count} ({100*searchable_count/total:.1f}%)")
print(f"Non-searchable:           {total - searchable_count} (too common or all particles)")
print()

print("HOW IT WORKS:")
print("-" * 70)
print("""
For a verse with N words, we extract:
- All 2-word n-grams: (word[0:2], word[1:3], word[2:4], ...)
- All 3-word n-grams: (word[0:3], word[1:4], word[2:5], ...)
- ...
- All 10-word n-grams: (word[0:10], word[1:11], ...)

Each phrase is:
1. Normalized (remove diacritics, maqqef→space, remove punctuation)
2. Counted in Tanakh corpus (how many verses contain it?)
3. Scored for distinctiveness (rare = high, common = low)
4. Marked searchable if it meets the threshold for its length
""")
