"""
Quick test to verify the grapheme cluster transformation works correctly.
"""
import re
import sys
from src.utils.document_generator import DocumentGenerator

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Test text from the actual document
test_text = '"And my נֶפֶשׁ is deeply terrified" (וְנַפְשִׁי נִבְהֲלָה מְאֹד). נֶפֶשׁ is not a detachable soul'

print("Original text:")
print(test_text)
print()

# Test the grapheme cluster splitting
hebrew = "וְנַפְשִׁי נִבְהֲלָה מְאֹד"
print(f"Hebrew text: {hebrew}")
print()

clusters = DocumentGenerator._split_into_grapheme_clusters(hebrew)
print(f"Split into {len(clusters)} clusters:")
for i, cluster in enumerate(clusters):
    print(f"  {i}: '{cluster}'")
print()

reversed_hebrew = DocumentGenerator._reverse_hebrew_by_clusters(hebrew)
print(f"Reversed: {reversed_hebrew}")
print()

# Test the full transformation
LRO = '\u202D'
PDF = '\u202C'

def transform_test(text):
    hebrew_paren_pattern = r'\(([\u0590-\u05FF\u05B0-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C7\s]+)\)'

    def reverse_hebrew_match(match):
        hebrew_text = match.group(1)
        reversed_hebrew = DocumentGenerator._reverse_hebrew_by_clusters(hebrew_text)
        return f'{LRO}({reversed_hebrew}){PDF}'

    return re.sub(hebrew_paren_pattern, reverse_hebrew_match, text)

transformed = transform_test(test_text)
print("Transformed text:")
print(transformed)
print()

# Show the transformation in detail
pattern = r'\(([\u0590-\u05FF\u05B0-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C7\s]+)\)'
matches = list(re.finditer(pattern, test_text))
print(f"Found {len(matches)} parenthesized Hebrew instances:")
for i, match in enumerate(matches):
    print(f"  Match {i}: '{match.group(0)}'")
    print(f"    Hebrew inside: '{match.group(1)}'")
    reversed = DocumentGenerator._reverse_hebrew_by_clusters(match.group(1))
    print(f"    Reversed: '{reversed}'")
