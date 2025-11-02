"""Check if Psalm 145 is really complete in Prayer 91."""

import sqlite3
import sys
sys.path.insert(0, '.')
from src.liturgy.liturgy_indexer import LiturgyIndexer

# Initialize indexer for normalization
indexer = LiturgyIndexer(verbose=False)

# Connect to databases
liturgy_conn = sqlite3.connect('data/liturgy.db')
liturgy_cursor = liturgy_conn.cursor()

tanakh_conn = sqlite3.connect('database/tanakh.db')
tanakh_cursor = tanakh_conn.cursor()

prayer_id = 91

print("CHECKING PRAYER 91 FOR COMPLETE PSALM 145")
print("=" * 80)

# Get prayer text
liturgy_cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id=?", (prayer_id,))
prayer_result = liturgy_cursor.fetchone()

if not prayer_result:
    print(f"Prayer {prayer_id} not found!")
    exit(1)

prayer_text = prayer_result[0]
print(f"\nPrayer {prayer_id} length: {len(prayer_text)} chars, {len(prayer_text.split())} words")

# Normalize prayer text
normalized_prayer = indexer._full_normalize(prayer_text)
print(f"Normalized length: {len(normalized_prayer)} chars, {len(normalized_prayer.split())} words\n")

# Get all 21 verses of Psalm 145
tanakh_cursor.execute("""
    SELECT verse, hebrew FROM verses
    WHERE book_name='Psalms' AND chapter=145
    ORDER BY verse
""")

verses = tanakh_cursor.fetchall()
print(f"Psalm 145 has {len(verses)} verses\n")

# Check each verse
print("Checking which verses are in the prayer:")
print("-" * 80)

found_verses = []
missing_verses = []

for verse_num, verse_text in verses:
    normalized_verse = indexer._full_normalize(verse_text)

    if normalized_verse in normalized_prayer:
        found_verses.append(verse_num)
        print(f"  [YES] Verse {verse_num:2d}: FOUND")
    else:
        missing_verses.append(verse_num)
        print(f"  [NO]  Verse {verse_num:2d}: NOT FOUND")
        # Check partial match
        verse_words = normalized_verse.split()
        if len(verse_words) > 3:
            # Try first half
            half_phrase = ' '.join(verse_words[:len(verse_words)//2])
            if half_phrase in normalized_prayer:
                print(f"      (but first half found)")

print("\n" + "=" * 80)
print(f"Summary: {len(found_verses)}/21 verses found")
if missing_verses:
    print(f"Missing verses: {missing_verses}")
else:
    print("ALL VERSES PRESENT!")

# Check current index
print("\n" + "=" * 80)
print("Current index for Prayer 91 - Psalm 145:")
liturgy_cursor.execute("""
    SELECT match_type, psalm_verse_start, psalm_verse_end
    FROM psalms_liturgy_index
    WHERE prayer_id=? AND psalm_chapter=145
    ORDER BY psalm_verse_start
""", (prayer_id,))

current_matches = liturgy_cursor.fetchall()
for match_type, vs, ve in current_matches:
    if vs == ve:
        print(f"  {match_type:15} Verse {vs}")
    else:
        print(f"  {match_type:15} Verses {vs}-{ve}")

liturgy_conn.close()
tanakh_conn.close()
