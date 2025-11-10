"""
Sacks Librarian Agent

Loads and formats Rabbi Jonathan Sacks' references to Psalms from his collected works.
This agent provides context snippets from Sacks' writings that reference specific psalm verses,
offering contemporary theological perspectives on the psalms.

About the Data:
- Source: Collection of Rabbi Jonathan Sacks' books and essays (1948-2020)
- Format: JSON array with verse references and context snippets
- Each entry includes ~1000 characters before and after the psalm reference
- These are NOT formal commentaries but excerpts showing Sacks' interpretation and usage

Usage:
    from src.agents.sacks_librarian import SacksLibrarian

    librarian = SacksLibrarian()
    entries = librarian.get_psalm_references(psalm=1)
    markdown = librarian.format_for_research_bundle(entries, psalm=1)

Author: Claude Code (Session 68)
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

# Default path to Sacks data file
DEFAULT_SACKS_JSON_PATH = Path(__file__).parent.parent.parent / "sacks_on_psalms.json"


@dataclass
class SacksReference:
    """Represents a single reference to a Psalm in Rabbi Sacks' writings."""
    source_ref: str              # e.g., "Studies in Spirituality; A Weekly Reading..."
    source_title: str            # Extracted title from ref
    psalm_ref: str               # e.g., "Psalms.1.1"
    psalm_chapter: int           # Extracted psalm number
    psalm_verse: int             # Extracted verse number
    context_snippet: str         # ~1000 chars before/after the psalm reference
    version_title: str           # English source version

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_ref": self.source_ref,
            "source_title": self.source_title,
            "psalm_ref": self.psalm_ref,
            "psalm_chapter": self.psalm_chapter,
            "psalm_verse": self.psalm_verse,
            "context_snippet": self.context_snippet,
            "version_title": self.version_title
        }


