#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test why Psalm 21:8 matches 'לא ימוט לעולם' when it shouldn't"""

import sys
from src.concordance.search import ConcordanceSearch
from src.data_sources.tanakh_database import TanakhDatabase

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize database and search
db = TanakhDatabase()
search = ConcordanceSearch(db)

def test_psalm_21_8():
    print("=" * 80)
    print("TESTING WHY PSALM 21:8 INCORRECTLY MATCHES 'לא ימוט לעולם'")
    print("=" * 80)

    # The phrase being searched
    phrase = "לא ימוט לעולם"
    print(f"\nSearching for: '{phrase}'")
    print("-" * 40)

    # Search for the phrase
    results = search.search_phrase(phrase, level='consonantal', scope='auto')
    print(f"\nDirect search_phrase results: {len(results)}")

    # Check if Psalm 21:8 is in the results
    psalm_21_8_found = False
    for r in results:
        if r.book == 'Psalms' and r.chapter == 21 and r.verse == 8:
            psalm_21_8_found = True
            print(f"\n❌ PROBLEM: Psalm 21:8 incorrectly included!")
            print(f"  Matched phrase: {getattr(r, 'matched_phrase', 'N/A')}")
            print(f"  Matched word: {r.matched_word}")
            print(f"  Word position: {r.word_position}")
            break

    if not psalm_21_8_found:
        print("\n✓ Psalm 21:8 NOT found in direct search_phrase results")

    # Now let's check what the concordance librarian is doing differently
    print("\n\n" + "=" * 80)
    print("TESTING WITH VARIATIONS (what concordance librarian does)")
    print("=" * 80)

    # The librarian generates variations including "בלא ימוט לעולם"
    test_variations = [
        "לא ימוט לעולם",  # Original
        "בלא ימוט לעולם",  # With prefix ב
    ]

    for variation in test_variations:
        print(f"\nTesting variation: '{variation}'")
        results = search.search_phrase(variation, level='consonantal', scope='auto')
        print(f"  Results: {len(results)}")

        for r in results:
            if r.book == 'Psalms' and r.chapter == 21 and r.verse == 8:
                print(f"  ❌ Found Psalm 21:8 with variation '{variation}'")
                print(f"     Matched: '{r.matched_word}' at position {r.word_position}")

    # Check if Psalm 21:8 actually contains "בלא ימוט לעולם"
    print("\n\nCHECKING PSALM 21:8 CONTENT:")
    print("-" * 40)

    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT position, word, word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 21 AND verse = 8
        ORDER BY position
    """)

    words = cursor.fetchall()
    print("Words in Psalm 21:8:")
    for pos, word, cons_split in words:
        if word.strip():
            print(f"  Pos {pos}: {word} (split: {cons_split})")

    # Check specifically for "בל ימוט" pattern
    print("\n\nCHECKING FOR 'בל ימוט' PATTERN:")
    print("-" * 40)

    # Look for consecutive words "בל" and "ימוט"
    consecutive_pairs = []
    for i in range(len(words) - 1):
        word1 = words[i][2] if words[i][2] and words[i][2].strip() else words[i][1]
        word2 = words[i+1][2] if words[i+1][2] and words[i+1][2].strip() else words[i+1][1]
        if word1.strip() and word2.strip():
            consecutive_pairs.append(f"{word1} {word2}")

    print("Consecutive word pairs in Psalm 21:8:")
    for pair in consecutive_pairs:
        if "בל" in pair and "ימוט" in pair:
            print(f"  ❌ Found: '{pair}' - This matches the search!")
        elif "בל" in pair:
            print(f"  Found with בל: '{pair}'")

    # The issue: the librarian is generating "בלא ימוט לעולם" as a variation
    # When it searches for this, it might be matching the "בל ימוט" part
    # and then the phrase_in_verse fallback is accepting it as a match

    print("\n\nCONCLUSION:")
    print("-" * 40)
    print("The issue is likely that:")
    print("1. ConcordanceLibrarian generates 'בלא ימוט לעולם' as a variation")
    print("2. This variation doesn't exist exactly in the database")
    print("3. The fallback search finds 'בל ימוט' and incorrectly accepts it as a match")
    print("4. The phrase matching logic is too permissive with partial matches")

if __name__ == "__main__":
    test_psalm_21_8()