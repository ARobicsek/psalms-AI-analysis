# -*- coding: utf-8 -*-
"""Test phrase search to diagnose concordance issue"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from src.concordance.search import ConcordanceSearch
from src.concordance.hebrew_text_processor import split_words, normalize_for_search

search = ConcordanceSearch()

# Test cases from Psalm 3
test_phrases = [
    ("מרים ראש", "Tanakh", "head lifting"),
    ("מה רבו", "Psalms", "how many"),
    ("הר קדש", "Psalms", "holy mountain"),
]

print("Testing phrase searches from Psalm 3:\n")

for phrase, scope, description in test_phrases:
    print(f"Phrase: {phrase} ({description})")
    print(f"  Scope: {scope}")

    # Show how it splits
    words = split_words(phrase)
    print(f"  Split into {len(words)} words: {words}")

    # Show normalization
    norm_words = [normalize_for_search(w, 'consonantal') for w in words]
    print(f"  Normalized: {norm_words}")

    # Search
    results = search.search_phrase(phrase, level='consonantal', scope=scope)
    print(f"  Results: {len(results)}")

    if results:
        for r in results[:3]:
            print(f"    - {r.reference}: {r.hebrew_text[:50]}...")

    print()

# Now test single word searches for comparison
print("\nTesting single word searches:\n")

single_words = [
    ("מרים", "Tanakh"),
    ("ראש", "Tanakh"),
    ("רבו", "Psalms"),
]

for word, scope in single_words:
    results = search.search_word(word, level='consonantal', scope=scope)
    print(f"Word: {word} in {scope} -> {len(results)} results")
    if results:
        # Check if any are from Psalm 3
        psalm_3_results = [r for r in results if r.book == "Psalms" and r.chapter == 3]
        if psalm_3_results:
            print(f"  Found in Psalm 3:")
            for r in psalm_3_results:
                print(f"    - {r.reference} position {r.word_position}: {r.hebrew_text}")
    print()
