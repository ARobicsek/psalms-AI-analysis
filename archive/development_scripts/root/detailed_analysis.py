import sqlite3
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

# Import the normalization function
sys.path.append('src')
from liturgy.liturgy_indexer import LiturgyIndexer

indexer = LiturgyIndexer()

conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()
tanakh_conn = sqlite3.connect('database/tanakh.db')
tanakh_cursor = tanakh_conn.cursor()

print("="*70)
print("DETAILED ANALYSIS OF ISSUE #1: Empty Context")
print("="*70)

# Analyze index_id 26037
cursor.execute("""
    SELECT i.psalm_phrase_hebrew, i.psalm_phrase_normalized, p.hebrew_text
    FROM psalms_liturgy_index i
    JOIN prayers p ON i.prayer_id = p.prayer_id
    WHERE i.index_id = 26037
""")

phrase, normalized, prayer_text = cursor.fetchone()
print(f"\nIndex 26037 - Phrase: {phrase}")
print(f"Normalized phrase: {normalized}")
print(f"Prayer length: {len(prayer_text)} chars")

# Try to find the phrase manually
normalized_prayer = indexer._full_normalize(prayer_text)
print(f"Normalized prayer length: {len(normalized_prayer)} chars")
print(f"Phrase in prayer: {normalized in normalized_prayer}")

if normalized in normalized_prayer:
    pos = normalized_prayer.find(normalized)
    print(f"Position in normalized prayer: {pos}")
    
# Check sliding window approach
words = prayer_text.split()
phrase_words = phrase.split()
print(f"Prayer has {len(words)} words, phrase has {len(phrase_words)} words")

# Check if phrase contains paseq
print(f"Phrase contains paseq (׀): {'׀' in phrase}")
print(f"Phrase starts with paseq: {phrase.startswith('׀')}")

# Count normalized words
normalized_phrase_words = normalized.split()
print(f"Normalized phrase has {len(normalized_phrase_words)} words")

print("\n" + "="*70)
print("DETAILED ANALYSIS OF ISSUE #2: Multiple phrases vs verse")
print("="*70)

# Get full verse text from Tanakh
tanakh_cursor.execute("""
    SELECT hebrew FROM verses
    WHERE book_name = 'Psalms' AND chapter = 1 AND verse = 3
""")
full_verse = tanakh_cursor.fetchone()[0]
print(f"\nFull verse: {full_verse}")
print(f"Full verse length: {len(full_verse)} chars")

# Get the two phrase matches
cursor.execute("""
    SELECT index_id, psalm_phrase_hebrew, phrase_length
    FROM psalms_liturgy_index
    WHERE index_id IN (26039, 26040)
    ORDER BY index_id
""")

for row in cursor.fetchall():
    idx, phrase, length = row
    print(f"\nIndex {idx}:")
    print(f"  Phrase: {phrase}")
    print(f"  Length: {length} words")
    print(f"  Normalized: {indexer._full_normalize(phrase)}")

# Check if full verse is in the searchable phrases
print(f"\nFull verse normalized: {indexer._full_normalize(full_verse)}")

# Get prayer text
cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = 626")
prayer_text = cursor.fetchone()[0]
print(f"\nFull verse in prayer: {indexer._full_normalize(full_verse) in indexer._full_normalize(prayer_text)}")

print("\n" + "="*70)
print("DETAILED ANALYSIS OF ISSUE #3: Chapter detection failure")
print("="*70)

# Check verses 1, 3, and 21 which are phrase_match instead of exact_verse
for verse_num in [1, 3, 21]:
    tanakh_cursor.execute("""
        SELECT hebrew FROM verses
        WHERE book_name = 'Psalms' AND chapter = 135 AND verse = ?
    """, (verse_num,))
    verse_text = tanakh_cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT psalm_phrase_hebrew, match_type
        FROM psalms_liturgy_index
        WHERE psalm_chapter = 135 AND psalm_verse_start = ? AND prayer_id = 832
        LIMIT 1
    """, (verse_num,))
    
    result = cursor.fetchone()
    if result:
        phrase, match_type = result
        print(f"\nVerse {verse_num}:")
        print(f"  Tanakh: {verse_text}")
        print(f"  Matched phrase: {phrase}")
        print(f"  Match type: {match_type}")
        print(f"  Tanakh normalized: {indexer._full_normalize(verse_text)}")
        print(f"  Phrase normalized: {indexer._full_normalize(phrase)}")
        print(f"  Match: {indexer._full_normalize(verse_text) == indexer._full_normalize(phrase)}")

print("\n" + "="*70)
print("DETAILED ANALYSIS OF ISSUE #4: Phrase when full verse present")
print("="*70)

# Check Psalm 150:1 in prayer 35
cursor.execute("""
    SELECT psalm_phrase_hebrew, match_type, phrase_length
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 150 AND psalm_verse_start = 1 AND prayer_id = 35
    LIMIT 1
""")

result = cursor.fetchone()
if result:
    phrase, match_type, length = result
    tanakh_cursor.execute("""
        SELECT hebrew FROM verses
        WHERE book_name = 'Psalms' AND chapter = 150 AND verse = 1
    """)
    full_verse = tanakh_cursor.fetchone()[0]
    
    print(f"\nPsalm 150:1 in prayer 35:")
    print(f"  Matched phrase: {phrase}")
    print(f"  Match type: {match_type}")
    print(f"  Phrase length: {length}")
    print(f"  Full verse: {full_verse}")
    print(f"  Phrase is full verse: {indexer._full_normalize(phrase) == indexer._full_normalize(full_verse)}")

conn.close()
tanakh_conn.close()
