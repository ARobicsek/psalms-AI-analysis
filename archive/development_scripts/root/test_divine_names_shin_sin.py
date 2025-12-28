"""
Test script to verify SHIN vs SIN distinction in divine names modifier.
Tests the bug fix for Psalm 8:8 where שָׂקָֽי was incorrectly modified.
"""

import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.utils.divine_names_modifier import DivineNamesModifier

def test_shin_vs_sin():
    """Test that SHIN (divine name) is modified but SIN is not"""

    modifier = DivineNamesModifier()

    # Test cases
    test_cases = [
        # (input, expected_output, description)
        # SHIN + PATACH cases (should be modified - divine name שַׁדַּי)
        ('שַׁדַּי', 'שַׁקַּי', 'Divine name with SHIN+PATACH - should be modified'),
        ('וְשַׁדַּי יְבָרֵךְ אֶתְכֶם', 'וְשַׁקַּי יְבָרֵךְ אֶתְכֶם', 'Divine name with prefix - should be modified'),
        ('שדי', 'שקי', 'Completely unvoweled - should be modified (no shin/sin distinction possible)'),
        ('וְאֵל שַׁדַּי יְבָרֵךְ', 'וְאֵל שַׁקַּי יְבָרֵךְ', 'El Shaddai phrase - should be modified'),

        # SHIN + SHEVA cases (should NOT be modified - שְׁדּי = breasts, not divine name)
        ('שְׁדּי', 'שְׁדּי', 'Word with SHIN+SHEVA (shadei=breasts) - should NOT be modified'),
        ('עַל־שְׁדּי אִמִּי', 'עַל־שְׁדּי אִמִּי', 'Psalm 22:10 phrase (breasts) - should NOT be modified'),
        ('מַבְטִיחִי עַל־שְׁדּי אִמִּי', 'מַבְטִיחִי עַל־שְׁדּי אִמִּי', 'Full Psalm 22:10 clause - should NOT be modified'),

        # SIN cases (should NOT be modified - not divine name, has שׂ not שׁ)
        ('שָׂדָֽי', 'שָׂדָֽי', 'Word with SIN (sadai) - should NOT be modified'),
        ('צֹנֶ֣ה וַאֲלָפִ֣ים כֻּלָּ֑ם וְ֝גַ֗ם בַּהֲמ֥וֹת שָׂדָֽי׃',
         'צֹנֶ֣ה וַאֲלָפִ֣ים כֻּלָּ֑ם וְ֝גַ֗ם בַּהֲמ֥וֹת שָׂדָֽי׃',
         'Psalm 8:8 with sadai (SIN) - should NOT be modified'),
    ]

    print("Testing SHIN vs SIN distinction in Divine Names Modifier\n")
    print("=" * 80)

    all_passed = True
    for i, (input_text, expected, description) in enumerate(test_cases, 1):
        result = modifier.modify_text(input_text)
        passed = result == expected
        all_passed = all_passed and passed

        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"\nTest {i}: {description}")
        print(f"  Input:    {input_text}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        print(f"  {status}")

        if not passed:
            # Show character breakdown for debugging
            print("\n  Character breakdown:")
            print(f"    Expected chars: {[f'{c} (U+{ord(c):04X})' for c in expected]}")
            print(f"    Got chars:      {[f'{c} (U+{ord(c):04X})' for c in result]}")

    print("\n" + "=" * 80)
    if all_passed:
        print("✓ All tests PASSED!")
    else:
        print("✗ Some tests FAILED")

    return all_passed

if __name__ == "__main__":
    test_shin_vs_sin()
