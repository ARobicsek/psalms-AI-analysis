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
BOLLS_API_BASE = "https://bolls.life"  # For LXX (Septuagint) text
RATE_LIMIT_DELAY = 0.5  # seconds between requests
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 3

# LXX Psalm Numbering: LXX Psalms 9-147 differ from MT
# LXX 9-10 = MT 9:1-20, 10:1-18 (combined)
# LXX 11-113 = MT 10-112 (one less)
# LXX 114-115 = MT 114-115 (combined in some traditions)
# LXX 116 = MT 116:1-9
# LXX 117 = MT 116:10-19
# LXX 118-146 = MT 117-145 (one more)
# LXX 147 = MT 146-147 (combined)
def get_lxx_psalm_number(mt_psalm: int) -> int:
    """Convert Masoretic Text psalm number to LXX psalm number."""
    if mt_psalm <= 8:
        return mt_psalm
    elif mt_psalm == 9:
        return 9  # MT 9 -> LXX 9 (part 1)
    elif 10 <= mt_psalm <= 112:
        return mt_psalm - 1  # Off by one
    elif 113 <= mt_psalm <= 115:
        return mt_psalm - 1
    elif mt_psalm == 116:
        return 115  # Split in LXX (115+116)
    elif 117 <= mt_psalm <= 145:
        return mt_psalm - 1
    elif mt_psalm == 146:
        return 146  # MT 146 -> LXX 146 (part 1)
    elif mt_psalm == 147:
        return 146  # MT 147 -> LXX 146 (part 2) + LXX 147
    elif mt_psalm >= 148:
        return mt_psalm - 1
    return mt_psalm


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


def strip_sefaria_footnotes(text: str) -> str:
    """
    Remove Sefaria footnote markers and footnote text from English translations.

    Sefaria embeds footnotes using two patterns:
    1. HTML-style: <sup class="footnote-marker">a</sup><i class="footnote">Footnote text here</i>
    2. Simple text markers: word.-a, phrase,-b, etc. (hyphen + lowercase letter)

    This function removes both types of markers and footnote content, leaving
    only the main translation text for reader-friendly output.

    Args:
        text: English text with embedded Sefaria footnotes

    Returns:
        Clean text with footnotes removed

    Examples:
        >>> text = 'May He receive the tokens<sup class="footnote-marker">a</sup><i class="footnote">Reference to azkara</i> of all'
        >>> strip_sefaria_footnotes(text)
        'May He receive the tokens of all'

        >>> text = 'I have fathered you this day.-b'
        >>> strip_sefaria_footnotes(text)
        'I have fathered you this day.'

        >>> text = 'pay homage in good faith,-d lest He be angered'
        >>> strip_sefaria_footnotes(text)
        'pay homage in good faith, lest He be angered'
    """
    if not text:
        return text

    # Remove footnote markers: <sup class="footnote-marker">x</sup>
    text = re.sub(r'<sup class="footnote-marker">[^<]+</sup>', '', text)

    # Remove footnote content: <i class="footnote">...</i>
    text = re.sub(r'<i class="footnote">[^<]*</i>', '', text)

    # Also handle any remaining <sup> or <i> tags (edge cases)
    text = re.sub(r'</?sup[^>]*>', '', text)
    text = re.sub(r'</?i[^>]*>', '', text, flags=re.IGNORECASE)

    # Remove <br> tags (line breaks)
    text = re.sub(r'<br\s*/?>', '\n', text)

    # Remove any other remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Convert HTML entities
    text = unescape(text)

    # Remove simple text-based footnote indicators (e.g., .-a, ,-b, -c)
    # Pattern: optional punctuation (. , ; :) followed by hyphen and lowercase letter
    # This matches: "day.-b", "faith,-d", "word-a", etc.
    text = re.sub(r'([.,;:])?\-[a-z](?=\s|$)', r'\1', text)

    # Clean up extra whitespace, but preserve intentional line breaks
    lines = text.split('\n')
    lines = [' '.join(line.split()) for line in lines]
    text = '\n'.join(lines)

    # Final cleanup - remove multiple consecutive newlines
    text = re.sub(r'\n\n+', '\n', text)

    return text.strip()


