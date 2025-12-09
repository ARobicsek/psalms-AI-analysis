#!/usr/bin/env python3
"""Check for actual Masoretic section markers."""

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "database" / "tanakh.db"
conn = sqlite3.connect(str(db_path))
c = conn.cursor()

print("CHECKING FOR MASORETIC SECTION MARKERS")
print("=" * 60)

# Check for proper Masoretic markers (with braces)
c.execute('SELECT COUNT(*) FROM verses WHERE hebrew LIKE "%{פ}%" OR hebrew LIKE "%{ס}%"')
count_with_braces = c.fetchone()[0]
print(f"Verses with {{פ}} or {{ס}} markers (with braces): {count_with_braces}")

if count_with_braces > 0:
    c.execute('SELECT book_name, chapter, verse, hebrew FROM verses WHERE hebrew LIKE "%{פ}%" OR hebrew LIKE "%{ס}%" LIMIT 5')
    print("\nExamples:")
    for row in c.fetchall():
        print(f"  {row[0]} {row[1]}:{row[2]}")

# Check for alternative formats
print("\nChecking for other marker formats...")
print("-" * 40)

# 1. Standalone letters at end of verse
c.execute("""
    SELECT COUNT(*)
    FROM verses
    WHERE book_name != 'Psalms'
    AND (hebrew LIKE '% ס' OR hebrew LIKE '% פ' OR hebrew LIKE '%ס%' OR hebrew LIKE '%פ%')
""")
count_standalone = c.fetchone()[0]
print(f"Verses with standalone ס or פ: {count_standalone}")

# 2. Check if markers are encoded differently
# Look at Genesis 1 to see pattern
print("\nAnalyzing Genesis 1 pattern:")
print("-" * 40)

c.execute("""
    SELECT verse, hebrew, LENGTH(hebrew) as length
    FROM verses
    WHERE book_name = 'Genesis' AND chapter = 1
    ORDER BY verse
    LIMIT 10
""")

verses = c.fetchall()
for verse, hebrew, length in verses:
    # Check last few characters
    last_chars = hebrew[-5:] if length >= 5 else hebrew

    # Check for any markers in verse
    has_peh = 'פ' in hebrew
    has_samekh = 'ס' in hebrew

    # Count occurrences (excluding normal words)
    # This is approximate - we can't easily distinguish markers from letters
    peh_count = hebrew.count('פ')
    samekh_count = hebrew.count('ס')

    print(f"Genesis 1:{verse:2d} | Length: {length:3d} | פ: {peh_count:2d} | ס: {samekh_count:2d}")

# Check what our chunking actually did
print("\n" + "=" * 60)
print("CONCLUSION:")
print("-" * 40)
print("The database likely does NOT contain proper Masoretic section markers.")
print("The 'פ' and 'ס' characters found are part of normal Hebrew words.")
print("")
print("This means our 'Masoretic marker chunking' is actually finding verses")
print("that happen to contain these letters, NOT true section boundaries!")
print("")
print("Recommendation: Use sliding window chunking instead, which is more")
print("honest about not having traditional section breaks.")

conn.close()