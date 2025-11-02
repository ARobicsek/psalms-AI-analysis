#!/usr/bin/env python3
"""Compare verse texts from canonical and liturgical sources."""

import sqlite3
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.liturgy.liturgy_indexer import LiturgyIndexer

# Open output file
output_file = Path(__file__).parent.parent / "output" / "verse_comparison.txt"
output = open(output_file, 'w', encoding='utf-8')

def compare_verse(psalm_ch, verse_num, prayer_id):
    """Compare a specific verse between canonical and liturgical text."""

    # Get canonical verse from tanakh.db
    tanakh_db = Path(__file__).parent.parent / "database" / "tanakh.db"
    conn1 = sqlite3.connect(tanakh_db)
    cursor1 = conn1.cursor()

    cursor1.execute("""
        SELECT hebrew FROM verses
        WHERE book_name = 'Psalms' AND chapter = ? AND verse = ?
    """, (psalm_ch, verse_num))

    canonical = cursor1.fetchone()
    conn1.close()

    if not canonical:
        output.write(f"Psalm {psalm_ch}:{verse_num} not found in tanakh.db\n")
        return

    canonical_text = canonical[0]

    # Get prayer text from liturgy.db
    liturgy_db = Path(__file__).parent.parent / "data" / "liturgy.db"
    conn2 = sqlite3.connect(liturgy_db)
    cursor2 = conn2.cursor()

    cursor2.execute("""
        SELECT hebrew_text FROM prayers WHERE prayer_id = ?
    """, (prayer_id,))

    prayer = cursor2.fetchone()
    conn2.close()

    if not prayer:
        output.write(f"Prayer {prayer_id} not found\n")
        return

    prayer_text = prayer[0]

    # Normalize both using the indexer's method
    indexer = LiturgyIndexer(verbose=False)
    canonical_norm = indexer._full_normalize(canonical_text)

    # Check if the canonical normalized text appears in the prayer
    prayer_norm = indexer._full_normalize(prayer_text)
    found = canonical_norm in prayer_norm

    output.write(f"\nPsalm {psalm_ch}:{verse_num} in Prayer {prayer_id}\n")
    output.write(f"  Canonical: {canonical_text}\n")
    output.write(f"  Canonical normalized: {canonical_norm}\n")
    output.write(f"  Found in prayer: {found}\n")

    if not found:
        # Try to find what's in the prayer that's close
        words = canonical_norm.split()
        if len(words) > 3:
            # Try first 3 words
            partial = ' '.join(words[:3])
            if partial in prayer_norm:
                output.write(f"  First 3 words found: {partial}\n")
            else:
                output.write(f"  First 3 words NOT found: {partial}\n")

    return found

# Check missing verses for Psalm 23
output.write("=" * 70 + "\n")
output.write("PSALM 23 MISSING VERSES\n")
output.write("=" * 70 + "\n")
compare_verse(23, 5, 574)
compare_verse(23, 6, 574)

# Check missing verses for Psalm 19
output.write("\n" + "=" * 70 + "\n")
output.write("PSALM 19 MISSING VERSES\n")
output.write("=" * 70 + "\n")
compare_verse(19, 8, 251)
compare_verse(19, 9, 251)
compare_verse(19, 10, 251)
compare_verse(19, 15, 251)

output.close()
print(f"Results written to {output_file}")
