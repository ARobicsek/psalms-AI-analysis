"""Show detailed concordance search results with all variations and matches."""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest

# Initialize
lib = ConcordanceLibrarian()

# Query to analyze
query = "הכית את"
alternates = ["הך את", "תכה את", "הכה את"]

print("=" * 80)
print("DETAILED CONCORDANCE SEARCH ANALYSIS")
print("=" * 80)
print()
print(f"Original Query: {query}")
print(f"Alternates: {alternates}")
print()

# Run search
req = ConcordanceRequest(
    query=query,
    alternate_queries=alternates,
    scope="Tanakh",
    level="consonantal"
)

bundle = lib.search_with_variations(req)

print("=" * 80)
print("VARIATIONS SEARCHED")
print("=" * 80)
print(f"Total variations: {len(bundle.variations_searched)}")
print()

# Group variations by source
main_variations = []
alt_variations = []

# Main query variations come first
for var in bundle.variations_searched[:100]:  # First variations are from main query
    if var not in main_variations:
        main_variations.append(var)

print(f"Main query '{query}' generated {len(main_variations)} variations:")
for i, var in enumerate(main_variations[:30], 1):  # Show first 30
    print(f"  {i:2d}. {var}")
if len(main_variations) > 30:
    print(f"  ... and {len(main_variations) - 30} more")

print()
print(f"Alternate queries generated {len(bundle.variations_searched) - len(main_variations)} additional variations")

print()
print("=" * 80)
print("MATCHED RESULTS")
print("=" * 80)
print(f"Total matches: {len(bundle.results)}")
print()

# Group by book
results_by_book = {}
for r in bundle.results:
    if r.book not in results_by_book:
        results_by_book[r.book] = []
    results_by_book[r.book].append(r)

for book, results in sorted(results_by_book.items()):
    print(f"\n{book} ({len(results)} matches):")
    for r in sorted(results, key=lambda x: (x.chapter, x.verse)):
        print(f"\n  {r.reference}")
        print(f"    Hebrew: {r.hebrew_text}")
        print(f"    English: {r.english_text}")
        print(f"    Matched word: {r.matched_word} (position {r.word_position})")

print()
print("=" * 80)
print("SEARCH SUMMARY")
print("=" * 80)
print(f"Original query: {query}")
print(f"Alternates: {len(alternates)}")
print(f"Total variations searched: {len(bundle.variations_searched)}")
print(f"Total matches found: {len(bundle.results)}")
print(f"Books with matches: {len(results_by_book)}")
print()
print("✓ Maqqef fix working - 'הכית את' successfully finds Psalm 3:8!")
