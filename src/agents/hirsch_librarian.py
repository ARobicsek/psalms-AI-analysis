"""
Hirsch Librarian Agent

Provides access to R. Samson Raphael Hirsch's 19th-century German commentary
on Psalms. Text extracted via OCR from "Hirsch on Tehilim" (1882).

About the Data:
- Source: R. Samson Raphael Hirsch's "Commentary on the Psalms" (German, 1882)
- Language: 19th-century scholarly German in Fraktur typeface
- Extraction: OCR using Tesseract with deu_frak language pack
- Format: Verse-by-verse commentary with Hebrew text, German analysis, and cross-references
- Author: R. Samson Raphael Hirsch (1808-1888), leader of German Orthodox Judaism

Usage:
    from src.agents.hirsch_librarian import HirschLibrarian

    librarian = HirschLibrarian()
    entries = librarian.get_psalm_commentary(psalm=1)
    markdown = librarian.format_for_research_bundle(entries, psalm=1)

Author: Claude Code (Session 70)
Date: 2025-11-06
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default path to Hirsch data file
DEFAULT_HIRSCH_JSON_PATH = Path(__file__).parent.parent.parent / "hirsch_on_psalms.json"


@dataclass
class HirschCommentary:
    """Represents Hirsch's commentary on a single verse."""
    psalm: int
    verse: int
    german_commentary: str
    hebrew_text: str
    cross_references: List[str]
    page_number: int
    confidence_score: float  # OCR confidence (0-100)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "psalm": self.psalm,
            "verse": self.verse,
            "german_commentary": self.german_commentary,
            "hebrew_text": self.hebrew_text,
            "cross_references": self.cross_references,
            "page_number": self.page_number,
            "confidence_score": self.confidence_score
        }


