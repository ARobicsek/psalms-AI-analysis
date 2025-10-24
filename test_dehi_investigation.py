"""
Investigate the Dehi accent mark (֭).

According to Tiberian cantillation, Dehi (֭) is actually a SECONDARY/CONJUNCTIVE accent,
not a primary disjunctive. It may not indicate word stress in the usual sense.

The definite article הָ (ha-) is typically UNSTRESSED in Hebrew. The stress
would fall on the noun itself (אָדָם = a-DAM).

So for הָ֭אָדָם:
- The Dehi mark is on the article (הָ֭)
- But the STRESS is on the noun (אָדָם = a-DAM)
- This is a case where cantillation != stress position

We need to handle definite articles specially.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

print("DEHI ACCENT INVESTIGATION")
print("="*80)
print()
print("Word: הָ֭אָדָם (ha-adam, 'the man')")
print()
print("Structure:")
print("  הָ֭     = definite article 'ha-' (UNSTRESSED proclitic)")
print("  אָדָם  = noun 'adam' (stress on final syllable: a-DAM)")
print()
print("Cantillation vs. Stress:")
print("  Dehi (֭) is on the article → marks the WORD for cantillation")
print("  But stress is on the NOUN → final syllable (DAM)")
print()
print("Conclusion:")
print("  Hebrew definite articles (ה with vowel) are PROCLITICS")
print("  Proclitics don't carry stress - stress is on the following word")
print("  So הָאָדָם should be: hā-'ā-**DHĀM** (stress on final syllable)")
print()
print("="*80)
print("SOLUTION")
print("="*80)
print()
print("Option 1: Downgrade Dehi to level 0 (not a stress marker)")
print("  - Dehi is actually a conjunctive/secondary accent")
print("  - May not indicate lexical stress position")
print()
print("Option 2: Apply default stress rule when no PRIMARY mark found")
print("  - Default Hebrew stress: ultima (final syllable)")
print("  - Only override when primary disjunctive accent present")
print()
print("Option 3: Detect proclitic patterns")
print("  - Definite article pattern: ה + vowel at word start")
print("  - Move stress to later syllable")
print()
print("RECOMMENDATION: Option 1 + Option 2")
print("  - Remove Dehi from stress markers (it's not actually indicating stress)")
print("  - Add default ultima stress rule for words without primary marks")
