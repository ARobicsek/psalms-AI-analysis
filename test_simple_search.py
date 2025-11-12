"""
Simple test to see if concordance search works at all
"""
import sys
sys.path.insert(0, '.')

from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest
from src.data_sources.tanakh_database import TanakhDatabase
from src.concordance.search import ConcordanceSearch

# Initialize
db = TanakhDatabase()
search = ConcordanceSearch(db)

print("Testing basic concordance search...")
print(f"Database path: {db.db_path}")

# Test 1: Direct SQL query
print("\n### Test 1: Direct SQL - find any word containing 'יהוה'")
cursor = db.conn.cursor()
cursor.execute("""
    SELECT book_name, chapter, verse, word_consonantal
    FROM concordance
    WHERE word_consonantal LIKE '%יהוה%'
    LIMIT 5
""")
results = cursor.fetchall()
print(f"Found {len(results)} results via SQL")
for row in results[:3]:
    print(f"  {row}")

# Test 2: Use ConcordanceSearch directly
print("\n### Test 2: ConcordanceSearch.search_word() for 'יהוה'")
from src.concordance.hebrew_text_processor import normalize_for_search
normalized = normalize_for_search("יהוה", "consonantal")
print(f"Normalized: {repr(normalized)}")
results2 = search.search_word(normalized, scope="psalms", level="consonantal", limit=5)
print(f"Found {len(results2)} results via search_word()")
for r in results2[:3]:
    print(f"  {r.reference}")

# Test 3: Use ConcordanceLibrarian
print("\n### Test 3: ConcordanceLibrarian for simple query")
lib = ConcordanceLibrarian(db=db)
req = ConcordanceRequest(
    query="יהוה",
    scope="psalms",
    level="consonantal"
)
bundle = lib.search_with_variations(req)
print(f"Found {len(bundle.results)} results")
print(f"Variations searched: {len(bundle.variations_searched)}")

print("\nDone!")
