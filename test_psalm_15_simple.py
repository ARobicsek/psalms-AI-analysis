#!/usr/bin/env python3
"""Simple test without Hebrew printing"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.concordance.search import ConcordanceSearch

def test_phrase_simple(phrase, level='consonantal'):
    """Test a phrase search without printing Hebrew"""
    print("\nTesting phrase ID")

    # Initialize search
    search = ConcordanceSearch("C:/Users/ariro/OneDrive/Documents/Bible/database/concordance_database.db")

    # Perform search
    results = search.search_phrase(phrase, level=level)

    print("Results found: {}".format(len(results)))

    if results:
        print("Top results:")
        for i, result in enumerate(results[:5], 1):
            print("  {}. {} {}:{}".format(i, result.book, result.chapter, result.verse))
            # Don't print Hebrew text, just counts
            print("     Has Hebrew: {}".format(bool(result.hebrew)))

    else:
        print("NO RESULTS FOUND")
        print("Debugging - trying word by word:")
        words = phrase.split()
        for word in words:
            word_results = search.search_word(word, level=level)
            print("  Word ID {}: {} results".format(id(word), len(word_results)))

    return results

def main():
    """Test failing phrases from Psalm 15"""

    # Test the phrases that are failing - use simple representation
    test_cases = [
        ("gvr bahl", "גור באהל", "consonantal"),
        ("hlk tmim", "הלך תמים", "consonantal"),
        ("ygvr bahl", "יגור באהל", "consonantal"),
        ("hlk tm", "הלך תם", "consonantal"),
    ]

    for case_id, hebrew_phrase, level in test_cases:
        print("\n" + "="*60)
        print("Test case: {} -> '{}'".format(case_id, hebrew_phrase))
        print("="*60)
        results = test_phrase_simple(hebrew_phrase, level)

    # Check Psalm 15:1 directly
    print("\n" + "="*60)
    print("CHECKING PSALM 15:1 FOR WORDS")
    print("="*60)

    search = ConcordanceSearch("C:/Users/ariro/OneDrive/Documents/Bible/database/concordance_database.db")

    # Test individual words from Psalm 15:1
    words_to_test = ["יגור", "באהל", "שכן", "הר", "קדש"]

    for word in words_to_test:
        word_results = search.search_word(word, book="Psalms", chapter=15)
        print("\nWord '{}' in Psalm 15: {} results".format(word, len(word_results)))
        for result in word_results[:2]:
            print("  Verse {}: found".format(result.verse))

if __name__ == "__main__":
    main()