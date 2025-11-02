"""Simple check for Psalm 145 chapter detection."""

import sqlite3

conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

# Prayer IDs that should contain entire Psalm 145
prayer_ids = [107, 91, 900, 801, 736]

print("PSALM 145 CHAPTER DETECTION DIAGNOSTIC")
print("=" * 80)

# Check each prayer
for prayer_id in prayer_ids:
    cursor.execute("""
        SELECT match_type, COUNT(*),
               GROUP_CONCAT(DISTINCT CAST(psalm_verse_start AS TEXT) || '-' || CAST(psalm_verse_end AS TEXT))
        FROM psalms_liturgy_index
        WHERE prayer_id=? AND psalm_chapter=145
        GROUP BY match_type
    """, (prayer_id,))

    results = cursor.fetchall()
    print(f"\nPrayer {prayer_id}:")

    if not results:
        print("  NO MATCHES")
        continue

    for match_type, count, verses in results:
        print(f"  {match_type}: {count} matches")
        if match_type == 'entire_chapter':
            print(f"    Verses: {verses}")
        elif match_type in ['exact_verse', 'verse_range']:
            # Count unique verses covered
            cursor.execute("""
                SELECT psalm_verse_start, psalm_verse_end
                FROM psalms_liturgy_index
                WHERE prayer_id=? AND psalm_chapter=145 AND match_type=?
            """, (prayer_id, match_type))
            verse_matches = cursor.fetchall()
            covered = set()
            for vs, ve in verse_matches:
                for v in range(vs, ve + 1):
                    covered.add(v)
            print(f"    Covers {len(covered)}/21 verses: {sorted(covered)[:10]}...")

    # Check total verse coverage
    cursor.execute("""
        SELECT psalm_verse_start, psalm_verse_end
        FROM psalms_liturgy_index
        WHERE prayer_id=? AND psalm_chapter=145
    """, (prayer_id,))
    all_matches = cursor.fetchall()
    all_covered = set()
    for vs, ve in all_matches:
        if vs and ve:
            for v in range(vs, ve + 1):
                all_covered.add(v)

    print(f"  TOTAL COVERAGE: {len(all_covered)}/21 verses")
    if len(all_covered) == 21:
        print("  >>> ALL 21 VERSES PRESENT BUT NO entire_chapter!")
    elif len(all_covered) >= 18:
        print(f"  >>> Nearly complete ({len(all_covered)}/21)")

    missing = set(range(1, 22)) - all_covered
    if missing:
        print(f"  Missing verses: {sorted(missing)}")

# Also check what prayers DO have entire_chapter
print("\n" + "=" * 80)
print("Prayers with entire_chapter for Psalm 145:")
cursor.execute("""
    SELECT prayer_id
    FROM psalms_liturgy_index
    WHERE psalm_chapter=145 AND match_type='entire_chapter'
""")
chapter_prayers = cursor.fetchall()
print(f"  Found {len(chapter_prayers)}: {[p[0] for p in chapter_prayers]}")

conn.close()
