"""Test the ktiv-kri normalization fix."""

import sys
sys.path.insert(0, '.')
from src.liturgy.liturgy_indexer import LiturgyIndexer

indexer = LiturgyIndexer(verbose=False)

print("TESTING KTIV-KRI NORMALIZATION FIX")
print("=" * 80)

# Canonical text with ktiv-kri notation
canonical = "וֶעֱז֣וּז נֽוֹרְאֹתֶ֣יךָ יֹאמֵ֑רוּ (וגדלותיך) [וּגְדֻלָּתְךָ֥] אֲסַפְּרֶֽנָּה׃"

# Prayer text with kri (read) form only
prayer = "עֱזוּז נוֹרְ֒אוֹתֶֽיךָ יֹאמֵֽרוּ וּגְדֻלָּתְ֒ךָ אֲסַפְּ֒רֶֽנָּה:"

print("\nCanonical text (with ktiv-kri):")
print(f"  {canonical}")

print("\nPrayer text (kri only):")
print(f"  {prayer}")

# Normalize both
normalized_canonical = indexer._full_normalize(canonical)
normalized_prayer = indexer._full_normalize(prayer)

print("\n" + "-" * 80)
print("\nNormalized canonical:")
print(f"  {normalized_canonical}")

print("\nNormalized prayer:")
print(f"  {normalized_prayer}")

print("\n" + "=" * 80)
if normalized_canonical == normalized_prayer:
    print("✓ SUCCESS! Texts match after normalization")
    print("  The ktiv-kri fix is working correctly!")
else:
    print("✗ MISMATCH! Texts don't match")
    print(f"\n  Canonical length: {len(normalized_canonical)} chars")
    print(f"  Prayer length: {len(normalized_prayer)} chars")

    # Show differences
    can_words = normalized_canonical.split()
    pray_words = normalized_prayer.split()

    print(f"\n  Canonical words: {len(can_words)}")
    print(f"  Prayer words: {len(pray_words)}")

    if len(can_words) == len(pray_words):
        print("\n  Word-by-word comparison:")
        for i, (c, p) in enumerate(zip(can_words, pray_words)):
            if c != p:
                print(f"    Word {i+1}: '{c}' != '{p}'")
    else:
        print(f"\n  Canonical: {' '.join(can_words)}")
        print(f"  Prayer:    {' '.join(pray_words)}")

print("=" * 80)
