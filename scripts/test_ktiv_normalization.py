"""Test the ktiv male/haser normalization to see what's breaking."""

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

# Get verse 4 (which is now missing)
tanakh_conn = sqlite3.connect('database/tanakh.db')
tanakh_cursor = tanakh_conn.cursor()
tanakh_cursor.execute('SELECT hebrew FROM verses WHERE book_name="Psalms" AND chapter=145 AND verse=4')
verse4 = tanakh_cursor.fetchone()[0]
tanakh_conn.close()

print("Testing verse 4 (now missing):")
print(f"Original: {verse4}")
print()

# Step by step normalization
# Step 1-4: Divine name, ktiv-kri, maqqef, vowels
import re
from src.concordance.hebrew_text_processor import normalize_for_search

text = verse4
text = text.replace("ה'", "יהוה")
text = re.sub(r'\([^)]*\)', '', text)
text = re.sub(r'\[([^\]]*)\]', r'\1', text)
text = text.replace('\u05BE', ' ')
text = normalize_for_search(text, level='consonantal')
print(f"After steps 1-4 (consonantal): {text}")

# Step 5: ktiv male/haser
normalized = indexer._normalize_ktiv_male_haser(text)
print(f"After ktiv male/haser: {normalized}")
print()

# Do the same for prayer
prayer_normalized_partial = indexer._full_normalize(prayer_text).split()
print(f"Looking for '{normalized}' in prayer...")
if normalized in indexer._full_normalize(prayer_text):
    print("FOUND in prayer (full normalization)")
else:
    # Check if partial string exists
    print("NOT FOUND in prayer (full normalization)")
    # Try to find similar text
    words = normalized.split()
    for i, word in enumerate(words):
        if word in indexer._full_normalize(prayer_text):
            print(f"  Word {i} '{word}' found in prayer")
        else:
            print(f"  Word {i} '{word}' NOT found")

# Compare a specific word that might be problematic
print()
print("Detailed word analysis:")
test_words = [
    ("יגידו", "from verse 4 - should match"),
    ("וגבורתיך", "from verse 4 - should match"),
]

for word, desc in test_words:
    # Normalize word
    w_norm = normalize_for_search(word, level='consonantal')
    w_ktiv = indexer._normalize_ktiv_male_haser(w_norm)
    print(f"{desc}:")
    print(f"  Original: {word}")
    print(f"  Consonantal: {w_norm}")
    print(f"  After ktiv: {w_ktiv}")
    print()
