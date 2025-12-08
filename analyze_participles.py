#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Analyze participle patterns in Hebrew"""

import sqlite3

def analyze_participles():
    """Find participle patterns"""

    db_path = "c:/Users/ariro/OneDrive/Documents/Psalms/database/tanakh.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    output = []

    # Find words that start with ה but the consonantal form without ה also exists
    # This suggests participle forms
    output.append("=== Analyzing Potential Participle Forms ===\n")

    # Get all unique words that start with ה
    cursor.execute("""
        SELECT DISTINCT word_consonantal_split
        FROM concordance
        WHERE word_consonantal_split LIKE 'ה%'
        AND LENGTH(word_consonantal_split) >= 3
        LIMIT 100
    """)

    he_words = [row[0] for row in cursor.fetchall()]
    output.append(f"Found {len(he_words)} words starting with ה")

    # Check for participle patterns
    participles = []
    for word in he_words:
        # Remove the ה and check if the rest exists as a word
        if len(word) >= 3:
            without_he = word[1:]  # Remove first letter ה
            if len(without_he) >= 2:  # Ensure remaining word is meaningful
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM concordance
                    WHERE word_consonantal_split = ?
                """, (without_he,))
                count = cursor.fetchone()['count']
                if count > 0:
                    participles.append((word, without_he, count))

    output.append(f"\nFound {len(participles)} potential participle forms:")
    for word, base, count in sorted(participles)[:20]:
        output.append(f"  {word} -> {base} (appears {count} times)")

    # Check specific cases from Psalm 15
    output.append("\n=== Specific Psalm 15 Cases ===")
    psalm_words = ['הולך', 'הוליך', 'יושב', 'יודע']

    for word in psalm_words:
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM concordance
            WHERE word_consonantal_split = ?
        """, (word,))
        count = cursor.fetchone()['count']
        output.append(f"\n{word}: {count} occurrences")

        # Check if it might be a participle
        if word.startswith('ה') and len(word) >= 3:
            base = word[1:]
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM concordance
                WHERE word_consonantal_split = ?
            """, (base,))
            base_count = cursor.fetchone()['count']
            output.append(f"  Base form '{base}': {base_count} occurrences")

    conn.close()

    # Write output
    with open("participle_analysis.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print("Analysis written to participle_analysis.txt")

if __name__ == "__main__":
    analyze_participles()