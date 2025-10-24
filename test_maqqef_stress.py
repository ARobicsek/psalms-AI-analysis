"""
Investigate stress detection on words with maqqef (־).
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'c:/Users/ariro/OneDrive/Documents/Psalms/src')

from agents.phonetic_analyst import PhoneticAnalyst
import unicodedata

def analyze_maqqef_word(analyst, hebrew_word, context=""):
    """Detailed analysis of maqqef compound."""
    print(f"\n{'='*80}")
    print(f"MAQQEF COMPOUND: {hebrew_word}")
    if context:
        print(f"Context: {context}")
    print(f"{'='*80}")

    # Show individual components
    parts = hebrew_word.split('־')
    print(f"\nComponents (split by maqqef ־):")
    for i, part in enumerate(parts, 1):
        print(f"  {i}. {part}")

    # Show character breakdown
    normalized = unicodedata.normalize('NFD', hebrew_word)
    print(f"\nCharacter breakdown:")
    for i, char in enumerate(normalized):
        cat = unicodedata.category(char)
        name = unicodedata.name(char, 'UNKNOWN')

        is_cantillation = char in analyst.cantillation_stress
        cantillation_info = ""
        if is_cantillation:
            level = analyst.cantillation_stress[char]
            level_name = "PRIMARY" if level == 2 else "SECONDARY"
            cantillation_info = f" ← {level_name} STRESS"

        if char == '־':
            print(f"  [{i:2d}] {char:3s} | MAQQEF (word connector)")
        elif cat in ['Lo', 'Mn']:
            print(f"  [{i:2d}] {char:3s} | {name:35s}{cantillation_info}")

    # Transcribe
    result = analyst._transcribe_word(hebrew_word)

    print(f"\nTranscription result:")
    print(f"  Regular:  {result.get('syllable_transcription', '')}")
    print(f"  Stressed: {result.get('syllable_transcription_stressed', '')}")
    print(f"  Stress level: {result.get('stress_level', 0)}")
    print(f"  Stressed syllable index: {result.get('stressed_syllable_index', 'None')}")

    return result

analyst = PhoneticAnalyst()

print("MAQQEF STRESS INVESTIGATION")
print("="*80)

# Issue 1: לְכׇל־הַנֹּפְלִ֑ים
analyze_maqqef_word(analyst, "לְכׇל־הַנֹּפְלִ֑ים", "Verse 14 - 'to all the fallen'")

# Issue 2: בְּכׇל־דְּרָכָ֑יו
analyze_maqqef_word(analyst, "בְּכׇל־דְּרָכָ֑יו", "Verse 17 - 'in all His ways'")

# Issue 3: בְּכׇל־מַעֲשָֽׂיו
analyze_maqqef_word(analyst, "בְּכׇל־מַעֲשָֽׂיו", "Verse 17 - 'in all His works'")

print("\n" + "="*80)
print("DIAGNOSIS")
print("="*80)
print("""
The issue: Maqqef (־) connects two words, but stress detection is treating
the entire compound as ONE word, so it's only detecting ONE stress mark
(the one on the second component).

Expected behavior:
- לְכׇל־הַנֹּפְלִ֑ים should have stress on כֹל (KHOL) in first component
- בְּכׇל־דְּרָכָ֑יו should have stress on כֹל (KHOL) in first component
- בְּכׇל־מַעֲשָֽׂיו should have stress on כֹל (KHOL) in first component

Current behavior:
- Only detecting stress on the SECOND component (where Atnah/Silluq is)
- Missing stress on the FIRST component (כֹל)

The word כֹל (kol, "all") typically has its own stress, even when connected
by maqqef. We need to either:
1. Split maqqef compounds and transcribe each part separately
2. Detect multiple stress positions within a maqqef compound
3. Apply default stress rules to both components

RECOMMENDATION: Option 1 - Split maqqef compounds at the word level
""")
