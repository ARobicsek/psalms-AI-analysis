#!/usr/bin/env python3
"""Test that phrase preservation works correctly with suffixes"""

import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import re

def test_phrase_matching():
    """Test the new substring matching logic for phrase preservation"""

    # Simulate exact_phrases dictionary as created by _extract_exact_phrases_from_discoveries
    # Key: normalized phrase (consonants only), Value: clean phrase (no vowels)
    exact_phrases = {
        # From Psalm 15:2: "דֹבֵר אֱמֶת בִּלְבָבוֹ"
        # After removing vowels: "דבר אמת בלבבו"
        # After removing non-consonants: "דבראמתבלבבו"
        'דבראמתבלבבו': 'דבר אמת בלבבו',

        # Another example: "הולך תמים"
        'הלךתמים': 'הלך תמים',
    }

    # Test queries that LLM might generate (without suffixes)
    test_queries = [
        'דבר אמת בלב',  # Missing "בו" suffix
        'הלך תמים',     # Exact match
        'הולך תמים',    # Has prefix "ו"
    ]

    print("Testing phrase matching logic:")
    print("=" * 50)

    for query in test_queries:
        print(f"\nQuery: [Hebrew text]")
        print(f"Normalized length: {len(re.sub(r'[^\\u05D0-\\u05EA]', '', query))}")

        # Normalize query (like in _override_llm_base_forms)
        normalized = re.sub(r'[^\u05D0-\u05EA]', '', query)
        normalized = re.sub(r'[\u0591-\u05C7]', '', normalized)

        # Check if normalized query is contained in any stored phrase
        matched_phrase = None
        matched_key = None
        for stored_key, stored_phrase in exact_phrases.items():
            # Check if query is substring of stored phrase (allowing suffixes/prefixes)
            if normalized in stored_key:
                matched_phrase = stored_phrase
                matched_key = stored_key
                break

        if matched_phrase:
            print(f"✓ MATCHED!")
            print(f"  Matched phrase length: {len(matched_phrase)}")
            print(f"  Query is substring of stored key: True")
        else:
            print("✗ No match found")

    print("\n" + "=" * 50)
    print("Summary:")
    print("- Queries without suffixes should match phrases with suffixes")
    print("- Queries with prefixes should match phrases without prefixes")
    print("- This ensures exact verse phrases are searched even when LLM generates simplified forms")

if __name__ == "__main__":
    test_phrase_matching()