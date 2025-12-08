"""
Check which specific variations are being generated.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.concordance_librarian import ConcordanceLibrarian

def main():
    lib = ConcordanceLibrarian()

    print("Testing phrase: הר קדש (holy mountain)")
    print("=" * 80)

    variations = lib.generate_phrase_variations("הר קדש", level='consonantal')

    print(f"\nGenerated {len(variations)} total variations")

    # Key variations we want to find
    key_variations = [
        ('בהר קדשך', 'in your holy mountain (Psalm 15:1)'),
        ('הרי קדש', 'mountains-of holy (with suffix on first word)'),
        ('מהר קדשו', 'from his holy mountain (Psalm 3:5)'),
        ('להר קדשו', 'to his holy mountain (Psalm 99:9)'),
        ('הר קדשו', 'his holy mountain (basic)'),
        ('הרי קדשו', 'his mountains-of holiness (both words)'),
    ]

    print("\nChecking for key variations:")
    print("-" * 80)

    for var, description in key_variations:
        status = '✓' if var in variations else '✗'
        print(f"{status} {var:<20} - {description}")

    # Show sample variations with suffixes on first word
    print("\n" + "=" * 80)
    print("Variations with suffix on FIRST word only:")
    print("-" * 80)

    first_word_suffix_vars = []
    for var in variations:
        words = var.split()
        if len(words) == 2:
            # Check if first word ends with a suffix and second word is base
            if any(words[0].endswith(s) for s in ['י', 'ך', 'ו', 'ה', 'נו', 'כם', 'כן', 'הם', 'הן']):
                if words[1] in ['קדש', 'קדשו', 'קדשך', 'קדשי', 'קדשה', 'קדשנו', 'קדשכם', 'קדשהם']:
                    # Second word also has suffix, skip
                    pass
                elif 'קדש' in words[1]:
                    first_word_suffix_vars.append(var)

    for var in sorted(first_word_suffix_vars)[:20]:
        print(f"  {var}")

    if len(first_word_suffix_vars) > 20:
        print(f"  ... and {len(first_word_suffix_vars) - 20} more")

    print(f"\nTotal with suffix on first word: {len(first_word_suffix_vars)}")


if __name__ == '__main__':
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    main()
