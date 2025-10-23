"""
Test script to verify commentary mode implementation.

Tests:
1. MicroAnalystV2 can be instantiated with both modes
2. Mode validation works correctly
3. Prompt templates are properly formatted
4. Both modes generate different instructions
"""

import sys
from pathlib import Path

# Ensure UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.micro_analyst import MicroAnalystV2, COMMENTARY_ALL_VERSES, COMMENTARY_SELECTIVE, RESEARCH_REQUEST_PROMPT

def test_commentary_mode_instantiation():
    """Test that MicroAnalystV2 can be instantiated with both modes."""
    print("TEST 1: MicroAnalystV2 instantiation with different modes")
    print("=" * 70)

    try:
        # Test default mode
        analyst_default = MicroAnalystV2()
        assert analyst_default.commentary_mode == "all", "Default mode should be 'all'"
        print("✓ Default mode (all): SUCCESS")

        # Test explicit all mode
        analyst_all = MicroAnalystV2(commentary_mode="all")
        assert analyst_all.commentary_mode == "all", "Explicit 'all' mode should work"
        print("✓ Explicit 'all' mode: SUCCESS")

        # Test selective mode
        analyst_selective = MicroAnalystV2(commentary_mode="selective")
        assert analyst_selective.commentary_mode == "selective", "Selective mode should work"
        print("✓ Selective mode: SUCCESS")

        print()
        return True

    except Exception as e:
        print(f"✗ FAILED: {e}")
        print()
        return False


def test_mode_validation():
    """Test that invalid modes are rejected."""
    print("TEST 2: Mode validation")
    print("=" * 70)

    try:
        # This should raise ValueError
        analyst = MicroAnalystV2(commentary_mode="invalid")
        print("✗ FAILED: Should have raised ValueError for invalid mode")
        print()
        return False

    except ValueError as e:
        if "Invalid commentary_mode" in str(e):
            print(f"✓ Correctly rejected invalid mode: {e}")
            print()
            return True
        else:
            print(f"✗ FAILED: Wrong error message: {e}")
            print()
            return False
    except Exception as e:
        print(f"✗ FAILED: Unexpected error: {e}")
        print()
        return False


def test_template_differences():
    """Test that the two templates are different and contain expected content."""
    print("TEST 3: Template content verification")
    print("=" * 70)

    # Check that templates exist and are different
    assert COMMENTARY_ALL_VERSES != COMMENTARY_SELECTIVE, "Templates should be different"
    print("✓ Templates are different")

    # Check ALL_VERSES template content
    assert "REQUEST COMMENTARY FOR EVERY VERSE" in COMMENTARY_ALL_VERSES, \
        "ALL_VERSES should request every verse"
    assert "7 available commentators" in COMMENTARY_ALL_VERSES, \
        "ALL_VERSES should mention 7 commentators"
    assert "comprehensive approach" in COMMENTARY_ALL_VERSES, \
        "ALL_VERSES should mention comprehensive approach"
    print("✓ ALL_VERSES template contains expected content")

    # Check SELECTIVE template content
    assert "REQUEST COMMENTARY ONLY FOR VERSES" in COMMENTARY_SELECTIVE, \
        "SELECTIVE should be selective"
    assert "3-8 verses" in COMMENTARY_SELECTIVE, \
        "SELECTIVE should mention 3-8 verses"
    assert "selective and judicious" in COMMENTARY_SELECTIVE, \
        "SELECTIVE should mention being judicious"
    print("✓ SELECTIVE template contains expected content")

    print()
    return True


def test_prompt_formatting():
    """Test that the research request prompt can be formatted with both templates."""
    print("TEST 4: Prompt formatting with commentary instructions")
    print("=" * 70)

    try:
        # Test formatting with ALL_VERSES
        prompt_all = RESEARCH_REQUEST_PROMPT.format(
            discoveries='{"test": "data"}',
            commentary_instructions=COMMENTARY_ALL_VERSES
        )
        assert "REQUEST COMMENTARY FOR EVERY VERSE" in prompt_all, \
            "Formatted prompt should contain ALL_VERSES instructions"
        assert "{commentary_instructions}" not in prompt_all, \
            "Placeholder should be replaced"
        print("✓ Prompt formats correctly with ALL_VERSES template")

        # Test formatting with SELECTIVE
        prompt_selective = RESEARCH_REQUEST_PROMPT.format(
            discoveries='{"test": "data"}',
            commentary_instructions=COMMENTARY_SELECTIVE
        )
        assert "REQUEST COMMENTARY ONLY FOR VERSES" in prompt_selective, \
            "Formatted prompt should contain SELECTIVE instructions"
        assert "{commentary_instructions}" not in prompt_selective, \
            "Placeholder should be replaced"
        print("✓ Prompt formats correctly with SELECTIVE template")

        print()
        return True

    except Exception as e:
        print(f"✗ FAILED: {e}")
        print()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("COMMENTARY MODES IMPLEMENTATION VERIFICATION")
    print("=" * 70)
    print()

    results = []

    results.append(("Instantiation", test_commentary_mode_instantiation()))
    results.append(("Validation", test_mode_validation()))
    results.append(("Template Content", test_template_differences()))
    results.append(("Prompt Formatting", test_prompt_formatting()))

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:.<50} {status}")

    all_passed = all(result[1] for result in results)

    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED")
        return 0
    else:
        print("⚠ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
