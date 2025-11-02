#!/usr/bin/env python3
"""Test Psalm 23 only."""

import sys
sys.path.insert(0, "c:/Users/ariro/OneDrive/Documents/Psalms")

from src.liturgy.liturgy_indexer import LiturgyIndexer

print("Indexing Psalm 23...")
indexer = LiturgyIndexer(verbose=False)  # verbose=False to avoid encoding issues
result = indexer.index_psalm(23)

print("\n" + "="*70)
print("RESULTS")
print("="*70)
print(f"Total matches: {result.get('total_matches', 0)}")
if 'match_details' in result:
    for match_type, count in result['match_details'].items():
        print(f"  {match_type}: {count}")

# Check Prayer 574 specifically
import sqlite3
conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT match_type, COUNT(*)
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 23 AND prayer_id = 574
    GROUP BY match_type
""")

print("\nPsalm 23 in Prayer 574:")
results = cursor.fetchall()
if results:
    for match_type, count in results:
        print(f"  {match_type}: {count}")
else:
    print("  No matches found")

conn.close()
