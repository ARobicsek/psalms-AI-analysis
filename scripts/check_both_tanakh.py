#!/usr/bin/env python3
"""Check both tanakh.db files."""

import sqlite3
from pathlib import Path

for db_path in ["data/tanakh.db", "database/tanakh.db"]:
    full_path = Path(__file__).parent.parent / db_path
    if not full_path.exists():
        print(f"{db_path}: NOT FOUND")
        continue

    conn = sqlite3.connect(full_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM verses")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verses WHERE book_name = 'Psalms'")
    psalm_verses = cursor.fetchone()[0]

    # Check Psalms 19 and 23 specifically
    cursor.execute("SELECT COUNT(*) FROM verses WHERE book_name = 'Psalms' AND chapter IN (19, 23)")
    psalms_19_23 = cursor.fetchone()[0]

    # Get all psalm chapters
    cursor.execute("SELECT DISTINCT chapter FROM verses WHERE book_name = 'Psalms' ORDER BY chapter")
    chapters = [row[0] for row in cursor.fetchall()]

    print(f"\n{db_path}:")
    print(f"  Total verses: {total}")
    print(f"  Psalm verses: {psalm_verses}")
    print(f"  Psalms 19+23 verses: {psalms_19_23}")
    if len(chapters) < 20:
        print(f"  Psalm chapters: {chapters}")
    else:
        print(f"  Psalm chapters: {len(chapters)} chapters (1-{max(chapters)})")

    conn.close()
