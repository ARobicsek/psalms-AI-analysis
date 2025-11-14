"""
Test V4.2 Fixes for Skipgram Deduplication and Verse Text

Tests:
1. Overlapping skipgrams from same verse are properly deduplicated
2. matches_from_a/b show full verse text, not just matched words
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_scorer_skipgram_dedup_v4 import load_shared_skipgrams_with_verses

def test_psalms_6_38():
    """
    Test Psalms 6 & 38 which have overlapping skipgrams from verses 1-2.

    Example from user:
    - "יהו אל תוכיח תיסר" (from verse 2)
    - "יהו אל תוכיח כי" (from verse 2)
    - "זמור דוד תוכיח תיסר" (from verse 1)

    These should be deduplicated since they all overlap in the same verses.
    """
    db_path = Path(__file__).parent.parent.parent / "data" / "psalm_relationships.db"

    print("=" * 80)
    print("Testing V4.2 Fixes: Psalms 6 & 38")
    print("=" * 80)

    # Load shared skipgrams
    skipgrams = load_shared_skipgrams_with_verses(db_path, 6, 38)

    print(f"\nTotal shared skipgrams after deduplication: {len(skipgrams)}")

    # Group by verse to check for overlaps
    verse_patterns = {}
    for sg in skipgrams:
        for match in sg['matches_from_a']:
            verse = match['verse']
            if verse not in verse_patterns:
                verse_patterns[verse] = []
            verse_patterns[verse].append({
                'pattern': sg['consonantal'],
                'matched': sg['matched_hebrew'],
                'full_span': sg['full_span_hebrew'],
                'length': sg['length']
            })

    print("\n" + "=" * 80)
    print("DEDUPLICATION TEST: Patterns from verse 1 (both psalms)")
    print("=" * 80)

    if 1 in verse_patterns:
        patterns_v1 = verse_patterns[1]
        print(f"Found {len(patterns_v1)} patterns from verse 1:")
        for i, p in enumerate(patterns_v1[:10], 1):  # Show first 10
            print(f"\n  {i}. {p['pattern']} (length={p['length']})")
            print(f"     Matched: {p['matched']}")
            print(f"     Span: {p['full_span']}")

        if len(patterns_v1) > 10:
            print(f"\n  ... and {len(patterns_v1) - 10} more")

    print("\n" + "=" * 80)
    print("DEDUPLICATION TEST: Patterns from verse 2 (both psalms)")
    print("=" * 80)

    if 2 in verse_patterns:
        patterns_v2 = verse_patterns[2]
        print(f"Found {len(patterns_v2)} patterns from verse 2:")
        for i, p in enumerate(patterns_v2[:10], 1):  # Show first 10
            print(f"\n  {i}. {p['pattern']} (length={p['length']})")
            print(f"     Matched: {p['matched']}")
            print(f"     Span: {p['full_span']}")

        if len(patterns_v2) > 10:
            print(f"\n  ... and {len(patterns_v2) - 10} more")

    print("\n" + "=" * 80)
    print("VERSE TEXT TEST: Check if matches show full verse text")
    print("=" * 80)

    # Check a few skipgrams to see if they have full verse text
    for i, sg in enumerate(skipgrams[:3], 1):
        print(f"\n{i}. Pattern: {sg['consonantal']}")
        print(f"   Matched words: {sg['matched_hebrew']}")

        if sg['matches_from_a']:
            match_a = sg['matches_from_a'][0]
            print(f"\n   Psalm 6, verse {match_a['verse']}:")
            print(f"   Text: {match_a['text']}")

            # Check if text is longer than matched words (indicates full verse)
            matched_word_count = len(sg['matched_hebrew'].split())
            full_text_word_count = len(match_a['text'].split())

            if full_text_word_count > matched_word_count:
                print(f"   ✓ FULL VERSE TEXT (matched={matched_word_count} words, full={full_text_word_count} words)")
            else:
                print(f"   ✗ ONLY MATCHED WORDS (both={full_text_word_count} words)")

        if sg['matches_from_b']:
            match_b = sg['matches_from_b'][0]
            print(f"\n   Psalm 38, verse {match_b['verse']}:")
            print(f"   Text: {match_b['text']}")

            matched_word_count = len(sg['matched_hebrew'].split())
            full_text_word_count = len(match_b['text'].split())

            if full_text_word_count > matched_word_count:
                print(f"   ✓ FULL VERSE TEXT (matched={matched_word_count} words, full={full_text_word_count} words)")
            else:
                print(f"   ✗ ONLY MATCHED WORDS (both={full_text_word_count} words)")

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    # Count overlapping patterns
    total_patterns = sum(len(patterns) for patterns in verse_patterns.values())
    print(f"\nTotal skipgram patterns: {len(skipgrams)}")
    print(f"Total verse-pattern pairs: {total_patterns}")

    # Expected: much fewer patterns per verse after deduplication
    if 1 in verse_patterns and 2 in verse_patterns:
        print(f"\nPatterns from verse 1: {len(verse_patterns[1])}")
        print(f"Patterns from verse 2: {len(verse_patterns[2])}")

        # The user showed 8 overlapping patterns from these verses
        # After deduplication, we should have much fewer
        if len(verse_patterns[1]) <= 2 and len(verse_patterns[2]) <= 2:
            print("\n✓ DEDUPLICATION WORKING: Few patterns per verse (expected)")
        else:
            print(f"\n✗ POSSIBLE ISSUE: Still have {len(verse_patterns[1]) + len(verse_patterns[2])} patterns from verses 1-2")
            print("  (User reported 8 overlapping patterns that should have been deduplicated)")

    # Check verse text
    has_full_text = False
    for sg in skipgrams[:5]:
        if sg['matches_from_a']:
            matched_words = len(sg['matched_hebrew'].split())
            full_words = len(sg['matches_from_a'][0]['text'].split())
            if full_words > matched_words:
                has_full_text = True
                break

    if has_full_text:
        print("\n✓ VERSE TEXT WORKING: Showing full verse text (not just matched words)")
    else:
        print("\n✗ VERSE TEXT ISSUE: Still showing only matched words")


if __name__ == "__main__":
    test_psalms_6_38()
