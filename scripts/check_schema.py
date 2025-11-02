#!/usr/bin/env python3
"""Check psalms_liturgy_index schema."""

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "data" / "liturgy.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(psalms_liturgy_index)")
columns = cursor.fetchall()

print("psalms_liturgy_index schema:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
