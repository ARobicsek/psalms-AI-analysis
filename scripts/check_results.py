#!/usr/bin/env python3
"""Check final results."""

import sqlite3
from pathlib import Path

liturgy_db = Path(__file__).parent.parent / "data" / "liturgy.db"
conn = sqlite3.connect(liturgy_db)
cursor = conn.cursor()

print("="*70)
print("PSALM 19 IN PRAYER 251")
print("="*70)
cursor.execute("""
    SELECT psalm_verse_start, psalm_verse_end, match_type, confidence
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 19 AND prayer_id = 251
    ORDER BY match_type DESC, psalm_verse_start
""")
for row in cursor.fetchall():
    v_start, v_end, match_type, conf = row
    verse_range = f"{v_start}" if v_start == v_end else f"{v_start}-{v_end}"
    print(f"  Verses {verse_range:5s}: {match_type:20s} (conf={conf:.2f})")

print("\n" + "="*70)
print("PSALM 23 IN PRAYER 574")
print("="*70)
cursor.execute("""
    SELECT psalm_verse_start, psalm_verse_end, match_type, confidence
    FROM psalms_liturgy_index
    WHERE psalm_chapter = 23 AND prayer_id = 574
    ORDER BY match_type DESC, psalm_verse_start
""")
for row in cursor.fetchall():
    v_start, v_end, match_type, conf = row
    verse_range = f"{v_start}" if v_start == v_end else f"{v_start}-{v_end}"
    print(f"  Verses {verse_range:5s}: {match_type:20s} (conf={conf:.2f})")

conn.close()
