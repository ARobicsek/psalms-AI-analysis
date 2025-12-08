#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Verify Psalm 15 phrases are now found"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.concordance.search import ConcordanceSearch

def verify_psalm_15():
    """Test key phrases from Psalm 15"""

    search = ConcordanceSearch()
    output = []

    # Test key phrases from Psalm 15
    test_phrases = [
        ("גור", "Should find Psalm 15:1 - יגור"),
        ("הלך", "Should find Psalm 15:2 - הולך"),
        ("תמים", "Should find Psalm 15:2 - תמים"),
        ("רגל", "Should find Psalm 15:3 - רגל"),
        ("אמת", "Should find Psalm 15:2 - אמת"),
    ]

    output.append("=== Testing Psalm 15 Word Variations ===\n")

    for word, description in test_phrases:
        output.append(f"Testing: {word}")
        output.append(f"  {description}")

        # Search for the word with variations
        results = search.search_word_with_variations(word, level='consonantal')
        psalm_15_results = [r for r in results if r.book == 'Psalms' and r.chapter == 15]

        output.append(f"  Total results: {len(results)}")
        output.append(f"  Psalm 15 results: {len(psalm_15_results)}")

        if psalm_15_results:
            output.append("  Found in Psalm 15:")
            for r in psalm_15_results[:3]:  # Show first 3
                output.append(f"    - {r.reference}: {r.matched_word}")
        else:
            output.append("  ❌ NOT FOUND in Psalm 15")
        output.append("")

    # Test phrase search
    output.append("=== Testing Phrase Search ===\n")

    phrases = [
        "גור באהל",
        "הלך תמים",
        "דבר אמת בלב",
    ]

    for phrase in phrases:
        output.append(f"Searching phrase: '{phrase}'")
        results = search.search_phrase(phrase, level='consonantal', scope='all')
        psalm_15_results = [r for r in results if r.book == 'Psalms' and r.chapter == 15]

        output.append(f"  Results: {len(results)}")
        output.append(f"  Psalm 15 matches: {len(psalm_15_results)}")

        if psalm_15_results:
            for r in psalm_15_results:
                output.append(f"    ✓ {r.reference}: {r.matched_text}")
        else:
            output.append("    ❌ No matches in Psalm 15")
        output.append("")

    # Write results
    with open("verify_psalm_15_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print("Verification results written to verify_psalm_15_results.txt")

if __name__ == "__main__":
    try:
        verify_psalm_15()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        with open("verify_psalm_15_error.txt", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)