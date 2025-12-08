#!/usr/bin/env python3
"""Debug script to check why phrase validation is failing."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.concordance_librarian import ConcordanceRequest, ConcordanceLibrarian
from src.concordance.search import ConcordanceSearch
from src.data_sources.tanakh_database import TanakhDatabase

def debug_ii_chronicles():
    """Debug why II Chronicles 15:15 is matching 'ימר שבועה'."""

    print("Debugging II Chronicles 15:15 match for 'ימר שבועה'")
    print("=" * 60)

    # Initialize
    db = TanakhDatabase()
    search = ConcordanceSearch(db)

    # Check what words are in II Chronicles 15:15
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT word, word_consonantal_split, position
        FROM concordance
        WHERE book_name = '2 Chronicles' AND chapter = 15 AND verse = 15
        ORDER BY position
    """)

    verse_words = cursor.fetchall()
    print(f"\nWords in II Chronicles 15:15:")
    for word, split, pos in verse_words:
        print(f"  Pos {pos}: {word} ({split})")

    # Get the consonantal split words
    verse_split_words = [row[1] for row in verse_words if row[1] and row[1].strip()]
    print(f"\nSplit words: {verse_split_words}")

    # Check our phrase
    phrase = "ימר שבועה"
    print(f"\nSearching for phrase: {phrase}")

    # Get normalized words
    from src.concordance.hebrew_text_processor import split_words, normalize_word_sequence
    words = split_words(phrase)
    normalized_words = normalize_word_sequence(words, 'consonantal')
    print(f"Normalized words: {normalized_words}")

    # Check each word
    for word in normalized_words:
        print(f"\nChecking word: {word}")
        variations = search._get_word_variations(word)
        print(f"  Variations ({len(variations)}): {list(variations)[:10]}...")

        # Check if any variation is in the verse
        matches = [v for v in variations if v in verse_split_words]
        if matches:
            print(f"  MATCHES found: {matches}")
        else:
            print(f"  No matches in verse")

    # Final check
    print(f"\nFinal validation result:")
    result = search._verse_contains_all_words(
        '2 Chronicles', 15, 15,
        normalized_words,
        'word_consonantal_split'
    )
    print(f"  Verse contains ALL words: {result}")


if __name__ == "__main__":
    # Set UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    debug_ii_chronicles()