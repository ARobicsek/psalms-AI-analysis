#!/usr/bin/env python3
"""
Test Psalm 23 thematic search with English translations from tanakh.db.
"""
import sys
import sqlite3
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def get_db_translations(references):
    """Get English translations from tanakh.db for given references"""
    conn = sqlite3.connect('database/tanakh.db')
    cursor = conn.cursor()

    translations = {}
    for ref in references:
        # Handle range references (e.g., "Psalms 141:5-9")
        if '-' in ref:
            # For now, just get the first verse of the range
            base_ref = ref.split('-')[0]
        else:
            base_ref = ref

        cursor.execute('SELECT hebrew, english FROM verses WHERE reference = ? LIMIT 1', (base_ref,))
        result = cursor.fetchone()
        if result:
            translations[ref] = {
                'hebrew': result[0],
                'english': result[1]
            }

    conn.close()
    return translations


def get_verse_range_translation(book, start_ch, start_v, end_ch, end_v):
    """Get translation for a range of verses by combining individual verses"""
    conn = sqlite3.connect('database/tanakh.db')
    cursor = conn.cursor()

    # If it's a simple single chapter range
    if start_ch == end_ch:
        cursor.execute('''
            SELECT hebrew, english FROM verses
            WHERE book_name = ? AND chapter = ? AND verse BETWEEN ? AND ?
            ORDER BY verse
        ''', (book, start_ch, start_v, end_v))
    else:
        # Multi-chapter range - get all verses in range
        cursor.execute('''
            SELECT hebrew, english FROM verses
            WHERE book_name = ? AND
                  ((chapter = ? AND verse >= ?) OR
                   (chapter > ? AND chapter < ?) OR
                   (chapter = ? AND verse <= ?))
            ORDER BY chapter, verse
        ''', (book, start_ch, start_v, start_ch, end_ch, end_ch, end_v))

    results = cursor.fetchall()
    conn.close()

    if results:
        hebrew = ' '.join(r[0] for r in results)
        english = ' '.join(r[1] for r in results)
        return hebrew, english

    return None, None


def parse_reference(reference):
    """Parse a reference like 'Psalms 141:5-9' into components"""
    import re

    # Handle different reference formats
    if ' ' not in reference:
        return None, None, None, None, None

    # Split book from chapter:verse
    parts = reference.split(' ', 1)
    if len(parts) != 2:
        return None, None, None, None, None

    book = parts[0]
    chapter_verse = parts[1]

    # Parse chapter:verse-range
    if '-' in chapter_verse:
        # Range like "5-9" or "3:4-5:6"
        if ':' in chapter_verse:
            # Format like "3:4-5:6" or "5:1-5:9"
            match = re.match(r'(\d+):(\d+)-(\d+):(\d+)', chapter_verse)
            if match:
                return book, int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
            # Format like "5:1-9"
            match = re.match(r'(\d+):(\d+)-(\d+)', chapter_verse)
            if match:
                return book, int(match.group(1)), int(match.group(2)), int(match.group(1)), int(match.group(3))
        else:
            # Format like "5-9" (same chapter)
            match = re.match(r'(\d+)-(\d+)', chapter_verse)
            if match:
                return book, int(match.group(1)), int(match.group(2)), int(match.group(1)), int(match.group(2))
    else:
        # Single verse like "5:7"
        if ':' in chapter_verse:
            ch, v = chapter_verse.split(':')
            return book, int(ch), int(v), int(ch), int(v)
        else:
            # Just verse number without chapter
            return book, 1, int(chapter_verse), 1, int(chapter_verse)

    return None, None, None, None, None


