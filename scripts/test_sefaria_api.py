"""
Test script to investigate Sefaria API response structure for footnotes.
"""

import requests
import json
import sys

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_sefaria_footnotes():
    """Check if Sefaria API provides separate footnote data."""

    # Test with Psalm 20:4 which has footnote contamination
    url = "https://www.sefaria.org/api/texts/Psalms.20.4"

    print("Fetching Psalm 20:4 from Sefaria API...\n")

    response = requests.get(url, params={'context': 0, 'commentary': 0})
    data = response.json()

    # Pretty print the full response to see structure
    print("=" * 80)
    print("FULL API RESPONSE:")
    print("=" * 80)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("\n")

    # Check for specific fields
    print("=" * 80)
    print("KEY FIELDS:")
    print("=" * 80)
    print(f"Hebrew text: {data.get('he', 'N/A')}")
    print(f"English text: {data.get('text', 'N/A')}")
    print(f"Available keys: {list(data.keys())}")

    # Check if there's any footnote-related metadata
    if 'notes' in data:
        print(f"\nNotes field found: {data['notes']}")
    if 'footnotes' in data:
        print(f"\nFootnotes field found: {data['footnotes']}")
    if 'commentary' in data:
        print(f"\nCommentary field found: {data['commentary']}")

if __name__ == '__main__':
    test_sefaria_footnotes()
