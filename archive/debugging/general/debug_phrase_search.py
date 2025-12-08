#!/usr/bin/env python3
"""
Debug phrase search with comprehensive logging to trace matching decisions.
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from src.concordance.search import ConcordanceSearch
from src.agents.concordance_librarian import ConcordanceRequest, ConcordanceLibrarian


def debug_phrase_search():
    """Debug phrase search with detailed logging."""

    print("=== Debugging Phrase Search with Logging ===\n")

    # Initialize librarian with logger
    librarian = ConcordanceLibrarian()
    librarian.logger = logger

    # Test Case 1: The problematic phrase
    print("\n*** Test Case 1: Searching for 'mi yagur be'aholekha' ***")
    query1 = "מי יגור באהלך"
    request = ConcordanceRequest(
        query=query1,
        scope='Tanakh',
        level='consonantal',
        include_variations=True,
        source_psalm=None,
        auto_scope_threshold=100
    )

    # Get variations that will be searched
    variations = librarian.generate_phrase_variations(query1, level='consonantal')
    print(f"\nVariations to search ({len(variations)}):")
    for i, var in enumerate(variations[:10]):  # Show first 10
        try:
            print(f"  {i+1}. '{var}'")
        except:
            print(f"  {i+1}. [unicode issue]")
    if len(variations) > 10:
        print(f"  ... and {len(variations) - 10} more")

    # Search with variations
    bundle = librarian.search_with_variations(request)

    print(f"\nTotal results found: {len(bundle.results)}")
    print(f"Total variations searched: {len(bundle.variations_searched)}")

    # Examine each result
    for i, result in enumerate(bundle.results[:3]):
        print(f"\nResult {i+1}:")
        print(f"  Reference: {result.reference}")
        print(f"  Matched: [showing as bytes]")
        print(f"  Is phrase match: {result.is_phrase_match}")
        if result.is_phrase_match:
            print(f"  Phrase match: True")
        print(f"  Hebrew length: {len(result.hebrew_text)} chars")

    # Test Case 2: Psalm 15 phrase
    print("\n\n*** Test Case 2: Searching for Psalm 15:2 phrase ***")
    query2 = "דובר אמת בלבבו"
    request2 = ConcordanceRequest(
        query=query2,
        scope='Tanakh',
        level='consonantal',
        include_variations=True,
        source_psalm=15,  # Include Psalm 15
        auto_scope_threshold=100
    )

    variations2 = librarian.generate_phrase_variations(query2, level='consonantal')
    print(f"\nVariations to search ({len(variations2)}):")
    for i, var in enumerate(variations2[:10]):
        try:
            print(f"  {i+1}. '{var}'")
        except:
            print(f"  {i+1}. [unicode issue]")

    bundle2 = librarian.search_with_variations(request2)
    print(f"\nTotal results found: {len(bundle2.results)}")

    # Check if Psalm 15:2 is in results
    psalm15_found = False
    for result in bundle2.results:
        if result.book == 'Psalms' and result.chapter == 15 and result.verse == 2:
            psalm15_found = True
            print(f"\n*** FOUND PSALM 15:2 ***")
            print(f"  Matched: '{result.matched_word}'")
            print(f"  Hebrew: {result.hebrew_text}")
            break

    if not psalm15_found:
        print(f"\n*** PSALM 15:2 NOT FOUND ***")
        # Let's check what's actually in Psalm 15:2
        search = ConcordanceSearch()
        direct_check = search.search_word("דבר", level='consonantal', scope='Psalms', limit=1)
        for result in direct_check:
            if result.chapter == 15 and result.verse == 2:
                print(f"\nDirect check of Psalm 15:2:")
                print(f"  Hebrew: {result.hebrew_text}")


if __name__ == "__main__":
    debug_phrase_search()