#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Test search again with improved fix"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.concordance.search import ConcordanceSearch

def test_search():
    """Test if our fix works"""

    search = ConcordanceSearch()

    # Write output to file
    output = []

    # Test cases
    test_words = [
        ("גור", "Should find יגור in Psalm 15:1"),
        ("הלך", "Should find הולך in Psalm 15:2"),
        ("תמים", "Should find תמים in Psalm 15:2"),
        ("באהל", "Should find באהל in Psalm 15:1"),
    ]

    for word, description in test_words:
        output.append(f"Testing: {word}")
        output.append(f"  {description}")

        results = search.search_word_with_variations(word, level='consonantal')
        psalm_15_results = [r for r in results if r.book == 'Psalms' and r.chapter == 15]

        output.append(f"  Results: {len(results)}")
        output.append(f"  Psalm 15: {len(psalm_15_results)}")

        if psalm_15_results:
            output.append("  Found in:")
            for r in psalm_15_results:
                output.append(f"    {r.reference}: {r.matched_word}")
        else:
            output.append("  ❌ Not found in Psalm 15")
        output.append("")

    # Test phrase search
    output.append("=== Phrase Search Test ===")
    phrases = [
        "גור באהל",
        "הלך תמים",
    ]

    for phrase in phrases:
        output.append(f"\nPhrase: '{phrase}'")
        results = search.search_phrase(phrase, level='consonantal', scope='all')
        psalm_15_results = [r for r in results if r.book == 'Psalms' and r.chapter == 15]

        output.append(f"  Results: {len(results)}")
        output.append(f"  Psalm 15: {len(psalm_15_results)}")

        if psalm_15_results:
            for r in psalm_15_results:
                output.append(f"    ✓ {r.reference}")

    # Write to file
    with open("search_test_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print("Results written to search_test_results.txt")

if __name__ == "__main__":
    test_search()