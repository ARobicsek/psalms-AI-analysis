"""
Deep dive into /api/words/ endpoint to understand its structure.
"""
import sys
import requests
import json

# Fix Windows UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def explore_words_endpoint():
    """Explore the structure of /api/words/{word}."""

    test_words = ['רעה', 'שמר']

    for word in test_words:
        print(f'\n{"="*70}')
        print(f'Analyzing /api/words/{word}')
        print("="*70)

        url = f'https://www.sefaria.org/api/words/{word}'
        resp = requests.get(url, params={'lookup_ref': 'Psalms.23.1'}, timeout=10)

        if not resp.ok:
            print(f'Error: {resp.status_code}')
            continue

        data = resp.json()

        print(f'\nData type: {type(data)}')
        print(f'Length: {len(data) if isinstance(data, list) else "N/A"}')

        if isinstance(data, list):
            print(f'\nList items: {len(data)}')
            for i, item in enumerate(data):
                print(f'\n--- Item {i+1} ---')
                print(f'Type: {type(item)}')
                if isinstance(item, dict):
                    print(f'Keys: {list(item.keys())}')
                    print(f'Full content:')
                    print(json.dumps(item, ensure_ascii=False, indent=2))
                else:
                    print(f'Value: {item}')

        elif isinstance(data, dict):
            print(f'\nDict keys: {list(data.keys())}')
            print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    explore_words_endpoint()
