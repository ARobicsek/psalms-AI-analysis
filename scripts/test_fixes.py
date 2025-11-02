"""Test the fixes for normalization, deduplication, and entire chapter detection."""
import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.liturgy.liturgy_indexer import LiturgyIndexer

print("=" * 80)
print("TESTING FIXES: Psalm 23 (should detect entire chapter)")
print("=" * 80)

indexer = LiturgyIndexer(verbose=True)

# Test Psalm 23
print("\n\nIndexing Psalm 23...")
result_23 = indexer.index_psalm(23)

print(f"\n\nPsalm 23 Results:")
print(f"  Total matches: {result_23['total_matches']}")
print(f"  Match breakdown:")
for match_type, count in result_23.get('match_details', {}).items():
    print(f"    {match_type}: {count}")

# Check prayer 574 specifically
import sqlite3
conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT match_type, COUNT(*)
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 23 AND prayer_id = 574
    GROUP BY match_type
""")

print(f"\n  Psalm 23 in Prayer 574 (Shabbat Kiddush):")
for match_type, count in cursor.fetchall():
    print(f"    {match_type}: {count}")

print("\n" + "=" * 80)
print("TESTING FIXES: Psalm 19 (should detect entire chapter)")
print("=" * 80)

# Test Psalm 19
print("\n\nIndexing Psalm 19...")
result_19 = indexer.index_psalm(19)

print(f"\n\nPsalm 19 Results:")
print(f"  Total matches: {result_19['total_matches']}")
print(f"  Match breakdown:")
for match_type, count in result_19.get('match_details', {}).items():
    print(f"    {match_type}: {count}")

# Check prayer 251 specifically
cursor.execute("""
    SELECT match_type, COUNT(*)
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 19 AND prayer_id = 251
    GROUP BY match_type
""")

print(f"\n  Psalm 19 in Prayer 251:")
for match_type, count in cursor.fetchall():
    print(f"    {match_type}: {count}")

conn.close()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
