"""
Test script to troubleshoot Sefaria BDB Lexicon API endpoints.
"""
import sys
import requests
import json

# Fix Windows UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_sefaria_lexicon_api():
    """Test various Sefaria API endpoints for lexicon data."""

    test_words = ['רעה', 'שמר', 'אל']  # shepherd/evil, guard/keep, God

    print('Testing Sefaria Lexicon API Endpoints')
    print('=' * 70)

    for test_word in test_words:
        print(f'\n\n### Testing word: {test_word} ###\n')

        # Test 1: /api/words/{word}
        print('1. Endpoint: /api/words/{word}')
        try:
            url = f'https://www.sefaria.org/api/words/{test_word}'
            resp = requests.get(url, params={'lookup_ref': 'Psalms.23.1'}, timeout=10)
            print(f'   Status: {resp.status_code}')
            if resp.ok:
                data = resp.json()
                print(f'   Response keys: {list(data.keys())}')
                if data:
                    # Print first 300 chars
                    print(f'   Sample: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...')
            else:
                print(f'   Error: {resp.text[:200]}')
        except Exception as e:
            print(f'   Exception: {e}')

        # Test 2: /api/name/{word} (lexicon lookup)
        print('\n2. Endpoint: /api/name/{word}')
        try:
            url = f'https://www.sefaria.org/api/name/{test_word}'
            resp = requests.get(url, timeout=10)
            print(f'   Status: {resp.status_code}')
            if resp.ok:
                data = resp.json()
                print(f'   Response keys: {list(data.keys())}')
                print(f'   Sample: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...')
            else:
                print(f'   Error: {resp.text[:200]}')
        except Exception as e:
            print(f'   Exception: {e}')

        # Test 3: Direct BDB text access
        print('\n3. Endpoint: /api/texts/BDB,{word}')
        try:
            # Try common BDB reference formats
            for format_attempt in [
                f'BDB,_{test_word}',
                f'BDB.{test_word}',
                f'BDB,{test_word}'
            ]:
                url = f'https://www.sefaria.org/api/texts/{format_attempt}'
                resp = requests.get(url, timeout=10)
                if resp.status_code != 404:
                    print(f'   Format: {format_attempt}')
                    print(f'   Status: {resp.status_code}')
                    if resp.ok:
                        data = resp.json()
                        print(f'   Keys: {list(data.keys())}')
                        if 'he' in data or 'text' in data:
                            print(f'   Hebrew: {str(data.get("he", ""))[:100]}...')
                            print(f'   English: {str(data.get("text", ""))[:100]}...')
                    break
        except Exception as e:
            print(f'   Exception: {e}')

    # Test 4: Check if BDB index exists
    print('\n\n### Testing BDB Index ###\n')
    print('4. Endpoint: /api/index/BDB')
    try:
        url = 'https://www.sefaria.org/api/index/BDB'
        resp = requests.get(url, timeout=10)
        print(f'   Status: {resp.status_code}')
        if resp.ok:
            data = resp.json()
            print(f'   Title: {data.get("title", "N/A")}')
            print(f'   Categories: {data.get("categories", [])}')
            print(f'   Schema: {data.get("schema", {}).get("titles", [])}')
        else:
            print(f'   Error: {resp.text[:200]}')
    except Exception as e:
        print(f'   Exception: {e}')

    # Test 5: Search for BDB entries
    print('\n5. Endpoint: /api/search-wrapper')
    try:
        url = 'https://www.sefaria.org/api/search-wrapper'
        params = {
            'q': 'רעה',
            'type': 'sheet',  # or 'text'
            'filters': 'lexicon'
        }
        resp = requests.get(url, params=params, timeout=10)
        print(f'   Status: {resp.status_code}')
        if resp.ok:
            data = resp.json()
            print(f'   Response keys: {list(data.keys())}')
            print(f'   Total results: {data.get("total", 0)}')
    except Exception as e:
        print(f'   Exception: {e}')

    print('\n\n' + '=' * 70)
    print('Testing complete.')


if __name__ == '__main__':
    test_sefaria_lexicon_api()
