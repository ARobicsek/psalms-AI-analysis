"""
Sefaria API Client

Fetches biblical texts and lexicon entries from Sefaria's public API.
API Documentation: https://developers.sefaria.org/

Key Features:
- Fetch Psalm text with Hebrew (vocalized/unvocalized) and English
- Fetch BDB lexicon entries
- Rate limiting (respectful API usage)
- Error handling and retry logic
- Caching for repeated requests
"""

import requests
import time
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from functools import lru_cache
from html import unescape
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
SEFARIA_API_BASE = "https://www.sefaria.org/api"
RATE_LIMIT_DELAY = 0.5  # seconds between requests
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 3


def clean_html_text(text: str) -> str:
    """
    Remove HTML markup from Sefaria text.

    Args:
        text: Raw text with HTML tags and entities

    Returns:
        Clean text with HTML removed

    Example:
        >>> clean_html_text("אַ֥שְֽׁרֵי<span>־</span>הָאִ֗ישׁ")
        'אַ֥שְֽׁרֵי־הָאִ֗ישׁ'
    """
    if not text:
        return text

    # Remove HTML tags (but keep their content)
    text = re.sub(r'<[^>]+>', '', text)

    # Convert HTML entities
    text = unescape(text)

    # Clean up extra whitespace
    text = ' '.join(text.split())

    return text


@dataclass
class Verse:
    """Represents a single verse from any biblical book."""
    book: str
    chapter: int
    verse: int
    hebrew: str
    english: str
    reference: str  # e.g., "Genesis 1:1" or "Psalms 23:1"


@dataclass
class PsalmVerse(Verse):
    """Represents a single verse from a Psalm (for backward compatibility)."""
    def __init__(self, chapter: int, verse: int, hebrew: str, english: str, reference: str):
        super().__init__(
            book="Psalms",
            chapter=chapter,
            verse=verse,
            hebrew=hebrew,
            english=english,
            reference=reference
        )


@dataclass
class BookText:
    """Complete text of a biblical book chapter with metadata."""
    book: str
    chapter: int
    title_hebrew: str
    title_english: str
    verses: List[Verse]
    verse_count: int

    def __repr__(self):
        return f"BookText(book={self.book}, chapter={self.chapter}, verses={self.verse_count})"


@dataclass
class PsalmText(BookText):
    """Complete text of a Psalm (for backward compatibility)."""
    def __init__(self, chapter: int, title_hebrew: str, title_english: str,
                 verses: List[PsalmVerse], verse_count: int):
        super().__init__(
            book="Psalms",
            chapter=chapter,
            title_hebrew=title_hebrew,
            title_english=title_english,
            verses=verses,
            verse_count=verse_count
        )
        # Store original chapter for backward compatibility
        self.chapter = chapter


@dataclass
class LexiconEntry:
    """BDB lexicon entry for a Hebrew word."""
    word: str
    headword: str
    definition: str
    raw_data: Dict[str, Any]  # Full API response for advanced use


