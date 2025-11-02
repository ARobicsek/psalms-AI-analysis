"""Extract the actual Psalm 23 text from prayer 574."""
import sys
import sqlite3

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id = 574")
prayer_text = cursor.fetchone()[0]
conn.close()

# Find "מזמור לדוד" (start of Psalm 23) and extract until next major section
start_marker = "מִזְמוֹר לְדָוִד, יְהֹוָה"
end_marker = "אִם תָּשִׁיב"  # Next section after psalm

if start_marker in prayer_text:
    start_idx = prayer_text.index(start_marker)
    end_idx = prayer_text.index(end_marker, start_idx) if end_marker in prayer_text[start_idx:] else len(prayer_text)

    psalm_excerpt = prayer_text[start_idx:end_idx].strip()

    print("Psalm 23 text in Prayer 574 (Shabbat Day Kiddush):")
    print("=" * 80)
    print(psalm_excerpt)
    print("=" * 80)
else:
    print("Could not find Psalm 23 marker in prayer")
