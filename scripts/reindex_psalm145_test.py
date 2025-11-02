"""Reindex Psalm 145 to test two-pass matching fix for verse 6."""

import sys
sys.path.insert(0, '.')

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.liturgy.liturgy_indexer import LiturgyIndexer
import sqlite3

print("Reindexing Psalm 145 with two-pass matching (exact + fuzzy)...")
print()

indexer = LiturgyIndexer(verbose=True)
result = indexer.index_psalm(145)

print()
print("=" * 60)
print("Reindexing complete!")
print(f"Total matches: {result.get('total_matches', 0)}")
print()

# Check if Prayer 91 now has verse 6
conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT psalm_verse, liturgy_phrase_hebrew, match_type
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 145 AND prayer_id = 91
    ORDER BY psalm_verse
''')

matches = cursor.fetchall()
verses_found = sorted(set(m[0] for m in matches))

print("Prayer 91 (Ashrei) now matches these Psalm 145 verses:")
print(f"  {verses_found}")
print()

if 6 in verses_found:
    print("✓ SUCCESS! Verse 6 is now indexed for Prayer 91")
    # Show the match
    cursor.execute('''
        SELECT liturgy_phrase_hebrew, match_type
        FROM psalms_liturgy_index
        WHERE psalm_chapter = 145 AND prayer_id = 91 AND psalm_verse = 6
        LIMIT 1
    ''')
    verse6_match = cursor.fetchone()
    if verse6_match:
        liturgy_text, match_type = verse6_match
        print(f"  Match type: {match_type}")
        print(f"  Liturgy text: {liturgy_text[:80]}...")
else:
    print("✗ FAILED: Verse 6 is still missing from Prayer 91")
    missing = set(range(1, 22)) - set(verses_found)
    print(f"  Missing verses: {sorted(missing)}")

conn.close()
