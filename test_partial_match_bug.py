#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test if there's a bug allowing partial phrase matches"""

import sys
from src.concordance.search import ConcordanceSearch
from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest
from src.data_sources.tanakh_database import TanakhDatabase

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize database and librarian
db = TanakhDatabase()
search = ConcordanceSearch(db)
librarian = ConcordanceLibrarian()

def test_partial_match_bug():
    print("=" * 80)
    print("TESTING FOR PARTIAL MATCH BUG")
    print("=" * 80)

    # Check if any of the 2841 variations are just 2 words
    phrase = "לא ימוט לעולם"
    variations = librarian.generate_phrase_variations(phrase, 'consonantal')

    two_word_variations = []
    for var in variations:
        words = var.split()
        if len(words) == 2:
            two_word_variations.append(var)

    print(f"\nTotal variations: {len(variations)}")
    print(f"Two-word variations: {len(two_word_variations)}")

    if two_word_variations:
        print(f"\nSome two-word variations found:")
        for var in two_word_variations[:10]:
            print(f"  '{var}'")

    # Now check if any of these two-word variations find Isaiah 40:20
    print(f"\n\nChecking if any two-word variations find Isaiah 40:20:")
    for var in two_word_variations[:20]:  # Check first 20
        results = search.search_phrase(var, level='consonantal', scope='auto', limit=10)
        for r in results:
            if r.book == 'Isaiah' and r.chapter == 40 and r.verse == 20:
                print(f"\n  ✗ Found Isaiah 40:20 with two-word variation: '{var}'")
                print(f"     This is the BUG! A 2-word variation is being returned")
                print(f"     for a 3-word search query.")
                return

    # Check if the issue is with search_phrase_in_verse accepting partial matches
    print(f"\n\nTesting if search_phrase_in_verse accepts partial matches:")

    # This should return False (as we verified earlier)
    has_all = search._verse_contains_all_words(
        'Isaiah', 40, 20,
        ['לא', 'ימוט', 'לעולם'],
        'word_consonantal_split'
    )
    print(f"  Does Isaiah 40:20 have all 3 words? {has_all}")

    # Now test with just 2 words
    has_all_2 = search._verse_contains_all_words(
        'Isaiah', 40, 20,
        ['לא', 'ימוט'],
        'word_consonantal_split'
    )
    print(f"  Does Isaiah 40:20 have 'לא ימוט'? {has_all_2}")

    # The issue might be in how the librarian is generating the variations
    # or how it's searching them

    print(f"\n\n" + "=" * 80)
    print("THEORY ABOUT THE BUG")
    print("=" * 80)

    print("""
    THEORY: One of the 2841 variations is actually just 'לא ימוט' (without לעולם).
    When the librarian searches for this 2-word variation, it finds Isaiah 40:20.
    But since this variation is generated FROM the original 3-word phrase,
    the result gets included under the "לא ימוט לעולם" search.

    This is a DESIGN BUG: The variation generator is creating partial phrases
    that don't contain all the original words.
    """)

    # Let's verify this theory by checking what words are in each variation
    print(f"\n\nVerifying the theory - checking variations that might match:")
    print(f"Looking for variations containing 'לא' and 'ימוט' but not 'לעולם'...")

    suspicious_vars = []
    for var in variations:
        words = var.split()
        if 'לא' in words and 'ימוט' in words and 'לעולם' not in words:
            suspicious_vars.append(var)

    if suspicious_vars:
        print(f"\n  ✗ Found {len(suspicious_vars)} suspicious variations!")
        for var in suspicious_vars[:5]:
            print(f"    '{var}' - missing 'לעולם'!")

        print(f"\n  This confirms the bug!")
        print(f"  The variation generator is creating partial phrases")
        print(f"  that don't contain all the words from the original phrase.")
    else:
        print(f"\n  ✓ No suspicious variations found.")
        print(f"  The bug might be elsewhere in the search logic.")

if __name__ == "__main__":
    test_partial_match_bug()