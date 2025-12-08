#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to trace phrase matching issues with proper Hebrew support.
"""

import sqlite3
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import os
    os.system('chcp 65001 >nul')

def check_database_content():
    """Check what's actually in the database for Psalm 15."""
    print("=" * 80)
    print("CHECKING DATABASE CONTENT FOR PSALM 15")
    print("=" * 80)

    db_path = Path(__file__).parent / "database" / "tanakh.db"
    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Get all words in Psalm 15:1-3
    print("\nAll words in Psalm 15:1-3:")
    cursor.execute("""
        SELECT verse, word_consonantal_split, position, hebrew_text
        FROM concordance
        WHERE book = 'Psalms' AND chapter = 15 AND verse <= 3
        ORDER BY verse, position
    """)

    words = cursor.fetchall()
    for word in words:
        print(f"  Verse {word[0]}:{word[2]} - {word[1]}")

    # Check specific words of interest
    print("\n" + "-" * 60)
    print("CHECKING SPECIFIC WORDS:")
    print("-" * 60)

    # Check for יגור (yagor) - should be in Psalm 15:1
    cursor.execute("""
        SELECT verse, position, word_consonantal_split
        FROM concordance
        WHERE book = 'Psalms' AND chapter = 15
        AND word_consonantal_split LIKE '%יגור%'
    """)
    results = cursor.fetchall()
    print(f"\nWords with 'יגור': {len(results)} found")
    for r in results:
        print(f"  Psalm 15:{r[0]} position {r[1]} - {r[2]}")

    # Check for הלך (halakh) - should be in Psalm 15:2
    cursor.execute("""
        SELECT verse, position, word_consonantal_split
        FROM concordance
        WHERE book = 'Psalms' AND chapter = 15
        AND word_consonantal_split LIKE '%הלך%'
    """)
    results = cursor.fetchall()
    print(f"\nWords with 'הלך': {len(results)} found")
    for r in results:
        print(f"  Psalm 15:{r[0]} position {r[1]} - {r[2]}")

    # Check for תמים (tamim) - should be in Psalm 15:2
    cursor.execute("""
        SELECT verse, position, word_consonantal_split
        FROM concordance
        WHERE book = 'Psalms' AND chapter = 15
        AND word_consonantal_split LIKE '%תמים%'
    """)
    results = cursor.fetchall()
    print(f"\nWords with 'תמים': {len(results)} found")
    for r in results:
        print(f"  Psalm 15:{r[0]} position {r[1]} - {r[2]}")

    conn.close()

def test_base_vs_variations():
    """Test if base words match their variations."""
    print("\n" + "=" * 80)
    print("TESTING BASE WORDS vs VARIATIONS")
    print("=" * 80)

    db_path = Path(__file__).parent / "database" / "tanakh.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Test cases: base word and its expected variation in Psalm 15
    test_cases = [
        ('גור', 'יגור'),  # base: gur, variation: yagor
        ('הלך', 'הלך'),  # base: halakh, variation: same
        ('תמים', 'תמים'),  # base: tamim, variation: same
    ]

    for base, expected in test_cases:
        print(f"\nTest case: base='{base}' -> expected='{expected}'")

        # Search for base word
        cursor.execute("""
            SELECT COUNT(*) FROM concordance
            WHERE book = 'Psalms' AND chapter = 15
            AND word_consonantal_split = ?
        """, (base,))
        base_count = cursor.fetchone()[0]
        print(f"  Base '{base}' in Psalm 15: {base_count} matches")

        # Search for expected variation
        cursor.execute("""
            SELECT verse, position FROM concordance
            WHERE book = 'Psalms' AND chapter = 15
            AND word_consonantal_split = ?
            ORDER BY verse, position
        """, (expected,))
        var_results = cursor.fetchall()
        print(f"  Variation '{expected}' in Psalm 15: {len(var_results)} matches")
        for v in var_results:
            print(f"    Found at 15:{v[0]} position {v[1]}")

    conn.close()

def check_variation_generator():
    """Check if the variation generator is working."""
    print("\n" + "=" * 80)
    print("CHECKING VARIATION GENERATOR")
    print("=" * 80)

    # Add src to path for imports
    src_path = Path(__file__).parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    try:
        # Import the Hebrew text processor
        from concordance.hebrew_text_processor import normalize_to_consonantal
        from concordance.search import ConcordanceSearch

        # Create search instance
        search = ConcordanceSearch()

        # Test variation generation
        test_words = ['גור', 'הלך', 'תמים']

        for word in test_words:
            print(f"\nTesting variations for '{word}':")

            # Get variations
            variations = search._get_word_variations(word)
            print(f"  Generated {len(variations)} variations")

            # Check first 10
            print("  First 10 variations:")
            for i, var in enumerate(list(variations)[:10]):
                print(f"    {i+1}. {var}")

            # Check if expected variation is included
            expected_map = {
                'גור': 'יגור',
                'הלך': 'הלך',
                'תמים': 'תמים'
            }

            expected = expected_map.get(word)
            if expected and expected in variations:
                print(f"  ✓ Expected variation '{expected}' found in list!")
            else:
                print(f"  ✗ Expected variation '{expected}' NOT found in list!")

            # Test search with variations
            results = search.search_word_with_variations(word, level='consonantal')
            psalm15_results = [r for r in results
                             if r.book == 'Psalms' and r.chapter == 15]
            print(f"  Search results in Psalm 15: {len(psalm15_results)}")
            for r in psalm15_results[:3]:
                print(f"    Found: {r.reference} - {r.matched_word}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def analyze_query_structure():
    """Analyze what queries are being executed."""
    print("\n" + "=" * 80)
    print("ANALYZING QUERY STRUCTURE")
    print("=" * 80)

    db_path = Path(__file__).parent / "database" / "tanakh.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check column types
    print("\nConcordance table structure:")
    cursor.execute("PRAGMA table_info(concordance)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]}: {col[2]}")

    # Test query that would be generated
    print("\nTesting typical variation query:")
    test_variations = ['גור', 'יגור', 'וגור', 'הגור']

    placeholders = ','.join(['?' for _ in test_variations])
    query = f"""
        SELECT book, chapter, verse, word_consonantal_split
        FROM concordance
        WHERE word_consonantal_split IN ({placeholders})
        AND book = 'Psalms' AND chapter = 15
    """

    print(f"Query: {query}")
    print(f"Parameters: {test_variations}")

    cursor.execute(query, test_variations)
    results = cursor.fetchall()
    print(f"\nResults: {len(results)} matches found")
    for r in results:
        print(f"  Psalm 15:{r[2]} - {r[3]}")

    conn.close()

def main():
    """Main function to run all tests."""
    print("DEBUGGING PHRASE MATCHING ISSUE")
    print("=" * 80)
    print("Issue: Base words not matching their prefixed forms in Psalm 15")

    check_database_content()
    test_base_vs_variations()
    check_variation_generator()
    analyze_query_structure()

    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("\nBased on the test results, we can determine:")
    print("1. Does the database contain the prefixed forms? (e.g., 'יגור')")
    print("2. Does the variation generator create the right prefixes?")
    print("3. Does the SQL query properly search for all variations?")
    print("\nThis will pinpoint exactly where the matching fails.")

if __name__ == "__main__":
    main()