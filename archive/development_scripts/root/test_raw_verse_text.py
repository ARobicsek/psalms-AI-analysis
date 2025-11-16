"""
Check raw Hebrew text from verses table
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import sqlite3
import json
from pathlib import Path

db_path = Path("database/tanakh.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get the raw Hebrew text for Psalm 3:8
cursor.execute("""
    SELECT book_name, chapter, verse, hebrew, english
    FROM verses
    WHERE book_name = 'Psalms' AND chapter = 3 AND verse = 8
""")
row = cursor.fetchone()

if row:
    book, ch, vs, hebrew, english = row

    result = {
        "reference": f"{book} {ch}:{vs}",
        "hebrew_raw": hebrew,
        "english": english,
        "analysis": {
            "contains_maqqef_char": "־" in hebrew,
            "maqqef_count": hebrew.count("־"),
            "character_breakdown": []
        }
    }

    # Break down each character
    for i, char in enumerate(hebrew):
        char_info = {
            "index": i,
            "char": char,
            "unicode": f"U+{ord(char):04X}",
            "name": ""
        }

        # Identify special characters
        if ord(char) == 0x05BE:
            char_info["name"] = "MAQQEF"
        elif ord(char) == 0x0020:
            char_info["name"] = "SPACE"
        elif 0x05D0 <= ord(char) <= 0x05EA:
            char_info["name"] = "HEBREW_LETTER"
        elif 0x0591 <= ord(char) <= 0x05C7:
            char_info["name"] = "DIACRITIC"
        else:
            char_info["name"] = "OTHER"

        result["analysis"]["character_breakdown"].append(char_info)

    # Save to JSON
    output_path = Path("output/debug/raw_verse_analysis.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Analysis saved to: {output_path}")
    print(f"\nRaw Hebrew text length: {len(hebrew)} characters")
    print(f"Contains maqqef (U+05BE)? {result['analysis']['contains_maqqef_char']}")
    print(f"Maqqef count: {result['analysis']['maqqef_count']}")

    # Show word split
    from src.concordance.hebrew_text_processor import split_words
    words = split_words(hebrew)
    print(f"\nWords after split_words(): {len(words)} words")
    for i, word in enumerate(words):
        has_maqqef = "־" in word
        print(f"  Word {i}: {has_maqqef and 'HAS MAQQEF' or 'no maqqef'}")

else:
    print("Verse not found!")

conn.close()
