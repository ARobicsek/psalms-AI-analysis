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
    SELECT chapter, verse, hebrew
    FROM verses
    WHERE book_name = 'Genesis'
    AND chapter = 1
    ORDER BY verse
""")

verses = cursor.fetchall()

print("\nChecking each verse for markers:")
print("-" * 40)

for chapter, verse, hebrew in verses:
    # Check for markers
    has_samekh = 'ס' in hebrew
    has_peh = 'פ' in hebrew

    # Get last few characters
    last_10 = hebrew[-10:] if len(hebrew) > 10 else hebrew

    print(f"\nGenesis {chapter}:{verse}")
    print(f"Has samekh (ס): {has_samekh}")
    print(f"Has peh (פ): {has_peh}")
    print(f"Last 10 chars: {last_10}")

    # If there's a marker, show its position
    if has_peh:
        for i, char in enumerate(hebrew):
            if char == 'פ':
                print(f"  Peh found at position {i} (0-based)")

# Now show the actual chunks created
print("\n" + "=" * 60)
print("ACTUAL CHUNKS CREATED FOR GENESIS 1:")
print("-" * 40)

# Load the Masoretic corpus
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from thematic.corpus_builder import load_corpus

corpus_dir = Path(__file__).parent.parent / "data" / "thematic_corpus_masoretic"
chunks = list(load_corpus(str(corpus_dir)))

# Get Genesis chunks
genesis_chunks = [c for c in chunks if c.book == "Genesis" and c.start_chapter == 1][:5]

for i, chunk in enumerate(genesis_chunks, 1):
    print(f"\nChunk {i}: {chunk.reference}")
    print(f"  Verses: {chunk.verse_count}")
    print(f"  Start: {chunk.start_chapter}:{chunk.start_verse}")
    print(f"  End: {chunk.end_chapter}:{chunk.end_verse}")

conn.close()