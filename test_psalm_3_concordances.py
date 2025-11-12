# -*- coding: utf-8 -*-
"""Test all Psalm 3 concordance queries that failed originally"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest

# Initialize librarian
librarian = ConcordanceLibrarian()

# These are the 7 concordance queries from Psalm 3 that all returned 0 results
psalm_3_queries = [
    ("ברח מפני בן", "Tanakh", "Flight from family members"),
    ("מה רב", "Psalms", "Quantitative overwhelm expressions"),
    ("ישועתה באלהים", "Tanakh", "Deliverance through God"),
    ("מרים ראש", "Tanakh", "Head-lifting as honor restoration"),
    ("הר קדש", "Psalms", "Holy mountain as divine dwelling"),
    ("שכב ישן הקיץ", "Psalms", "Sleep cycle as trust metaphor"),
    ("לא אירא מרבבות", "Psalms", "Fearlessness against overwhelming numbers"),
]

print("=" * 80)
print("TESTING PSALM 3 CONCORDANCE QUERIES WITH ENHANCED LIBRARIAN")
print("=" * 80)

total_found = 0
total_queries = len(psalm_3_queries)

for query, scope, purpose in psalm_3_queries:
    print(f"\nQuery: {query}")
    print(f"  Scope: {scope}")
    print(f"  Purpose: {purpose}")

    request = ConcordanceRequest(
        query=query,
        scope=scope,
        level='consonantal',
        include_variations=True
    )

    bundle = librarian.search_with_variations(request)

    print(f"  Variations searched: {len(bundle.variations_searched)}")
    print(f"  Results found: {len(bundle.results)}")

    if bundle.results:
        total_found += 1
        print("  ✓ SUCCESS - Found results!")
        # Show first result
        first = bundle.results[0]
        print(f"    Example: {first.reference}")
        if first.book == "Psalms" and first.chapter == 3:
            print(f"    *** FOUND IN PSALM 3 ***")

        # Check if Psalm 3 is in the results
        psalm_3_results = [r for r in bundle.results if r.book == "Psalms" and r.chapter == 3]
        if psalm_3_results:
            print(f"    Psalm 3 matches: {len(psalm_3_results)}")
            for result in psalm_3_results:
                print(f"      - {result.reference}: {result.hebrew_text[:60]}...")
    else:
        print("  ✗ FAILED - No results found")

print("\n" + "=" * 80)
print(f"SUMMARY: {total_found}/{total_queries} queries now return results")
print("=" * 80)

# Test one query in detail to show the variation generation
print("\n" + "=" * 80)
print("DETAILED EXAMPLE: 'מה רבו' variation generation")
print("=" * 80)

request = ConcordanceRequest(
    query="מה רבו",
    scope="Psalms",
    level='consonantal',
    include_variations=True
)

bundle = librarian.search_with_variations(request)

print(f"\nAll {len(bundle.variations_searched)} variations searched:")
for i, var in enumerate(bundle.variations_searched, 1):
    print(f"  {i}. {var}")

print(f"\n{len(bundle.results)} results found:")
for result in bundle.results:
    print(f"\n  {result.reference}")
    print(f"    Hebrew: {result.hebrew_text}")
    print(f"    English: {result.english_text[:100]}...")
    print(f"    Matched word: {result.matched_word} (position {result.word_position})")
