#!/usr/bin/env python3
"""
Complete Psalm 23 report with database translations.
"""
import sqlite3
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def get_verse_translation(book, chapter, verse):
    """Get translation for a specific verse"""
    conn = sqlite3.connect('database/tanakh.db')
    cursor = conn.cursor()
    cursor.execute('SELECT english FROM verses WHERE book_name = ? AND chapter = ? AND verse = ?',
                   (book, chapter, verse))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def main():
    # Connect to database
    conn = sqlite3.connect('database/tanakh.db')
    cursor = conn.cursor()

    # Query text
    query_hebrew = "נַפְשִׁי יְשׁוֹבֵב יַנְחֵנִי בְמַעְגְּלֵי צֶדֶק לְמַעַן שְׁמוֹ׃ גַּם כִּי אֵלֵךְ בְּגֵיא צַלְמָוֶת לֹא אִירָא רָע כִּי אַתָּה עִמָּדִי שִׁבְטְךָ וּמִשְׁעַנְתֶּךָ הֵמָּה יְנַחֲמֻנִי׃ תַּעֲרֹךְ לְפָנַי שֻׁלְחָן נֶגֶד צֹרְרָי דִּשַּׁנְתָּ בַשֶּׁמֶן רֹאשִׁי כּוֹסִי רְוָיָה׃"

    # Get query translation
    psalm_23_3 = get_verse_translation('Psalms', 23, 3)
    psalm_23_4 = get_verse_translation('Psalms', 23, 4)
    psalm_23_5 = get_verse_translation('Psalms', 23, 5)
    query_english = f"{psalm_23_3} {psalm_23_4} {psalm_23_5}"

    # Create librarian
    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.35,
        max_results=30
    )

    # Search for parallels
    parallels = librarian.find_parallels(query_hebrew)

    # Filter results
    filtered = []
    for p in parallels:
        if "23:" not in p.reference:  # Exclude Psalm 23
            filtered.append(p)

    # Get top results
    top_10 = filtered[:10]

    # Write report
    with open("psalm_23_with_complete_db_translations.txt", "w", encoding="utf-8") as f:
        f.write("PSALM 23 THEMATIC PARALLELS - COMPLETE REPORT\n")
        f.write("="*60 + "\n\n")

        f.write("QUERY TEXT - Psalm 23:3-5:\n")
        f.write("-"*40 + "\n\n")
        f.write("Hebrew:\n")
        f.write(f"{query_hebrew}\n\n")
        f.write("English Translation (from tanakh.db):\n")
        f.write(f"{query_english}\n\n")
        f.write("="*60 + "\n\n")

        f.write(f"TOP 10 THEMATIC PARALLELS (excluding Psalm 23):\n")
        f.write("="*60 + "\n\n")

        for i, parallel in enumerate(top_10, 1):
            f.write(f"{i}. {parallel.reference}\n")
            f.write(f"   Similarity: {parallel.similarity:.6f}\n")
            f.write(f"   Book: {parallel.book}\n\n")

            # Try to get translation
            # Parse reference to get book, chapter, verse
            parts = parallel.reference.split()
            if len(parts) >= 2:
                book = parts[0]
                ref_part = parts[1]
                if ':' in ref_part:
                    ref_parts = ref_part.split(':')
                    if len(ref_parts) >= 2:
                        chapter = ref_parts[0]
                        verse = ref_parts[1]
                        try:
                            chapter = int(chapter)
                            verse = int(verse)
                            translation = get_verse_translation(book, chapter, verse)
                            if translation:
                                f.write(f"   English: {translation}\n\n")
                            else:
                                f.write("   English: [Verse translation not found]\n\n")
                        except:
                            f.write("   English: [Could not parse reference]\n\n")
                    else:
                        f.write("   English: [Invalid reference format]\n\n")
                else:
                    f.write("   English: [Could not parse reference]\n\n")
            else:
                f.write("   English: [Invalid reference format]\n\n")

            f.write("-"*60 + "\n\n")

        # Summary
        psalms_count = sum(1 for p in top_10 if p.book == "Psalms")
        non_psalms = [p for p in top_10 if p.book != "Psalms"]
        non_psalms_books = list(set(p.book for p in non_psalms))

        f.write("SUMMARY:\n")
        f.write("-"*30 + "\n")
        f.write(f"Total results shown: {len(top_10)}\n")
        f.write(f"From Psalms: {psalms_count}\n")
        f.write(f"From other books: {len(non_psalms)}\n")
        if non_psalms_books:
            f.write(f"Other books: {', '.join(non_psalms_books)}\n")

        avg_sim = sum(p.similarity for p in top_10) / len(top_10)
        f.write(f"Average similarity: {avg_sim:.4f}\n")

    conn.close()

    # Console output
    print("\n" + "="*60)
    print("PSALM 23 THEMATIC PARALLELS")
    print("="*60)
    print("\nQuery Text - Psalm 23:3-5:")
    print(f"\nEnglish:\n{query_english}\n")
    print("-"*60)
    print(f"\nTop {len(top_10)} Thematic Parallels:\n")

    for i, p in enumerate(top_10[:5], 1):
        print(f"\n{i}. {p.reference} (similarity: {p.similarity:.4f})")
        print(f"   Book: {p.book}")

        # Get first verse translation for context
        parts = p.reference.split()
        if len(parts) >= 2 and ':' in parts[1]:
            book = parts[0]
            ref_parts = parts[1].split(':')
            if len(ref_parts) >= 2:
                chapter = ref_parts[0]
                verse = ref_parts[1]
                try:
                    chapter = int(chapter)
                    verse = int(verse)
                    translation = get_verse_translation(book, chapter, verse)
                    if translation:
                        print(f"   {translation[:100]}...")
                except:
                    pass

    print(f"\nFull report saved to: psalm_23_with_complete_db_translations.txt")


if __name__ == "__main__":
    main()