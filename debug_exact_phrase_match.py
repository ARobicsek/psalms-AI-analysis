#!/usr/bin/env python3
"""
Debug script to check why exact phrases from Psalm 15 are not being found.
"""

import sqlite3
from pathlib import Path

def check_exact_phrases():
    """Check if the exact phrases from Psalm 15 are in the database."""
    print("=" * 80)
    print("CHECKING EXACT PHRASE MATCHES")
    print("=" * 80)

    db_path = Path(__file__).parent / "database" / "tanakh.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # The failing phrases
    test_phrases = [
        ("הלך תמים", "Should match Psalm 15:2"),
        ("גור באהל", "Should match Psalm 15:1"),
        ("יגור באהל", "Should match Psalm 15:1"),
        ("הולך תמים", "Alternative form for Psalm 15:2")
    ]

    for phrase, description in test_phrases:
        print(f"\nTesting phrase: '{phrase}' ({description})")

        # Split into words
        words = phrase.split()
        print(f"  Words: {words}")

        # Check if all words exist in the database
        all_words_exist = True
        word_positions = {}

        for word in words:
            cursor.execute("""
                SELECT verse, position, word_consonantal_split
                FROM concordance
                WHERE book_name = 'Psalms' AND chapter = 15
                AND word_consonantal_split = ?
                ORDER BY verse, position
            """, (word,))
            results = cursor.fetchall()

            if results:
                print(f"    ✓ '{word}' found: {len(results)} times")
                word_positions[word] = results
                for r in results[:3]:  # Show first 3
                    print(f"      Psalm 15:{r[0]}, pos {r[1]}")
            else:
                print(f"    ✗ '{word}' NOT found in Psalm 15")
                all_words_exist = False

        # If all words exist, check if they appear in correct sequence
        if all_words_exist and len(words) > 1:
            print(f"  \nChecking if words appear in sequence:")
            found_sequence = False

            # Get all words in Psalm 15
            cursor.execute("""
                SELECT verse, position, word_consonantal_split
                FROM concordance
                WHERE book_name = 'Psalms' AND chapter = 15
                ORDER BY verse, position
            """)
            all_psalm_words = cursor.fetchall()

            # Create a list of just the words
            word_sequence = [w[2] for w in all_psalm_words]

            # Look for the sequence
            for i in range(len(word_sequence) - len(words) + 1):
                sequence = word_sequence[i:i+len(words)]
                if sequence == words:
                    found_sequence = True
                    start_pos = all_psalm_words[i][1]
                    print(f"    ✓ Found sequence starting at position {start_pos}")
                    # Show context
                    context_start = max(0, i - 2)
                    context_end = min(len(word_sequence), i + len(words) + 2)
                    context = word_sequence[context_start:context_end]
                    print(f"      Context: {' '.join(context)}")
                    break

            if not found_sequence:
                print(f"    ✗ Words not found in sequence")
                # Try alternative sequences
                for i in range(len(word_sequence)):
                    if word_sequence[i] == words[0]:
                        print(f"    Word '{words[0]}' found at position {all_psalm_words[i][1]}")
                        # Show what follows
                        next_words = word_sequence[i:i+len(words)]
                        print(f"      What follows: {' '.join(next_words)}")

    # Also test the concordance_librarian search method
    print("\n" + "=" * 80)
    print("TESTING CONCORDANCE LIBRARIAN SEARCH")
    print("=" * 80)

    try:
        import sys
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))

        from agents.concordance_librarian import ConcordanceLibrarian

        librarian = ConcordanceLibrarian()

        # Create a test request
        from agents.concordance_librarian import ConcordanceRequest

        request = ConcordanceRequest(
            phrase="גור באהל",
            level="consonantal",
            scope="auto"
        )

        print(f"\nSearching for 'גור באהל' with ConcordanceLibrarian...")
        results = librarian.search_concordance(request)

        print(f"Results: {len(results)}")
        for result in results[:3]:
            print(f"  - {result.reference}: {result.matched_hebrew}")

    except Exception as e:
        print(f"Error testing ConcordanceLibrarian: {e}")
        import traceback
        traceback.print_exc()

    conn.close()

def main():
    print("DEBUGGING EXACT PHRASE MATCH FAILURES")
    print("=" * 80)
    print("Issue: Exact phrases from micro analyst return 0 results")
    print("Expected: Should always find matches since micro analyst provides exact text")

    check_exact_phrases()

    print("\n" + "=" * 80)
    print("LIKELY ROOT CAUSES:")
    print("=" * 80)
    print("\n1. Micro analyst NOT providing exact phrase from verse")
    print("   - It might be providing a reduced form")
    print("   - Check micro analyst output for these phrases")

    print("\n2. Normalization issue")
    print("   - Database uses different normalization")
    print("   - Check word_consonantal_split vs word_consonantal")

    print("\n3. Word boundary issue")
    print("   - Search might be looking for exact whole phrase match")
    print("   - Not checking individual word positions")

if __name__ == "__main__":
    main()