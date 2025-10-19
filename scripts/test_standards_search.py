"""
Quick test to investigate 'standards' search results
"""
import sys
from pathlib import Path
import sqlite3
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = Path("C:/Users/ariro/OneDrive/Documents/Bible/database/Pentateuch_Psalms_fig_language.db")

# Connect to database
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Run the same query that the librarian would use
query = """
    SELECT
        v.reference,
        f.figurative_text,
        f.vehicle,
        f.explanation
    FROM figurative_language f
    JOIN verses v ON f.verse_id = v.id
    WHERE f.vehicle LIKE ? COLLATE NOCASE
    LIMIT 10
"""

search_term = "%standards%"
cursor.execute(query, (search_term,))
rows = cursor.fetchall()

print(f"Searching for vehicle LIKE '{search_term}'")
print(f"Found {len(rows)} results\n")
print("=" * 80)

for i, row in enumerate(rows, 1):
    vehicle = json.loads(row['vehicle']) if row['vehicle'] else None
    print(f"\n{i}. {row['reference']}")
    print(f"   Figurative text: {row['figurative_text']}")
    print(f"   Vehicle JSON: {row['vehicle']}")
    print(f"   Vehicle parsed: {vehicle}")
    print(f"   Explanation: {row['explanation'][:100]}...")

conn.close()
