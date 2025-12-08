#!/usr/bin/env python3
"""
Test script to validate the phrase matching fixes.

Tests the specific issues reported:
1. "לֹא יִמּוֹט" should NOT match Numbers 13:23 (which only has "בַמּוֹט")
2. "יָמַר שְׁבֻעָה" should NOT match II Chronicles 15:15 (which only has "הַשְּׁבוּעָה")
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.concordance_librarian import ConcordanceRequest, ConcordanceLibrarian


def test_phrase_fixes():
    """Test that phrase matching fixes work correctly."""

    print("=" * 80)
    print("TESTING PHRASE MATCHING FIXES")
    print("=" * 80)

    librarian = ConcordanceLibrarian()

    # Test 1: "לא ימוט" should NOT match Numbers 13:23
    print("\nTest 1: Phrase 'לא ימוט' should NOT match Numbers 13:23")
    request1 = ConcordanceRequest(
        query="לא ימוט",
        level='consonantal',
        scope='Tanakh'
    )
    bundle1 = librarian.search_with_variations(request1)

    # Check if Numbers 13:23 is in results
    numbers_match = False
    for result in bundle1.results:
        if result.book == 'Numbers' and result.chapter == 13 and result.verse == 23:
            numbers_match = True
            print(f"  ❌ FAIL: Found Numbers 13:23 in results")
            print(f"     Hebrew: {result.hebrew_text}")
            print(f"     Matched phrase: {result.matched_phrase}")
            break

    if not numbers_match:
        print(f"  ✅ PASS: Numbers 13:23 correctly excluded")
    print(f"  Total results: {len(bundle1.results)}")
    print(f"  Variations searched: {len(bundle1.variations_searched)}")

    # Show a few valid results if any
    if bundle1.results:
        print(f"\n  Sample valid results:")
        for result in bundle1.results[:3]:
            print(f"    - {result.reference}: {result.hebrew_text[:50]}...")

    # Test 2: "ימר שבועה" should NOT match II Chronicles 15:15
    print("\n\nTest 2: Phrase 'ימר שבועה' should NOT match II Chronicles 15:15")
    request2 = ConcordanceRequest(
        query="ימר שבועה",
        level='consonantal',
        scope='Tanakh'
    )
    bundle2 = librarian.search_with_variations(request2)

    # Check if II Chronicles 15:15 is in results
    chronicles_match = False
    for result in bundle2.results:
        if result.book == '2 Chronicles' and result.chapter == 15 and result.verse == 15:
            chronicles_match = True
            print(f"  ❌ FAIL: Found II Chronicles 15:15 in results")
            print(f"     Hebrew: {result.hebrew_text}")
            print(f"     Matched phrase: {result.matched_phrase}")
            break

    if not chronicles_match:
        print(f"  ✅ PASS: II Chronicles 15:15 correctly excluded")
    print(f"  Total results: {len(bundle2.results)}")
    print(f"  Variations searched: {len(bundle2.variations_searched)}")

    # Show a few valid results if any
    if bundle2.results:
        print(f"\n  Sample valid results:")
        for result in bundle2.results[:3]:
            print(f"    - {result.reference}: {result.hebrew_text[:50]}...")

    # Test 3: Verify valid phrase still works
    print("\n\nTest 3: Valid phrase 'דובר אמת בלבבו' should find Psalm 15:2")
    request3 = ConcordanceRequest(
        query="דובר אמת בלבבו",
        level='consonantal',
        scope='Tanakh',
        source_psalm=15
    )
    bundle3 = librarian.search_with_variations(request3)

    psalm_match = False
    for result in bundle3.results:
        if result.book == 'Psalms' and result.chapter == 15 and result.verse == 2:
            psalm_match = True
            print(f"  ✅ PASS: Found Psalm 15:2")
            print(f"     Hebrew: {result.hebrew_text}")
            print(f"     English: {result.english_text}")
            break

    if not psalm_match:
        print(f"  ❌ FAIL: Psalm 15:2 not found!")
        print(f"  Results found in:")
        for result in bundle3.results[:5]:
            print(f"    - {result.reference}")

    # Test 4: Check that 3-word phrases don't generate 2-word variations
    print("\n\nTest 4: Verify 3-word phrases don't generate 2-word variations")
    test_phrase = "לא ימוט לעולם"
    variations = librarian.generate_phrase_variations(test_phrase, 'consonantal')

    two_word_vars = [v for v in variations if len(v.split()) == 2]

    if two_word_vars:
        print(f"  ❌ FAIL: Found {len(two_word_vars)} two-word variations:")
        for var in two_word_vars[:5]:
            print(f"    '{var}'")
    else:
        print(f"  ✅ PASS: No incomplete variations found")
        print(f"  All {len(variations)} variations have 3 words")

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    all_passed = not numbers_match and not chronicles_match and psalm_match and not two_word_vars

    if all_passed:
        print("✅ ALL TESTS PASSED! The phrase matching fixes are working correctly.")
    else:
        print("❌ Some tests failed. Please review the output above.")

    return all_passed


if __name__ == "__main__":
    # Set UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    success = test_phrase_fixes()
    sys.exit(0 if success else 1)