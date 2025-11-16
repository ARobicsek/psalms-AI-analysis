"""
Check concordance table structure
"""
import sqlite3
from pathlib import Path

db_path = Path("database/tanakh.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 80)
print("CONCORDANCE TABLE INVESTIGATION")
print("=" * 80)

# Get concordance table schema
print("\n### Concordance table schema:")
cursor.execute("PRAGMA table_info(concordance)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Count rows
print("\n### Row count:")
cursor.execute("SELECT COUNT(*) FROM concordance")
print(f"  {cursor.fetchone()[0]} rows")

# Check Psalm 3:8
print("\n### Entries for Psalm 3:8:")
cursor.execute("""
    SELECT position, word, word_consonantal
    FROM concordance
    WHERE book_name = 'Psalms' AND chapter = 3 AND verse = 8
    ORDER BY position
    LIMIT 20
""")
rows = cursor.fetchall()
if rows:
    for pos, word, cons in rows:
        print(f"  Pos {pos}: '{word}' (cons: '{cons}')")
else:
    print("  NO ROWS FOUND")

# Try different book name
print("\n### Try 'Tehillim' instead of 'Psalms':")
cursor.execute("""
    SELECT position, word, word_consonantal
    FROM concordance
    WHERE book_name = 'Tehillim' AND chapter = 3 AND verse = 8
    ORDER BY position
    LIMIT 20
""")
rows = cursor.fetchall()
if rows:
    for pos, word, cons in rows:
        print(f"  Pos {pos}: '{word}' (cons: '{cons}')")
else:
    print("  NO ROWS FOUND")

# Check what books are in the database
print("\n### Unique book names in concordance table:")
cursor.execute("SELECT DISTINCT book_name FROM concordance ORDER BY book_name LIMIT 50")
books = cursor.fetchall()
for (book,) in books:
    print(f"  - '{book}'")

conn.close()

print("\n" + "=" * 80)
print("END")
print("=" * 80)
