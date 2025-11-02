"""
Test script to validate all 5 fixes on Psalm 1 and Psalm 6.

This script:
1. Captures BEFORE state (current index stats)
2. Re-indexes Psalm 1 and Psalm 6 with fixes
3. Shows AFTER state and improvements
4. Validates each specific fix worked
"""

import sqlite3
import sys
import io
from pathlib import Path

# Configure UTF-8 output for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from liturgy.liturgy_indexer import LiturgyIndexer


def get_stats_for_psalm(psalm_num):
    """Get statistics for a specific psalm."""
    conn = sqlite3.connect("c:/Users/ariro/OneDrive/Documents/Psalms/data/liturgy.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN liturgy_context = '' OR liturgy_context IS NULL THEN 1 ELSE 0 END) as empty_context,
            SUM(CASE WHEN match_type = 'exact_verse' THEN 1 ELSE 0 END) as exact_verses,
            SUM(CASE WHEN match_type = 'phrase_match' THEN 1 ELSE 0 END) as phrases,
            SUM(CASE WHEN match_type = 'entire_chapter' THEN 1 ELSE 0 END) as chapters,
            SUM(CASE WHEN match_type = 'verse_range' THEN 1 ELSE 0 END) as verse_ranges
        FROM psalms_liturgy_index
        WHERE psalm_chapter = ?
    """, (psalm_num,))

    result = cursor.fetchone()
    conn.close()

    return {
        'total': result[0],
        'empty_context': result[1],
        'empty_context_pct': round(result[1] / result[0] * 100, 1) if result[0] > 0 else 0,
        'exact_verses': result[2],
        'phrases': result[3],
        'chapters': result[4],
        'verse_ranges': result[5]
    }


def check_specific_issues():
    """Check if specific issues from docs/indexer_issues.txt are fixed."""
    conn = sqlite3.connect("c:/Users/ariro/OneDrive/Documents/Psalms/data/liturgy.db")
    cursor = conn.cursor()

    print("\n" + "="*80)
    print("CHECKING SPECIFIC ISSUE EXAMPLES")
    print("="*80)

    # Issue #2: Psalm 1:3 in prayer 626 should be ONE exact_verse (not 2 phrases)
    print("\n--- Issue #2: Psalm 1:3 in prayer 626 ---")
    cursor.execute("""
        SELECT index_id, match_type, psalm_phrase_hebrew
        FROM psalms_liturgy_index
        WHERE psalm_chapter = 1 AND psalm_verse_start = 3 AND prayer_id = 626
    """)

    results = cursor.fetchall()
    print(f"Number of entries: {len(results)}")
    for index_id, match_type, phrase in results:
        print(f"  - index_id {index_id}: {match_type}")
        print(f"    Phrase: {phrase[:60]}...")

    if len(results) == 1 and results[0][1] == 'exact_verse':
        print("✓ FIXED: Now has 1 exact_verse entry (was 2 phrases)")
    else:
        print("✗ NOT FIXED: Still has multiple entries or wrong type")

    # Issue #1: Check for empty contexts
    print("\n--- Issue #1: Empty contexts ---")
    cursor.execute("""
        SELECT COUNT(*) as empty_count
        FROM psalms_liturgy_index
        WHERE (psalm_chapter = 1 OR psalm_chapter = 6)
          AND (liturgy_context = '' OR liturgy_context IS NULL)
    """)

    empty_count = cursor.fetchone()[0]
    print(f"Empty contexts in Psalms 1 & 6: {empty_count}")

    if empty_count == 0:
        print("✓ FIXED: No empty contexts")
    else:
        print(f"✗ NOT FIXED: Still {empty_count} empty contexts")

        # Show examples
        cursor.execute("""
            SELECT index_id, psalm_chapter, psalm_verse_start, match_type
            FROM psalms_liturgy_index
            WHERE (psalm_chapter = 1 OR psalm_chapter = 6)
              AND (liturgy_context = '' OR liturgy_context IS NULL)
            LIMIT 5
        """)

        print("  Examples:")
        for index_id, ps, vs, mt in cursor.fetchall():
            print(f"    - index_id {index_id}: Psalm {ps}:{vs} ({mt})")

    # Issue #5: Check for verse_range entries
    print("\n--- Issue #5: Verse ranges ---")
    cursor.execute("""
        SELECT psalm_chapter, psalm_verse_start, psalm_verse_end, prayer_id
        FROM psalms_liturgy_index
        WHERE (psalm_chapter = 1 OR psalm_chapter = 6)
          AND match_type = 'verse_range'
    """)

    ranges = cursor.fetchall()
    if ranges:
        print(f"Found {len(ranges)} verse_range entries:")
        for ps, vs, ve, pr in ranges:
            print(f"  - Psalm {ps}:{vs}-{ve} in prayer {pr}")
        print("✓ FEATURE WORKING: verse_range detection functional")
    else:
        print("No verse_range entries found (may be expected if no consecutive sequences)")

    conn.close()


def main():
    """Run comprehensive test."""
    print("\n" + "="*80)
    print("TESTING INDEXER FIXES - PSALM 1 & 6")
    print("="*80)

    # Get BEFORE stats
    print("\n--- BEFORE RE-INDEXING ---")
    print("\nPsalm 1:")
    before_ps1 = get_stats_for_psalm(1)
    print(f"  Total matches: {before_ps1['total']}")
    print(f"  Empty contexts: {before_ps1['empty_context']} ({before_ps1['empty_context_pct']}%)")
    print(f"  exact_verse: {before_ps1['exact_verses']}")
    print(f"  phrase_match: {before_ps1['phrases']}")
    print(f"  entire_chapter: {before_ps1['chapters']}")
    print(f"  verse_range: {before_ps1['verse_ranges']}")

    print("\nPsalm 6:")
    before_ps6 = get_stats_for_psalm(6)
    print(f"  Total matches: {before_ps6['total']}")
    print(f"  Empty contexts: {before_ps6['empty_context']} ({before_ps6['empty_context_pct']}%)")
    print(f"  exact_verse: {before_ps6['exact_verses']}")
    print(f"  phrase_match: {before_ps6['phrases']}")
    print(f"  entire_chapter: {before_ps6['chapters']}")
    print(f"  verse_range: {before_ps6['verse_ranges']}")

    # Re-index with fixes
    print("\n" + "="*80)
    print("RE-INDEXING WITH FIXES")
    print("="*80)

    indexer = LiturgyIndexer(verbose=True)

    print("\n--- Indexing Psalm 1 ---")
    result1 = indexer.index_psalm(1)

    print("\n--- Indexing Psalm 6 ---")
    result6 = indexer.index_psalm(6)

    # Get AFTER stats
    print("\n" + "="*80)
    print("AFTER RE-INDEXING")
    print("="*80)

    print("\nPsalm 1:")
    after_ps1 = get_stats_for_psalm(1)
    print(f"  Total matches: {after_ps1['total']} (was {before_ps1['total']})")
    print(f"  Empty contexts: {after_ps1['empty_context']} ({after_ps1['empty_context_pct']}%) (was {before_ps1['empty_context_pct']}%)")
    print(f"  exact_verse: {after_ps1['exact_verses']} (was {before_ps1['exact_verses']})")
    print(f"  phrase_match: {after_ps1['phrases']} (was {before_ps1['phrases']})")
    print(f"  entire_chapter: {after_ps1['chapters']} (was {before_ps1['chapters']})")
    print(f"  verse_range: {after_ps1['verse_ranges']} (was {before_ps1['verse_ranges']})")

    print("\nPsalm 6:")
    after_ps6 = get_stats_for_psalm(6)
    print(f"  Total matches: {after_ps6['total']} (was {before_ps6['total']})")
    print(f"  Empty contexts: {after_ps6['empty_context']} ({after_ps6['empty_context_pct']}%) (was {before_ps6['empty_context_pct']}%)")
    print(f"  exact_verse: {after_ps6['exact_verses']} (was {before_ps6['exact_verses']})")
    print(f"  phrase_match: {after_ps6['phrases']} (was {before_ps6['phrases']})")
    print(f"  entire_chapter: {after_ps6['chapters']} (was {before_ps6['chapters']})")
    print(f"  verse_range: {after_ps6['verse_ranges']} (was {before_ps6['verse_ranges']})")

    # Check specific issues
    check_specific_issues()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY OF IMPROVEMENTS")
    print("="*80)

    total_before_empty = before_ps1['empty_context'] + before_ps6['empty_context']
    total_after_empty = after_ps1['empty_context'] + after_ps6['empty_context']

    print(f"\n1. Empty contexts:")
    print(f"   Before: {total_before_empty}")
    print(f"   After: {total_after_empty}")
    print(f"   Improvement: {total_before_empty - total_after_empty} fixed")

    total_before_exact = before_ps1['exact_verses'] + before_ps6['exact_verses']
    total_after_exact = after_ps1['exact_verses'] + after_ps6['exact_verses']

    print(f"\n2. Exact verse matches:")
    print(f"   Before: {total_before_exact}")
    print(f"   After: {total_after_exact}")
    print(f"   Improvement: {total_after_exact - total_before_exact} more exact verses")

    total_before_phrase = before_ps1['phrases'] + before_ps6['phrases']
    total_after_phrase = after_ps1['phrases'] + after_ps6['phrases']

    print(f"\n3. Phrase matches:")
    print(f"   Before: {total_before_phrase}")
    print(f"   After: {total_after_phrase}")
    print(f"   Change: {total_after_phrase - total_before_phrase} (should decrease as phrases upgrade to verses)")

    total_after_ranges = after_ps1['verse_ranges'] + after_ps6['verse_ranges']

    print(f"\n4. Verse ranges (NEW):")
    print(f"   After: {total_after_ranges}")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
