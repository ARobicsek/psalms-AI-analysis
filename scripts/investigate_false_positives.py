import sys
import sqlite3

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

print("Investigating False Positives for Psalm 1")
print("=" * 70)
print()

# Get a specific false positive case: the phrase that validator said doesn't exist
# אֲשֶׁר פִּרְי֤וֹ ׀ יִתֵּ֬ן בְּעִתּ֗וֹ וְעָלֵ֥הוּ (from Hakafot for Simchat Torah)

cursor.execute('''
    SELECT
        i.index_id,
        i.psalm_phrase_hebrew,
        i.liturgy_phrase_hebrew,
        i.liturgy_context,
        i.match_type,
        i.confidence,
        p.canonical_prayer_name,
        p.nusach
    FROM psalms_liturgy_index i
    JOIN prayers p ON i.prayer_id = p.prayer_id
    WHERE i.psalm_chapter = 1
    AND p.canonical_prayer_name = 'Hakafot for Simchat Torah'
    LIMIT 5
''')

print("Matches in 'Hakafot for Simchat Torah':")
print()

for row in cursor.fetchall():
    index_id, psalm_phrase, liturgy_phrase, liturgy_context, match_type, confidence, prayer_name, nusach = row

    print(f"Index ID: {index_id}")
    print(f"Match Type: {match_type}")
    print(f"Confidence: {confidence}")
    print(f"Psalm Phrase (what we're searching for): {psalm_phrase}")
    print(f"Liturgy Phrase (what was found): {liturgy_phrase}")
    print(f"Liturgy Context (surrounding text):")
    print(f"  {liturgy_context}")
    print()

    # Check if the psalm phrase actually appears in the liturgy context
    if psalm_phrase in liturgy_context:
        print("✓ Psalm phrase FOUND in liturgy_context")
    else:
        print("✗ Psalm phrase NOT FOUND in liturgy_context")

    if liturgy_phrase in liturgy_context:
        print("✓ Liturgy phrase FOUND in liturgy_context")
    else:
        print("✗ Liturgy phrase NOT FOUND in liturgy_context")

    print("-" * 70)
    print()

# Now check the actual hebrew_text from the prayer to see if phrase exists there
cursor.execute('''
    SELECT
        i.index_id,
        i.psalm_phrase_hebrew,
        i.liturgy_context,
        p.hebrew_text
    FROM psalms_liturgy_index i
    JOIN prayers p ON i.prayer_id = p.prayer_id
    WHERE i.psalm_chapter = 1
    AND p.canonical_prayer_name = 'Hakafot for Simchat Torah'
    LIMIT 1
''')

row = cursor.fetchone()
if row:
    index_id, psalm_phrase, liturgy_context, hebrew_text = row

    print("\n" + "=" * 70)
    print("Checking full hebrew_text for first match:")
    print("=" * 70)
    print(f"Index ID: {index_id}")
    print(f"Psalm phrase: {psalm_phrase}")
    print()

    if psalm_phrase in hebrew_text:
        print("✓ Psalm phrase FOUND in full hebrew_text")
        # Find where it appears
        index = hebrew_text.find(psalm_phrase)
        context_start = max(0, index - 200)
        context_end = min(len(hebrew_text), index + len(psalm_phrase) + 200)
        actual_context = hebrew_text[context_start:context_end]
        print(f"\nActual context from hebrew_text (200 chars before/after):")
        print(f"  ...{actual_context}...")
    else:
        print("✗ Psalm phrase NOT FOUND in full hebrew_text either!")
        print("\nThis indicates the indexer created a phantom match.")

conn.close()
