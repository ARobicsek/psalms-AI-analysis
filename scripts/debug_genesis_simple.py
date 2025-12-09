#!/usr/bin/env python3
"""Debug Genesis 1 markers to understand chunking."""

import sqlite3
from pathlib import Path

# Connect to database
db_path = Path(__file__).parent.parent / "database" / "tanakh.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("DEBUGGING GENESIS 1 MARKERS")
print("=" * 60)

# Get Genesis 1 verses
cursor.execute("""
    SELECT chapter, verse, hebrew, english
    FROM verses
    WHERE book_name = 'Genesis'
    AND chapter = 1
    ORDER BY verse
""")

verses = cursor.fetchall()

print("\nChecking each verse for markers:")
print("-" * 40)

chunks = []
current_chunk = []
chunk_num = 0

for chapter, verse, hebrew, english in verses:
    # Check for markers
    has_samekh = 'ס' in hebrew
    has_peh = 'פ' in hebrew

    # Add to current chunk
    current_chunk.append(verse)

    print(f"\nGenesis {chapter}:{verse}")
    print(f"  Marker present: {'YES' if has_samekh or has_peh else 'NO'}")

    if has_samekh:
        print(f"  Type: Samekh (closed section)")
    if has_peh:
        print(f"  Type: Peh (open section)")

    # Show Hebrew last character
    if hebrew:
        print(f"  Hebrew ends with: '{hebrew[-10:]}'")

    # If marker found, end the chunk
    if has_samekh or has_peh:
        chunk_num += 1
        verse_range = f"{current_chunk[0]}-{verse}" if len(current_chunk) > 1 else verse
        print(f"  >>> END OF CHUNK {chunk_num}: Genesis 1:{verse_range}")
        chunks.append(current_chunk.copy())
        current_chunk = []

# Add any remaining verses
if current_chunk:
    chunk_num += 1
    verse_range = f"{current_chunk[0]}-{current_chunk[-1]}" if len(current_chunk) > 1 else current_chunk[0]
    print(f"\n  >>> END OF CHUNK {chunk_num}: Genesis 1:{verse_range}")
    chunks.append(current_chunk)

# Summary
print("\n" + "=" * 60)
print("SUMMARY OF GENESIS 1 CHUNKING:")
print("-" * 40)
for i, chunk in enumerate(chunks, 1):
    if len(chunk) == 1:
        print(f"Chunk {i}: Genesis 1:{chunk[0]} (1 verse)")
    else:
        print(f"Chunk {i}: Genesis 1:{chunk[0]}-{chunk[-1]} ({len(chunk)} verses)")

conn.close()