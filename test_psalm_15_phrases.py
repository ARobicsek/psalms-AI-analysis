#!/usr/bin/env python3
"""Test specific failing phrases from Psalm 15"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.concordance.search import ConcordanceSearch

def test_phrase(phrase, level='consonantal'):
    """Test a phrase search"""
    print("\n" + "="*60)
    print("Testing phrase: '{}' (level: {})".format(phrase, level))
    print("="*60)

    # Initialize search
    search = ConcordanceSearch("C:/Users/ariro/OneDrive/Documents/Bible/database/concordance_database.db")

    # Perform search
    results = search.search_phrase(phrase, level=level)

    print("\nResults found: {}".format(len(results)))

    if results:
        print("\nTop results:")
        for i, result in enumerate(results[:5], 1):
            print("\n{}. {} {}:{}".format(i, result.book, result.chapter, result.verse))
            print("   Hebrew: {}".format(result.hebrew[:100] + "..." if len(result.hebrew) > 100 else result.hebrew))
            print("   English: {}".format(result.english[:100] + "..." if len(result.english) > 100 else result.english))
            print("   Matched: {}".format(result.matched_hebrew))

    else:
        print("\n❌ NO RESULTS FOUND")
        print("\nDebugging - trying word by word:")
        words = phrase.split()
        for word in words:
            word_results = search.search_word(word, level=level)
            print("  Word '{}': {} results".format(word, len(word_results)))
            if word_results and len(word_results) <= 10:
                for wr in word_results[:3]:
                    print("    - {} {}:{}".format(wr.book, wr.chapter, wr.verse))

    return results

def main():
    """Test failing phrases from Psalm 15"""

    # Test the phrases that are failing
    phrases = [
        ("גור באהל", "consonantal"),
        ("הלך תמים", "consonantal"),
        # Also test with vowels
        ("יגור באהל", "consonantal"),
        ("הלך תם", "consonantal"),
        # Test individual words
        ("גור", "consonantal"),
        ("אהל", "consonantal"),
        ("הלך", "consonantal"),
        ("תמים", "consonantal"),
    ]

    for phrase, level in phrases:
        test_phrase(phrase, level)

    # Also test Psalm 15:1 directly
    print("\n" + "="*60)
    print("CHECKING PSALM 15:1 DIRECTLY")
    print("="*60)

    search = ConcordanceSearch("C:/Users/ariro/OneDrive/Documents/Bible/database/concordance_database.db")

    # Check if Psalm 15:1 is in the database
    psalm_results = search.search_word("יגור", book="Psalms", chapter=15)

    print("\nPsalm 15:1 results for 'יגור': {}".format(len(psalm_results)))
    for result in psalm_results:
        print("\n{} {}:{}".format(result.book, result.chapter, result.verse))
        print("Hebrew: {}".format(result.hebrew))
        print("Consonantal: {}".format(result.word_consonantal))
        print("Voweled: {}".format(result.word_voweled))

if __name__ == "__main__":
    main()