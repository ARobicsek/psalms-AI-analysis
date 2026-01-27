"""
Commentary Formatter
This utility assembles the final, print-ready commentary from the various
output files of the pipeline. It integrates the introduction, verse commentary,
and a new bibliographical summary section.

Key Features:
- Assembles introduction and verse-by-verse commentary.
- Parses `pipeline_summary.json` to extract key statistics for a bibliographical summary.
- Applies formatting for clean copy-paste into MS Word (e.g., tabs for RTL/LTR text).
- Handles divine name modifications.

Author: Claude (Anthropic), with modifications by Gemini Code Assist
Date: 2025-10-19
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, Any

# Handle imports
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.data_sources.tanakh_database import TanakhDatabase
    from src.utils.logger import get_logger
    from src.utils.divine_names_modifier import DivineNamesModifier
else:
    from ..data_sources.tanakh_database import TanakhDatabase
    from .logger import get_logger
    from .divine_names_modifier import DivineNamesModifier


class CommentaryFormatter:
    """Assembles and formats the final print-ready commentary."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("commentary_formatter")
        self.modifier = DivineNamesModifier(logger=self.logger)

    def format_commentary(
        self,
        psalm_num: int,
        intro_text: str,
        verses_text: str,
        summary_data: Dict[str, Any],
        psalm_text_data: Dict[int, Dict[str, str]]
    ) -> str:
        """
        Assembles the full print-ready commentary markdown.

        Args:
            psalm_num: The psalm number.
            intro_text: The introduction essay markdown.
            verses_text: The verse-by-verse commentary markdown.
            summary_data: The parsed pipeline summary JSON data.
            psalm_text_data: A dictionary mapping verse number to its Hebrew/English text.

        Returns:
            A string containing the complete, formatted commentary.
        """
        self.logger.info(f"Formatting print-ready commentary for Psalm {psalm_num}...")

        # 1. Header
        header = f"# Commentary on Psalm {psalm_num}\n"

        # 2. Introduction
        introduction_section = f"## Introduction\n{self._format_body_text(intro_text)}\n"

        # 3. Psalm Text Section
        psalm_text_section = self._format_psalm_text(psalm_num, psalm_text_data).strip() + "\n"

        # 4. Verse-by-Verse Commentary (verse text with punctuation now provided by LLM)
        verse_commentary_section = f"## Verse-by-Verse Commentary\n{self._format_body_text(verses_text)}\n"

        # 5. Bibliographical Summary
        biblio_summary_section = self._format_bibliographical_summary(summary_data)

        # Assemble the document
        full_commentary = (
            header +
            "---\n" +
            introduction_section +
            "---\n" +
            psalm_text_section +
            "---\n" +
            verse_commentary_section +
            "---\n" +
            biblio_summary_section
        )

        self.logger.info("Formatting complete.")
        return full_commentary

    def _format_body_text(self, text: str) -> str:
        """Applies formatting for body text (intro/commentary) for Word compatibility."""
        # Normalize line endings to \n
        normalized_text = text.replace('\r\n', '\n')
        # Replace any sequence of two or more newlines with a single newline
        # This converts hard paragraph breaks into soft line breaks for Word.
        return re.sub(r'\n{2,}', '\n', normalized_text)

    def _insert_verse_text_into_commentary(self, verses_text: str, psalm_text_data: Dict[int, Dict[str, str]]) -> str:
        """
        Programmatically inserts Hebrew verse text before each verse's commentary.

        Args:
            verses_text: The verse-by-verse commentary markdown from the LLM.
            psalm_text_data: A dictionary mapping verse number to its Hebrew/English text.

        Returns:
            Modified verse commentary with Hebrew text inserted before each verse.
        """
        lines = verses_text.split('\n')
        result = []

        for line in lines:
            # Check if this is a verse header (e.g., "**Verse 1**" or "**Verse 23**")
            verse_match = re.match(r'\*\*Verse (\d+)\*\*', line.strip())
            if verse_match:
                verse_num = int(verse_match.group(1))
                result.append(line)  # Add the verse header

                # Add the Hebrew verse text if available
                if verse_num in psalm_text_data:
                    hebrew = psalm_text_data[verse_num].get('hebrew', '')
                    if hebrew:
                        # Apply divine names modification
                        modified_hebrew = self.modifier.modify_text(hebrew)
                        result.append(f"\n{modified_hebrew}\n")
                        self.logger.debug(f"Inserted Hebrew text for verse {verse_num}")
                else:
                    result.append('')  # Add blank line after header if no Hebrew found
            else:
                result.append(line)

        return '\n'.join(result)

    def _format_psalm_text(self, psalm_num: int, psalm_text_data: Dict[int, Dict[str, str]]) -> str:
        """Formats the full psalm text with Hebrew and English side-by-side."""
        lines = [f"## Psalm {psalm_num}\n"]
        for verse_num in sorted(psalm_text_data.keys()):
            hebrew = psalm_text_data[verse_num].get('hebrew', '')
            english = psalm_text_data[verse_num].get('english', '')
            modified_hebrew = self.modifier.modify_text(hebrew)
            # Use LTR mark and tabs for reliable spacing in Word
            lines.append(f"{verse_num}. {modified_hebrew}\u200e\t\t{english}")
        return "\n".join(lines) + "\n\n"

    def _format_bibliographical_summary(self, summary_data: Dict[str, Any]) -> str:
        """Formats the methodological and bibliographical summary."""
        self.logger.info("Formatting bibliographical summary.")
        lines = ["## Methodological & Bibliographical Summary"]

        # The stats are at the root of the JSON object. Do not look for a 'summary' key.
        stats = summary_data

        # --- Research Inputs ---
        lines.append("### Research & Data Inputs")
        analysis_data = stats.get('analysis', {}) or {}
        verse_count = analysis_data.get('verse_count', 'N/A') 
        lines.append(f"- **Psalm Verses Analyzed**: {verse_count}")
        lines.append(f"- **LXX (Septuagint) Verses Reviewed**: {verse_count}") # Assumes LXX is reviewed for all verses
        lines.append(f"- **Phonetic Transcriptions Generated**: {verse_count}") # Assumes one per verse

        research_data = stats.get('research', {}) or {}
        ugaritic_count = len(research_data.get('ugaritic_parallels', []))
        lines.append(f"- **Ugaritic Parallels Reviewed**: {ugaritic_count}")

        lexicon_count = research_data.get('lexicon_entries_count', 'N/A')
        lines.append(f"- **Lexicon Entries (BDB/Klein) Reviewed**: {lexicon_count}")
        
        commentaries = research_data.get('commentary_counts', {})
        total_commentaries = sum(commentaries.values()) if commentaries else 'N/A'
        if commentaries:
            commentary_lines = [f"{c} ({n})" for c, n in sorted(commentaries.items())]
            lines.append(f"- **Traditional Commentaries Reviewed**: {total_commentaries} ({'; '.join(commentary_lines)})")
        elif total_commentaries != 'N/A':
            lines.append(f"- **Traditional Commentaries Reviewed**: {total_commentaries}")

        concordance_total = sum((research_data.get('concordance_results', {}) or {}).values())
        lines.append(f"- **Concordance Entries Reviewed**: {concordance_total if concordance_total > 0 else 'N/A'}")

        # The key is 'figurative_results' which contains a dict like {'total_instances_used': 15}
        figurative_results = research_data.get('figurative_results', {}) or {}
        figurative_total = figurative_results.get('total_instances_used', 0) if isinstance(figurative_results, dict) else 0
        lines.append(f"- **Figurative Language Instances Reviewed**: {figurative_total if figurative_total > 0 else 'N/A'}")

        # Rabbi Sacks references
        sacks_count = research_data.get('sacks_references_count', 0)
        lines.append(f"- **Rabbi Jonathan Sacks References Reviewed**: {sacks_count if sacks_count > 0 else 'N/A'}")

        # Get Master Editor prompt size from the 'steps' section
        master_editor_stats = stats.get('steps', {}).get('master_editor', {})
        prompt_chars = master_editor_stats.get('input_char_count', 'N/A')
        if isinstance(prompt_chars, int):
            lines.append(f"- **Master Editor/Writer Prompt Size**: {prompt_chars:,} characters")
        else:
            lines.append(f"- **Master Editor/Writer Prompt Size**: {prompt_chars} characters")

        lines.append("") # Add a space before the next section
        
        # --- Models Used ---
        lines.append("### Models Used")
        # The key in pipeline_stats.json is 'model_usage', not 'models'.
        agent_models = stats.get('model_usage', {})
        if agent_models:
            lines.append(f"**Structural Analysis (Macro)**: {agent_models.get('macro_analysis', 'N/A')}")
            lines.append(f"**Verse Discovery (Micro)**: {agent_models.get('micro_analysis', 'N/A')}")
            if agent_models.get('insight_extractor'):
                lines.append(f"**Insights Extraction**: {agent_models.get('insight_extractor')}")
            if agent_models.get('synthesis'):
                lines.append(f"**Commentary Synthesis**: {agent_models.get('synthesis', 'N/A')}")

            # Use "Master Writer" if available, else "Editorial Review"
            if agent_models.get('master_writer'):
                lines.append(f"**Master Writer**: {agent_models.get('master_writer', 'N/A')}")
            else:
                lines.append(f"**Editorial Review**: {agent_models.get('master_editor', 'N/A')}")
        else:
            lines.append("Model attribution data not available.")

        lines.append("") # Add a space before the next section

        # --- Date Produced ---
        lines.append("### Date Produced")
        completion_date_str = master_editor_stats.get('completion_date')
        if completion_date_str:
            from datetime import datetime
            dt = datetime.fromisoformat(completion_date_str.replace('Z', '+00:00'))
            lines.append(dt.strftime('%B %d, %Y'))
        else:
            lines.append("Date not available in statistics file.")

        return "\n".join(lines) + "\n"


