"""Check which verses of Psalm 145 match in Prayer 91."""

import sqlite3
import sys
sys.path.insert(0, '.')
from src.liturgy.liturgy_indexer import LiturgyIndexer

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

indexer = LiturgyIndexer(verbose=False)

# Get all verses of Psalm 145 from tanakh
tanakh_conn = sqlite3.connect('database/tanakh.db')
tanakh_cursor = tanakh_conn.cursor()
tanakh_cursor.execute('SELECT verse, hebrew FROM verses WHERE book_name="Psalms" AND chapter=145 ORDER BY verse')
verses = {verse: hebrew for verse, hebrew in tanakh_cursor.fetchall()}
tanakh_conn.close()

# Get Prayer 91 text
liturgy_conn = sqlite3.connect('data/liturgy.db')
liturgy_cursor = liturgy_conn.cursor()
liturgy_cursor.execute('SELECT hebrew_text FROM prayers WHERE prayer_id=91')
prayer_text = liturgy_cursor.fetchone()[0]
liturgy_conn.close()

# Normalize prayer text once
normalized_prayer = indexer._full_normalize(prayer_text)

print('Checking which Psalm 145 verses are in Prayer 91 after normalization:')
print()

found_verses = []
missing_verses = []

for verse_num, verse_text in sorted(verses.items()):
    normalized_verse = indexer._full_normalize(verse_text)
    if normalized_verse in normalized_prayer:
        print(f'[OK] Verse {verse_num:2d} FOUND')
        found_verses.append(verse_num)
    else:
        print(f'[--] Verse {verse_num:2d} NOT FOUND')
        missing_verses.append(verse_num)
        # Show what we're looking for
        print(f'     Looking for: {normalized_verse[:60]}...')

print()
print(f'Summary:')
print(f'  Found: {len(found_verses)} verses - {found_verses}')
print(f'  Missing: {len(missing_verses)} verses - {missing_verses}')