class HirschLibrarian:
    """
    Manages access to R. Samson Raphael Hirsch's Psalm commentaries.

    This agent loads the hirsch_on_psalms.json file (generated via OCR extraction)
    and provides methods to retrieve and format commentary for specific psalms.
    """

    def __init__(self, json_path: Optional[Path] = None):
        """
        Initialize Hirsch Librarian.

        Args:
            json_path: Path to hirsch_on_psalms.json (uses default if None)
        """
        self.json_path = json_path or DEFAULT_HIRSCH_JSON_PATH
        self.entries: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Load the Hirsch JSON data file."""
        if not self.json_path.exists():
            logger.warning(f"Hirsch data file not found at {self.json_path}")
            logger.info(
                "To generate this file, run: python scripts/extract_hirsch_pdf.py\n"
                "See docs/HIRSCH_OCR_RESEARCH.md for setup instructions."
            )
            return

        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle both direct list format and nested structure
            if isinstance(data, list):
                self.entries = data
            elif isinstance(data, dict) and 'verses' in data:
                self.entries = data['verses']
            else:
                logger.error(f"Unexpected JSON structure in {self.json_path}")
                self.entries = []

            logger.info(f"Loaded {len(self.entries)} Hirsch commentaries from {self.json_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Hirsch JSON file: {e}")
            self.entries = []
        except Exception as e:
            logger.error(f"Error loading Hirsch data: {e}")
            self.entries = []

    def get_psalm_commentary(self, psalm: int) -> List[HirschCommentary]:
        """
        Get all Hirsch commentaries for a specific psalm.

        Args:
            psalm: Psalm number (1-150)

        Returns:
            List of HirschCommentary objects, sorted by verse
        """
        commentaries = []

        for entry in self.entries:
            if entry.get('psalm') == psalm:
                commentaries.append(HirschCommentary(
                    psalm=entry['psalm'],
                    verse=entry['verse'],
                    german_commentary=entry.get('german_commentary', ''),
                    hebrew_text=entry.get('hebrew_text', ''),
                    cross_references=entry.get('cross_references', []),
                    page_number=entry.get('page_number', 0),
                    confidence_score=entry.get('confidence_score', 0.0)
                ))

        # Sort by verse number
        commentaries.sort(key=lambda c: c.verse)

        logger.info(f"Found {len(commentaries)} Hirsch commentaries for Psalm {psalm}")
        return commentaries

    def get_verse_commentary(self, psalm: int, verse: int) -> Optional[HirschCommentary]:
        """
        Get Hirsch's commentary on a specific verse.

        Args:
            psalm: Psalm number (1-150)
            verse: Verse number

        Returns:
            HirschCommentary object or None if not found
        """
        for entry in self.entries:
            if entry.get('psalm') == psalm and entry.get('verse') == verse:
                return HirschCommentary(
                    psalm=entry['psalm'],
                    verse=entry['verse'],
                    german_commentary=entry.get('german_commentary', ''),
                    hebrew_text=entry.get('hebrew_text', ''),
                    cross_references=entry.get('cross_references', []),
                    page_number=entry.get('page_number', 0),
                    confidence_score=entry.get('confidence_score', 0.0)
                )

        return None

    def get_available_psalms(self) -> List[int]:
        """
        Get list of psalms that have Hirsch commentary available.

        Returns:
            Sorted list of psalm numbers
        """
        psalms = set(entry.get('psalm') for entry in self.entries if 'psalm' in entry)
        return sorted(psalms)

    def format_for_research_bundle(self, commentaries: List[HirschCommentary], psalm: int) -> str:
        """
        Format Hirsch commentaries as Markdown for LLM consumption.

        Note: Includes warning that this is 19th-century German text
        requiring translation for English-speaking agents.

        Args:
            commentaries: List of HirschCommentary objects
            psalm: Psalm number for header

        Returns:
            Formatted Markdown string
        """
        if not commentaries:
            return ""

        lines = [
            f"## R. Samson Raphael Hirsch on Psalm {psalm}",
            "",
            "**About this source**: R. Samson Raphael Hirsch (1808-1888) was a German rabbi and one of the ",
            "foremost leaders of Orthodox Judaism in the 19th century. His commentary on Psalms, written in scholarly ",
            "German, combines traditional Jewish interpretation with philological analysis and philosophical insight. ",
            "Hirsch's approach emphasizes the ethical and moral dimensions of the Psalms while maintaining strict ",
            "adherence to Orthodox theology.",
            "",
            "**IMPORTANT - Language Note**: This commentary is in 19th-century German. When citing Hirsch's insights, ",
            "LLM agents should:",
            "1. Translate relevant passages to English for the reader",
            "2. Summarize key theological or philological points in English",
            "3. Note that German-reading scholars should consult the original for precision",
            "4. Be aware that some OCR errors may exist (confidence scores provided)",
            ""
        ]

        # Calculate average confidence
        avg_confidence = sum(c.confidence_score for c in commentaries) / len(commentaries) if commentaries else 0
        if avg_confidence > 0:
            lines.append(f"**OCR Quality**: Average confidence {avg_confidence:.1f}% for this psalm")
            lines.append("")

        # Format each verse commentary
        for comm in commentaries:
            lines.append(f"### Verse {comm.verse}")
            lines.append("")

            if comm.hebrew_text:
                lines.append(f"**Hebrew Text**: {comm.hebrew_text}")
                lines.append("")

            lines.append(f"**German Commentary** (Page {comm.page_number}):")
            lines.append(comm.german_commentary)
            lines.append("")

            if comm.cross_references:
                lines.append(f"**Biblical Cross-References**: {', '.join(comm.cross_references)}")
                lines.append("")

            if comm.confidence_score > 0:
                quality_note = "high quality" if comm.confidence_score >= 80 else "may contain OCR errors"
                lines.append(f"*OCR Confidence: {comm.confidence_score:.1f}% ({quality_note})*")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)


def main():
    """Test the Hirsch Librarian with a few psalm chapters."""
    librarian = HirschLibrarian()

    print("=" * 80)
    print("Testing Hirsch Librarian")
    print("=" * 80)

    # Check if data is available
    available_psalms = librarian.get_available_psalms()
    if not available_psalms:
        print("\nNo Hirsch commentary data available.")
        print("To extract commentary from PDF, run:")
        print("  python scripts/extract_hirsch_pdf.py")
        print("\nSee docs/HIRSCH_OCR_RESEARCH.md for setup instructions.")
        return

    print(f"\nAvailable psalms: {available_psalms[:10]}{'...' if len(available_psalms) > 10 else ''}")
    print(f"Total: {len(available_psalms)} psalms with commentary")

    # Test with first available psalm
    test_psalm = available_psalms[0]
    print(f"\n{'=' * 80}")
    print(f"Testing with Psalm {test_psalm}")
    print("=" * 80)

    commentaries = librarian.get_psalm_commentary(test_psalm)
    print(f"\nFound {len(commentaries)} verse commentaries for Psalm {test_psalm}")

    if commentaries:
        print("\nFirst verse commentary:")
        first = commentaries[0]
        print(f"  Verse: {first.verse}")
        print(f"  Page: {first.page_number}")
        print(f"  Hebrew: {first.hebrew_text[:50]}{'...' if len(first.hebrew_text) > 50 else ''}")
        print(f"  German preview: {first.german_commentary[:150]}...")
        print(f"  Cross-references: {first.cross_references}")
        print(f"  OCR confidence: {first.confidence_score:.1f}%")

        print("\nFormatted markdown (first 800 chars):")
        markdown = librarian.format_for_research_bundle(commentaries, test_psalm)
        print(markdown[:800] + "...")


if __name__ == '__main__':
    main()
