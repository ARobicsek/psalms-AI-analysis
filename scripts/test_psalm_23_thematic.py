#!/usr/bin/env python3
"""
Direct test of Psalm 23 thematic parallels
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.thematic_parallels_librarian import create_thematic_librarian

# Psalm 23 verses in Hebrew
psalm_23_verses = [
    {"verse": 1, "hebrew": "מזמור לדוד יהוה רעי לא אחסר", "english": "A Psalm of David. The LORD is my shepherd; I shall not want."},
    {"verse": 2, "hebrew": "בנאות דשא ירביצני על מי מנחות ינהלני", "english": "He maketh me to lie down in green pastures: he leadeth me beside the still waters."},
    {"verse": 3, "hebrew": "נפשי ישובב ינחני במעגלי צדק למען שמו", "english": "He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake."},
    {"verse": 4, "hebrew": "גם כי אלך בגיא צלמות לא אירא רע כי אתה עמדי שבטך ומשענתך המה ינחמוני", "english": "Yea, though I walk through the valley of the shadow of death, I will fear no evil: for thou art with me; thy rod and thy staff they comfort me."},
    {"verse": 5, "hebrew": "תערוך לפני שלחן נגד צררי דשנת בשמן ראשי כוסי רויה", "english": "Thou preparest a table before me in the presence of mine enemies: thou anointest my head with oil; my cup runneth over."},
    {"verse": 6, "hebrew": "אך טוב וחסד ירדפוני כל ימי חיי ושבתי בבית יהוה לארך ימים", "english": "Surely goodness and mercy shall follow me all the days of my life: and I will dwell in the house of the LORD for ever."}
]

def main():
    print("Testing Thematic Parallels for Psalm 23")
    print("=" * 60)

    # Create librarian
    librarian = create_thematic_librarian()

    # Find parallels using 5-verse windowing
    parallels = librarian.find_parallels_for_psalm_with_windowing(
        psalm_number=23,
        verses=psalm_23_verses,
        window_size=5,
        window_overlap=4
    )

    if parallels:
        print(f"\n✅ Found {len(parallels)} thematic parallels\n")

        # Group by book category
        by_category = {}
        for parallel in parallels:
            category = parallel.book_category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(parallel)

        # Display results
        for category in ["Torah", "Prophets", "Writings"]:
            if category in by_category:
                print(f"\n{category.upper()}:")
                print("-" * 40)
                category_parallels = sorted(by_category[category], key=lambda p: p.similarity, reverse=True)
                for parallel in category_parallels[:5]:  # Top 5 per category
                    similarity_pct = int(parallel.similarity * 100)
                    print(f"\n{parallel.reference} (Similarity: {similarity_pct}%)")
                    print(f"Hebrew: {parallel.hebrew_text[:150]}...")
    else:
        print("\n❌ No thematic parallels found")

    print("\n" + "=" * 60)
    print("Test complete!")

if __name__ == "__main__":
    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')

    main()