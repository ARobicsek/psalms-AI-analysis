"""Check what verse 6 actually looks like in Prayer 91."""

import sqlite3
import sys
sys.path.insert(0, '.')
from src.liturgy.liturgy_indexer import LiturgyIndexer

# Set stdout encoding to UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

indexer = LiturgyIndexer(verbose=False)

# Get prayer text
conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()
cursor.execute('SELECT prayer_id, prayer_name, hebrew_text FROM prayers WHERE prayer_id=91')
prayer_id, prayer_name, prayer_text = cursor.fetchone()
conn.close()

# Get canonical verse 6
tanakh_conn = sqlite3.connect('database/tanakh.db')
tanakh_cursor = tanakh_conn.cursor()
tanakh_cursor.execute('SELECT hebrew FROM verses WHERE book_name="Psalms" AND chapter=145 AND verse=6')
result = tanakh_cursor.fetchone()
canonical_verse6 = result[0] if result else None
tanakh_conn.close()

print(f"Prayer {prayer_id}: {prayer_name}")
print(f"Prayer text length: {len(prayer_text)} chars")
print()

if not canonical_verse6:
    print("ERROR: Could not find Psalm 145:6 in tanakh.db")
    sys.exit(1)

print(f"Canonical Psalm 145:6:")
print(f"  {canonical_verse6}")
print()

# Normalize both
normalized_prayer = indexer._full_normalize(prayer_text)
normalized_canonical = indexer._full_normalize(canonical_verse6)

print(f"Normalized canonical verse 6:")
print(f"  {normalized_canonical}")
print()

# Search for verse 6 in prayer
if normalized_canonical in normalized_prayer:
    print("✓ Verse 6 FOUND in prayer (exact match after normalization)")
    idx = normalized_prayer.find(normalized_canonical)
    print(f"  Position: {idx}")
else:
    print("✗ Verse 6 NOT FOUND in prayer after normalization")
    print()

    # Try finding fragments
    verse_words = normalized_canonical.split()
    print(f"Searching for fragments of verse 6 ({len(verse_words)} words)...")

    found_fragments = []
    for i in range(len(verse_words)):
        for j in range(i+2, len(verse_words)+1):
            fragment = ' '.join(verse_words[i:j])
            if fragment in normalized_prayer:
                found_fragments.append((i, j, fragment))

    if found_fragments:
        print(f"  Found {len(found_fragments)} fragments:")
        for i, j, fragment in found_fragments[:5]:  # Show first 5
            print(f"    Words {i+1}-{j}: '{fragment}'")
    else:
        print("  No fragments found")

print()

# Write detailed output to file
with open('output/prayer91_verse6_check.txt', 'w', encoding='utf-8') as f:
    f.write(f"PRAYER {prayer_id}: {prayer_name}\n")
    f.write("=" * 60 + "\n\n")

    f.write("CANONICAL VERSE 6 (Psalm 145:6):\n")
    f.write(canonical_verse6 + "\n\n")
    f.write("NORMALIZED:\n")
    f.write(normalized_canonical + "\n\n")

    f.write("=" * 60 + "\n\n")

    # Find the position of key words
    search_terms = ['עזוז', 'נוראותיך', 'גדולתך']
    for term in search_terms:
        idx = prayer_text.find(term)
        if idx != -1:
            f.write(f"PRAYER 91 (snippet around '{term}' at position {idx}):\n")
            snippet = prayer_text[max(0, idx-100):idx+200]
            f.write(snippet + "\n\n")
            f.write("NORMALIZED SNIPPET:\n")
            f.write(indexer._full_normalize(snippet) + "\n\n")
            break
    else:
        f.write("None of the search terms found in prayer text\n\n")

    f.write("=" * 60 + "\n\n")
    f.write("FULL PRAYER TEXT:\n")
    f.write(prayer_text + "\n")

print("Detailed output written to output/prayer91_verse6_check.txt")
