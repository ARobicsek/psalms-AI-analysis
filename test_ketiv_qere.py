"""
Test ketiv-qere handling in phonetic transcription
"""
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from agents.phonetic_analyst import PhoneticAnalyst

def test_ketiv_qere():
    """Test that ketiv-qere notation is handled correctly"""
    analyst = PhoneticAnalyst()

    # Verse 6 from Psalm 145 - contains ketiv-qere
    verse = "וֶעֱז֣וּז נֽוֹרְאֹתֶ֣יךָ יֹאמֵ֑רוּ (וגדלותיך) [וּגְדֻלָּתְךָ֥] אֲסַפְּרֶֽנָּה׃"

    print("=" * 100)
    print("KETIV-QERE HANDLING TEST")
    print("=" * 100)
    print(f"\nOriginal verse:")
    print(f"  {verse}")
    print(f"\nKetiv-Qere notation:")
    print(f"  (וגדלותיך) [וּגְדֻלָּתְךָ֥]")
    print(f"  └─ (ketiv)  └─ [qere]")
    print(f"\n  • Ketiv (כְּתִיב) = 'what is written' - should be IGNORED")
    print(f"  • Qere (קְרִי) = 'what is read' - should be TRANSCRIBED")
    print("─" * 100)

    result = analyst.transcribe_verse(verse)

    print(f"\nWords transcribed:")
    ketiv_found = False
    qere_found = False

    for i, word_data in enumerate(result['words'], 1):
        word = word_data['word']
        syllables = word_data['syllable_transcription']
        phonemes = ''.join(word_data['phonemes'])

        print(f"  {i}. {word:25} → {syllables:30} (phonemes: {phonemes})")

        # Check if ketiv appears (it shouldn't)
        if 'וגדלותיך' in word or 'wghdhlwthykh' in phonemes:
            ketiv_found = True

        # Check if qere appears (it should)
        if 'וּגְדֻלָּתְךָ' in word or 'ūghədhullāthəkhā' in phonemes:
            qere_found = True

    print("\n" + "─" * 100)
    print("VERIFICATION:")
    print("─" * 100)

    if not ketiv_found:
        print("  ✓ PASS: Ketiv (וגדלותיך) was correctly IGNORED")
    else:
        print("  ✗ FAIL: Ketiv (וגדלותיך) was incorrectly transcribed")

    if qere_found:
        print("  ✓ PASS: Qere (וּגְדֻלָּתְךָ֥) was correctly TRANSCRIBED")
    else:
        print("  ✗ FAIL: Qere (וּגְדֻלָּתְךָ֥) was not transcribed")

    # Show full phonetic
    phonetic_parts = [w['syllable_transcription'] for w in result['words']]
    full_phonetic = ' '.join(phonetic_parts)

    print(f"\nFull verse phonetic:")
    print(f"  {full_phonetic}")

    print("\n" + "=" * 100)
    print("Expected: we-ʿe-zūz nō-rə-ʿō-they-khā yō-ʿmē-rū ū-ghə-dhul-lā-thə-khā ʿa-sap-ren-nāh")
    print("=" * 100)

if __name__ == '__main__':
    test_ketiv_qere()
