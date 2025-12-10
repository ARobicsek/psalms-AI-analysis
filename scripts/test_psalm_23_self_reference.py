#!/usr/bin/env python3
"""
Test Psalm 23 thematic search WITHOUT filtering to confirm Psalm 23 comes up as #1 match.
This script will output full results including Hebrew text for review.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.thematic_parallels_librarian import ThematicParallelsLibrarian


def main():
    print("="*80)
    print("PSALM 23 THEMATIC SELF-REFERENCE TEST")
    print("="*80)
    print("\nTesting that Psalm 23 appears as #1 match for its own verses")
    print("WITHOUT any filtering to exclude original verses\n")

    # Create librarian with lower threshold to get more results
    librarian = ThematicParallelsLibrarian(
        similarity_threshold=0.3,  # Lower threshold to get more matches
        max_results=20  # More results to see the full range
    )

    # Psalm 23 verses with Hebrew and English
    psalm_23_verses = [
        {
            "reference": "Psalm 23:1",
            "hebrew": "יהוה רעי לא אחסר",
            "english": "The LORD is my shepherd; I shall not want",
            "query": "יהוה רעי לא אחסר The LORD is my shepherd; I shall not want"
        },
        {
            "reference": "Psalm 23:2",
            "hebrew": "בנאות דשא ירביצני על מי מנחות ינהלני",
            "english": "He maketh me to lie down in green pastures: he leadeth me beside the still waters",
            "query": "בנאות דשא ירביצני על מי מנחות ינהלני He maketh me to lie down in green pastures"
        },
        {
            "reference": "Psalm 23:3",
            "hebrew": "נפשי ישובב ינחני במעגלי צדק למען שמו",
            "english": "He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake",
            "query": "נפשי ישובב ינחני במעגלי צדק למען שמו He restoreth my soul"
        },
        {
            "reference": "Psalm 23:4",
            "hebrew": "גם כי אלך בגיא צלמות לא אירא רע כי אתה עמדי",
            "english": "Yea, though I walk through the valley of the shadow of death, I will fear no evil: for thou art with me",
            "query": "גם כי אלך בגיא צלמות לא אירא רע כי אתה עמדי Yea though I walk through the valley of the shadow of death"
        },
        {
            "reference": "Psalm 23:5",
            "hebrew": "תערך לפני שלחן נגד צררי דשנת בשמן ראשי כוסי רויה",
            "english": "Thou preparest a table before me in the presence of mine enemies: thou anointest my head with oil; my cup runneth over",
            "query": "תערך לפני שלחן נגד צררי דשנת בשמן ראשי Thou preparest a table before me in the presence of mine enemies"
        },
        {
            "reference": "Psalm 23:6",
            "hebrew": "אך טוב וחסד ירדפוני כל ימי חיי",
            "english": "Surely goodness and mercy shall follow me all the days of my life",
            "query": "אך טוב וחסד ירדפוני כל ימי חיי Surely goodness and mercy shall follow me all the days of my life"
        }
    ]

    print(f"Vector Store Statistics:")
    print(f"  Total chunks: {librarian.vector_store.count()}")
    print(f"  Embedding model: {librarian.embedding_service.model_name}")
    print(f"  Similarity threshold: {librarian.similarity_threshold}")
    print(f"  Max results: {librarian.max_results}\n")

    # Test each verse
    for verse_data in psalm_23_verses:
        print("="*80)
        print(f"TESTING: {verse_data['reference']}")
        print("="*80)
        print(f"\nHebrew: {verse_data['hebrew']}")
        print(f"English: {verse_data['english']}\n")

        # Find parallels WITHOUT filtering (no query_verses parameter)
        parallels = librarian.find_parallels(verse_data['query'])

        print(f"Found {len(parallels)} parallels:\n")

        # Check if Psalm 23 is #1
        is_psalm_23_number_one = False
        if parallels and "Psalm 23" in parallels[0].reference:
            is_psalm_23_number_one = True

        for i, parallel in enumerate(parallels, 1):
            # Mark if this is Psalm 23
            marker = " ← PSALM 23!" if "Psalm 23" in parallel.reference else ""

            print(f"{i}. {parallel.reference}{marker}")
            print(f"   Similarity: {parallel.similarity:.4f}")
            print(f"   Book: {parallel.book} ({parallel.book_category})")
            print(f"   Context verses: {parallel.context_verses}")
            print(f"   Hebrew: {parallel.hebrew_text}")

            # Show English if available in metadata
            if hasattr(parallel, 'english_text') and parallel.english_text:
                print(f"   English: {parallel.english_text}")

            print()

        # Summary for this verse
        print("-" * 60)
        print(f"SUMMARY for {verse_data['reference']}:")
        print(f"  Psalm 23 is #1 match: {'YES ✓' if is_psalm_23_number_one else 'NO ✗'}")
        if is_psalm_23_number_one:
            print(f"  Similarity score: {parallels[0].similarity:.4f}")
        print(f"  Total parallels found: {len(parallels)}")
        print()

    print("="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    print("\nAll tests completed. Review the results above to confirm:")
    print("1. Psalm 23 appears as #1 match for each verse")
    print("2. Similarity scores are reasonable (>0.5 expected)")
    print("3. Hebrew text matches correctly")