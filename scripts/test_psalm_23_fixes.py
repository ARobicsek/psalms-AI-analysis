"""
Test all 5 fixes on Psalm 23 (which has empty contexts in current DB).
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


def get_stats(psalm_num):
    """Get statistics for a psalm."""
    conn = sqlite3.connect("c:/Users/ariro/OneDrive/Documents/Psalms/data/liturgy.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN liturgy_context = '' OR liturgy_context IS NULL THEN 1 ELSE 0 END) as empty,
            SUM(CASE WHEN match_type = 'exact_verse' THEN 1 ELSE 0 END) as exact,
            SUM(CASE WHEN match_type = 'phrase_match' THEN 1 ELSE 0 END) as phrases,
            SUM(CASE WHEN match_type = 'entire_chapter' THEN 1 ELSE 0 END) as chapters,
            SUM(CASE WHEN match_type = 'verse_range' THEN 1 ELSE 0 END) as ranges
        FROM psalms_liturgy_index
        WHERE psalm_chapter = ?
    """, (psalm_num,))

    total, empty, exact, phrases, chapters, ranges = cursor.fetchone()
    conn.close()

    return {
        'total': total,
        'empty': empty,
        'empty_pct': round(100 * empty / total, 1) if total > 0 else 0,
        'exact': exact,
        'phrases': phrases,
        'chapters': chapters,
        'ranges': ranges
    }


def main():
    print("="*80)
    print("TESTING ALL FIXES ON PSALM 23")
    print("="*80)

    # Get BEFORE stats
    print("\n--- BEFORE Re-indexing ---")
    before = get_stats(23)
    print(f"Total matches: {before['total']}")
    print(f"Empty contexts: {before['empty']} ({before['empty_pct']}%)")
    print(f"exact_verse: {before['exact']}")
    print(f"phrase_match: {before['phrases']}")
    print(f"entire_chapter: {before['chapters']}")
    print(f"verse_range: {before['ranges']}")

    # Re-index with fixes
    print("\n" + "="*80)
    print("RE-INDEXING WITH FIXES")
    print("="*80)

    indexer = LiturgyIndexer(verbose=True)
    result = indexer.index_psalm(23)

    # Get AFTER stats
    print("\n" + "="*80)
    print("AFTER Re-indexing")
    print("="*80)

    after = get_stats(23)
    print(f"\nTotal matches: {after['total']} (was {before['total']})")
    print(f"Empty contexts: {after['empty']} ({after['empty_pct']}%) (was {before['empty']} / {before['empty_pct']}%)")
    print(f"exact_verse: {after['exact']} (was {before['exact']})")
    print(f"phrase_match: {after['phrases']} (was {before['phrases']})")
    print(f"entire_chapter: {after['chapters']} (was {before['chapters']})")
    print(f"verse_range: {after['ranges']} (was {before['ranges']})")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    if after['empty'] < before['empty']:
        print(f"✓ Issue #1 (Empty contexts): IMPROVED - {before['empty'] - after['empty']} fixed")
    elif after['empty'] == 0:
        print(f"✓ Issue #1 (Empty contexts): FIXED - No empty contexts!")
    else:
        print(f"✗ Issue #1 (Empty contexts): NOT FIXED - Still {after['empty']} empty")

    if after['exact'] > before['exact']:
        print(f"✓ Issue #2/#4 (Phrase->Verse upgrades): {after['exact'] - before['exact']} more exact_verse matches")
    else:
        print(f"  Issue #2/#4: No change in exact_verse count")

    if after['ranges'] > before['ranges']:
        print(f"✓ Issue #5 (Verse ranges): {after['ranges']} verse_range entries created")
    else:
        print(f"  Issue #5: No verse_range entries (may be expected)")

    if after['chapters'] > before['chapters']:
        print(f"✓ Issue #3 (Entire chapters): {after['chapters']} entire_chapter entries created")
    else:
        print(f"  Issue #3: No entire_chapter entries (expected for partial psalms)")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
