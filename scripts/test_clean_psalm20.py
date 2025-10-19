"""
Test that Psalm 20 verse text is clean in print-ready output.
"""

import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.commentary_formatter import CommentaryFormatter

def test_clean_verses():
    """Test that verses are cleaned of footnotes."""

    formatter = CommentaryFormatter()

    # Get verses for Psalm 20
    verses = formatter._get_psalm_verses(20)

    print("=" * 80)
    print("PSALM 20 VERSES - TESTING FOOTNOTE REMOVAL")
    print("=" * 80)

    # Check verse 4 specifically (has footnotes)
    verse_4 = verses.get(4, {})
    english_4 = verse_4.get('english', '')

    print("\nVerse 4 (should have NO footnotes):")
    print("-" * 80)
    print(f"Hebrew: {verse_4.get('hebrew', '')}")
    print(f"English: {english_4}")
    print("-" * 80)

    # Verification checks
    print("\nVERIFICATION:")
    print(f"✓ Contains 'tokens': {('tokens' in english_4)}")
    print(f"✓ Contains 'Selah': {('Selah' in english_4)}")
    print(f"✗ Contains 'Reference to azkara': {('Reference to azkara' in english_4)}")
    print(f"✗ Contains 'Meaning of Heb. uncertain': {('Meaning of Heb. uncertain' in english_4)}")
    print(f"✗ Contains HTML tags: {('<' in english_4)}")

    # Show verse 2 as well (also has footnotes in JPS)
    print("\n" + "=" * 80)
    verse_2 = verses.get(2, {})
    english_2 = verse_2.get('english', '')

    print("\nVerse 2:")
    print("-" * 80)
    print(f"Hebrew: {verse_2.get('hebrew', '')}")
    print(f"English: {english_2}")
    print("-" * 80)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    has_footnotes = any(
        'footnote' in verses[v].get('english', '').lower() or
        '<' in verses[v].get('english', '')
        for v in verses
    )

    if has_footnotes:
        print("❌ FAILED: Some verses still contain footnotes or HTML")
    else:
        print("✅ SUCCESS: All verses are clean of footnotes and HTML")

    return not has_footnotes

if __name__ == '__main__':
    success = test_clean_verses()
    sys.exit(0 if success else 1)