class SacksLibrarian:
    """
    Manages access to Rabbi Jonathan Sacks' references to Psalms.

    This agent loads the sacks_on_psalms.json file and provides methods
    to retrieve and format references for specific psalms.
    """

    def __init__(self, json_path: Optional[Path] = None):
        """
        Initialize Sacks Librarian.

        Args:
            json_path: Path to sacks_on_psalms.json (uses default if None)
        """
        self.json_path = json_path or DEFAULT_SACKS_JSON_PATH
        self.entries: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Load the Sacks JSON data file."""
        if not self.json_path.exists():
            logger.warning(f"Sacks data file not found at {self.json_path}")
            return

        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.entries = json.load(f)
            logger.info(f"Loaded {len(self.entries)} Sacks references from {self.json_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Sacks JSON file: {e}")
            self.entries = []
        except Exception as e:
            logger.error(f"Error loading Sacks data: {e}")
            self.entries = []

    def get_psalm_references(self, psalm_chapter: int) -> List[SacksReference]:
        """
        Get all Sacks references for a specific psalm chapter.

        Args:
            psalm_chapter: Psalm number (1-150)

        Returns:
            List of SacksReference objects for this psalm
        """
        references = []

        for entry in self.entries:
            source_psalm_ref = entry.get('source_psalm_ref', '')
            context_snippet = entry.get('context_snippet', '')

            # Skip entries without context snippets
            if not context_snippet:
                continue

            # Parse the psalm reference (e.g., "Psalms.1.1" -> chapter=1, verse=1)
            if not source_psalm_ref.startswith('Psalms.'):
                continue

            try:
                parts = source_psalm_ref.split('.')
                if len(parts) >= 3:
                    chapter = int(parts[1])
                    verse = int(parts[2])

                    # Filter by requested chapter
                    if chapter == psalm_chapter:
                        # Extract a cleaner source title
                        source_ref = entry.get('ref', '')
                        source_title = self._extract_title(source_ref)

                        references.append(SacksReference(
                            source_ref=source_ref,
                            source_title=source_title,
                            psalm_ref=source_psalm_ref,
                            psalm_chapter=chapter,
                            psalm_verse=verse,
                            context_snippet=context_snippet,
                            version_title=entry.get('versionTitle', 'Unknown')
                        ))
            except (ValueError, IndexError) as e:
                logger.debug(f"Could not parse psalm reference '{source_psalm_ref}': {e}")
                continue

        logger.info(f"Found {len(references)} Sacks references for Psalm {psalm_chapter}")
        return references

    def _extract_title(self, source_ref: str) -> str:
        """
        Extract a readable title from the full source reference.

        Args:
            source_ref: Full reference string from the JSON

        Returns:
            Cleaned title for display
        """
        # Example: "Studies in Spirituality; A Weekly Reading of the Jewish Bible, Pekudei; Don't Sit, Walk 4"
        # We want: "Pekudei: Don't Sit, Walk"

        if ';' in source_ref:
            # Get the part after the first semicolon
            parts = source_ref.split(';', 1)
            if len(parts) > 1:
                remainder = parts[1].strip()
                # Remove trailing numbers (paragraph references)
                remainder = ' '.join([word for word in remainder.split() if not word.isdigit()])
                return remainder

        # Fallback: return the whole thing
        return source_ref

    def format_for_research_bundle(self, references: List[SacksReference], psalm_chapter: int) -> str:
        """
        Format Sacks references as Markdown for LLM consumption.

        Args:
            references: List of SacksReference objects
            psalm_chapter: Psalm number for header

        Returns:
            Formatted Markdown string
        """
        if not references:
            return ""

        lines = [
            f"## Rabbi Jonathan Sacks on Psalm {psalm_chapter}",
            "",
            "### About Rabbi Jonathan Sacks",
            "",
            "Rabbi Lord Jonathan Sacks (1948–2020) was a British Orthodox rabbi, philosopher, and public theologian who served as the Chief Rabbi of the Commonwealth from 1991 to 2013. A graduate in philosophy from Cambridge, he became one of the world's most prominent public voices for faith, integrating traditional Jewish thought with Western philosophy and science. His vast scholarly corpus includes over 40 books, which fall into two main categories: biblical and liturgical commentary, most famously his *Covenant & Conversation* essays on the weekly Torah portion; and works of public theology, such as *The Great Partnership* and *The Dignity of Difference*.",
            "",
            "Rabbi Sacks's philosophy was a 21st-century application of *Torah ve-Hokhma* (Torah and Wisdom). He argued that science and religion are not in conflict but are \"two hemispheres of the brain\": \"Science takes things apart to see how they work. Religion puts things together to see what they mean.\" His exegetical approach is not that of a classical *parshan* (commentator) focused on grammatical or textual puzzles. His method is thematic, philosophical, and ethical. In *Covenant & Conversation*, he uses the Torah portion as a springboard to discuss the most pressing existential and moral concerns of modernity—leadership, family, ethics, and alienation. A typical essay masterfully blends insights from classical commentators like Rashi with Western philosophers, modern psychology, and current events. His work answers a new, modern question. While classical commentators asked, \"What does this verse *mean*?\" Rabbi Sacks, writing for an educated and often secularized world, answers the question, \"Why does this verse *matter*?\" He translated the text's covenantal message into a universal moral framework for the 21st century.",
            "",
            "**About this section**: These excerpts are from Rabbi Sacks' writings. They are NOT traditional commentaries on Psalms. Rather, they show how Sacks references and interprets psalm verses in his broader theological and philosophical works. Each entry includes the psalm verse he referenced plus approximately 1000 characters before and after to reveal his thinking about that verse.",
            ""
        ]

        # Group by verse for cleaner presentation
        refs_by_verse: Dict[int, List[SacksReference]] = {}
        for ref in references:
            if ref.psalm_verse not in refs_by_verse:
                refs_by_verse[ref.psalm_verse] = []
            refs_by_verse[ref.psalm_verse].append(ref)

        # Format each verse group
        for verse_num in sorted(refs_by_verse.keys()):
            verse_refs = refs_by_verse[verse_num]
            lines.append(f"### Verse {verse_num} ({len(verse_refs)} reference{'s' if len(verse_refs) > 1 else ''})")
            lines.append("")

            for i, ref in enumerate(verse_refs, 1):
                lines.append(f"#### Reference {i}: {ref.source_title}")
                lines.append(f"**Source**: {ref.version_title}")
                lines.append("")
                lines.append(ref.context_snippet)
                lines.append("")
                lines.append("---")
                lines.append("")

        return "\n".join(lines)


def main():
    """Test the Sacks Librarian with a few psalm chapters."""
    librarian = SacksLibrarian()

    # Test with Psalm 1
    print("=" * 80)
    print("Testing Sacks Librarian with Psalm 1")
    print("=" * 80)
    refs = librarian.get_psalm_references(1)
    print(f"\nFound {len(refs)} references for Psalm 1")

    if refs:
        print("\nFirst reference:")
        print(f"  Verse: {refs[0].psalm_verse}")
        print(f"  Source: {refs[0].source_title}")
        print(f"  Snippet preview: {refs[0].context_snippet[:150]}...")

        print("\nFormatted markdown (first 500 chars):")
        markdown = librarian.format_for_research_bundle(refs, 1)
        print(markdown[:500])


if __name__ == '__main__':
    main()
