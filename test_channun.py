"""
Test the specific word חַנּוּן to debug the gemination and syllabification
"""
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from agents.phonetic_analyst import PhoneticAnalyst
import unicodedata

def test_channun():
    analyst = PhoneticAnalyst()

    word = "חַנּוּן"

    print("=" * 80)
    print(f"Testing word: {word}")
    print("=" * 80)

    # Show normalized form and characters
    normalized = unicodedata.normalize('NFD', word)
    print(f"\nCharacters breakdown:")
    for i, char in enumerate(normalized):
        print(f"  {i}: U+{ord(char):04X} - {unicodedata.name(char, 'UNNAMED')} - '{char}'")

    result = analyst._transcribe_word(word)

    print(f"\nTranscription results:")
    print(f"  Phonemes: {result['phonemes']}")
    print(f"  Joined: {''.join(result['phonemes'])}")
    print(f"  Syllables: {result['syllables']}")
    print(f"  Syllabified: {result['syllable_transcription']}")

    print(f"\nExpected:")
    print(f"  Should be: khan-nūn")
    print(f"  Reasoning:")
    print(f"    - ח (khet) + ַ (patah) = 'kha'")
    print(f"    - נּ (nun + dagesh forte) = geminated 'n'")
    print(f"    - First 'n' closes syllable: khan")
    print(f"    - Second 'n' starts new syllable: nūn")
    print(f"    - וּ (vav + dagesh = shureq) = 'ū'")
    print(f"    - ן (final nun) = 'n'")

if __name__ == '__main__':
    test_channun()
