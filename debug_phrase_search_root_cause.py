#!/usr/bin/env python3
"""
Debug script to trace the root cause of phrase search non-matching.

Issue: search_word_with_variations() is not finding morphological variants
like "יגור" when searching for "גור" from Psalm 15:1.
"""

import sys
import os
import sqlite3
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import needed modules with absolute imports
from data_sources.tanakh_database import TanakhDatabase
from concordance.search import ConcordanceSearch

def test_direct_database_query():
    """Test direct database queries to verify data exists."""
    print("=" * 80)
    print("1. DIRECT DATABASE QUERY TEST")
    print("=" * 80)

    db_path = Path(__file__).parent / "database" / "tanakh.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check if Psalm 15:1 contains יגור
    print("\nChecking Psalm 15:1 for 'יגור':")
    cursor.execute("""
        SELECT verse_text, word_consonantal_split, position
        FROM concordance
        WHERE book = 'Psalms' AND chapter = 15 AND verse = 1
        AND word_consonantal_split LIKE '%יגור%'
        ORDER BY position
    """)

    results = cursor.fetchall()
    if results:
        print(f"✓ Found {len(results)} matches:")
        for row in results:
            print(f"  - Word: {row[1]} at position {row[2]}")
            print(f"    Text: ...{row[0][:50]}...")
    else:
        print("✗ No matches found for 'יגור' in Psalm 15:1")

    # Check all words in Psalm 15:1
    print("\nAll words in Psalm 15:1:")
    cursor.execute("""
        SELECT word_consonantal_split, position
        FROM concordance
        WHERE book = 'Psalms' AND chapter = 15 AND verse = 1
        ORDER BY position
    """)

    words = cursor.fetchall()
    for word in words:
        print(f"  Position {word[1]}: {word[0]}")

    # Check for any word containing 'גור'
    print("\nWords containing 'גור' in Psalm 15:")
    cursor.execute("""
        SELECT book, chapter, verse, word_consonantal_split, position
        FROM concordance
        WHERE book = 'Psalms' AND chapter = 15
        AND word_consonantal_split LIKE '%גור%'
        ORDER BY chapter, verse, position
    """)

    gur_results = cursor.fetchall()
    print(f"Found {len(gur_results)} words with 'גור':")
    for row in gur_results:
        print(f"  Psalm {row[1]}:{row[2]} - {row[3]} (position {row[4]})")

    conn.close()

