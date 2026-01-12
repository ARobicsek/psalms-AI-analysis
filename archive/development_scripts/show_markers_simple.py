#!/usr/bin/env python3
"""Show Masoretic markers using ASCII representation."""

import sqlite3
from pathlib import Path

# Connect to database
db_path = Path(__file__).parent.parent / "database" / "tanakh.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get some verses with markers from Genesis
cursor.execute("""
    SELECT chapter, verse, hebrew, english
    FROM verses
    WHERE (hebrew LIKE '%ס%' OR hebrew LIKE '%פ%')
    AND book_name = 'Genesis'
    ORDER BY chapter, verse
    LIMIT 5
""")

rows = cursor.fetchall()

print("Masoretic Section Markers in Genesis")
print("=" * 60)
print("\nSamekh (ס) = closed section (like paragraph break)")
print("Peh (פ) = open section (like new line)")
print("-" * 60)

for chapter, verse, hebrew, english in rows:
    print(f"\nGenesis {chapter}:{verse}")
    print("-" * 30)

    # Count markers
    samekh_count = hebrew.count('ס')
    peh_count = hebrew.count('פ')

    print(f"Markers found: {samekh_count} Samekh, {peh_count} Peh")

    # Show character positions (first 100 chars)
    print(f"\nFirst 100 chars of Hebrew text:")
    print(hebrew[:100])

    # Show English
    print(f"\nEnglish (first 100 chars):")
    print(english[:100] + "...")

print("\n" + "=" * 60)

# Statistics for entire Tanakh
cursor.execute("""
    SELECT
        SUM(CASE WHEN hebrew LIKE '%ס%' THEN 1 ELSE 0 END) as samekh_count,
        SUM(CASE WHEN hebrew LIKE '%פ%' THEN 1 ELSE 0 END) as peh_count
    FROM verses
    WHERE book_name != 'Psalms'
""")

stats = cursor.fetchone()
print(f"\nTotal verses with markers (excluding Psalms):")
print(f"  Samekh markers: {stats[0]:,}")
print(f"  Peh markers: {stats[1]:,}")
print(f"  Total marked verses: {stats[0] + stats[1]:,}")

# Example of chunking
print("\n" + "=" * 60)
print("Example of Masoretic chunking:")
print("Verses are grouped until a marker is found, then a new chunk starts.")
print("\nExample from Genesis 1:")
print("  Gen 1:1-2 -> Chunk 1 (no marker after v.1, marker after v.2)")
print("  Gen 1:3-5 -> Chunk 2 (marker after v.5)")
print("  Gen 1:6-8 -> Chunk 3 (marker after v.8)")

conn.close()