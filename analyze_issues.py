import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

print("="*70)
print("ISSUE #1: Empty liturgical_context fields")
print("="*70)

# Get examples with empty context
cursor.execute("""
    SELECT i.index_id, i.psalm_chapter, i.psalm_verse_start, i.psalm_phrase_hebrew,
           i.prayer_id, i.match_type, LENGTH(p.hebrew_text) as text_length
    FROM psalms_liturgy_index i
    JOIN prayers p ON i.prayer_id = p.prayer_id
    WHERE i.liturgy_context = '' AND i.index_id IN (26037, 26049, 27072)
    ORDER BY i.index_id
""")

for row in cursor.fetchall():
    index_id, psalm_ch, verse, phrase, prayer_id, match_type, text_len = row
    print(f"\nIndex {index_id}: Ps {psalm_ch}:{verse}, Prayer {prayer_id}")
    print(f"  Phrase: {phrase[:50]}...")
    print(f"  Prayer text length: {text_len} chars")
    print(f"  Match type: {match_type}")

print("\n" + "="*70)
print("ISSUE #2: Multiple phrase entries instead of single verse")
print("="*70)

# Check Psalm 1:3 in prayer 626
cursor.execute("""
    SELECT index_id, psalm_verse_start, psalm_phrase_hebrew, match_type, 
           LENGTH(psalm_phrase_hebrew) as phrase_len
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 1 AND psalm_verse_start = 3 AND prayer_id = 626
    ORDER BY index_id
""")

print("\nPsalm 1:3 in prayer 626:")
for row in cursor.fetchall():
    print(f"  {row[0]}: v{row[1]}, {row[3]}, len={row[4]}: {row[2][:60]}...")

# Get the full verse from Tanakh
tanakh_conn = sqlite3.connect('database/tanakh.db')
tanakh_cursor = tanakh_conn.cursor()
tanakh_cursor.execute("""
    SELECT hebrew FROM verses 
    WHERE book_name = 'Psalms' AND chapter = 1 AND verse = 3
""")
full_verse = tanakh_cursor.fetchone()[0]
print(f"\nFull verse from Tanakh: {full_verse}")
tanakh_conn.close()

print("\n" + "="*70)
print("ISSUE #3: Missed entire_chapter (Psalm 135 in prayer 832)")
print("="*70)

# Check what verses of Psalm 135 are detected
cursor.execute("""
    SELECT psalm_verse_start, match_type, COUNT(*) as cnt
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 135 AND prayer_id = 832
    GROUP BY psalm_verse_start, match_type
    ORDER BY psalm_verse_start
""")

print("\nPsalm 135 verse matches in prayer 832:")
for row in cursor.fetchall():
    print(f"  Verse {row[0]}: {row[1]} ({row[2]} matches)")

# Check total verses in Psalm 135
tanakh_conn = sqlite3.connect('database/tanakh.db')
tanakh_cursor = tanakh_conn.cursor()
tanakh_cursor.execute("""
    SELECT COUNT(*) FROM verses 
    WHERE book_name = 'Psalms' AND chapter = 135
""")
total_verses = tanakh_cursor.fetchone()[0]
print(f"\nTotal verses in Psalm 135: {total_verses}")
tanakh_conn.close()

conn.close()
