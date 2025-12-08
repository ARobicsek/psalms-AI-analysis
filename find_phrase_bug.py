#!/usr/bin/env python3
"""
Find the phrase matching bug and save results to file.
"""

import sqlite3
import sys
from pathlib import Path

def main():
    # Create output file
    output_file = Path(__file__).parent / "phrase_bug_analysis.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("PHRASE MATCHING BUG ANALYSIS\n")
        f.write("=" * 80 + "\n\n")

        db_path = Path(__file__).parent / "database" / "tanakh.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 1. Check Psalm 15:1 words
        f.write("1. Words in Psalm 15:1:\n")
        cursor.execute("""
            SELECT position, word_consonantal_split
            FROM concordance
            WHERE book_name = 'Psalms' AND chapter = 15 AND verse = 1
            ORDER BY position
        """)
        words = cursor.fetchall()
        for word in words:
            f.write(f"  Position {word[0]}: {word[1]}\n")

        # 2. Check for 'יגור'
        f.write("\n2. Words containing 'גור' in Psalm 15:\n")
        cursor.execute("""
            SELECT verse, position, word_consonantal_split
            FROM concordance
            WHERE book_name = 'Psalms' AND chapter = 15
            AND word_consonantal_split LIKE '%גור%'
            ORDER BY verse, position
        """)
        results = cursor.fetchall()
        f.write(f"  Found {len(results)} matches:\n")
        for r in results:
            f.write(f"    Psalm 15:{r[0]}, Pos {r[1]}: {r[2]}\n")

        # 3. Test variation generation if possible
        f.write("\n3. Testing variation generation:\n")
        src_path = Path(__file__).parent / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        try:
            from concordance.search import ConcordanceSearch
            search = ConcordanceSearch()

            # Test 'גור'
            f.write("\n  Variations for 'גור':\n")
            variations = search._get_word_variations('גור')
            f.write(f"    Total: {len(variations)} variations\n")

            # Check for 'יגור'
            if 'יגור' in variations:
                f.write("    ✓ 'יגור' is in variations!\n")
            else:
                f.write("    ✗ 'יגור' is NOT in variations!\n")

            # Show first 10
            f.write("    First 10 variations:\n")
            for i, var in enumerate(list(variations)[:10]):
                f.write(f"      {i+1}. {var}\n")

            # Test search
            f.write("\n  search_word_with_variations('גור') results:\n")
            results = search.search_word_with_variations('גור', level='consonantal')
            psalm15_results = [r for r in results
                             if r.book == 'Psalms' and r.chapter == 15]
            f.write(f"    Results in Psalm 15: {len(psalm15_results)}\n")
            for r in psalm15_results:
                f.write(f"      - {r.reference}: {r.matched_word}\n")

        except Exception as e:
            f.write(f"    Error: {e}\n")
            import traceback
            traceback.print_exc(file=f)

        conn.close()

        # 4. Analysis
        f.write("\n" + "=" * 80 + "\n")
        f.write("ANALYSIS:\n")
        f.write("\nThe issue appears to be:\n")
        f.write("1. Psalm 15:1 contains 'יגור' (prefixed form)\n")
        f.write("2. Micro analyst provides base form 'גור'\n")
        f.write("3. Variation generator must add 'י' prefix to match\n")
        f.write("4. If not finding match, variation generator is incomplete\n")

    print(f"Analysis saved to {output_file}")
    print("Please check the file for results.")

if __name__ == "__main__":
    main()