def main():
    # Query text (Psalm 23:3-5)
    query_hebrew = "נַפְשִׁי יְשׁוֹבֵב יַנְחֵנִי בְמַעְגְּלֵי צֶדֶק לְמַעַן שְׁמוֹ׃ גַּם כִּי אֵלֵךְ בְּגֵיא צַלְמָוֶת לֹא אִירָא רָע כִּי אַתָּה עִמָּדִי שִׁבְטְךָ וּמִשְׁעַנְתֶּךָ הֵמָּה יְנַחֲמֻנִי׃ תַּעֲרֹךְ לְפָנַי שֻׁלְחָן נֶגֶד צֹרְרָי דִּשַּׁנְתָּ בַשֶּׁמֶן רֹאשִׁי כּוֹסִי רְוָיָה׃"

    # Get query translation from database
    query_english = None
    conn = sqlite3.connect('database/tanakh.db')
    cursor = conn.cursor()

    # Combine translations for Psalm 23:3-5
    psalm_23_eng = []
    for verse_num in [3, 4, 5]:
        cursor.execute('SELECT english FROM verses WHERE reference = ?', (f'Psalm 23:{verse_num}',))
        result = cursor.fetchone()
        if result:
            psalm_23_eng.append(result[0])
    query_english = ' '.join(psalm_23_eng)

    conn.close()

    # Create librarian
    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.35,
        max_results=30
    )

    # Search for parallels
    parallels = librarian.find_parallels(query_hebrew)

    # Filter and categorize results
    psalms_results = []
    non_psalms_results = []

    for p in parallels:
        if "23:" in p.reference:
            continue  # Skip Psalm 23 itself
        if p.book == "Psalms":
            psalms_results.append(p)
        else:
            non_psalms_results.append(p)

    # Take top 5 from each category
    top_psalms = psalms_results[:5]
    top_non_psalms = non_psalms_results[:5]

    # Get translations for all results
    all_refs = [p.reference for p in top_psalms + top_non_psalms]
    translations = get_db_translations(all_refs)

    # Save results with database translations
    with open("psalm_23_with_db_translations.txt", "w", encoding="utf-8") as f:
        f.write("PSALM 23 THEMATIC PARALLELS - USING DATABASE TRANSLATIONS")
        f.write("="*70 + "\n\n")

        f.write("QUERY TEXT - PSALM 23:3-5:\n")
        f.write("-"*40 + "\n\n")
        f.write("Hebrew (with vowels):\n")
        f.write(f"{query_hebrew}\n\n")
        f.write("English Translation (from tanakh.db):\n")
        f.write(f"{query_english}\n\n")
        f.write("="*70 + "\n\n")

        # Results from other Psalms
        f.write("TOP 5 MATCHES FROM OTHER PSALMS:\n")
        f.write("="*50 + "\n\n")

        for i, parallel in enumerate(top_psalms, 1):
            f.write(f"{i}. {parallel.reference}\n")
            f.write(f"   Similarity Score: {parallel.similarity:.6f}\n")
            f.write(f"   Book: {parallel.book} ({parallel.book_category})\n")
            f.write(f"   Context: {parallel.context_verses} verses\n\n")

            f.write("   Hebrew Text from Vector Store:\n")
            f.write(f"   {parallel.hebrew_text}\n\n")

            f.write("   Hebrew Text from Database:\n")
            if parallel.reference in translations:
                f.write(f"   {translations[parallel.reference]['hebrew']}\n\n")
            else:
                # Try to get range translation
                book, start_ch, start_v, end_ch, end_v = parse_reference(parallel.reference)
                if book:
                    db_hebrew, db_english = get_verse_range_translation(book, start_ch, start_v, end_ch, end_v)
                    if db_hebrew:
                        f.write(f"   {db_hebrew}\n\n")
                    else:
                        f.write("   [Translation not found in database]\n\n")
                else:
                    f.write("   [Could not parse reference]\n\n")

            f.write("   English Translation (from tanakh.db):\n")
            if parallel.reference in translations:
                f.write(f"   {translations[parallel.reference]['english']}\n\n")
            else:
                # Try to get range translation
                if book:
                    db_hebrew, db_english = get_verse_range_translation(book, start_ch, start_v, end_ch, end_v)
                    if db_english:
                        f.write(f"   {db_english}\n\n")
                    else:
                        f.write("   [Translation not found in database]\n\n")
                else:
                    f.write("   [Could not parse reference]\n\n")

            f.write("-"*70 + "\n\n")

        # Results from outside Psalms
        f.write("TOP 5 MATCHES FROM OUTSIDE PSALMS:\n")
        f.write("="*50 + "\n\n")

        if top_non_psalms:
            for i, parallel in enumerate(top_non_psalms, 1):
                f.write(f"{i}. {parallel.reference}\n")
                f.write(f"   Similarity Score: {parallel.similarity:.6f}\n")
                f.write(f"   Book: {parallel.book} ({parallel.book_category})\n")
                f.write(f"   Context: {parallel.context_verses} verses\n\n")

                f.write("   Hebrew Text from Vector Store:\n")
                f.write(f"   {parallel.hebrew_text}\n\n")

                f.write("   English Translation (from tanakh.db):\n")
                if parallel.reference in translations:
                    f.write(f"   {translations[parallel.reference]['english']}\n\n")
                else:
                    # Try to get range translation
                    book, start_ch, start_v, end_ch, end_v = parse_reference(parallel.reference)
                    if book:
                        db_hebrew, db_english = get_verse_range_translation(book, start_ch, start_v, end_ch, end_v)
                        if db_english:
                            f.write(f"   {db_english}\n\n")
                        else:
                            f.write("   [Translation not found in database]\n\n")
                    else:
                        f.write("   [Could not parse reference]\n\n")

                f.write("-"*70 + "\n\n")
        else:
            f.write("No results from outside Psalms found with similarity >= 0.35\n\n")

        # Summary
        f.write("SUMMARY:\n")
        f.write("-"*30 + "\n")
        f.write(f"Total parallels found: {len(parallels)}\n")
        f.write(f"Other Psalms: {len(top_psalms)} matches\n")
        f.write(f"Outside Psalms: {len(top_non_psalms)} matches\n")

        if top_non_psalms:
            f.write(f"\nNon-Psalms books found: {', '.join(set(p.book for p in top_non_psalms))}\n")
            avg_sim = sum(p.similarity for p in top_non_psalms) / len(top_non_psalms)
            f.write(f"Average similarity (non-Psalms): {avg_sim:.4f}\n")

    print("Report created with database translations: psalm_23_with_db_translations.txt")
    print(f"\nSummary:")
    print(f"  Top Psalm match: {top_psalms[0].reference if top_psalms else 'None'}")
    print(f"  Top non-Psalm match: {top_non_psalms[0].reference if top_non_psalms else 'None'}")


if __name__ == "__main__":
    main()