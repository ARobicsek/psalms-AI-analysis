#!/usr/bin/env python3
"""Extract all variants of tet-ayin-resh-kaf from prayer 574."""

import sqlite3
import unicodedata
from pathlib import Path

# Get Prayer 574 text
liturgy_db = Path(__file__).parent.parent / "data" / "liturgy.db"
conn = sqlite3.connect(liturgy_db)
cursor = conn.cursor()
cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = 574")
prayer_text = cursor.fetchone()[0]
conn.close()

# Look for the letter combination ת-ע-ר (tet-ayin-resh)
output_file = Path(__file__).parent.parent / "output" / "variants_search.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("SEARCHING FOR תער COMBINATIONS IN PRAYER 574\n")
    f.write("="*70 + "\n\n")

    # Search for ת followed by ע
    for i in range(len(prayer_text) - 10):
        if prayer_text[i] == 'ת':
            # Check next few characters
            snippet = prayer_text[i:i+20]
            # Check if it contains ער after ת
            if 'ער' in snippet[1:5]:
                f.write(f"Position {i}: {snippet}\n")
                f.write(f"  Chars: ")
                for j, char in enumerate(snippet[:10]):
                    f.write(f"'{char}'(U+{ord(char):04X}) ")
                f.write("\n\n")

    # Also look for "Mizm or leDavid" - the psalm header
    f.write("\n" + "="*70 + "\n")
    f.write("SEARCHING FOR PSALM HEADER\n\n")

    # Search for מזמור
    idx = prayer_text.find("מִזְמוֹר")
    if idx >= 0:
        context = prayer_text[idx:idx+300]
        f.write(f"Found 'מִזְמוֹר' at position {idx}\n")
        f.write(f"Text: {context}\n\n")

    idx = prayer_text.find("מזמור")
    if idx >= 0:
        context = prayer_text[idx:idx+300]
        f.write(f"Found 'מזמור' (no vowels) at position {idx}\n")
        f.write(f"Text: {context}\n\n")

print(f"Variants search written to {output_file}")
