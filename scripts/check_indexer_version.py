import sys
import sqlite3

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

# Check which search function is actually being used
# Look for clues in the database - old vs new method

cursor.execute('''
    SELECT
        COUNT(*) as total_matches,
        COUNT(DISTINCT psalm_chapter) as psalm_count,
        AVG(length(liturgy_context)) as avg_context_len,
        MIN(length(liturgy_context)) as min_context_len,
        MAX(length(liturgy_context)) as max_context_len
    FROM psalms_liturgy_index
''')

stats = cursor.fetchone()
print("Database Statistics:")
print(f"  Total matches: {stats[0]}")
print(f"  Psalms indexed: {stats[1]}")
print(f"  Avg context length: {stats[2]:.0f} chars")
print(f"  Min context length: {stats[3]} chars")
print(f"  Max context length: {stats[4]} chars")
print()

# Check if there's a specific pattern: old method uses word-based extraction (shorter contexts)
# new method uses character-based extraction (500 before + 500 after = ~1000 chars)

if stats[2] < 400:
    print("⚠ Context lengths suggest OLD indexer (word-based, ~200 chars)")
    print("  Expected for NEW indexer: ~1000 chars (500 before + 500 after)")
else:
    print("✓ Context lengths suggest NEW indexer (character-based)")

print()

# Now let's check if the context extraction is actually broken
# by verifying if matched phrases exist in their contexts

cursor.execute('''
    SELECT
        i.psalm_phrase_hebrew,
        i.liturgy_context,
        i.liturgy_phrase_hebrew
    FROM psalms_liturgy_index i
    WHERE i.psalm_chapter = 1
    LIMIT 10
''')

print("Checking if phrases exist in their contexts (Psalm 1, first 10 matches):")
print()

found_count = 0
missing_count = 0

for psalm_phrase, liturgy_context, liturgy_phrase in cursor.fetchall():
    # Check if either psalm_phrase or liturgy_phrase exists in context
    psalm_in_context = psalm_phrase in liturgy_context
    liturgy_in_context = liturgy_phrase in liturgy_context

    if psalm_in_context or liturgy_in_context:
        found_count += 1
        status = "✓"
    else:
        missing_count += 1
        status = "✗"

    print(f"{status} Phrase: {psalm_phrase[:40]}...")

print()
print(f"Result: {found_count} found in context, {missing_count} missing")

if missing_count > 0:
    print("\n⚠ CRITICAL: Some phrases don't exist in their liturgy_context!")
    print("  This indicates the indexer is broken or database needs re-indexing.")

conn.close()