def main():
    """Command-line interface for commentary formatter."""
    import argparse
    from src.data_sources.tanakh_database import TanakhDatabase

    # Ensure UTF-8 for Hebrew output
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Generate a print-ready commentary file.")
    parser.add_argument('--psalm', type=int, required=True, help="Psalm number")
    parser.add_argument('--intro', type=str, required=True, help="Path to the edited introduction markdown file.")
    parser.add_argument('--verses', type=str, required=True, help="Path to the edited verse-by-verse commentary markdown file.")
    parser.add_argument('--summary', type=str, required=True, help="Path to the pipeline_summary.json file.")
    parser.add_argument('--output', type=str, required=True, help="Path for the output print-ready markdown file.")
    parser.add_argument('--db-path', type=str, default='database/tanakh.db', help="Path to Tanakh database. (Default: database/tanakh.db)")
    args = parser.parse_args()
    
    logger = get_logger("formatter_cli")

    try:
        # Load input files
        logger.info(f"Loading introduction from: {args.intro}")
        intro_text = Path(args.intro).read_text('utf-8')

        logger.info(f"Loading verse commentary from: {args.verses}")
        verses_text = Path(args.verses).read_text('utf-8')

        logger.info(f"Loading summary from: {args.summary}")
        summary_data = json.loads(Path(args.summary).read_text('utf-8'))

        logger.info("Fetching psalm text from database...")
        db = TanakhDatabase(Path(args.db_path))
        psalm_data = db.get_psalm(args.psalm)
        if not psalm_data:
            raise FileNotFoundError(f"Psalm {args.psalm} not found in database.")

        psalm_text_data = {v.verse: {'hebrew': v.hebrew, 'english': v.english} for v in psalm_data.verses}

        # Format the commentary
        formatter = CommentaryFormatter(logger)
        formatted_commentary = formatter.format_commentary(
            psalm_num=args.psalm,
            intro_text=intro_text,
            verses_text=verses_text,
            summary_data=summary_data,
            psalm_text_data=psalm_text_data
        )

        # Save the output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Apply divine names modifications to the final document
        final_output = formatter.modifier.modify_text(formatted_commentary)
        output_path.write_text(final_output, encoding='utf-8')
        logger.info(f"Successfully created print-ready file: {output_path}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing summary JSON file: {e}")
        return 1
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
