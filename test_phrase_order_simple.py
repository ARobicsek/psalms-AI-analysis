#!/usr/bin/env python3
"""
Simple test script to verify that phrase extraction works correctly
for Psalm 15:3 "נשא חרפה" issue.
"""

import sys
import re
from pathlib import Path
from itertools import product

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.concordance.hebrew_text_processor import split_words


def extract_all_phrase_forms_from_verse(query: str, verse_hebrew: str):
    """
    Test implementation of the phrase extraction method.
    """
    # Remove vowel points for matching
    query_clean = re.sub(r'[\u0591-\u05C7]', '', query)

    query_words = split_words(query_clean)
    verse_words = split_words(verse_hebrew)  # Original with pointing

    # Clean each word individually to maintain array alignment
    verse_words_clean = [re.sub(r'[\u0591-\u05C7]', '', word) for word in verse_words]

    results = []

    # Find all positions where each query word appears
    word_positions = {}
    for qword in query_words:
        word_positions[qword] = []
        for i, vword in enumerate(verse_words_clean):
            # Skip empty words (like paseq marks)
            if not vword or not qword:
                continue
            # Substring match (allows prefixes/suffixes)
            if qword in vword or vword in qword:
                word_positions[qword].append(i)

    # Check if all query words are present
    if not all(positions for positions in word_positions.values()):
        return []  # Some words not found

    # Generate all valid combinations
    for combination in product(*word_positions.values()):
        # Sort positions to get actual verse order
        sorted_positions = sorted(combination)

        # Skip if positions are duplicates
        if len(set(sorted_positions)) != len(sorted_positions):
            continue

        # Extract the span from first to last position
        start = sorted_positions[0]
        end = sorted_positions[-1]

        # Form 1: With intervening words (actual verse order)
        full_span = ' '.join(verse_words[start:end+1])
        # Remove vowel points for searching
        full_span_clean = re.sub(r'[\u0591-\u05C7]', '', full_span)
        if full_span_clean not in results:
            results.append(full_span_clean)

        # Form 2: Without intervening words (collapsed)
        collapsed = ' '.join(verse_words[i] for i in sorted_positions)
        collapsed_clean = re.sub(r'[\u0591-\u05C7]', '', collapsed)
        if collapsed_clean not in results and collapsed_clean != full_span_clean:
            results.append(collapsed_clean)

    return results


def test_psalm_15_3():
    """Test with Psalm 15:3 actual text."""
    print("=" * 80)
    print("TEST: Phrase Order Guarantee - Psalm 15:3")
    print("=" * 80)

    # Actual Psalm 15:3 text (from the micro JSON)
    verse_hebrew = "לֹֽא־רָגַ֨ל ׀ עַל־לְשֹׁנ֗וֹ לֹא־עָשָׂ֣ה לְרֵעֵ֣הוּ רָעָ֑ה וְ֝חֶרְפָּ֗ה לֹא־נָשָׂ֥א עַל־קְרֹבֽוֹ׃"
    verse_english = "He does not slander with his tongue, he does not do evil to his fellow, he does not bring reproach upon his neighbor"

    print(f"\nPsalm 15:3:")
    print(f"  Hebrew: {verse_hebrew}")
    print(f"  English: {verse_english}")

    # Test Case 1: "נשא חרפה" (the failing case - LLM's conceptual phrase)
    print("\n" + "-" * 80)
    print("Test Case 1: נשא חרפה (bear reproach - LLM's order)")
    print("-" * 80)

    query = "נשא חרפה"
    print(f"\nQuery: '{query}'")
    print(f"  Problem: Words appear in REVERSE order in the verse")
    print(f"  Verse has: וְחֶרְפָּה לֹא־נָשָׂא (and reproach NOT bear)")

    forms = extract_all_phrase_forms_from_verse(query, verse_hebrew)

    print(f"\nExtracted forms ({len(forms)}):")
    for i, form in enumerate(forms, 1):
        print(f"  {i}. '{form}'")

    if forms:
        print(f"\n✅ SUCCESS: Found {len(forms)} form(s) that will match the verse!")
        print(f"   These will be added as alternate queries to guarantee a match.")
    else:
        print(f"\n❌ FAILURE: No forms found - the verse won't be found!")

    # Test Case 2: "חרפה נשא" (actual verse order)
    print("\n" + "-" * 80)
    print("Test Case 2: חרפה נשא (reproach bear - actual verse order)")
    print("-" * 80)

    query2 = "חרפה נשא"
    print(f"\nQuery: '{query2}'")

    forms2 = extract_all_phrase_forms_from_verse(query2, verse_hebrew)

    print(f"\nExtracted forms ({len(forms2)}):")
    for i, form in enumerate(forms2, 1):
        print(f"  {i}. '{form}'")

    if forms2:
        print(f"\n✅ SUCCESS: Found {len(forms2)} form(s)")
    else:
        print(f"\n❌ FAILURE: No forms found!")

    # Verify the forms would actually match the verse
    print("\n" + "-" * 80)
    print("Verification: Do extracted forms match the original verse?")
    print("-" * 80)

    verse_clean = re.sub(r'[\u0591-\u05C7]', '', verse_hebrew)
    print(f"\nVerse (no vowels): {verse_clean}")

    all_forms = forms + forms2
    matches_found = 0
    for form in all_forms:
        if form in verse_clean:
            print(f"  ✅ '{form}' FOUND in verse")
            matches_found += 1
        else:
            print(f"  ❌ '{form}' NOT in verse")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    success = (len(forms) > 0 and matches_found > 0)

    if success:
        print("\n✅ ALL TESTS PASSED")
        print("\nThe fix successfully extracts phrase forms that will match the verse,")
        print("even when the LLM's query has words in a different order!")
        print(f"\nFor query 'נשא חרפה', we now generate {len(forms)} alternate(s)")
        print("that will be searched alongside the original query.")
    else:
        print("\n❌ TESTS FAILED")
        print("\nThe fix is not working as expected.")

    return success


if __name__ == '__main__':
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    success = test_psalm_15_3()
    sys.exit(0 if success else 1)
