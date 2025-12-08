#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script to trace phrase matching issues"""

import sys
import json
from pathlib import Path
from src.concordance.search import ConcordanceSearch
from src.concordance.hebrew_text_processor import normalize_for_search_split, split_on_maqqef

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize search
search = ConcordanceSearch()

def test_phrase_matching():
    print("=" * 80)
    print("DEBUGGING PHRASE MATCHING ISSUES")
    print("=" * 80)

    # Test case 1: Phrase that should NOT match but does (partial match)
    print("\n1. TESTING PARTIAL MATCH ISSUE:")
    print("-" * 40)
    phrase1 = "מי יגור באהלך"
    print(f"Searching for: {phrase1}")

    results1 = search.search_phrase(phrase1, level='consonantal', scope='auto')
    print(f"Results found: {len(results1)}")

    for r in results1[:3]:  # Show first 3 results
        print(f"\nResult: {r.reference}")
        print(f"Hebrew: {r.hebrew_text[:100]}...")
        print(f"English: {r.english_text[:100]}...")
        if hasattr(r, 'matched_phrase'):
            print(f"Matched phrase: {r.matched_phrase}")

    # Now check what the database actually contains
    print("\n--- Checking database content for matched verse ---")
    if results1:
        # Check words in the first result verse
        cursor = search.db.conn.cursor()
        cursor.execute("""
            SELECT position, word, word_consonantal_split
            FROM concordance
            WHERE book_name = ? AND chapter = ? AND verse = ?
            ORDER BY position
        """, (results1[0].book, results1[0].chapter, results1[0].verse))

        verse_words = cursor.fetchall()
        print(f"Verse {results1[0].reference} words:")
        for pos, word, cons_split in verse_words:
            if word.strip():
                print(f"  Pos {pos}: {word} (split: {cons_split})")

    # Test case 2: Phrase from Psalm 15 that should match but doesn't
    print("\n\n2. TESTING MISSING SOURCE PSALM PHRASE:")
    print("-" * 40)
    phrase2 = "דובר אמת בלבבו"
    print(f"Searching for: {phrase2}")

    # First check what Psalm 15:2 actually contains
    print("\n--- Checking Psalm 15:2 content ---")
    cursor = search.db.conn.cursor()
    cursor.execute("""
        SELECT position, word, word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15 AND verse = 2
        ORDER BY position
    """)

    psalm_words = cursor.fetchall()
    print("Psalm 15:2 words:")
    for pos, word, cons_split in psalm_words:
        if word.strip():
            print(f"  Pos {pos}: {word} (split: {cons_split})")

    # Now search for the phrase
    results2 = search.search_phrase(phrase2, level='consonantal', scope='auto')
    print(f"\nResults found: {len(results2)}")

    # Also test with source_psalm
    print("\n--- Testing with source_psalm scope ---")
    results2_src = search.search_phrase(phrase2, level='consonantal', scope='Psalms')
    print(f"Results with scope='Psalms': {len(results2_src)}")

    # Test case 3: Check normalization
    print("\n\n3. TESTING NORMALIZATION:")
    print("-" * 40)

    # Normalize the phrase
    phrase_split = split_on_maqqef(phrase2)
    words = phrase2.split()
    normalized_words = [normalize_for_search_split(w, 'consonantal') for w in words]

    print(f"Original phrase: {phrase2}")
    print(f"Split by maqqef: {phrase_split}")
    print(f"Words: {words}")
    print(f"Normalized words: {normalized_words}")

    # Check if these normalized words exist in Psalm 15:2
    verse_word_set = set()
    cursor.execute("""
        SELECT word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15 AND verse = 2
    """)

    for row in cursor.fetchall():
        if row[0] and row[0].strip():
            verse_word_set.add(row[0])

    print(f"\nNormalized words in Psalm 15:2: {sorted(verse_word_set)}")
    for norm_word in normalized_words:
        if norm_word in verse_word_set:
            print(f"✓ Found: {norm_word}")
        else:
            print(f"✗ Missing: {norm_word}")

    # Test case 4: Check if search_phrase uses variations
    print("\n\n4. TESTING VARIATIONS IN PHRASE SEARCH:")
    print("-" * 40)

    # Check if search_word_with_variations finds דובר
    first_word_var_results = search.search_word_with_variations("דובר", level='consonantal', scope='Psalms', limit=5)
    print(f"search_word_with_variations('דובר'): {len(first_word_var_results)} results")
    for r in first_word_var_results[:3]:
        print(f"  - {r.reference}: '{r.matched_word}'")

    # Check if it finds ודבר directly
    direct_search = search.search_word("ודבר", level='consonantal', scope='Psalms', limit=5)
    print(f"\nsearch_word('ודבר'): {len(direct_search)} results")
    for r in direct_search:
        print(f"  - {r.reference}: '{r.matched_word}'")

    # Test case 5: Debug why phrase search is failing
    print("\n\n5. DEBUGGING PHRASE SEARCH STEP BY STEP:")
    print("-" * 40)

    # Simulate what search_phrase does
    print("Simulating search_phrase steps:")

    # Step 1: Search for first word
    print(f"\nStep 1: Search for first word 'דובר'")
    first_word_results = search.search_word("דובר", level='consonantal', scope='Psalms', use_split=True)
    print(f"  Results: {len(first_word_results)}")

    # Step 2: If no results, try with variations (this should be done in search_word_with_variations)
    if not first_word_results:
        print("  No direct matches found, trying variations...")
        first_word_results = search.search_word_with_variations("דובר", level='consonantal', scope='Psalms', use_split=True)
        print(f"  With variations: {len(first_word_results)} results")

    # Step 3: Check each result for full phrase
    for i, match in enumerate(first_word_results[:3]):
        print(f"\nStep 3.{i+1}: Checking {match.reference} for full phrase")
        phrase_match = search._verse_contains_phrase(
            match.book, match.chapter, match.verse,
            match.word_position, normalized_words, 'word_consonantal_split'
        )
        print(f"  Phrase match result: {phrase_match}")

if __name__ == "__main__":
    test_phrase_matching()
