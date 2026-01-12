"""
Migration Script: Add Maqqef-Split Concordance Column

This script adds a new column word_consonantal_split to the concordance table
and populates it with maqqef-split normalized text.

Root Cause: System was stripping maqqef (־) but not splitting on it,
creating unsearchable combined words like כיהכית (ki-hikita combined).

Solution: Add new column where maqqef is replaced with space BEFORE
normalization, allowing individual morphemes to be searched.

Expected time: 2-5 minutes for ~270K entries
"""

import sys
import os
import time
import logging
import argparse

# Configure UTF-8 output for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_sources.tanakh_database import TanakhDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Migrate concordance to add maqqef-split column')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Skip confirmation prompt')
    args = parser.parse_args()

    print("=" * 70)
    print("MAQQEF-SPLIT CONCORDANCE MIGRATION")
    print("=" * 70)
    print()
    print("This migration will:")
    print("  1. Add word_consonantal_split column to concordance table")
    print("  2. Populate ~270K entries with maqqef-split normalized text")
    print("  3. Create index for fast searching")
    print()
    print("Root cause: Maqqef (־) was being stripped but not split,")
    print("            creating unsearchable combined words.")
    print()
    print("Solution:   Replace maqqef with space BEFORE normalization,")
    print("            making individual morphemes searchable.")
    print()
    print("Expected time: 2-5 minutes")
    print()

    # Ask for confirmation unless --yes flag provided
    if not args.yes:
        response = input("Continue with migration? (y/n): ").strip().lower()
        if response != 'y':
            print("Migration cancelled.")
            sys.exit(0)

    print()
    print("=" * 70)
    print("Starting migration...")
    print("=" * 70)
    print()

    start_time = time.time()

    try:
        # Initialize database
        db = TanakhDatabase()

        # Get current statistics
        stats = db.get_statistics()
        print(f"Database statistics:")
        print(f"  Concordance entries: {stats['concordance_words']:,}")
        print()

        # Step 1: Add column
        print("Step 1: Adding word_consonantal_split column...")
        column_added = db.add_split_concordance_column()
        if column_added:
            print("✓ Column added successfully with index")
        else:
            print("✓ Column already exists, proceeding to population")
        print()

        # Step 2: Populate column
        print("Step 2: Populating word_consonantal_split column...")
        print("  (Processing in batches of 1000, progress updates every 10K)")
        print()

        pop_stats = db.populate_split_concordance()

        print()
        print("✓ Population complete!")
        print(f"  Entries processed: {pop_stats['entries_processed']:,}")
        print(f"  Entries updated: {pop_stats['entries_updated']:,}")

        if pop_stats['failed_entries']:
            print(f"  ⚠ Failed entries: {len(pop_stats['failed_entries'])}")

        # Close database
        db.close()

        # Calculate elapsed time
        elapsed = time.time() - start_time

        print()
        print("=" * 70)
        print("MIGRATION COMPLETE")
        print("=" * 70)
        print(f"Time elapsed: {elapsed/60:.2f} minutes")
        print()
        print("Next steps:")
        print("  1. Update search.py to use word_consonantal_split column")
        print("  2. Update concordance_librarian.py with use_split flag")
        print("  3. Run baseline test to verify improvements")
        print("     python test_concordance_baseline.py")
        print()
        print("✓ Concordance system ready for testing!")

    except Exception as e:
        print()
        print("=" * 70)
        print("MIGRATION FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        print("The database should be unchanged (transaction rollback).")
        print("Please investigate the error and try again.")
        sys.exit(1)
