"""Test the footnote stripping function."""

import sys
sys.path.insert(0, 'c:/Users/ariro/OneDrive/Documents/Psalms/src')

from data_sources.sefaria_client import strip_sefaria_footnotes

# Test with actual Psalm 20:4 text from Sefaria
test_text = 'May He receive the tokens<sup class="footnote-marker">a</sup><i class="footnote">Reference to azkara, "token portion" of meal offering; Lev. 2.2, 9, 16, etc.</i> of all your meal offerings,<br>and approve<sup class="footnote-marker">b</sup><i class="footnote">Meaning of Heb. uncertain.</i> your burnt offerings. <i>Selah</i>.'

print("=" * 80)
print("ORIGINAL TEXT:")
print("=" * 80)
print(test_text)
print()

print("=" * 80)
print("CLEANED TEXT (footnotes stripped):")
print("=" * 80)
cleaned = strip_sefaria_footnotes(test_text)
print(cleaned)
print()

print("=" * 80)
print("VERIFICATION:")
print("=" * 80)
print(f"Contains 'Reference to azkara': {('Reference to azkara' in cleaned)}")
print(f"Contains 'Meaning of Heb. uncertain': {('Meaning of Heb. uncertain' in cleaned)}")
print(f"Contains 'tokens': {('tokens' in cleaned)}")
print(f"Contains 'Selah': {('Selah' in cleaned)}")
print(f"Contains HTML tags: {('<' in cleaned)}")
