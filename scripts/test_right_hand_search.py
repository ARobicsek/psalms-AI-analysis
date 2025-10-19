"""
Test the figurative librarian with 'right hand' + synonyms
to see what it returns across the entire database
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.figurative_librarian import FigurativeLibrarian, FigurativeRequest

# Set up UTF-8 for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize librarian
lib = FigurativeLibrarian()

# Test 1: Search with vehicle_contains only
print("=" * 80)
print("TEST 1: vehicle_contains='right hand' (simple search)")
print("=" * 80)
req1 = FigurativeRequest(
    vehicle_contains='right hand',
    max_results=100
)
bundle1 = lib.search(req1)
print(f"Results: {len(bundle1.instances)}")
if len(bundle1.instances) > 0:
    print("\nFirst 5 results:")
    for i, inst in enumerate(bundle1.instances[:5], 1):
        print(f"{i}. {inst.reference}: {inst.figurative_text}")
        print(f"   Vehicle: {inst.vehicle}")
print()

# Test 2: Search with vehicle_search_terms (hierarchical)
print("=" * 80)
print("TEST 2: vehicle_search_terms=['right hand', 'right arm', 'hand', 'arm']")
print("=" * 80)
req2 = FigurativeRequest(
    vehicle_search_terms=['right hand', 'right arm', 'hand', 'arm'],
    max_results=100
)
bundle2 = lib.search(req2)
print(f"Results: {len(bundle2.instances)}")
if len(bundle2.instances) > 0:
    print("\nFirst 5 results:")
    for i, inst in enumerate(bundle2.instances[:5], 1):
        print(f"{i}. {inst.reference}: {inst.figurative_text}")
        print(f"   Vehicle: {inst.vehicle}")
print()

# Test 3: Search just Psalms with vehicle_search_terms
print("=" * 80)
print("TEST 3: Psalms only, vehicle_search_terms=['right hand', 'right arm', 'hand', 'arm']")
print("=" * 80)
req3 = FigurativeRequest(
    book='Psalms',
    vehicle_search_terms=['right hand', 'right arm', 'hand', 'arm'],
    max_results=100
)
bundle3 = lib.search(req3)
print(f"Results: {len(bundle3.instances)}")
if len(bundle3.instances) > 0:
    print("\nFirst 10 results:")
    for i, inst in enumerate(bundle3.instances[:10], 1):
        print(f"{i}. {inst.reference}: {inst.figurative_text}")
        print(f"   Vehicle: {inst.vehicle}")
print()

# Test 4: Search Psalms + Pentateuch with vehicle_search_terms
print("=" * 80)
print("TEST 4: Psalms + Pentateuch, vehicle_search_terms=['right hand', 'right arm', 'hand', 'arm']")
print("=" * 80)
req4 = FigurativeRequest(
    books=['Psalms', 'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy'],
    vehicle_search_terms=['right hand', 'right arm', 'hand', 'arm'],
    max_results=100
)
bundle4 = lib.search(req4)
print(f"Results: {len(bundle4.instances)}")
if len(bundle4.instances) > 0:
    print("\nFirst 10 results:")
    for i, inst in enumerate(bundle4.instances[:10], 1):
        print(f"{i}. {inst.reference}: {inst.figurative_text}")
        print(f"   Vehicle: {inst.vehicle}")
print()

# Show the distribution across books
if len(bundle4.instances) > 0:
    print("\nDistribution by book:")
    book_counts = {}
    for inst in bundle4.instances:
        book = inst.book
        book_counts[book] = book_counts.get(book, 0) + 1
    for book, count in sorted(book_counts.items()):
        print(f"  {book}: {count}")
