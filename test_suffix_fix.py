"""
Test script to verify the suffix variation fix for concordance phrase search.

Test case: "הר קדש" should find Psalm 15:1 which contains "בהר קדשך"
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest
from src.concordance.hebrew_text_processor import split_words

def test_suffix_variations():
    """Test that suffix variations are generated for all words in a phrase."""

    print("=" * 80)
    print("Testing Suffix Variation Fix")
    print("=" * 80)

    librarian = ConcordanceLibrarian()

    # Test phrase: "הר קדש" (holy mountain)
    test_phrase = "הר קדש"

    print(f"\nTest phrase: {test_phrase}")
    print(f"Words: {split_words(test_phrase)}")

    # Generate variations
    variations = librarian.generate_phrase_variations(test_phrase, level='consonantal')

    print(f"\nGenerated {len(variations)} variations:")
    print("-" * 80)

    # Look for specific variations we need
    key_variations = [
        "הר קדש",      # Base phrase
        "הר קדשך",     # Suffix on last word (old behavior)
        "הרי קדש",     # Suffix on first word (NEW!)
        "בהר קדש",     # Prefix on first word
        "בהר קדשך",    # Prefix on first + suffix on second (THIS IS THE KEY ONE!)
        "הרי קדשך",    # Suffix on both words
    ]

    found_variations = []
    missing_variations = []

    for var in key_variations:
        if var in variations:
            found_variations.append(var)
            print(f"✓ {var}")
        else:
            missing_variations.append(var)
            print(f"✗ {var} (MISSING)")

    # Show all variations (limited to first 50 for readability)
    print(f"\nAll variations (showing first 50 of {len(variations)}):")
    for i, var in enumerate(sorted(variations)[:50], 1):
        print(f"  {i:3d}. {var}")

    if len(variations) > 50:
        print(f"  ... and {len(variations) - 50} more")

    print("\n" + "=" * 80)
    print("Searching for phrase: הר קדש")
    print("=" * 80)

    # Now do the actual search
    request = ConcordanceRequest(
        query=test_phrase,
        scope='Psalms',  # Limit to Psalms for faster search
        level='consonantal',
        include_variations=True,
        max_results=20
    )

    bundle = librarian.search_with_variations(request)

    print(f"\nFound {len(bundle.results)} results in Psalms")
    print(f"Searched {len(bundle.variations_searched)} variations")

    # Check if Psalm 15:1 is in the results
    psalm_15_1_found = False

    print("\nResults:")
    print("-" * 80)
    for i, result in enumerate(bundle.results, 1):
        is_target = result.reference == "Psalms 15:1"
        marker = " ← TARGET VERSE!" if is_target else ""
        print(f"{i:2d}. {result.reference}{marker}")
        print(f"    Hebrew: {result.hebrew_text}")
        print(f"    English: {result.english_text}")
        print(f"    Matched: {result.matched_word} (position {result.word_position})")
        print()

        if is_target:
            psalm_15_1_found = True

    # Summary
    print("=" * 80)
    print("TEST RESULTS")
    print("=" * 80)

    print(f"\n1. Key variations generated:")
    print(f"   Found: {len(found_variations)}/{len(key_variations)}")
    for var in found_variations:
        print(f"   ✓ {var}")
    if missing_variations:
        print(f"\n   Missing:")
        for var in missing_variations:
            print(f"   ✗ {var}")

    print(f"\n2. Psalm 15:1 search:")
    if psalm_15_1_found:
        print(f"   ✓ SUCCESS! Found Psalm 15:1 with 'בהר קדשך'")
    else:
        print(f"   ✗ FAILED! Psalm 15:1 not found")

    print("\n" + "=" * 80)

    return psalm_15_1_found and "בהר קדשך" in variations


if __name__ == '__main__':
    # Ensure UTF-8 encoding on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    success = test_suffix_variations()

    sys.exit(0 if success else 1)
