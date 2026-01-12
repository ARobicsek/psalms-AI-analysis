"""
Re-index all 150 Psalms with corrected indexer.

This script clears existing corrupted data and rebuilds the entire
psalms_liturgy_index table with the fixed context extraction logic.
"""

import sys
import os

# Configure UTF-8 output for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.liturgy.liturgy_indexer import LiturgyIndexer
import time

if __name__ == "__main__":
    print("=" * 70)
    print("RE-INDEXING ALL 150 PSALMS")
    print("=" * 70)
    print()
    print("This will:")
    print("  1. Clear existing index for each Psalm")
    print("  2. Re-index with corrected context extraction")
    print("  3. Store matches with proper liturgy_context field")
    print()

    # Initialize indexer (verbose=False to avoid UTF-8 print issues)
    indexer = LiturgyIndexer(verbose=False)

    # Track statistics
    start_time = time.time()
    total_matches = 0
    failed_psalms = []

    # Index all 150 Psalms
    for psalm_num in range(1, 151):
        print(f"\n{'='*70}")
        print(f"PSALM {psalm_num}/150")
        print(f"{'='*70}")

        try:
            result = indexer.index_psalm(psalm_num)

            if 'error' in result:
                print(f"⚠ Error: {result['error']}")
                failed_psalms.append(psalm_num)
            else:
                matches = result.get('total_matches', 0)
                total_matches += matches
                print(f"✓ Indexed {matches} matches for Psalm {psalm_num}")

        except Exception as e:
            print(f"✗ Failed to index Psalm {psalm_num}: {e}")
            failed_psalms.append(psalm_num)

    # Print summary
    elapsed = time.time() - start_time

    print()
    print("=" * 70)
    print("RE-INDEXING COMPLETE")
    print("=" * 70)
    print(f"Total matches indexed: {total_matches:,}")
    print(f"Psalms processed: {150 - len(failed_psalms)}/150")
    print(f"Time elapsed: {elapsed/60:.1f} minutes")

    if failed_psalms:
        print(f"\n⚠ Failed psalms: {failed_psalms}")
    else:
        print("\n✓ All 150 Psalms indexed successfully!")
