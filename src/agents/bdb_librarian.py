"""
BDB Librarian Agent

Fetches Hebrew lexicon entries from the Brown-Driver-Briggs (BDB) Hebrew-English Lexicon
via the Sefaria API. This is a pure Python data retriever (not an LLM agent).

The BDB Librarian provides:
- Word definitions and etymologies
- Semantic ranges and usage notes
- Biblical Hebrew lexicography
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.data_sources.sefaria_client import SefariaClient
else:
    from ..data_sources.sefaria_client import SefariaClient


@dataclass
class LexiconEntry:
    """A single lexicon entry from BDB."""
    word: str
    lexicon_name: str
    entry_text: str
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'word': self.word,
            'lexicon': self.lexicon_name,
            'entry': self.entry_text,
            'url': self.url
        }


@dataclass
class LexiconRequest:
    """A request for lexicon entries."""
    word: str
    notes: Optional[str] = None  # Why this word is being requested

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LexiconRequest':
        """Create from dictionary."""
        return cls(
            word=data['word'],
            notes=data.get('notes')
        )


@dataclass
class LexiconBundle:
    """Bundle of lexicon entries for multiple words."""
    entries: List[LexiconEntry]
    requests: List[LexiconRequest]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'entries': [e.to_dict() for e in self.entries],
            'requests': [
                {'word': r.word, 'notes': r.notes}
                for r in self.requests
            ]
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class BDBLibrarian:
    """
    Fetches Hebrew lexicon entries from Sefaria's BDB lexicon.

    This is a pure Python data retriever - no LLM calls are made.
    It serves as the "librarian" that fetches reference materials
    for the Scholar-Researcher agent to analyze.
    """

    def __init__(self, client: Optional[SefariaClient] = None):
        """
        Initialize BDB Librarian.

        Args:
            client: SefariaClient instance (creates new if None)
        """
        self.client = client or SefariaClient()

    def fetch_entry(self, word: str) -> List[LexiconEntry]:
        """
        Fetch lexicon entry for a single Hebrew word.

        Args:
            word: Hebrew word to look up

        Returns:
            List of LexiconEntry objects (may be multiple lexicons)

        Example:
            >>> librarian = BDBLibrarian()
            >>> entries = librarian.fetch_entry("שָׁמַר")
            >>> for entry in entries:
            ...     print(f"{entry.lexicon_name}: {entry.entry_text[:100]}...")
        """
        entries = []

        try:
            # Fetch from Sefaria API
            response = self.client.fetch_lexicon_entry(word)

            # Sefaria returns a list of entries from different lexicons
            if isinstance(response, list):
                for item in response:
                    entry = LexiconEntry(
                        word=word,
                        lexicon_name=item.get('lexicon', 'Unknown'),
                        entry_text=item.get('content', {}).get('senses', [{}])[0].get('definition', ''),
                        url=item.get('url')
                    )
                    entries.append(entry)

            elif isinstance(response, dict):
                # Single entry format
                entry = LexiconEntry(
                    word=word,
                    lexicon_name=response.get('lexicon', 'Unknown'),
                    entry_text=response.get('content', {}).get('senses', [{}])[0].get('definition', ''),
                    url=response.get('url')
                )
                entries.append(entry)

        except Exception as e:
            # Return empty list if lookup fails
            print(f"Warning: Could not fetch lexicon entry for '{word}': {e}", file=sys.stderr)

        return entries

    def fetch_multiple(self, requests: List[LexiconRequest]) -> LexiconBundle:
        """
        Fetch lexicon entries for multiple words.

        Args:
            requests: List of LexiconRequest objects

        Returns:
            LexiconBundle containing all entries and original requests

        Example:
            >>> requests = [
            ...     LexiconRequest("שָׁמַר", notes="Key verb in v.5"),
            ...     LexiconRequest("מִצְוָה", notes="Commandment"),
            ... ]
            >>> bundle = librarian.fetch_multiple(requests)
            >>> print(bundle.to_json())
        """
        all_entries = []

        for request in requests:
            entries = self.fetch_entry(request.word)
            all_entries.extend(entries)

        return LexiconBundle(
            entries=all_entries,
            requests=requests
        )

    def fetch_from_json(self, json_str: str) -> LexiconBundle:
        """
        Fetch lexicon entries from JSON request.

        Args:
            json_str: JSON string with list of word requests
                Format: {"words": [{"word": "שָׁמַר", "notes": "..."}]}

        Returns:
            LexiconBundle with all fetched entries

        Example:
            >>> json_request = '''
            ... {
            ...   "words": [
            ...     {"word": "שָׁמַר", "notes": "guard/keep"},
            ...     {"word": "צֶדֶק", "notes": "righteousness"}
            ...   ]
            ... }
            ... '''
            >>> bundle = librarian.fetch_from_json(json_request)
        """
        data = json.loads(json_str)

        requests = []
        for item in data.get('words', []):
            if isinstance(item, str):
                requests.append(LexiconRequest(word=item))
            elif isinstance(item, dict):
                requests.append(LexiconRequest.from_dict(item))

        return self.fetch_multiple(requests)


def main():
    """Command-line interface for BDB Librarian."""
    import argparse

    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Fetch Hebrew lexicon entries from BDB via Sefaria'
    )
    parser.add_argument('word', type=str, nargs='?',
                       help='Hebrew word to look up')
    parser.add_argument('--json', type=str,
                       help='JSON file with multiple word requests')
    parser.add_argument('--output', type=str,
                       help='Output file for results (default: stdout)')

    args = parser.parse_args()

    librarian = BDBLibrarian()

    if args.json:
        # Load requests from JSON file
        with open(args.json, 'r', encoding='utf-8') as f:
            json_str = f.read()
        bundle = librarian.fetch_from_json(json_str)

        # Output results
        output = bundle.to_json()
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Results written to {args.output}")
        else:
            print(output)

    elif args.word:
        # Single word lookup
        entries = librarian.fetch_entry(args.word)

        if not entries:
            print(f"No lexicon entries found for '{args.word}'")
            return

        print(f"\n=== Lexicon Entries for {args.word} ===\n")
        for i, entry in enumerate(entries, 1):
            print(f"{i}. {entry.lexicon_name}")
            print(f"   {entry.entry_text}")
            if entry.url:
                print(f"   URL: {entry.url}")
            print()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
