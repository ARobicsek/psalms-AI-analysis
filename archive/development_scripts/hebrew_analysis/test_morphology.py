"""
Proof of Concept: Test Hebrew Morphological Analysis

Tests the new morphology system against the false positive examples from V2.

Expected Results:
- "מָחִיתָ" (machita, "you destroyed") → root "מחה"
- "חַיִּים" (chayim, "life") → root "חיה"
- These should be DIFFERENT roots (V2 incorrectly matched both to "חי")

Run with: python test_morphology.py
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hebrew_analysis.morphology import HebrewMorphologyAnalyzer


def test_false_positive_examples():
    """
    Test the false positive examples from V2 to verify they're now correctly distinguished.
    """
    print("Hebrew Morphological Analysis - Proof of Concept")
    print("=" * 80)
    
    analyzer = HebrewMorphologyAnalyzer()
    
    # Display cache status
    stats = analyzer.get_cache_stats()
    print(f"\nCache Status:")
    print(f"  Loaded: {stats['cache_loaded']}")
    print(f"  Size: {stats['cache_size']} entries")
    print(f"  Path: {stats['cache_path']}")
    
    if not stats['cache_loaded']:
        print("\n⚠ WARNING: Cache not loaded!")
        print("  Results will use fallback extraction only.")
        print("  To build cache: python cache_builder.py")
    
    print("\n" + "=" * 80)
    print("FALSE POSITIVE TEST CASES")
    print("=" * 80)
    
    # Test Case 1: מחה vs חיה
    print("\n1. Test Case: מחה vs חיה (destroy vs live)")
    print("-" * 80)
    
    word1 = "מָחִיתָ"  # machita - "you destroyed" from root מחה
    word2 = "חַיִּים"  # chayim - "life" from root חיה
    
    root1 = analyzer.extract_root(word1)
    root2 = analyzer.extract_root(word2)
    
    print(f"Word 1: {word1:15} (machita, 'you destroyed')")
    print(f"  V3 Root: {root1}")
    print()
    print(f"Word 2: {word2:15} (chayim, 'life')")
    print(f"  V3 Root: {root2}")
    print()
    
    if root1 == root2:
        print(f"❌ FAIL: Both words extracted to same root '{root1}'")
        print("   (This is the V2 false positive problem)")
        test1_pass = False
    else:
        print(f"✅ PASS: Different roots extracted ('{root1}' vs '{root2}')")
        test1_pass = True
    
    # Test Case 2: לב vs ב+בית
    print("\n2. Test Case: לב vs ב+בית (heart vs in+house)")
    print("-" * 80)
    
    word3 = "לִבִּי"   # libi - "my heart" from root לב
    word4 = "בְּבֵית"  # b'veit - "in house" = preposition ב + בית
    
    root3 = analyzer.extract_root(word3)
    root4 = analyzer.extract_root(word4)
    
    print(f"Word 3: {word3:15} (libi, 'my heart')")
    print(f"  V3 Root: {root3}")
    print()
    print(f"Word 4: {word4:15} (b'veit, 'in house')")
    print(f"  V3 Root: {root4}")
    print()
    
    if root3 == root4:
        print(f"❌ FAIL: Both words extracted to same root '{root3}'")
        test2_pass = False
    else:
        print(f"✅ PASS: Different roots extracted ('{root3}' vs '{root4}')")
        test2_pass = True
    
    # Test Case 3: מאד vs אדן
    print("\n3. Test Case: מאד vs אדן (very vs Lord)")
    print("-" * 80)
    
    word5 = "מְאֹד"    # me'od - "very/much"
    word6 = "אֲדֹנָי"  # Adonai - "Lord" from root אדן
    
    root5 = analyzer.extract_root(word5)
    root6 = analyzer.extract_root(word6)
    
    print(f"Word 5: {word5:15} (me'od, 'very')")
    print(f"  V3 Root: {root5}")
    print()
    print(f"Word 6: {word6:15} (Adonai, 'Lord')")
    print(f"  V3 Root: {root6}")
    print()
    
    if root5 == root6:
        print(f"❌ FAIL: Both words extracted to same root '{root5}'")
        test3_pass = False
    else:
        print(f"✅ PASS: Different roots extracted ('{root5}' vs '{root6}')")
        test3_pass = True
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_tests = 3
    passed_tests = sum([test1_pass, test2_pass, test3_pass])
    
    print(f"\nTests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("   V3 morphological analysis successfully distinguishes false positives.")
        return True
    else:
        print(f"\n⚠ {total_tests - passed_tests} TEST(S) FAILED")
        if not stats['cache_loaded']:
            print("   Note: Cache was not loaded. Build cache for better results.")
        else:
            print("   Some false positives may still exist.")
        return False


def show_improvement_examples():
    """
    Show additional examples of improved root extraction.
    """
    print("\n" + "=" * 80)
    print("ADDITIONAL EXAMPLES")
    print("=" * 80)
    
    analyzer = HebrewMorphologyAnalyzer()
    
    examples = [
        ("יְהוָה", "YHWH", "the Name"),
        ("אֱלֹהִים", "Elohim", "God"),
        ("דָּוִד", "David", "David"),
        ("יְרוּשָׁלִַם", "Yerushalayim", "Jerusalem"),
        ("שָׁמַיִם", "shamayim", "heaven"),
        ("אָרֶץ", "aretz", "earth"),
        ("מֶלֶךְ", "melekh", "king"),
        ("נֶפֶשׁ", "nefesh", "soul"),
    ]
    
    print("\nCommon Biblical Hebrew words:")
    print("-" * 80)
    
    for hebrew, transliteration, meaning in examples:
        root = analyzer.extract_root(hebrew)
        print(f"{hebrew:15} ({transliteration:15}) '{meaning:15}' → {root}")
    
    print("=" * 80)


if __name__ == '__main__':
    # Run tests
    success = test_false_positive_examples()
    
    # Show additional examples
    show_improvement_examples()
    
    # Exit code
    sys.exit(0 if success else 1)
