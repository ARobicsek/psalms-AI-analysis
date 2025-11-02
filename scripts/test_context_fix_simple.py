"""
Simple test for Issue #1 fix - empty context extraction.
Tests the specific example from the user's request.
"""

import sqlite3
import sys
import io
from pathlib import Path

# Configure UTF-8 output for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from liturgy.liturgy_indexer import LiturgyIndexer


def test_empty_context_fix():
    """Test the _extract_context fix on actual problematic cases."""

    print("="*80)
    print("TESTING ISSUE #1 FIX: Empty Context Extraction")
    print("="*80)

    conn = sqlite3.connect("c:/Users/ariro/OneDrive/Documents/Psalms/data/liturgy.db")
    cursor = conn.cursor()

    # Get 5 examples with empty contexts
    cursor.execute("""
        SELECT
            psalm_phrase_hebrew,
            prayer_id
        FROM psalms_liturgy_index
        WHERE (liturgy_context = '' OR liturgy_context IS NULL)
          AND psalm_chapter = 1
        LIMIT 5
    """)

    test_cases = cursor.fetchall()

    print(f"\nFound {len(test_cases)} test cases from Psalm 1 with empty contexts")
    print("\nTesting context extraction...\n")

    indexer = LiturgyIndexer(verbose=False)

    success_count = 0
    fail_count = 0

    for phrase, prayer_id in test_cases:
        # Get prayer text
        cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = ?", (prayer_id,))
        prayer_text = cursor.fetchone()[0]

        # Test context extraction
        context = indexer._extract_context(
            full_text=prayer_text,
            phrase=phrase,
            context_words=10
        )

        is_success = len(context) > 0

        if is_success:
            success_count += 1
            status = "✓ SUCCESS"
        else:
            fail_count += 1
            status = "✗ FAILED"

        print(f"{status}: prayer_id {prayer_id}")
        print(f"  Phrase: {phrase[:40]}...")
        if context:
            print(f"  Context: {context[:80]}...")
        else:
            print(f"  Context: (still empty)")
        print()

    print("="*80)
    print(f"RESULTS: {success_count} success, {fail_count} failed out of {len(test_cases)}")
    print("="*80)

    conn.close()

    return success_count, fail_count


if __name__ == "__main__":
    success, fail = test_empty_context_fix()

    if fail == 0:
        print("\n✓ Issue #1 FIXED: All contexts successfully extracted!")
        sys.exit(0)
    else:
        print(f"\n✗ Issue #1 NOT FULLY FIXED: {fail} cases still empty")
        sys.exit(1)
