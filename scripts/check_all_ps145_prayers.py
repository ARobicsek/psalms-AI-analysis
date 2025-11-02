"""Check which prayers actually have complete Psalm 145."""

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

# Get all 21 verses of Psalm 145
tanakh_cursor.execute("""
    SELECT verse, hebrew FROM verses
    WHERE book_name='Psalms' AND chapter=145
    ORDER BY verse
""")
verses = tanakh_cursor.fetchall()

# Prayers to check
prayer_ids = [107, 91, 900, 801, 736]

print("CHECKING WHICH PRAYERS HAVE COMPLETE PSALM 145")
print("=" * 80)

for prayer_id in prayer_ids:
    # Get prayer text
    liturgy_cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id=?", (prayer_id,))
    prayer_result = liturgy_cursor.fetchone()

    if not prayer_result:
        print(f"\nPrayer {prayer_id}: NOT FOUND in database")
        continue

    prayer_text = prayer_result[0]
    normalized_prayer = indexer._full_normalize(prayer_text)

    # Check each verse
    found_verses = []
    missing_verses = []

    for verse_num, verse_text in verses:
        normalized_verse = indexer._full_normalize(verse_text)

        if normalized_verse in normalized_prayer:
            found_verses.append(verse_num)
        else:
            missing_verses.append(verse_num)

    # Print summary
    print(f"\nPrayer {prayer_id}: {len(found_verses)}/21 verses", end="")
    if len(found_verses) == 21:
        print(" - COMPLETE!")
    else:
        print(f" - MISSING: {missing_verses}")

liturgy_conn.close()
tanakh_conn.close()

print("\n" + "=" * 80)
