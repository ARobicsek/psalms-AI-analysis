#!/usr/bin/env python3
"""Quick analysis of corpus text issues."""
import sqlite3
import re
from pathlib import Path

# Connect to database
conn = sqlite3.connect('database/tanakh.db')
conn.row_factory = sqlite3.Row

print("=== CORPUS TEXT ANALYSIS ===\n")

# Check for Hebrew dividers
cursor = conn.execute("SELECT COUNT(*) FROM verses WHERE hebrew LIKE '%׀%'")
pasuq_count = cursor.fetchone()[0]
print(f"1. Pasuq (verse divider): Found in {pasuq_count} verses")

cursor = conn.execute("SELECT COUNT(*) FROM verses WHERE hebrew LIKE '%{ס}%' OR hebrew LIKE '%{פ}%'")
peh_samech_count = cursor.fetchone()[0]
print(f"2. Peh/Samech markers: Found in {peh_samech_count} verses")

# Check for English footnotes
cursor = conn.execute("""
    SELECT COUNT(*) FROM verses
    WHERE english LIKE '%*%'
    OR english LIKE '%^%'
    OR english LIKE '%[_]%'
    OR english LIKE '% Cf.%'
    OR english LIKE '% Heb.%'
    OR english LIKE '% Emendation%'
""")
footnote_count = cursor.fetchone()[0]
print(f"3. English footnotes/notes: Found in {footnote_count} verses")

# Show example with footnote
cursor = conn.execute("""
    SELECT book_name, chapter, verse, english
    FROM verses
    WHERE english LIKE '%*%' OR english LIKE '% Emendation%'
    LIMIT 3
""")

print("\nExample with footnote:")
for row in cursor:
    print(f"\n{row['book_name']} {row['chapter']}:{row['verse']}")
    print(f"English: {row['english'][:200]}...")

conn.close()

print("\n=== RECOMMENDATIONS ===")
print("1. Remove pasuq (׀) - verse divider not needed for thematic search")
print("2. Remove peh/samech markers - these are parsha divisions")
print("3. Clean English text to remove all footnotes and translator notes")