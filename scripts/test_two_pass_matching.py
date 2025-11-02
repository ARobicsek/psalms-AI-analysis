"""Test the two-pass matching (exact + fuzzy) for Prayer 91 verse 6."""

import sqlite3
import sys
sys.path.insert(0, '.')
from src.liturgy.liturgy_indexer import LiturgyIndexer

# Set UTF-8 encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

indexer = LiturgyIndexer(verbose=False)

# Get Prayer 91 text
liturgy_conn = sqlite3.connect('data/liturgy.db')
liturgy_cursor = liturgy_conn.cursor()
liturgy_cursor.execute('SELECT hebrew_text FROM prayers WHERE prayer_id=91')
prayer_text = liturgy_cursor.fetchone()[0]
liturgy_conn.close()

# Get Psalm 145 verse 6 from tanakh
tanakh_conn = sqlite3.connect('database/tanakh.db')
tanakh_cursor = tanakh_conn.cursor()
tanakh_cursor.execute('SELECT hebrew FROM verses WHERE book_name="Psalms" AND chapter=145 AND verse=6')
verse6 = tanakh_cursor.fetchone()[0]
tanakh_conn.close()

print("Testing two-pass matching for Psalm 145:6 in Prayer 91:")
print(f"Verse 6: {verse6}")
print()

# Test PASS 1: Exact matching (no ktiv normalization)
print("PASS 1: Exact matching (without ktiv normalization)")
normalized_prayer_exact = indexer._full_normalize(prayer_text, apply_ktiv_normalization=False)
normalized_verse_exact = indexer._full_normalize(verse6, apply_ktiv_normalization=False)
print(f"  Prayer (excerpt): {normalized_prayer_exact[:100]}...")
print(f"  Verse 6 normalized: {normalized_verse_exact}")

if normalized_verse_exact in normalized_prayer_exact:
    print("  ✓ FOUND in exact pass")
    exact_match = True
else:
    print("  ✗ NOT FOUND in exact pass")
    exact_match = False

print()

# Test PASS 2: Fuzzy matching (with ktiv normalization)
print("PASS 2: Fuzzy matching (with ktiv normalization)")
normalized_prayer_fuzzy = indexer._full_normalize(prayer_text, apply_ktiv_normalization=True)
normalized_verse_fuzzy = indexer._full_normalize(verse6, apply_ktiv_normalization=True)
print(f"  Prayer (excerpt): {normalized_prayer_fuzzy[:100]}...")
print(f"  Verse 6 normalized: {normalized_verse_fuzzy}")

if normalized_verse_fuzzy in normalized_prayer_fuzzy:
    print("  ✓ FOUND in fuzzy pass")
    fuzzy_match = True
else:
    print("  ✗ NOT FOUND in fuzzy pass")
    fuzzy_match = False

print()
print("=" * 60)
if exact_match:
    print("Result: Verse 6 would be matched in EXACT pass")
elif fuzzy_match:
    print("Result: Verse 6 would be matched in FUZZY pass")
else:
    print("Result: Verse 6 would NOT be matched in either pass")
    print()
    print("Debugging: Let's check word-by-word")
    verse_words = normalized_verse_fuzzy.split()
    prayer_words = set(normalized_prayer_fuzzy.split())
    for i, word in enumerate(verse_words):
        if word in prayer_words:
            print(f"  Word {i+1} '{word}': FOUND")
        else:
            print(f"  Word {i+1} '{word}': NOT FOUND")
