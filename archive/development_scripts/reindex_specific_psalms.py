#!/usr/bin/env python3
"""
Re-index specific Psalms in the liturgical database.

This script allows you to re-index specific Psalm chapters, overwriting
the old buggy data with newly indexed data using the fixed indexer.

Usage:
    python scripts/reindex_specific_psalms.py 1 145 148
    python scripts/reindex_specific_psalms.py --all  # Re-index all 150 Psalms
    python scripts/reindex_specific_psalms.py --range 1-10  # Re-index range

Created: 2025-10-30 (Session 48)
Purpose: Quick re-indexing of specific Psalms after indexer fixes
"""

import sys
import sqlite3
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.liturgy.liturgy_indexer import LiturgyIndexer


def check_empty_contexts(db_path: str = "data/liturgy.db") -> tuple:
    """
    Check how many matches have empty contexts.

    Returns:
        (empty_count, total_count, percentage)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM psalms_liturgy_index
        WHERE liturgy_context IS NULL OR liturgy_context = ''
    """)
    empty = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM psalms_liturgy_index")
    total = cursor.fetchone()[0]

    conn.close()

    percentage = (empty / total * 100) if total > 0 else 0
    return empty, total, percentage


def get_psalm_stats(psalm_chapter: int, db_path: str = "data/liturgy.db") -> dict:
    """Get statistics for a specific Psalm."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM psalms_liturgy_index
        WHERE psalm_chapter = ?
    """, (psalm_chapter,))
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM psalms_liturgy_index
        WHERE psalm_chapter = ? AND (liturgy_context IS NULL OR liturgy_context = '')
    """, (psalm_chapter,))
    empty = cursor.fetchone()[0]

    cursor.execute("""
        SELECT match_type, COUNT(*)
        FROM psalms_liturgy_index
        WHERE psalm_chapter = ?
        GROUP BY match_type
    """, (psalm_chapter,))
    by_type = dict(cursor.fetchall())

    conn.close()

    return {
        'total': total,
        'empty_contexts': empty,
        'by_type': by_type
    }


def reindex_psalms(psalm_chapters: list, liturgy_db: str = "data/liturgy.db",
                   tanakh_db: str = "database/tanakh.db", verbose: bool = True):
    """
    Re-index specific Psalms, overwriting old data.

    Args:
        psalm_chapters: List of Psalm numbers (1-150) to re-index
        liturgy_db: Path to liturgy database
        tanakh_db: Path to Tanakh database
        verbose: Print progress messages
    """
    # Sort and validate
    psalm_chapters = sorted(set(psalm_chapters))
    invalid = [p for p in psalm_chapters if p < 1 or p > 150]

    if invalid:
        print(f"Error: Invalid Psalm numbers: {invalid}")
        print("Psalm numbers must be between 1 and 150")
        return

    print("=" * 70)
    print(f"RE-INDEXING {len(psalm_chapters)} PSALMS")
    print("=" * 70)
    print(f"Psalms to re-index: {', '.join(map(str, psalm_chapters))}")
    print(f"Database: {liturgy_db}")
    print(f"Using Aho-Corasick optimization: YES")
    print()

    # Check initial state
    print("Database state BEFORE re-indexing:")
    empty, total, pct = check_empty_contexts(liturgy_db)
    print(f"  Total matches: {total:,}")
    print(f"  Empty contexts: {empty:,} ({pct:.1f}%)")
    print()

    # Create indexer
    indexer = LiturgyIndexer(
        liturgy_db=liturgy_db,
        tanakh_db=tanakh_db,
        verbose=verbose
    )

    # Re-index each Psalm
    results = []
    total_start_time = time.time()

    for i, psalm in enumerate(psalm_chapters, 1):
        print(f"\n{'=' * 70}")
        print(f"[{i}/{len(psalm_chapters)}] Re-indexing Psalm {psalm}")
        print(f"{'=' * 70}")

        # Get stats before
        before_stats = get_psalm_stats(psalm, liturgy_db)
        print(f"\nBEFORE:")
        print(f"  Total matches: {before_stats['total']}")
        print(f"  Empty contexts: {before_stats['empty_contexts']}")
        if before_stats['by_type']:
            print(f"  By type: {before_stats['by_type']}")

        # Index (this clears and re-indexes)
        start_time = time.time()

        try:
            result = indexer.index_psalm(psalm)
            elapsed = time.time() - start_time

            # Get stats after
            after_stats = get_psalm_stats(psalm, liturgy_db)

            print(f"\nAFTER:")
            print(f"  Total matches: {after_stats['total']}")
            print(f"  Empty contexts: {after_stats['empty_contexts']}")
            if after_stats['by_type']:
                print(f"  By type: {after_stats['by_type']}")

            print(f"\n✓ Completed in {elapsed:.1f} seconds")

            results.append({
                'psalm': psalm,
                'success': True,
                'time': elapsed,
                'before': before_stats,
                'after': after_stats
            })

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n✗ ERROR: {e}")
            print(f"Failed after {elapsed:.1f} seconds")

            results.append({
                'psalm': psalm,
                'success': False,
                'time': elapsed,
                'error': str(e)
            })

    # Summary
    total_elapsed = time.time() - total_start_time
    successful = [r for r in results if r['success']]

    print("\n" + "=" * 70)
    print("RE-INDEXING COMPLETE")
    print("=" * 70)
    print(f"Total time: {total_elapsed:.1f} seconds ({total_elapsed/60:.1f} minutes)")
    print(f"Successful: {len(successful)}/{len(psalm_chapters)} Psalms")

    if successful:
        avg_time = sum(r['time'] for r in successful) / len(successful)
        print(f"Average time per Psalm: {avg_time:.1f} seconds")

    # Check final state
    print("\nDatabase state AFTER re-indexing:")
    empty, total, pct = check_empty_contexts(liturgy_db)
    print(f"  Total matches: {total:,}")
    print(f"  Empty contexts: {empty:,} ({pct:.1f}%)")

    # Show improvements
    if successful:
        print("\nImprovements:")
        for r in successful:
            before_empty = r['before']['empty_contexts']
            after_empty = r['after']['empty_contexts']
            if before_empty > 0 or after_empty > 0:
                print(f"  Psalm {r['psalm']:3d}: {before_empty} → {after_empty} empty contexts")

    print()


def main():
    """Command-line interface."""
    import argparse

    # Configure UTF-8 output for Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Re-index specific Psalms in the liturgical database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Re-index Psalms 1, 145, and 148
  python scripts/reindex_specific_psalms.py 1 145 148

  # Re-index a range
  python scripts/reindex_specific_psalms.py --range 1-10

  # Re-index all 150 Psalms
  python scripts/reindex_specific_psalms.py --all

  # Check current database state
  python scripts/reindex_specific_psalms.py --stats
        """
    )

    parser.add_argument(
        'psalms',
        type=int,
        nargs='*',
        help='Psalm numbers to re-index (1-150)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Re-index all 150 Psalms'
    )
    parser.add_argument(
        '--range',
        type=str,
        help='Re-index a range of Psalms (e.g., "1-10")'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show current database statistics'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress detailed output'
    )
    parser.add_argument(
        '--liturgy-db',
        type=str,
        default='data/liturgy.db',
        help='Path to liturgy database (default: data/liturgy.db)'
    )
    parser.add_argument(
        '--tanakh-db',
        type=str,
        default='database/tanakh.db',
        help='Path to Tanakh database (default: database/tanakh.db)'
    )

    args = parser.parse_args()

    # Stats mode
    if args.stats:
        print("\n" + "=" * 70)
        print("DATABASE STATISTICS")
        print("=" * 70)

        empty, total, pct = check_empty_contexts(args.liturgy_db)
        print(f"Total matches: {total:,}")
        print(f"Empty contexts: {empty:,} ({pct:.1f}%)")

        conn = sqlite3.connect(args.liturgy_db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(DISTINCT psalm_chapter) FROM psalms_liturgy_index
        """)
        indexed = cursor.fetchone()[0]
        print(f"Psalms indexed: {indexed}/150")

        cursor.execute("""
            SELECT match_type, COUNT(*)
            FROM psalms_liturgy_index
            GROUP BY match_type
        """)
        by_type = dict(cursor.fetchall())
        print("\nBy match type:")
        for match_type, count in sorted(by_type.items()):
            print(f"  {match_type.replace('_', ' ').title()}: {count:,}")

        conn.close()
        print()
        return

    # Determine which Psalms to index
    psalm_list = []

    if args.all:
        psalm_list = list(range(1, 151))
    elif args.range:
        try:
            start, end = map(int, args.range.split('-'))
            if start < 1 or end > 150 or start > end:
                print("Error: Range must be between 1-150 and start <= end")
                return
            psalm_list = list(range(start, end + 1))
        except ValueError:
            print("Error: Range must be in format 'start-end' (e.g., '1-10')")
            return
    elif args.psalms:
        psalm_list = args.psalms
    else:
        parser.print_help()
        return

    # Confirm if many Psalms
    if len(psalm_list) > 10:
        confirm = input(f"\nRe-index {len(psalm_list)} Psalms? This may take a while. (y/N): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return

    # Re-index
    reindex_psalms(
        psalm_chapters=psalm_list,
        liturgy_db=args.liturgy_db,
        tanakh_db=args.tanakh_db,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()
