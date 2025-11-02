#!/usr/bin/env python3
"""Check prayers table schema."""

import sqlite3
from pathlib import Path

liturgy_db = Path(__file__).parent.parent / "data" / "liturgy.db"
conn = sqlite3.connect(liturgy_db)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(prayers)")
cols = cursor.fetchall()
print("prayers table columns:")
for col in cols:
    print(f"  {col[1]} ({col[2]})")

conn.close()
