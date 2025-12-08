#!/usr/bin/env python3
"""
Test if the combined word variation is causing the bad match
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.concordance.search import ConcordanceSearch


def test_combined_search():
    """Test if the combined word matches Genesis 9:27"""

    print("=== Testing Combined Word Search ===")

    search = ConcordanceSearch()

    # The single combined variation
    combined_word = "מייגורבאהלך"
    print(f"\nSearching for combined word: {combined_word.encode('utf-8')}")

    # Search for this combined word
    results = search.search_word(combined_word, level='consonantal', scope='Tanakh', limit=10)
    print(f"\nResults for combined word: {len(results)}")

    for result in results:
        print(f"  - {result.reference}")

    # Now check if "באהל" alone finds Genesis 9:27
    print(f"\n=== Searching for 'B-AH-L' ===")
    results2 = search.search_word("באהל", level='consonantal', scope='Tanakh', limit=10)
    print(f"Found {len(results2)} results")

    # Show all results
    print(f"\nResults for 'B-AH-L':")
    for result in results2:
        print(f"  - {result.reference}")
        if result.book == 'Genesis' and result.chapter == 9 and result.verse == 27:
            print(f"    *** FOUND GENESIS 9:27! ***")
            print(f"    Matched word bytes: {result.matched_word.encode('utf-8')}")

    # Check the actual Hebrew in Genesis 9:27
    if any(r.book == 'Genesis' and r.chapter == 9 and r.verse == 27 for r in results2):
        print(f"\nGenesis 9:27 contains 'באהל' - this explains the bad match!")


if __name__ == "__main__":
    test_combined_search()