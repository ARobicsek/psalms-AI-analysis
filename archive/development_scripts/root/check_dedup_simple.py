#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple deduplication analysis on Psalm 23."""

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('src')

from liturgy.phrase_extractor import PhraseExtractor

print("="*70)
print("DEDUPLICATION ANALYSIS: Psalm 23 (6 verses)")
print("="*70)
print()

extractor = PhraseExtractor(verbose=False)
phrases = extractor.extract_phrases(23, use_cache=False)

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

print(f"Word Count | Total Extracted | Unique | Dedup %")
print(f"{'-'*70}")

for wc in sorted(by_length.keys()):
    total = by_length[wc]
    unique = len(unique_by_length[wc])
    dedup_pct = 100 * (1 - unique/total) if total > 0 else 0
    print(f"{wc:10} | {total:15} | {unique:6} | {dedup_pct:6.1f}%")

total_all = sum(by_length.values())
unique_all = sum(len(s) for s in unique_by_length.values())
overall_dedup = 100 * (1 - unique_all/total_all)

print(f"{'-'*70}")
print(f"{'TOTAL':10} | {total_all:15} | {unique_all:6} | {overall_dedup:6.1f}%")

print()
print("="*70)
print("KEY INSIGHT:")
print("="*70)
print(f"""
In Psalm 23 alone:
- We extracted {total_all:,} total phrases
- But only {unique_all:,} are unique ({overall_dedup:.1f}% deduplicated!)

Why? Short phrases repeat within the same Psalm:
- Verse 1: "יהוה רעי לא אחסר" (The LORD is my shepherd, I shall not want)
- Generates many overlapping 2-word, 3-word, etc. phrases
- "יהוה רעי", "רעי לא", "לא אחסר" all appear multiple times

This is CORRECT behavior! We want unique searchable phrases, not duplicates.

Across all 150 Psalms, common phrases like "יהוה אלהים" appear
hundreds of times but only count once in the cache.
""")
