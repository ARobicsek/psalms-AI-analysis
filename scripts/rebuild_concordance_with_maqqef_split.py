"""
Rebuild Concordance Index with Maqqef Splitting

This script rebuilds the entire concordance index, splitting on maqqef
BEFORE creating concordance rows. This ensures maqqef-connected morphemes
become separate searchable entries.

Expected changes:
- Word count will increase (maqqef-connected words → multiple rows)
- "כִּֽי־הִכִּ֣יתָ" becomes two rows: "כִּֽי" and "הִכִּ֣יתָ"
- Phrase searches will now find maqqef-separated morphemes

Expected time: 2-3 minutes for ~270K entries
"""

import sys
import os
import time
import logging

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
    print("=" * 70)
    print("REBUILD CONCORDANCE WITH MAQQEF SPLITTING")
    print("=" * 70)
    print()
    print("This will:")
    print("  1. Delete existing concordance index (~270K entries)")
    print("  2. Rebuild from scratch with maqqef splitting")
    print("  3. Create more entries (maqqef words → separate rows)")
    print()
    print("Root cause: Previous migration added split COLUMN but kept")
    print("            single rows. Need separate ROWS for searching.")
    print()
    print("Expected time: 2-3 minutes")
    print("Expected new entry count: ~300K+ (increase due to splitting)")
    print()

    # Ask for confirmation
    response = input("Continue with rebuild? (y/n): ").strip().lower()
    if response != 'y':
        print("Rebuild cancelled.")
        sys.exit(0)

    print()
    print("=" * 70)
    print("Starting rebuild...")
    print("=" * 70)
    print()

    start_time = time.time()

    try:
        # Initialize database
        db = TanakhDatabase()

        # Get current statistics
        print("Before rebuild:")
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM concordance")
        before_count = cursor.fetchone()['count']
        print(f"  Concordance entries: {before_count:,}")
        print()

        # Rebuild concordance
        print("Rebuilding concordance index...")
        print("  (This will split on maqqef BEFORE creating rows)")
        print()

        stats = db.build_concordance_index(force=True)

        print()
        print("After rebuild:")
        cursor.execute("SELECT COUNT(*) as count FROM concordance")
        after_count = cursor.fetchone()['count']
        print(f"  Concordance entries: {after_count:,}")
        print(f"  Change: +{after_count - before_count:,} entries")
        print()

        # Close database
        db.close()

        # Calculate elapsed time
        elapsed = time.time() - start_time

        print("=" * 70)
        print("REBUILD COMPLETE")
        print("=" * 70)
        print(f"Time elapsed: {elapsed/60:.2f} minutes")
        print(f"Verses processed: {stats['verses_processed']:,}")
        print(f"Words indexed: {stats['words_indexed']:,}")
        print()
        print("Next steps:")
        print("  1. Run test_split_column.py to verify split searching works")
        print("  2. Run test_concordance_baseline.py to verify improvements")
        print("     Expected: Queries should now return results!")
        print()
        print("✓ Concordance index rebuilt with maqqef splitting!")

    except Exception as e:
        print()
        print("=" * 70)
        print("REBUILD FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        print("The database may be in an inconsistent state.")
        print("You may need to rebuild from the original Tanakh download.")
        sys.exit(1)
