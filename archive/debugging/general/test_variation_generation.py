#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test what variations are generated for 'לא ימוט לעולם'"""

import sys
from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest
from src.data_sources.tanakh_database import TanakhDatabase

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize database and librarian
db = TanakhDatabase()
librarian = ConcordanceLibrarian()

def test_variation_generation():
    print("=" * 80)
    print("TESTING VARIATION GENERATION FOR 'לא ימוט לעולם'")
    print("=" * 80)

    # Generate variations
    phrase = "לא ימוט לעולם"
    variations = librarian.generate_phrase_variations(phrase, 'consonantal')

    print(f"\nTotal variations generated: {len(variations)}")
    print(f"\nFirst 20 variations:")
    for i, var in enumerate(variations[:20]):
        print(f"  {i+1:2d}. '{var}'")

    # Look for variations that might match Isaiah 40:20
    print(f"\n\nLooking for variations that might match Isaiah 40:20:")
    print(f"(Isaiah 40:20 contains: לא ... ימוט at positions 12-13)")

    # Check for variations with just the first two words
    two_word_vars = []
    for var in variations:
        words = var.split()
        if len(words) == 2 and 'לא' in words and 'ימוט' in words:
            two_word_vars.append(var)

    print(f"\nVariations with just 'לא ימוט':")
    for var in two_word_vars[:10]:
        print(f"  '{var}'")

    # Also check if "לא ימוט" without לעולם is being generated
    print(f"\n\nChecking if 'לא ימוט' is in variations:")
    if 'לא ימוט' in variations:
        print(f"  ✓ Found: 'לא ימוט'")
    else:
        print(f"  ✗ Not found as variation")

    # Check if there's a maqqef variant
    print(f"\n\nChecking for maqqef variants:")
    maqqef_vars = [v for v in variations if '-' in v or '־' in v]
    print(f"  Variations with maqqef: {len(maqqef_vars)}")
    for var in maqqef_vars[:5]:
        print(f"    '{var}'")

    # Check if the issue is with the maqqef handling
    print(f"\n\nTesting maqqef handling:")
    print(f"  Original: 'לא ימוט לעולם'")
    print(f"  With maqqef: 'לא־ימוט לעולם'")

    # Test search with maqqef
    from src.concordance.search import ConcordanceSearch
    search = ConcordanceSearch(db)

    test_phrases = [
        'לא ימוט לעולם',
        'לא־ימוט לעולם',
        'לא ימוט',  # Without third word
    ]

    print(f"\n\nTesting different phrase forms:")
    for test_phrase in test_phrases:
        results = search.search_phrase(test_phrase, level='consonantal', scope='auto')
        if results:
            print(f"\n  '{test_phrase}': {len(results)} results")
            for r in results[:3]:
                if 'Isaiah' in r.reference and '40:20' in r.reference:
                    print(f"    ❌ Found Isaiah 40:20!")
                    print(f"       Matched: '{r.matched_word}'")
                else:
                    print(f"    - {r.reference}")
        else:
            print(f"  '{test_phrase}': 0 results")

    # Now let's see what happens when we test the full librarian search with logging
    print(f"\n\n" + "=" * 80)
    print("FULL LIBRARIAN SEARCH WITH ALL VARIATIONS")
    print("=" * 80)

    # Create request
    request = ConcordanceRequest(
        query="לא ימוט לעולם",
        level='consonantal',
        scope='auto',
        include_variations=True
    )

    # Search each variation and check for Isaiah 40:20
    found_in_variation = None
    words = phrase.split()

    # Generate variations again
    variations = librarian.generate_phrase_variations(phrase, 'consonantal')

    print(f"\nSearching variations for Isaiah 40:20...")
    for i, variation in enumerate(variations):
        # Search for this specific variation
        results = search.search_phrase(variation, level='consonantal', scope='auto', limit=10)

        # Check if Isaiah 40:20 is in results
        for r in results:
            if r.book == 'Isaiah' and r.chapter == 40 and r.verse == 20:
                found_in_variation = variation
                print(f"\n  ✗ FOUND Isaiah 40:20 in variation {i+1}:")
                print(f"     Variation: '{variation}'")
                print(f"     Matched: '{r.matched_word}'")
                break

        if found_in_variation:
            break

    if not found_in_variation:
        print(f"\n  ✓ Isaiah 40:20 NOT found in any variation")

        # Check fallback searches
        print(f"\n\nChecking fallback searches...")
        for i, variation in enumerate(variations[:20]):  # Check first 20
            results = search.search_phrase_in_verse(variation, level='consonantal', scope='auto', limit=10)
            for r in results:
                if r.book == 'Isaiah' and r.chapter == 40 and r.verse == 20:
                    found_in_variation = f"FALLBACK: {variation}"
                    print(f"\n  ✗ Found Isaiah 40:20 in fallback search!")
                    print(f"     Variation: '{variation}'")
                    print(f"     Matched: '{r.matched_word}'")
                    break
            if found_in_variation:
                break

if __name__ == "__main__":
    test_variation_generation()