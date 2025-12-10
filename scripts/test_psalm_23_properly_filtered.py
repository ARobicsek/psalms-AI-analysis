#!/usr/bin/env python3
"""
Test Psalm 23 thematic search with proper filtering.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def main():
    # Psalm 23 text (verses 3-5) for better thematic content
    psalm_23_text = "נַפְשִׁי יְשׁוֹבֵב יַנְחֵנִי בְמַעְגְּלֵי צֶדֶק לְמַעַן שְׁמוֹ׃ גַּם כִּי אֵלֵךְ בְּגֵיא צַלְמָוֶת לֹא אִירָא רָע כִּי אַתָּה עִמָּדִי שִׁבְטְךָ וּמִשְׁעַנְתֶּךָ הֵמָּה יְנַחֲמֻנִי׃ תַּעֲרֹךְ לְפָנַי שֻׁלְחָן נֶגֶד צֹרְרָי דִּשַּׁנְתָּ בַשֶּׁמֶן רֹאשִׁי כּוֹסִי רְוָיָה׃"

    # Create librarian
    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.4,
        max_results=15
    )

    # Search for parallels
    parallels = librarian.find_parallels(psalm_23_text)

    # Filter out any results from Psalms 23 (note: "Psalms" not "Psalm")
    filtered_parallels = []
    for p in parallels:
        # Check if it's from Psalm 23
        if "23:" not in p.reference:  # This excludes Psalms 23:1-5, Psalms 23:2-6, etc.
            filtered_parallels.append(p)

    # Save results
    with open("psalm_23_cross_book_parallels.txt", "w", encoding="utf-8") as f:
        f.write("PSALM 23 THEMATIC PARALLELS (EXCLUDING ALL PSALM 23)\n")
        f.write("="*60 + "\n\n")
        f.write("Query Text (Psalms 23:3-5):\n")
        f.write("-"*30 + "\n")
        f.write(psalm_23_text)
        f.write("\n\n")
        f.write(f"Total results found: {len(parallels)}\n")
        f.write(f"After filtering Psalm 23: {len(filtered_parallels)}\n\n")

        if filtered_parallels:
            f.write("TOP 5 THEMATIC PARALLELS FROM OTHER BOOKS:\n")
            f.write("="*50 + "\n\n")

            for i, parallel in enumerate(filtered_parallels[:5], 1):
                f.write(f"{i}. {parallel.reference}\n")
                f.write(f"   Similarity: {parallel.similarity:.6f}\n")
                f.write(f"   Book: {parallel.book} ({parallel.book_category})\n")
                f.write(f"   Context verses: {parallel.context_verses}\n\n")

                f.write("   Full Hebrew Text:\n")
                # Format Hebrew text with proper line breaks
                hebrew_lines = parallel.hebrew_text.split('׃')
                for j, line in enumerate(hebrew_lines):
                    if line.strip():
                        f.write(f"   {line.strip()}׃\n")
                f.write("\n")

                # Try to identify thematic connection
                f.write("   Thematic elements:\n")
                if "צַלְמָוֶת" in parallel.hebrew_text:
                    f.write("   - Death/darkness imagery\n")
                if "רֹעִי" in parallel.hebrew_text or "צֹאן" in parallel.hebrew_text:
                    f.write("   - Shepherd/sheep imagery\n")
                if "יְהֹוָה" in parallel.hebrew_text:
                    f.write("   - Divine presence/protection\n")
                if "שֻׁלְחָן" in parallel.hebrew_text or "אֹכֶל" in parallel.hebrew_text:
                    f.write("   - Provision/feast imagery\n")
                f.write("\n")

                f.write("-"*50 + "\n\n")

            # Analysis
            f.write("ANALYSIS:\n")
            f.write("-"*30 + "\n")

            # Group by book category
            categories = {}
            for p in filtered_parallels[:10]:
                cat = p.book_category
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(p)

            f.write(f"• Average similarity of top 5: {sum(p.similarity for p in filtered_parallels[:5])/5:.4f}\n")
            f.write(f"• Book categories represented: {', '.join(sorted(categories.keys()))}\n")
            f.write(f"• Most common category: {max(categories.keys(), key=lambda k: len(categories[k]))}\n")

            # Check if we have non-Psalms results
            non_psalms = [p for p in filtered_parallels[:5] if p.book != "Psalms"]
            f.write(f"• Non-Psalms books in top 5: {len(non_psalms)}/5\n")
            if non_psalms:
                f.write(f"  Non-Psalms: {', '.join(p.book for p in non_psalms)}\n")
        else:
            f.write("No parallels found outside Psalm 23\n")

    # Console summary
    print("Test complete. Full results saved to psalm_23_cross_book_parallels.txt")
    if filtered_parallels:
        non_psalms = [p for p in filtered_parallels[:5] if p.book != "Psalms"]
        print(f"\nQuick summary:")
        print(f"  Top result: {filtered_parallels[0].reference} (similarity: {filtered_parallels[0].similarity:.4f})")
        print(f"  Non-Psalms in top 5: {len(non_psalms)}/5")
        if non_psalms:
            print(f"  Non-Psalms books: {', '.join(p.book for p in non_psalms)}")
    else:
        print("\nNo parallels found outside Psalm 23")


if __name__ == "__main__":
    main()