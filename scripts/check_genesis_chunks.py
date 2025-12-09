#!/usr/bin/env python3
"""Check actual Genesis chunks from Masoretic corpus."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from thematic.corpus_builder import load_corpus

# Load corpus
corpus_dir = Path(__file__).parent.parent / "data" / "thematic_corpus_masoretic"
chunks = list(load_corpus(str(corpus_dir)))

# Get Genesis chunks
genesis_chunks = [c for c in chunks if c.book == "Genesis" and c.start_chapter == 1][:10]

print("FIRST 10 CHUNKS FROM GENESIS 1 (Masoretic Markers):")
print("=" * 60)

for i, chunk in enumerate(genesis_chunks, 1):
    print(f"\nChunk {i}: {chunk.reference}")
    print(f"  Verses: {chunk.verse_count}")
    print(f"  Chapter:Verse range: {chunk.start_chapter}:{chunk.start_verse} - {chunk.end_chapter}:{chunk.end_verse}")

    # Show first 50 characters of English
    eng_preview = chunk.english_text.replace('\n', ' ')[:100]
    print(f"  Text preview: {eng_preview}...")

# Now let's manually check the Hebrew text to see if there's really a marker
print("\n" + "=" * 60)
print("MANUAL CHECK OF GENESIS 1:1-2:")
print("-" * 40)

import sqlite3
db_path = Path(__file__).parent.parent / "database" / "tanakh.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT verse, hebrew
    FROM verses
    WHERE book_name = 'Genesis'
    AND chapter = 1
    AND verse IN (1, 2)
    ORDER BY verse
""")

for verse, hebrew in cursor.fetchall():
    # Check if marker is anywhere in text
    has_marker = 'ס' in hebrew or 'פ' in hebrew
    print(f"\nGenesis 1:{verse}")
    print(f"  Has marker: {has_marker}")

    # Check last character
    if hebrew:
        last_char = hebrew[-1]
        print(f"  Last char is: {last_char} ({'SAMEKH' if last_char == 'ס' else 'PEH' if last_char == 'פ' else 'NOT A MARKER'})")

conn.close()