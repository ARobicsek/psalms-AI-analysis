"""
Test that skipgrams no longer cross verse boundaries.

This script verifies the fix for the issue where skipgrams were being found
across verse boundaries (e.g., "ארץ יהו" matching "אָֽרֶץ׃ יְ֭הֹוָה" where
the sof pasuq marker indicates end of verse).
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "psalm_relationships.db"

def test_no_cross_verse_skipgrams():
    """Test that no skipgrams cross verse boundaries."""

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    print("=" * 70)
    print("TESTING: No Skipgrams Cross Verse Boundaries")
    print("=" * 70)

    # Check if any skipgrams have the sof pasuq marker (׃) followed by a space
    # This would indicate the marker is BETWEEN words (cross-verse match)
    # If the marker is at the END of the span, that's fine (it's just the last word)
    cursor.execute("""
        SELECT
            psalm_number,
            verse,
            pattern_roots,
            pattern_hebrew,
            full_span_hebrew,
            pattern_length
        FROM psalm_skipgrams
        WHERE full_span_hebrew LIKE '%׃ %'
        LIMIT 20
    """)

    cross_verse_skipgrams = cursor.fetchall()

    if cross_verse_skipgrams:
        print(f"\n❌ FAILURE: Found {len(cross_verse_skipgrams)} skipgrams with sof pasuq BETWEEN words!")
        print("\nExamples (showing cross-verse matches):")
        for row in cross_verse_skipgrams[:5]:
            print(f"\n  Psalm {row[0]}, Verse {row[1]}")
            print(f"  Pattern roots: {row[2]}")
            print(f"  Pattern Hebrew: {row[3]}")
            print(f"  Full span: {row[4]}")
            print(f"  Length: {row[5]}")
    else:
        print("\n✅ SUCCESS: No skipgrams have sof pasuq BETWEEN words")
        print("   (Sof pasuq at end of verse is fine - it's just the last word's marker)")

    # Additional test: Check user's specific examples
    print("\n" + "=" * 70)
    print("CHECKING USER'S SPECIFIC EXAMPLES (Psalms 25 & 34)")
    print("=" * 70)

    # Example 1: "ציל אל" - should not match across verses
    cursor.execute("""
        SELECT
            psalm_number,
            verse,
            pattern_roots,
            pattern_hebrew,
            full_span_hebrew
        FROM psalm_skipgrams
        WHERE pattern_roots = 'ציל אל'
        AND psalm_number IN (25, 34)
    """)

    results = cursor.fetchall()
    print(f"\n1. Pattern 'ציל אל' in Psalms 25 & 34:")
    if results:
        print(f"   Found {len(results)} matches (all should be within single verses)")
        for row in results:
            has_sof_pasuq = '׃' in row[4]
            status = "❌ CROSS-VERSE" if has_sof_pasuq else "✅ WITHIN VERSE"
            print(f"   {status}: Psalm {row[0]}, Verse {row[1]}")
            print(f"   Full span: {row[4]}")
    else:
        print("   No matches found (pattern may not exist in these psalms)")

    # Example 2: "ארץ יהו" - should not match across verses
    cursor.execute("""
        SELECT
            psalm_number,
            verse,
            pattern_roots,
            pattern_hebrew,
            full_span_hebrew
        FROM psalm_skipgrams
        WHERE pattern_roots = 'ארץ יהו'
        AND psalm_number IN (25, 34)
    """)

    results = cursor.fetchall()
    print(f"\n2. Pattern 'ארץ יהו' in Psalms 25 & 34:")
    if results:
        print(f"   Found {len(results)} matches (all should be within single verses)")
        for row in results:
            has_sof_pasuq = '׃' in row[4]
            status = "❌ CROSS-VERSE" if has_sof_pasuq else "✅ WITHIN VERSE"
            print(f"   {status}: Psalm {row[0]}, Verse {row[1]}")
            print(f"   Full span: {row[4]}")
    else:
        print("   No matches found (pattern may not exist in these psalms)")

    # Example 3: "כל לא" - should not match across verses
    cursor.execute("""
        SELECT
            psalm_number,
            verse,
            pattern_roots,
            pattern_hebrew,
            full_span_hebrew
        FROM psalm_skipgrams
        WHERE pattern_roots = 'כל לא'
        AND psalm_number IN (25, 34)
    """)

    results = cursor.fetchall()
    print(f"\n3. Pattern 'כל לא' in Psalms 25 & 34:")
    if results:
        print(f"   Found {len(results)} matches (all should be within single verses)")
        for row in results:
            has_sof_pasuq = '׃' in row[4]
            status = "❌ CROSS-VERSE" if has_sof_pasuq else "✅ WITHIN VERSE"
            print(f"   {status}: Psalm {row[0]}, Verse {row[1]}")
            print(f"   Full span: {row[4]}")
    else:
        print("   No matches found (pattern may not exist in these psalms)")

    conn.close()

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_no_cross_verse_skipgrams()
