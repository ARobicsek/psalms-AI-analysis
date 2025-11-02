#!/usr/bin/env python3
"""Check verse counts for Psalms 19 and 23."""

import sqlite3
from pathlib import Path

def check_verse_counts():
    tanakh_db = Path(__file__).parent.parent / "data" / "tanakh.db"
    conn = sqlite3.connect(tanakh_db)
    cursor = conn.cursor()

    for psalm in [19, 23]:
        cursor.execute("""
            SELECT COUNT(*), MIN(verse), MAX(verse)
            FROM verses
            WHERE book_name = 'Psalms' AND chapter = ?
        """, (psalm,))
        count, min_v, max_v = cursor.fetchone()
        print(f"Psalm {psalm}: {count} verses (verse {min_v} to {max_v})")

        # Show all verse numbers
        cursor.execute("""
            SELECT verse FROM verses
            WHERE book_name = 'Psalms' AND chapter = ?
            ORDER BY verse
        """, (psalm,))
        verses = [row[0] for row in cursor.fetchall()]
        print(f"  Verses: {verses}")
        print()

    conn.close()

if __name__ == '__main__':
    check_verse_counts()
