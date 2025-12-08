"""
Detailed test to examine how phrase variations match actual database content.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_sources.tanakh_database import TanakhDatabase
from src.concordance.hebrew_text_processor import normalize_for_search_split

def examine_psalm_15_1():
    """Examine the actual Hebrew words in Psalm 15:1 from the database."""

    print("=" * 80)
    print("Examining Psalm 15:1 Word-by-Word")
    print("=" * 80)

    db = TanakhDatabase()

    # Query all words from Psalm 15:1
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT position, word, word_voweled, word_consonantal, word_consonantal_split
        FROM concordance
        WHERE book_name = 'Psalms' AND chapter = 15 AND verse = 1
        ORDER BY position
    """)

    print("\nWords in Psalm 15:1:")
    print("-" * 80)
    print(f"{'Pos':<4} {'Word (exact)':<20} {'Voweled':<20} {'Consonantal':<20} {'Split':<20}")
    print("-" * 80)

    words_for_phrase = []
    for row in cursor.fetchall():
        pos = row['position']
        word = row['word']
        voweled = row['word_voweled']
        consonantal = row['word_consonantal']
        split = row['word_consonantal_split']

        print(f"{pos:<4} {word:<20} {voweled:<20} {consonantal:<20} {split:<20}")

        # Collect positions 8 and 9 (the phrase we're looking for)
        if pos in [8, 9]:
            words_for_phrase.append((pos, word, consonantal, split))

    print("\n" + "=" * 80)
    print("Analysis of positions 8-9 (target phrase)")
    print("=" * 80)

    if len(words_for_phrase) >= 2:
        pos1, word1, cons1, split1 = words_for_phrase[0]
        pos2, word2, cons2, split2 = words_for_phrase[1]

        print(f"\nPosition {pos1}:")
        print(f"  Exact:       {word1}")
        print(f"  Consonantal: {cons1}")
        print(f"  Split:       {split1}")

        print(f"\nPosition {pos2}:")
        print(f"  Exact:       {word2}")
        print(f"  Consonantal: {cons2}")
        print(f"  Split:       {split2}")

        # Now test what our search would normalize to
        from src.agents.concordance_librarian import ConcordanceLibrarian

        librarian = ConcordanceLibrarian()

        test_phrase = "הר קדש"
        print(f"\n" + "=" * 80)
        print(f"Testing how '{test_phrase}' matches the database")
        print("=" * 80)

        # Normalize our search phrase
        search_word1_norm = normalize_for_search_split("הר", "consonantal")
        search_word2_norm = normalize_for_search_split("קדש", "consonantal")

        print(f"\nBase phrase normalized:")
        print(f"  Word 1: 'הר' → '{search_word1_norm}'")
        print(f"  Word 2: 'קדש' → '{search_word2_norm}'")

        print(f"\nDatabase at positions 8-9:")
        print(f"  Word 1: '{split1}'")
        print(f"  Word 2: '{split2}'")

        print(f"\nMatch?")
        print(f"  Word 1: {search_word1_norm} == {split1} ? {search_word1_norm == split1}")
        print(f"  Word 2: {search_word2_norm} == {split2} ? {search_word2_norm == split2}")

        # Now test with prefix and suffix
        search_with_prefix_suffix = normalize_for_search_split("בהר קדשך", "consonantal")
        print(f"\n\nVariation 'בהר קדשך' normalized: '{search_with_prefix_suffix}'")

        # Split it
        from src.concordance.hebrew_text_processor import split_words
        words = split_words(search_with_prefix_suffix)
        if len(words) >= 2:
            word1_var = normalize_for_search_split(words[0], "consonantal")
            word2_var = normalize_for_search_split(words[1], "consonantal")

            print(f"  Word 1: '{words[0]}' → '{word1_var}'")
            print(f"  Word 2: '{words[1]}' → '{word2_var}'")

            print(f"\nMatch?")
            print(f"  Word 1: {word1_var} == {split1} ? {word1_var == split1}")
            print(f"  Word 2: {word2_var} == {split2} ? {word2_var == split2}")

            if word1_var == split1 and word2_var == split2:
                print("\n✓ SUCCESS! The variation 'בהר קדשך' matches Psalm 15:1!")
            else:
                print("\n✗ NO MATCH - need to investigate further")

    db.close()


def test_other_phrases():
    """Test a few more phrase searches to ensure robustness."""

    print("\n\n" + "=" * 80)
    print("Additional Phrase Search Tests")
    print("=" * 80)

    from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest

    librarian = ConcordanceLibrarian()

    test_cases = [
        ("יהוה רעי", "Psalms", "The LORD is my shepherd (Psalm 23:1)"),
        ("מלך כבוד", "Psalms", "King of glory (Psalm 24)"),
        ("אלהי צדקי", "Psalms", "God of my righteousness (Psalm 4:1)"),
    ]

    for phrase, scope, description in test_cases:
        print(f"\n{'-' * 80}")
        print(f"Testing: {phrase} ({description})")
        print(f"Scope: {scope}")

        request = ConcordanceRequest(
            query=phrase,
            scope=scope,
            level='consonantal',
            include_variations=True,
            max_results=5
        )

        bundle = librarian.search_with_variations(request)

        print(f"Found {len(bundle.results)} results")
        print(f"Searched {len(bundle.variations_searched)} variations")

        if bundle.results:
            print(f"\nTop results:")
            for i, result in enumerate(bundle.results[:3], 1):
                print(f"  {i}. {result.reference}")
                print(f"     {result.hebrew_text[:80]}...")
                print(f"     {result.english_text[:80]}...")


if __name__ == '__main__':
    # Ensure UTF-8 encoding on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    examine_psalm_15_1()
    test_other_phrases()
