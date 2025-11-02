#!/usr/bin/env python3
"""Check specific prayers 251 and 574."""

import sqlite3
from pathlib import Path

liturgy_db = Path(__file__).parent.parent / "data" / "liturgy.db"
conn = sqlite3.connect(liturgy_db)
cursor = conn.cursor()

for pid in [251, 574]:
    cursor.execute("""
        SELECT prayer_id, prayer_name, sefaria_ref, hebrew_text
        FROM prayers WHERE prayer_id = ?
    """, (pid,))
    row = cursor.fetchone()
    if row:
        prayer_id, name, ref, text = row
        try:
            print(f"Prayer {prayer_id}:")
            print(f"  Name: {name}")
            print(f"  Sefaria ref: {ref}")
            if text:
                print(f"  Text length: {len(text)} chars")
                print(f"  Word count: {len(text.split())}")
                print(f"  First 150 chars: {text[:150]}")
            print()
        except UnicodeEncodeError:
            print(f"Prayer {prayer_id}:")
            print(f"  Name: {name}")
            print(f"  Sefaria ref: {ref}")
            if text:
                print(f"  Text length: {len(text)} chars")
                print(f"  Word count: {len(text.split())}")
                print(f"  [Hebrew text - encoding issue]")
            print()

conn.close()
