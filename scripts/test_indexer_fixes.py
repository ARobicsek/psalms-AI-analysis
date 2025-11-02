"""
Test script to diagnose and validate indexer fixes.

This script tests all 5 critical issues:
1. Empty liturgical_context fields (35.1% failure rate)
2. Multiple phrase entries instead of single exact_verse
3. Missed entire_chapter detection
4. Phrase matches when verse-present should be detected
5. Consecutive verse sequences (verse_range)
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


def test_issue_1_empty_contexts():
    """Test Issue #1: Empty liturgical_context fields."""
    print("\n" + "="*80)
    print("ISSUE #1: Testing empty context extraction")
    print("="*80)

    # Connect to database
    conn = sqlite3.connect("c:/Users/ariro/OneDrive/Documents/Psalms/data/liturgy.db")
    cursor = conn.cursor()

    # Get examples with empty contexts
    cursor.execute("""
        SELECT
            index_id,
            psalm_chapter,
            psalm_verse_start,
            psalm_phrase_hebrew,
            prayer_id,
            liturgy_context,
            match_type
        FROM psalms_liturgy_index
        WHERE liturgy_context = '' OR liturgy_context IS NULL
        LIMIT 10
    """)

    empty_contexts = cursor.fetchall()

    print(f"\nFound {len(empty_contexts)} examples with empty contexts:")

    indexer = LiturgyIndexer(verbose=False)

    for index_id, psalm_ch, verse_start, phrase, prayer_id, context, match_type in empty_contexts:
        print(f"\n--- Test Case: index_id {index_id} ---")
        print(f"Psalm {psalm_ch}:{verse_start}")
        print(f"Phrase: {phrase[:60]}...")
        print(f"Prayer ID: {prayer_id}")
        print(f"Match type: {match_type}")
        print(f"Current context: '{context}'")

        # Get prayer text
        cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = ?", (prayer_id,))
        result = cursor.fetchone()
        if not result:
            print("ERROR: Prayer not found!")
            continue

        prayer_text = result[0]
        print(f"Prayer length: {len(prayer_text)} chars, {len(prayer_text.split())} words")

        # Test context extraction
        new_context = indexer._extract_context(
            full_text=prayer_text,
            phrase=phrase,
            context_words=10
        )

        print(f"NEW context: '{new_context[:100]}{'...' if len(new_context) > 100 else ''}'")
        print(f"Success: {'YES' if new_context else 'NO - STILL EMPTY!'}")

        if not new_context:
            # Debug why it's empty
            print("\nDEBUG INFO:")
            normalized_phrase = indexer._full_normalize(phrase)
            print(f"Normalized phrase: '{normalized_phrase}'")
            print(f"Phrase word count: {len(normalized_phrase.split())}")

            # Check if phrase appears in prayer at all
            normalized_prayer = indexer._full_normalize(prayer_text)
            if normalized_phrase in normalized_prayer:
                print("✓ Phrase DOES appear in normalized prayer")
                pos = normalized_prayer.find(normalized_phrase)
                print(f"  Position: {pos}")
                context_window = normalized_prayer[max(0,pos-50):pos+len(normalized_phrase)+50]
                print(f"  Context: ...{context_window}...")
            else:
                print("✗ Phrase DOES NOT appear in normalized prayer")
                # Try to find partial matches
                phrase_words = normalized_phrase.split()
                print(f"  Phrase words: {phrase_words}")
                first_word = phrase_words[0] if phrase_words else ""
                if first_word and first_word in normalized_prayer:
                    print(f"  First word '{first_word}' found in prayer")
                else:
                    print(f"  First word '{first_word}' NOT found")

    conn.close()

    # Statistics
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            match_type,
            COUNT(*) as total,
            SUM(CASE WHEN liturgy_context = '' OR liturgy_context IS NULL THEN 1 ELSE 0 END) as empty,
            ROUND(100.0 * SUM(CASE WHEN liturgy_context = '' OR liturgy_context IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) as empty_pct
        FROM psalms_liturgy_index
        GROUP BY match_type
    """)

    print("\n\nEMPTY CONTEXT STATISTICS BY MATCH TYPE:")
    print("-" * 80)
    print(f"{'Match Type':<20} {'Total':<10} {'Empty':<10} {'Empty %':<10}")
    print("-" * 80)

    for match_type, total, empty, empty_pct in cursor.fetchall():
        print(f"{match_type:<20} {total:<10} {empty:<10} {empty_pct:<10}")


def test_issue_2_duplicate_phrases():
    """Test Issue #2: Multiple phrase entries that should be one exact_verse."""
    print("\n" + "="*80)
    print("ISSUE #2: Testing duplicate phrase entries (should be exact_verse)")
    print("="*80)

    # The example: Psalm 1:3 in prayer 626 has TWO phrase entries
    # index_id 26039 and 26040

    conn = sqlite3.connect("c:/Users/ariro/OneDrive/Documents/Psalms/data/liturgy.db")
    cursor = conn.cursor()

    # Find cases where same verse+prayer has multiple phrase entries
    cursor.execute("""
        SELECT
            psalm_chapter,
            psalm_verse_start,
            psalm_verse_end,
            prayer_id,
            COUNT(*) as count,
            GROUP_CONCAT(index_id) as index_ids,
            GROUP_CONCAT(phrase_length) as lengths
        FROM psalms_liturgy_index
        WHERE match_type = 'phrase_match'
        GROUP BY psalm_chapter, psalm_verse_start, psalm_verse_end, prayer_id
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 10
    """)

    duplicates = cursor.fetchall()
    print(f"\nFound {len(duplicates)} cases with multiple phrase entries for same verse+prayer")

    for psalm_ch, verse_start, verse_end, prayer_id, count, index_ids, lengths in duplicates:
        print(f"\n--- Psalm {psalm_ch}:{verse_start} in prayer {prayer_id} ---")
        print(f"Number of entries: {count}")
        print(f"Index IDs: {index_ids}")
        print(f"Phrase lengths: {lengths}")

        # Get the full verse text
        tanakh_conn = sqlite3.connect("c:/Users/ariro/OneDrive/Documents/Psalms/database/tanakh.db")
        tanakh_cursor = tanakh_conn.cursor()
        tanakh_cursor.execute("""
            SELECT hebrew FROM verses
            WHERE book_name = 'Psalms' AND chapter = ? AND verse = ?
        """, (psalm_ch, verse_start))

        verse_result = tanakh_cursor.fetchone()
        tanakh_conn.close()

        if verse_result:
            verse_text = verse_result[0]
            print(f"Full verse: {verse_text}")

            # Get prayer text
            cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = ?", (prayer_id,))
            prayer_text = cursor.fetchone()[0]

            # Check if full verse appears in prayer
            indexer = LiturgyIndexer(verbose=False)
            normalized_verse = indexer._full_normalize(verse_text)
            normalized_prayer = indexer._full_normalize(prayer_text)

            if normalized_verse in normalized_prayer:
                print("✓ Full verse DOES appear in prayer - should be exact_verse!")
            else:
                print("✗ Full verse does NOT appear in prayer - phrases are correct")

    conn.close()


def test_issue_3_entire_chapter():
    """Test Issue #3: Missed entire_chapter detection."""
    print("\n" + "="*80)
    print("ISSUE #3: Testing entire_chapter detection")
    print("="*80)

    # Example: Psalm 135 in prayer 832 should be entire_chapter

    conn = sqlite3.connect("c:/Users/ariro/OneDrive/Documents/Psalms/data/liturgy.db")
    cursor = conn.cursor()

    # Find cases where all verses of a psalm appear in same prayer but not marked as entire_chapter
    cursor.execute("""
        SELECT
            psalm_chapter,
            prayer_id,
            COUNT(DISTINCT psalm_verse_start) as verse_count,
            GROUP_CONCAT(DISTINCT match_type) as match_types
        FROM psalms_liturgy_index
        WHERE psalm_verse_start = psalm_verse_end
        GROUP BY psalm_chapter, prayer_id
        HAVING verse_count >= 5 AND match_types NOT LIKE '%entire_chapter%'
        ORDER BY verse_count DESC
        LIMIT 5
    """)

    candidates = cursor.fetchall()
    print(f"\nFound {len(candidates)} potential entire_chapter candidates")

    tanakh_conn = sqlite3.connect("c:/Users/ariro/OneDrive/Documents/Psalms/database/tanakh.db")
    tanakh_cursor = tanakh_conn.cursor()

    for psalm_ch, prayer_id, verse_count, match_types in candidates:
        # Get total verses in this psalm
        tanakh_cursor.execute("""
            SELECT COUNT(*) FROM verses
            WHERE book_name = 'Psalms' AND chapter = ?
        """, (psalm_ch,))
        total_verses = tanakh_cursor.fetchone()[0]

        print(f"\n--- Psalm {psalm_ch} in prayer {prayer_id} ---")
        print(f"Verses found: {verse_count}/{total_verses}")
        print(f"Match types: {match_types}")

        if verse_count == total_verses:
            print("✓ All verses present - SHOULD BE entire_chapter!")
        else:
            print(f"✗ Missing {total_verses - verse_count} verses")

    tanakh_conn.close()
    conn.close()


def test_issue_4_phrase_when_verse():
    """Test Issue #4: Phrase matches when should be exact_verse."""
    print("\n" + "="*80)
    print("ISSUE #4: Testing phrase_match that should be exact_verse")
    print("="*80)

    # Examples: Psalm 150:1 and 145:1 appear as phrase_match but should be exact_verse

    conn = sqlite3.connect("c:/Users/ariro/OneDrive/Documents/Psalms/data/liturgy.db")
    cursor = conn.cursor()

    # Get phrase matches
    cursor.execute("""
        SELECT
            index_id,
            psalm_chapter,
            psalm_verse_start,
            psalm_phrase_hebrew,
            prayer_id
        FROM psalms_liturgy_index
        WHERE match_type = 'phrase_match'
          AND psalm_verse_start = psalm_verse_end
        LIMIT 20
    """)

    phrase_matches = cursor.fetchall()
    print(f"\nChecking {len(phrase_matches)} phrase_match entries...")

    tanakh_conn = sqlite3.connect("c:/Users/ariro/OneDrive/Documents/Psalms/database/tanakh.db")
    tanakh_cursor = tanakh_conn.cursor()
    indexer = LiturgyIndexer(verbose=False)

    upgradeable = 0

    for index_id, psalm_ch, verse_start, phrase, prayer_id in phrase_matches:
        # Get full verse
        tanakh_cursor.execute("""
            SELECT hebrew FROM verses
            WHERE book_name = 'Psalms' AND chapter = ? AND verse = ?
        """, (psalm_ch, verse_start))

        verse_result = tanakh_cursor.fetchone()
        if not verse_result:
            continue

        verse_text = verse_result[0]

        # Compare at consonantal level
        normalized_verse = indexer._full_normalize(verse_text)
        normalized_phrase = indexer._full_normalize(phrase)

        if normalized_verse == normalized_phrase:
            upgradeable += 1
            if upgradeable <= 5:  # Show first 5 examples
                print(f"\n✓ index_id {index_id}: Psalm {psalm_ch}:{verse_start}")
                print(f"  Phrase matches full verse - should be exact_verse!")

    print(f"\n\nTotal upgradeable: {upgradeable} out of {len(phrase_matches)}")

    tanakh_conn.close()
    conn.close()


def test_issue_5_verse_ranges():
    """Test Issue #5: Detect consecutive verse sequences."""
    print("\n" + "="*80)
    print("ISSUE #5: Testing consecutive verse range detection")
    print("="*80)

    # Example: Psalm 6:2-11 in Tachanun (prayer 73)

    conn = sqlite3.connect("c:/Users/ariro/OneDrive/Documents/Psalms/data/liturgy.db")
    cursor = conn.cursor()

    # Find consecutive verses in same prayer
    cursor.execute("""
        SELECT
            psalm_chapter,
            prayer_id,
            GROUP_CONCAT(psalm_verse_start) as verses
        FROM psalms_liturgy_index
        WHERE match_type IN ('exact_verse', 'phrase_match')
          AND psalm_verse_start = psalm_verse_end
        GROUP BY psalm_chapter, prayer_id
        HAVING COUNT(*) >= 3
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)

    candidates = cursor.fetchall()
    print(f"\nFound {len(candidates)} candidates with 3+ verses")

    for psalm_ch, prayer_id, verses_str in candidates:
        verses = sorted([int(v) for v in verses_str.split(',')])

        # Find consecutive sequences
        sequences = []
        current_seq = [verses[0]]

        for v in verses[1:]:
            if v == current_seq[-1] + 1:
                current_seq.append(v)
            else:
                if len(current_seq) >= 3:
                    sequences.append(current_seq)
                current_seq = [v]

        if len(current_seq) >= 3:
            sequences.append(current_seq)

        if sequences:
            print(f"\n--- Psalm {psalm_ch} in prayer {prayer_id} ---")
            print(f"Verses: {verses}")
            for seq in sequences:
                print(f"  ✓ Consecutive: {seq[0]}-{seq[-1]} ({len(seq)} verses)")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("LITURGICAL INDEXER - ISSUE DIAGNOSIS")
    print("="*80)

    test_issue_1_empty_contexts()
    test_issue_2_duplicate_phrases()
    test_issue_3_entire_chapter()
    test_issue_4_phrase_when_verse()
    test_issue_5_verse_ranges()

    print("\n" + "="*80)
    print("DIAGNOSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
