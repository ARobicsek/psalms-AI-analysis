import sqlite3
db_path = 'c:\\Users\\ariro\\OneDrive\\Documents\\Psalms\\data\\liturgy.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tables in {db_path}: {tables}")
for table_name in tables:
    table_name = table_name[0]
    print(f"\nSchema for table: {table_name}")
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
conn.close()
