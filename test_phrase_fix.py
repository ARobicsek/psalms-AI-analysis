#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script to verify phrase search fixes"""

import sys
from src.concordance.search import ConcordanceSearch

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize search
search = ConcordanceSearch()

def test_original_vs_fixed():
    print("=" * 80)
    print("TESTING ORIGINAL vs FIXED PHRASE SEARCH")
    print("=" * 80)

    # Test phrases
    test_phrases = [
        ("דובר אמת בלבבו", "Psalm 15:2 - should match"),
        ("הללויה", "Simple praise phrase - should match many"),
        ("רגל על לשונו", "From Psalm 15:3 - should match"),
        ("לא ימוט לעולם", "Common phrase - should match"),
        ("מי יגור באהלך", "Should NOT match 'וישכן באהלי'"),
    ]

    for phrase, description in test_phrases:
        print(f"\nTesting: {phrase}")
        print(f"Description: {description}")
        print("-" * 60)

        # Original search_phrase
        original_results = search.search_phrase(phrase, level='consonantal', scope='auto')
        print(f"Original search_phrase: {len(original_results)} results")

        # Manual test with search_word_with_variations
        words = phrase.split()
        if len(words) >= 2:
            # Use search_word_with_variations for first word
            first_word_results = search.search_word_with_variations(words[0], level='consonantal', scope='auto')
            print(f"Using search_word_with_variations for first word: {len(first_word_results)} results")

            # Check if any match Psalm 15:2
            for r in first_word_results:
                if r.book == 'Psalms' and r.chapter == 15 and r.verse == 2:
                    print(f"  ✓ Found Psalm 15:2 with word '{r.matched_word}' at position {r.word_position}")

        # Show a few results
        for i, result in enumerate(original_results[:3]):
            print(f"  Result {i+1}: {result.reference} - '{result.matched_word}'")

def test_phrase_in_verse_method():
    print("\n\n" + "=" * 80)
    print("TESTING _verse_contains_phrase METHOD")
    print("=" * 80)

    # Test with Psalm 15:2
    cursor = search.db.conn.cursor()
    cursor.execute("""
        SELECT hebrew, english
        FROM verses
        WHERE book_name = 'Psalms' AND chapter = 15 AND verse = 2
    """)

    verse_info = cursor.fetchone()
    if verse_info:
        print(f"\nPsalm 15:2:")
        print(f"Hebrew: {verse_info[0]}")
        print(f"English: {verse_info[1]}")

    # Test phrase matching step by step
    phrase = "דובר אמת בלבבו"
    words = phrase.split()

    # Find the position of "ודבר" in Psalm 15:2
    cursor.execute("""
        SELECT position
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15 AND verse = 2
        AND word_consonantal_split = 'ודבר'
    """)

    pos_info = cursor.fetchone()
    if pos_info:
        start_pos = pos_info[0]
        print(f"\nFound 'ודבר' at position {start_pos}")

        # Check if phrase would match starting from this position
        # Note: We need to adjust normalized_words to match database form
        from src.concordance.hebrew_text_processor import normalize_for_search_split
        normalized_words = [normalize_for_search_split(w, 'consonantal') for w in words]

        # Replace first word with database form
        normalized_words[0] = 'ודבר'

        print(f"\nChecking phrase match with adjusted words: {normalized_words}")

        phrase_match = search._verse_contains_phrase(
            'Psalms', 15, 2,
            start_pos, normalized_words, 'word_consonantal_split'
        )
        print(f"Phrase match result: {phrase_match}")

if __name__ == "__main__":
    test_original_vs_fixed()
    test_phrase_in_verse_method()