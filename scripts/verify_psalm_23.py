#!/usr/bin/env python3
"""
Verify Psalm 23 appears as #1 match for its verses.
Results saved to file.
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
        ("Psalm 23:4", "גם כי אלך בגיא צלמות", "Yea though I walk through the valley of the shadow of death"),
        ("Psalm 23:5", "תערך לפני שלחן נגד צררי", "Thou preparest a table before me in the presence of mine enemies")
    ]

    results = []

    for ref, hebrew, english in tests:
        query = f"{hebrew} {english}"
        parallels = librarian.find_parallels(query)

        is_number_one = parallels and "Psalm 23" in parallels[0].reference
        similarity = parallels[0].similarity if parallels else 0

        results.append({
            "reference": ref,
            "is_number_one": is_number_one,
            "similarity": similarity,
            "top_match": parallels[0].reference if parallels else "None"
        })

    # Save results to file
    with open("psalm_23_verification.txt", "w", encoding="utf-8") as f:
        f.write("PSALM 23 SELF-REFERENCE VERIFICATION RESULTS\n")
        f.write("="*50 + "\n\n")

        for result in results:
            f.write(f"{result['reference']}: ")
            f.write(f"{'PASS' if result['is_number_one'] else 'FAIL'}\n")
            f.write(f"  Top match: {result['top_match']}\n")
            f.write(f"  Similarity: {result['similarity']:.4f}\n\n")

    print("Verification complete. Results saved to psalm_23_verification.txt")


if __name__ == "__main__":
    main()