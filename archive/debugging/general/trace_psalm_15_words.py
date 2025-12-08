#!/usr/bin/env python3
"""Trace exactly what words are in Psalm 15"""

import sqlite3

def trace_psalm_15():
    """Trace Psalm 15 words"""

    db_path = "c:/Users/ariro/OneDrive/Documents/Psalms/database/tanakh.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=== TRACING PSALM 15 WORDS ===\n")

    # Get all words in Psalm 15:1-5
    cursor.execute("""
        SELECT chapter, verse, position, word, word_consonantal, word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15 AND verse <= 5
        ORDER BY chapter, verse, position
    """)

    rows = cursor.fetchall()

    current_verse = None
    for row in rows:
        ch, v, pos, word, cons, split = row
        if v != current_verse:
            current_verse = v
            print(f"\n--- Psalm 15:{v} ---")

        print(f"  Pos {pos:2d}: {word:15s} | cons: {cons:15s} | split: {split:15s}")

    # Now test what happens when we search for "גור"
    print("\n=== TESTING SEARCH FOR 'גור' ===")

    # Check exact match
    cursor.execute("""
        SELECT chapter, verse, position, word, word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15 AND word_consonantal_split = 'גור'
    """)

    exact = cursor.fetchall()
    print(f"\nExact matches for 'גור': {len(exact)}")
    for row in exact:
        ch, v, pos, word, split = row
        print(f"  Psalm 15:{v} pos {pos}: {word} -> {split}")

    # Check for variations with prefixes
    cursor.execute("""
        SELECT chapter, verse, position, word, word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15
        AND word_consonantal_split LIKE '%גור%'
        ORDER BY verse, position
    """)

    variations = cursor.fetchall()
    print(f"\nAll variations containing 'גור': {len(variations)}")
    for row in variations:
        ch, v, pos, word, split = row
        print(f"  Psalm 15:{v} pos {pos}: {word} -> {split}")

    # Test "באהל" similarly
    print("\n=== TESTING SEARCH FOR 'באהל' ===")

    cursor.execute("""
        SELECT chapter, verse, position, word, word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15
        AND word_consonantal_split LIKE '%באהל%'
        ORDER BY verse, position
    """)

    variations = cursor.fetchall()
    print(f"\nAll variations containing 'באהל': {len(variations)}")
    for row in variations:
        ch, v, pos, word, split = row
        print(f"  Psalm 15:{v} pos {pos}: {word} -> {split}")

    # Test "הלך" and "תמים"
    print("\n=== TESTING SEARCH FOR 'הלך' AND 'תמים' ===")

    for test_word in ["הלך", "תמים"]:
        cursor.execute("""
            SELECT chapter, verse, position, word, word_consonantal_split
            FROM concordance
            WHERE book_name = 'Psalms' AND chapter = 15
            AND word_consonantal_split LIKE ?
            ORDER BY verse, position
        """, (f'%{test_word}%',))

        variations = cursor.fetchall()
        print(f"\nVariations containing '{test_word}': {len(variations)}")
        for row in variations:
            ch, v, pos, word, split = row
            print(f"  Psalm 15:{v} pos {pos}: {word} -> {split}")

    conn.close()

if __name__ == "__main__":
    trace_psalm_15()