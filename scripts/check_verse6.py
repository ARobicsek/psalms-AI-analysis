"""Check why verse 6 of Psalm 145 is only phrase_match in prayers."""

import sqlite3

conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

# Check verse 6 matches across all prayers
cursor.execute("""
    SELECT prayer_id, match_type, confidence, phrase_length,
           psalm_phrase_normalized,
           SUBSTR(liturgy_context, 1, 150) as context
    FROM psalms_liturgy_index
    WHERE psalm_chapter=145 AND psalm_verse_start=6 AND psalm_verse_end=6
    ORDER BY prayer_id
""")

matches = cursor.fetchall()

print("VERSE 6 OF PSALM 145 - ACROSS ALL PRAYERS")
print("=" * 80)
print(f"Found {len(matches)} matches for verse 6\n")

for prayer_id, match_type, conf, phrase_len, normalized, context in matches[:5]:
    print(f"Prayer {prayer_id}:")
    print(f"  Type: {match_type} (conf: {conf:.2f}, length: {phrase_len})")
    print(f"  Normalized: {normalized[:80]}...")
    print()

# Get the canonical verse 6 text
# We need to connect to the Tanakh database
tanakh_conn = sqlite3.connect('data/tanakh.db')
tanakh_cursor = tanakh_conn.cursor()

try:
    tanakh_cursor.execute("""
        SELECT hebrew FROM verses
        WHERE book_name='Psalms' AND chapter=145 AND verse=6
    """)
    verse_result = tanakh_cursor.fetchone()
    if verse_result:
        verse_6_text = verse_result[0]
        print("\nCANONICAL PSALM 145:6:")
        print(f"  {verse_6_text}")

        # Normalize it to compare
        # We need to use the indexer's normalization
        from src.liturgy.liturgy_indexer import LiturgicalLibrarian
        indexer = LiturgicalLibrarian(verbose=False)
        normalized_canonical = indexer._full_normalize(verse_6_text)
        print(f"\n  Normalized: {normalized_canonical}")

        # Compare with what we found
        if matches:
            phrase_normalized = matches[0][4]
            print(f"\n  Found in prayer: {phrase_normalized}")
            print(f"\n  Match? {normalized_canonical == phrase_normalized}")
            if normalized_canonical != phrase_normalized:
                print("\n  MISMATCH! This explains why it's not exact_verse")
                print(f"  Canonical length: {len(normalized_canonical.split())} words")
                print(f"  Found length: {len(phrase_normalized.split())} words")
    else:
        print("\n⚠️  Could not find Psalm 145:6 in tanakh.db!")
except Exception as e:
    print(f"\n⚠️  Error accessing tanakh.db: {e}")

tanakh_conn.close()
conn.close()
