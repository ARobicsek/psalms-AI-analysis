#!/usr/bin/env python3
"""Fetch actual topic data from Sefaria API."""

import json
import requests

SEFARIA_API = "https://www.sefaria.org/api"

def fetch_topic_texts(topic_name):
    """Fetch texts associated with a topic from Sefaria."""
    try:
        # Try the topics API endpoint
        url = f"{SEFARIA_API}/v2/topics/{topic_name}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Topic '{topic_name}' not found or API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching topic {topic_name}: {e}")
        return None

def fetch_text_structure(text_name):
    """Fetch text structure to understand divisions."""
    try:
        url = f"{SEFARIA_API}/index/{text_name}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching structure for {text_name}: {e}")
        return None

def search_topic(topic_name):
    """Search for topic mentions in texts."""
    try:
        # Use search API to find topic references
        url = f"{SEFARIA_API}/search?q={topic_name}&type=text"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error searching for {topic_name}: {e}")
        return None

def main():
    print("FETCHING SEFARIA TOPIC DATA")
    print("=" * 60)

    # Try to fetch some common topics
    topics_to_try = [
        "Creation",
        "Covenant",
        "Prophecy",
        "Wisdom",
        "Messianism",
        "Exile",
        "Redemption"
    ]

    for topic in topics_to_try:
        print(f"\nTopic: {topic}")
        print("-" * 40)

        # Try different API approaches
        # 1. Direct topic fetch
        topic_data = fetch_topic_texts(topic)
        if topic_data:
            print(f"✓ Found topic data via /v2/topics/{topic}")
            if isinstance(topic_data, dict):
                if 'texts' in topic_data:
                    print(f"  Texts: {len(topic_data['texts'])} items")
                if 'related' in topic_data:
                    print(f"  Related topics: {len(topic_data.get('related', []))}")

        # 2. Search for the term
        search_results = search_topic(topic)
        if search_results and 'hits' in search_results:
            print(f"✓ Found {len(search_results['hits'])} search results")
            # Show first 3 results
            for hit in search_results['hits'][:3]:
                if 'ref' in hit:
                    print(f"  - {hit['ref']}")

        # 3. Show example from Genesis
        if topic.lower() == "creation":
            print("\nExample: Creation passages in Genesis")
            print("  - Genesis 1:1-2:3 (Seven days of creation)")
            print("  - Genesis 2:4-25 (Adam and Eve)")
            print("  - Related themes: Light, Water, Life, Order from chaos")

    print("\n" + "=" * 60)
    print("SEFARIA TEXT STRUCTURES")
    print("-" * 40)

    # Show how texts are structured
    books_to_check = ["Genesis", "Psalms", "Isaiah"]

    for book in books_to_check:
        structure = fetch_text_structure(book)
        if structure:
            print(f"\n{book}:")
            if 'categories' in structure:
                print(f"  Category: {' > '.join(structure['categories'])}")
            if 'length' in structure:
                print(f"  Length: {structure['length']} verses")
            if 'heTitle' in structure:
                print(f"  Hebrew: {structure['heTitle']}")

if __name__ == "__main__":
    main()