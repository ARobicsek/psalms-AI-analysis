"""
Commentary Librarian Agent

Fetches traditional Jewish commentaries on Psalms verses from Sefaria API.
Provides classical interpretations to put AI analysis in dialogue with established scholarship.

Supported Commentators:
- Rashi (Rabbi Shlomo Yitzchaki, 11th century, France)
- Ibn Ezra (Rabbi Abraham ibn Ezra, 12th century, Spain)
- Radak (Rabbi David Kimchi, 12th-13th century, Provence)
- Metzudat David (18th century, Italy)
- Malbim (Rabbi Meir Leibush ben Yehiel Michel Wisser, 19th century, Ukraine)
- Meiri (Rabbi Menachem ben Solomon Meiri, 13th-14th century, Provence)

Usage:
    from src.agents.commentary_librarian import CommentaryLibrarian

    librarian = CommentaryLibrarian()

    # Fetch all available commentaries for a verse
    commentaries = librarian.fetch_commentaries(
        psalm=23,
        verse=1,
        commentators=['Rashi', 'Ibn Ezra']
    )

    # Process multiple verse requests
    requests = [
        {"psalm": 23, "verse": 1, "reason": "Rare metaphor"},
        {"psalm": 23, "verse": 4, "reason": "Perplexing imagery"}
    ]
    bundle = librarian.process_requests(requests)
"""

import requests
import time
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from html import unescape
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
SEFARIA_API_BASE = "https://www.sefaria.org/api"
RATE_LIMIT_DELAY = 0.5  # seconds between requests
REQUEST_TIMEOUT = 10  # seconds

# Supported commentators (Sefaria text names)
COMMENTATORS = {
    "Rashi": "Rashi on Psalms",
    "Ibn Ezra": "Ibn Ezra on Psalms",
    "Radak": "Radak on Psalms",
    "Metzudat David": "Metzudat David on Psalms",
    "Malbim": "Malbim on Psalms",
    "Meiri": "Meiri on Psalms"
}


