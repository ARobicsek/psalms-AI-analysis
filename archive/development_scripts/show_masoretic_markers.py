#!/usr/bin/env python3
"""Show actual Masoretic markers in the text."""

import sqlite3
from pathlib import Path

# Connect to database
db_path = Path(__file__).parent.parent / "database" / "tanakh.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get some verses with markers
cursor.execute("""
    SELECT book_name, chapter, verse, hebrew, english
    FROM verses
    WHERE (hebrew LIKE '%ס%' OR hebrew LIKE '%פ%')
    AND book_name = 'Genesis'
    ORDER BY chapter, verse
    LIMIT 10
""")

rows = cursor.fetchall()

print("Masoretic Section Markers in Genesis")
print("=" * 60)
print("\nס (Samekh) = closed section (paragraph break)")
print("פ (Peh) = open section (new line)")
print("-" * 60)

for book, chapter, verse, hebrew, english in rows[:5]:
    print(f"\n{book} {chapter}:{verse}")
    print("-" * 30)

    # Find marker positions
    markers = []
    for i, char in enumerate(hebrew):
        if char == 'ס':
            markers.append(('ס', i))
        elif char == 'פ':
            markers.append(('פ', i))

    # Show Hebrew with markers highlighted
    print(f"Hebrew: {hebrew}")
    if markers:
        print(f"Markers at: {', '.join([f'{m[0]} (position {m[1]})' for m in markers])}")

    # Show first part of English
    eng_words = english.split()[:15]
    print(f"English: {' '.join(eng_words)}...")

# Show statistics
cursor.execute("""
    SELECT
        SUM(CASE WHEN hebrew LIKE '%ס%' THEN 1 ELSE 0 END) as samekh_count,
        SUM(CASE WHEN hebrew LIKE '%פ%' THEN 1 ELSE 0 END) as peh_count,
        COUNT(*) as total_verses
    FROM verses
    WHERE book_name != 'Psalms'
""")

stats = cursor.fetchone()
print("\n" + "=" * 60)
print("Masoretic Marker Statistics (Tanakh, excluding Psalms):")
print(f"  Verses with Samekh (ס): {stats[0]:,}")
print(f"  Verses with Peh (פ): {stats[1]:,}")
print(f"  Total verses: {stats[2]:,}")
print(f"  Percentage with markers: {(stats[0] + stats[1]) / stats[2] * 100:.1f}%")

conn.close()