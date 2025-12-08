#!/usr/bin/env python3
"""
Trace exactly which variation matched and what words were found.
"""

import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger()

from src.concordance.search import ConcordanceSearch
from src.agents.concordance_librarian import ConcordanceRequest, ConcordanceLibrarian
from src.concordance.hebrew_text_processor import normalize_for_search


def trace_exact_match():
    """Trace exactly what variation matched Psalm 15:1 for our test phrase."""

    print("=== Tracing Exact Match ===")

    # Initialize search directly (without librarian to see raw results)
    search = ConcordanceSearch()

    # Test phrase
    phrase = "מי יגור באהלך"
    print(f"\nSearching for phrase (bytes): {phrase.encode('utf-8')}")

    # Get the normalized form
    words = phrase.split()
    print(f"Original words (bytes): {[w.encode('utf-8') for w in words]}")

    # Test strict phrase search
    results = search.search_phrase(phrase, level='consonantal', scope='Tanakh', limit=10)

    print(f"\nStrict phrase search found: {len(results)} results")

    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  Reference: {result.reference}")
        print(f"  Matched word (bytes): {result.matched_word.encode('utf-8')}")
        print(f"  Hebrew text length: {len(result.hebrew_text)} chars")
        print(f"  Is phrase match: {result.is_phrase_match}")
        print(f"  Word position: {result.word_position}")

        # Get the actual words in that verse
        cursor = search.db.conn.cursor()
        cursor.execute("""
            SELECT position, word_consonantal
            FROM concordance
            WHERE book_name = ? AND chapter = ? AND verse = ?
            ORDER BY position
        """, (result.book, result.chapter, result.verse))

        verse_words = [(row[0], row[1]) for row in cursor.fetchall()]
        print(f"\n  Verse words (count: {len(verse_words)}):")
        for pos, word in verse_words:
            print(f"    Pos {pos}: {word.encode('utf-8')}")

        # Check the specific variation that matched
        if result.matched_word != phrase:
            print(f"\n  DIFFERENT VARIATION MATCHED!")
            print(f"  Original phrase: {phrase.encode('utf-8')}")
            print(f"  Matched variation: {result.matched_word.encode('utf-8')}")
            matched_words = result.matched_word.split()
            print(f"  Matched variation has {len(matched_words)} words")

            # Check each word from the matched variation
            print(f"\n  Checking each word from matched variation:")
            for j, var_word in enumerate(matched_words):
                print(f"    Word {j}: {var_word.encode('utf-8')}")
                # Find where this word appears in the verse
                matches = [(pos, w) for pos, w in verse_words if w == var_word]
                if matches:
                    print(f"      Found at position(s): {matches}")
                else:
                    # Check for partial/inclusion matches
                    partial_matches = [(pos, w) for pos, w in verse_words if var_word in w or w in var_word]
                    if partial_matches:
                        print(f"      Partial match with: {partial_matches}")
                    else:
                        print(f"      NOT FOUND in verse!")

        # Summary of what matched
        print(f"\n  SUMMARY:")
        if result.is_phrase_match:
            print(f"    Was marked as phrase match")
        else:
            print(f"    Was NOT marked as phrase match")


if __name__ == "__main__":
    trace_exact_match()