import sqlite3

db_path = "data/liturgy.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='psalms_liturgy_index';")
table_exists = cursor.fetchone()

if table_exists:
    print("Schema for psalms_liturgy_index:")
    cursor.execute("PRAGMA table_info(psalms_liturgy_index);")
    schema = cursor.fetchall()
    for column in schema:
        print(column)
else:
    print("Table 'psalms_liturgy_index' not found.")

conn.close()
