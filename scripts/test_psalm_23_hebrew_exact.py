#!/usr/bin/env python3
"""
Test Psalm 23 exact match with Hebrew-only text.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def main():
    # Hebrew text of Psalm 23:1-5 (exact)
    psalm_23_1_5_hebrew = "מזמור לדוד יהוה רעי לא אחסר בנאות דשא ירביצני על מי מנחות ינהלני נפשי ישובב ינחני במעגלי צדק למען שמו גם כי אלך בגיא צלמות לא אירא רע כי אתה עמדי שבטך ומשענתך המה ינחמוני תערך לפני שלחן נגד צררי דשנת בשמן ראשי כוסי רויה"

    # Create librarian with high threshold
    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.9,
        max_results=5
    )

    # Search with exact Hebrew text
    parallels = librarian.find_parallels(psalm_23_1_5_hebrew)

    # Output results to file
    with open("psalm_23_exact_match_results.txt", "w", encoding="utf-8") as f:
        f.write("PSALM 23 EXACT MATCH TEST (HEBREW ONLY)\n")
        f.write("="*50 + "\n\n")
        f.write("Query text: [Hebrew text of Psalm 23:1-5]\n")
        f.write(f"Length: {len(psalm_23_1_5_hebrew)} characters\n\n")
        f.write(f"Results found: {len(parallels)}\n\n")

        if parallels:
            for i, p in enumerate(parallels, 1):
                f.write(f"{i}. {p.reference}\n")
                f.write(f"   Similarity: {p.similarity:.6f}\n")
                f.write(f"   Book: {p.book}\n")

                if "Psalm 23" in p.reference:
                    f.write("   *** THIS IS PSALM 23 ***\n")

                if p.similarity > 0.999:
                    f.write("   ✅ PERFECT MATCH (>0.999)\n")
                else:
                    f.write(f"   ⚠️ Similarity: {p.similarity:.6f} (should be ~1.0 for exact match)\n")
                f.write("\n")

            # Summary
            f.write("SUMMARY:\n")
            f.write("-"*30 + "\n")
            if parallels and "Psalm 23" in parallels[0].reference:
                if parallels[0].similarity > 0.999:
                    f.write("✅ PASS: Psalm 23 is #1 with perfect similarity!\n")
                else:
                    f.write(f"⚠️ PARTIAL: Psalm 23 is #1 but similarity is {parallels[0].similarity:.6f}\n")
            else:
                f.write("❌ FAIL: Psalm 23 is not the top result\n")

    # Simple console output
    print("Test complete. Results saved to psalm_23_exact_match_results.txt")
    if parallels:
        print(f"Top result: {parallels[0].reference} with similarity {parallels[0].similarity:.6f}")


if __name__ == "__main__":
    main()