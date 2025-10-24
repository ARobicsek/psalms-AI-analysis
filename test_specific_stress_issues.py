"""
Test specific stress detection issues identified by user.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'c:/Users/ariro/OneDrive/Documents/Psalms/src')

from agents.phonetic_analyst import PhoneticAnalyst
import unicodedata

def analyze_word_detailed(analyst, hebrew_word, verse_context=""):
    """Detailed character-by-character analysis of a word."""
    print(f"\n{'='*80}")
    print(f"DETAILED ANALYSIS: {hebrew_word}")
    if verse_context:
        print(f"Context: {verse_context}")
    print(f"{'='*80}")

    # Normalize to see combining characters
    normalized = unicodedata.normalize('NFD', hebrew_word)

    print("\nCharacter-by-character breakdown:")
    for i, char in enumerate(normalized):
        cat = unicodedata.category(char)
        name = unicodedata.name(char, 'UNKNOWN')

        # Check if cantillation
        is_cantillation = char in analyst.cantillation_stress
        cantillation_info = ""
        if is_cantillation:
            level = analyst.cantillation_stress[char]
            level_name = "PRIMARY" if level == 2 else "SECONDARY"
            cantillation_info = f" ← {level_name} STRESS MARKER"

        print(f"  [{i:2d}] {char:3s} | {name:35s} | Cat: {cat:2s}{cantillation_info}")

    # Transcribe
    result = analyst._transcribe_word(hebrew_word)

    print(f"\nTranscription results:")
    print(f"  Regular:  {result.get('syllable_transcription', '')}")
    print(f"  Stressed: {result.get('syllable_transcription_stressed', '')}")
    print(f"  Stress level: {result.get('stress_level', 0)} (0=none, 1=secondary, 2=primary)")
    print(f"  Stressed syllable index: {result.get('stressed_syllable_index', 'None')}")
    print(f"  Syllables: {result.get('syllables', [])}")

    return result

# Test cases
analyst = PhoneticAnalyst()

print("ISSUE INVESTIGATION")
print("="*80)
print()

# Issue 1: הָ֭אָדָם - should have stress on DHAM
print("ISSUE 1: Should hā-'ā-dhām have stress on DHĀM?")
print("-"*80)
analyze_word_detailed(analyst, "הָ֭אָדָם", "Verse 12")

# Issue 2: וּ֝מֶֽמְשַׁלְתְּךָ֗ - should be MEM-shal-tə-KHA not MEM-shal-tkhā
print("\n" + "="*80)
print("ISSUE 2: Should וּ֝מֶֽמְשַׁלְתְּךָ֗ be MEM-shal-tə-KHĀ?")
print("-"*80)
analyze_word_detailed(analyst, "וּ֝מֶֽמְשַׁלְתְּךָ֗", "Verse 13")

# Issue 3: מַלְכוּתְךָ֣ - should be mal-khū-thə-KHĀ
print("\n" + "="*80)
print("ISSUE 3: Should מַלְכוּתְךָ֣ be mal-khū-thə-KHĀ?")
print("-"*80)
analyze_word_detailed(analyst, "מַלְכוּתְךָ֣", "Verse 11")

# Additional analysis: Let's check a few more instances
print("\n" + "="*80)
print("ADDITIONAL: Testing similar word patterns")
print("-"*80)

# Compare different instances of מַלְכוּת
print("\nComparing different forms of מַלְכוּת:")
test_words = [
    ("כְּב֣וֹד", "Verse 11 - glory"),
    ("מַלְכוּתְךָ֣", "Verse 11 - your kingdom"),
    ("גְּבוּרָתְךָ֥", "Verse 11 - your might"),
]

for word, context in test_words:
    result = analyst._transcribe_word(word)
    print(f"\n  {word:20s} ({context})")
    print(f"    Stressed: {result.get('syllable_transcription_stressed', '')}")

print("\n" + "="*80)
print("DIAGNOSIS SUMMARY")
print("="*80)
print("""
Expected vs. Actual:

1. הָ֭אָדָם (ha-adam)
   Expected: Should detect stress mark (֭ = ?) on אָ → stress on DĀM
   Actual: Need to check if ֭ is in our cantillation map

2. וּ֝מֶֽמְשַׁלְתְּךָ֗ (u-memshaltekha)
   Expected: MEM-shal-tə-KHĀ (schwa ְ should be transcribed)
   Actual: Need to verify schwa handling + stress on final KHĀ

3. מַלְכוּתְךָ֣ (malkhutekha)
   Expected: mal-khū-thə-KHĀ (schwa ְ before final khā)
   Actual: Need to verify schwa transcription

Key question: Are schwas being transcribed correctly in syllabification?
""")
