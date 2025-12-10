#!/usr/bin/env python3
"""
Verify Psalm 23 appears as #1 match for its verses.
Results saved to file with corrected checking logic.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def main():
    # Create librarian with lower threshold
    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.3,
        max_results=10
    )

    # Test verses
    tests = [
        ("Psalm 23:1", "יהוה רעי לא אחסר", "The LORD is my shepherd; I shall not want"),
        ("Psalm 23:2", "בנאות דשא ירביצני", "He maketh me to lie down in green pastures"),
        ("Psalm 23:4", "גם כי אלך בגיא צלמות", "Yea though I walk through the valley of the shadow of death"),
        ("Psalm 23:5", "תערך לפני שלחן נגד צררי", "Thou preparest a table before me in the presence of mine enemies"),
        ("Psalm 23:6", "אך טוב וחסד ירדפוני", "Surely goodness and mercy shall follow me")
    ]

    results = []

    print("Running Psalm 23 self-reference verification...")
    print("="*50)

    for ref, hebrew, english in tests:
        query = f"{hebrew} {english}"
        parallels = librarian.find_parallels(query)

        # Check if top result is from Psalm 23 (either "Psalm 23" or "Psalms 23")
        is_psalm_23_top = False
        if parallels:
            top_ref = parallels[0].reference
            is_psalm_23_top = "Psalm 23" in top_ref or "Psalms 23" in top_ref

        similarity = parallels[0].similarity if parallels else 0
        top_match = parallels[0].reference if parallels else "None"

        results.append({
            "reference": ref,
            "is_psalm_23_top": is_psalm_23_top,
            "similarity": similarity,
            "top_match": top_match
        })

        # Print progress
        status = "PASS ✓" if is_psalm_23_top else "FAIL ✗"
        print(f"{ref}: {status} - {top_match} (similarity: {similarity:.4f})")

    # Save detailed results to file
    with open("psalm_23_verification_final.txt", "w", encoding="utf-8") as f:
        f.write("PSALM 23 SELF-REFERENCE VERIFICATION RESULTS (FINAL)\n")
        f.write("="*50 + "\n\n")
        f.write(f"Vector store stats: {librarian.vector_store.count()} chunks\n")
        f.write(f"Similarity threshold: {librarian.similarity_threshold}\n")
        f.write(f"Max results: {librarian.max_results}\n\n")

        f.write("DETAILED RESULTS:\n")
        f.write("-"*50 + "\n\n")

        for result in results:
            f.write(f"Test Verse: {result['reference']}\n")
            f.write(f"Result: {'PASS - Psalm 23 is #1 match!' if result['is_psalm_23_top'] else 'FAIL - Psalm 23 is not #1 match'}\n")
            f.write(f"Top Match: {result['top_match']}\n")
            f.write(f"Similarity: {result['similarity:.4f}\n\n")

        # Summary
        all_passed = all(r['is_psalm_23_top'] for r in results)
        f.write("="*50 + "\n")
        f.write(f"OVERALL RESULT: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}\n")
        f.write(f"Tests Passed: {sum(1 for r in results if r['is_psalm_23_top'])}/{len(results)}\n")

    print("\nDetailed results saved to psalm_23_verification_final.txt")


if __name__ == "__main__":
    main()