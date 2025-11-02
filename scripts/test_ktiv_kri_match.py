"""Test the ktiv-kri normalization fix - just check if they match."""

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

if normalized_canonical == normalized_prayer:
    print("SUCCESS: Ktiv-kri normalization is working!")
    print(f"Both texts normalize to the same {len(normalized_canonical.split())} words")
else:
    print("FAIL: Texts still don't match after normalization")
    print(f"Canonical: {len(normalized_canonical.split())} words, {len(normalized_canonical)} chars")
    print(f"Prayer: {len(normalized_prayer.split())} words, {len(normalized_prayer)} chars")

    # Try to show ASCII-safe version
    can_words = normalized_canonical.split()
    pray_words = normalized_prayer.split()

    if len(can_words) != len(pray_words):
        print(f"\nWord count mismatch: {len(can_words)} vs {len(pray_words)}")
    else:
        mismatches = sum(1 for c, p in zip(can_words, pray_words) if c != p)
        if mismatches > 0:
            print(f"\n{mismatches} words differ out of {len(can_words)}")
