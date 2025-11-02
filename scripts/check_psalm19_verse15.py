#!/usr/bin/env python3
"""Check why Psalm 19:15 isn't matching as exact_verse."""

import sqlite3
from pathlib import Path

def check_verse():
    # Get Psalm 19:15 from tanakh.db
    tanakh_db = Path(__file__).parent.parent / "data" / "tanakh.db"
    conn = sqlite3.connect(tanakh_db)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT hebrew FROM verses
        WHERE book_name = 'Psalms' AND chapter = 19 AND verse = 15
    """)
    verse_15 = cursor.fetchone()
    conn.close()

    if verse_15:
        print(f"Psalm 19:15 text:")
        print(f"  {verse_15[0]}")
        print(f"\nWord count: {len(verse_15[0].split())}")
    else:
        print("Psalm 19:15 not found!")

if __name__ == '__main__':
    check_verse()
