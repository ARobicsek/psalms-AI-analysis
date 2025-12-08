#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Test הולך vs הלץ matching"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.concordance.search import ConcordanceSearch

def test_holokh():
    """Test if הלך matches הולך"""

    search = ConcordanceSearch()

    # Get variations for הלך
    variations = search._get_word_variations('הלך')

    print("Testing if 'הלך' variations include 'הולך':")
    print(f"Generated {len(variations)} variations")
    print(f"'הולך' in variations: {'הולך' in variations}")

    # Check what variations are generated
    print("\nFirst 20 variations containing 'הלך':")
    for var in sorted([v for v in variations if 'הלך' in v])[:20]:
        print(f"  {var}")

    # Direct search
    print("\nDirect search results:")
    results = search.search_word_with_variations('הלך', level='consonantal')
    psalm_15 = [r for r in results if r.book == 'Psalms' and r.chapter == 15]
    print(f"Total results: {len(results)}")
    print(f"Psalm 15 results: {len(psalm_15)}")

    if psalm_15:
        for r in psalm_15:
            print(f"  {r.reference}: {r.matched_word}")

if __name__ == "__main__":
    # Write to file
    import sys
    from io import StringIO

    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    try:
        test_holokh()
        output = mystdout.getvalue()
    finally:
        sys.stdout = old_stdout

    with open("holokh_test.txt", "w", encoding="utf-8") as f:
        f.write(output)

    print("Test results written to holokh_test.txt")