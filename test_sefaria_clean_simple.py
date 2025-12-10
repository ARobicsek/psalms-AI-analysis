#!/usr/bin/env python3
"""Simple test for Sefaria API clean text."""

import sys
sys.path.append('src')

from data_sources.sefaria_client import SefariaClient
import re

def test_clean_english():
    client = SefariaClient()

    # Get Genesis 2:7
    book_text = client.fetch_book_chapter("Genesis", 2)

    # Find verse 7
    for verse in book_text.verses:
        if verse.verse == 7:
            print(f"Reference: {verse.reference}")
            print(f"English length: {len(verse.english)} chars")
            print(f"Has 'Heb.': {'Heb.' in verse.english}")
            print(f"Has 'Lit.': {'Lit.' in verse.english}")
            print(f"Has '*': {'*' in verse.english}")

            # Count footnote patterns
            heb_count = len(re.findall(r'Heb\.', verse.english))
            lit_count = len(re.findall(r'Lit\.', verse.english))
            star_count = len(re.findall(r'\*', verse.english))

            print(f"\nFootnote counts:")
            print(f"  Heb. notes: {heb_count}")
            print(f"  Lit. notes: {lit_count}")
            print(f"  Asterisks: {star_count}")

            # Show first 200 chars
            preview = verse.english[:200].replace('\n', ' ')
            print(f"\nPreview: {preview}...")

            return verse

if __name__ == "__main__":
    verse = test_clean_english()