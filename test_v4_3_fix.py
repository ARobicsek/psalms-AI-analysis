#!/usr/bin/env python3
"""
Test V4.3 cross-match-type deduplication fix.

Tests that contiguous phrases are removed when they're subsequences of skipgrams.
"""

import json
import sys
sys.path.insert(0, 'scripts/statistical_analysis')

from enhanced_scorer_skipgram_dedup_v4 import deduplicate_across_match_types

def test_psalms_6_38_example():
    """Test the actual example from user's report."""

    # Contiguous phrases from Psalms 6-38
    contiguous_phrases = [
        {
            "consonantal": "זמור דוד",
            "hebrew": "מִזְמ֥וֹר לְדָוִֽד׃",
            "length": 2
        },
        {
            "consonantal": "יהו אל",
            "hebrew": "יְֽהֹוָ֗ה אַל",
            "length": 2
        },
        {
            "consonantal": "חמת תיסר",
            "hebrew": "בַּחֲמָתְךָ֥ תְיַסְּרֵֽנִי׃",
            "length": 2
        }
    ]

    # Skipgrams from Psalms 6-38
    skipgrams = [
        {
            "consonantal": "זמור דוד יהו תיסר",
            "matched_hebrew": "מִזְמ֥וֹר לְדָוִֽד׃ יְֽהֹוָ֗ה תְיַסְּרֵֽנִי׃",
            "length": 4
        },
        {
            "consonantal": "יהו אל תוכיח כי",
            "matched_hebrew": "יְֽהֹוָ֗ה אַל תוֹכִיחֵ֑נִי כִּ֤י",
            "length": 4
        }
    ]

    print("=" * 70)
    print("V4.3 Cross-Match-Type Deduplication Test")
    print("=" * 70)

    print("\nBEFORE deduplication:")
    print(f"  Contiguous phrases: {len(contiguous_phrases)}")
    for p in contiguous_phrases:
        print(f"    - {p['consonantal']} ({p['length']} words)")

    print(f"  Skipgrams: {len(skipgrams)}")
    for s in skipgrams:
        print(f"    - {s['consonantal']} ({s['length']} words)")

    # Apply V4.3 deduplication
    dedup_contiguous, dedup_skipgrams = deduplicate_across_match_types(
        contiguous_phrases,
        skipgrams
    )

    print("\nAFTER V4.3 deduplication:")
    print(f"  Contiguous phrases: {len(dedup_contiguous)}")
    for p in dedup_contiguous:
        print(f"    - {p['consonantal']} ({p['length']} words)")

    print(f"  Skipgrams: {len(dedup_skipgrams)}")
    for s in dedup_skipgrams:
        print(f"    - {s['consonantal']} ({s['length']} words)")

    print("\n" + "=" * 70)
    print("Expected Results:")
    print("=" * 70)
    print("  'זמור דוד' should be REMOVED (contained in 'זמור דוד יהו תיסר')")
    print("  'יהו אל' should be REMOVED (contained in 'יהו אל תוכיח כי')")
    print("  'חמת תיסר' should be KEPT (not in any skipgram)")
    print("  Both skipgrams should be KEPT")

    print("\n" + "=" * 70)
    print("Verification:")
    print("=" * 70)

    # Check expected results
    contiguous_patterns = {p['consonantal'] for p in dedup_contiguous}
    skipgram_patterns = {s['consonantal'] for s in dedup_skipgrams}

    success = True

    if "זמור דוד" in contiguous_patterns:
        print("  ❌ FAIL: 'זמור דוד' should have been removed")
        success = False
    else:
        print("  ✅ PASS: 'זמור דוד' correctly removed")

    if "יהו אל" in contiguous_patterns:
        print("  ❌ FAIL: 'יהו אל' should have been removed")
        success = False
    else:
        print("  ✅ PASS: 'יהו אל' correctly removed")

    if "חמת תיסר" not in contiguous_patterns:
        print("  ❌ FAIL: 'חמת תיסר' should have been kept")
        success = False
    else:
        print("  ✅ PASS: 'חמת תיסר' correctly kept")

    if len(dedup_skipgrams) != 2:
        print(f"  ❌ FAIL: Expected 2 skipgrams, got {len(dedup_skipgrams)}")
        success = False
    else:
        print("  ✅ PASS: Both skipgrams correctly kept")

    print("\n" + "=" * 70)
    if success:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 70)

    return success

if __name__ == "__main__":
    success = test_psalms_6_38_example()
    sys.exit(0 if success else 1)
