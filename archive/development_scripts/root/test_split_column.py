"""Test if the split column was populated correctly."""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from src.data_sources.tanakh_database import TanakhDatabase
from src.concordance.search import ConcordanceSearch

# Initialize
db = TanakhDatabase()
search = ConcordanceSearch(db)

print("=" * 70)
print("TESTING MAQQEF-SPLIT COLUMN")
print("=" * 70)
print()

# Test 1: Check if column exists and has data
print("Test 1: Check column data for Psalm 3:8")
cursor = db.conn.cursor()
cursor.execute("""
    SELECT word, word_consonantal, word_consonantal_split
    FROM concordance
    WHERE book_name = 'Psalms' AND chapter = 3 AND verse = 8
    ORDER BY position
""")

rows = cursor.fetchall()
print(f"  Found {len(rows)} words in Psalm 3:8")
for i, row in enumerate(rows):
    print(f"  Word {i}: {row['word']}")
    print(f"    Consonantal: {row['word_consonantal']}")
    print(f"    Split: {row['word_consonantal_split']}")
    print()

# Test 2: Search for הכית with split
print()
print("Test 2: Search for 'הכית' (hikita) with use_split=True")
results_with_split = search.search_word("הכית", level='consonantal', scope='Psalms', use_split=True)
print(f"  Results with split: {len(results_with_split)}")
if results_with_split:
    for r in results_with_split[:3]:
        print(f"    - {r.reference}")

# Test 3: Search for הכית without split
print()
print("Test 3: Search for 'הכית' (hikita) with use_split=False")
results_without_split = search.search_word("הכית", level='consonantal', scope='Psalms', use_split=False)
print(f"  Results without split: {len(results_without_split)}")
if results_without_split:
    for r in results_without_split[:3]:
        print(f"    - {r.reference}")

# Test 4: Search for phrase with split
print()
print("Test 4: Search for phrase 'הכית את' with use_split=True")
phrase_results = search.search_phrase("הכית את", level='consonantal', scope='Psalms', use_split=True)
print(f"  Results: {len(phrase_results)}")
if phrase_results:
    for r in phrase_results[:3]:
        print(f"    - {r.reference}")
        print(f"      Hebrew: {r.hebrew_text}")

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)

db.close()
