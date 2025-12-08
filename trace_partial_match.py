#!/usr/bin/env python3
"""
Trace why 'לא ימוט לעולם' returns partial matches
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest
from src.concordance.search import ConcordanceSearch


def trace_partial_match():
    """Trace the partial match issue"""

    print("=== Tracing Partial Match Issue ===")

    # Test the problematic phrase
    phrase = "לא ימוט לעולם"
    print(f"\nSearching for phrase: '{phrase.encode('utf-8')}'")

    librarian = ConcordanceLibrarian()

    # Get variations
    variations = librarian.generate_phrase_variations(phrase, level='consonantal')
    print(f"\nTotal variations generated: {len(variations)}")

    # Look for problematic variations
    single_word_vars = [v for v in variations if len(v.split()) == 1]
    two_word_vars = [v for v in variations if len(v.split()) == 2]
    three_word_vars = [v for v in variations if len(v.split()) == 3]

    print(f"\nVariation breakdown:")
    print(f"  Single-word: {len(single_word_vars)}")
    print(f"  Two-word: {len(two_word_vars)}")
    print(f"  Three-word: {len(three_word_vars)}")

    # Check if there's a variation that's just "לא ימוט"
    target = "לא ימוט"
    matching_vars = [v for v in two_word_vars if v == target]
    print(f"\nVariations equal to '{target.encode('utf-8')}': {len(matching_vars)}")
    if matching_vars:
        print(f"  Found: {[v.encode('utf-8') for v in matching_vars[:3]]}")

    # Search for the full phrase
    print(f"\n=== Searching with librarian ===")
    request = ConcordanceRequest(
        query=phrase,
        scope='auto',
        level='consonantal',
        include_variations=True,
        auto_scope_threshold=100
    )

    bundle = librarian.search_with_variations(request)
    print(f"\nResults found: {len(bundle.results)}")

    # Check for partial matches
    for result in bundle.results:
        print(f"\nResult: {result.reference}")
        print(f"  Matched: {result.matched_word.encode('utf-8')}")
        print(f"  Word count: {len(result.matched_word.split())}")

        # Check if it's a partial match
        if len(result.matched_word.split()) < len(phrase.split()):
            print(f"  *** PARTIAL MATCH! ***")

            # Check what words are shared
            phrase_words = set(phrase.split())
            match_words = set(result.matched_word.split())
            common = phrase_words.intersection(match_words)
            print(f"  Shared words: {[w.encode('utf-8') for w in common]}")

    # Test direct phrase search to see if strict matching works
    print(f"\n=== Direct strict phrase search ===")
    search = ConcordanceSearch()
    strict_results = search.search_phrase(phrase, level='consonantal', scope='Tanakh', limit=10)
    print(f"Strict phrase search results: {len(strict_results)}")
    for result in strict_results:
        print(f"  - {result.reference}")

    # Test the two-word variation that's causing problems
    print(f"\n=== Testing variation 'לא ימוט' ===")
    two_word_results = search.search_phrase("לא ימוט", level='consonantal', scope='Tanakh', limit=5)
    print(f"Found {len(two_word_results)} results for 'לא ימוט':")
    for result in two_word_results:
        print(f"  - {result.reference}")


if __name__ == "__main__":
    trace_partial_match()