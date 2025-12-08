#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug script to find root cause of phrase matching failures.
Focus on testing if search_word_with_variations can find prefixed forms.
"""

import sys
import os

# Add src to path and fix imports
sys.path.insert(0, os.path.dirname(__file__))

# Import directly from src
from src.concordance.search import ConcordanceSearch

def test_variations():
    """Test variation generation and matching"""
    search = ConcordanceSearch()

    # Test cases from Psalm 15
    test_words = [
        ("גור", "יגור"),  # Should find י�ור in Psalm 15:1
        ("הלך", "הלך"),  # Should find הלך in Psalm 15:2
        ("תמים", "תמים"),  # Should find תמים in Psalm 15:2
    ]

    print("=== Testing Word Variations ===")

    for base_word, expected_form in test_words:
        print(f"\nTesting base word: {base_word}")
        print(f"Expected to find: {expected_form}")

        # Get variations
        variations = search._get_word_variations(base_word)
        print(f"Generated {len(variations)} variations")

        # Check if expected form is in variations
        has_expected = expected_form in variations
        print(f"Has expected form '{expected_form}': {has_expected}")

        # Show first few variations
        print("First 10 variations:")
        for i, var in enumerate(variations[:10]):
            print(f"  {i+1}. {var}")

        # Test actual search
        results = search.search_word_with_variations(base_word, level='consonantal')
        print(f"Search results: {len(results)} matches")

        # Check if Psalm 15 is in results
        psalm_15_results = [r for r in results if r.book == 'Psalms' and r.chapter == 15]
        print(f"Psalm 15 matches: {len(psalm_15_results)}")

        for result in psalm_15_results[:3]:
            print(f"  - {result.reference}: {result.word}")

def test_phrase_search():
    """Test phrase search directly"""
    search = ConcordanceSearch()

    print("\n\n=== Testing Phrase Search ===")

    # Test phrase from Psalm 15
    phrase = "גור באהל"
    print(f"\nSearching for phrase: {phrase}")

    results = search.search_phrase(phrase, level='consonantal', scope='all')
    print(f"Phrase search results: {len(results)}")

    for result in results[:5]:
        print(f"  - {result.reference}: {result.matched_text}")

if __name__ == "__main__":
    # Set UTF-8 encoding for output
    if sys.platform == "win32":
        os.system('chcp 65001 >nul')

    try:
        test_variations()
        test_phrase_search()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()