def test_variation_generation():
    """Test if variations are being generated correctly."""
    print("\n" + "=" * 80)
    print("2. VARIATION GENERATION TEST")
    print("=" * 80)

    search = ConcordanceSearch()

    # Test _get_word_variations method directly
    print("\nTesting _get_word_variations('גור'):")
    try:
        variations = search._get_word_variations('גור')
        print(f"Generated {len(variations)} variations:")

        # Check for expected variations
        expected = ['יגור', 'וגור', 'מגור', 'בגור', 'לגור', 'כגור',
                   'שגור', 'הגור', 'תגור', 'נגור']
        found = []
        missing = []

        for exp in expected:
            if exp in variations:
                found.append(exp)
            else:
                missing.append(exp)

        print(f"\n✓ Found expected variations: {found}")
        print(f"✗ Missing expected variations: {missing}")

        # Print first 20 variations for inspection
        print("\nFirst 20 variations generated:")
        for i, var in enumerate(list(variations)[:20]):
            print(f"  {i+1}. {var}")

        # Check if 'יגור' is specifically in variations
        if 'יגור' in variations:
            print(f"\n✓ CRITICAL: 'יגור' IS in variations list!")
        else:
            print(f"\n✗ CRITICAL: 'יגור' is NOT in variations list!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_search_word_with_variations():
    """Test the search_word_with_variations method directly."""
    print("\n" + "=" * 80)
    print("3. SEARCH_WORD_WITH_VARIATIONS TEST")
    print("=" * 80)

    search = ConcordanceSearch()

    # Test searching for 'גור'
    print("\nTesting search_word_with_variations('גור'):")
    try:
        results = search.search_word_with_variations('גור', level='consonantal')
        print(f"Found {len(results)} results")

        # Check if Psalm 15:1 is in results
        psalm_15_found = False
        for result in results:
            if result.book == 'Psalms' and result.chapter == 15 and result.verse == 1:
                psalm_15_found = True
                print(f"\n✓ CRITICAL: Found Psalm 15:1!")
                print(f"  Matched word: {result.matched_word}")
                print(f"  Context: {result.context}")
                break

        if not psalm_15_found:
            print(f"\n✗ CRITICAL: Psalm 15:1 NOT found in results!")
            print("\nFirst 5 results:")
            for i, result in enumerate(results[:5]):
                print(f"  {i+1}. {result.reference} - {result.matched_word}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_individual_variations():
    """Test searching for individual variations."""
    print("\n" + "=" * 80)
    print("4. INDIVIDUAL VARIATION SEARCH TEST")
    print("=" * 80)

    search = ConcordanceSearch()

    test_variations = ['גור', 'יגור', 'וגור', 'הגור', 'מגור']

    for variation in test_variations:
        print(f"\nSearching for '{variation}':")
        try:
            results = search.search_word(variation, level='consonantal')
            psalm_15_results = [r for r in results
                              if r.book == 'Psalms' and r.chapter == 15 and r.verse == 1]

            if psalm_15_results:
                print(f"  ✓ Found Psalm 15:1 ({len(psalm_15_results)} matches)")
                for r in psalm_15_results:
                    print(f"    - Matched: {r.matched_word}")
            else:
                print(f"  ✗ Psalm 15:1 not found (total results: {len(results)})")
                if results:
                    print(f"    First result: {results[0].reference} - {results[0].matched_word}")

        except Exception as e:
            print(f"  Error: {e}")

def test_sql_query_generation():
    """Test what SQL queries are being generated."""
    print("\n" + "=" * 80)
    print("5. SQL QUERY GENERATION TEST")
    print("=" * 80)

    # This is a bit tricky since we can't easily intercept SQL,
    # but we can check the query structure

    from concordance.search import normalize_to_consonantal

    search = ConcordanceSearch()

    print("\nTesting normalization:")
    test_words = ['גור', 'יגור', 'וגור', 'הגור']
    for word in test_words:
        normalized = normalize_to_consonantal(word)
        print(f"  '{word}' -> '{normalized}'")

    print("\nExpected SQL pattern for 'גור':")
    print("  SELECT * FROM concordance WHERE word_consonantal_split IN ('גור', 'יגור', ...)")

    # Try to understand the column structure
    db_path = Path(__file__).parent / "database" / "tanakh.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("\nColumn info for concordance table:")
    cursor.execute("PRAGMA table_info(concordance)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

    # Check exact value stored for Psalm 15:1
    cursor.execute("""
        SELECT word_consonantal_split
        FROM concordance
        WHERE book = 'Psalms' AND chapter = 15 AND verse = 1
        AND position = 3
    """)
    result = cursor.fetchone()
    if result:
        print(f"\nExact value at Psalm 15:1, position 3: '{result[0]}'")

    conn.close()

def main():
    print("DEBUGGING PHRASE SEARCH ROOT CAUSE")
    print("=" * 80)
    print("Issue: search_word_with_variations('גור') not finding 'יגור' in Psalm 15:1")

    # Run all tests
    test_direct_database_query()
    test_variation_generation()
    test_search_word_with_variations()
    test_individual_variations()
    test_sql_query_generation()

    print("\n" + "=" * 80)
    print("SUMMARY AND NEXT STEPS")
    print("=" * 80)
    print("\nBased on the test results above, we can identify where the issue occurs:")
    print("1. If 'יגור' is in the database but not in variations -> Issue in _get_word_variations")
    print("2. If 'יגור' is in variations but not found -> Issue in SQL query or matching")
    print("3. If individual search for 'יגור' works -> Issue in the list/parameter passing")
    print("4. If individual search fails -> Issue in base search_word method")

if __name__ == "__main__":
    main()