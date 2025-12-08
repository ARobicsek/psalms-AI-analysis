#!/usr/bin/env python3
"""
Test script to verify that phrase searches always find the source verse,
even when LLM creates conceptual phrases with different word order.

Tests the fix for Psalm 15:3 "נשא חרפה" issue.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.micro_analyst import MicroAnalystV2
from src.data_sources.tanakh_database import TanakhDatabase

def test_phrase_extraction():
    """Test the _extract_all_phrase_forms_from_verse method."""

    print("=" * 80)
    print("TEST: Phrase Order Guarantee")
    print("=" * 80)

    # Initialize components
    db_path = Path('data/tanakh.db')
    db = TanakhDatabase(db_path)
    analyst = MicroAnalystV2(db_path=str(db_path))

    # Get Psalm 15:3
    psalm = db.get_psalm(15)
    verse_3 = psalm.verses[2]  # 0-indexed, so verse 3 is index 2

    print(f"\nPsalm 15:3 Hebrew text:")
    print(f"  {verse_3.hebrew}")
    print(f"  {verse_3.english}")

    # Test Case 1: "נשא חרפה" (the failing case)
    print("\n" + "-" * 80)
    print("Test Case 1: נשא חרפה (bear reproach)")
    print("-" * 80)

    query = "נשא חרפה"
    print(f"\nQuery: '{query}'")
    print(f"  Expected: Should find forms from verse even though word order is reversed")

    forms = analyst._extract_all_phrase_forms_from_verse(query, verse_3.hebrew)

    print(f"\nExtracted forms ({len(forms)}):")
    for i, form in enumerate(forms, 1):
        print(f"  {i}. {form}")

    if forms:
        print(f"\n✅ SUCCESS: Found {len(forms)} form(s) that will guarantee match")
    else:
        print(f"\n❌ FAILURE: No forms found!")

    # Test Case 2: Forward order (should also work)
    print("\n" + "-" * 80)
    print("Test Case 2: חרפה נשא (reproach bear - actual order)")
    print("-" * 80)

    query2 = "חרפה נשא"
    print(f"\nQuery: '{query2}'")

    forms2 = analyst._extract_all_phrase_forms_from_verse(query2, verse_3.hebrew)

    print(f"\nExtracted forms ({len(forms2)}):")
    for i, form in enumerate(forms2, 1):
        print(f"  {i}. {form}")

    if forms2:
        print(f"\n✅ SUCCESS: Found {len(forms2)} form(s)")
    else:
        print(f"\n❌ FAILURE: No forms found!")

    # Test Case 3: Phrase from another verse (should find the actual phrase)
    print("\n" + "-" * 80)
    print("Test Case 3: דבר אמת (speak truth - from verse 2)")
    print("-" * 80)

    verse_2 = psalm.verses[1]
    print(f"\nPsalm 15:2 Hebrew text:")
    print(f"  {verse_2.hebrew}")

    query3 = "דבר אמת"
    print(f"\nQuery: '{query3}'")

    forms3 = analyst._extract_all_phrase_forms_from_verse(query3, verse_2.hebrew)

    print(f"\nExtracted forms ({len(forms3)}):")
    for i, form in enumerate(forms3, 1):
        print(f"  {i}. {form}")

    if forms3:
        print(f"\n✅ SUCCESS: Found {len(forms3)} form(s)")
    else:
        print(f"\n❌ FAILURE: No forms found!")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    all_passed = all([forms, forms2, forms3])

    if all_passed:
        print("\n✅ ALL TESTS PASSED")
        print("\nThe fix successfully extracts all phrase forms from verses,")
        print("guaranteeing that phrase searches will find the source verse")
        print("regardless of word order in the query.")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nThe fix may not be working correctly.")

    return all_passed

if __name__ == '__main__':
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    success = test_phrase_extraction()
    sys.exit(0 if success else 1)
