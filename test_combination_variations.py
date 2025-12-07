#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the new combination variation generation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set UTF-8 encoding for stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.concordance_librarian import ConcordanceLibrarian
from src.concordance.search import normalize_for_search

def test_combinations():
    librarian = ConcordanceLibrarian()

    # Test case 1: "דבר אמת בלב" (should generate "ודבר אמת בלבבו")
    phrase = "דבר אמת בלב"
    variations = librarian.generate_phrase_variations(phrase, "consonantal")

    print(f"Testing phrase: {phrase}")
    print(f"Total variations generated: {len(variations)}")
    print("\nSample variations (first 20):")
    for var in sorted(variations)[:20]:
        print(f"  - {var}")

    # Check for the specific variation we need
    target = "ודבר אמת בלבבו"
    consonantal_target = normalize_for_search(target, "consonantal")

    print(f"\nLooking for target: {target}")
    print(f"Normalized to: {consonantal_target}")
    print(f"Found: {consonantal_target in variations}")

    # Show all variations that start with 'ודבר'
    print(f"\nVariations starting with 'ודבר':")
    for var in sorted([v for v in variations if v.startswith('ודבר')]):
        print(f"  - {var}")

    # Test case 2: "הר קדש" (should generate "בהר קדשך")
    phrase2 = "הר קדש"
    variations2 = librarian.generate_phrase_variations(phrase2, "consonantal")

    print(f"\n\nTesting phrase: {phrase2}")
    print(f"Total variations generated: {len(variations2)}")

    target2 = "בהר קדשך"
    consonantal_target2 = normalize_for_search(target2, "consonantal")

    print(f"\nLooking for target: {target2}")
    print(f"Normalized to: {consonantal_target2}")
    print(f"Found: {consonantal_target2 in variations2}")

    # Show all variations that start with 'ב'
    print(f"\nVariations starting with 'ב':")
    for var in sorted([v for v in variations2 if v.startswith('ב')]):
        print(f"  - {var}")

if __name__ == "__main__":
    test_combinations()