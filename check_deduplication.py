#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check deduplication impact on phrase counts."""

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('src')

from liturgy.phrase_extractor import PhraseExtractor

# Test with a few sample Psalms to see extraction vs. unique counts
print("="*70)
print("DEDUPLICATION ANALYSIS: Extraction vs. Unique Phrases")
print("="*70)
print()

# Test Psalms: 23 (short), 119 (long), 1 (short)
test_psalms = [1, 23, 119]

for psalm_num in test_psalms:
    print(f"\n{'='*70}")
    print(f"PSALM {psalm_num}")
    print(f"{'='*70}")

    extractor = PhraseExtractor(verbose=False)
    phrases = extractor.extract_phrases(psalm_num, use_cache=False)

    # Count by word length
    by_length = {}
    unique_by_length = {}

    for phrase_data in phrases:
        wc = phrase_data['word_count']
        phrase_norm = phrase_data['phrase_normalized']

        # Total count
        by_length[wc] = by_length.get(wc, 0) + 1

        # Unique count
        if wc not in unique_by_length:
            unique_by_length[wc] = set()
        unique_by_length[wc].add(phrase_norm)

    print(f"\nWord Count | Total Extracted | Unique | Dedup Ratio")
    print(f"{'-'*70}")

    for wc in sorted(by_length.keys()):
        total = by_length[wc]
        unique = len(unique_by_length[wc])
        ratio = unique / total if total > 0 else 0
        print(f"{wc:10} | {total:15} | {unique:6} | {ratio:6.1%}")

    total_all = sum(by_length.values())
    unique_all = sum(len(s) for s in unique_by_length.values())
    print(f"{'-'*70}")
    print(f"{'TOTAL':10} | {total_all:15} | {unique_all:6} | {unique_all/total_all:6.1%}")

print("\n" + "="*70)
print("EXPLANATION:")
print("="*70)
print("""
Short phrases (2-3 words) have MUCH higher deduplication:
- They appear multiple times within the same Psalm
- Common phrases like "יהוה אלהים" get deduplicated

Long phrases (8-10 words) are naturally more unique:
- Most appear only once or twice
- Less affected by deduplication

The cache statistics show UNIQUE phrases (deduplicated),
which is correct for our indexing purpose!
""")
