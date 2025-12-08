#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Trace the exact bug in search_word_with_variations"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.concordance.search import ConcordanceSearch

def trace_search():
    """Trace what happens when searching for 'גור'"""

    search = ConcordanceSearch()

    # Write to file
    output = []

    # Step 1: Check normalization
    word = "גור"
    output.append(f"=== Searching for word: '{word}' ===")

    from src.concordance.hebrew_text_processor import normalize_for_search_split
    normalized = normalize_for_search_split(word, 'consonantal')
    output.append(f"Normalized form: '{normalized}'")

    # Step 2: Get variations
    variations = search._get_word_variations(normalized)
    output.append(f"\nGenerated {len(variations)} variations:")

    # Check if יגור is in variations
    target = "יגור"
    has_target = target in variations
    output.append(f"\nDoes variations include '{target}'? {has_target}")

    if has_target:
        output.append(f"✓ '{target}' found in variations!")
    else:
        output.append(f"✗ '{target}' NOT found in variations!")
        output.append("First 20 variations:")
        for i, var in enumerate(list(variations)[:20]):
            output.append(f"  {i+1}. '{var}'")

    # Step 3: Check database directly
    output.append(f"\n=== Database check for '{target}' ===")
    cursor = search.db.conn.cursor()
    cursor.execute("""
        SELECT book_name, chapter, verse, word
        FROM concordance
        WHERE word_consonantal_split = ?
        LIMIT 5
    """, (target,))

    results = cursor.fetchall()
    output.append(f"Direct DB query for '{target}' found {len(results)} results:")
    for row in results:
        output.append(f"  {row[0]} {row[1]}:{row[2]} - {row[3]}")

    # Step 4: Execute the actual search
    output.append(f"\n=== Actual search_word_with_variations('{word}') ===")
    search_results = search.search_word_with_variations(word, level='consonantal')
    output.append(f"Search returned {len(search_results)} results")

    # Check if Psalm 15:1 is in results
    psalm_15_1 = [r for r in search_results if r.book == 'Psalms' and r.chapter == 15 and r.verse == 1]
    output.append(f"Psalm 15:1 in results: {len(psalm_15_1)}")

    # Step 5: Manually construct and test the SQL
    output.append(f"\n=== Manual SQL test ===")
    if has_target:
        # Test with just the target variation
        cursor.execute(f"""
            SELECT DISTINCT
                c.book_name, c.chapter, c.verse, c.word, c.position
            FROM concordance c
            WHERE c.word_consonantal_split = ?
            ORDER BY c.book_name, c.chapter, c.verse, c.position
            LIMIT 10
        """, (target,))

        manual_results = cursor.fetchall()
        output.append(f"Manual SQL for '{target}' returned {len(manual_results)} results:")
        for row in manual_results:
            output.append(f"  {row[0]} {row[1]}:{row[2]} - {row[3]} (pos {row[4]})")

    # Write all output
    with open("search_trace.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print("Trace written to search_trace.txt")

if __name__ == "__main__":
    try:
        trace_search()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        with open("search_trace_error.txt", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)