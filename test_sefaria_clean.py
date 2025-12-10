#!/usr/bin/env python3
"""Test if Sefaria API can return clean English text without footnotes."""

import sys
sys.path.append('src')

from data_sources.sefaria_client import SefariaClient
import requests
import json

def test_clean_english():
    """Test various approaches to get clean English from Sefaria."""

    client = SefariaClient()

    # Test 1: Standard API call
    print("=== Test 1: Standard API call ===")
    ref = "Genesis.2.7"
    data = client._make_request(f"texts/{ref}", params={
        'context': 0,
        'commentary': 0,
        'pad': 0
    })
    english = data.get('text', [''])[0] if isinstance(data.get('text'), list) else data.get('text', '')
    print(f"English: {english[:200]}...")
    print()

    # Test 2: Try different parameters that might exclude notes
    print("=== Test 2: Try 'version' parameter ===")
    try:
        # Try different versions
        versions = ["en", "english", "Sefaria English Translation", "The Holy Scriptures: A New Translation"]
        for version in versions[:2]:  # Test first 2
            print(f"Trying version: {version}")
            data = client._make_request(f"texts/{ref}", params={
                'context': 0,
                'commentary': 0,
                'version': version,
                'lang': 'en'
            })
            english = data.get('text', [''])[0] if isinstance(data.get('text'), list) else data.get('text', '')
            print(f"Result: {english[:100]}...")
            print()
    except Exception as e:
        print(f"Version test failed: {e}")
        print()

    # Test 3: Direct API call to see available options
    print("=== Test 3: Check API response structure ===")
    try:
        url = "https://www.sefaria.org/api/texts/Genesis.2.7"
        response = requests.get(url, params={'context': 0, 'commentary': 0})
        data = response.json()

        # Check what fields are available
        print(f"Available keys: {list(data.keys())}")

        # Check if there's a clean version
        if 'text' in data:
            print(f"Text type: {type(data['text'])}")
            if isinstance(data['text'], list) and data['text']:
                print(f"First verse: {data['text'][0][:200]}...")

        # Check for alternative fields
        for key in ['clean', 'plain', 'source', 'original']:
            if key in data:
                print(f"{key}: {str(data[key])[:100]}...")

    except Exception as e:
        print(f"Direct API test failed: {e}")

if __name__ == "__main__":
    test_clean_english()