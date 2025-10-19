"""
Commentary Formatter
Formats Psalm commentary with verse text (Hebrew + English) and applies divine names modifications.

Author: Claude (Anthropic)
Date: 2025-10-17
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Handle imports
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.data_sources.tanakh_database import TanakhDatabase
    from src.utils.divine_names_modifier import DivineNamesModifier
    from src.utils.logger import get_logger
else:
    from ..data_sources.tanakh_database import TanakhDatabase
    from .divine_names_modifier import DivineNamesModifier
    from .logger import get_logger


class CommentaryFormatter:
    """
    Formats Psalm commentary with verse text and divine names modifications.
    """

    def __init__(self, db_path: Optional[str] = None, logger=None):
        """
        Initialize formatter.

        Args:
            db_path: Path to Tanakh database (optional)
            logger: Logger instance
        """
        self.logger = logger or get_logger("commentary_formatter")

        # Initialize database
        if not db_path:
            # Use default path relative to project
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "database" / "tanakh.db"
        elif isinstance(db_path, str):
            db_path = Path(db_path)

        self.db = TanakhDatabase(db_path)
        self.modifier = DivineNamesModifier(logger=self.logger)

    def format_print_ready_commentary(
        self,
        introduction: str,
        verse_commentary: str,
        psalm_number: int,
        apply_divine_names: bool = True
    ) -> str:
        """
        Format complete print-ready commentary with verse text.

        Args:
            introduction: Introduction essay text
            verse_commentary: Verse-by-verse commentary text
            psalm_number: Psalm number
            apply_divine_names: Whether to apply divine names modifications

        Returns:
            Formatted commentary markdown
        """
        self.logger.info(f"Formatting print-ready commentary for Psalm {psalm_number}")

        # Get verse data
        verses = self._get_psalm_verses(psalm_number)

        if not verses:
            self.logger.error(f"No verses found for Psalm {psalm_number}")
            return ""

        # Parse verse commentary sections
        commentary_sections = self._parse_verse_commentary(verse_commentary)

        # Build formatted document
        output = []

        # Title
        output.append(f"# Commentary on Psalm {psalm_number}")
        output.append("---")

        # Psalm Text (Hebrew and English, verse by verse)
        output.append("## Psalm Text")
        for verse_num, verse_data in verses.items():
            hebrew = verse_data['hebrew']
            english = verse_data['english']

            # Format: verse number, Hebrew, then three spaces, then English (same line)
            # Three spaces for visual separation between RTL/LTR text
            output.append(f"{verse_num}. {hebrew}   {english}")

        # Introduction
        output.append("---")
        output.append("## Introduction")
        output.append(introduction.strip())

        # Verse-by-verse commentary
        output.append("## Verse-by-Verse Commentary")

        for verse_num, verse_data in verses.items():
            hebrew = verse_data['hebrew']
            english = verse_data['english']
            commentary = commentary_sections.get(verse_num, "[Commentary not found]")

            # Format verse section - no bold labels
            output.append(f"### Verse {verse_num}")
            # Hebrew and English text without labels
            output.append(f"{hebrew}")
            output.append(f"{english}")
            # Commentary
            output.append(commentary.strip())
            output.append("---")

        # Join into single document
        document = "\n".join(output)

        # Apply divine names modifications if requested
        if apply_divine_names:
            self.logger.info("Applying divine names modifications")
            document = self.modifier.modify_text(document)

        self.logger.info(f"Commentary formatted: {len(document)} chars")
        return document

    def _get_psalm_verses(self, psalm_number: int) -> Dict[int, Dict[str, str]]:
        """
        Get all verses for a psalm from database.

        English text is already cleaned of Sefaria footnotes when downloaded
        from the API (via strip_sefaria_footnotes in sefaria_client.py).

        Args:
            psalm_number: Psalm number

        Returns:
            Dictionary mapping verse number to {'hebrew': ..., 'english': ...}
        """
        verses = {}

        try:
            # Get Psalm from database
            psalm = self.db.get_psalm(psalm_number)

            if not psalm:
                self.logger.error(f"Could not retrieve Psalm {psalm_number} from database")
                return {}

            # Convert to dictionary format
            for psalm_verse in psalm.verses:
                verses[psalm_verse.verse] = {
                    'hebrew': psalm_verse.hebrew,
                    'english': psalm_verse.english  # Already clean from API fetch
                }

            self.logger.info(f"Retrieved {len(verses)} verses for Psalm {psalm_number}")
            return verses

        except Exception as e:
            self.logger.error(f"Error retrieving verses: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _parse_verse_commentary(self, verse_commentary: str) -> Dict[int, str]:
        """
        Parse verse commentary text into dictionary by verse number.

        Args:
            verse_commentary: Raw verse commentary markdown

        Returns:
            Dictionary mapping verse number to commentary text
        """
        sections = {}

        # Split by verse markers: **Verse N**
        pattern = r'\*\*Verse (\d+)\*\*'
        matches = list(re.finditer(pattern, verse_commentary))

        for i, match in enumerate(matches):
            verse_num = int(match.group(1))
            start = match.end()

            # Find end of this verse's commentary (start of next verse or end of text)
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(verse_commentary)

            # Extract commentary text
            commentary = verse_commentary[start:end].strip()
            sections[verse_num] = commentary

        self.logger.info(f"Parsed {len(sections)} verse commentary sections")
        return sections

    def format_from_files(
        self,
        intro_file: str,
        verses_file: str,
        psalm_number: int,
        output_file: str,
        apply_divine_names: bool = True
    ) -> None:
        """
        Format commentary from separate intro and verse files.

        Args:
            intro_file: Path to introduction markdown file
            verses_file: Path to verse commentary markdown file
            psalm_number: Psalm number
            output_file: Path to output file
            apply_divine_names: Whether to apply divine names modifications
        """
        # Read input files
        with open(intro_file, 'r', encoding='utf-8') as f:
            introduction = f.read()

        with open(verses_file, 'r', encoding='utf-8') as f:
            verse_commentary = f.read()

        # Format commentary
        formatted = self.format_print_ready_commentary(
            introduction=introduction,
            verse_commentary=verse_commentary,
            psalm_number=psalm_number,
            apply_divine_names=apply_divine_names
        )

        # Write output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted)

        self.logger.info(f"Print-ready commentary saved to {output_file}")


def main():
    """Command-line interface for commentary formatter."""
    import argparse

    # Ensure UTF-8 for Hebrew output
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Format Psalm commentary with verse text and divine names modifications'
    )
    parser.add_argument('--intro', type=str, required=True,
                       help='Path to introduction markdown file')
    parser.add_argument('--verses', type=str, required=True,
                       help='Path to verse commentary markdown file')
    parser.add_argument('--psalm', type=int, required=True,
                       help='Psalm number')
    parser.add_argument('--output', type=str, required=True,
                       help='Path to output file')
    parser.add_argument('--no-divine-names', action='store_true',
                       help='Skip divine names modifications')
    parser.add_argument('--db', type=str, default=None,
                       help='Path to Tanakh database (optional)')

    args = parser.parse_args()

    try:
        formatter = CommentaryFormatter(db_path=args.db)

        print("=" * 80)
        print("COMMENTARY FORMATTER")
        print("=" * 80)
        print()
        print(f"Psalm Number: {args.psalm}")
        print(f"Introduction: {args.intro}")
        print(f"Verses:       {args.verses}")
        print(f"Output:       {args.output}")
        print(f"Divine Names: {'Modified' if not args.no_divine_names else 'Original'}")
        print()
        print("Formatting...")

        formatter.format_from_files(
            intro_file=args.intro,
            verses_file=args.verses,
            psalm_number=args.psalm,
            output_file=args.output,
            apply_divine_names=not args.no_divine_names
        )

        print()
        print("=" * 80)
        print(f"COMPLETE! Print-ready commentary saved to:")
        print(f"  {args.output}")
        print("=" * 80)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
