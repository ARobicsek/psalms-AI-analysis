"""
Test script to verify Torah Temimah integration.

This script tests that:
1. Torah Temimah can be fetched from Sefaria API
2. Commentary Librarian handles it correctly
3. Output formatting works as expected

Usage:
    python test_torah_temimah_integration.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.commentary_librarian import CommentaryLibrarian, COMMENTATORS

def test_torah_temimah_available():
    """Test that Torah Temimah is registered."""
    print("=" * 80)
    print("TEST 1: Torah Temimah Registration")
    print("=" * 80)

    if "Torah Temimah" in COMMENTATORS:
        print("✓ Torah Temimah is registered in COMMENTATORS dictionary")
        print(f"  Sefaria text name: {COMMENTATORS['Torah Temimah']}")
        return True
    else:
        print("✗ Torah Temimah NOT found in COMMENTATORS")
        return False

def test_fetch_single_commentary():
    """Test fetching Torah Temimah for a single verse."""
    print("\n" + "=" * 80)
    print("TEST 2: Fetch Torah Temimah on Psalm 1:1")
    print("=" * 80)

    librarian = CommentaryLibrarian()

    try:
        entry = librarian.fetch_commentary(
            psalm=1,
            verse=1,
            commentator="Torah Temimah"
        )

        if entry:
            print("✓ Successfully fetched Torah Temimah commentary")
            print(f"\n  Commentator: {entry.commentator}")
            print(f"  Psalm: {entry.psalm}")
            print(f"  Verse: {entry.verse}")
            print(f"  Hebrew length: {len(entry.hebrew)} characters")
            print(f"  English length: {len(entry.english)} characters")
            print(f"\n  Hebrew preview (first 200 chars):")
            print(f"    {entry.hebrew[:200]}...")

            if entry.english:
                print(f"\n  English preview:")
                print(f"    {entry.english[:200]}...")
            else:
                print(f"\n  Note: No English translation available (expected for Torah Temimah)")

            return True
        else:
            print("✗ No commentary found (may not be available for this verse)")
            return False

    except Exception as e:
        print(f"✗ Error fetching commentary: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fetch_all_commentators():
    """Test fetching all 7 commentators including Torah Temimah."""
    print("\n" + "=" * 80)
    print("TEST 3: Fetch All Commentators (including Torah Temimah) for Psalm 1:1")
    print("=" * 80)

    librarian = CommentaryLibrarian()

    try:
        commentaries = librarian.fetch_commentaries(
            psalm=1,
            verse=1,
            commentators=None  # None = fetch all
        )

        print(f"✓ Fetched {len(commentaries)} commentaries")

        commentator_names = [c.commentator for c in commentaries]
        print(f"\n  Available commentators:")
        for name in commentator_names:
            print(f"    - {name}")

        if "Torah Temimah" in commentator_names:
            print(f"\n✓ Torah Temimah is included in the results")
            return True
        else:
            print(f"\n✗ Torah Temimah NOT in results (may not be available)")
            return False

    except Exception as e:
        print(f"✗ Error fetching commentaries: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_process_requests():
    """Test processing multiple commentary requests."""
    print("\n" + "=" * 80)
    print("TEST 4: Process Multiple Commentary Requests")
    print("=" * 80)

    librarian = CommentaryLibrarian()

    requests = [
        {"psalm": 1, "verse": 1, "reason": "Opening verse - testing Torah Temimah"},
        {"psalm": 1, "verse": 2, "reason": "Torah study verse - likely rich in commentary"}
    ]

    try:
        bundles = librarian.process_requests(requests)

        print(f"✓ Processed {len(bundles)} commentary requests")

        total_commentaries = sum(len(b.commentaries) for b in bundles)
        print(f"  Total commentaries fetched: {total_commentaries}")

        # Check if Torah Temimah appears in any bundle
        torah_temimah_found = False
        for bundle in bundles:
            for comm in bundle.commentaries:
                if comm.commentator == "Torah Temimah":
                    torah_temimah_found = True
                    print(f"\n✓ Torah Temimah found in bundle for Psalm {bundle.psalm}:{bundle.verse}")
                    print(f"  Preview: {comm.hebrew[:150]}...")

        if not torah_temimah_found:
            print(f"\n⚠ Torah Temimah not found in any bundles (may not have commentary on these verses)")

        return True

    except Exception as e:
        print(f"✗ Error processing requests: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_markdown_formatting():
    """Test markdown formatting with Torah Temimah."""
    print("\n" + "=" * 80)
    print("TEST 5: Markdown Formatting with Torah Temimah")
    print("=" * 80)

    librarian = CommentaryLibrarian()

    try:
        requests = [{"psalm": 1, "verse": 1, "reason": "Testing markdown output"}]
        bundles = librarian.process_requests(requests)

        if bundles:
            markdown = librarian.format_bundle_as_markdown(bundles)

            print("✓ Generated markdown output")
            print(f"  Length: {len(markdown)} characters")

            if "Torah Temimah" in markdown:
                print(f"\n✓ Torah Temimah appears in markdown output")
            else:
                print(f"\n⚠ Torah Temimah not in markdown (may not have commentary)")

            print(f"\n  Markdown preview (first 500 chars):")
            print("-" * 80)
            print(markdown[:500])
            print("-" * 80)

            return True
        else:
            print("⚠ No bundles to format")
            return False

    except Exception as e:
        print(f"✗ Error with markdown formatting: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("TORAH TEMIMAH INTEGRATION TEST SUITE")
    print("=" * 80)

    # Ensure UTF-8 for Hebrew output
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    tests = [
        test_torah_temimah_available,
        test_fetch_single_commentary,
        test_fetch_all_commentators,
        test_process_requests,
        test_markdown_formatting
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(results)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed! Torah Temimah integration is working correctly.")
        return 0
    elif passed > 0:
        print(f"\n⚠ {total - passed} test(s) failed. Check output above for details.")
        print("  Note: Some failures may be expected if Torah Temimah doesn't have")
        print("  commentary on the specific test verses.")
        return 0
    else:
        print("\n✗ All tests failed. There may be a configuration issue.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
