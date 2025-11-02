import sqlite3
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def normalize(text):
    nikud_pattern = r'[\u0591-\u05C7]'
    text = re.sub(nikud_pattern, '', text)
    text = re.sub(r'[^\u05D0-\u05EA\s]', '', text)
    return ' '.join(text.split())

# Get verse 15
conn_tanakh = sqlite3.connect('database/tanakh.db')
cursor = conn_tanakh.cursor()
cursor.execute('''
    SELECT hebrew FROM verses
    WHERE book_name = 'Psalms' AND chapter = 81 AND verse = 15
''')
verse15 = cursor.fetchone()[0]
conn_tanakh.close()

norm_verse15 = normalize(verse15)
words = norm_verse15.split()

print(f"Psalm 81:15 normalized: {norm_verse15}")
print(f"Words: {words}\n")

# Get prayer
conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()
cursor.execute('SELECT hebrew_text FROM prayers WHERE prayer_id = 921')
prayer_text = cursor.fetchone()[0]
conn.close()

norm_prayer = normalize(prayer_text)

# Find where each part appears
print("Finding each part in prayer:\n")

part1 = ' '.join(words[:4])  # כמעט אויביהם אכניע ועל
part2 = ' '.join(words[4:])  # צריהם אשיב ידי

print(f"Part 1: '{part1}'")
if part1 in norm_prayer:
    pos1 = norm_prayer.find(part1)
    print(f"  ✓ FOUND at position {pos1}")
    print(f"  Context: ...{norm_prayer[max(0,pos1-30):pos1+len(part1)+30]}...")
else:
    print(f"  ✗ NOT FOUND")

print(f"\nPart 2: '{part2}'")
if part2 in norm_prayer:
    pos2 = norm_prayer.find(part2)
    print(f"  ✓ FOUND at position {pos2}")
    print(f"  Context: ...{norm_prayer[max(0,pos2-30):pos2+len(part2)+30]}...")
else:
    print(f"  ✗ NOT FOUND")

if part1 in norm_prayer and part2 in norm_prayer:
    pos1 = norm_prayer.find(part1)
    pos2 = norm_prayer.find(part2)
    gap_start = pos1 + len(part1)
    gap_end = pos2

    print(f"\n{'='*70}")
    print(f"FOUND SPLIT! Part 1 ends at {gap_start}, Part 2 starts at {gap_end}")
    print(f"Gap size: {gap_end - gap_start} characters")
    print(f"\nText in gap:")
    print(f"'{norm_prayer[gap_start:gap_end]}'")
    print(f"\nOriginal prayer text in gap (unnormalized):")

    # Find this location in original prayer
    # This is tricky - need to map normalized positions back to original
    # For now, just search for the parts in original
    if part1 in normalize(prayer_text[:len(prayer_text)//2]):
        # Try to find in first half
        for i in range(len(prayer_text) - 100):
            snippet = prayer_text[i:i+100]
            if part1 in normalize(snippet) and part2 in normalize(snippet):
                print(f"\n{snippet}")
                break
