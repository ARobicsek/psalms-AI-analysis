#!/usr/bin/env python3
"""Find the root cause of phrase search failures"""

import sqlite3

def find_root_cause():
    """Find why phrase search is failing"""

    db_path = "c:/Users/ariro/OneDrive/Documents/Psalms/database/tanakh.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=== ROOT CAUSE ANALYSIS ===\n")

    # 1. Check if the variation generator is working
    print("1. Testing prefix variations:")

    # The word "גור" should have prefix variations like "יגור"
    cursor.execute("""
        SELECT DISTINCT word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15 AND verse = 1
        AND word_consonantal_split LIKE '%גור%'
    """)

    variations = cursor.fetchall()
    print(f"   Found {len(variations)} variations of 'גור' in Psalm 15:1")

    # 2. Check the actual phrase matching logic
    print("\n2. Checking phrase sequence:")

    # Get the sequence of words in Psalm 15:1
    cursor.execute("""
        SELECT position, word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15 AND verse = 1
        ORDER BY position
    """)

    words = cursor.fetchall()
    print(f"   Psalm 15:1 has {len(words)} words")

    # Look for "גור" and "אהל" or "באהל" in sequence
    gvr_pos = None
    ahl_variants = ['אהל', 'באהל']
    ahl_pos = None

    for pos, word in words:
        if 'גור' in word:
            gvr_pos = pos
            print(f"   Found 'גור' variant at position {pos}: {repr(word)}")
        if any(var in word for var in ahl_variants):
            ahl_pos = pos
            print(f"   Found 'אהל' variant at position {pos}: {repr(word)}")

    if gvr_pos and ahl_pos:
        distance = ahl_pos - gvr_pos
        print(f"   Distance between words: {distance}")
        if distance <= 3:  # Allow some intervening words
            print("   -> Words are close enough that phrase search should work!")
        else:
            print(f"   -> Words are too far apart ({distance} positions)")

    # 3. Test the specific search issue
    print("\n3. Testing search problem:")

    # Check if searching for "יגור" finds Psalm 15:1
    cursor.execute("""
        SELECT COUNT(*)
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15 AND verse = 1
        AND word_consonantal_split = 'יגור'
    """)

    count = cursor.fetchone()[0]
    print(f"   Exact 'יגור' in Psalm 15:1: {count}")

    # Check if searching for "גור" finds Psalm 15:1
    cursor.execute("""
        SELECT COUNT(*)
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15 AND verse = 1
        AND word_consonantal_split = 'גור'
    """)

    count = cursor.fetchone()[0]
    print(f"   Exact 'גור' in Psalm 15:1: {count}")

    # 4. The key issue
    print("\n4. KEY FINDING:")
    print("   The search phrase 'גור באהל' is looking for:")
    print("   - First word: 'גור'")
    print("   - Second word: 'באהל'")
    print("   ")
    print("   But Psalm 15:1 has:")
    print("   - 'יָגוּר' (with prefix י-)")
    print("   - 'בְּאׇהֳלֶךָ' (with prefix ב- and suffix ך)")
    print("   ")
    print("   The variation generator SHOULD create:")
    print("   - 'יגור' from 'גור' (adding prefix י-)")
    print("   - 'באהל' from 'באהלך' (removing suffix ך-)")
    print("   ")
    print("   If this isn't happening, that's the bug!")

    # 5. Check similar issue with Psalm 15:2
    print("\n5. Checking Psalm 15:2 for 'הלך תמים':")

    cursor.execute("""
        SELECT position, word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15 AND verse = 2
        ORDER BY position
    """)

    words = cursor.fetchall()

    for pos, word in words:
        if 'הלך' in word or 'תמ' in word:
            print(f"   Position {pos}: {repr(word)}")

    conn.close()

if __name__ == "__main__":
    find_root_cause()