"""Compare Psalm 23 verses in tanakh.db vs prayer 574."""
import sys
import sqlite3
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.concordance.hebrew_text_processor import normalize_for_search

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def normalize_text(text: str) -> str:
    """Apply same normalization as liturgy_indexer._normalize_text()"""
    if not text:
        return text

    # Replace maqqef with space
    text = text.replace('\u05BE', ' ')

    # Remove geresh and gershayim
    text = text.replace('\u05F3', '')
    text = text.replace('\u05F4', '')

    # Remove ASCII punctuation
    text = re.sub(r'[,.:;!?\-\(\)\[\]{}\"\'`]', ' ', text)

    # Normalize whitespace
    text = ' '.join(text.split())

    return text

# Get canonical verses from tanakh.db
tanakh_conn = sqlite3.connect('database/tanakh.db')
tanakh_cursor = tanakh_conn.cursor()
tanakh_cursor.execute("""
    SELECT verse, hebrew
    FROM verses
    WHERE book_name = 'Psalms' AND chapter = 23
    ORDER BY verse
""")
canonical_verses = {v: text for v, text in tanakh_cursor.fetchall()}
tanakh_conn.close()

# Get prayer text
liturgy_conn = sqlite3.connect('data/liturgy.db')
liturgy_cursor = liturgy_conn.cursor()
liturgy_cursor.execute("SELECT hebrew_text, prayer_name FROM prayers WHERE prayer_id = 574")
prayer_text, prayer_name = liturgy_cursor.fetchone()
liturgy_conn.close()

# Find Psalm 23 in the prayer
print("=" * 80)
print(f"Comparing Canonical Psalm 23 vs Prayer 574 ({prayer_name})")
print("=" * 80)

for verse_num in range(1, 7):
    canonical = canonical_verses[verse_num]

    # Apply full normalization (consonantal + punctuation removal)
    canonical_norm = normalize_for_search(canonical, level='consonantal')
    canonical_norm = normalize_text(canonical_norm)

    prayer_norm = normalize_for_search(prayer_text, level='consonantal')
    prayer_norm = normalize_text(prayer_norm)

    # Check if canonical verse appears in prayer
    match = canonical_norm in prayer_norm

    print(f"\nVerse {verse_num}: {'✓ MATCH' if match else '✗ NO MATCH'}")
    print(f"Canonical: {canonical}")

    if not match:
        # Show normalized forms for debugging
        print(f"  Normalized canonical: {canonical_norm}")
        # Find similar substring in prayer
        if canonical_norm[:20] in prayer_norm:
            print(f"  (First 20 chars found in prayer)")
        else:
            print(f"  (Not found even partially)")
