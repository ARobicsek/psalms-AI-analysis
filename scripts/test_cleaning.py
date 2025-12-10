#!/usr/bin/env python3
"""Test and improve text cleaning."""
import sqlite3
import re

# Connect to database
conn = sqlite3.connect('database/tanakh.db')
conn.row_factory = sqlite3.Row

def clean_english_text_improved(text: str) -> str:
    """Improved version of English text cleaning."""
    if not text:
        return text

    # Remove asterisk patterns first
    text = re.sub(r'\*[^*]*\*', '', text)  # *text*
    text = re.sub(r'\*', '', text)  # remaining asterisks

    # Remove brackets and content
    text = re.sub(r'\[[^\]]*\]', '', text)

    # Handle specific patterns
    patterns_to_remove = [
        r'\s*a\s+wind\s+from\s+Others[^,.]*',
        r'\s*the\s+spirit\s+of\.\s*Others[^,.]*',
        r'\s*When\s+God\s+began\s+to\s+create\*[^,.]*',
        r'\s*When\s+God\s+began\s+to\s+create[^,.]*',
        r'\s*Others[^,.]*',
        r'\s*Heb\.[^,.]*',
        r'\s*Cf\.[^,.]*',
        r'\s*Emendation[^,.]*',
        r'\s*[^.]*\s*Hebrew\s+translation[^,.]*',
    ]

    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Clean up artifacts
    text = re.sub(r'[,;]\s*$', '', text)  # trailing punctuation
    text = re.sub(r'\s+', ' ', text)  # multiple spaces
    text = re.sub(r'\s*([,.])', r'\1', text)  # space before punctuation
    text = text.strip()

    return text

# Test on Genesis 1:1-2
cursor = conn.execute("""
    SELECT chapter, verse, hebrew, english
    FROM verses
    WHERE book_name = 'Genesis'
    AND chapter = 1
    AND verse IN (1, 2)
    ORDER BY chapter, verse
""")

print("=== TESTING ENGLISH CLEANING ===\n")

verses = []
for row in cursor:
    verses.append(row)
    print(f"Genesis {row['chapter']}:{row['verse']}")
    print(f"Original: {row['english']}")
    cleaned = clean_english_text_improved(row['english'])
    print(f"Cleaned:  {cleaned}")
    print()

# Test combining verses
print("=== COMBINED TEXT ===\n")
combined_original = " ".join(v["english"] for v in verses)
combined_cleaned = " ".join(clean_english_text_improved(v["english"]) for v in verses)

print(f"Original combined: {combined_original[:200]}...")
print(f"Cleaned combined:  {combined_cleaned[:200]}...")

conn.close()