#!/usr/bin/env python3
"""
Test Psalm 23 thematic search WITH filtering out Psalm 23 matches.
Shows full text for query and top 5 matches.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def main():
    # Use the actual Hebrew text from Psalm 23:3-24:1 chunk (with vowels)
    psalm_23_chunk = "נַפְשִׁי יְשׁוֹבֵב יַנְחֵנִי בְמַעְגְּלֵי צֶדֶק לְמַעַן שְׁמוֹ׃ גַּם כִּי אֵלֵךְ בְּגֵיא צַלְמָוֶת לֹא אִירָא רָע כִּי אַתָּה עִמָּדִי שִׁבְטְךָ וּמִשְׁעַנְתֶּךָ הֵמָּה יְנַחֲמֻנִי׃ תַּעֲרֹךְ לְפָנַי שֻׁלְחָן נֶגֶד צֹרְרָי דִּשַּׁנְתָּ בַשֶּׁמֶן רֹאשִׁי כּוֹסִי רְוָיָה׃ אַךְ טוֹב וָחֶסֶד יִרְדְּפוּנִי כׇּל יְמֵי חַיָּי וְשַׁבְתִּי בְּבֵית יְהֹוָה לְאֹרֶךְ יָמִים׃ לְדָוִד מִזְמוֹר לַיהֹוָה הָאָרֶץ וּמְלוֹאָהּ תֵּבֵל וְיֹשְׁבֵי בָהּ׃"

    # Create librarian with default threshold
    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.4,
        max_results=10
    )

    # Search for parallels, filtering out Psalm 23
    query_verses = ["Psalm 23:3", "Psalm 23:4", "Psalm 23:5"]
    parallels = librarian.find_parallels(psalm_23_chunk, query_verses=query_verses)

    # Filter out any remaining Psalm 23 references
    filtered_parallels = []
    for p in parallels:
        if "Psalm 23" not in p.reference:
            filtered_parallels.append(p)

    # Save results to file
    with open("psalm_23_filtered_results.txt", "w", encoding="utf-8") as f:
        f.write("PSALM 23 THEMATIC PARALLELS (PSALM 23 FILTERED OUT)\n")
        f.write("="*60 + "\n\n")
        f.write(f"Query Text (Psalms 23:3-24:1):\n")
        f.write("-"*40 + "\n")
        f.write(psalm_23_chunk)
        f.write("\n\n")
        f.write(f"Query verses being filtered: {', '.join(query_verses)}\n")
        f.write(f"Total results found: {len(parallels)}\n")
        f.write(f"Results after filtering Psalm 23: {len(filtered_parallels)}\n\n")

        f.write("TOP 5 THEMATIC PARALLELS (excluding Psalm 23):\n")
        f.write("="*50 + "\n\n")

        for i, parallel in enumerate(filtered_parallels[:5], 1):
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
        if filtered_parallels:
            avg_similarity = sum(p.similarity for p in filtered_parallels[:5]) / min(5, len(filtered_parallels))
            f.write(f"• Average similarity of top 5: {avg_similarity:.4f}\n")
            f.write(f"• Highest similarity: {filtered_parallels[0].similarity:.4f} ({filtered_parallels[0].reference})\n")
            f.write(f"• Books represented: {', '.join(sorted(set(p.book for p in filtered_parallels[:5])))}\n")
        else:
            f.write("• No thematic parallels found after filtering Psalm 23\n")

    # Simple console output
    print("Test complete. Full results saved to psalm_23_filtered_results.txt")
    if filtered_parallels:
        print(f"\nTop 3 parallels (excluding Psalm 23):")
        for i, p in enumerate(filtered_parallels[:3], 1):
            print(f"  {i}. {p.reference} (similarity: {p.similarity:.4f})")
    else:
        print("\nNo parallels found after filtering Psalm 23")


if __name__ == "__main__":
    main()