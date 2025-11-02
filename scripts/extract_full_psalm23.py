#!/usr/bin/env python3
"""Extract full Psalm 23 starting from position 2141."""

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

# Extract from position 2141
start_pos = 2141
# Extract until we find "אִם תָּשִׁיב" (the next section)
end_marker = "אִם תָּשִׁיב"
end_pos = prayer_text.find(end_marker, start_pos)

psalm_text = prayer_text[start_pos:end_pos]

# Get canonical verses 5 and 6
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

# Write output
output_file = Path(__file__).parent.parent / "output" / "full_psalm23_extraction.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("FULL PSALM 23 FROM PRAYER 574\n")
    f.write("="*70 + "\n\n")
    f.write(psalm_text)
    f.write("\n\n" + "="*70 + "\n\n")

    # Now normalize and compare each verse
    indexer = LiturgyIndexer(verbose=False)
    psalm_norm = indexer._full_normalize(psalm_text)

    f.write("Normalized prayer psalm:\n")
    f.write(psalm_norm)
    f.write("\n\n" + "="*70 + "\n\n")

    for verse_num, canonical_text in verses:
        f.write(f"VERSE {verse_num}\n")
        f.write(f"Canonical: {canonical_text}\n")

        canonical_norm = indexer._full_normalize(canonical_text)
        f.write(f"Canonical normalized: {canonical_norm}\n")

        found = canonical_norm in psalm_norm
        f.write(f"Found: {found}\n")

        if not found and verse_num in [5, 6]:
            # For verses 5-6, let's check character by character
            f.write("\nLooking for this verse in the normalized prayer text...\n")
            # Find where it might be
            first_word = canonical_norm.split()[0]
            idx = psalm_norm.find(first_word)
            if idx >= 0:
                context = psalm_norm[idx:idx+len(canonical_norm)+50]
                f.write(f"Context starting with '{first_word}': {context}\n")

        f.write("\n")

print(f"Full extraction written to {output_file}")
