#!/usr/bin/env python3
"""Debug the text cleaning issues."""
import sqlite3
import re

# Connect to database
conn = sqlite3.connect('database/tanakh.db')
conn.row_factory = sqlite3.Row

# Get the exact verses for Genesis 3:19-23
cursor = conn.execute("""
    SELECT chapter, verse, english
    FROM verses
    WHERE book_name = 'Genesis'
    AND chapter = 3
    AND verse BETWEEN 19 AND 23
    ORDER BY chapter, verse
""")

print("=== ORIGINAL TEXT FROM DATABASE ===\n")
verses = []
for row in cursor:
    verses.append(row)
    print(f"Genesis {row['chapter']}:{row['verse']}")
    print(f"Text: {row['english']}")
    print()

print("=== COMBINED TEXT ===\n")
combined = " ".join(v["english"] for v in verses)
print(combined[:1000] + "...")

# Test cleaning
def clean_english_text_v2(text: str) -> str:
    """More precise version that preserves valid text."""
    if not text:
        return text

    # Fix the specific "*When God began to create*When God began to create Others" pattern
    # This seems to be a duplication issue where the asterisked part duplicates the text
    text = re.sub(r'\*([^*]+)\* \1', r'\1', text)

    # Remove the asterisked duplicate but keep the original text
    text = re.sub(r'\*[^*]+\*', '', text)

    # Remove footnotes more precisely
    # Pattern: Heb. 'text'. Cf. text.
    text = re.sub(r'\s+Heb\.\s*\'[^\']*\'(?:\.|\s+)(?:Cf\.\s*[^\.,]+\.?)?', '', text)

    # Pattern: Heb. text. Cf. text.
    text = re.sub(r'\s+Heb\.\s+[^.,;:]+\.\s*(?:Cf\.\s*[^.,;:]+\.?)?', '', text)

    # Pattern: *text* (asterisked notes)
    text = re.sub(r'\s*\*[^*]+\*\s*', ' ', text)

    # Pattern: Single asterisks
    text = re.sub(r'\*+', '', text)

    # Pattern: "Others 'text'"
    text = re.sub(r'\s+Others\s*\'[^\']*\'\s*', '', text)

    # Pattern: Cf. text.
    text = re.sub(r'\s+Cf\.\s+[^.,;:]+\.?', '', text)

    # Pattern: Emendation text
    text = re.sub(r'\s+Emendation[^.,;:]*\.?', '', text)

    # Pattern: (Heb: text)
    text = re.sub(r'\s*\([^)]*Heb[^)]*\)', '', text)

    # Pattern: "Moved up from v. X for clarity"
    text = re.sub(r'\s+[^.,]*\s+Moved up from v\.\s+\d+\s+for clarity', '', text)

    # Pattern: Lit. 'text'.
    text = re.sub(r'\s+Lit\.\s*\'[^\']*\'\.?', '', text)

    # Fix specific spacing issues
    text = re.sub(r'(\w)([A-Z][a-z])', r'\1 \2', text)  # wordWord -> word Word
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces
    text = re.sub(r'\s*([.,])', r'\1', text)  # Space before punctuation
    text = re.sub(r'([.,])(\w)', r'\1 \2', text)  # Ensure space after punctuation

    return text.strip()

print("\n=== AFTER CLEANING (V2) ===\n")
cleaned = clean_english_text_v2(combined)
print(cleaned[:1000] + "...")

conn.close()