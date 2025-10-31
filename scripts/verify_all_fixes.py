"""
Quick verification script to test fixes on multiple problem Psalms.
Tests Psalms with historically high empty context rates.
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
            SUM(CASE WHEN liturgy_context = '' OR liturgy_context IS NULL THEN 1 ELSE 0 END) as empty
        FROM psalms_liturgy_index
        WHERE psalm_chapter = ?
    """, (psalm_num,))

    total, empty = cursor.fetchone()
    conn.close()

    return {
        'total': total or 0,
        'empty': empty or 0,
        'empty_pct': round(100 * (empty or 0) / total, 1) if total and total > 0 else 0
    }


def test_psalm(psalm_num, indexer):
    """Test a single psalm."""
    print(f"\n{'='*80}")
    print(f"Testing Psalm {psalm_num}")
    print('='*80)

    # Get BEFORE stats
    before = get_stats(psalm_num)
    print(f"\nBEFORE: {before['total']} matches, {before['empty']} empty ({before['empty_pct']}%)")

    # Re-index
    print(f"\nRe-indexing Psalm {psalm_num}...")
    indexer.index_psalm(psalm_num)

    # Get AFTER stats
    after = get_stats(psalm_num)
    print(f"\nAFTER: {after['total']} matches, {after['empty']} empty ({after['empty_pct']}%)")

    # Check if fixed
    if after['empty'] == 0:
        print(f"✓ SUCCESS: All contexts extracted correctly!")
        return True
    elif after['empty'] < before['empty']:
        print(f"⚠ PARTIAL: Improved from {before['empty']} to {after['empty']} empty")
        return False
    else:
        print(f"✗ FAILED: Still has {after['empty']} empty contexts")
        return False


def main():
    """Test fixes on multiple problem Psalms."""
    print("="*80)
    print("VERIFYING FIXES ON PROBLEM PSALMS")
    print("="*80)
    print("\nTesting on Psalms with historically high empty context rates:")
    print("- Psalm 45: 86.2% empty (worst case)")
    print("- Psalm 89: 50.7% empty")
    print("- Psalm 10: 49.2% empty")

    # Create indexer (quiet mode)
    indexer = LiturgyIndexer(verbose=False)

    # Test problem Psalms
    test_psalms = [45, 89, 10]
    results = {}

    for psalm_num in test_psalms:
        results[psalm_num] = test_psalm(psalm_num, indexer)

    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)

    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)

    print(f"\nPassed: {success_count}/{total_count}")

    for psalm_num, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        stats = get_stats(psalm_num)
        print(f"  {status}: Psalm {psalm_num} - {stats['empty']} empty contexts ({stats['empty_pct']}%)")

    if success_count == total_count:
        print("\n✓ All fixes working correctly! Ready for full re-index.")
        return 0
    else:
        print(f"\n⚠ {total_count - success_count} Psalm(s) still have issues. Review code.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
