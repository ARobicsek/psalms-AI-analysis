import sqlite3

db_path = "data/liturgy.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Match types for Psalm 1:")
cursor.execute("SELECT DISTINCT match_type FROM psalms_liturgy_index WHERE psalm_chapter = 1")
for row in cursor.fetchall():
    print(row)

print("\nMatch types for Psalm 145:")
cursor.execute("SELECT DISTINCT match_type FROM psalms_liturgy_index WHERE psalm_chapter = 145")
for row in cursor.fetchall():
    print(row)

print("\nMatches for phrase 'בַּעֲצַת רְשָׁעִים' in Psalm 1:")
# The user provided the un-normalized phrase. I will query for it.
# The user said they saw it in the db, so it should be there.
cursor.execute("SELECT * FROM psalms_liturgy_index WHERE psalm_chapter = 1 AND psalm_phrase_hebrew = 'בַּעֲצַת רְשָׁעִים' AND is_unique = 1")
rows = cursor.fetchall()
print(f"Found {len(rows)} matches for 'בַּעֲצַת רְשָׁעִים'.")
for row in rows:
    print(row)

# I will also check the number of matches for this phrase group.
# The summary is generated if len(matches) >= 3.
# The matches are grouped by psalm_phrase_hebrew.
print("\nNumber of matches for each phrase in Psalm 1:")
cursor.execute("SELECT psalm_phrase_hebrew, COUNT(*) FROM psalms_liturgy_index WHERE psalm_chapter = 1 AND match_type = 'phrase_match' AND is_unique = 1 GROUP BY psalm_phrase_hebrew")
for row in cursor.fetchall():
    print(row)


conn.close()
