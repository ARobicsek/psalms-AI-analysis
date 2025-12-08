#!/usr/bin/env python3
"""Debug the phrase search failure"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.concordance.search import ConcordanceSearch
from src.data_sources.tanakh_database import TanakhDatabase

def debug_phrase_matching():
    """Debug why phrase matching is failing"""

    # Initialize database and search
    db = TanakhDatabase("C:/Users/ariro/OneDrive/Documents/Bible/database/concordance_database.db")
    search = ConcordanceSearch("C:/Users/ariro/OneDrive/Documents/Bible/database/concordance_database.db")

    print("=== DEBUGGING PHRASE SEARCH FAILURE ===\n")

    # Test case 1: Check if Psalm 15:1 is in the database
    print("1. Checking if Psalm 15:1 exists in database...")
    psalm_15_1 = db.get_verse("Psalms", 15, 1)
    if psalm_15_1:
        print(f"Found Psalm 15:1")
        print(f"  Hebrew: {psalm_15_1.hebrew[:100]}...")
        print(f"  Consonantal text: {psalm_15_1.text_consonantal[:100]}...")

        # Check word splits
        words = psalm_15_1.text_consonantal.split()
        print(f"  Words: {words[:10]}...")
    else:
        print("Psalm 15:1 not found!")
        return

    # Test case 2: Search for individual words
    print("\n2. Testing individual word searches...")
    test_words = ["יגור", "גור", "אהל", "באהל"]
    for word in test_words:
        results = search.search_word(word, level='consonantal')
        print(f"  '{word}': {len(results)} results")
        # Check if Psalm 15:1 is in results
        psalm_found = any(r.book == "Psalms" and r.chapter == 15 and r.verse == 1 for r in results)
        print(f"    Psalm 15:1 found: {'YES' if psalm_found else 'NO'}")

    # Test case 3: Test phrase search directly
    print("\n3. Testing phrase search...")
    test_phrases = [
        ("גור באהל", "consonantal"),
        ("יגור באהל", "consonantal"),
        ("מי יגור", "consonantal"),
    ]

    for phrase, level in test_phrases:
        print(f"\n  Testing phrase: '{phrase}' (level: {level})")
        results = search.search_phrase(phrase, level=level)
        print(f"    Results: {len(results)}")

        if results:
            print("    Top 3 results:")
            for i, r in enumerate(results[:3], 1):
                print(f"      {i}. {r.book} {r.chapter}:{r.verse}")

    # Test case 4: Check the search_phrase implementation
    print("\n4. Examining search_phrase implementation...")

    # Let's trace what happens with a specific phrase
    phrase = "גור באהל"
    print(f"\n  Tracing search for '{phrase}':")

    # Check word splitting
    words = phrase.split()
    print(f"    Words: {words}")

    # Check first word search
    print(f"    Searching for first word '{words[0]}'...")
    first_word_results = search.search_word_with_variations(words[0], level='consonantal')
    print(f"    First word results: {len(first_word_results)}")

    if first_word_results:
        # Check if Psalm 15:1 is among first word results
        psalm_in_first = any(r.book == "Psalms" and r.chapter == 15 and r.verse == 1 for r in first_word_results)
        print(f"    Psalm 15:1 in first word results: {'YES' if psalm_in_first else 'NO'}")

        # If Psalm 15:1 is found, check subsequent words
        if psalm_in_first:
            print(f"    Checking subsequent words in Psalm 15:1...")
            for word in words[1:]:
                has_word = search._verse_contains_word("Psalms", 15, 1, word, 'word_consonantal')
                print(f"      '{word}': {'YES' if has_word else 'NO'}")

    # Test case 5: Check _verse_contains_phrase directly
    print("\n5. Testing _verse_contains_phrase...")
    if psalm_15_1:
        contains_phrase = search._verse_contains_phrase(
            psalm_15_1.book, psalm_15_1.chapter, psalm_15_1.verse,
            phrase, 'consonantal'
        )
        print(f"  _verse_contains_phrase('{phrase}'): {contains_phrase}")

        # Check with different phrase variations
        variations = ["מי יגור", "יגור באהל", "מי יגור באהל"]
        for var in variations:
            contains = search._verse_contains_phrase(
                psalm_15_1.book, psalm_15_1.chapter, psalm_15_1.verse,
                var, 'consonantal'
            )
            print(f"  _verse_contains_phrase('{var}'): {contains}")

if __name__ == "__main__":
    debug_phrase_matching()