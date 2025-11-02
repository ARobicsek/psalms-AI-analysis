"""Check the detailed match structure for Psalm 145 in Prayer 107."""

import sqlite3

conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

prayer_id = 900
psalm_ch = 145

print(f"DETAILED MATCH STRUCTURE - Psalm {psalm_ch} in Prayer {prayer_id}")
print("=" * 80)

cursor.execute("""
    SELECT match_type, psalm_verse_start, psalm_verse_end, confidence
    FROM psalms_liturgy_index
    WHERE prayer_id=? AND psalm_chapter=?
    ORDER BY psalm_verse_start, psalm_verse_end
""", (prayer_id, psalm_ch))

matches = cursor.fetchall()

print(f"\nAll matches ({len(matches)} total):")
for match_type, vs, ve, conf in matches:
    verse_span = f"{vs}:{ve}" if vs == ve else f"{vs}-{ve}"
    print(f"  {match_type:15} Psalm {psalm_ch}:{verse_span:10} (conf: {conf:.2f})")

# Count by type
exact_verse = [m for m in matches if m[0] == 'exact_verse']
verse_range = [m for m in matches if m[0] == 'verse_range']
phrase_match = [m for m in matches if m[0] == 'phrase_match']

print(f"\nBreakdown:")
print(f"  exact_verse: {len(exact_verse)}")
print(f"  verse_range: {len(verse_range)}")
print(f"  phrase_match: {len(phrase_match)}")

# Check verse coverage from exact_verse ONLY
# This is what the chapter detection logic does
covered_by_exact_single = set()
for m in exact_verse:
    vs, ve = m[1], m[2]
    # The bug: only adds if single verse!
    if vs == ve:
        covered_by_exact_single.add(vs)

print(f"\nVerse coverage FROM exact_verse (SINGLE verse only - THE BUG!):")
print(f"  Covered: {len(covered_by_exact_single)}/21 verses")
if covered_by_exact_single:
    print(f"  Verses: {sorted(covered_by_exact_single)}")

# What SHOULD happen: count all verses in exact_verse matches
covered_by_exact_all = set()
for m in exact_verse:
    vs, ve = m[1], m[2]
    for v in range(vs, ve + 1):
        covered_by_exact_all.add(v)

print(f"\nVerse coverage FROM exact_verse (ALL - what it SHOULD be):")
print(f"  Covered: {len(covered_by_exact_all)}/21 verses")
if covered_by_exact_all:
    print(f"  Verses: {sorted(covered_by_exact_all)}")

# Now add verse_range coverage
covered_total = set(covered_by_exact_all)
for m in verse_range:
    vs, ve = m[1], m[2]
    for v in range(vs, ve + 1):
        covered_total.add(v)

print(f"\nVerse coverage FROM exact_verse + verse_range:")
print(f"  Covered: {len(covered_total)}/21 verses")

missing = set(range(1, 22)) - covered_total
if missing:
    print(f"  Missing: {sorted(missing)}")
else:
    print(f"  ALL VERSES COVERED!")

print("\n" + "=" * 80)
print("DIAGNOSIS:")
print("=" * 80)
if len(covered_total) == 21 and len(covered_by_exact_single) < 21:
    print("BUG CONFIRMED: Chapter detection only counts SINGLE-verse exact_verse matches!")
    print(f"  Single-verse exact_verse: {len(covered_by_exact_single)}/21")
    print(f"  Actual coverage: {len(covered_total)}/21")
    print("\nThe fix: Chapter detection should count ALL verses in exact_verse matches,")
    print("not just single-verse matches!")

conn.close()
