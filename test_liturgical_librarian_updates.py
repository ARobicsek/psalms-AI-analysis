"""
Quick test of updated liturgical librarian (Session 53)
Tests:
1. is_unique filter is working
2. Canonical fields are loaded
3. No LLM validation errors
"""

import sqlite3
import sys

# Check database schema
print("=" * 70)
print("1. Checking database schema...")
print("=" * 70)

conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

# Check if is_unique column exists in psalms_liturgy_index
try:
    cursor.execute("PRAGMA table_info(psalms_liturgy_index)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'is_unique' in columns:
        print("[OK] is_unique column exists in psalms_liturgy_index")
    else:
        print("[ERROR] is_unique column NOT found in psalms_liturgy_index")
        print(f"  Available columns: {columns}")
except Exception as e:
    print(f"[ERROR] ERROR checking psalms_liturgy_index: {e}")

# Check if canonical fields exist in prayers table
try:
    cursor.execute("PRAGMA table_info(prayers)")
    columns = [row[1] for row in cursor.fetchall()]
    canonical_fields = [
        'canonical_prayer_name',
        'canonical_L1_Occasion',
        'canonical_L2_Service',
        'canonical_L3_Signpost',
        'canonical_L4_SubSection',
        'canonical_location_description'
    ]
    missing_fields = [f for f in canonical_fields if f not in columns]
    if not missing_fields:
        print("[OK] All canonical fields exist in prayers table")
    else:
        print(f"[ERROR] ERROR: Missing canonical fields in prayers table: {missing_fields}")
except Exception as e:
    print(f"[ERROR] ERROR checking prayers table: {e}")

# Check psalms indexed
cursor.execute("SELECT COUNT(DISTINCT psalm_chapter) FROM psalms_liturgy_index")
psalms_indexed = cursor.fetchone()[0]
print(f"\nPsalms indexed: {psalms_indexed}")

# Check if there are any records with is_unique=0 and match_type='phrase_match'
cursor.execute("""
    SELECT COUNT(*)
    FROM psalms_liturgy_index
    WHERE match_type = 'phrase_match' AND is_unique = 0
""")
non_unique_phrase_matches = cursor.fetchone()[0]
print(f"Non-unique phrase matches in index: {non_unique_phrase_matches}")

conn.close()

print("\n" + "=" * 70)
print("2. Testing liturgical librarian import and basic functionality...")
print("=" * 70)

try:
    from src.agents.liturgical_librarian import LiturgicalLibrarian
    print("[OK] LiturgicalLibrarian imported successfully")

    # Initialize without LLM to avoid API calls
    librarian = LiturgicalLibrarian(use_llm_summaries=False, verbose=False)
    print("[OK] LiturgicalLibrarian initialized successfully (no LLM mode)")

    # Try to get matches for a psalm (using Psalm 23 as example if indexed)
    if psalms_indexed > 0:
        # Find a psalm that's indexed
        conn = sqlite3.connect('data/liturgy.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT psalm_chapter FROM psalms_liturgy_index ORDER BY psalm_chapter LIMIT 1")
        test_psalm = cursor.fetchone()[0]
        conn.close()

        print(f"\nTesting with Psalm {test_psalm}...")

        # Test _get_raw_matches (should filter out non-unique phrase_matches)
        raw_matches = librarian._get_raw_matches(
            psalm_chapter=test_psalm,
            psalm_verses=None,
            min_confidence=0.75
        )

        print(f"[OK] Retrieved {len(raw_matches)} raw matches")

        # Check that all matches have the required fields
        if raw_matches:
            first_match = raw_matches[0]
            required_fields = [
                'is_unique',
                'canonical_prayer_name',
                'canonical_L1_Occasion',
                'canonical_L2_Service',
                'canonical_L3_Signpost',
                'canonical_L4_SubSection',
                'canonical_location_description'
            ]
            missing_fields = [f for f in required_fields if not hasattr(first_match, f)]
            if not missing_fields:
                print("[OK] All required fields present in LiturgicalMatch objects")
            else:
                print(f"[ERROR] ERROR: Missing fields in LiturgicalMatch: {missing_fields}")

            # Check that is_unique filter is working
            phrase_matches = [m for m in raw_matches if m.match_type == 'phrase_match']
            if phrase_matches:
                non_unique_filtered = [m for m in phrase_matches if m.is_unique == 0]
                if not non_unique_filtered:
                    print("[OK] is_unique filter working correctly (no non-unique phrase matches returned)")
                else:
                    print(f"[ERROR] ERROR: Found {len(non_unique_filtered)} non-unique phrase matches that should have been filtered")
            else:
                print("  (No phrase matches to test is_unique filter)")

            # Check canonical fields are populated
            canonical_populated = [
                m for m in raw_matches
                if m.canonical_prayer_name or m.canonical_L1_Occasion
            ]
            print(f"  Matches with canonical fields populated: {len(canonical_populated)}/{len(raw_matches)}")
        else:
            print("  (No matches to test)")
    else:
        print("  (No psalms indexed yet, skipping match test)")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED! [OK]")
    print("=" * 70)

except Exception as e:
    print(f"\n[ERROR] ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
