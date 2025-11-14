"""
Test V4.3 fixes for Psalms 6-38 example.

This script tests both fixes:
1. Full verse text in matches_from_a/b
2. Aggressive skipgram deduplication
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_scorer_skipgram_dedup_v4 import (
    load_shared_skipgrams_with_verses,
    filter_contiguous_contained_in_skipgrams,
    keep_best_skipgram_per_verse_pair
)

def main():
    print("=" * 70)
    print("Testing V4.3 Fixes on Psalms 6-38")
    print("=" * 70)

    # Load skipgrams
    db_path = Path(__file__).parent.parent.parent / "data" / "psalm_relationships.db"
    skipgrams = load_shared_skipgrams_with_verses(db_path, 6, 38)

    print(f"\nOriginal skipgrams loaded: {len(skipgrams)}")

    # Test Issue #2: Check if full verse text is present
    if skipgrams:
        first_sg = skipgrams[0]
        print(f"\n{'='*70}")
        print("TESTING ISSUE #2: Full Verse Text")
        print('='*70)
        print(f"Pattern: {first_sg['consonantal']}")
        print(f"Matched Hebrew: {first_sg['matched_hebrew']}")
        print(f"Full span Hebrew: {first_sg['full_span_hebrew']}")

        if first_sg.get('matches_from_a'):
            match_text = first_sg['matches_from_a'][0]['text']
            print(f"\nMatch text from Psalm 6:")
            print(f"  {match_text}")
            print(f"  Length: {len(match_text.split())} words")

            # Check if it's the full verse or just matched words
            matched_word_count = len(first_sg['matched_hebrew'].split())
            match_text_word_count = len(match_text.split())

            if match_text_word_count > matched_word_count:
                print(f"\n✓ ISSUE #2 FIXED: Match text has {match_text_word_count} words vs {matched_word_count} matched words")
                print("  (Full verse is being shown, not just matched words)")
            else:
                print(f"\n✗ ISSUE #2 NOT FIXED: Match text has same word count as matched words")
                print(f"  (Only showing matched words, not full verse)")

    # Test Issue #1: Apply aggressive deduplication
    print(f"\n{'='*70}")
    print("TESTING ISSUE #1: Aggressive Deduplication")
    print('='*70)

    # Apply per-verse deduplication
    deduped_skipgrams = keep_best_skipgram_per_verse_pair(skipgrams)
    print(f"\nAfter per-verse deduplication: {len(deduped_skipgrams)} skipgrams")
    print(f"Reduction: {len(skipgrams)} → {len(deduped_skipgrams)} ({100*(len(skipgrams)-len(deduped_skipgrams))/len(skipgrams):.1f}% reduction)")

    # Show remaining skipgrams
    print(f"\nRemaining skipgrams:")
    for i, sg in enumerate(deduped_skipgrams[:10], 1):
        verses_a = set(m['verse'] for m in sg.get('matches_from_a', []))
        verses_b = set(m['verse'] for m in sg.get('matches_from_b', []))
        print(f"  {i}. {sg['consonantal']} (len={sg['length']}, verses_a={sorted(verses_a)}, verses_b={sorted(verses_b)})")

    if len(deduped_skipgrams) <= 3:
        print(f"\n✓ ISSUE #1 FIXED: Only {len(deduped_skipgrams)} skipgrams remain (expected: 1-3)")
    else:
        print(f"\n⚠ ISSUE #1 PARTIALLY FIXED: {len(deduped_skipgrams)} skipgrams remain (expected: 1-3)")

    # Test contiguous phrase filtering
    print(f"\n{'='*70}")
    print("TESTING: Contiguous Phrase Filtering")
    print('='*70)

    # Create sample contiguous phrases matching the user's example
    sample_contiguous = [
        {'consonantal': 'אד כל', 'hebrew': 'test', 'length': 2},
        {'consonantal': 'זמור דוד', 'hebrew': 'test', 'length': 2},
        {'consonantal': 'יהו אל', 'hebrew': 'test', 'length': 2},
        {'consonantal': 'חמת תיסר', 'hebrew': 'test', 'length': 2}
    ]

    filtered_contiguous = filter_contiguous_contained_in_skipgrams(
        sample_contiguous,
        deduped_skipgrams
    )

    print(f"\nOriginal contiguous phrases: {len(sample_contiguous)}")
    for p in sample_contiguous:
        print(f"  - {p['consonantal']}")

    print(f"\nAfter filtering (removed if contained in skipgrams): {len(filtered_contiguous)}")
    for p in filtered_contiguous:
        print(f"  - {p['consonantal']}")

    removed_count = len(sample_contiguous) - len(filtered_contiguous)
    print(f"\nContiguous phrases removed: {removed_count}")

    if removed_count > 0:
        print(f"✓ Hierarchical deduplication working (removed {removed_count} contiguous phrases)")

    print(f"\n{'='*70}")
    print("Test complete!")
    print('='*70)

if __name__ == '__main__':
    main()
