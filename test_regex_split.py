"""
Test the markdown regex pattern to see why it's splitting into thousands of parts.
"""
import re
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

text = 'In the Psalter, bones are often the deepest register of a person\'s condition: "All my bones shall say, \'YHWH, who is like you?\'" (Ps 35:10);'

# The actual pattern from document_generator.py
pattern = r'(\*\*|__.*?__|\\*.*?\\*|_.*?_|`.*?`)'

print(f"Text: {text[:100]}...")
print(f"Text length: {len(text)}")
print()

parts = re.split(pattern, text)
print(f"Split into {len(parts)} parts")
print()

print("First 30 parts:")
for i, part in enumerate(parts[:30]):
    print(f"  {i}: {repr(part)}")

print("\nLet's test each pattern component separately:")
patterns = [
    (r'\*\*', 'Double asterisk'),
    (r'__.*?__', 'Double underscore'),
    (r'\\*.*?\\*', 'Backslash-asterisk'),
    (r'_.*?_', 'Single underscore'),
    (r'`.*?`', 'Backtick'),
]

for pat, name in patterns:
    matches = list(re.finditer(pat, text))
    if matches:
        print(f"\n{name} ({pat}):")
        print(f"  Found {len(matches)} matches")
        for m in matches[:5]:
            print(f"    '{m.group(0)}' at position {m.start()}")

print("\n\n=== WAIT - Let me check if there's a string escaping issue ===")
print(f"Pattern as seen by Python: {pattern}")
print(f"Pattern repr: {repr(pattern)}")
