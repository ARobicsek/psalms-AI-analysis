"""
Check what's in Psalm 3:8
"""
import sqlite3
import json
from pathlib import Path

db_path = Path("database/tanakh.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get Psalm 3:8 words
cursor.execute("""
    SELECT position, word, word_consonantal
    FROM concordance
    WHERE book_name = 'Psalms' AND chapter = 3 AND verse = 8
    ORDER BY position
""")
rows = cursor.fetchall()

result = {
    "verse": "Psalm 3:8",
    "word_count": len(rows),
    "words": [
        {
            "position": pos,
            "word": word,
            "consonantal": cons
        }
        for pos, word, cons in rows
    ]
}

# Save to JSON
output_path = Path("output/debug/psalm_3_verse_8.json")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Results saved to: {output_path}")
print(f"Found {len(rows)} words in Psalm 3:8")

# Now search for phrases
print("\n### Searching for 'הכית את' variations...")
query1_variations = [
    "הכית את",
    "הכית",
    "הכה את",
    "הך את",
    "תכה את"
]

for var in query1_variations:
    cursor.execute("""
        SELECT COUNT(*)
        FROM concordance
        WHERE word_consonantal LIKE ?
    """, (f"%{var}%",))
    count = cursor.fetchone()[0]
    print(f"  '{var}': {count} matches in Tanakh")

print("\n### Searching for 'שבר שן' variations...")
query2_variations = [
    "שבר",
    "שבר שן",
    "שן",
    "שני",
    "שיניים",
    "שבור"
]

for var in query2_variations:
    cursor.execute("""
        SELECT COUNT(*)
        FROM concordance
        WHERE word_consonantal LIKE ?
    """, (f"%{var}%",))
    count = cursor.fetchone()[0]
    print(f"  '{var}': {count} matches in Tanakh")

conn.close()
print("\nDone!")
