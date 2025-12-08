#!/usr/bin/env python3
"""
Simple trace to find the bad match
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest


def simple_trace():
    """Trace the bad match"""

    print("=== Simple Trace for Bad Match ===")

    librarian = ConcordanceLibrarian()

    # Search for the phrase
    phrase = "מי יגור באהלך"
    request = ConcordanceRequest(
        query=phrase,
        scope='Tanakh',
        level='consonantal',
        include_variations=True,
        auto_scope_threshold=100
    )

    print(f"\nSearching for phrase...")
    bundle = librarian.search_with_variations(request)

    print(f"\nTotal results: {len(bundle.results)}")

    # Show all results
    print(f"\nAll results:")
    for i, result in enumerate(bundle.results):
        print(f"\nResult {i+1}:")
        print(f"  Reference: {result.reference}")
        print(f"  Matched word (bytes): {result.matched_word.encode('utf-8')}")
        print(f"  Is phrase match: {result.is_phrase_match}")
        print(f"  Word count in match: {len(result.matched_word.split())}")

    # Check if Genesis 9:27 is in results
    gen9_27 = any(r.book == 'Genesis' and r.chapter == 9 and r.verse == 27 for r in bundle.results)
    if gen9_27:
        print(f"\n*** GENESIS 9:27 WAS FOUND ***")
    else:
        print(f"\n*** GENESIS 9:27 NOT FOUND ***")
        print(f"  This suggests the issue may have been fixed!")


if __name__ == "__main__":
    simple_trace()