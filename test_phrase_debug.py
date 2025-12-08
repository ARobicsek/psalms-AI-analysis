#!/usr/bin/env python3
"""
Debug test to understand what's being extracted.
"""

import sys
import re
from pathlib import Path
from itertools import product

sys.path.insert(0, str(Path(__file__).parent))

from src.concordance.hebrew_text_processor import split_words

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Actual Psalm 15:3
verse_hebrew = "לֹֽא־רָגַ֨ל ׀ עַל־לְשֹׁנ֗וֹ לֹא־עָשָׂ֣ה לְרֵעֵ֣הוּ רָעָ֑ה וְ֝חֶרְפָּ֗ה לֹא־נָשָׂ֥א עַל־קְרֹבֽוֹ׃"

# Split first, then clean each word to maintain alignment
verse_words = split_words(verse_hebrew)
verse_words_clean = [re.sub(r'[\u0591-\u05C7]', '', word) for word in verse_words]

print("Psalm 15:3 word-by-word analysis:")
print("=" * 80)
for i, (word, word_clean) in enumerate(zip(verse_words, verse_words_clean)):
    print(f"{i}: '{word}' → '{word_clean}'")

print("\n" + "=" * 80)
print("Query: 'נשא חרפה'")
print("=" * 80)

query = "נשא חרפה"
query_clean = re.sub(r'[\u0591-\u05C7]', '', query)
query_words = split_words(query_clean)

print(f"\nQuery words: {query_words}")

print("\nSearching for matches:")
word_positions = {}
for qword in query_words:
    word_positions[qword] = []
    print(f"\n  Looking for '{qword}':")
    for i, vword in enumerate(verse_words_clean):
        # Skip empty words
        if not vword or not qword:
            continue
        # Substring match
        if qword in vword or vword in qword:
            print(f"    Found at position {i}: '{vword}' (in '{verse_words[i]}')")
            word_positions[qword].append(i)

print(f"\n\nWord positions found:")
for qword, positions in word_positions.items():
    print(f"  '{qword}': {positions}")

print(f"\n\nGenerating all combinations:")
for combination in product(*word_positions.values()):
    sorted_positions = sorted(combination)

    # Skip duplicates
    if len(set(sorted_positions)) != len(sorted_positions):
        print(f"  {combination} → SKIP (duplicates)")
        continue

    start = sorted_positions[0]
    end = sorted_positions[-1]

    full_span = ' '.join(verse_words[start:end+1])
    full_span_clean = re.sub(r'[\u0591-\u05C7]', '', full_span)

    collapsed = ' '.join(verse_words[i] for i in sorted_positions)
    collapsed_clean = re.sub(r'[\u0591-\u05C7]', '', collapsed)

    print(f"\n  Combination: {combination} (positions {start}-{end})")
    print(f"    Full span: '{full_span}' → '{full_span_clean}'")
    print(f"    Collapsed: '{collapsed}' → '{collapsed_clean}'")

