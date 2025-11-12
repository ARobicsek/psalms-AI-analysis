"""
Direct database query test
"""
import sys
sys.path.insert(0, '.')

import sqlite3
import json
from pathlib import Path

db_path = Path("database/tanakh.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("Testing direct database queries...\n")

# Test 1: Check if specific consonantal forms exist
test_words = [
    ("שני", "teeth (construct)"),
    ("שברת", "you broke"),
    ("הכית", "struck"),
    ("יהוה", "YHWH"),
    ("קומה", "arise")
]

results = {}

for word, desc in test_words:
    cursor.execute("""
        SELECT COUNT(*), MIN(book_name || ' ' || chapter || ':' || verse) as example
        FROM concordance
        WHERE word_consonantal = ?
    """, (word,))
    row = cursor.fetchone()
    count = row[0]
    example = row[1] if row[1] else "N/A"
    results[word] = {
        "description": desc,
        "count": count,
        "example": example
    }
    print(f"{desc} ('{word}'): {count} matches")
    if count > 0:
        print(f"  Example: {example}")
    print()

# Save to JSON
output_path = Path("output/debug/db_query_results.json")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Results saved to: {output_path}")

# Also check for partial matches
print("\n### Checking for partial matches (LIKE queries):")
for word, desc in test_words:
    cursor.execute("""
        SELECT COUNT(*)
        FROM concordance
        WHERE word_consonantal LIKE ?
    """, (f"%{word}%",))
    count = cursor.fetchone()[0]
    print(f"{desc}: {count} partial matches")

conn.close()
