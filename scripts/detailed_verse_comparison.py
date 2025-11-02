#!/usr/bin/env python3
"""Detailed comparison of Psalm 23:5-6 between canonical and liturgical."""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.liturgy.liturgy_indexer import LiturgyIndexer

# Get canonical verses
tanakh_db = Path(__file__).parent.parent / "database" / "tanakh.db"
conn = sqlite3.connect(tanakh_db)
cursor = conn.cursor()

cursor.execute("""
    SELECT verse, hebrew FROM verses
    WHERE book_name = 'Psalms' AND chapter = 23 AND verse IN (5, 6)
    ORDER BY verse
""")
verses = cursor.fetchall()
conn.close()

# Get prayer text
liturgy_db = Path(__file__).parent.parent / "data" / "liturgy.db"
conn2 = sqlite3.connect(liturgy_db)
cursor2 = conn2.cursor()

cursor2.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = 574")
prayer_text = cursor2.fetchone()[0]
conn2.close()

# Initialize indexer for normalization
indexer = LiturgyIndexer(verbose=False)

output_file = Path(__file__).parent.parent / "output" / "detailed_verse_comparison.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    for verse_num, canonical_text in verses:
        f.write("="*70 + "\n")
        f.write(f"VERSE {verse_num}\n")
        f.write("="*70 + "\n\n")

        f.write(f"Canonical text:\n{canonical_text}\n\n")

        # Show each character with its Unicode codepoint
        f.write("Canonical characters:\n")
        for i, char in enumerate(canonical_text[:50]):  # First 50 chars
            f.write(f"  {i:2d}: '{char}' (U+{ord(char):04X})\n")

        canonical_norm = indexer._full_normalize(canonical_text)
        f.write(f"\nCanonical normalized:\n{canonical_norm}\n\n")

        # Check if it's in the prayer
        prayer_norm = indexer._full_normalize(prayer_text)
        found = canonical_norm in prayer_norm

        f.write(f"Found in prayer (normalized): {found}\n\n")

        if not found:
            # Try to find what part of the prayer might be this verse
            # Search for the first few words
            words = canonical_text.split()[:5]
            f.write("Searching for first 5 words in prayer:\n")
            for w in words:
                w_norm = indexer._full_normalize(w)
                if w_norm in prayer_norm:
                    f.write(f"  '{w}' (normalized: '{w_norm}') - FOUND\n")
                else:
                    f.write(f"  '{w}' (normalized: '{w_norm}') - NOT FOUND\n")

        f.write("\n")

print(f"Detailed comparison written to {output_file}")
