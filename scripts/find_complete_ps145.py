"""Find all prayers that have complete Psalm 145."""

import sqlite3
import sys
sys.path.insert(0, '.')
from src.liturgy.liturgy_indexer import LiturgyIndexer

print("FINDING ALL PRAYERS WITH COMPLETE PSALM 145")
print("=" * 80)

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
verse_dict = {v[0]: v[1] for v in verses}

# Get all prayers that have at least one match for Psalm 145
liturgy_cursor.execute("""
    SELECT DISTINCT prayer_id
    FROM psalms_liturgy_index
    WHERE psalm_chapter=145
    ORDER BY prayer_id
""")
prayer_ids_with_matches = [row[0] for row in liturgy_cursor.fetchall()]

print(f"Checking {len(prayer_ids_with_matches)} prayers with Psalm 145 matches...\n")

complete_prayers = []
almost_complete = []

for prayer_id in prayer_ids_with_matches:
    # Get prayer text
    liturgy_cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id=?", (prayer_id,))
    prayer_result = liturgy_cursor.fetchone()

    if not prayer_result:
        continue

    prayer_text = prayer_result[0]
    normalized_prayer = indexer._full_normalize(prayer_text)

    # Check each verse
    found_count = 0
    missing = []

    for verse_num, verse_text in verses:
        normalized_verse = indexer._full_normalize(verse_text)

        if normalized_verse in normalized_prayer:
            found_count += 1
        else:
            missing.append(verse_num)

    if found_count == 21:
        complete_prayers.append(prayer_id)
        print(f"  Prayer {prayer_id}: COMPLETE (21/21) ✓")
    elif found_count >= 20:
        almost_complete.append((prayer_id, found_count, missing))

print("\n" + "=" * 80)
print(f"RESULTS:")
print(f"  Complete prayers (21/21 verses): {len(complete_prayers)}")
if complete_prayers:
    print(f"  Prayer IDs: {complete_prayers}")

print(f"\n  Almost complete (20/21 verses): {len(almost_complete)}")
for pid, count, missing in almost_complete[:10]:
    print(f"    Prayer {pid}: {count}/21 - missing {missing}")
if len(almost_complete) > 10:
    print(f"    ... and {len(almost_complete) - 10} more")

# Check current entire_chapter matches
liturgy_cursor.execute("""
    SELECT prayer_id
    FROM psalms_liturgy_index
    WHERE psalm_chapter=145 AND match_type='entire_chapter'
""")
current_entire = [row[0] for row in liturgy_cursor.fetchall()]

print(f"\n  Current entire_chapter matches: {len(current_entire)}")
if current_entire:
    print(f"  Prayer IDs: {current_entire}")

print("\n" + "=" * 80)
if complete_prayers and set(complete_prayers) != set(current_entire):
    print("DISCREPANCY FOUND!")
    print(f"  Should have entire_chapter: {set(complete_prayers)}")
    print(f"  Currently have entire_chapter: {set(current_entire)}")
    missing_from_index = set(complete_prayers) - set(current_entire)
    if missing_from_index:
        print(f"  Missing from index: {missing_from_index}")

liturgy_conn.close()
tanakh_conn.close()
