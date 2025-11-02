"""Debug the ktiv-kri normalization."""

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

# Write to file
with open('output/ktiv_kri_debug.txt', 'w', encoding='utf-8') as f:
    f.write("CANONICAL TEXT:\n")
    f.write(canonical + "\n\n")
    f.write("NORMALIZED CANONICAL:\n")
    f.write(normalized_canonical + "\n\n")
    f.write("PRAYER TEXT:\n")
    f.write(prayer + "\n\n")
    f.write("NORMALIZED PRAYER:\n")
    f.write(normalized_prayer + "\n\n")

    f.write("=" * 60 + "\n")
    f.write("WORD-BY-WORD COMPARISON:\n")
    f.write("=" * 60 + "\n")

    can_words = normalized_canonical.split()
    pray_words = normalized_prayer.split()

    for i, (c, p) in enumerate(zip(can_words, pray_words)):
        match = "✓" if c == p else "✗"
        f.write(f"Word {i+1} {match}:\n")
        f.write(f"  Canonical: {c}\n")
        f.write(f"  Prayer:    {p}\n")
        if c != p:
            f.write(f"  Canonical bytes: {c.encode('utf-8').hex()}\n")
            f.write(f"  Prayer bytes:    {p.encode('utf-8').hex()}\n")
        f.write("\n")

print("Debug output written to output/ktiv_kri_debug.txt")
