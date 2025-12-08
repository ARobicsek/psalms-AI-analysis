#!/usr/bin/env python3
"""
Simple debug script to trace phrase matching issues.
Works directly with database to understand the root cause.
"""

import sqlite3
from pathlib import Path

def check_database_content():
    """Check what's actually in the database for Psalm 15."""
    print("=" * 80)
    print("CHECKING DATABASE CONTENT FOR PSALM 15")
    print("=" * 80)

    db_path = Path(__file__).parent / "database" / "tanakh.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Get all words in Psalm 15:1-3
    print("\nAll words in Psalm 15:1-3 (word_consonantal_split):")
    cursor.execute("""
        SELECT verse, word_consonantal_split, position, word_hebrew
        FROM concordance
        WHERE book = 'Psalms' AND chapter = 15 AND verse <= 3
        ORDER BY verse, position
    """)

    words = cursor.fetchall()
    for word in words:
        print(f"  v{word[0]}:{word[2]} - {word[1]} (hebrew: {word[3] or 'None'})")

    # Check specifically for words with 'גור' (gur)
    print("\nWords containing 'גור' in Psalm 15:")
    cursor.execute("""
        SELECT verse, word_consonantal_split, position
        FROM concordance
        WHERE book = 'Psalms' AND chapter = 15
        AND word_consonantal_split LIKE '%גור%'
        ORDER BY verse, position
    """)

    gur_words = cursor.fetchall()
    print(f"Found {len(gur_words)} words with 'גור':")
    for word in gur_words:
        print(f"  v{word[0]}:{word[2]} - {word[1]}")

    # Check specifically for words with 'הלך' (halakh)
    print("\nWords containing 'הלך' in Psalm 15:")
    cursor.execute("""
        SELECT verse, word_consonantal_split, position
        FROM concordance
        WHERE book = 'Psalms' AND chapter = 15
        AND word_consonantal_split LIKE '%הלך%'
        ORDER BY verse, position
    """)

    halakh_words = cursor.fetchall()
    print(f"Found {len(halakh_words)} words with 'הלך':")
    for word in halakh_words:
        print(f"  v{word[0]}:{word[2]} - {word[1]}")

    # Check specifically for words with 'תמים' (tamim)
    print("\nWords containing 'תמים' in Psalm 15:")
    cursor.execute("""
        SELECT verse, word_consonantal_split, position
        FROM concordance
        WHERE book = 'Psalms' AND chapter = 15
        AND word_consonantal_split LIKE '%תמים%'
        ORDER BY verse, position
    """)

    tamim_words = cursor.fetchall()
    print(f"Found {len(tamim_words)} words with 'תמים':")
    for word in tamim_words:
        print(f"  v{word[0]}:{word[2]} - {word[1]}")

    conn.close()

def test_variations_directly():
    """Test if variations would match with direct SQL."""
    print("\n" + "=" * 80)
    print("TESTING VARIATION MATCHING WITH DIRECT SQL")
    print("=" * 80)

    db_path = Path(__file__).parent / "database" / "tanakh.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Test base word and common variations
    test_cases = [
        {
            'base': 'גור',
            'variations': ['גור', 'יגור', 'וגור', 'הגור', 'מגור', 'לגור', 'כגור', 'שגור']
        },
        {
            'base': 'הלך',
            'variations': ['הלך', 'והלך', 'מהלך', 'להלך', 'הלכו', 'הולך', 'הולכים']
        },
        {
            'base': 'תמים',
            'variations': ['תמים', 'ותמים', 'התם', 'מתמם', 'תמימם', 'תמים', 'תמים']
        }
    ]

    for test in test_cases:
        print(f"\nTesting base word '{test['base']}':")
        base = test['base']

        # Check base word
        cursor.execute("""
            SELECT COUNT(*) FROM concordance
            WHERE book = 'Psalms' AND chapter = 15
            AND word_consonantal_split = ?
        """, (base,))
        count = cursor.fetchone()[0]
        print(f"  Exact match for '{base}': {count}")

        # Check each variation
        for var in test['variations']:
            cursor.execute("""
                SELECT verse, position FROM concordance
                WHERE book = 'Psalms' AND chapter = 15
                AND word_consonantal_split = ?
                ORDER BY verse, position
            """, (var,))
            matches = cursor.fetchall()
            if matches:
                print(f"  ✓ '{var}' found: {matches}")
            else:
                print(f"  ✗ '{var}' not found")

    conn.close()

def analyze_variation_patterns():
    """Analyze common prefix/suffix patterns in Psalm 15."""
    print("\n" + "=" * 80)
    print("ANALYZING PREFIX/SUFFIX PATTERNS IN PSALM 15")
    print("=" * 80)

    db_path = Path(__file__).parent / "database" / "tanakh.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Get all unique words in Psalm 15
    cursor.execute("""
        SELECT DISTINCT word_consonantal_split, word_hebrew
        FROM concordance
        WHERE book = 'Psalms' AND chapter = 15
        ORDER BY word_consonantal_split
    """)

    words = cursor.fetchall()

    # Analyze prefixes
    prefixes = {}
    for word in words:
        if len(word[0]) > 2:
            prefix = word[0][:1]
            if prefix in ['ו', 'ב', 'ל', 'ה', 'מ', 'כ', 'ש']:
                if prefix not in prefixes:
                    prefixes[prefix] = []
                prefixes[prefix].append(word[0])

    print("\nPrefix analysis:")
    for prefix, words_list in prefixes.items():
        print(f"\n  Prefix '{prefix}' ({len(words_list)} words):")
        for w in words_list[:5]:  # Show first 5
            print(f"    {w}")
        if len(words_list) > 5:
            print(f"    ... and {len(words_list) - 5} more")

    conn.close()

def main():
    print("SIMPLE DEBUG OF PHRASE MATCHING ISSUE")
    print("=" * 80)
    print("Goal: Understand why base words don't match their prefixed forms in Psalm 15")

    check_database_content()
    test_variations_directly()
    analyze_variation_patterns()

    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print("\nExpected findings:")
    print("1. Psalm 15:1 contains 'יגור' at position 3")
    print("2. Psalm 15:2 contains 'הלך' and 'תמים'")
    print("3. Base words 'גור', 'הלך', 'תמים' don't exist in Psalm 15")
    print("4. Only their prefixed forms exist")
    print("\nThis would confirm the issue: The variation generator needs to")
    print("create 'יגור' from 'גור' to find the match.")

if __name__ == "__main__":
    main()