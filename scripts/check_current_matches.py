#!/usr/bin/env python3
"""Check current state of Psalm 19 and 23 matches in database."""

import sqlite3
from pathlib import Path

def check_matches():
    db_path = Path(__file__).parent.parent / "data" / "liturgy.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for psalm_num in [19, 23]:
        print(f"\n{'='*80}")
        print(f"PSALM {psalm_num} MATCHES")
        print('='*80)

        cursor.execute("""
            SELECT psalm_chapter, psalm_verse_start, psalm_verse_end, prayer_id,
                   match_type, confidence, psalm_phrase_hebrew
            FROM psalms_liturgy_index
            WHERE psalm_chapter = ?
            ORDER BY prayer_id, psalm_verse_start
        """, (psalm_num,))

        matches = cursor.fetchall()

        if not matches:
            print(f"NO MATCHES FOUND for Psalm {psalm_num}")
            continue

        # Group by prayer
        by_prayer = {}
        for row in matches:
            psalm_ch, v_start, v_end, prayer_id, match_type, conf, phrase = row
            if prayer_id not in by_prayer:
                by_prayer[prayer_id] = []
            verse_range = f"{v_start}" if v_start == v_end else f"{v_start}-{v_end}"
            by_prayer[prayer_id].append({
                'verse_start': v_start,
                'verse_end': v_end,
                'verse_range': verse_range,
                'type': match_type,
                'confidence': conf,
                'phrase': phrase
            })

        for prayer_id, prayer_matches in sorted(by_prayer.items()):
            print(f"\nPrayer {prayer_id}: {len(prayer_matches)} matches")
            for m in prayer_matches:
                phrase_preview = m['phrase'][:60] if m['phrase'] else ''
                # Handle encoding for console
                try:
                    print(f"  - Verse {m['verse_range']:5s}: {m['type']:20s} (conf={m['confidence']:.2f}) | {phrase_preview}")
                except UnicodeEncodeError:
                    print(f"  - Verse {m['verse_range']:5s}: {m['type']:20s} (conf={m['confidence']:.2f}) | [Hebrew text]")

        # Check for entire_chapter matches
        cursor.execute("""
            SELECT COUNT(*) FROM psalms_liturgy_index
            WHERE psalm_chapter = ? AND match_type = 'entire_chapter'
        """, (psalm_num,))
        chapter_count = cursor.fetchone()[0]
        print(f"\n>>> Entire chapter matches: {chapter_count}")

    conn.close()

if __name__ == '__main__':
    check_matches()
