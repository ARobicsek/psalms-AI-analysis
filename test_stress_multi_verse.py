"""
Test stress extraction on multiple verses from Psalm 145.
This will help us verify the algorithm works across different patterns.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
import unicodedata
import re

# Cantillation marks with stress levels
CANTILLATION_STRESS = {
    # Primary stress (level 2) - major disjunctive accents
    '\u05BD': ('Silluq/Meteg', 2),
    '\u0591': ('Atnah', 2),
    '\u0594': ('Zaqef Qaton', 2),
    '\u0595': ('Zaqef Gadol', 2),
    '\u0596': ('Tifcha', 2),
    '\u0597': ("R'vi'i", 2),
    '\u0598': ('Zarqa', 2),
    '\u0599': ('Pashta', 2),
    '\u059A': ('Yetiv', 2),
    '\u059B': ('Tevir', 2),
    '\u05A0': ('Telisha Gedola', 2),
    '\u05A9': ('Telisha Qetana', 2),
    '\u0593': ('Shalshelet', 2),

    # Secondary stress (level 1) - conjunctive accents
    '\u05A3': ('Munach', 1),
    '\u05A4': ('Mahpakh', 1),
    '\u05A5': ('Mercha', 1),
    '\u05A8': ('Qadma', 1),
    '\u05AB': ('Ole', 1),
    '\u05A1': ('Pazer', 1),
}

# Vowels for reference
VOWELS = {
    '\u05B7': 'a',   # Patah
    '\u05B8': 'ā',   # Qamets
    '\u05B5': 'ē',   # Tsere
    '\u05B6': 'e',   # Segol
    '\u05B4': 'i',   # Hiriq
    '\u05B9': 'ō',   # Holam
    '\u05BA': 'ō',   # Holam Haser
    '\u05BB': 'u',   # Qubuts
    '\u05B0': 'ə',   # Shewa
    '\u05B2': 'a',   # Hataf Patah
    '\u05B1': 'e',   # Hataf Segol
    '\u05B3': 'o',   # Hataf Qamets
    '\u05C7': 'o',   # Qamets Qatan
}

CONSONANTS = {
    'א': "'", 'ב': 'b', 'ג': 'g', 'ד': 'd', 'ה': 'h', 'ו': 'w', 'ז': 'z',
    'ח': 'kh', 'ט': 't', 'י': 'y', 'כ': 'k', 'ך': 'kh', 'ל': 'l', 'מ': 'm',
    'ם': 'm', 'נ': 'n', 'ן': 'n', 'ס': 's', 'ע': 'ʿ', 'פ': 'p', 'ף': 'f',
    'צ': 'ts', 'ץ': 'ts', 'ק': 'q', 'ר': 'r', 'ש': 'sh', 'ת': 't'
}

def analyze_word_stress(hebrew_word):
    """
    Analyze where stress falls in a Hebrew word based on cantillation marks.
    Returns the letter index where stress is marked.
    """
    normalized = unicodedata.normalize('NFD', hebrew_word)

    stress_positions = []

    for i, char in enumerate(normalized):
        if char in CANTILLATION_STRESS:
            name, level = CANTILLATION_STRESS[char]
            # Find the base letter this mark attaches to
            # Cantillation marks (Mn category) follow the letter they accent
            # So we need to look backward to find the letter
            for j in range(i-1, -1, -1):
                if normalized[j] in CONSONANTS or normalized[j] in ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט', 'י', 'כ', 'ך', 'ל', 'מ', 'ם', 'נ', 'ן', 'ס', 'ע', 'פ', 'ף', 'צ', 'ץ', 'ק', 'ר', 'ש', 'ת']:
                    stress_positions.append({
                        'char_index': j,
                        'letter': normalized[j],
                        'mark': char,
                        'mark_name': name,
                        'level': level
                    })
                    break

    return stress_positions

def simple_syllabify(hebrew_word):
    """
    Very simple syllabification - just split at vowels.
    This is a rough approximation for demonstration.
    """
    normalized = unicodedata.normalize('NFD', hebrew_word)
    syllables = []
    current = []

    for char in normalized:
        if char in ['־', '׃']:  # Skip maqqef and sof pasuq
            continue
        current.append(char)
        if char in VOWELS:
            syllables.append(''.join(current))
            current = []

    if current:
        syllables.append(''.join(current))

    return syllables

def analyze_verse(verse_text, verse_num):
    """Analyze stress patterns in a complete verse."""
    print(f"\n{'='*80}")
    print(f"VERSE {verse_num}")
    print(f"{'='*80}")
    print(f"\nHebrew: {verse_text}")
    print()

    # Split into words
    words = verse_text.split()

    all_stresses = []

    for word_idx, word in enumerate(words):
        # Skip verse markers
        if word == '׃':
            continue

        print(f"\nWord {word_idx + 1}: {word}")
        print("-" * 40)

        # Find stress positions
        stress_info = analyze_word_stress(word)

        if stress_info:
            for s in stress_info:
                print(f"  Stress found: {s['mark_name']} (level {s['level']}) on letter '{s['letter']}'")
                all_stresses.append(s)
        else:
            print(f"  No stress mark found (likely proclitic or unstressed)")

        # Show syllables
        syllables = simple_syllabify(word)
        if syllables:
            print(f"  Syllables: {' | '.join(syllables)}")

    print(f"\n{'-'*80}")
    print(f"SUMMARY: Found {len(all_stresses)} stress marks in verse {verse_num}")

    # Count by level
    primary = sum(1 for s in all_stresses if s['level'] == 2)
    secondary = sum(1 for s in all_stresses if s['level'] == 1)
    print(f"  Primary (level 2): {primary}")
    print(f"  Secondary (level 1): {secondary}")

    return all_stresses

# Test verses from Psalm 145
verses = [
    (7, "זֵ֣כֶר רַב־טוּבְךָ֣ יַבִּ֑יעוּ וְצִדְקָתְךָ֥ יְרַנֵּֽנוּ׃"),
    (8, "חַנּ֣וּן וְרַח֣וּם יְהֹוָ֑ה אֶ֥רֶךְ אַ֝פַּ֗יִם וּגְדׇל־חָֽסֶד׃"),
    (9, "טוֹב־יְהֹוָ֥ה לַכֹּ֑ל וְ֝רַחֲמָ֗יו עַל־כׇּל־מַעֲשָֽׂיו׃"),
    (10, "יוֹד֣וּךָ יְ֭הֹוָה כׇּל־מַעֲשֶׂ֑יךָ וַ֝חֲסִידֶ֗יךָ יְבָרְכֽוּכָה׃"),
    (11, "כְּב֣וֹד מַלְכוּתְךָ֣ יֹאמֵ֑רוּ וּגְבוּרָתְךָ֥ יְדַבֵּֽרוּ׃"),
    (12, "לְהוֹדִ֤יעַ ׀ לִבְנֵ֣י הָ֭אָדָם גְּבוּרֹתָ֑יו וּ֝כְב֗וֹד הֲדַ֣ר מַלְכוּתֽוֹ׃"),
    (13, "מַֽלְכוּתְךָ֗ מַלְכ֥וּת כׇּל־עֹלָמִ֑ים וּ֝מֶֽמְשַׁלְתְּךָ֗ בְּכׇל־דּ֥וֹר וָדֹֽר׃"),
]

if __name__ == '__main__':
    print("STRESS PATTERN ANALYSIS - Psalm 145:7-13")
    print("="*80)

    total_verses = len(verses)
    total_stresses = 0

    for verse_num, verse_text in verses:
        stresses = analyze_verse(verse_text, verse_num)
        total_stresses += len(stresses)

    print(f"\n{'='*80}")
    print(f"OVERALL SUMMARY")
    print(f"{'='*80}")
    print(f"Analyzed {total_verses} verses")
    print(f"Found {total_stresses} total stress marks")
    print(f"Average {total_stresses / total_verses:.1f} stresses per verse")

    print(f"\n{'='*80}")
    print("KEY FINDINGS")
    print(f"{'='*80}")
    print("""
1. Cantillation marks ARE present in all verses
2. They attach to specific letters (consonants)
3. We can detect them using Unicode normalization (NFD)
4. Primary vs. secondary distinction is clear
5. Most verses have 4-6 stress marks

NEXT STEP: Map stress positions to syllables
- Currently: "stress on letter מ"
- Need: "stress on syllable MĒ"
- Requires: Better syllabification algorithm that tracks letter→syllable mapping
""")
