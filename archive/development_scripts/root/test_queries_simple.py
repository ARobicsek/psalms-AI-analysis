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
print("\n\n### Query 1: hakitah et (you struck)")
req1 = ConcordanceRequest(
    query="הכית את",
    alternate_queries=["הך את", "תכה את", "הכה את"],
    scope="tanakh",
    level="consonantal"
)
bundle1 = lib.search_with_variations(req1)
print(f"Results: {len(bundle1.results)}")
print(f"Variations generated: {len(bundle1.variations_searched)}")
# Can't print variations due to Unicode issues

# Check if the phrase exists in Psalm 3:8
print("\n\nDirect check: Words in Psalm 3:8:")
cursor = db.conn.cursor()
cursor.execute("""
    SELECT verse_ref, position, word
    FROM word_index
    WHERE book = 'Psalms' AND chapter = 3 AND verse = 8
    ORDER BY position
""")
ps3_v8_words = cursor.fetchall()
for ref, pos, word in ps3_v8_words:
    print(f"  Position {pos}: {word}")

# Test Query 2: שבר שן (breaks tooth/teeth)
print("\n\n### Query 2: shavar shen (break tooth)")
req2 = ConcordanceRequest(
    query="שבר שן",
    alternate_queries=["שבר שיניים", "שבור שן", "שבר שני"],
    scope="tanakh",
    level="consonantal"
)
bundle2 = lib.search_with_variations(req2)
print(f"Results: {len(bundle2.results)}")
print(f"Variations generated: {len(bundle2.variations_searched)}")
# Can't print variations due to Unicode issues

# Look for teeth-related words in Psalm 3:8
print("\n\nLooking for shin/shen related words in Psalm 3:8:")
cursor = db.conn.cursor()
cursor.execute("""
    SELECT verse_ref, position, word
    FROM word_index
    WHERE book = 'Psalms' AND chapter = 3 AND verse = 8
    AND word LIKE '%שן%'
    ORDER BY position
""")
matches = cursor.fetchall()
if matches:
    print("Matches found:")
    for ref, pos, word in matches:
        print(f"  Position {pos}: {word}")
else:
    print("NO MATCHES for shen")

# Look for break-related words in Psalm 3:8
cursor.execute("""
    SELECT verse_ref, position, word
    FROM word_index
    WHERE book = 'Psalms' AND chapter = 3 AND verse = 8
    AND word LIKE '%שבר%'
    ORDER BY position
""")
matches = cursor.fetchall()
if matches:
    print("\nMatches found for shavar:")
    for ref, pos, word in matches:
        print(f"  Position {pos}: {word}")
else:
    print("NO MATCHES for shavar")

# Let's check consonantal normalization
print("\n\nConsonantal forms of Psalm 3:8 words:")
from src.concordance.hebrew_text_processor import normalize_for_search
cursor.execute("""
    SELECT verse_ref, position, word
    FROM word_index
    WHERE book = 'Psalms' AND chapter = 3 AND verse = 8
    ORDER BY position
""")
for ref, pos, word in cursor.fetchall():
    consonantal = normalize_for_search(word, level='consonantal')
    print(f"  Position {pos}: {word} -> {consonantal}")

print("\n" + "=" * 80)
print("END INVESTIGATION")
print("=" * 80)
