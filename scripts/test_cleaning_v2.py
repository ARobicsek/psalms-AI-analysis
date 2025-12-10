#!/usr/bin/env python3
"""Test improved cleaning function."""
import re

def clean_english_text_v2(text: str) -> str:
    """More precise version that preserves valid text."""
    if not text:
        return text

    # Fix the specific "*When God began to create*When God began to create Others" pattern
    # This seems to be a duplication issue where the asterisked part duplicates the text
    text = re.sub(r'\*([^*]+)\* \1', r'\1', text)

    # Remove the asterisked duplicate but keep the original text
    text = re.sub(r'\*[^*]+\*', '', text)

    # Remove footnotes more precisely
    # Pattern: Heb. 'text'. Cf. text.
    text = re.sub(r'\s+Heb\.\s*\'[^\']*\'(?:\.|\s+)(?:Cf\.\s*[^\.,]+\.?)?', '', text)

    # Pattern: Heb. text. Cf. text.
    text = re.sub(r'\s+Heb\.\s+[^.,;:]+\.\s*(?:Cf\.\s*[^.,;:]+\.?)?', '', text)

    # Pattern: *text* (asterisked notes)
    text = re.sub(r'\s*\*[^*]+\*\s*', ' ', text)

    # Pattern: Single asterisks
    text = re.sub(r'\*+', '', text)

    # Pattern: "Others 'text'"
    text = re.sub(r'\s+Others\s*\'[^\']*\'\s*', '', text)

    # Pattern: Cf. text.
    text = re.sub(r'\s+Cf\.\s+[^.,;:]+\.?', '', text)

    # Pattern: Emendation text
    text = re.sub(r'\s+Emendation[^.,;:]*\.?', '', text)

    # Pattern: (Heb: text)
    text = re.sub(r'\s*\([^)]*Heb[^)]*\)', '', text)

    # Pattern: "Moved up from v. X for clarity"
    text = re.sub(r'\s+[^.,]*\s+Moved up from v\.\s+\d+\s+for clarity', '', text)

    # Pattern: Lit. 'text'.
    text = re.sub(r'\s+Lit\.\s*\'[^\']*\'\.?', '', text)

    # Fix specific spacing issues
    text = re.sub(r'(\w)([A-Z][a-z])', r'\1 \2', text)  # wordWord -> word Word
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces
    text = re.sub(r'\s*([.,])', r'\1', text)  # Space before punctuation
    text = re.sub(r'([.,])(\w)', r'\1 \2', text)  # Ensure space after punctuation

    return text.strip()

# Test with the provided example
test_text = '''By the sweat of your browShall you get bread to eat,Until you return to the ground—For from it you were taken.For dust*dust Heb. 'afar. Cf. the second note at 2.7. you are,And to dust you shall return." The Human named his wife Eve,*Eve Heb. hawwah. because she was the mother of all the living.*living Heb. hai. And God LORD made garments of skins for Adam and his wife, and clothed them. And God LORD said, "Now that humankind has become like any of us, knowing good and bad, what if one should stretch out a hand and take also from the tree of life and eat, and live forever!" So God LORD banished humankind*humankind Moved up from v. 24 for clarity. from the garden of Eden, to till the humus*humus Lit. "soil." See the second note at 2.7. from which it was taken:'''

print("=== TEST CLEANING ===\n")
print("Length of original:", len(test_text))
print("Length after cleaning:", len(clean_english_text_v2(test_text)))

# Write result to file for checking
with open('test_cleaning_output.txt', 'w', encoding='utf-8') as f:
    f.write("ORIGINAL TEXT:\n")
    f.write(test_text[:1000] + "...\n\n")
    f.write("CLEANED TEXT:\n")
    f.write(clean_english_text_v2(test_text))

print("\nResult written to test_cleaning_output.txt")