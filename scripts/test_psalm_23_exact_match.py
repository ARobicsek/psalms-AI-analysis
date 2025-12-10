#!/usr/bin/env python3
"""
Test Psalm 23 by searching with the exact Hebrew text from its chunks.
This should return similarity ~1.0 for exact matches.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def main():
    # The actual Hebrew text of Psalm 23 (verses 1-5) - NO ENGLISH
    # This should match the chunk in the corpus exactly
    psalm_23_1_5_hebrew = "מזמור לדוד יהוה רעי לא אחסר בנאות דשא ירביצני על מי מנחות ינהלני נפשי ישובב ינחני במעגלי צדק למען שמו גם כי אלך בגיא צלמות לא אירא רע כי אתה עמדי שבטך ומשענתך המה ינחמוני תערך לפני שלחן נגד צררי דשנת בשמן ראשי כוסי רויה"

    print("PSALM 23 EXACT MATCH TEST (HEBREW ONLY)")
    print("="*50)
    print("\nSearching with HEBREW-ONLY text of Psalm 23:1-5")
    print("\nHebrew text:")
    print(psalm_23_1_5_hebrew[:100] + "...")
    print("\nNOTE: Using only Hebrew text because the corpus is Hebrew-only!")

    # Create librarian with high similarity threshold
    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.9,  # Only show very close matches
        max_results=5
    )

    # Search with the exact Hebrew text
    print("\n\nSEARCHING...")
    parallels = librarian.find_parallels(psalm_23_1_5_hebrew)

    print(f"\nFound {len(parallels)} results with similarity >= 0.9\n")

    if parallels:
        print("RESULTS:")
        print("-" * 50)

        for i, parallel in enumerate(parallels, 1):
            print(f"\n{i}. {parallel.reference}")
            print(f"   Similarity: {parallel.similarity:.6f}")
            print(f"   Book: {parallel.book}")
            print(f"   Context verses: {parallel.context_verses}")

            if "Psalm 23" in parallel.reference:
                print("   *** THIS IS PSALM 23! ***")

            # Check if this is essentially a perfect match
            if parallel.similarity > 0.999:
                print("   ✅ PERFECT MATCH (>0.999)")
            elif parallel.similarity > 0.99:
                print("   ⚠️  VERY HIGH SIMILARITY (>0.99) - should be 1.0 for exact match?")
            else:
                print(f"   ⚠️  Lower than expected similarity ({parallel.similarity:.6f})")

        # Check if Psalm 23 is #1
        top_is_psalm_23 = "Psalm 23" in parallels[0].reference
        print("\n" + "="*50)
        if top_is_psalm_23 and parallels[0].similarity > 0.999:
            print("✅ SUCCESS: Psalm 23 is #1 with near-perfect similarity!")
        elif top_is_psalm_23:
            print(f"⚠️  Psalm 23 is #1 but similarity is {parallels[0].similarity:.6f} (should be ~1.0)")
        else:
            print("❌ FAILED: Psalm 23 is not the top result")
    else:
        print("❌ ERROR: No results found with similarity >= 0.9")
        print("\nTrying with lower threshold...")

        # Try with lower threshold to see what we get
        librarian_low = ThematicParallelsLibrarian(similarity_threshold=0.5, max_results=5)
        parallels_low = librarian_low.find_parallels(psalm_23_1_5_hebrew)

        if parallels_low:
            print(f"\nResults with threshold 0.5:")
            for i, p in enumerate(parallels_low[:3], 1):
                print(f"  {i}. {p.reference} - similarity: {p.similarity:.6f}")


if __name__ == "__main__":
    main()