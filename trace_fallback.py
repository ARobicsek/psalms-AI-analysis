#!/usr/bin/env python3
"""
Trace if the search is falling back to phrase-in-verse search
"""

import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
logger = logging.getLogger()

from src.concordance.search import ConcordanceSearch


def trace_fallback():
    """Trace if phrase search falls back to verse search"""

    print("=== Tracing Phrase Search Fallback ===")

    search = ConcordanceSearch()

    # Test phrase
    phrase = "מי יגור באהלך"
    print(f"\nSearching for: {phrase.encode('utf-8')}")

    # First try strict phrase search
    print("\n=== 1. Strict Phrase Search ===")
    results = search.search_phrase(phrase, level='consonantal', scope='Tanakh', limit=10)
    print(f"Strict search found: {len(results)} results")

    for result in results[:3]:
        print(f"  - {result.reference}")

    # Now try the fallback method directly
    print("\n=== 2. Fallback Verse Search (same verse search) ===")
    fallback_results = search.search_phrase_in_verse(phrase, level='consonantal', scope='Tanakh', limit=10)
    print(f"Fallback search found: {len(fallback_results)} results")

    # Check if Genesis 9:27 is in fallback results
    for result in fallback_results:
        if result.book == 'Genesis' and result.chapter == 9 and result.verse == 27:
            print(f"\n*** FOUND GENESIS 9:27 IN FALLBACK RESULTS ***")
            print(f"  Matched word: {result.matched_word.encode('utf-8')}")
            print(f"  Is phrase match: {result.is_phrase_match}")
            print(f"  Hebrew text length: {len(result.hebrew_text)} chars")

            # Get actual words in this verse
            cursor = search.db.conn.cursor()
            cursor.execute("""
                SELECT position, word_consonantal
                FROM concordance
                WHERE book_name = ? AND chapter = ? AND verse = ?
                ORDER BY position
            """, (result.book, result.chapter, result.verse))

            verse_words = [(row[0], row[1]) for row in cursor.fetchall()]
            print(f"\n  Verse words:")
            for pos, word in verse_words:
                print(f"    Pos {pos}: {word.encode('utf-8')}")

            # Check what words from our phrase are found
            phrase_words = phrase.split()
            print(f"\n  Phrase words: {[w.encode('utf-8') for w in phrase_words]}")
            print(f"  Which words are in the verse:")
            for pword in phrase_words:
                found = [(pos, w) for pos, w in verse_words if pword in w or w in pword]
                if found:
                    print(f"    '{pword.encode('utf-8')}' found in: {found}")
                else:
                    print(f"    '{pword.encode('utf-8')}' NOT FOUND")


if __name__ == "__main__":
    trace_fallback()