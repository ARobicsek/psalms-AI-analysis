#!/usr/bin/env python3
"""
Test Psalm 23 with lower similarity threshold to see what matches we get.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def main():
    # Hebrew text of Psalm 23:1-5
    psalm_23_1_5_hebrew = "מזמור לדוד יהוה רעי לא אחסר בנאות דשא ירביצני על מי מנחות ינהלני נפשי ישובב ינחני במעגלי צדק למען שמו גם כי אלך בגיא צלמות לא אירא רע כי אתה עמדי שבטך ומשענתך המה ינחמוני תערך לפני שלחן נגד צררי דשנת בשמן ראשי כוסי רויה"

    # Test with different thresholds
    thresholds = [0.7, 0.5, 0.3, 0.1]

    with open("psalm_23_threshold_test.txt", "w", encoding="utf-8") as f:
        f.write("PSALM 23 THRESHOLD TEST (HEBREW ONLY)\n")
        f.write("="*50 + "\n\n")
        f.write("Testing with different similarity thresholds:\n\n")

        for threshold in thresholds:
            f.write(f"Threshold: {threshold}\n")
            f.write("-"*30 + "\n")

            librarian = ThematicParallelsLibrarian(
                similarity_threshold=threshold,
                max_results=5
            )

            parallels = librarian.find_parallels(psalm_23_1_5_hebrew)

            f.write(f"Results found: {len(parallels)}\n\n")

            if parallels:
                for i, p in enumerate(parallels, 1):
                    f.write(f"  {i}. {p.reference}\n")
                    f.write(f"     Similarity: {p.similarity:.6f}\n")
                    if "Psalm 23" in p.reference:
                        f.write(f"     *** THIS IS PSALM 23 ***\n")
                    f.write("\n")
            else:
                f.write("  No results\n\n")

            f.write("\n")

    # Also try with just the first verse to see what happens
    psalm_23_1_hebrew = "יהוה רעי לא אחסר"
    librarian_low = ThematicParallelsLibrarian(similarity_threshold=0.3, max_results=5)
    parallels_verse = librarian_low.find_parallels(psalm_23_1_hebrew)

    with open("psalm_23_threshold_test.txt", "a", encoding="utf-8") as f:
        f.write("SINGLE VERSE TEST (Psalm 23:1 only)\n")
        f.write("-"*30 + "\n")
        f.write(f"Query: {psalm_23_1_hebrew}\n")
        f.write(f"Results: {len(parallels_verse)}\n\n")

        if parallels_verse:
            for i, p in enumerate(parallels_verse, 1):
                f.write(f"  {i}. {p.reference}\n")
                f.write(f"     Similarity: {p.similarity:.6f}\n")
                if "Psalm 23" in p.reference:
                    f.write(f"     *** THIS IS PSALM 23 ***\n")

    print("Test complete. Results saved to psalm_23_threshold_test.txt")


if __name__ == "__main__":
    main()