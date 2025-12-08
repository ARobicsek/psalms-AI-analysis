#!/usr/bin/env python3
"""
Debug why variations are causing bad matches
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.concordance_librarian import ConcordanceLibrarian
from src.concordance.hebrew_text_processor import normalize_for_search


def debug_variations():
    """Debug what variations are generated and why bad matches occur."""

    print("=== Debugging Variations ===")

    librarian = ConcordanceLibrarian()

    # Generate variations for the problematic phrase
    phrase = "מי יגור באהלך"
    print(f"\nOriginal phrase: {phrase.encode('utf-8')}")

    variations = librarian.generate_phrase_variations(phrase, level='consonantal')
    print(f"\nTotal variations generated: {len(variations)}")

    # Look for the bad variation that matched Genesis 9:27
    target_match = "וישכן באהלי"
    print(f"\nLooking for variation that would match: {target_match.encode('utf-8')}")

    # Check first 20 variations
    print(f"\nFirst 20 variations:")
    for i, var in enumerate(variations[:20]):
        print(f"  {i+1:3d}. {var.encode('utf-8')}")

    # Check if target words appear in any variation
    target_words = set(target_match.split())
    print(f"\nTarget words: {[w.encode('utf-8') for w in target_words]}")

    matching_vars = []
    for i, var in enumerate(variations):
        var_words = set(var.split())
        # Check if ANY target word appears in the variation
        common = target_words.intersection(var_words)
        if common:
            matching_vars.append((i, var, common))
            if len(matching_vars) <= 5:  # Show first 5
                print(f"\nVariation {i} shares words: {[w.encode('utf-8') for w in common]}")
                print(f"  Full variation: {var.encode('utf-8')}")

    print(f"\nTotal variations with any target word: {len(matching_vars)}")

    # Check specifically for the issue: single word variations
    print(f"\n=== Checking for single-word variations ===")
    single_word_vars = [v for v in variations if len(v.split()) == 1]
    print(f"Single-word variations: {len(single_word_vars)}")

    # Check if any single word variation contains just "באהל" or similar
    for var in single_word_vars[:10]:
        if "באהל" in var:
            print(f"  Found problematic variation: {var.encode('utf-8')}")

    # Check the suffix variations generation
    print(f"\n=== Suffix Variations Analysis ===")
    words = phrase.split()
    print(f"Original words: {[w.encode('utf-8') for w in words]}")

    # For each word, show some variations
    for word in words:
        print(f"\nVariations for '{word.encode('utf-8')}':")
        word_vars = [v for v in variations if v.startswith(word) or v.endswith(word) or word in v][:5]
        for var in word_vars:
            print(f"  - {var.encode('utf-8')}")


if __name__ == "__main__":
    debug_variations()