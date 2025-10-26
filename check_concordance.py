import sqlite3

conn = sqlite3.connect('database/tanakh.db')
cursor = conn.cursor()

cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
print('Tables:', [row[0] for row in cursor.fetchall()])

cursor.execute('PRAGMA table_info(concordance)')
print('\nConcordance schema:')
for row in cursor.fetchall():
    print(f'  {row}')

cursor.execute('SELECT COUNT(*) FROM concordance')
print(f'\nConcordance entries: {cursor.fetchone()[0]:,}')

# Check if we have normalized text
cursor.execute('SELECT * FROM concordance LIMIT 3')
print('\nSample entries:')
for row in cursor.fetchall():
    print(f'  {row}')

conn.close()