class SefariaClient:
    """Client for interacting with Sefaria API."""

    def __init__(self, rate_limit_delay: float = RATE_LIMIT_DELAY):
        """
        Initialize Sefaria API client.

        Args:
            rate_limit_delay: Seconds to wait between API requests
        """
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Psalms-AI-Commentary/1.0 (Educational Research)'
        })

    def _wait_for_rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a rate-limited request to Sefaria API.

        Args:
            endpoint: API endpoint (relative to base URL)
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.RequestException: If request fails after retries
        """
        url = f"{SEFARIA_API_BASE}/{endpoint}"

        for attempt in range(MAX_RETRIES):
            try:
                self._wait_for_rate_limit()

                logger.debug(f"Request to {endpoint} (attempt {attempt + 1}/{MAX_RETRIES})")
                response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()

                return response.json()

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}/{MAX_RETRIES}")
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error on attempt {attempt + 1}/{MAX_RETRIES}: {e}")
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(2 ** attempt)

    def fetch_psalm(self, chapter: int, include_commentary: bool = False) -> PsalmText:
        """
        Fetch a complete Psalm with Hebrew and English text.

        Args:
            chapter: Psalm number (1-150)
            include_commentary: Whether to fetch commentary (not implemented yet)

        Returns:
            PsalmText object with all verses

        Raises:
            ValueError: If chapter number is invalid
            requests.RequestException: If API request fails
        """
        if not 1 <= chapter <= 150:
            raise ValueError(f"Invalid Psalm number: {chapter}. Must be 1-150.")

        logger.info(f"Fetching Psalm {chapter} from Sefaria...")

        # Fetch Hebrew text
        ref = f"Psalms.{chapter}"
        data = self._make_request(f"texts/{ref}", params={
            'context': 0,
            'commentary': 0,
            'pad': 0
        })

        # Parse response
        hebrew_verses = data.get('he', [])
        english_verses = data.get('text', [])

        # Handle nested structure (Sefaria sometimes returns nested arrays)
        if hebrew_verses and isinstance(hebrew_verses[0], list):
            hebrew_verses = [v for sublist in hebrew_verses for v in sublist]
        if english_verses and isinstance(english_verses[0], list):
            english_verses = [v for sublist in english_verses for v in sublist]

        # Create verse objects
        verses = []
        for i, (heb, eng) in enumerate(zip(hebrew_verses, english_verses), start=1):
            verse = PsalmVerse(
                chapter=chapter,
                verse=i,
                hebrew=clean_html_text(heb),
                english=clean_html_text(eng),
                reference=f"Psalms {chapter}:{i}"
            )
            verses.append(verse)

        psalm = PsalmText(
            chapter=chapter,
            title_hebrew=data.get('heTitle', f'תהלים {chapter}'),
            title_english=data.get('title', f'Psalms {chapter}'),
            verses=verses,
            verse_count=len(verses)
        )

        logger.info(f"Successfully fetched Psalm {chapter} ({psalm.verse_count} verses)")
        return psalm

    def fetch_verse(self, chapter: int, verse: int) -> PsalmVerse:
        """
        Fetch a single verse from a Psalm.

        Args:
            chapter: Psalm number (1-150)
            verse: Verse number

        Returns:
            PsalmVerse object

        Raises:
            ValueError: If reference is invalid
            requests.RequestException: If API request fails
        """
        if not 1 <= chapter <= 150:
            raise ValueError(f"Invalid Psalm number: {chapter}")

        logger.info(f"Fetching Psalms {chapter}:{verse}...")

        ref = f"Psalms.{chapter}.{verse}"
        data = self._make_request(f"texts/{ref}", params={
            'context': 0,
            'commentary': 0
        })

        # Extract text (handle possible nested structure)
        hebrew = data.get('he', [''])[0] if isinstance(data.get('he'), list) else data.get('he', '')
        english = data.get('text', [''])[0] if isinstance(data.get('text'), list) else data.get('text', '')

        return PsalmVerse(
            chapter=chapter,
            verse=verse,
            hebrew=clean_html_text(hebrew),
            english=clean_html_text(english),
            reference=f"Psalms {chapter}:{verse}"
        )

    @lru_cache(maxsize=1000)
    def fetch_lexicon_entry(self, word: str, lexicon: str = "scholarly") -> List[LexiconEntry]:
        """
        Fetch lexicon entries for a Hebrew word from multiple lexicons.

        Args:
            word: Hebrew word (can be vocalized or unvocalized)
            lexicon: Lexicon filter (default: "scholarly")
                     - "scholarly": BDB Dictionary + Klein Dictionary (rich academic content)
                     - "BDB Dictionary": Only BDB (most comprehensive)
                     - "Klein Dictionary": Only Klein (etymological)
                     - "Jastrow Dictionary": Talmudic Hebrew
                     - "all": All available lexicons

        Returns:
            List of LexiconEntry objects (may be from multiple lexicons)
            Empty list if no entries found.

        Note:
            Results are cached to avoid repeated lookups of same words.
            Default "scholarly" filter returns BDB Dictionary + Klein for maximum
            semantic/etymological richness without biblical usage examples
            (which are provided by Concordance Librarian).
        """
        logger.info(f"Fetching lexicon entries for: {word}")

        try:
            # Sefaria lexicon lookup endpoint
            # Format: /api/words/{word}?lookup_ref=Psalms.1.1
            # Returns a LIST of entries from different lexicons
            data = self._make_request(f"words/{word}", params={
                'lookup_ref': 'Psalms.1.1'  # Reference context for disambiguation
            })

            if not isinstance(data, list):
                logger.warning(f"Unexpected response format for {word}: {type(data)}")
                return []

            entries = []

            # Define scholarly lexicon set
            scholarly_lexicons = {"BDB Dictionary", "Klein Dictionary"}

            # Parse each lexicon entry from response
            for entry_data in data:
                lexicon_name = entry_data.get('parent_lexicon', 'Unknown')

                # Filter by requested lexicon
                if lexicon == "scholarly":
                    if lexicon_name not in scholarly_lexicons:
                        continue
                elif lexicon != "all" and lexicon_name != lexicon:
                    continue

                # Extract definition from nested content structure
                content = entry_data.get('content', {})
                senses = content.get('senses', [])

                # Build definition text from senses
                definition = self._extract_definition_from_senses(senses)

                if not definition:
                    definition = 'No definition available'

                # Strip HTML tags for clean text (BDB Dictionary has extensive markup)
                definition = clean_html_text(definition)

                entry = LexiconEntry(
                    word=word,
                    headword=entry_data.get('headword', word),
                    definition=definition,
                    raw_data=entry_data
                )
                entries.append(entry)

            if not entries:
                logger.warning(f"No {lexicon} entries found for: {word}")

            return entries

        except requests.RequestException as e:
            logger.error(f"Error fetching lexicon entry for {word}: {e}")
            return []

    def _extract_definition_from_senses(self, senses: List[Dict], depth: int = 0) -> str:
        """
        Recursively extract definition text from nested senses structure.

        Args:
            senses: List of sense dictionaries (possibly nested)
            depth: Current recursion depth (for indentation)

        Returns:
            Formatted definition string
        """
        if not senses:
            return ""

        definitions = []
        for sense in senses:
            if isinstance(sense, dict):
                # Get direct definition if present
                if 'definition' in sense:
                    indent = "  " * depth
                    definitions.append(f"{indent}{sense['definition']}")

                # Recurse into nested senses
                if 'senses' in sense and isinstance(sense['senses'], list):
                    nested_def = self._extract_definition_from_senses(sense['senses'], depth + 1)
                    if nested_def:
                        definitions.append(nested_def)

        return "\n".join(definitions)

    def fetch_multiple_psalms(self, chapters: List[int]) -> List[PsalmText]:
        """
        Fetch multiple Psalms efficiently.

        Args:
            chapters: List of Psalm numbers to fetch

        Returns:
            List of PsalmText objects
        """
        logger.info(f"Fetching {len(chapters)} Psalms...")
        psalms = []

        for i, chapter in enumerate(chapters, 1):
            logger.info(f"Progress: {i}/{len(chapters)}")
            psalm = self.fetch_psalm(chapter)
            psalms.append(psalm)

        return psalms

    def get_psalm_metadata(self, chapter: int) -> Dict[str, Any]:
        """
        Fetch metadata about a Psalm (links, categories, etc.).

        Args:
            chapter: Psalm number

        Returns:
            Metadata dictionary
        """
        ref = f"Psalms.{chapter}"
        return self._make_request(f"index/{ref}")

    def fetch_book_chapter(self, book: str, chapter: int) -> BookText:
        """
        Fetch a complete chapter from any biblical book.

        Args:
            book: Book name (e.g., "Genesis", "Isaiah", "Psalms")
            chapter: Chapter number

        Returns:
            BookText object with all verses

        Raises:
            requests.RequestException: If API request fails
        """
        logger.info(f"Fetching {book} {chapter} from Sefaria...")

        # Fetch text
        ref = f"{book}.{chapter}"
        data = self._make_request(f"texts/{ref}", params={
            'context': 0,
            'commentary': 0,
            'pad': 0
        })

        # Parse response
        hebrew_verses = data.get('he', [])
        english_verses = data.get('text', [])

        # Handle nested structure (Sefaria sometimes returns nested arrays)
        if hebrew_verses and isinstance(hebrew_verses[0], list):
            hebrew_verses = [v for sublist in hebrew_verses for v in sublist]
        if english_verses and isinstance(english_verses[0], list):
            english_verses = [v for sublist in english_verses for v in sublist]

        # Create verse objects
        verses = []
        for i, (heb, eng) in enumerate(zip(hebrew_verses, english_verses), start=1):
            verse = Verse(
                book=book,
                chapter=chapter,
                verse=i,
                hebrew=clean_html_text(heb) if heb else "",
                english=clean_html_text(eng) if eng else "",
                reference=f"{book} {chapter}:{i}"
            )
            verses.append(verse)

        book_text = BookText(
            book=book,
            chapter=chapter,
            title_hebrew=data.get('heTitle', f'{book} {chapter}'),
            title_english=data.get('title', f'{book} {chapter}'),
            verses=verses,
            verse_count=len(verses)
        )

        logger.info(f"Successfully fetched {book} {chapter} ({book_text.verse_count} verses)")
        return book_text

    def get_book_metadata(self, book: str) -> Dict[str, Any]:
        """
        Fetch metadata about a book (chapter count, categories, etc.).

        Args:
            book: Book name (e.g., "Genesis", "Isaiah")

        Returns:
            Metadata dictionary including chapter count
        """
        return self._make_request(f"index/{book}")


def main():
    """Command-line interface for testing the Sefaria client."""
    import argparse
    import sys

    # Ensure UTF-8 encoding for Hebrew text on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='Fetch Psalms from Sefaria API')
    parser.add_argument('--psalm', type=int, help='Psalm number to fetch (1-150)')
    parser.add_argument('--verse', type=int, help='Specific verse number (optional)')
    parser.add_argument('--word', type=str, help='Hebrew word for lexicon lookup')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    client = SefariaClient()

    if args.word:
        # Lexicon lookup
        entries = client.fetch_lexicon_entry(args.word, lexicon="all")
        if entries:
            print(f"\n=== Lexicon Entries for {args.word} ===\n")
            for entry in entries:
                print(f"--- {entry.raw_data.get('parent_lexicon', 'Unknown')} ---")
                print(f"Headword: {entry.headword}")
                print(f"Definition:\n{entry.definition[:500]}...")
                print()
        else:
            print(f"No entry found for: {args.word}")

    elif args.psalm:
        if args.verse:
            # Single verse
            verse = client.fetch_verse(args.psalm, args.verse)
            print(f"\n=== {verse.reference} ===")
            print(f"Hebrew: {verse.hebrew}")
            print(f"English: {verse.english}")
        else:
            # Full psalm
            psalm = client.fetch_psalm(args.psalm)
            print(f"\n=== {psalm.title_english} ({psalm.title_hebrew}) ===")
            print(f"Verses: {psalm.verse_count}\n")

            for verse in psalm.verses[:5]:  # Show first 5 verses
                print(f"{verse.reference}")
                print(f"  HE: {verse.hebrew}")
                print(f"  EN: {verse.english}")
                print()

            if psalm.verse_count > 5:
                print(f"... ({psalm.verse_count - 5} more verses)")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
