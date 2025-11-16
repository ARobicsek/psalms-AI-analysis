# -*- coding: utf-8 -*-
"""Test the new alternates feature for concordance searches"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest

librarian = ConcordanceLibrarian()

print("=" * 80)
print("TESTING ALTERNATES FEATURE")
print("=" * 80)

# Test 1: Search with alternates for different verb forms
print("\nTest 1: Searching for 'ברח' with verb form alternates")
print("-" * 80)

request = ConcordanceRequest(
    query="ברח",
    scope="Tanakh",
    level="consonantal",
    include_variations=True,
    alternate_queries=["יברח", "בורח", "ברוח"],  # Different verb forms
    notes="Fleeing verb with multiple conjugations"
)

bundle = librarian.search_with_variations(request)

print(f"Main query: {request.query}")
print(f"Alternates: {request.alternate_queries}")
print(f"Total variations searched: {len(bundle.variations_searched)}")
print(f"Total results: {len(bundle.results)}")

# Check if we found Psalm 3:1 (superscription about fleeing)
psalm_3_results = [r for r in bundle.results if r.book == "Psalms" and r.chapter == 3]
print(f"\nFound in Psalm 3: {len(psalm_3_results)} match(es)")
for result in psalm_3_results[:3]:
    print(f"  {result.reference}: {result.hebrew_text[:60]}...")

# Test 2: Search with alternates for maqqef-connected words
print("\n" + "=" * 80)
print("\nTest 2: Searching with maqqef alternates")
print("-" * 80)

request = ConcordanceRequest(
    query="מה רבו",
    scope="Psalms",
    level="consonantal",
    include_variations=True,
    alternate_queries=["מהרבו"],  # Combined maqqef form
    notes="How many - with maqqef variant"
)

bundle = librarian.search_with_variations(request)

print(f"Main query: {request.query}")
print(f"Alternates: {request.alternate_queries}")
print(f"Total variations searched: {len(bundle.variations_searched)}")
print(f"Total results: {len(bundle.results)}")

psalm_3_2 = [r for r in bundle.results if r.book == "Psalms" and r.chapter == 3 and r.verse == 2]
print(f"\nFound Psalm 3:2: {'✓' if psalm_3_2 else '✗'}")
if psalm_3_2:
    print(f"  {psalm_3_2[0].hebrew_text}")

# Test 3: Search with related word alternates
print("\n" + "=" * 80)
print("\nTest 3: Searching for divine names with alternates")
print("-" * 80)

request = ConcordanceRequest(
    query="יהוה צבאות",
    scope="Psalms",
    level="consonantal",
    include_variations=True,
    alternate_queries=["יהוה אלהים", "אלהי צבאות"],  # Related divine epithets
    notes="LORD of Hosts with variant divine names"
)

bundle = librarian.search_with_variations(request)

print(f"Main query: {request.query}")
print(f"Alternates: {request.alternate_queries}")
print(f"Total variations searched: {len(bundle.variations_searched)}")
print(f"Total results: {len(bundle.results)}")
print(f"\nFirst 5 results:")
for result in bundle.results[:5]:
    print(f"  {result.reference}: {result.matched_word}")

# Test 4: Compare with and without alternates
print("\n" + "=" * 80)
print("\nTest 4: Comparison - with vs without alternates")
print("-" * 80)

# Without alternates
request_no_alt = ConcordanceRequest(
    query="ברח",
    scope="Tanakh",
    level="consonantal",
    include_variations=True,
    notes="Fleeing verb - no alternates"
)

bundle_no_alt = librarian.search_with_variations(request_no_alt)

# With alternates
request_with_alt = ConcordanceRequest(
    query="ברח",
    scope="Tanakh",
    level="consonantal",
    include_variations=True,
    alternate_queries=["יברח", "בורח"],
    notes="Fleeing verb - with alternates"
)

bundle_with_alt = librarian.search_with_variations(request_with_alt)

print(f"WITHOUT alternates:")
print(f"  Variations searched: {len(bundle_no_alt.variations_searched)}")
print(f"  Results found: {len(bundle_no_alt.results)}")

print(f"\nWITH alternates ['יברח', 'בורח']:")
print(f"  Variations searched: {len(bundle_with_alt.variations_searched)}")
print(f"  Results found: {len(bundle_with_alt.results)}")
print(f"  Additional results: {len(bundle_with_alt.results) - len(bundle_no_alt.results)}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
The alternates feature allows the Micro Analyst to:
1. Suggest different verb conjugations for the same root
2. Provide both separated and maqqef-combined forms
3. List related theological terms that should be searched together
4. Catch different binyanim (verb patterns) for action verbs

The Concordance Librarian then:
- Generates morphological variations for EACH alternate
- Searches all variations and combines results
- Deduplicates by verse to avoid repetition

This creates a two-layer enhancement:
- Layer 1: Micro Analyst's contextual understanding
- Layer 2: Librarian's automatic morphological variations
""")
