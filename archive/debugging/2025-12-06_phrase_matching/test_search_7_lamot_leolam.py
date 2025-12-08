#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the exact search phrase: לא ימוט לעולם"""

import sys
from src.concordance.search import ConcordanceSearch
from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest
from src.agents.research_assembler import ResearchRequest
from src.data_sources.tanakh_database import TanakhDatabase

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize database and search
db = TanakhDatabase()
search = ConcordanceSearch(db)
librarian = ConcordanceLibrarian()

def test_exact_search():
    print("=" * 80)
    print("TESTING SEARCH 7: לא ימוט לעולם")
    print("=" * 80)

    # The exact phrase from the research output
    phrase = "לא ימוט לעולם"
    print(f"\nSearching for phrase: '{phrase}'")
    print("-" * 40)

    # Test 1: Direct search_phrase (what should be used)
    print("\n1. DIRECT search_phrase RESULTS:")
    print("-" * 40)
    results1 = search.search_phrase(phrase, level='consonantal', scope='auto')
    print(f"Number of results: {len(results1)}")

    for i, r in enumerate(results1):
        print(f"\nResult {i+1}: {r.reference}")
        print(f"  Hebrew: {r.hebrew_text}")
        print(f"  English: {r.english_text}")
        if hasattr(r, 'matched_phrase') and r.matched_phrase:
            print(f"  Matched phrase: {r.matched_phrase}")
        else:
            print(f"  Matched word: {r.matched_word}")

    # Test 2: Simulate what concordance_librarian does
    print("\n\n2. SIMULATING CONCORDANCE LIBRARIAN PROCESS:")
    print("-" * 40)

    # Create a mock research request like the librarian would
    class MockRequest:
        def __init__(self):
            self.search_phrase = phrase
            self.level = 'consonantal'
            self.scope = 'auto'
            self.include_variations = True
            self.source_psalm = None

    request = MockRequest()

    # Call the librarian's search method
    print(f"\nLibrarian searching for: '{request.search_phrase}'")

    # Create a proper ConcordanceRequest
    lib_request = ConcordanceRequest(
        query=request.search_phrase,
        level=request.level,
        scope=request.scope,
        include_variations=request.include_variations,
        notes="Test search for לא ימוט לעולם"
    )

    librarian_results = librarian.search_with_variations(lib_request)

    # The librarian returns a ConcordanceBundle
    print(f"\nLibrarian search completed")
    print(f"Total results: {len(librarian_results.results)}")
    print(f"Variations searched: {librarian_results.variations_searched}")

    # Show the variations that were searched
    print(f"\nVariations searched:")
    for i, variation in enumerate(librarian_results.variations_searched[:10]):  # Show first 10
        print(f"  {i+1}. '{variation}'")

    # Show all results
    print(f"\nAll results:")
    for i, result in enumerate(librarian_results.results[:10]):  # Show first 10
        print(f"\nResult {i+1}:")
        print(f"  Reference: {result.reference}")
        print(f"  Matched text: {result.matched_word}")
        if result.matched_word and len(result.matched_word.split()) == 1:
            print(f"  ⚠️  WARNING: Only matched ONE word: '{result.matched_word}'")
        elif result.matched_word:
            words = result.matched_word.split()
            print(f"  Words matched: {len(words)} - {words}")

    # Test 3: Check what words are actually in Psalm 21:8
    print("\n\n3. CHECKING PSALM 21:8 (one of the results mentioned):")
    print("-" * 40)

    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT hebrew, english
        FROM verses
        WHERE book_name = 'Psalms' AND chapter = 21 AND verse = 8
    """)

    verse_info = cursor.fetchone()
    if verse_info:
        print(f"Hebrew: {verse_info[0]}")
        print(f"English: {verse_info[1]}")

        # Get all words in this verse
        cursor.execute("""
            SELECT position, word, word_consonantal_split
            FROM concordance
            WHERE book_name = 'Psalms' AND chapter = 21 AND verse = 8
            ORDER BY position
        """)

        words = cursor.fetchall()
        print(f"\nWords in verse:")
        for pos, word, cons_split in words:
            if word.strip():
                print(f"  Pos {pos}: {word} (split: {cons_split})")

    # Test 4: Check if "בל־ימוט" matches our search
    print("\n\n4. TESTING IF 'בל־ימוט' SHOULD MATCH 'לא ימוט':")
    print("-" * 40)

    # Search for just "ימוט"
    print(f"\nSearching for 'ימוט' alone:")
    yimot_results = search.search_word_with_variations("ימוט", level='consonantal', scope='auto', limit=5)
    for r in yimot_results:
        print(f"  - {r.reference}: '{r.matched_word}'")

    # Search for "לא ימוט"
    print(f"\nSearching for 'לא ימוט':")
    lo_yimot_results = search.search_phrase("לא ימוט", level='consonantal', scope='auto')
    for r in lo_yimot_results:
        print(f"  - {r.reference}")

    # Check if any of these are using fallback search_phrase_in_verse
    print("\n\n5. CHECKING IF FALLBACK SEARCH IS BEING USED:")
    print("-" * 40)

    # search_phrase_in_verse finds verses containing ALL words (not necessarily adjacent)
    fallback_results = search.search_phrase_in_verse(phrase, level='consonantal', scope='auto')
    print(f"search_phrase_in_verse (fallback) results: {len(fallback_results)}")
    for r in fallback_results:
        print(f"  - {r.reference}")

if __name__ == "__main__":
    test_exact_search()