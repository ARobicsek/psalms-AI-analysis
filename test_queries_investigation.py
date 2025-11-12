"""
Investigation of concordance query results for Psalm 3
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest
from src.data_sources.tanakh_database import TanakhDatabase

# Initialize librarian
db = TanakhDatabase()
lib = ConcordanceLibrarian(db=db)

print("=" * 80)
print("INVESTIGATION: Concordance Query Results")
print("=" * 80)

# Test Query 1: הכית את (should be common - "you struck")
print("\n\n### Query 1: הכית את")
print("Expected: Common biblical expression")
req1 = ConcordanceRequest(
    query="הכית את",
    alternates=["הך את", "תכה את", "הכה את"],
    scope="tanakh",
    level="consonantal"
)
results1 = lib.search_concordance(req1)
print(f"Results: {len(results1)}")
print(f"Variations generated: (checking...)")

# Generate variations manually to see what's happening
from src.agents.concordance_librarian import ConcordanceLibrarian as CL
variations1 = CL._generate_phrase_variations(lib, "הכית את")
print(f"Variations for main query: {len(variations1)}")
print(f"Sample variations: {list(variations1)[:20]}")

# Check if the phrase exists in Psalm 3:8
print("\n\nDirect check: Does 'הכית' appear in Psalm 3:8?")
cursor = db.conn.cursor()
cursor.execute("""
    SELECT verse_ref, position, word
    FROM word_index
    WHERE book = 'Psalms' AND chapter = 3 AND verse = 8
    ORDER BY position
""")
ps3_v8_words = cursor.fetchall()
print("Psalm 3:8 words:")
for ref, pos, word in ps3_v8_words:
    print(f"  Position {pos}: {word}")

# Test Query 2: שבר שן (breaks tooth/teeth)
print("\n\n### Query 2: שבר שן")
print("Expected: At least 1 result (Psalm 3:8 itself)")
req2 = ConcordanceRequest(
    query="שבר שן",
    alternates=["שבר שיניים", "שבור שן", "שבר שני"],
    scope="tanakh",
    level="consonantal"
)
results2 = lib.search_concordance(req2)
print(f"Results: {len(results2)}")

variations2 = CL._generate_phrase_variations(lib, "שבר שן")
print(f"Variations for main query: {len(variations2)}")
print(f"Sample variations: {list(variations2)[:20]}")

# Check if the phrase exists in Psalm 3:8
print("\n\nLooking for 'שבר' or 'שן' in Psalm 3:8:")
cursor = db.conn.cursor()
cursor.execute("""
    SELECT verse_ref, position, word
    FROM word_index
    WHERE book = 'Psalms' AND chapter = 3 AND verse = 8
    AND (word LIKE '%שבר%' OR word LIKE '%שן%')
    ORDER BY position
""")
matches = cursor.fetchall()
if matches:
    print("Matches found:")
    for ref, pos, word in matches:
        print(f"  Position {pos}: {word}")
else:
    print("NO MATCHES - This is the problem!")

# Let's check what the actual words are
print("\n\nActual words in Psalm 3:8 containing ש:")
cursor = db.conn.cursor()
cursor.execute("""
    SELECT verse_ref, position, word
    FROM word_index
    WHERE book = 'Psalms' AND chapter = 3 AND verse = 8
    AND word LIKE '%ש%'
    ORDER BY position
""")
matches = cursor.fetchall()
for ref, pos, word in matches:
    print(f"  Position {pos}: {word}")

print("\n" + "=" * 80)
print("END INVESTIGATION")
print("=" * 80)
