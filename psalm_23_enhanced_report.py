#!/usr/bin/env python3
"""
Enhanced Psalm 23 report with database translations and categorized results.
Shows query chunk with translation and top 5 parallels from Psalms and other books.
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


def get_chunk_translations(book, chapter, verse_range):
    """Get translations for a chunk with verse ranges like '3-5' or '3-24:1'"""
    translations = []

    # Handle cross-chapter range like "3-24:1"
    if '-' in verse_range and ':' in verse_range.split('-')[1]:
        parts = verse_range.split('-')
        start_verse = int(parts[0])
        end_part = parts[1].split(':')
        end_chapter = int(end_part[0])
        end_verse = int(end_part[1])

        # From start verse to end of chapter
        for v in range(start_verse, 100):  # Assume max 100 verses per chapter
            trans = get_verse_translation(book, chapter, v)
            if trans:
                translations.append(f"{chapter}:{v}: {trans}")
            else:
                break  # Stop when verse doesn't exist

        # From next chapter to end verse
        for c in range(chapter + 1, end_chapter + 1):
            for v in range(1, end_verse + 1):
                trans = get_verse_translation(book, c, v)
                if trans:
                    translations.append(f"{c}:{v}: {trans}")
                else:
                    break

    # Handle simple range like "3-5"
    elif '-' in verse_range:
        start, end = map(int, verse_range.split('-'))
        for v in range(start, end + 1):
            trans = get_verse_translation(book, chapter, v)
            if trans:
                translations.append(f"v{v}: {trans}")
    else:
        # Single verse
        single_verse = int(verse_range)
        trans = get_verse_translation(book, chapter, single_verse)
        if trans:
            translations.append(f"v{verse_range}: {trans}")

    return translations


def parse_reference(reference):
    """Parse a reference like 'Psalms 23:3-5' into components"""
    parts = reference.split()
    if len(parts) < 2:
        return None, None, None

    book = parts[0]
    ref_part = parts[1]

    if ':' not in ref_part:
        return book, None, None

    chapter, verse_range = ref_part.split(':', 1)

    try:
        chapter = int(chapter)
        return book, chapter, verse_range
    except:
        return book, None, None


def format_translations(translations):
    """Format translations for display"""
    if not translations:
        return "[No translations found]"
    return '\n   '.join(translations)


def main():
    print("Creating enhanced Psalm 23 thematic parallels report...")

    # Query text - Psalm 23:3-5 in Hebrew
    query_hebrew = "נַפְשִׁי יְשׁוֹבֵב יַנְחֵנִי בְמַעְגְּלֵי צֶדֶק לְמַעַן שְׁמוֹ׃ גַּם כִּי אֵלֵךְ בְּגֵיא צַלְמָוֶת לֹא אִירָא רָע כִּי אַתָּה עִמָּדִי שִׁבְטְךָ וּמִשְׁעַנְתֶּךָ הֵמָּה יְנַחֲמֻנִי׃ תַּעֲרֹךְ לְפָנַי שֻׁלְחָן נֶגֶד צֹרְרָי דִּשַּׁנְתָּ בַשֶּׁמֶן רֹאשִׁי כּוֹסִי רְוָיָה׃"

    # Get query translation
    query_translations = []
    for v in [3, 4, 5]:
        trans = get_verse_translation('Psalms', 23, v)
        if trans:
            query_translations.append(f"v{v}: {trans}")

    # Create librarian
    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.35,  # Lower threshold to get more results
        max_results=50
    )

    # Search for parallels
    print("Searching for thematic parallels...")
    parallels = librarian.find_parallels(query_hebrew)

    # Filter results (exclude Psalm 23 itself)
    filtered = [p for p in parallels if "23:" not in p.reference or not p.reference.startswith("Psalms")]

    # Separate Psalms and non-Psalms results
    psalms_results = [p for p in filtered if p.book == "Psalms"]
    non_psalms_results = [p for p in filtered if p.book != "Psalms"]

    # Take top 5 from each category
    top_5_psalms = psalms_results[:5]
    top_5_non_psalms = non_psalms_results[:5]

    # Write report
    with open("psalm_23_enhanced_report.txt", "w", encoding="utf-8") as f:
        f.write("PSALM 23 THEMATIC PARALLELS - ENHANCED REPORT\n")
        f.write("="*80 + "\n\n")

        # Query chunk section
        f.write("QUERY CHUNK - Psalm 23:3-5:\n")
        f.write("-"*50 + "\n\n")
        f.write("Reference: Psalms 23:3-5\n\n")
        f.write("Hebrew Text:\n")
        f.write(f"{query_hebrew}\n\n")
        f.write("English Translation (from tanakh.db):\n")
        f.write(f"   {format_translations(query_translations)}\n\n")
        f.write("="*80 + "\n\n")

        # Psalms parallels section
        f.write(f"TOP 5 THEMATIC PARALLELS FROM PSALMS:\n")
        f.write("="*80 + "\n\n")

        if top_5_psalms:
            for i, parallel in enumerate(top_5_psalms, 1):
                f.write(f"{i}. {parallel.reference}\n")
                f.write(f"   Similarity Score: {parallel.similarity:.6f}\n")
                f.write(f"   Hebrew Text:\n")
                f.write(f"   {parallel.hebrew_text}\n\n")

                # Get translations
                book, chapter, verse_range = parse_reference(parallel.reference)
                if book and chapter and verse_range:
                    translations = get_chunk_translations(book, chapter, verse_range)
                    f.write(f"   English Translation:\n")
                    f.write(f"   {format_translations(translations)}\n\n")
                else:
                    f.write("   English Translation: [Could not parse reference]\n\n")

                f.write("-"*80 + "\n\n")
        else:
            f.write("No parallels found from other Psalms.\n\n")

        # Non-Psalms parallels section
        f.write(f"TOP 5 THEMATIC PARALLELS FROM OTHER BOOKS:\n")
        f.write("="*80 + "\n\n")

        if top_5_non_psalms:
            for i, parallel in enumerate(top_5_non_psalms, 1):
                f.write(f"{i}. {parallel.reference}\n")
                f.write(f"   Similarity Score: {parallel.similarity:.6f}\n")
                f.write(f"   Hebrew Text:\n")
                f.write(f"   {parallel.hebrew_text}\n\n")

                # Get translations
                book, chapter, verse_range = parse_reference(parallel.reference)
                if book and chapter and verse_range:
                    translations = get_chunk_translations(book, chapter, verse_range)
                    f.write(f"   English Translation:\n")
                    f.write(f"   {format_translations(translations)}\n\n")
                else:
                    f.write("   English Translation: [Could not parse reference]\n\n")

                f.write("-"*80 + "\n\n")
        else:
            f.write("No parallels found from other books.\n\n")

        # Summary statistics
        f.write("SUMMARY STATISTICS:\n")
        f.write("-"*30 + "\n")
        f.write(f"Total parallels found: {len(filtered)}\n")
        f.write(f"From Psalms: {len(psalms_results)}\n")
        f.write(f"From other books: {len(non_psalms_results)}\n\n")

        if top_5_psalms:
            avg_sim_psalms = sum(p.similarity for p in top_5_psalms) / len(top_5_psalms)
            f.write(f"Average similarity (Top 5 Psalms): {avg_sim_psalms:.4f}\n")

        if top_5_non_psalms:
            avg_sim_non_psalms = sum(p.similarity for p in top_5_non_psalms) / len(top_5_non_psalms)
            f.write(f"Average similarity (Top 5 Other): {avg_sim_non_psalms:.4f}\n")

        # Book distribution for non-Psalms
        if non_psalms_results:
            non_psalms_books = {}
            for p in non_psalms_results[:20]:  # Count top 20
                non_psalms_books[p.book] = non_psalms_books.get(p.book, 0) + 1

            f.write(f"\nNon-Psalms books represented (top 20): {', '.join(f'{book} ({count})' for book, count in non_psalms_books.items())}\n")

    # Console output
    print("\n" + "="*80)
    print("PSALM 23 THEMATIC PARALLELS - ENHANCED REPORT")
    print("="*80)

    print("\nQUERY CHUNK - Psalm 23:3-5:")
    print(f"\nEnglish Translation:\n   {format_translations(query_translations)}\n")

    print("\n" + "-"*80)
    print("\nTOP 5 PARALLELS FROM PSALMS:")
    for i, p in enumerate(top_5_psalms, 1):
        print(f"\n{i}. {p.reference} (similarity: {p.similarity:.4f})")
        # Get first verse translation for preview
        book, chapter, verse_range = parse_reference(p.reference)
        if book and chapter and verse_range:
            if '-' in verse_range:
                first_verse = int(verse_range.split('-')[0])
            else:
                first_verse = int(verse_range)
            trans = get_verse_translation(book, chapter, first_verse)
            if trans:
                print(f"   Preview: {trans[:80]}...")

    print("\n" + "-"*80)
    print("\nTOP 5 PARALLELS FROM OTHER BOOKS:")
    for i, p in enumerate(top_5_non_psalms, 1):
        print(f"\n{i}. {p.reference} (similarity: {p.similarity:.4f})")
        # Get first verse translation for preview
        book, chapter, verse_range = parse_reference(p.reference)
        if book and chapter and verse_range:
            if '-' in verse_range:
                first_verse = int(verse_range.split('-')[0])
            else:
                first_verse = int(verse_range)
            trans = get_verse_translation(book, chapter, first_verse)
            if trans:
                print(f"   Preview: {trans[:80]}...")

    print(f"\n" + "="*80)
    print(f"Full report saved to: psalm_23_enhanced_report.txt")
    print(f"Total parallels found: {len(filtered)} (Psalms: {len(psalms_results)}, Other: {len(non_psalms_results)})")


if __name__ == "__main__":
    main()