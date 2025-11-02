"""Test the ktiv-kri normalization fix - simple version."""

import sys
sys.path.insert(0, '.')
from src.liturgy.liturgy_indexer import LiturgyIndexer

indexer = LiturgyIndexer(verbose=False)

# Canonical text with ktiv-kri notation
canonical = "וֶעֱז֣וּז נֽוֹרְאֹתֶ֣יךָ יֹאמֵ֑רוּ (וגדלותיך) [וּגְדֻלָּתְךָ֥] אֲסַפְּרֶֽנָּה׃"

# Prayer text with kri (read) form only
prayer = "עֱזוּז נוֹרְ֒אוֹתֶֽיךָ יֹאמֵֽרוּ וּגְדֻלָּתְ֒ךָ אֲסַפְּ֒רֶֽנָּה:"

# Normalize both
normalized_canonical = indexer._full_normalize(canonical)
normalized_prayer = indexer._full_normalize(prayer)

print("KTIV-KRI NORMALIZATION TEST")
print("=" * 60)
print(f"Canonical normalized: '{normalized_canonical}'")
print(f"Prayer normalized:    '{normalized_prayer}'")
print("=" * 60)

if normalized_canonical == normalized_prayer:
    print("SUCCESS: Texts match!")
else:
    print("MISMATCH:")
    can_words = normalized_canonical.split()
    pray_words = normalized_prayer.split()
    print(f"  Canonical: {len(can_words)} words")
    print(f"  Prayer: {len(pray_words)} words")

    for i, (c, p) in enumerate(zip(can_words, pray_words)):
        if c != p:
            print(f"  Diff at word {i+1}: '{c}' vs '{p}'")
