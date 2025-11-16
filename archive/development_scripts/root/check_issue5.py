import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

print("="*70)
print("ISSUE #5: No consecutive verse detection (Psalm 6 in prayer 73)")
print("="*70)

# Check what verses of Psalm 6 are detected in prayer 73
cursor.execute("""
    SELECT psalm_verse_start, psalm_verse_end, match_type, 
           substr(psalm_phrase_hebrew, 1, 50) as phrase_preview
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 6 AND prayer_id = 73
    ORDER BY psalm_verse_start
""")

print("\nPsalm 6 matches in prayer 73 (Tachanun):")
matches = cursor.fetchall()
for row in matches:
    verse_start, verse_end, match_type, phrase = row
    print(f"  Verse {verse_start}-{verse_end}: {match_type} - {phrase}...")

print(f"\nTotal matches: {len(matches)}")
print("Expected: Verses 2-11 (10 consecutive verses)")

# Check if the full text of verses 2-11 appears in the prayer
tanakh_conn = sqlite3.connect('database/tanakh.db')
tanakh_cursor = tanakh_conn.cursor()

tanakh_cursor.execute("""
    SELECT verse, hebrew FROM verses
    WHERE book_name = 'Psalms' AND chapter = 6 AND verse BETWEEN 2 AND 11
    ORDER BY verse
""")

print("\nFull verses from Tanakh (Psalm 6:2-11):")
for verse_num, verse_text in tanakh_cursor.fetchall():
    print(f"  v{verse_num}: {verse_text[:60]}...")

tanakh_conn.close()
conn.close()
