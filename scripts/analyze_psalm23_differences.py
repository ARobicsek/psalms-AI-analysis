"""Analyze consonantal differences between canonical and liturgical Psalm 23."""
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
    text = text.replace('\u05BE', ' ')  # maqqef
    text = text.replace('\u05F3', '')   # geresh
    text = text.replace('\u05F4', '')   # gershayim
    text = re.sub(r'[,.:;!?\-\(\)\[\]{}\"\'`]', ' ', text)
    text = ' '.join(text.split())
    return text

# Get canonical text
tanakh_conn = sqlite3.connect('database/tanakh.db')
cursor = tanakh_conn.cursor()
cursor.execute("""
    SELECT GROUP_CONCAT(hebrew, ' ')
    FROM verses
    WHERE book_name = 'Psalms' AND chapter = 23
    ORDER BY verse
""")
canonical_full = cursor.fetchone()[0]
tanakh_conn.close()

# Get liturgical text (just Psalm 23 portion)
liturgy_conn = sqlite3.connect('data/liturgy.db')
cursor = liturgy_conn.cursor()
cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = 574")
prayer_full = cursor.fetchone()[0]
liturgy_conn.close()

# Extract just Psalm 23 from prayer
start = prayer_full.find("מִזְמוֹר לְדָוִד")
end = prayer_full.find("אִם תָּשִׁיב", start)
liturgical_psalm23 = prayer_full[start:end].strip()

# Remove the ending colon and "אִם תָּשִׁיב" intro
liturgical_psalm23 = liturgical_psalm23.rstrip(':').strip()

print("CANONICAL (tanakh.db):")
print("=" * 80)
print(canonical_full)
print()

print("LITURGICAL (prayer 574):")
print("=" * 80)
print(liturgical_psalm23)
print()

# Normalize both
canonical_norm = normalize_for_search(canonical_full, level='consonantal')
canonical_norm = normalize_text(canonical_norm)

liturgical_norm = normalize_for_search(liturgical_psalm23, level='consonantal')
liturgical_norm = normalize_text(liturgical_norm)

print("NORMALIZED CANONICAL:")
print("=" * 80)
print(canonical_norm)
print()

print("NORMALIZED LITURGICAL:")
print("=" * 80)
print(liturgical_norm)
print()

# Compare
if canonical_norm == liturgical_norm:
    print("✓ IDENTICAL at consonantal level!")
else:
    print("✗ DIFFERENT at consonantal level")
    print(f"\nCanonical length: {len(canonical_norm)} chars")
    print(f"Liturgical length: {len(liturgical_norm)} chars")

    # Find first difference
    for i, (c, l) in enumerate(zip(canonical_norm, liturgical_norm)):
        if c != l:
            print(f"\nFirst difference at position {i}:")
            print(f"  Canonical:  ...{canonical_norm[max(0,i-20):i+20]}...")
            print(f"  Liturgical: ...{liturgical_norm[max(0,i-20):i+20]}...")
            break
