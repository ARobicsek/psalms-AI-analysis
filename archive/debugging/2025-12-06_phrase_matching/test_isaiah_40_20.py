#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test why Isaiah 40:20 matches 'לא ימוט לעולם' when it only has 'לא ימוט'"""

import sys
from src.concordance.search import ConcordanceSearch
from src.data_sources.tanakh_database import TanakhDatabase

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize database and search
db = TanakhDatabase()
search = ConcordanceSearch(db)

def test_isaiah_40_20():
    print("=" * 80)
    print("TESTING WHY ISAIAH 40:20 MATCHES 'לא ימוט לעולם'")
    print("=" * 80)

    # Check what Isaiah 40:20 actually contains
    print("\nISAIAH 40:20 CONTENT:")
    print("-" * 40)

    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT hebrew, english
        FROM verses
        WHERE book_name = 'Isaiah' AND chapter = 40 AND verse = 20
    """)

    verse_info = cursor.fetchone()
    if verse_info:
        print(f"Hebrew: {verse_info[0]}")
        print(f"English: {verse_info[1]}")

        # Get all words in this verse
        cursor.execute("""
            SELECT position, word, word_consonantal_split
            FROM concordance
            WHERE book_name = 'Isaiah' AND chapter = 40 AND verse = 20
            ORDER BY position
        """)

        words = cursor.fetchall()
        print(f"\nWords in verse:")
        for pos, word, cons_split in words:
            if word.strip():
                print(f"  Pos {pos}: {word} (split: {cons_split})")

    # Test the search with variations
    print("\n\n" + "=" * 80)
    print("TESTING SEARCH FOR 'לא ימוט לעולם'")
    print("=" * 80)

    # The full phrase search
    print(f"\n1. Direct search for 'לא ימוט לעולם':")
    results = search.search_phrase("לא ימוט לעולם", level='consonantal', scope='auto')
    print(f"   Results: {len(results)}")

    # Check if Isaiah 40:20 appears
    isaiah_found = False
    for r in results:
        if r.book == 'Isaiah' and r.chapter == 40 and r.verse == 20:
            isaiah_found = True
            print(f"   ❌ Isaiah 40:20 found!")
            print(f"      Matched: {r.matched_word}")
            break

    if not isaiah_found:
        print("   ✓ Isaiah 40:20 NOT found in direct search")

    # Test search for just "לא ימוט"
    print(f"\n2. Search for just 'לא ימוט':")
    results2 = search.search_phrase("לא ימוט", level='consonantal', scope='auto')
    print(f"   Results: {len(results2)}")

    for r in results2:
        if r.book == 'Isaiah' and r.chapter == 40 and r.verse == 20:
            print(f"   ✓ Found Isaiah 40:20 with 'לא ימוט'")
            print(f"      Matched: {r.matched_word}")
            if hasattr(r, 'matched_phrase') and r.matched_phrase:
                print(f"      Full phrase matched: {r.matched_phrase}")
            break

    # Test search_phrase_in_verse (fallback)
    print(f"\n3. Fallback search (search_phrase_in_verse) for 'לא ימוט לעולם':")
    results3 = search.search_phrase_in_verse("לא ימוט לעולם", level='consonantal', scope='auto')
    print(f"   Results: {len(results3)}")

    for r in results3:
        if r.book == 'Isaiah' and r.chapter == 40 and r.verse == 20:
            print(f"   ❌ Isaiah 40:20 found in fallback search!")
            print(f"      Matched: {r.matched_word}")
            break

    # Now let's trace what the ConcordanceLibrarian does
    print("\n\n" + "=" * 80)
    print("TRACING CONCORDANCE LIBRARIAN PROCESS")
    print("=" * 80)

    # The librarian generates many variations
    print("\nThe librarian generates 2841 variations including:")
    print("  - לא ימוט לעולם (original)")
    print("  - בלא ימוט לעולם (with prefix)")
    print("  - ... and many more")

    # When it searches for "לא ימוט לעולם", it uses search_phrase_in_verse as fallback
    print("\nWhen searching for 'לא ימוט לעולם':")
    print("  1. Tries exact phrase match (finds 0 results)")
    print("  2. Falls back to search_phrase_in_verse")
    print("  3. search_phrase_in_verse looks for verses containing ALL words")
    print("  4. Isaiah 40:20 has 'לא ימוט' but NOT 'לעולם'")
    print("  5. Yet it's being included - THIS IS THE BUG!")

    # Check if 'לעולם' appears anywhere in Isaiah 40:20
    print(f"\n4. Does 'לעולם' appear in Isaiah 40:20?")
    cursor.execute("""
        SELECT COUNT(*) FROM concordance
        WHERE book_name = 'Isaiah' AND chapter = 40 AND verse = 20
        AND word_consonantal_split LIKE '%לעולם%'
    """)
    count = cursor.fetchone()[0]
    print(f"   Occurrences of 'לעולם': {count}")

    # Let's manually check _verse_contains_all_words
    print(f"\n5. Manual check of _verse_contains_all_words:")
    from src.concordance.hebrew_text_processor import normalize_for_search_split, split_words

    # Check if Isaiah 40:20 contains all words
    words = ["לא", "ימוט", "לעולם"]
    normalized_words = [normalize_for_search_split(w, 'consonantal') for w in words]

    contains_all = search._verse_contains_all_words(
        'Isaiah', 40, 20, normalized_words, 'word_consonantal_split'
    )
    print(f"   Does Isaiah 40:20 contain all words? {contains_all}")

    # Check each word individually
    print(f"\n   Checking each word:")
    for word in normalized_words:
        cursor.execute("""
            SELECT COUNT(*) FROM concordance
            WHERE book_name = 'Isaiah' AND chapter = 40 AND verse = 20
            AND word_consonantal_split = ?
        """, (word,))
        count = cursor.fetchone()[0]
        print(f"     '{word}': {'✓' if count > 0 else '✗'}")

if __name__ == "__main__":
    test_isaiah_40_20()