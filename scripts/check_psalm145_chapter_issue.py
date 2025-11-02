"""Check why Psalm 145 isn't matching as entire_chapter in prayers that contain it."""

import sqlite3
import sys

def check_psalm145_in_prayers():
    conn = sqlite3.connect('data/liturgy.db')
    cursor = conn.cursor()

    # Prayer IDs that should contain entire Psalm 145
    prayer_ids = [107, 91, 900, 801, 736]

    print("=" * 80)
    print("PSALM 145 ENTIRE CHAPTER DETECTION ISSUE")
    print("=" * 80)

    # Determine total verses from the data itself
    cursor.execute("""
        SELECT MAX(psalm_verse_end)
        FROM psalms_liturgy_index
        WHERE psalm_chapter=145
    """)
    total_verses = cursor.fetchone()[0]
    print(f"\nPsalm 145 total verses (from index): {total_verses}")

    # Psalm 145 has 21 verses (we know this)
    if total_verses != 21:
        print(f"  ⚠️  Expected 21 verses, found {total_verses}")

    # Check for entire_chapter matches anywhere
    cursor.execute("""
        SELECT prayer_id, COUNT(*)
        FROM psalms_liturgy_index
        WHERE psalm_chapter=145 AND match_type='entire_chapter'
        GROUP BY prayer_id
    """)
    entire_chapter_matches = cursor.fetchall()
    print(f"\nTotal entire_chapter matches for Psalm 145: {len(entire_chapter_matches)}")
    if entire_chapter_matches:
        print("Found in prayers:", [pid for pid, _ in entire_chapter_matches])

    # Check each specified prayer
    for prayer_id in prayer_ids:
        print("\n" + "=" * 80)
        print(f"PRAYER {prayer_id}")
        print("=" * 80)

        # Get all matches for Psalm 145 in this prayer
        cursor.execute("""
            SELECT match_type, psalm_verse_start, psalm_verse_end, confidence,
                   SUBSTR(liturgy_context, 1, 100) as context_preview
            FROM psalms_liturgy_index
            WHERE prayer_id=? AND psalm_chapter=145
            ORDER BY psalm_verse_start, psalm_verse_end
        """, (prayer_id,))

        matches = cursor.fetchall()
        print(f"\nTotal matches: {len(matches)}")

        if not matches:
            print("  NO MATCHES FOUND!")
            continue

        # Group by match type
        by_type = {}
        verses_covered = set()
        for match in matches:
            match_type = match[0]
            verse_start = match[1]
            verse_end = match[2]

            if match_type not in by_type:
                by_type[match_type] = []
            by_type[match_type].append(match)

            # Track covered verses
            if verse_start and verse_end:
                for v in range(verse_start, verse_end + 1):
                    verses_covered.add(v)

        # Show summary by type
        for match_type, type_matches in sorted(by_type.items()):
            print(f"\n  {match_type}: {len(type_matches)} matches")
            for m in type_matches[:5]:  # Show first 5
                print(f"    {m[1]}:{m[2]} (conf: {m[3]:.2f}) - {m[4][:60]}...")
            if len(type_matches) > 5:
                print(f"    ... and {len(type_matches) - 5} more")

        # Check verse coverage
        print(f"\n  Verses covered: {len(verses_covered)}/{total_verses}")
        missing_verses = set(range(1, total_verses + 1)) - verses_covered
        if missing_verses:
            print(f"  Missing verses: {sorted(missing_verses)}")
        else:
            print("  ALL VERSES COVERED!")

            # If all verses covered but no entire_chapter, why?
            if 'entire_chapter' not in by_type:
                print("\n  ⚠️  ALL VERSES PRESENT BUT NO entire_chapter MATCH!")
                print("  Checking exact_verse coverage...")

                # Count exact_verse matches
                exact_verses = set()
                for m in by_type.get('exact_verse', []):
                    for v in range(m[1], m[2] + 1):
                        exact_verses.add(v)

                print(f"  exact_verse count: {len(by_type.get('exact_verse', []))}")
                print(f"  exact_verse covers: {len(exact_verses)}/{total_verses} verses")

                # Count verse_range matches
                range_verses = set()
                for m in by_type.get('verse_range', []):
                    for v in range(m[1], m[2] + 1):
                        range_verses.add(v)

                print(f"  verse_range count: {len(by_type.get('verse_range', []))}")
                print(f"  verse_range covers: {len(range_verses)}/{total_verses} verses")

                combined_exact = exact_verses | range_verses
                print(f"  exact_verse + verse_range: {len(combined_exact)}/{total_verses} verses")

                if len(combined_exact) < total_verses:
                    missing_from_exact = set(range(1, total_verses + 1)) - combined_exact
                    print(f"  Verses not in exact_verse or verse_range: {sorted(missing_from_exact)}")

                    # Show what type these are
                    for v in sorted(missing_from_exact)[:5]:
                        cursor.execute("""
                            SELECT match_type, psalm_verse_start, psalm_verse_end, confidence
                            FROM psalms_liturgy_index
                            WHERE prayer_id=? AND psalm_chapter=145
                              AND psalm_verse_start <= ? AND psalm_verse_end >= ?
                        """, (prayer_id, v, v))
                        verse_matches = cursor.fetchall()
                        print(f"    Verse {v}: {[f'{m[0]}({m[1]}:{m[2]})' for m in verse_matches]}")

    conn.close()

if __name__ == '__main__':
    check_psalm145_in_prayers()
