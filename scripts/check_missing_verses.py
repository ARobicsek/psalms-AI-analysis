#!/usr/bin/env python3
"""Check which verses are missing for Psalms 19 and 23."""

import sqlite3
from pathlib import Path

liturgy_db = Path(__file__).parent.parent / "data" / "liturgy.db"
conn = sqlite3.connect(liturgy_db)
cursor = conn.cursor()

print("="*70)
print("PSALM 23 IN PRAYER 574")
print("="*70)

# Get all matches for Psalm 23 in Prayer 574
cursor.execute("""
    SELECT psalm_verse_start, psalm_verse_end, match_type, confidence
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 23 AND prayer_id = 574
    ORDER BY psalm_verse_start, match_type DESC
""")

matches = cursor.fetchall()
for v_start, v_end, match_type, conf in matches:
    print(f"Verse {v_start}: {match_type} (conf={conf:.2f})")

# Check which verses have exact_verse matches
verse_set = set()
for v_start, v_end, match_type, conf in matches:
    if match_type == 'exact_verse':
        verse_set.add(v_start)

print(f"\nVerses with exact_verse: {sorted(verse_set)}")
print(f"Psalm 23 has 6 verses total")
missing = set(range(1, 7)) - verse_set
if missing:
    print(f"Missing verses: {sorted(missing)}")

print("\n" + "="*70)
print("PSALM 19 IN PRAYER 251")
print("="*70)

# Get all matches for Psalm 19 in Prayer 251
cursor.execute("""
    SELECT psalm_verse_start, psalm_verse_end, match_type, confidence
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 19 AND prayer_id = 251
    ORDER BY psalm_verse_start, match_type DESC
""")

matches = cursor.fetchall()
for v_start, v_end, match_type, conf in matches:
    print(f"Verse {v_start}: {match_type} (conf={conf:.2f})")

# Check which verses have exact_verse matches
verse_set = set()
for v_start, v_end, match_type, conf in matches:
    if match_type == 'exact_verse':
        verse_set.add(v_start)

print(f"\nVerses with exact_verse: {sorted(verse_set)}")
print(f"Psalm 19 has 15 verses total")
missing = set(range(1, 16)) - verse_set
if missing:
    print(f"Missing verses: {sorted(missing)}")

conn.close()
