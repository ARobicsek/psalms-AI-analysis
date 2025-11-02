#!/usr/bin/env python3
"""Check if Psalms are stored in liturgy.db."""

import sqlite3
from pathlib import Path

def check_liturgy_db():
    liturgy_db = Path(__file__).parent.parent / "data" / "liturgy.db"
    conn = sqlite3.connect(liturgy_db)
    cursor = conn.cursor()

    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables in liturgy.db:")
    for table in tables:
        print(f"  - {table[0]}")
    print()

    # Check total prayers
    cursor.execute("SELECT COUNT(*) FROM prayers")
    total = cursor.fetchone()[0]
    print(f"Total prayers: {total}")
    print()

    # Check if there are any prayers with "Psalm" in the title
    cursor.execute("""
        SELECT prayer_id, title FROM prayers
        WHERE title LIKE '%Psalm%' OR title LIKE '%Tehillim%'
        ORDER BY prayer_id
        LIMIT 10
    """)
    psalm_prayers = cursor.fetchall()
    if psalm_prayers:
        print("Prayers with 'Psalm' in title:")
        for prayer_id, title in psalm_prayers:
            print(f"  {prayer_id}: {title}")
    else:
        print("No prayers with 'Psalm' or 'Tehillim' in title found")
    print()

    # Check Prayer 251 and 574 specifically
    for pid in [251, 574]:
        cursor.execute("SELECT prayer_id, title, hebrew_text FROM prayers WHERE prayer_id = ?", (pid,))
        row = cursor.fetchone()
        if row:
            prayer_id, title, text = row
            print(f"Prayer {prayer_id}: {title}")
            if text:
                print(f"  Text length: {len(text)} chars")
                print(f"  First 100 chars: {text[:100]}")
            print()

    conn.close()

if __name__ == '__main__':
    check_liturgy_db()
