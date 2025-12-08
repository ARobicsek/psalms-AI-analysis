#!/usr/bin/env python3
"""Debug script to understand phrase extraction and matching"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import re

def test_normalization():
    """Test how phrases are being normalized"""

    # From micro analyst (with vowel points)
    original_phrase = "דֹבֵר אֱמֶת בִּלְבָבוֹ"

    # What LLM generates (without suffix)
    llm_query = "דבר אמת בלב"

    print("Original phrase (from micro analyst):")
    # Can't print Hebrew due to console encoding

    # Remove vowel points (like in _extract_exact_phrases_from_discoveries)
    clean_phrase = re.sub(r'[\u0591-\u05C7]', '', original_phrase)
    print(f"  Clean (no vowels): [Hebrew text]")

    # Create normalized key for matching (like in the extraction method)
    key = re.sub(r'[^\u05D0-\u05EA]', '', clean_phrase)
    # Can't print Hebrew due to console encoding issues
    print("  Normalized key length:", len(key))

    print("\nLLM generated query:")
    # Can't print Hebrew due to console encoding

    # Normalize for matching (like in _override_llm_base_forms)
    normalized = re.sub(r'[^\u05D0-\u05EA]', '', llm_query)
    normalized = re.sub(r'[\u0591-\u05C7]', '', normalized)
    print("  Normalized length:", len(normalized))

    print(f"\nDo they match? {key == normalized}")

    # Show the difference
    if key != normalized:
        print("\nDifference:")
        diff = key.replace(normalized, '')
        print(f"  Length difference: {len(key) - len(normalized)} characters")
        if len(diff) > 0:
            print(f"  Key has extra characters (likely suffixes):")
            for i, char in enumerate(diff):
                print(f"    Char {i}: 0x{ord(char):04X}")

if __name__ == "__main__":
    test_normalization()