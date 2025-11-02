"""
Check if the multiple Psalm 1 matches in prayer 626 are duplicates or legitimate.
"""
import sqlite3
import sys
sys.path.append('.')

from src.liturgy.liturgy_indexer import LiturgyIndexer

# Initialize indexer
indexer = LiturgyIndexer(verbose=False)

# Connect to database
conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

# Get all Psalm 1 matches in prayer 626
cursor.execute("""
    SELECT
        index_id,
        psalm_verse_start,
        psalm_phrase_hebrew,
        psalm_phrase_normalized,
        phrase_length,
        liturgy_context
    FROM psalms_liturgy_index
    WHERE psalm_chapter=1 AND prayer_id=626
    ORDER BY psalm_verse_start, phrase_length DESC
""")

matches = cursor.fetchall()

# Get the prayer text
cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id=626")
prayer_text = cursor.fetchone()[0]
normalized_prayer = indexer._full_normalize(prayer_text)

conn.close()

with open('output/psalm1_duplicates_analysis.txt', 'w', encoding='utf-8') as f:
    f.write("=== Analysis: Psalm 1 Matches in Prayer 626 ===\n\n")
    f.write(f"Total matches: {len(matches)}\n\n")

    for idx, verse, phrase_heb, phrase_norm, phrase_len, context in matches:
        f.write(f"\n{'='*80}\n")
        f.write(f"Match ID: {idx}\n")
        f.write(f"Verse: 1:{verse}\n")
        f.write(f"Phrase length: {phrase_len} words\n")
        f.write(f"Phrase (Hebrew): {phrase_heb}\n")
        f.write(f"Phrase (normalized): {phrase_norm}\n")

        # Find the position in the prayer
        pos = normalized_prayer.find(phrase_norm)
        if pos != -1:
            f.write(f"Position in prayer: {pos}\n")
            f.write(f"Prayer excerpt around match:\n")
            start = max(0, pos - 100)
            end = min(len(normalized_prayer), pos + len(phrase_norm) + 100)
            f.write(f"...{normalized_prayer[start:end]}...\n")
        else:
            f.write("NOT FOUND in normalized prayer\n")

        if context:
            f.write(f"\nContext (from DB): {context[:200]}...\n")
        else:
            f.write("\nContext: EMPTY\n")

    f.write(f"\n\n{'='*80}\n")
    f.write("OVERLAP ANALYSIS:\n\n")

    # Check for overlaps
    positions = []
    for idx, verse, phrase_heb, phrase_norm, phrase_len, context in matches:
        pos = normalized_prayer.find(phrase_norm)
        if pos != -1:
            positions.append({
                'id': idx,
                'verse': verse,
                'start': pos,
                'end': pos + len(phrase_norm),
                'phrase': phrase_norm
            })

    positions.sort(key=lambda x: x['start'])

    for i, p1 in enumerate(positions):
        for p2 in positions[i+1:]:
            # Check if they overlap
            if p1['start'] <= p2['end'] and p2['start'] <= p1['end']:
                overlap_start = max(p1['start'], p2['start'])
                overlap_end = min(p1['end'], p2['end'])
                overlap_len = overlap_end - overlap_start
                f.write(f"OVERLAP DETECTED:\n")
                f.write(f"  Match {p1['id']} (verse 1:{p1['verse']}, pos {p1['start']}-{p1['end']})\n")
                f.write(f"  Match {p2['id']} (verse 1:{p2['verse']}, pos {p2['start']}-{p2['end']})\n")
                f.write(f"  Overlap: {overlap_len} chars at position {overlap_start}-{overlap_end}\n\n")

print("Analysis complete. Results written to output/psalm1_duplicates_analysis.txt")
