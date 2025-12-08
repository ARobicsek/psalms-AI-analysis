#!/usr/bin/env python3
"""
Trace the phrase matching bug without Unicode printing issues.
"""

import sqlite3
import sys
from pathlib import Path

def main():
    print("TRACING PHRASE MATCHING BUG")
    print("=" * 80)
    print("Investigating why search_word_with_variations fails")

    db_path = Path(__file__).parent / "database" / "tanakh.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 1. Check what's actually in Psalm 15:1
    print("\n1. Words in Psalm 15:1:")
    cursor.execute("""
        SELECT position, word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15 AND verse = 1
        ORDER BY position
    """)
    words = cursor.fetchall()
    for word in words:
        print(f"  Position {word[0]}: {repr(word[1])}")

    # 2. Check for 'יגור' specifically
    print("\n2. Looking for 'יגור' in Psalm 15:")
    cursor.execute("""
        SELECT verse, position, word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15
        AND word_consonantal_split LIKE '%גור%'
    """)
    results = cursor.fetchall()
    print(f"  Found {len(results)} words with 'גור':")
    for r in results:
        print(f"    Verse {r[0]}, Pos {r[1]}: {repr(r[2])}")

    # 3. Test direct SQL query with variations
    print("\n3. Testing SQL query with variations:")
    variations = ['גור', 'יגור', 'וגור', 'הגור', 'מגור']
    placeholders = ','.join(['?' for _ in variations])

    query = f"""
        SELECT verse, position, word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15
        AND word_consonantal_split IN ({placeholders})
    """
    print(f"  Query: {query}")
    print(f"  Parameters: {variations}")

    cursor.execute(query, variations)
    matches = cursor.fetchall()
    print(f"\n  Results: {len(matches)} matches")
    for m in matches:
        print(f"    Found at 15:{m[0]}, pos {m[1]}: {repr(m[2])}")

    # 4. Check ConcordanceSearch if available
    print("\n4. Testing ConcordanceSearch._get_word_variations:")
    src_path = Path(__file__).parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    try:
        from concordance.search import ConcordanceSearch
        search = ConcordanceSearch()

        print("\n  Getting variations for 'גור':")
        variations = search._get_word_variations('גור')
        print(f"    Generated {len(variations)} variations")

        # Check first 20
        print("    First 20 variations:")
        for i, var in enumerate(list(variations)[:20]):
            print(f"      {i+1}. {repr(var)}")

        # Check if 'יגור' is there
        if 'יגור' in variations:
            print("    CRITICAL: 'יגור' IS in variations!")
        else:
            print("    CRITICAL: 'יגור' is NOT in variations!")

        # Test the search method
        print("\n  Testing search_word_with_variations('גור'):")
        results = search.search_word_with_variations('גור', level='consonantal')
        psalm15_results = [r for r in results
                         if r.book == 'Psalms' and r.chapter == 15]
        print(f"    Results in Psalm 15: {len(psalm15_results)}")

    except Exception as e:
        print(f"    Error: {e}")
        import traceback
        traceback.print_exc()

    conn.close()

    print("\n" + "=" * 80)
    print("ANALYSIS:")
    print("=" * 80)
    print("\nIf Psalm 15:1 contains 'יגור' but search_word_with_variations('גור')")
    print("doesn't find it, the issue is either:")
    print("1. _get_word_variations doesn't generate 'יגור'")
    print("2. The SQL query isn't properly matching the variations")
    print("3. The normalization level is causing mismatches")

if __name__ == "__main__":
    main()