#!/usr/bin/env python3
"""Debug the phrase matching issue with Numbers 13:23"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Fix imports
import importlib.util
spec = importlib.util.spec_from_file_location("tanakh_database", os.path.join(os.path.dirname(__file__), "src", "data_sources", "tanakh_database.py"))
tanakh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tanakh)

sys.modules['src.data_sources.tanakh_database'] = tanakh
sys.modules['src.data_sources'] = tanakh

from src.concordance.search import ConcordanceSearch

def test_numbers_13_23():
    """Test why Numbers 13:23 matches 'לֹא יִמּוֹט'"""

    # Find the database
    db_path = None
    for root, dirs, files in os.walk('.'):
        if 'hebrew_concordance.db' in files:
            db_path = os.path.join(root, 'hebrew_concordance.db')
            break

    if not db_path:
        print("ERROR: Could not find concordance database")
        return

    search = ConcordanceSearch(db_path)

    # Test the verse checker
    print("Testing Numbers 13:23 with word 'לא':")
    contains_lo = search._verse_contains_all_words(
        'Numbers', 13, 23, ['לא'], 'word_consonantal'
    )
    print(f"Contains 'לא': {contains_lo}")

    print("\nTesting Numbers 13:23 with word 'ימוט':")
    contains_mot = search._verse_contains_all_words(
        'Numbers', 13, 23, ['ימוט'], 'word_consonantal'
    )
    print(f"Contains 'ימוט': {contains_mot}")

    print("\nTesting Numbers 13:23 with both words ['לא', 'ימוט']:")
    contains_both = search._verse_contains_all_words(
        'Numbers', 13, 23, ['לא', 'ימוט'], 'word_consonantal'
    )
    print(f"Contains both: {contains_both}")

    # Check what variations are generated for 'ימוט'
    print("\nVariations generated for 'ימוט':")
    mot_variations = search._get_word_variations('ימוט')
    print(f"Count: {len(mot_variations)}")
    print(f"Variations containing 'מוט': {[v for v in mot_variations if 'מוט' in v]}")

    # Get all words in Numbers 13:23
    cursor = search.db.conn.cursor()
    cursor.execute("""
        SELECT word_text, word_consonantal
        FROM concordance
        WHERE book_name = 'Numbers' AND chapter = 13 AND verse = 23
    """)
    verse_words = cursor.fetchall()
    print(f"\nWords in Numbers 13:23 (showing first 20):")
    for i, (text, consonantal) in enumerate(verse_words[:20]):
        print(f"  {i+1}. {text} -> {consonantal}")

if __name__ == "__main__":
    test_numbers_13_23()