"""Check Psalm 23 matches in prayer 574."""
import sys
import sqlite3

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT psalm_verse_start, psalm_verse_end, match_type, phrase_length,
           psalm_phrase_hebrew, confidence
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 23 AND prayer_id = 574
    ORDER BY psalm_verse_start, phrase_length DESC
""")

results = cursor.fetchall()

print("Psalm 23 matches in prayer 574:")
print("=" * 80)
print(f"Total matches: {len(results)}\n")

for verse_start, verse_end, match_type, phrase_len, phrase, confidence in results:
    verse_range = f"{verse_start}" if verse_start == verse_end else f"{verse_start}-{verse_end}"
    print(f"Verse {verse_range:5} | {match_type:15} | Len: {phrase_len:2} | Conf: {confidence:.2f}")
    print(f"  {phrase[:60]}{'...' if len(phrase) > 60 else ''}")
    print()

conn.close()
