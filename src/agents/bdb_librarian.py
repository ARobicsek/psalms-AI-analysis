"""
BDB Librarian Agent

Fetches Hebrew lexicon entries from scholarly lexicons (BDB Dictionary + Klein Dictionary)
via the Sefaria API. This is a pure Python data retriever (not an LLM agent).

The BDB Librarian provides:
- Word definitions and semantic ranges (BDB Dictionary)
- Etymology and linguistic notes (Klein Dictionary)
- Morphological information
- Cross-references to related words

Note: Biblical usage examples are intentionally NOT extracted here.
The Concordance Librarian handles all biblical citations and usage patterns.
This maintains clean separation of responsibilities.
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
    """
    A single lexicon entry from scholarly lexicons (BDB Dictionary or Klein Dictionary).

    For homographs (words with same consonants but different meanings),
    multiple entries will be returned with disambiguation metadata:
    - headword: Vocalized form (e.g., רַע vs רָעָה)
    - strong_number: Unique identifier (e.g., 7451 vs 7462)
    - transliteration: Pronunciation guide (e.g., raʻ vs râʻâh)
    - morphology: Part of speech (e.g., "adj.", "m.n.", "v.")
    - etymology_notes: Etymology and linguistic notes (Klein Dictionary)
    - derivatives: Related words and derivatives (Klein Dictionary)

    Note: Biblical usage examples are NOT included here.
    Use Concordance Librarian for biblical citations and usage patterns.
    """
    word: str
    lexicon_name: str
    entry_text: str
    url: Optional[str] = None
    # Disambiguation metadata for homographs
    headword: Optional[str] = None  # Vocalized form (רַע, רָעָה, etc.)
    strong_number: Optional[str] = None  # Strong's number (7451, 7462, etc.)
    transliteration: Optional[str] = None  # Pronunciation (raʻ, râʻâh, etc.)
    morphology: Optional[str] = None  # Part of speech (adj., m.n., v., etc.)
    # Klein-specific fields
    etymology_notes: Optional[str] = None  # Etymology (Klein)
    derivatives: Optional[str] = None  # Related words (Klein)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'word': self.word,
            'lexicon': self.lexicon_name,
            'entry': self.entry_text,
        }
        # Include optional disambiguation fields if present
        if self.headword:
            result['headword'] = self.headword
        if self.strong_number:
            result['strong_number'] = self.strong_number
        if self.transliteration:
            result['transliteration'] = self.transliteration
        if self.morphology:
            result['morphology'] = self.morphology
        if self.etymology_notes:
            result['etymology_notes'] = self.etymology_notes
        if self.derivatives:
            result['derivatives'] = self.derivatives
        if self.url:
            result['url'] = self.url
        return result


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

    def fetch_entry(self, word: str, lexicon: str = "scholarly") -> List[LexiconEntry]:
        """
        Fetch lexicon entry for a single Hebrew word.

        Args:
            word: Hebrew word to look up
            lexicon: Lexicon filter (default: "scholarly")
                     - "scholarly": BDB Dictionary + Klein Dictionary (recommended)
                     - "BDB Dictionary": Only BDB
                     - "Klein Dictionary": Only Klein
                     - "all": All available lexicons

        Returns:
            List of LexiconEntry objects (may be from multiple lexicons)

        Example:
            >>> librarian = BDBLibrarian()
            >>> entries = librarian.fetch_entry("אֶבְיוֹן")
            >>> for entry in entries:
            ...     print(f"{entry.lexicon_name}: {entry.entry_text[:100]}...")
            BDB Dictionary: adj. in want, needy, poor,—so, always abs., Dt 15:4 + 40 times...
            Klein Dictionary: needy, poor. [Prob. from אבה and orig. meaning 'desirous, longing'...]
        """
        entries = []

        try:
            # Fetch from Sefaria API (now returns list of LexiconEntry objects)
            sefaria_entries = self.client.fetch_lexicon_entry(word, lexicon=lexicon)

            # Convert SefariaClient.LexiconEntry to BDBLibrarian.LexiconEntry
            for sefaria_entry in sefaria_entries:
                # Extract morphology from content if available
                content = sefaria_entry.raw_data.get('content', {})
                morphology = content.get('morphology')

                # Extract Klein-specific fields (etymology notes and derivatives)
                raw_etymology = sefaria_entry.raw_data.get('notes', '')
                raw_derivatives = sefaria_entry.raw_data.get('derivatives', '')

                # Strip HTML from Klein fields
                import re
                def strip_html(text):
                    """Remove HTML tags from text."""
                    if not text:
                        return None
                    # Remove tags
                    text = re.sub(r'<[^>]+>', '', text)
                    # Clean whitespace
                    text = ' '.join(text.split())
                    return text if text else None

                etymology_notes = strip_html(raw_etymology)
                derivatives = strip_html(raw_derivatives)

                entry = LexiconEntry(
                    word=word,
                    lexicon_name=sefaria_entry.raw_data.get('parent_lexicon', 'Unknown'),
                    entry_text=sefaria_entry.definition,
                    url=sefaria_entry.raw_data.get('url'),
                    # Add disambiguation metadata for homographs
                    headword=sefaria_entry.raw_data.get('headword'),
                    strong_number=sefaria_entry.raw_data.get('strong_number'),
                    transliteration=sefaria_entry.raw_data.get('transliteration'),
                    morphology=morphology,
                    # Klein-specific fields
                    etymology_notes=etymology_notes,
                    derivatives=derivatives
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
        if len(entries) > 1:
            print(f"Note: Found {len(entries)} different meanings (homographs)")
            print()

        for i, entry in enumerate(entries, 1):
            print(f"{i}. {entry.lexicon_name}")

            # Show disambiguation metadata for homographs
            if entry.headword:
                print(f"   Vocalized: {entry.headword}")
            if entry.strong_number:
                print(f"   Strong's: {entry.strong_number}")
            if entry.transliteration:
                print(f"   Pronunciation: {entry.transliteration}")
            if entry.morphology:
                print(f"   Morphology: {entry.morphology}")

            print(f"   Definition: {entry.entry_text}")

            # Show Klein-specific fields
            if entry.etymology_notes:
                print(f"   Etymology: {entry.etymology_notes}")
            if entry.derivatives:
                print(f"   Derivatives: {entry.derivatives}")

            if entry.url:
                print(f"   URL: {entry.url}")
            print()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
