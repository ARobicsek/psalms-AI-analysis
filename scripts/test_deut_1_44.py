"""
Test to investigate why Deut 1:44 appears in 'hand' search results
"""
import sys
from pathlib import Path
import sqlite3
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = Path("C:/Users/ariro/OneDrive/Documents/Bible/database/Pentateuch_Psalms_fig_language.db")

# Set up UTF-8 for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Connect to database
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get the specific verse
query = """
    SELECT
        v.reference,
        v.hebrew_text,
        v.english_text,
        f.figurative_text,
        f.vehicle,
        f.target,
        f.ground,
        f.explanation
    FROM figurative_language f
    JOIN verses v ON f.verse_id = v.id
    WHERE v.reference = 'Deuteronomy 1:44'
"""

cursor.execute(query)
row = cursor.fetchone()

if row:
    print("=" * 80)
    print("Deuteronomy 1:44 Database Entry")
    print("=" * 80)
    print(f"\nReference: {row['reference']}")
    print(f"\nHebrew: {row['hebrew_text']}")
    print(f"\nEnglish: {row['english_text']}")
    print(f"\nFigurative phrase: {row['figurative_text']}")
    print(f"\nVehicle (JSON): {row['vehicle']}")

    vehicle = json.loads(row['vehicle']) if row['vehicle'] else None
    print(f"Vehicle (parsed): {vehicle}")

    print(f"\nTarget (JSON): {row['target']}")
    target = json.loads(row['target']) if row['target'] else None
    print(f"Target (parsed): {target}")

    print(f"\nGround (JSON): {row['ground']}")
    ground = json.loads(row['ground']) if row['ground'] else None
    print(f"Ground (parsed): {ground}")

    print(f"\nExplanation: {row['explanation'][:200]}...")

    # Check if 'hand' or 'arm' appears anywhere
    print("\n" + "=" * 80)
    print("Searching for 'hand' or 'arm' in all fields:")
    print("=" * 80)

    all_text = " ".join([
        str(row['hebrew_text'] or ''),
        str(row['english_text'] or ''),
        str(row['figurative_text'] or ''),
        str(row['vehicle'] or ''),
        str(row['target'] or ''),
        str(row['ground'] or ''),
        str(row['explanation'] or '')
    ]).lower()

    if 'hand' in all_text:
        print("✓ Found 'hand' in text")
    else:
        print("✗ 'hand' NOT found")

    if 'arm' in all_text:
        print("✓ Found 'arm' in text")
    else:
        print("✗ 'arm' NOT found")
else:
    print("Verse not found in database!")

conn.close()
