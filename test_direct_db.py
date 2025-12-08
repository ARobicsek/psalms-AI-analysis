#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Direct database test to understand word variations matching"""

import sqlite3
import sys
import os

def test_database():
    """Test database directly with SQL queries"""
    db_path = "c:/Users/ariro/OneDrive/Documents/Psalms/database/tanakh.db"

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Test 1: Check if Psalm 15:1 contains "יגור"
    print("=== Test 1: Direct query for יגור in Psalm 15:1 ===")
    cursor.execute("""
        SELECT word, word_consonantal, word_consonantal_split, position
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15 AND verse = 1
        ORDER BY position
    """)

    psalm_15_1 = cursor.fetchall()
    print(f"Psalm 15:1 has {len(psalm_15_1)} words:")
    for row in psalm_15_1:
        print(f"  Position {row['position']}: {row['word']} | {row['word_consonantal']} | {row['word_consonantal_split']}")

    # Test 2: Check for any verse containing "יגור"
    print("\n=== Test 2: Any verse with word_consonantal_split = 'יגור' ===")
    cursor.execute("""
        SELECT book_name, chapter, verse, word
        FROM concordance
        WHERE word_consonantal_split = 'יגור'
        LIMIT 10
    """)

    yigurot = cursor.fetchall()
    print(f"Found {len(yigurot)} instances of 'יגור':")
    for row in yigurot:
        print(f"  {row['book_name']} {row['chapter']}:{row['verse']} - {row['word']}")

    # Test 3: Generate variations for "גור" and check if they're in DB
    print("\n=== Test 3: Generate variations for 'גור' ===")

    # Simulate variation generation
    base_word = "גור"
    prefixes = ["", "ו", "ב", "ל", "מ", "כ", "ה", "ש"]
    suffixes = ["", "ו", "ך", "י", "נו", "ם", "ן", "ה", "יך", "יו", "יה", "ינו", "יכם", "יכן"]

    variations = set()
    for prefix in prefixes:
        for suffix in suffixes:
            variations.add(prefix + base_word + suffix)

    print(f"Generated {len(variations)} variations for 'גור'")

    # Check if any of these variations are in Psalm 15
    print("\nChecking if any variations appear in Psalm 15...")
    for variation in list(variations)[:20]:  # Check first 20
        cursor.execute("""
            SELECT chapter, verse, position
            FROM concordance
            WHERE book_name = 'Psalms' AND chapter = 15
            AND word_consonantal_split = ?
        """, (variation,))
        results = cursor.fetchall()
        if results:
            print(f"  Found '{variation}' in Psalm 15:")
            for r in results:
                print(f"    Verse {r['verse']}, position {r['position']}")

    # Test 4: Check the normalization issue
    print("\n=== Test 4: Normalization check ===")

    # Check what normalize_for_search_split does to "יגור"
    test_word = "יגור"
    cursor.execute("""
        SELECT word, word_consonantal, word_consonantal_split
        FROM concordance
        WHERE word_consonantal_split LIKE ?
        LIMIT 5
    """, (f"%{test_word}%",))

    results = cursor.fetchall()
    for row in results:
        print(f"  Word: {row['word']}")
        print(f"  Consonantal: {row['word_consonantal']}")
        print(f"  Split: {row['word_consonantal_split']}")
        print()

    conn.close()

if __name__ == "__main__":
    try:
        test_database()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()