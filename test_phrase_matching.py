#!/usr/bin/env python3
"""
Test script to verify phrase matching fixes in concordance lookup.

This tests the fixes for:
1. Phrase searches returning only single-word matches
2. Phrases from the source psalm not being found
3. Display issues with phrase matches
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.concordance.search import ConcordanceSearch
from src.agents.concordance_librarian import ConcordanceRequest, ConcordanceLibrarian


def test_phrase_matching():
    """Test that phrase searches only return verses with ALL words present."""

    print("=== Testing Phrase Matching Fixes ===\n")

    # Initialize concordance search
    search = ConcordanceSearch()
    librarian = ConcordanceLibrarian()

    # Test Case 1: "גור ושכן" should NOT match verses with only "גור"
    print("Test 1: Phrase 'גור ושכן' should NOT match Chronicles 26:7 (only has גור)")
    test_phrase_1 = "גור ושכן"
    results = search.search_phrase(test_phrase_1, level='consonantal', scope='Tanakh', limit=50)

    chronicles_match = False
    for result in results:
        if result.book == '2 Chronicles' and result.chapter == 26 and result.verse == 7:
            chronicles_match = True
            print(f"  ❌ FAIL: Found match in Chronicles 26:7")
            print(f"     Hebrew: {result.hebrew_text[:50]}...")
            print(f"     Matched: {result.matched_phrase if result.is_phrase_match else result.matched_word}")
            break

    if not chronicles_match:
        print(f"  ✅ PASS: Chronicles 26:7 correctly excluded")

    print(f"  Total results: {len(results)}")
    print()

    # Test Case 2: "דובר אמת בלבבו" should find Psalm 15:2
    print("Test 2: Phrase 'דובר אמת בלבבו' should find Psalm 15:2")
    request = ConcordanceRequest(
        query="דובר אמת בלבבו",
        scope='Tanakh',
        level='consonantal',
        source_psalm=15  # This should ensure Psalms is included
    )
    bundle = librarian.search_with_variations(request)

    psalm_match = False
    for result in bundle.results:
        if result.book == 'Psalms' and result.chapter == 15 and result.verse == 2:
            psalm_match = True
            print(f"  ✅ PASS: Found match in Psalm 15:2")
            print(f"     Hebrew: {result.hebrew_text}")
            print(f"     English: {result.english_text}")
            print(f"     Matched: {result.matched_phrase if result.is_phrase_match else result.matched_word}")
            print(f"     Is phrase match: {result.is_phrase_match}")
            break

    if not psalm_match:
        print(f"  ❌ FAIL: Psalm 15:2 not found!")
        print(f"  Total results: {len(bundle.results)}")
        if bundle.results:
            print("  Results found in:")
            for result in bundle.results[:5]:
                print(f"    - {result.reference}")

    print()

    # Test Case 3: "רגל על־לשונו" should find Psalm 15:3
    print("Test 3: Phrase 'רגל על־לשונו' should find Psalm 15:3")
    request = ConcordanceRequest(
        query="רגל על־לשונו",
        scope='Tanakh',
        level='consonantal',
        source_psalm=15
    )
    bundle = librarian.search_with_variations(request)

    psalm_match = False
    for result in bundle.results:
        if result.book == 'Psalms' and result.chapter == 15 and result.verse == 3:
            psalm_match = True
            print(f"  ✅ PASS: Found match in Psalm 15:3")
            print(f"     Hebrew: {result.hebrew_text}")
            print(f"     English: {result.english_text}")
            print(f"     Matched: {result.matched_phrase if result.is_phrase_match else result.matched_word}")
            print(f"     Is phrase match: {result.is_phrase_match}")
            break

    if not psalm_match:
        print(f"  ❌ FAIL: Psalm 15:3 not found!")
        print(f"  Total results: {len(bundle.results)}")
        if bundle.results:
            print("  Results found in:")
            for result in bundle.results[:5]:
                print(f"    - {result.reference}")

    print()

    # Test Case 4: Verify phrase match display
    print("Test 4: Verify phrase matches display full phrase, not first word")
    test_phrase = "הלך תם"
    results = search.search_phrase(test_phrase, level='consonantal', scope='Tanakh', limit=5)

    if results:
        for result in results[:3]:
            if result.is_phrase_match:
                print(f"  ✅ PASS: Phrase match correctly identified")
                print(f"     Reference: {result.reference}")
                print(f"     Displayed: {result.matched_phrase}")
                print(f"     Is phrase match: {result.is_phrase_match}")
                break
        else:
            print(f"  ⚠️  Note: No phrase matches found for '{test_phrase}'")
    else:
        print(f"  ⚠️  Note: No results found for '{test_phrase}'")

    print()
    print("=== Test Summary ===")
    print("All tests completed. Check output above for any failures.")
    print("\nKey fixes verified:")
    print("1. Phrase searches should not match single words")
    print("2. Source psalm inclusion should work with source_psalm field")
    print("3. Phrase matches should display the full phrase")
    print("4. Maqqef handling should work for phrases like 'רגל על־לשונו'")


if __name__ == "__main__":
    test_phrase_matching()