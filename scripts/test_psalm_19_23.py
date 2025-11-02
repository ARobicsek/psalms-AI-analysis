"""
Quick test for Psalms 19 and 23 with all fixes applied.

Tests:
- Psalm 23 in Prayer 574 (Shabbat Kiddush) - should detect entire_chapter
- Psalm 19 in Prayer 251 - should detect entire_chapter
"""
import sys
import os
import time

# Configure UTF-8 output for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.liturgy.liturgy_indexer import LiturgyIndexer

if __name__ == "__main__":
    print("=" * 70)
    print("TESTING FIXES: Psalms 19 and 23")
    print("=" * 70)
    print()
    print("Fixes applied:")
    print("  1. Maqqef normalization (replace BEFORE vowel stripping)")
    print("  2. Improved deduplication (interval merging)")
    print("  3. Entire chapter detection (when all verses present)")
    print()

    # Initialize indexer (verbose=True to see progress)
    indexer = LiturgyIndexer(verbose=True)

    # Track statistics
    start_time = time.time()

    # Index Psalm 19
    print("\n" + "=" * 70)
    print("INDEXING PSALM 19")
    print("=" * 70)
    result_19 = indexer.index_psalm(19)

    # Index Psalm 23
    print("\n" + "=" * 70)
    print("INDEXING PSALM 23")
    print("=" * 70)
    result_23 = indexer.index_psalm(23)

    # Print summary
    elapsed = time.time() - start_time
    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print(f"Time elapsed: {elapsed:.1f} seconds")
    print()

    print("Psalm 19 Results:")
    print(f"  Total matches: {result_19.get('total_matches', 0)}")
    if 'match_details' in result_19:
        for match_type, count in result_19['match_details'].items():
            print(f"    {match_type}: {count}")

    print()
    print("Psalm 23 Results:")
    print(f"  Total matches: {result_23.get('total_matches', 0)}")
    if 'match_details' in result_23:
        for match_type, count in result_23['match_details'].items():
            print(f"    {match_type}: {count}")

    # Check specific prayers
    print()
    print("=" * 70)
    print("CHECKING SPECIFIC PRAYERS")
    print("=" * 70)

    import sqlite3
    conn = sqlite3.connect('data/liturgy.db')
    cursor = conn.cursor()

    # Check Psalm 19 in Prayer 251
    cursor.execute("""
        SELECT match_type, COUNT(*)
        FROM psalms_liturgy_index
        WHERE psalm_chapter = 19 AND prayer_id = 251
        GROUP BY match_type
    """)

    print("\nPsalm 19 in Prayer 251:")
    results = cursor.fetchall()
    if results:
        for match_type, count in results:
            print(f"  {match_type}: {count}")
    else:
        print("  No matches found")

    # Check Psalm 23 in Prayer 574
    cursor.execute("""
        SELECT match_type, COUNT(*)
        FROM psalms_liturgy_index
        WHERE psalm_chapter = 23 AND prayer_id = 574
        GROUP BY match_type
    """)

    print("\nPsalm 23 in Prayer 574 (Shabbat Kiddush):")
    results = cursor.fetchall()
    if results:
        for match_type, count in results:
            print(f"  {match_type}: {count}")
    else:
        print("  No matches found")

    conn.close()

    print()
    print("Expected results:")
    print("  - Both should show '1 entire_chapter' match (not multiple verse/phrase matches)")
    print("  - This indicates entire chapter detection is working correctly")
    print()
