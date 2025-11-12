"""
Direct database investigation
"""
import sqlite3
from pathlib import Path

db_path = Path("database/tanakh.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 80)
print("DATABASE INVESTIGATION")
print("=" * 80)

# Check tables
print("\n### Tables in database:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for (table,) in tables:
    print(f"  - {table}")

# Count rows in word_index
print("\n### word_index table row count:")
try:
    cursor.execute("SELECT COUNT(*) FROM word_index")
    count = cursor.fetchone()[0]
    print(f"  Total words: {count}")
except Exception as e:
    print(f"  ERROR: {e}")

# Check Psalm 3:8
print("\n### Words in Psalm 3:8:")
try:
    cursor.execute("""
        SELECT book, chapter, verse, position, word, consonantal
        FROM word_index
        WHERE book = 'Psalms' AND chapter = 3 AND verse = 8
        ORDER BY position
    """)
    words = cursor.fetchall()
    if words:
        for book, ch, vs, pos, word, cons in words:
            print(f"  Pos {pos}: '{word}' (consonantal: '{cons}')")
    else:
        print("  NO WORDS FOUND")
except Exception as e:
    print(f"  ERROR: {e}")

# Look for "strike" related words in Psalm 3:8
print("\n### Looking for 'strike' words (hkh/nkh roots) in Psalm 3:8:")
try:
    cursor.execute("""
        SELECT position, word, consonantal
        FROM word_index
        WHERE book = 'Psalms' AND chapter = 3 AND verse = 8
        AND (consonantal LIKE '%הכ%' OR consonantal LIKE '%נכ%')
        ORDER BY position
    """)
    matches = cursor.fetchall()
    if matches:
        for pos, word, cons in matches:
            print(f"  Pos {pos}: '{word}' (consonantal: '{cons}')")
    else:
        print("  NO MATCHES")
except Exception as e:
    print(f"  ERROR: {e}")

# Look for "tooth" related words in Psalm 3:8
print("\n### Looking for 'tooth' words (shn root) in Psalm 3:8:")
try:
    cursor.execute("""
        SELECT position, word, consonantal
        FROM word_index
        WHERE book = 'Psalms' AND chapter = 3 AND verse = 8
        AND consonantal LIKE '%שנ%'
        ORDER BY position
    """)
    matches = cursor.fetchall()
    if matches:
        for pos, word, cons in matches:
            print(f"  Pos {pos}: '{word}' (consonantal: '{cons}')")
    else:
        print("  NO MATCHES")
except Exception as e:
    print(f"  ERROR: {e}")

# Look for "break" related words in Psalm 3:8
print("\n### Looking for 'break' words (shbr root) in Psalm 3:8:")
try:
    cursor.execute("""
        SELECT position, word, consonantal
        FROM word_index
        WHERE book = 'Psalms' AND chapter = 3 AND verse = 8
        AND consonantal LIKE '%שבר%'
        ORDER BY position
    """)
    matches = cursor.fetchall()
    if matches:
        for pos, word, cons in matches:
            print(f"  Pos {pos}: '{word}' (consonantal: '{cons}')")
    else:
        print("  NO MATCHES")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 80)
print("END INVESTIGATION")
print("=" * 80)

conn.close()
