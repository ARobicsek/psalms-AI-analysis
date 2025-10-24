"""
Test script to validate the qamets qatan and syllabification fixes.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from agents.phonetic_analyst import PhoneticAnalyst

def test_qamets_qatan_fix():
    """Test that qamets qatan is transcribed as 'o' not 'ā'"""
    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    analyst = PhoneticAnalyst()

    # Psalm 145:2 - בְּכׇל־יוֹם
    verse = "בְּכׇל־יוֹם אֲבָרְכֶךָּ וַאֲהַלְלָה שִׁמְךָ לְעוֹלָם וָעֶד׃"
    result = analyst.transcribe_verse(verse)

    print("=" * 80)
    print("QAMETS QATAN FIX TEST")
    print("=" * 80)
    print(f"\nOriginal Hebrew: {verse}")
    print("\n" + "-" * 80)

    for word_data in result['words']:
        word = word_data['word']
        syllables = word_data['syllable_transcription']
        phonemes = ''.join(word_data['phonemes'])

        print(f"\nWord: {word}")
        print(f"  Phonemes:     {phonemes}")
        print(f"  Syllabified:  {syllables}")

        # Specific checks for בְּכׇל
        if 'בְּכׇל' in word:
            print("\n  ✓ TESTING בְּכׇל:")
            if 'o' in phonemes and 'ā' not in phonemes:
                print("    ✓ PASS: Qamets Qatan correctly transcribed as 'o' (not 'ā')")
            else:
                print(f"    ✗ FAIL: Expected 'o', got phonemes: {phonemes}")

            if syllables == 'bə-khol':
                print("    ✓ PASS: Syllabification is correct (bə-khol)")
            else:
                print(f"    ✗ FAIL: Expected 'bə-khol', got: {syllables}")

    print("\n" + "=" * 80)
    print("EXPECTED OUTPUT:")
    print("=" * 80)
    print("\nVerse 2:")
    print("Hebrew: בְּכׇל־יוֹם אֲבָרְכֶךָּ וַאֲהַלְלָה שִׁמְךָ לְעוֹלָם וָעֶד׃")
    print("Phonetic: bə-khol-yōm 'a-vā-rə-khe-khā wa-'a-hal-lāh shim-khā lə-ʿō-lām wā-ʿedh")
    print("\nKey improvements:")
    print("  • בְּכׇל now correctly: bə-khol (with short 'o', not 'ā')")
    print("  • Proper syllabification: bə-khol-yōm (three syllables, not bəkh-lyōm)")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    test_qamets_qatan_fix()
