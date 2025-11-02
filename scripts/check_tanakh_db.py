#!/usr/bin/env python3
"""Check tanakh.db structure and contents."""

import sqlite3
from pathlib import Path

def check_db():
    tanakh_db = Path(__file__).parent.parent / "data" / "tanakh.db"
    conn = sqlite3.connect(tanakh_db)
    cursor = conn.cursor()

    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables in tanakh.db:")
    for table in tables:
        print(f"  - {table[0]}")
    print()

    # Check verses table structure
    cursor.execute("PRAGMA table_info(verses)")
    cols = cursor.fetchall()
    print("verses table columns:")
    for col in cols:
        print(f"  {col[1]} ({col[2]})")
    print()

    # Check what books exist
    cursor.execute("SELECT DISTINCT book_name FROM verses")
    books = cursor.fetchall()
    print("Books in verses table:")
    for book in books:
        print(f"  - {book[0]}")
    print()

    # Check total verse count
    cursor.execute("SELECT COUNT(*) FROM verses")
    total = cursor.fetchone()[0]
    print(f"Total verses in database: {total}")
    print()

    # Check Psalm chapters that exist
    cursor.execute("""
        SELECT DISTINCT chapter FROM verses
        WHERE book_name = 'Psalms'
        ORDER BY chapter
        LIMIT 20
    """)
    chapters = [row[0] for row in cursor.fetchall()]
    print(f"First 20 Psalm chapters in database: {chapters}")

    conn.close()

if __name__ == '__main__':
    check_db()
