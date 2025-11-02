import sys
import sqlite3

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

print("Checking liturgy_context field lengths for Psalm 1:\n")

cursor.execute('''
    SELECT index_id, psalm_phrase_hebrew, length(liturgy_context) as context_len,
           substr(liturgy_context, 1, 200) as context_start
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 1
    LIMIT 5
''')

for row in cursor.fetchall():
    index_id, phrase, length, context = row
    print(f"Index ID: {index_id}")
    print(f"Phrase: {phrase}")
    print(f"Context Length: {length} characters")
    print(f"Context Start: {context}")
    print(f"Expected: ~400 chars (200 before + 200 after)")
    print("-" * 70)
    print()

# Get statistics
cursor.execute('''
    SELECT
        COUNT(*) as total_matches,
        AVG(length(liturgy_context)) as avg_length,
        MIN(length(liturgy_context)) as min_length,
        MAX(length(liturgy_context)) as max_length
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 1
''')

stats = cursor.fetchone()
print(f"\nStatistics for Psalm 1:")
print(f"Total matches: {stats[0]}")
print(f"Average context length: {stats[1]:.0f} chars")
print(f"Min context length: {stats[2]} chars")
print(f"Max context length: {stats[3]} chars")

conn.close()
