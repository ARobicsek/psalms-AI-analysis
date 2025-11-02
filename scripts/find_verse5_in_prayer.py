#!/usr/bin/env python3
"""Find verse 5 in prayer 574."""

import sqlite3
from pathlib import Path

# Get Prayer 574 text
liturgy_db = Path(__file__).parent.parent / "data" / "liturgy.db"
conn = sqlite3.connect(liturgy_db)
cursor = conn.cursor()

cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = 574")
prayer_text = cursor.fetchone()[0]
conn.close()

# Search for different variations of the first word
search_patterns = [
    "תַּעֲרֹךְ",
    "תַּעֲרֹךְ לפָנַי",
    "תַּעֲרֹךְ לְפָנַי",
    "תערך",  # Without vowels
    "שֻׁלְחָן נֶגֶד צֹרְרָי",  # Try the distinctive phrase
]

output_file = Path(__file__).parent.parent / "output" / "verse5_search.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("SEARCHING FOR VERSE 5 IN PRAYER 574\n")
    f.write("="*70 + "\n\n")

    for pattern in search_patterns:
        idx = prayer_text.find(pattern)
        f.write(f"Pattern: {pattern}\n")
        if idx >= 0:
            # Show context
            context_start = max(0, idx - 50)
            context_end = min(len(prayer_text), idx + len(pattern) + 100)
            context = prayer_text[context_start:context_end]
            f.write(f"  FOUND at position {idx}\n")
            f.write(f"  Context: ...{context}...\n")
        else:
            f.write(f"  NOT FOUND\n")
        f.write("\n")

    # Also search for the distinctive "שֻׁלְחָן נֶגֶד"
    f.write("\nSearching for complete verse 5 manually:\n")
    # Try to find "table before my enemies"
    idx = prayer_text.find("שֻׁלְחָן")
    if idx >= 0:
        context = prayer_text[idx-20:idx+150]
        f.write(f"Found 'שֻׁלְחָן' (table) at position {idx}\n")
        f.write(f"Context: {context}\n")

print(f"Search results written to {output_file}")