@dataclass
class Verse:
    """Represents a single verse from any biblical book."""
    book: str
    chapter: int
    verse: int
    hebrew: str
    english: str
    reference: str  # e.g., "Genesis 1:1" or "Psalms 23:1"
    lxx: Optional[str] = None  # Septuagint (Greek) text, if available


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

    def fetch_psalm(self, chapter: int, include_commentary: bool = False, include_lxx: bool = True) -> PsalmText:
        """
        Fetch a complete Psalm with Hebrew and English text.

        Args:
            chapter: Psalm number (1-150)
            include_commentary: Whether to fetch commentary (not implemented yet)
            include_lxx: Whether to fetch Septuagint (LXX) Greek text (default: True)

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

        # Fetch LXX (Septuagint) text if requested
        lxx_verses = []
        if include_lxx:
            lxx_verses = self.fetch_lxx_psalm(chapter)

        # Create verse objects
        verses = []
        for i, (heb, eng) in enumerate(zip(hebrew_verses, english_verses), start=1):
            # Get corresponding LXX verse if available
            lxx_text = lxx_verses[i - 1] if i <= len(lxx_verses) else None

            verse = PsalmVerse(
                chapter=chapter,
                verse=i,
                hebrew=clean_html_text(heb),
                # Use strip_sefaria_footnotes for English to remove footnote content
                # while preserving the main translation text
                english=strip_sefaria_footnotes(eng),
                reference=f"Psalms {chapter}:{i}"
            )
            # Add LXX text to verse
            verse.lxx = lxx_text
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
            english=strip_sefaria_footnotes(english),
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
                english=strip_sefaria_footnotes(eng) if eng else "",
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

    def fetch_lxx_psalm(self, chapter: int) -> List[str]:
        """
        Fetch Septuagint (Greek) text for a Psalm from Bolls.life API.

        The LXX uses different numbering than the Masoretic Text (MT).
        This method handles the conversion automatically.

        Args:
            chapter: Psalm number in Masoretic Text numbering (1-150)

        Returns:
            List of Greek verses (LXX text)
            Empty list if not available

        Note:
            - Uses Bolls.life API as Sefaria doesn't include LXX
            - Psalm numbering: LXX Psalms 10-146 are typically off by one
              (e.g., MT Psalm 23 = LXX Psalm 22)
            - For analysis purposes, this provides Vorlage comparison
        """
        try:
            # Convert MT psalm number to LXX numbering
            lxx_number = get_lxx_psalm_number(chapter)

            logger.info(f"Fetching LXX Psalm {lxx_number} (MT Psalm {chapter}) from Bolls.life...")

            # Bolls.life API: /get-chapter/LXX/{book_id}/{chapter}/
            # Book ID 19 = Psalms in standard biblical ordering
            url = f"{BOLLS_API_BASE}/get-chapter/LXX/19/{lxx_number}/"

            self._wait_for_rate_limit()
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            data = response.json()

            # Bolls.life returns list of verse objects: [{"pk": ..., "verse": 1, "text": "..."}]
            if isinstance(data, list):
                lxx_verses = [verse_obj.get('text', '') for verse_obj in data]
                logger.info(f"Successfully fetched LXX Psalm {lxx_number} ({len(lxx_verses)} verses)")
                return lxx_verses
            else:
                logger.warning(f"Unexpected LXX response format for Psalm {chapter}")
                return []

        except requests.RequestException as e:
            logger.warning(f"Could not fetch LXX for Psalm {chapter}: {e}")
            return []
        except Exception as e:
            logger.warning(f"Error processing LXX for Psalm {chapter}: {e}")
            return []


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
