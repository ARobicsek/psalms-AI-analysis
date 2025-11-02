"""
Test the paseq fix for context extraction.
"""
import sys
sys.path.append('.')

from src.liturgy.liturgy_indexer import LiturgyIndexer
import sqlite3

# Initialize indexer
indexer = LiturgyIndexer(verbose=False)

# Get the prayer text from prayer 626
conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()
cursor.execute("SELECT hebrew_text FROM prayers WHERE prayer_id=626")
prayer_text = cursor.fetchone()[0]
conn.close()

# Test case: The 10-word phrase with paseq
test_phrase = "וְֽהָיָ֗ה כְּעֵץ֮ שָׁת֢וּל עַֽל־פַּלְגֵ֫י־מָ֥יִם אֲשֶׁ֤ר פִּרְי֨וֹ ׀ יִתֵּ֬ן בְּעִתּ֗וֹ וְעָלֵ֥הוּ"

with open('output/paseq_fix_test.txt', 'w', encoding='utf-8') as f:
    f.write("Test: Paseq Fix for Context Extraction\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Test phrase: {test_phrase}\n\n")

    # Count words in original
    original_words = test_phrase.split()
    f.write(f"Original word count: {len(original_words)}\n")
    f.write(f"Original words: {original_words}\n\n")

    # Count words after normalization
    normalized = indexer._full_normalize(test_phrase)
    normalized_words = normalized.split()
    f.write(f"Normalized phrase: {normalized}\n")
    f.write(f"Normalized word count: {len(normalized_words)}\n")
    f.write(f"Normalized words: {normalized_words}\n\n")

    # Try to extract context
    context = indexer._extract_context(prayer_text, test_phrase, context_words=10)

    if context:
        f.write("✅ SUCCESS: Context extracted!\n")
        f.write(f"Context ({len(context)} chars):\n")
        f.write(context + "\n\n")

        # Verify the phrase is in the context
        if test_phrase in context:
            f.write("✅ Original phrase found in context\n")
        elif normalized in indexer._full_normalize(context):
            f.write("✅ Normalized phrase found in context\n")
        else:
            f.write("⚠️ WARNING: Phrase not found in extracted context\n")
    else:
        f.write("❌ FAILURE: Context extraction returned empty\n")

print("Test complete. Results written to output/paseq_fix_test.txt")
