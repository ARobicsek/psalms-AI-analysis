#!/usr/bin/env python3
"""Check if Prayer 251 contains all of Psalm 19."""

import sqlite3
from pathlib import Path

# Get Prayer 251 text
liturgy_db = Path(__file__).parent.parent / "data" / "liturgy.db"
conn = sqlite3.connect(liturgy_db)
cursor = conn.cursor()

cursor.execute("SELECT hebrew_text, prayer_name FROM prayers WHERE prayer_id = 251")
prayer = cursor.fetchone()
conn.close()

if prayer:
    prayer_text, name = prayer
    print(f"Prayer 251: {name}")
    print(f"Length: {len(prayer_text)} chars")
    print(f"Words: {len(prayer_text.split())}")

    # Write to file to check content
    output_file = Path(__file__).parent.parent / "output" / "prayer_251_text.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Prayer 251: {name}\n")
        f.write(f"Length: {len(prayer_text)} chars\n")
        f.write(f"Words: {len(prayer_text.split())}\n\n")
        f.write(prayer_text)

    print(f"Text written to {output_file}")

# Now check all 15 verses from tanakh.db
tanakh_db = Path(__file__).parent.parent / "database" / "tanakh.db"
conn2 = sqlite3.connect(tanakh_db)
cursor2 = conn2.cursor()

cursor2.execute("""
    SELECT verse, hebrew FROM verses
    WHERE book_name = 'Psalms' AND chapter = 19
    ORDER BY verse
""")

verses = cursor2.fetchall()
conn2.close()

# Write canonical psalm to file
output_file2 = Path(__file__).parent.parent / "output" / "psalm_19_canonical.txt"
with open(output_file2, 'w', encoding='utf-8') as f:
    f.write("Psalm 19 - Canonical Text\n")
    f.write("="*70 + "\n\n")
    for verse_num, verse_text in verses:
        f.write(f"Verse {verse_num}: {verse_text}\n\n")

print(f"Canonical Psalm 19 written to {output_file2}")
print(f"\nTotal verses in canonical Psalm 19: {len(verses)}")
