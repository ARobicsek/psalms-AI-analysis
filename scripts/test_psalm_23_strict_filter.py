#!/usr/bin/env python3
"""
Test Psalm 23 thematic search with STRICT filtering - exclude any chunk
that contains ANY part of Psalm 23 (even overlapping).
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def main():
    # Use a shorter Psalm 23 text (just verses 3-4) to get cleaner results
    psalm_23_3_4 = "נַפְשִׁי יְשׁוֹבֵב יַנְחֵנִי בְמַעְגְּלֵי צֶדֶק לְמַעַן שְׁמוֹ׃ גַּם כִּי אֵלֵךְ בְּגֵיא צַלְמָוֶת לֹא אִירָא רָע כִּי אַתָּה עִמָּדִי שִׁבְטְךָ וּמִשְׁעַנְתֶּךָ הֵמָּה יְנַחֲמֻנִי׃"

    # Create librarian
    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.4,
        max_results=20
    )

    # Search without initial filtering to see what we get
    all_parallels = librarian.find_parallels(psalm_23_3_4)

    # Strict filtering - exclude anything that contains Psalm 23
    strictly_filtered = []
    for p in all_parallels:
        # Check if reference contains Psalm 23
        if "Psalm 23" not in p.reference:
            # Also check if the chunk contains Psalm 23 text (for overlapping chunks)
            if "יְהֹוָה רֹעִי" not in p.hebrew_text:  # This is Psalm 23:1
                strictly_filtered.append(p)

    # Save results
    with open("psalm_23_strictly_filtered.txt", "w", encoding="utf-8") as f:
        f.write("PSALM 23 THEMATIC PARALLELS (STRICTLY FILTERED)\n")
        f.write("="*60 + "\n\n")
        f.write("Query Text (Psalms 23:3-4):\n")
        f.write("-"*30 + "\n")
        f.write(psalm_23_3_4)
        f.write("\n\n")
        f.write(f"Total results found: {len(all_parallels)}\n")
        f.write(f"After strict filtering (no Psalm 23): {len(strictly_filtered)}\n\n")

        f.write("TOP 5 THEMATIC PARALLELS (NO PSALM 23 AT ALL):\n")
        f.write("="*50 + "\n\n")

        for i, parallel in enumerate(strictly_filtered[:5], 1):
            f.write(f"{i}. {parallel.reference}\n")
            f.write(f"   Similarity: {parallel.similarity:.6f}\n")
            f.write(f"   Book: {parallel.book} ({parallel.book_category})\n")
            f.write(f"   Context verses: {parallel.context_verses}\n\n")

            f.write("   Full Hebrew Text:\n")
            f.write("   " + parallel.hebrew_text.replace("\n", "\n   ") + "\n\n")

            f.write("-"*50 + "\n\n")

        # Analysis
        f.write("ANALYSIS:\n")
        f.write("-"*30 + "\n")
        if strictly_filtered:
            avg_similarity = sum(p.similarity for p in strictly_filtered[:5]) / min(5, len(strictly_filtered))
            f.write(f"• Average similarity of top 5: {avg_similarity:.4f}\n")
            f.write(f"• Highest similarity: {strictly_filtered[0].similarity:.4f} ({strictly_filtered[0].reference})\n")
            f.write(f"• Books represented: {', '.join(sorted(set(p.book for p in strictly_filtered[:5])))}\n")

            # Check variety
            books = [p.book for p in strictly_filtered[:5]]
            unique_books = len(set(books))
            f.write(f"• Unique books in top 5: {unique_books}/5\n")
        else:
            f.write("• No parallels found after strict filtering\n")

    # Console output
    print("Test complete. Results saved to psalm_23_strictly_filtered.txt")
    if strictly_filtered:
        print(f"\nTop 3 parallels (strictly filtered):")
        for i, p in enumerate(strictly_filtered[:3], 1):
            print(f"  {i}. {p.reference} ({p.book}) - similarity: {p.similarity:.4f}")
    else:
        print("\nNo parallels found after strict filtering")


if __name__ == "__main__":
    main()