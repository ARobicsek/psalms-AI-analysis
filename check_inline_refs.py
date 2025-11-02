import sqlite3
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Get prayer 921 text
conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()
cursor.execute('SELECT hebrew_text FROM prayers WHERE prayer_id = 921')
prayer_text = cursor.fetchone()[0]
conn.close()

# Search for inline references - pattern: (תהילים ...)
# Common patterns: (תהילים XX:YY), (פסוק YY), parenthetical references
ref_pattern = r'\([^)]*תהילים[^)]*\)'
matches = re.findall(ref_pattern, prayer_text)

print(f"Found {len(matches)} inline Psalm references in prayer 921:")
for i, match in enumerate(matches[:10], 1):
    print(f"  {i}. {match}")

if len(matches) > 10:
    print(f"  ... and {len(matches)-10} more")

# Also check for verse 15 specifically
print("\n" + "="*70)
print("Searching for Psalm 81:15 area in prayer text:")
print("="*70)

# Look for key words from verse 15
search_word = "אויביהם"  # "their enemies"
if search_word in prayer_text:
    pos = prayer_text.find(search_word)
    context_start = max(0, pos - 100)
    context_end = min(len(prayer_text), pos + 100)
    context = prayer_text[context_start:context_end]

    print(f"\nFound '{search_word}' at position {pos}:")
    print(f"\n{context}\n")

    # Check for inline references in this context
    refs_in_context = re.findall(ref_pattern, context)
    if refs_in_context:
        print(f"⚠ INLINE REFERENCES IN THIS CONTEXT:")
        for ref in refs_in_context:
            print(f"  {ref}")
