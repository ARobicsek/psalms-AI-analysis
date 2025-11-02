import sqlite3
import sys

# Write to file with UTF-8 encoding
with open('output/context_issue_results.txt', 'w', encoding='utf-8') as f:
    # Connect to database
    conn = sqlite3.connect('data/liturgy.db')
    cursor = conn.cursor()

    # Get Psalm 1 matches in prayer 626
    cursor.execute("""
        SELECT
            psalm_phrase_hebrew,
            liturgy_phrase_hebrew,
            liturgy_context,
            match_type
        FROM psalms_liturgy_index
        WHERE psalm_chapter=1 AND prayer_id=626
        LIMIT 5
    """)

    results = cursor.fetchall()

    f.write(f"Found {len(results)} matches for Psalm 1 in prayer 626\n\n")

    for i, (psalm_phrase, matched_phrase, context, match_type) in enumerate(results, 1):
        f.write(f"Match {i} ({match_type}):\n")
        f.write(f"  Psalm phrase: {psalm_phrase}\n")
        f.write(f"  Matched phrase: {matched_phrase}\n")
        f.write(f"  Context length: {len(context)} chars\n")

        # Check if the matched phrase appears in the context
        if matched_phrase in context:
            pos = context.find(matched_phrase)
            f.write(f"  ✓ Matched phrase FOUND in context at position {pos}\n")
            # Show a bit of context around it
            start = max(0, pos - 50)
            end = min(len(context), pos + len(matched_phrase) + 50)
            f.write(f"  Context around match: ...{context[start:end]}...\n")
        else:
            f.write(f"  ✗ Matched phrase NOT FOUND in context!\n")
            f.write(f"  Context starts with: {context[:200]}...\n")
        f.write('\n')

    conn.close()

print("Results written to output/context_issue_results.txt")
