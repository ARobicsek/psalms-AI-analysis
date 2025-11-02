import sys
import sqlite3

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT index_id, psalm_chapter, psalm_verse_start, psalm_verse_end,
           psalm_phrase_hebrew, match_type, prayer_id
    FROM psalms_liturgy_index
    WHERE index_id IN (12651, 12668)
    ORDER BY index_id
''')

print("Checking duplicate match issue (IDs 12651 and 12668):\n")

for row in cursor.fetchall():
    print(f"ID: {row[0]}")
    print(f"  Psalm: {row[1]}:{row[2]}-{row[3] if row[3] else row[2]}")
    print(f"  Match Type: {row[5]}")
    print(f"  Prayer ID: {row[6]}")
    print(f"  Phrase: {row[4][:60]}...")
    print()

conn.close()
