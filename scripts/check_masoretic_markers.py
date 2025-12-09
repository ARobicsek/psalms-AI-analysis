#!/usr/bin/env python3
"""Check for Masoretic section markers in the database."""

import sqlite3
from pathlib import Path

# Connect to database
db_path = Path(__file__).parent.parent / "database" / "tanakh.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Look for verses with Masoretic markers (samekh ס for closed, peh פ for open)
cursor.execute("""
    SELECT book_name, chapter, verse, hebrew
    FROM verses
    WHERE hebrew LIKE '%ס%' OR hebrew LIKE '%פ%'
    ORDER BY book_name, chapter, verse
    LIMIT 20
""")

results = cursor.fetchall()
print(f"Found {len(results)} verses with Masoretic markers (first 20):")
print()

for book, chapter, verse, hebrew in results:
    # Find position of markers
    sam_pos = hebrew.find('ס')
    peh_pos = hebrew.find('פ')

    markers = []
    if sam_pos >= 0:
        markers.append(f"samekh(closed) at pos {sam_pos}")
    if peh_pos >= 0:
        markers.append(f"peh(open) at pos {peh_pos}")

    print(f"{book} {chapter}:{verse} - {', '.join(markers)}")

# Count total markers
cursor.execute("""
    SELECT
        COUNT(CASE WHEN hebrew LIKE '%ס%' THEN 1 END) as samekh_count,
        COUNT(CASE WHEN hebrew LIKE '%פ%' THEN 1 END) as peh_count,
        COUNT(*) as total_verses
    FROM verses
    WHERE book_name != 'Psalms'
""")

stats = cursor.fetchone()
print(f"\nMasoretic Marker Statistics:")
print(f"  Samekh (closed sections): {stats[0]}")
print(f"  Peh (open sections): {stats[1]}")
print(f"  Total verses (non-Psalms): {stats[2]}")

conn.close()