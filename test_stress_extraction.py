"""
Test script to demonstrate stress extraction from cantillation marks.
This shows how the enhancement will work on Psalm 145:11.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import unicodedata

# Sample verse with cantillation marks
hebrew_verse = "כְּב֣וֹד מַלְכוּתְךָ֣ יֹאמֵ֑רוּ וּגְבוּרָתְךָ֥ יְדַבֵּֽרוּ׃"

# Cantillation marks with stress levels
CANTILLATION_STRESS = {
    # Primary stress (level 2) - major disjunctive accents
    '\u05BD': 2,  # Silluq (ֽ◌) - verse end
    '\u0591': 2,  # Atnah (֑◌) - major division
    '\u0594': 2,  # Zaqef Qaton (֔◌)
    '\u0595': 2,  # Zaqef Gadol (֕◌)
    '\u0596': 2,  # Tifcha (֖◌)
    '\u0597': 2,  # R'vi'i (֗◌)
    '\u0598': 2,  # Zarqa (֘◌)
    '\u0599': 2,  # Pashta (֙◌)
    '\u059A': 2,  # Yetiv (֚◌)
    '\u059B': 2,  # Tevir (֛◌)

    # Secondary stress (level 1) - minor accents
    '\u05A3': 1,  # Munach (֣◌)
    '\u05A4': 1,  # Mahpakh (֤◌)
    '\u05A5': 1,  # Mercha (֥◌)
}

def analyze_stress(text):
    """Analyze cantillation marks in Hebrew text."""
    print(f"Original text: {text}")
    print()

    # Normalize to NFD to separate base characters from diacritics
    normalized = unicodedata.normalize('NFD', text)

    print("Character-by-character analysis:")
    print("-" * 60)

    current_word = []
    stress_info = []

    for i, char in enumerate(normalized):
        cat = unicodedata.category(char)
        name = unicodedata.name(char, 'UNKNOWN')

        # Check if it's a cantillation mark
        stress_level = CANTILLATION_STRESS.get(char, 0)

        if cat == 'Mn':  # Combining mark
            stress_marker = ""
            if stress_level == 2:
                stress_marker = " ← PRIMARY STRESS"
            elif stress_level == 1:
                stress_marker = " ← SECONDARY STRESS"

            print(f"  {char} | {name:30s} | Category: {cat}{stress_marker}")
        elif char in ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י', 'כ', 'ך', 'ל', 'מ', 'ם', 'נ', 'ן', 'ס', 'ע', 'פ', 'ף', 'צ', 'ץ', 'ק', 'ר', 'ש', 'ת']:
            print(f"{char} | {name:30s} | Category: {cat} (Hebrew letter)")
        elif char == ' ':
            print()
            print("-" * 60)
        elif char == '׃':
            print(f"{char} | {name:30s} | Category: {cat} (Verse marker)")

    print()
    print("=" * 60)
    print("STRESS SUMMARY")
    print("=" * 60)

    # Count stress marks
    primary_count = sum(1 for c in normalized if CANTILLATION_STRESS.get(c, 0) == 2)
    secondary_count = sum(1 for c in normalized if CANTILLATION_STRESS.get(c, 0) == 1)

    print(f"Primary stress marks (level 2): {primary_count}")
    print(f"Secondary stress marks (level 1): {secondary_count}")
    print(f"Total stress marks: {primary_count + secondary_count}")

    # Show the marks found
    print()
    print("Stress marks found:")
    for char in normalized:
        if char in CANTILLATION_STRESS:
            level = CANTILLATION_STRESS[char]
            name = unicodedata.name(char)
            level_name = "PRIMARY" if level == 2 else "SECONDARY"
            print(f"  {char} ({name}) - {level_name}")

if __name__ == '__main__':
    print("STRESS EXTRACTION TEST - Psalm 145:11")
    print("=" * 60)
    print()

    analyze_stress(hebrew_verse)

    print()
    print("=" * 60)
    print("EXPECTED PHONETIC OUTPUT WITH STRESS")
    print("=" * 60)
    print()
    print("WITHOUT stress marking (current):")
    print("  kə-vōdh mal-khūth-khā yō-mē-rū ū-ghə-vū-rā-thə-khā yə-dha-bē-rū")
    print()
    print("WITH stress marking (enhanced):")
    print("  kə-**VŌDH** mal-**KHŪTH**-khā **YŌ**-mē-rū ū-**GHƏ**-vū-**RĀ**-thə-khā **YƏ**-dha-bē-rū")
    print()
    print("Stress count: [3 stresses in colon 1] + [3 stresses in colon 2] = 3+3 pattern")
    print()
    print("For commentary:")
    print('  "The verse exhibits a balanced 3+3 stress pattern. In the first colon')
    print('  (kə-**VŌDH** mal-**KHŪTH**-khā **YŌ**-mē-rū), primary stress falls on')
    print('  vōdh | khūth | yō, creating three evenly-spaced beats that convey the')
    print('  measured solemnity of royal proclamation."')
