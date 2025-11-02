#!/usr/bin/env python3
"""Extract the full Psalm 23 from Prayer 574 and compare to canonical."""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.liturgy.liturgy_indexer import LiturgyIndexer

# Get Prayer 574 text
liturgy_db = Path(__file__).parent.parent / "data" / "liturgy.db"
conn = sqlite3.connect(liturgy_db)
cursor = conn.cursor()

cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = 574")
prayer_text = cursor.fetchone()[0]
conn.close()

# Find the start of Psalm 23 in the prayer
# It starts with "מִזְמוֹר לְדָוִד, יְהֹוָה רֹעִי"
start_marker = "מִזְמוֹר לְדָוִד"
start_idx = prayer_text.find(start_marker)

if start_idx == -1:
    print("Could not find Psalm 23 start marker!")
    sys.exit(1)

# Extract from start marker to a reasonable length (let's say 500 chars)
psalm_in_prayer = prayer_text[start_idx:start_idx+500]

# Get canonical Psalm 23
tanakh_db = Path(__file__).parent.parent / "database" / "tanakh.db"
conn2 = sqlite3.connect(tanakh_db)
cursor2 = conn2.cursor()

cursor2.execute("""
    SELECT verse, hebrew FROM verses
    WHERE book_name = 'Psalms' AND chapter = 23
    ORDER BY verse
""")
verses = cursor2.fetchall()
conn2.close()

# Write to file
output_file = Path(__file__).parent.parent / "output" / "psalm23_comparison.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("PSALM 23 IN PRAYER 574 (extracted)\n")
    f.write("="*70 + "\n\n")
    f.write(psalm_in_prayer)
    f.write("\n\n" + "="*70 + "\n\n")

    # Now compare each verse
    indexer = LiturgyIndexer(verbose=False)
    prayer_norm = indexer._full_normalize(prayer_text)

    f.write("VERSE-BY-VERSE COMPARISON\n")
    f.write("="*70 + "\n\n")

    for verse_num, canonical_text in verses:
        f.write(f"VERSE {verse_num}\n")
        f.write(f"Canonical: {canonical_text}\n")

        canonical_norm = indexer._full_normalize(canonical_text)
        f.write(f"Canonical normalized: {canonical_norm}\n")

        found = canonical_norm in prayer_norm
        f.write(f"Found in prayer: {found}\n")

        if not found:
            # Try to find what's in the prayer that's close
            # Look for the first 3 words
            words = canonical_norm.split()[:3]
            search_phrase = ' '.join(words)
            if search_phrase in prayer_norm:
                # Find the context
                idx = prayer_norm.find(search_phrase)
                context = prayer_norm[max(0, idx-20):idx+len(canonical_norm)+20]
                f.write(f"Context around first 3 words: ...{context}...\n")

        f.write("\n")

print(f"Comparison written to {output_file}")
