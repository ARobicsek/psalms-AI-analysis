#!/usr/bin/env python3
"""Test script to verify phrase substring matching works correctly"""

import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.concordance.search import ConcordanceSearch
from src.data_sources.tanakh_database import TanakhDatabase

def test_psalm_15_phrase():
    """Test that 'דבר אמת בלב' matches Psalm 15:2"""
    db = TanakhDatabase(Path('database/tanakh.db'))
    search = ConcordanceSearch(db)

    # Test the problematic phrase
    phrase = "דבר אמת בלב"
    results = search.search_phrase(phrase, level='consonantal', scope='Psalms')

    print(f"Searching for phrase with {len(phrase.split())} words")
    print(f"Found {len(results)} results:")

    for result in results:
        print(f"\n- {result.reference}")
        # Skip printing Hebrew to avoid console encoding issues
        # print(f"  Hebrew: {result.hebrew_text}")
        # print(f"  Matched phrase: {result.matched_phrase}")
        print(f"  Position: {result.word_position}")

    # Check if Psalm 15:2 is found
    psalm_15_2_found = any(
        result.book == "Psalms" and result.chapter == 15 and result.verse == 2
        for result in results
    )

    print(f"\nPsalm 15:2 found: {psalm_15_2_found}")

    # Also test exact phrase match
    exact_results = search.search_phrase("ודובר אמת בלבבו", level='consonantal', scope='Psalms')
    print(f"\nSearching for exact phrase (with suffixes)")
    print(f"Found {len(exact_results)} results")

    return psalm_15_2_found

if __name__ == "__main__":
    found = test_psalm_15_phrase()
    if found:
        print("\n[SUCCESS] Phrase substring matching is working!")
    else:
        print("\n[FAILURE] Phrase substring matching not working as expected")