#!/usr/bin/env python3
"""Show exactly what's in the database for Genesis 1:2."""

import sqlite3
from pathlib import Path

# Database location
db_path = Path(__file__).parent.parent / "database" / "tanakh.db"
print(f"Database location: {db_path}")
print(f"Full path: {db_path.absolute()}")
print()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get Genesis 1:2
cursor.execute("""
    SELECT verse, hebrew, english
    FROM verses
    WHERE book_name = 'Genesis'
    AND chapter = 1
    AND verse = 2
""")
result = cursor.fetchone()

if result:
    verse, hebrew, english = result

    print("GENESIS 1:2 FROM DATABASE")
    print("=" * 60)
    print(f"Verse: {verse}")
    print()

    print("Hebrew text (last 20 characters):")
    print("-" * 40)

    # Show last 20 characters with their positions and Unicode codes
    start_pos = max(0, len(hebrew) - 20)
    for i in range(start_pos, len(hebrew)):
        char = hebrew[i]
        hex_code = f"U+{ord(char):04X}"
        char_name = {
            '\u05e1': "SAMEKH",
            '\u05e4': "PEH",
            '\u05c3': "SOF PASUQ (verse punctuation)",
            '\u05d0': "ALEF",
            '\u05d1': "BET",
            '\u05d2': "GIMEL",
            '\u05d3': "DALET",
            '\u05d4': "HE",
            '\u05d5': "VAV",
            '\u05d6': "ZAYIN",
            '\u05d7': "HET",
            '\u05d8': "TET",
            '\u05d9': "YOD",
            '\u05da': "FINAL KAF",
            '\u05db': "KAF",
            '\u05dc': "LAMED",
            '\u05dd': "FINAL MEM",
            '\u05de': "MEM",
            '\u05df': "FINAL NUN",
            '\u05e0': "NUN",
            '\u05e3': "FINAL PEH",
            '\u05e4': "PEH",
            '\u05e5': "FINAL TSADE",
            '\u05e6': "TSADE",
            '\u05e7': "QOF",
            '\u05e8': "RESH",
            '\u05e9': "SHIN",
            '\u05ea': "TAV",
            '\u200f': "RIGHT-TO-LEFT MARK",
            '\u200e': "LEFT-TO-RIGHT MARK"
        }.get(hex_code, "UNKNOWN")

        print(f"Position {i:3d}: {hex_code} - {char_name}")

    print()
    print("Full Hebrew text (as bytes):")
    print(hebrew.encode('utf-8'))
    print()
    print("English translation (first 200 chars):")
    print(english[:200] + "..." if len(english) > 200 else english)

    # Check specifically for markers
    print()
    print("MARKER CHECK:")
    print("-" * 40)
    has_samekh = '\u05e1' in hebrew
    has_peh = '\u05e4' in hebrew

    print(f"Contains Samekh (U+05E1): {has_samekh}")
    print(f"Contains Peh (U+05E4): {has_peh}")

    # Show where markers are
    if has_peh:
        positions = [i for i, char in enumerate(hebrew) if char == '\u05e4']
        print(f"Peh positions: {positions}")

    if has_samekh:
        positions = [i for i, char in enumerate(hebrew) if char == '\u05e1']
        print(f"Samekh positions: {positions}")

# Also show database info
print()
print("DATABASE INFO:")
print("-" * 40)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tables: {[t[0] for t in tables]}")
cursor.execute("SELECT COUNT(*) FROM verses")
total_verses = cursor.fetchone()[0]
print(f"Total verses in database: {total_verses:,}")

conn.close()