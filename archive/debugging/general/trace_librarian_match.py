#!/usr/bin/env python3
"""
Trace exactly what the librarian does that causes the bad match
"""

import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger()

from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest


def trace_librarian_match():
    """Trace how the librarian finds Genesis 9:27"""

    print("=== Tracing Librarian Match ===")

    # Initialize librarian with custom logger
    class DebugLogger:
        def info(self, msg):
            if "גור" in msg or "Genesis" in msg or "מי יגור" in msg:
                print(f"INFO: {msg}")
        def debug(self, msg):
            if "variation" in msg.lower() or "match" in msg.lower():
                print(f"DEBUG: {msg}")
        def warning(self, msg):
            print(f"WARNING: {msg}")
        def error(self, msg):
            print(f"ERROR: {msg}")

    librarian = ConcordanceLibrarian()
    librarian.logger = DebugLogger()

    # Search for the phrase
    phrase = "מי יגור באהלך"
    request = ConcordanceRequest(
        query=phrase,
        scope='Tanakh',
        level='consonantal',
        include_variations=True,
        auto_scope_threshold=100
    )

    print(f"\nSearching with librarian...")
    bundle = librarian.search_with_variations(request)

    print(f"\nResults found: {len(bundle.results)}")

    # Check if Genesis 9:27 is in results
    for result in bundle.results:
        if result.book == 'Genesis' and result.chapter == 9 and result.verse == 27:
            print(f"\n*** FOUND BAD MATCH! ***")
            print(f"  Reference: {result.reference}")
            print(f"  Matched word: {result.matched_word.encode('utf-8')}")
            print(f"  Is phrase match: {result.is_phrase_match}")

            # Check which variation was searched
            print(f"\nChecking which variation matched...")
            variations = librarian.generate_phrase_variations(phrase, level='consonantal')

            # Check if "שכן" appears in any variation (shouldn't!)
            print(f"Looking for 'שכן' in variations...")
            for i, var in enumerate(variations):
                if "שכן" in var:
                    print(f"  Variation {i} contains 'שכן': {var.encode('utf-8')}")
                    break

    # Now test direct word search for "שכן"
    print(f"\n=== Direct word search for 'שכן' ===")
    from src.concordance.search import ConcordanceSearch
    search = ConcordanceSearch()
    results = search.search_word("שכן", level='consonantal', scope='Tanakh', limit=5)
    print(f"Found {len(results)} results for 'שכן':")
    for result in results:
        print(f"  - {result.reference}")
        if result.book == 'Genesis' and result.chapter == 9 and result.verse == 27:
            print(f"    ^ Genesis 9:27 has 'שכן'!")


if __name__ == "__main__":
    trace_librarian_match()