def clean_html_text(text: str) -> str:
    """
    Remove HTML markup from commentary text.

    Args:
        text: Raw text with HTML tags and entities

    Returns:
        Clean text with HTML removed
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
class CommentaryEntry:
    """Represents a single commentary on a verse."""
    commentator: str          # Name (e.g., "Rashi")
    psalm: int                # Psalm number
    verse: int                # Verse number
    hebrew: str               # Hebrew commentary text
    english: str              # English translation
    reference: str            # Sefaria reference (e.g., "Rashi on Psalms 23:1:1")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "commentator": self.commentator,
            "psalm": self.psalm,
            "verse": self.verse,
            "hebrew": self.hebrew,
            "english": self.english,
            "reference": self.reference
        }


@dataclass
class CommentaryBundle:
    """Bundle of commentaries for a verse."""
    psalm: int
    verse: int
    reason: str                           # Why this verse needs commentary
    commentaries: List[CommentaryEntry]   # All fetched commentaries

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "psalm": self.psalm,
            "verse": self.verse,
            "reason": self.reason,
            "commentaries": [c.to_dict() for c in self.commentaries]
        }

    def to_markdown(self) -> str:
        """Format as markdown for LLM consumption."""
        lines = [
            f"### Psalms {self.psalm}:{self.verse}",
            f"**Reason for commentary request**: {self.reason}",
            ""
        ]

        for comm in self.commentaries:
            lines.append(f"#### {comm.commentator}")
            lines.append(f"**Hebrew**: {comm.hebrew[:300]}..." if len(comm.hebrew) > 300 else f"**Hebrew**: {comm.hebrew}")
            lines.append(f"**English**: {comm.english[:300]}..." if len(comm.english) > 300 else f"**English**: {comm.english}")
            lines.append("")

        return "\n".join(lines)


class CommentaryLibrarian:
    """
    Fetches traditional Jewish commentaries on Psalms verses.

    This agent is NOT an LLM - it's a pure Python script that queries Sefaria API.
    """

    def __init__(self, rate_limit_delay: float = RATE_LIMIT_DELAY):
        """
        Initialize Commentary Librarian.

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
        """
        url = f"{SEFARIA_API_BASE}/{endpoint}"

        self._wait_for_rate_limit()
        logger.debug(f"Request to {endpoint}")

        response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        return response.json()

    def fetch_commentary(self,
                         psalm: int,
                         verse: int,
                         commentator: str = "Rashi") -> Optional[CommentaryEntry]:
        """
        Fetch a single commentary on a specific verse.

        Args:
            psalm: Psalm number (1-150)
            verse: Verse number
            commentator: Commentator name (default: "Rashi")

        Returns:
            CommentaryEntry if found, None if not available
        """
        if commentator not in COMMENTATORS:
            logger.warning(f"Unknown commentator: {commentator}")
            return None

        commentary_text = COMMENTATORS[commentator]
        ref = f"{commentary_text}.{psalm}.{verse}"

        try:
            logger.info(f"Fetching {commentator} on Psalms {psalm}:{verse}...")

            data = self._make_request(f"texts/{ref}", params={'context': 0})

            # Extract text (may be nested array)
            hebrew = data.get('he', [])
            english = data.get('text', [])

            # Handle nested structure
            if isinstance(hebrew, list):
                hebrew = ' | '.join([clean_html_text(h) for h in hebrew if h])
            else:
                hebrew = clean_html_text(hebrew)

            if isinstance(english, list):
                english = ' | '.join([clean_html_text(e) for e in english if e])
            else:
                english = clean_html_text(english)

            if not hebrew and not english:
                logger.info(f"No {commentator} commentary found for Psalms {psalm}:{verse}")
                return None

            entry = CommentaryEntry(
                commentator=commentator,
                psalm=psalm,
                verse=verse,
                hebrew=hebrew,
                english=english,
                reference=data.get('ref', ref)
            )

            logger.info(f"Successfully fetched {commentator} commentary ({len(hebrew)} Hebrew chars)")
            return entry

        except requests.RequestException as e:
            logger.warning(f"Error fetching {commentator} on Psalms {psalm}:{verse}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching commentary: {e}")
            return None

    def fetch_commentaries(self,
                          psalm: int,
                          verse: int,
                          commentators: Optional[List[str]] = None) -> List[CommentaryEntry]:
        """
        Fetch multiple commentaries on a verse.

        Args:
            psalm: Psalm number (1-150)
            verse: Verse number
            commentators: List of commentator names (default: all available)

        Returns:
            List of CommentaryEntry objects (may be empty)
        """
        if commentators is None:
            commentators = list(COMMENTATORS.keys())

        entries = []
        for commentator in commentators:
            entry = self.fetch_commentary(psalm, verse, commentator)
            if entry:
                entries.append(entry)

        return entries

    def process_requests(self,
                        requests: List[Dict[str, Any]],
                        commentators: Optional[List[str]] = None) -> List[CommentaryBundle]:
        """
        Process multiple commentary requests.

        Args:
            requests: List of request dicts with keys:
                     - psalm (int): Psalm number
                     - verse (int): Verse number
                     - reason (str): Why this verse needs commentary
            commentators: List of commentator names (default: all 6 available commentators)

        Returns:
            List of CommentaryBundle objects
        """
        if commentators is None:
            # Default to all available commentators for comprehensive coverage
            commentators = list(COMMENTATORS.keys())

        logger.info(f"Processing {len(requests)} commentary requests...")

        bundles = []
        for req in requests:
            psalm = req.get('psalm')
            verse = req.get('verse')
            reason = req.get('reason', 'Requested by Scholar-Researcher')

            if not psalm or not verse:
                logger.warning(f"Invalid request (missing psalm or verse): {req}")
                continue

            commentaries = self.fetch_commentaries(psalm, verse, commentators)

            bundle = CommentaryBundle(
                psalm=psalm,
                verse=verse,
                reason=reason,
                commentaries=commentaries
            )
            bundles.append(bundle)

        logger.info(f"Fetched {sum(len(b.commentaries) for b in bundles)} commentaries total")
        return bundles

    def format_bundle_as_markdown(self, bundles: List[CommentaryBundle]) -> str:
        """
        Format commentary bundles as markdown for LLM consumption.

        Args:
            bundles: List of CommentaryBundle objects

        Returns:
            Formatted markdown string
        """
        if not bundles:
            return "No commentaries requested.\n"

        lines = [
            "# Traditional Commentaries",
            "",
            "The following commentaries provide classical interpretations of verses "
            "identified by the Scholar-Researcher as particularly interesting or perplexing.",
            ""
        ]

        for bundle in bundles:
            lines.append(bundle.to_markdown())

        return "\n".join(lines)


def main():
    """Command-line interface for testing the Commentary Librarian."""
    import argparse
    import sys
    import json

    # Ensure UTF-8 encoding for Hebrew text on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='Fetch traditional commentaries on Psalms verses')
    parser.add_argument('--psalm', type=int, required=True, help='Psalm number (1-150)')
    parser.add_argument('--verse', type=int, required=True, help='Verse number')
    parser.add_argument('--commentator', type=str, default='Rashi',
                       choices=list(COMMENTATORS.keys()),
                       help='Commentator name')
    parser.add_argument('--all', action='store_true',
                       help='Fetch all available commentators')
    parser.add_argument('--format', choices=['json', 'markdown'], default='markdown',
                       help='Output format')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    librarian = CommentaryLibrarian()

    if args.all:
        commentaries = librarian.fetch_commentaries(args.psalm, args.verse)
    else:
        commentary = librarian.fetch_commentary(args.psalm, args.verse, args.commentator)
        commentaries = [commentary] if commentary else []

    if not commentaries:
        print(f"No commentaries found for Psalms {args.psalm}:{args.verse}")
        return

    if args.format == 'json':
        print(json.dumps([c.to_dict() for c in commentaries], indent=2, ensure_ascii=False))
    else:
        bundle = CommentaryBundle(
            psalm=args.psalm,
            verse=args.verse,
            reason="Command-line test",
            commentaries=commentaries
        )
        print(bundle.to_markdown())


if __name__ == '__main__':
    main()
