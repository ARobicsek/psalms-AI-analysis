#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Test final fix for all matching issues"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.concordance.search import ConcordanceSearch

def test_final_fix():
    """Test comprehensive fix"""

    search = ConcordanceSearch()

    # Direct search for הולך
    print("=== Direct Search Test ===")
    results = search.search_word_with_variations('הולך', level='consonantal')
    psalm_15 = [r for r in results if r.book == 'Psalms' and r.chapter == 15]
    print(f"Direct search for 'הולך' found {len(results)} total, {len(psalm_15)} in Psalm 15")

    # Now search for הלך with substring approach
    print("\n=== Enhanced Search Test ===")
    # We need to modify the search to ALWAYS include substring matches for short words

    # Get all words in Psalm 15
    cursor = search.db.conn.cursor()
    cursor.execute("""
        SELECT word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15
    """)

    psalm_words = [row[0] for row in cursor.fetchall() if row[0]]

    # Test substring matching directly
    test_cases = [
        ('הלך', 'הולך'),
        ('גור', 'יגור'),
        ('אהל', 'אהל'),
        ('בלב', 'בלבבו'),
    ]

    for search_term, target in test_cases:
        # Check if target is in Psalm 15 words
        found = any(target in word for word in psalm_words)
        print(f"\nSearch: '{search_term}' -> Target: '{target}'")
        print(f"  Target in Psalm 15: {found}")

        if found:
            # Find which verse
            cursor.execute("""
                SELECT chapter, verse, word_consonantal_split
                FROM concordance
                WHERE book_name = 'Psalms' AND chapter = 15
                AND word_consonantal_split LIKE ?
                LIMIT 5
            """, (f"%{target}%",))

            matches = cursor.fetchall()
            for match in matches:
                print(f"  Found in 15:{match['verse']} - {match['word_consonantal_split']}")

if __name__ == "__main__":
    # Write to file
    import sys
    from io import StringIO

    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    try:
        test_final_fix()
        output = mystdout.getvalue()
    finally:
        sys.stdout = old_stdout

    with open("final_fix_test.txt", "w", encoding="utf-8") as f:
        f.write(output)

    print("Test results written to final_fix_test.txt")