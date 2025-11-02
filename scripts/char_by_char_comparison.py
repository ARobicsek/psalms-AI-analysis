#!/usr/bin/env python3
"""Character-by-character comparison of verse 5."""

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

# Get canonical verse 5
tanakh_db = Path(__file__).parent.parent / "database" / "tanakh.db"
conn2 = sqlite3.connect(tanakh_db)
cursor2 = conn2.cursor()

cursor2.execute("""
    SELECT hebrew FROM verses
    WHERE book_name = 'Psalms' AND chapter = 23 AND verse = 5
""")
canonical_v5 = cursor2.fetchone()[0]
conn2.close()

# Extract verse 5 from prayer (after "יְנַחֲמֻנִי:")
# Verse 5 starts with "תַּעֲרֹךְ"
v5_start = prayer_text.find("תַּעֲרֹךְ לפָנַי")
if v5_start == -1:
    v5_start = prayer_text.find("תַּעֲרֹךְ לְפָנַי")

# Get approximately one verse worth
prayer_v5 = prayer_text[v5_start:v5_start+100]

# Find the actual end (probably a colon)
colon_idx = prayer_v5.find(":")
if colon_idx > 0:
    prayer_v5 = prayer_v5[:colon_idx]

# Normalize both
indexer = LiturgyIndexer(verbose=False)
canonical_norm = indexer._full_normalize(canonical_v5)
prayer_v5_norm = indexer._full_normalize(prayer_v5)

output_file = Path(__file__).parent.parent / "output" / "char_comparison.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("VERSE 5 CHARACTER-BY-CHARACTER COMPARISON\n")
    f.write("="*70 + "\n\n")

    f.write("CANONICAL TEXT:\n")
    f.write(canonical_v5 + "\n\n")
    for i, char in enumerate(canonical_v5):
        f.write(f"{i:3d}: '{char}' U+{ord(char):04X}\n")

    f.write("\n" + "="*70 + "\n\n")

    f.write("PRAYER TEXT (extracted):\n")
    f.write(prayer_v5 + "\n\n")
    for i, char in enumerate(prayer_v5):
        f.write(f"{i:3d}: '{char}' U+{ord(char):04X}\n")

    f.write("\n" + "="*70 + "\n\n")

    f.write("NORMALIZED CANONICAL:\n")
    f.write(canonical_norm + "\n\n")
    for i, char in enumerate(canonical_norm):
        f.write(f"{i:3d}: '{char}' U+{ord(char):04X}\n")

    f.write("\n" + "="*70 + "\n\n")

    f.write("NORMALIZED PRAYER:\n")
    f.write(prayer_v5_norm + "\n\n")
    for i, char in enumerate(prayer_v5_norm):
        f.write(f"{i:3d}: '{char}' U+{ord(char):04X}\n")

    f.write("\n" + "="*70 + "\n\n")

    f.write(f"Canonical normalized length: {len(canonical_norm)}\n")
    f.write(f"Prayer normalized length: {len(prayer_v5_norm)}\n")
    f.write(f"Match: {canonical_norm == prayer_v5_norm}\n")

    if canonical_norm != prayer_v5_norm:
        f.write("\nDIFFERENCES:\n")
        max_len = max(len(canonical_norm), len(prayer_v5_norm))
        for i in range(max_len):
            c_char = canonical_norm[i] if i < len(canonical_norm) else '�'
            p_char = prayer_v5_norm[i] if i < len(prayer_v5_norm) else '�'
            if c_char != p_char:
                c_code = f"U+{ord(c_char):04X}" if c_char != '�' else "END"
                p_code = f"U+{ord(p_char):04X}" if p_char != '�' else "END"
                f.write(f"  Position {i}: canonical='{c_char}' ({c_code}), prayer='{p_char}' ({p_code})\n")

print(f"Character comparison written to {output_file}")
