#!/usr/bin/env python3
"""Analyze and clean up the thematic corpus text issues."""
import sqlite3
import re
from pathlib import Path

# Connect to database
conn = sqlite3.connect('database/tanakh.db')
conn.row_factory = sqlite3.Row

def analyze_hebrew_dividers():
    """Check if Hebrew dividers exist in the database."""
    print("=== CHECKING HEBREW DIVIDERS ===\n")

    # Get a sample of verses
    cursor = conn.execute("""
        SELECT book_name, chapter, verse, hebrew
        FROM verses
        WHERE book_name = 'Psalms'
        LIMIT 10
    """)

    has_pasuq = False
    has_peh_samech = False

    for row in cursor:
        hebrew = row['hebrew']
        ref = f"{row['book_name']} {row['chapter']}:{row['verse']}"

        if '׀' in hebrew:
            has_pasuq = True
            print(f"[X] Found pasuq in {ref}")

        if '{ס}' in hebrew or '{פ}' in hebrew:
            has_peh_samech = True
            print(f"[X] Found peh/samech {{פ/{{ס}} in {ref}")

    print(f"\nSummary:")
    print(f"- Pasuq (׀): {'Found' if has_pasuq else 'Not found'}")
    print(f"- Peh/Samech {{פ/{{ס}}: {'Found' if has_peh_samech else 'Not found'}")

    return has_pasuq, has_peh_samech

def analyze_english_footnotes():
    """Analyze footnote patterns in English text."""
    print("\n=== ANALYZING ENGLISH FOOTNOTES ===\n")

    # Get a sample of verses with footnotes
    cursor = conn.execute("""
        SELECT book_name, chapter, verse, english
        FROM verses
        WHERE english LIKE '%*%'
        OR english LIKE '%^%'
        OR english LIKE '%[_]%'
        OR english LIKE '%/%'
        LIMIT 10
    """)

    footnote_patterns = []

    for row in cursor:
        english = row['english']
        ref = f"{row['book_name']} {row['chapter']}:{row['verse']}"

        # Find footnote patterns
        if '*' in english:
            footnote_patterns.append((ref, 'Asterisk (*)', english[:100] + '...'))
        if '^' in english:
            footnote_patterns.append((ref, 'Caret (^)', english[:100] + '...'))
        if '[_' in english:
            footnote_patterns.append((ref, 'Bracket [_]', english[:100] + '...'))
        if ' Cf.' in english:
            footnote_patterns.append((ref, 'Cf. reference', english[:100] + '...'))
        if ' Heb.' in english:
            footnote_patterns.append((ref, 'Hebrew note', english[:100] + '...'))
        if ' Emendation' in english:
            footnote_patterns.append((ref, 'Emendation note', english[:100] + '...'))

    if footnote_patterns:
        print("Sample footnote patterns found:")
        for ref, pattern, text in footnote_patterns[:5]:
            print(f"\n{ref} - {pattern}:")
            print(f"  {text}")
    else:
        print("No obvious footnote patterns found in sample")

    return len(footnote_patterns) > 0

def clean_english_text(text):
    """Remove footnotes and translator notes from English text."""
    if not text:
        return text

    # Remove text within asterisks (including asterisks)
    text = re.sub(r'\*[^*]*\*', '', text)

    # Remove remaining asterisks
    text = re.sub(r'\*', '', text)

    # Remove text between brackets and parentheses (common for notes)
    text = re.sub(r'\[[^\]]*\]', '', text)
    text = re.sub(r'\([^)]*Heb\.[^)]*\)', '', text)
    text = re.sub(r'\([^)]*Cf\.[^)]*\)', '', text)
    text = re.sub(r'\([^)]*Emendation[^)]*\)', '', text)

    # Remove specific patterns
    text = re.sub(r' Cf\..*?$', '', text, flags=re.MULTILINE)
    text = re.sub(r'; .* Heb\..*?$', '', text, flags=re.MULTILINE)
    text = re.sub(r'; .*^.*?$', '', text, flags=re.MULTILINE)

    # Clean up extra spaces and punctuation
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # Remove trailing semicolons with no following text
    text = re.sub(r';\s*$', '', text)

    return text

def test_cleaning():
    """Test the cleaning function on some examples."""
    print("\n=== TESTING ENGLISH CLEANING ===\n")

    test_cases = [
        'The great day of GOD is approaching,Approaching most swiftly.Hark, the day of GOD!It is bitter:There a warrior shrieks!kHark, the day of GOD! / It is bitter: / There a warrior shrieks! Emendation yields: "The day of GOD is faster than a runner, / Fleeter than a warrior"; cf. Ps. 19.6.',
        'For dust*dust Heb. "afar. Cf. the second note at 2.7.',
        '*living Heb. ḥai.',
        '*humankind Moved up from v. 24 for clarity.'
    ]

    for i, text in enumerate(test_cases, 1):
        cleaned = clean_english_text(text)
        print(f"Example {i}:")
        print(f"  Original: {text[:100]}...")
        print(f"  Cleaned:  {cleaned[:100]}...")
        print()

if __name__ == "__main__":
    has_pasuq, has_peh_samech = analyze_hebrew_dividers()
    has_footnotes = analyze_english_footnotes()
    test_cleaning()

    print("\n=== RECOMMENDATIONS ===\n")
    print("1. Hebrew Dividers:")
    if has_pasuq:
        print("   - Pasuq (׀): Consider removing for cleaner embeddings")
    if has_peh_samech:
        print("   - Peh/Samech {{פ/{{ס}}: Remove - these are parsha markers not relevant for thematic search")

    print("\n2. English Footnotes:")
    if has_footnotes:
        print("   - Remove all footnotes and translator notes")
        print("   - This will reduce noise in embeddings")

    conn.close()