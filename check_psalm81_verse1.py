import sqlite3
import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Get Psalm 81 verse 1 from Tanakh
conn_tanakh = sqlite3.connect('database/tanakh.db')
cursor_tanakh = conn_tanakh.cursor()
cursor_tanakh.execute('''
    SELECT hebrew FROM verses
    WHERE book_name = 'Psalms' AND chapter = 81 AND verse = 1
''')
verse1_hebrew = cursor_tanakh.fetchone()[0]
print(f'Psalm 81:1 text:\n{verse1_hebrew}\n')
conn_tanakh.close()

# Get prayer 921 text
conn_liturgy = sqlite3.connect('data/liturgy.db')
cursor_liturgy = conn_liturgy.cursor()
cursor_liturgy.execute('SELECT hebrew_text FROM prayers WHERE prayer_id = 921')
prayer_text = cursor_liturgy.fetchone()[0]
conn_liturgy.close()

# Check if verse 1 appears in the prayer
if verse1_hebrew in prayer_text:
    print('✓ Verse 1 FOUND in prayer text')
    # Find its position
    pos = prayer_text.find(verse1_hebrew)
    print(f'  Position: {pos}')
    print(f'  Context: ...{prayer_text[max(0,pos-50):pos+len(verse1_hebrew)+50]}...')
else:
    print('✗ Verse 1 NOT FOUND in prayer text')

    # Check for partial matches
    words = verse1_hebrew.split()
    print(f'\nChecking for partial matches (verse has {len(words)} words):')
    for i in range(len(words)):
        for j in range(i+1, len(words)+1):
            substring = ' '.join(words[i:j])
            if len(substring) > 10 and substring in prayer_text:
                print(f'  Found substring ({j-i} words): {substring[:50]}...')
                break

# Also check: are ALL of verses 2-17 actually present?
print('\n' + '='*70)
print('Checking verses 2-17:')

conn_tanakh = sqlite3.connect('database/tanakh.db')
cursor_tanakh = conn_tanakh.cursor()

for verse_num in range(2, 18):
    cursor_tanakh.execute('''
        SELECT hebrew FROM verses
        WHERE book_name = 'Psalms' AND chapter = 81 AND verse = ?
    ''', (verse_num,))
    verse_text = cursor_tanakh.fetchone()[0]

    # Normalize for matching (remove nikud, etc)
    import re
    def normalize(text):
        # Remove nikud (vowel points)
        nikud_pattern = r'[\u0591-\u05C7]'
        text = re.sub(nikud_pattern, '', text)
        # Remove other marks
        text = re.sub(r'[^\u05D0-\u05EA\s]', '', text)
        return ' '.join(text.split())

    norm_verse = normalize(verse_text)
    norm_prayer = normalize(prayer_text)

    if norm_verse in norm_prayer:
        print(f'  ✓ Verse {verse_num:2d} found')
    else:
        print(f'  ✗ Verse {verse_num:2d} NOT FOUND')
        print(f'      Text: {verse_text[:60]}...')

conn_tanakh.close()
