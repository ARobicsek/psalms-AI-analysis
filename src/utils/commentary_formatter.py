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
        apply_divine_names: bool = True,
        models_used: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Format complete print-ready commentary with verse text.

        Args:
            introduction: Introduction essay text
            verse_commentary: Verse-by-verse commentary text
            psalm_number: Psalm number
            apply_divine_names: Whether to apply divine names modifications
            models_used: Dictionary with model names for each step:
                         {'macro': 'model-name', 'micro': 'model-name',
                          'synthesis': 'model-name', 'editor': 'model-name'}
                         If None, defaults to current pipeline models.

        Returns:
            Formatted commentary markdown
        """
        self.logger.info(f"Formatting print-ready commentary for Psalm {psalm_number}")

        # Default models if not provided
        if models_used is None:
            models_used = {
                'macro': 'Claude Sonnet 4.5',
                'micro': 'Claude Sonnet 4.5',
                'synthesis': 'Claude Sonnet 4.5',
                'editor': 'GPT-5'
            }

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

            # Use a Left-to-Right Mark (U+200E) followed by a tab to force separation
            # when pasting into applications like Microsoft Word.
            # The LRM signals the start of LTR text, and the tab creates a visible space.
            lrm = "\u200e"  # Left-to-Right Mark
            output.append(f"{verse_num}. {hebrew}   {lrm}\t\t{english}")

        # Introduction
        output.append("---")
        output.append("## Introduction")

        # Replace double newlines with single newlines in the introduction
        # to reduce paragraph spacing when pasting into Word.
        single_spaced_intro = introduction.strip().replace('\n\n', '\n')
        output.append(single_spaced_intro)

        # Verse-by-verse commentary
        output.append("## Verse-by-Verse Commentary")

        for verse_num, verse_data in verses.items():
            hebrew = verse_data['hebrew']
            english = verse_data['english']
            commentary = commentary_sections.get(verse_num, "[Commentary not found]")

            # Format verse section - no bold labels
            output.append(f"### Verse {verse_num}") 
            # Use a Left-to-Right Mark (U+200E) followed by a tab to force separation
            # when pasting into applications like Microsoft Word.
            lrm = "\u200e"
            output.append(f"{hebrew}   {lrm}\t\t{english}")
            # Commentary
            single_spaced_commentary = commentary.strip().replace('\n\n', '\n')
            output.append(single_spaced_commentary)
            output.append("---")

        # Models footer (using dynamic model information)
        output.append("## Models Used")
        output.append("This commentary was generated using:")
        output.append(f"**Structural Analysis (Macro)**: {models_used.get('macro', 'Unknown')}")
        output.append(f"**Verse Discovery (Micro)**: {models_used.get('micro', 'Unknown')}")
        output.append(f"**Commentary Synthesis**: {models_used.get('synthesis', 'Unknown')}")
        output.append(f"**Editorial Review**: {models_used.get('editor', 'Unknown')}")

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

        # Split by verse markers: Verse N (plain or bold, on its own line or inline)
        # Matches: "Verse 1", "**Verse 1**", "Verse 1\n"
        pattern = r'(?:^|\n)(?:\*\*)?Verse (\d+)(?:\*\*)?\s*\n'
        matches = list(re.finditer(pattern, verse_commentary, re.MULTILINE))

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

            # Clean up the commentary text
            # Remove any trailing separators or extra whitespace
            commentary = re.sub(r'\s*---\s*$', '', commentary)
            commentary = commentary.strip()

            sections[verse_num] = commentary

        self.logger.info(f"Parsed {len(sections)} verse commentary sections")
        return sections

    def format_from_files(
        self,
        intro_file: str,
        verses_file: str,
        psalm_number: int,
        output_file: str,
        apply_divine_names: bool = True,
        models_used: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Format commentary from separate intro and verse files.

        Args:
            intro_file: Path to introduction markdown file
            verses_file: Path to verse commentary markdown file
            psalm_number: Psalm number
            output_file: Path to output file
            apply_divine_names: Whether to apply divine names modifications
            models_used: Dictionary with model names for each step (optional)
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
            apply_divine_names=apply_divine_names,
            models_used=models_used
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

        # Create a default models_used dictionary for standalone execution
        # This ensures the correct formatting path is taken.
        default_models = {
            'macro': 'Claude Sonnet 4.5',
            'micro': 'Claude Sonnet 4.5',
            'synthesis': 'Claude Sonnet 4.5',
            'editor': 'GPT-5'
        }

        formatter.format_from_files(
            intro_file=args.intro,
            verses_file=args.verses,
            psalm_number=args.psalm,
            output_file=args.output,
            apply_divine_names=not args.no_divine_names,
            models_used=default_models
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
