#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the full ConcordanceLibrarian search process for 'לא ימוט לעולם'"""

import sys
from src.concordance.search import ConcordanceSearch
from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest
from src.data_sources.tanakh_database import TanakhDatabase

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize database and search
db = TanakhDatabase()
search = ConcordanceSearch(db)
librarian = ConcordanceLibrarian()

def test_librarian_search():
    print("=" * 80)
    print("TESTING FULL CONCORDANCE LIBRARIAN SEARCH")
    print("=" * 80)

    # Create the request as it would be generated
    request = ConcordanceRequest(
        query="לא ימוט לעולם",
        level='consonantal',
        scope='auto',
        include_variations=True,
        notes="Test search from Psalm 15"
    )

    print(f"\nRequest details:")
    print(f"  Query: '{request.query}'")
    print(f"  Level: {request.level}")
    print(f"  Scope: {request.scope}")
    print(f"  Include variations: {request.include_variations}")

    # Search with variations
    print(f"\n\nExecuting search...")
    bundle = librarian.search_with_variations(request)

    print(f"\n\nSearch results:")
    print(f"  Total results: {len(bundle.results)}")
    print(f"  Variations searched: {len(bundle.variations_searched)}")

    # Check if Isaiah 40:20 is in the results
    print(f"\n\nChecking for Isaiah 40:20:")
    isaiah_found = False
    for result in bundle.results:
        if result.book == 'Isaiah' and result.chapter == 40 and result.verse == 20:
            isaiah_found = True
            print(f"  ❌ FOUND Isaiah 40:20!")
            print(f"     Matched text: '{result.matched_word}'")
            print(f"     Reference: {result.reference}")
            break

    if not isaiah_found:
        print(f"  ✓ Isaiah 40:20 NOT found in results")

    # Check the first few variations that were actually searched
    print(f"\n\nFirst 10 variations searched:")
    for i, variation in enumerate(bundle.variations_searched[:10]):
        print(f"  {i+1}. '{variation}'")

    # Now let's manually test the fallback search process
    print(f"\n\n" + "=" * 80)
    print("MANUAL TEST OF FALLBACK PROCESS")
    print("=" * 80)

    # First, try strict phrase matching
    print(f"\n1. Strict phrase search for 'לא ימוט לעולם':")
    strict_results = search.search_phrase("לא ימוט לעולם", level='consonantal', scope='auto')
    print(f"   Results: {len(strict_results)}")

    # Since that returns 0, the fallback should be used
    if not strict_results:
        print(f"\n2. No strict results, trying fallback search_phrase_in_verse:")
        fallback_results = search.search_phrase_in_verse(
            phrase="לא ימוט לעולם",
            level='consonantal',
            scope='auto',
            limit=50
        )
        print(f"   Fallback results: {len(fallback_results)}")

        # Check each fallback result
        for r in fallback_results:
            print(f"\n   Fallback result: {r.reference}")
            print(f"      Matched: '{r.matched_word}'")

            # Manually verify if this verse actually has all the words
            from src.concordance.hebrew_text_processor import normalize_for_search_split
            words = ["לא", "ימוט", "לעולם"]
            normalized_words = [normalize_for_search_split(w, 'consonantal') for w in words]

            has_all = search._verse_contains_all_words(
                r.book, r.chapter, r.verse,
                normalized_words, 'word_consonantal_split'
            )
            print(f"      Actually has all words: {has_all}")

            if not has_all:
                print(f"      ❌ FALSE POSITIVE - Verse missing some words!")
            else:
                print(f"      ✓ Valid match - has all words")

    # Let's check if the librarian is doing something different
    print(f"\n\n" + "=" * 80)
    print("CHECKING WHAT THE LIBRARIAN ACTUALLY DOES")
    print("=" * 80)

    # The librarian might be searching for variations individually
    # Let's check if searching for just "לא ימוט" finds Isaiah 40:20
    test_variations = [
        "לא ימוט",
        "לא־ימוט",  # Without space
        "לא ימוט",  # With space
    ]

    for var in test_variations:
        print(f"\nTesting variation '{var}':")
        results = search.search_phrase(var, level='consonantal', scope='auto')
        print(f"   Results: {len(results)}")

        for r in results:
            if r.book == 'Isaiah' and r.chapter == 40 and r.verse == 20:
                print(f"   Found Isaiah 40:20!")
                print(f"   Matched: '{r.matched_word}'")
                break

if __name__ == "__main__":
    test_librarian_search()