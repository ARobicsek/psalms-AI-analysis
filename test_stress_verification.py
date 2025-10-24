"""
Verify stress patterns in Psalm 145:11 using Hebrew stress rules.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

# Word-by-word analysis with syllabification
words = [
    {
        "hebrew": "כְּבוֹד",
        "syllables": ["kə", "vōdh"],
        "stress_position": -1,  # ultima (last syllable)
        "stressed_form": "kə-**VŌDH**",
        "stress_syllable": "vōdh"
    },
    {
        "hebrew": "מַלְכוּתְךָ",
        "syllables": ["mal", "khūth", "khā"],
        "stress_position": -1,  # ultima (last syllable)
        "stressed_form": "mal-khūth-**KHĀ**",
        "stress_syllable": "khā"
    },
    {
        "hebrew": "יֹאמֵרוּ",
        "syllables": ["yō", "mē", "rū"],
        "stress_position": -1,  # ultima? or penultimate?
        # Need to check: defective plural forms often penultimate
        "stressed_form": "yō-**MĒ**-rū OR **YŌ**-mē-rū",
        "note": "Segolate plural - need to verify"
    },
    {
        "hebrew": "וּגְבוּרָתְךָ",
        "syllables": ["ū", "ghə", "vū", "rā", "thə", "khā"],
        "stress_position": -1,  # ultima
        "stressed_form": "ū-ghə-vū-rā-thə-**KHĀ**",
        "stress_syllable": "khā"
    },
    {
        "hebrew": "יְדַבֵּרוּ",
        "syllables": ["yə", "dha", "bē", "rū"],
        "stress_position": -2,  # penultimate (before ū ending)
        # Pi'el verbs with ū ending typically penultimate
        "stressed_form": "yə-dha-**BĒ**-rū",
        "stress_syllable": "bē"
    }
]

print("STRESS VERIFICATION - Psalm 145:11")
print("=" * 70)
print()
print("Hebrew: כְּבוֹד מַלְכוּתְךָ יֹאמֵרוּ וּגְבוּרָתְךָ יְדַבֵּרוּ")
print()
print("=" * 70)
print()

for word in words:
    print(f"Hebrew:      {word['hebrew']}")
    print(f"Syllables:   {'-'.join(word['syllables'])}")
    print(f"Stress pos:  {word['stress_position']} (ultima=-1, penult=-2)")
    print(f"Stressed:    {word['stressed_form']}")
    if 'note' in word:
        print(f"Note:        {word['note']}")
    print()

print("=" * 70)
print("USER'S PROPOSED STRESS PATTERN")
print("=" * 70)
print()
print("kə-VODH mal-khūth-KHĀ yō-ME-rū ū-ghə-vū-rā-thə-KHĀ yə-dha-BE-rū")
print()
print("Breaking down:")
print("  kə-VODH          ✓ (ultima stress)")
print("  mal-khūth-KHĀ    ✓ (ultima stress)")
print("  yō-ME-rū         ? (need to verify: milra' or mil'el)")
print("  ū-ghə-vū-rā-thə-KHĀ  ✓ (ultima stress)")
print("  yə-dha-BE-rū     ✓ (penultimate stress - Pi'el with ū ending)")
print()

print("=" * 70)
print("CANTILLATION MARK ANALYSIS")
print("=" * 70)
print()
print("The cantillation marks tell us WHERE the stress falls:")
print()
print("כְּב֣וֹד    - Munah on vōdh → stress on vōdh ✓")
print("מַלְכוּתְךָ֣  - Munah on khā → stress on khā ✓")
print("יֹאמֵ֑רוּ   - Atnah on mē → stress on mē (PENULTIMATE!) ✓")
print("וּגְבוּרָתְךָ֥ - Merkha on khā → stress on khā ✓")
print("יְדַבֵּֽרוּ  - Silluq on bē → stress on bē (PENULTIMATE!) ✓")
print()

print("=" * 70)
print("CORRECT STRESS PATTERN")
print("=" * 70)
print()
print("kə-**VŌDH** mal-khūth-**KHĀ** yō-**MĒ**-rū // ū-ghə-vū-rā-thə-**KHĀ** yə-dha-**BĒ**-rū")
print()
print("Stress count: [3 stresses] + [2 stresses] = 3+2 pattern")
print()
print("Stressed syllables:")
print("  Colon 1: VŌDH | KHĀ | MĒ  (3 stresses)")
print("  Colon 2: KHĀ | BĒ          (2 stresses)")
print()

print("=" * 70)
print("KEY INSIGHT: CANTILLATION MARKS OVERRIDE DEFAULT RULES")
print("=" * 70)
print()
print("While Hebrew typically has ultima stress (milra'), the cantillation marks")
print("tell us EXACTLY where the stress falls - even when it's exceptional.")
print()
print("In this verse:")
print("  - יֹאמֵ֑רוּ has Atnah on מֵ (penultimate) → stress on MĒ not rū")
print("  - יְדַבֵּֽרוּ has Silluq on בֵּ (penultimate) → stress on BĒ not rū")
print()
print("This is why cantillation marks are ESSENTIAL for stress detection!")
print("We can't rely on general rules - we must read the te'amim.")
