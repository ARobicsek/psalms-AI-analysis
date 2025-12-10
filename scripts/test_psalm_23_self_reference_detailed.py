#!/usr/bin/env python3
"""
Detailed test to confirm Psalm 23 appears as #1 match for its verses.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def main():
    # Create librarian with lower threshold to get more results
    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.3,
        max_results=10
    )

    # Test all major verses of Psalm 23
    test_cases = [
        {
            "reference": "Psalm 23:1",
            "hebrew": "יהוה רעי לא אחסר",
            "english": "The LORD is my shepherd; I shall not want"
        },
        {
            "reference": "Psalm 23:2",
            "hebrew": "בנאות דשא ירביצני",
            "english": "He maketh me to lie down in green pastures"
        },
        {
            "reference": "Psalm 23:4",
            "hebrew": "גם כי אלך בגיא צלמות",
            "english": "Yea, though I walk through the valley of the shadow of death"
        },
        {
            "reference": "Psalm 23:5",
            "hebrew": "תערך לפני שלחן נגד צררי",
            "english": "Thou preparest a table before me in the presence of mine enemies"
        }
    ]

    print("="*80)
    print("PSALM 23 SELF-REFERENCE TEST")
    print("="*80)
    print("\nTesting whether Psalm 23 appears as #1 match for its own verses")
    print("WITHOUT filtering out original verses\n")

    all_passed = True

    for test in test_cases:
        print(f"\n{'-'*60}")
        print(f"TESTING: {test['reference']}")
        print(f"{'-'*60}")
        print(f"Hebrew: {test['hebrew']}")
        print(f"English: {test['english']}\n")

        # Create query
        query = f"{test['hebrew']} {test['english']}"

        # Find parallels WITHOUT passing query_verses (no filtering)
        parallels = librarian.find_parallels(query)

        # Check if first result contains Psalm 23
        is_number_one = parallels and "Psalm 23" in parallels[0].reference

        print(f"Results (showing top 5):")
        for i, parallel in enumerate(parallels[:5], 1):
            # Check if this is a Psalm 23 reference
            is_psalm_23 = "Psalm 23" in parallel.reference
            marker = " ← #1 MATCH!" if i == 1 and is_psalm_23 else " ← PSALM 23" if is_psalm_23 else ""

            print(f"  {i}. {parallel.reference} (similarity: {parallel.similarity:.4f}){marker}")

        print(f"\nRESULT for {test['reference']}:")
        if is_number_one:
            print(f"  ✓ PASS - Psalm 23 is #1 with similarity {parallels[0].similarity:.4f}")
        else:
            print(f"  ✗ FAIL - Psalm 23 is not #1")
            all_passed = False

    print(f"\n{'='*80}")
    if all_passed:
        print("OVERALL RESULT: ✓ ALL TESTS PASSED")
        print("Psalm 23 appears as #1 match for all tested verses")
    else:
        print("OVERALL RESULT: ✗ SOME TESTS FAILED")
    print("="*80)


if __name__ == "__main__":
    main()