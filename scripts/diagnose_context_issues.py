"""
Diagnose why some liturgical_context fields are empty after the fix.
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

# Get Psalm 1 matches with empty context
cursor.execute("""
    SELECT
        index_id,
        psalm_verse_start,
        psalm_phrase_hebrew,
        phrase_length,
        prayer_id,
        liturgy_phrase_hebrew,
        liturgy_context
    FROM psalms_liturgy_index
    WHERE psalm_chapter=1
    ORDER BY psalm_verse_start, phrase_length DESC
""")

results = cursor.fetchall()

# Also get the prayer text for prayer 626
cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id=626")
prayer_text = cursor.fetchone()[0]

with open('output/context_diagnosis.txt', 'w', encoding='utf-8') as f:
    f.write(f"=== DIAGNOSIS: Psalm 1 Context Issues ===\n\n")
    f.write(f"Total matches for Psalm 1: {len(results)}\n\n")

    empty_contexts = 0
    for idx, verse_start, phrase_heb, phrase_len, prayer_id, liturgy_phrase, context in results:
        if not context or context.strip() == "":
            empty_contexts += 1
            f.write(f"\n{'='*80}\n")
            f.write(f"EMPTY CONTEXT - Index ID: {idx}\n")
            f.write(f"Verse: 1:{verse_start}\n")
            f.write(f"Phrase length: {phrase_len} words\n")
            f.write(f"Psalm phrase: {phrase_heb}\n")
            f.write(f"Liturgy phrase: {liturgy_phrase}\n")
            f.write(f"Prayer ID: {prayer_id}\n\n")

            if prayer_id == 626:
                # Try to extract context manually
                f.write("Attempting manual context extraction...\n")
                try:
                    extracted_context = indexer._extract_context(prayer_text, phrase_heb, context_words=10)
                    if extracted_context:
                        f.write(f"✓ Successfully extracted: {extracted_context[:200]}...\n")
                    else:
                        f.write("✗ Manual extraction also returned empty\n")

                        # Try to find the phrase in the prayer
                        normalized_phrase = indexer._full_normalize(phrase_heb)
                        normalized_prayer = indexer._full_normalize(prayer_text)

                        if normalized_phrase in normalized_prayer:
                            pos = normalized_prayer.find(normalized_phrase)
                            f.write(f"✓ Phrase IS in normalized prayer at position {pos}\n")
                            f.write(f"  Normalized phrase: {normalized_phrase}\n")
                            f.write(f"  Prayer excerpt: ...{normalized_prayer[max(0,pos-50):pos+len(normalized_phrase)+50]}...\n")
                        else:
                            f.write(f"✗ Phrase NOT FOUND in normalized prayer\n")
                            f.write(f"  Normalized phrase: {normalized_phrase}\n")
                            f.write(f"  Searching for substrings...\n")

                            # Check if any words from the phrase exist
                            phrase_words = normalized_phrase.split()
                            for i, word in enumerate(phrase_words):
                                if word in normalized_prayer:
                                    f.write(f"    Word {i+1} '{word}': FOUND\n")
                                else:
                                    f.write(f"    Word {i+1} '{word}': NOT FOUND\n")
                except Exception as e:
                    f.write(f"✗ Error during extraction: {e}\n")

    f.write(f"\n\n{'='*80}\n")
    f.write(f"SUMMARY:\n")
    f.write(f"Total matches: {len(results)}\n")
    f.write(f"Empty contexts: {empty_contexts}\n")
    f.write(f"Success rate: {100 * (len(results) - empty_contexts) / len(results):.1f}%\n")

conn.close()
print("Diagnosis complete. Results written to output/context_diagnosis.txt")
