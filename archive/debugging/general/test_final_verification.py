"""
Final comprehensive test to verify the suffix fix works correctly
and doesn't introduce any regressions.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest


def test_phrase_searches():
    """Test multiple phrase searches to verify comprehensive coverage."""

    print("=" * 80)
    print("FINAL COMPREHENSIVE VERIFICATION TEST")
    print("=" * 80)

    librarian = ConcordanceLibrarian()

    test_cases = [
        {
            'phrase': 'הר קדש',
            'scope': 'Psalms',
            'expected_verses': [
                'Psalms 15:1',  # בהר קדשך
                'Psalms 2:6',   # הר קדשי
                'Psalms 3:5',   # מהר קדשו
                'Psalms 43:3',  # הר קדשך
                'Psalms 48:2',  # הר קדשו
                'Psalms 99:9',  # להר קדשו
            ],
            'description': 'Holy mountain - primary test case'
        },
        {
            'phrase': 'יהוה רעי',
            'scope': 'Psalms',
            'expected_verses': ['Psalms 23:1'],
            'description': 'The LORD is my shepherd'
        },
        {
            'phrase': 'אלהי צדקי',
            'scope': 'Psalms',
            'expected_verses': ['Psalms 4:2'],
            'description': 'God of my righteousness'
        },
    ]

    all_passed = True

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"Test {i}: {test['phrase']} - {test['description']}")
        print(f"{'=' * 80}")

        request = ConcordanceRequest(
            query=test['phrase'],
            scope=test['scope'],
            level='consonantal',
            include_variations=True,
            max_results=50
        )

        bundle = librarian.search_with_variations(request)

        print(f"\nQuery: {test['phrase']}")
        print(f"Scope: {test['scope']}")
        print(f"Found: {len(bundle.results)} results")
        print(f"Variations searched: {len(bundle.variations_searched)}")

        # Check if expected verses are found
        found_refs = {r.reference for r in bundle.results}
        expected_refs = set(test['expected_verses'])

        missing = expected_refs - found_refs
        unexpected = found_refs - expected_refs

        print(f"\nExpected verses: {len(expected_refs)}")
        print(f"Found expected: {len(expected_refs - missing)}/{len(expected_refs)}")

        if missing:
            print(f"\n✗ MISSING expected verses:")
            for ref in sorted(missing):
                print(f"  - {ref}")
            all_passed = False
        else:
            print(f"\n✓ All expected verses found!")

        if bundle.results:
            print(f"\nAll results found:")
            for result in bundle.results[:10]:
                marker = "✓" if result.reference in expected_refs else " "
                print(f"  {marker} {result.reference}")
                print(f"     Matched: {result.matched_word} at position {result.word_position}")

            if len(bundle.results) > 10:
                print(f"  ... and {len(bundle.results) - 10} more")

    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)

    if all_passed:
        print("\n✓ ALL TESTS PASSED!")
        print("\nThe suffix variation fix is working correctly:")
        print("- Suffixes are generated for ALL words, not just the last word")
        print("- Prefixes are combined with suffixes on any word")
        print("- All expected verses are found by phrase searches")
        return True
    else:
        print("\n✗ SOME TESTS FAILED")
        print("See details above for missing verses.")
        return False


def test_variation_count():
    """Verify that we're generating more variations than before."""

    print("\n" + "=" * 80)
    print("VARIATION COUNT TEST")
    print("=" * 80)

    librarian = ConcordanceLibrarian()

    test_phrase = "הר קדש"
    variations = librarian.generate_phrase_variations(test_phrase, level='consonantal')

    print(f"\nPhrase: {test_phrase}")
    print(f"Total variations generated: {len(variations)}")

    # Check for specific important variations
    critical_variations = [
        'הר קדש',      # base
        'בהר קדשך',    # prefix + suffix on last (Psalm 15:1)
        'הרי קדש',     # suffix on first
        'מהר קדשו',    # preposition + suffix on last (Psalm 3:5)
        'להר קדשו',    # preposition + suffix on last (Psalm 99:9)
        'הרי קדשו',    # suffixes on both
    ]

    print(f"\nCritical variations:")
    all_found = True
    for var in critical_variations:
        status = '✓' if var in variations else '✗'
        if var not in variations:
            all_found = False
        print(f"  {status} {var}")

    if all_found:
        print(f"\n✓ All critical variations are generated!")
        return True
    else:
        print(f"\n✗ Some critical variations are missing!")
        return False


def test_no_regressions():
    """Verify that we haven't broken any existing functionality."""

    print("\n" + "=" * 80)
    print("REGRESSION TEST")
    print("=" * 80)

    librarian = ConcordanceLibrarian()

    # Test simple single-word search
    request = ConcordanceRequest(
        query='שמר',
        scope='Psalms',
        level='consonantal',
        include_variations=True,
        max_results=10
    )

    bundle = librarian.search_with_variations(request)

    print(f"\nSingle-word search test: שמר (guard/keep)")
    print(f"Found: {len(bundle.results)} results")

    if len(bundle.results) > 0:
        print("✓ Single-word search still works")
        success1 = True
    else:
        print("✗ Single-word search broken!")
        success1 = False

    # Test phrase search without variations
    request = ConcordanceRequest(
        query='יהוה רעי',
        scope='Psalms',
        level='consonantal',
        include_variations=False,  # No variations!
        max_results=10
    )

    bundle = librarian.search_with_variations(request)

    print(f"\nPhrase search without variations: יהוה רעי")
    print(f"Found: {len(bundle.results)} results")
    print(f"Variations searched: {len(bundle.variations_searched)}")

    if len(bundle.variations_searched) == 1:
        print("✓ Variation disabling still works")
        success2 = True
    else:
        print("✗ Variation disabling broken!")
        success2 = False

    return success1 and success2


if __name__ == '__main__':
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    # Run all tests
    test1 = test_phrase_searches()
    test2 = test_variation_count()
    test3 = test_no_regressions()

    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)

    print(f"\nPhrase search tests: {'✓ PASS' if test1 else '✗ FAIL'}")
    print(f"Variation count test: {'✓ PASS' if test2 else '✗ FAIL'}")
    print(f"Regression tests: {'✓ PASS' if test3 else '✗ FAIL'}")

    overall = test1 and test2 and test3

    print(f"\n{'=' * 80}")
    if overall:
        print("✓✓✓ ALL TESTS PASSED - FIX IS WORKING CORRECTLY ✓✓✓")
    else:
        print("✗✗✗ SOME TESTS FAILED - NEEDS INVESTIGATION ✗✗✗")
    print("=" * 80)

    sys.exit(0 if overall else 1)
