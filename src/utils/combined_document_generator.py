"""
Generates a combined print-ready Microsoft Word (.docx) document that includes
both main and college commentary versions in a single document.

This script creates a document with:
1. Full psalm text (Hebrew and English)
2. Main introduction
3. College introduction (titled "Introduction - College version")
4. Modern Jewish Liturgical Use section (from main version)
5. Verse-by-verse commentary with both main and college versions
   - Each verse shows the main commentary, then a divider line, then the college commentary
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, ns

# Handle imports for both module and script usage
if __name__ == '__main__' and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from src.data_sources.tanakh_database import TanakhDatabase
    from src.utils.divine_names_modifier import DivineNamesModifier
    from src.data_sources.sefaria_client import strip_sefaria_footnotes
else:
    from ..data_sources.tanakh_database import TanakhDatabase
    from .divine_names_modifier import DivineNamesModifier
    from ..data_sources.sefaria_client import strip_sefaria_footnotes


def add_page_number(paragraph):
    """
    Adds a page number field to the given paragraph.
    The paragraph should be in a footer.
    """
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Create the run that will contain the page number field
    run = paragraph.add_run()

    # Create the complex field for the page number
    fldChar_begin = OxmlElement('w:fldChar')
    fldChar_begin.set(ns.qn('w:fldCharType'), 'begin')

    instrText = OxmlElement('w:instrText')
    instrText.set(ns.qn('xml:space'), 'preserve')
    instrText.text = 'PAGE'

    fldChar_end = OxmlElement('w:fldChar')
    fldChar_end.set(ns.qn('w:fldCharType'), 'end')

    run._r.append(fldChar_begin)
    run._r.append(instrText)
    run._r.append(fldChar_end)

class CombinedDocumentGenerator:
    """Generates a combined .docx with main and college commentaries."""

    def __init__(self, psalm_num: int,
                 main_intro_path: Path, main_verses_path: Path,
                 college_intro_path: Path, college_verses_path: Path,
                 stats_path: Path, output_path: Path):
        self.psalm_num = psalm_num
        self.main_intro_path = main_intro_path
        self.main_verses_path = main_verses_path
        self.college_intro_path = college_intro_path
        self.college_verses_path = college_verses_path
        self.stats_path = stats_path
        self.output_path = output_path
        self.document = Document()
        self._set_default_styles()
        self.modifier = DivineNamesModifier()

    @staticmethod
    def _split_into_grapheme_clusters(text: str) -> List[str]:
        """
        Split Hebrew text into grapheme clusters (base letter + combining marks).

        A grapheme cluster consists of:
        - A base character (Hebrew letter or space)
        - Followed by zero or more combining characters (nikud, cantillation, shin/sin dot, etc.)

        Combining character ranges:
        - U+0591-U+05BD: Cantillation marks
        - U+05BF: Rafe
        - U+05C1-U+05C2: Shin/Sin dots
        - U+05C4-U+05C7: Other marks
        - U+05B0-U+05BD: Vowel points (nikud)
        """
        # Pattern: base character followed by any combining marks
        # Base: Hebrew letter (U+05D0-U+05EA) or space
        # Combining: U+0591-U+05BD, U+05BF, U+05C1-U+05C2, U+05C4-U+05C7
        cluster_pattern = r'[\u05D0-\u05EA\s][\u0591-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C7]*'
        clusters = re.findall(cluster_pattern, text)
        return clusters

    @staticmethod
    def _reverse_hebrew_by_clusters(hebrew_text: str) -> str:
        """
        Reverse Hebrew text by grapheme clusters (keeping letter+nikud together).

        Example:
        - Input: "שִׁלוֹם" (shalom) = [שִׁ, ל, וֹ, ם]
        - Output: "םוֹלשִׁ" (reversed clusters)

        This prevents combining marks (nikud) from detaching from their base letters,
        which would cause dotted circle placeholders to appear.
        """
        clusters = CombinedDocumentGenerator._split_into_grapheme_clusters(hebrew_text)
        # Reverse the order of clusters (but keep each cluster intact)
        reversed_clusters = clusters[::-1]
        return ''.join(reversed_clusters)

    def _set_default_styles(self):
        """Set default font for the document."""
        # Set default font
        font = self.document.styles['Normal'].font
        font.name = 'Times New Roman'
        font.size = Pt(12)

        # Create a new style for the sans-serif body text (intro and commentary)
        style = self.document.styles.add_style('BodySans', 1) # 1 for paragraph style
        style.base_style = self.document.styles['Normal']
        style.font.name = 'Aptos'
        style.font.size = Pt(12) # Aptos 12pt for intro and commentary

        # Create a new style for the methodological summary
        summary_style = self.document.styles.add_style('SummaryText', 1) # 1 for paragraph style
        summary_style.base_style = self.document.styles['Normal']
        summary_style.font.name = 'Times New Roman'
        summary_style.font.size = Pt(9) # Times New Roman 9pt for summary
        summary_style.paragraph_format.line_spacing = 0.8 # 70% line spacing

        # Set spacing for all heading levels to be tighter
        for i in range(1, 5):
            style = self.document.styles[f'Heading {i}']
            style.paragraph_format.space_before = Pt(12)
            style.paragraph_format.space_after = Pt(4)

        # Set paragraph spacing to be tighter (soft breaks)
        style = self.document.styles['Normal']
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(8)

        # Set document margins to 1 inch on all sides
        for section in self.document.sections:
            section.top_margin = Pt(72)  # 1 inch = 72 points
            section.bottom_margin = Pt(72)
            section.left_margin = Pt(72)
            section.right_margin = Pt(72)

    def _set_paragraph_ltr(self, paragraph):
        """Set paragraph direction to left-to-right."""
        pPr = paragraph._element.get_or_add_pPr()
        bidi = OxmlElement('w:bidi')
        bidi.set(ns.qn('w:val'), '0')
        pPr.append(bidi)

    def _add_paragraph_with_markdown(self, text: str, style: str = 'Normal'):
        """
        Add a paragraph with basic markdown formatting (bold, italic).
        Handles Hebrew text with RTL formatting.
        """
        paragraph = self.document.add_paragraph(style=style)
        self._set_paragraph_ltr(paragraph)

        # Process with the centralized formatting method
        self._process_markdown_formatting(paragraph, text, set_font=True)

    def _process_markdown_formatting(self, paragraph, text, set_font=False):
        """
        Process markdown formatting (bold, italic, etc.) and add runs to the given paragraph.
        This handles Hebrew in parentheses correctly using LRO/PDF Unicode control characters.

        Args:
            paragraph: The paragraph to add runs to
            text: The text to process
            set_font: If True, explicitly set Aptos 12pt font on all runs
        """
        modified_text = self.modifier.modify_text(text)
        parts = re.split(r'(\*\*.*?\*\*|__.*?__|\*.*?\*|_.*?_)', modified_text)

        for part in parts:
            if not part:
                continue

            if part.startswith('**') and part.endswith('**'):
                run = paragraph.add_run(part[2:-2])
                run.bold = True
                if set_font:
                    run.font.name = 'Aptos'
                    run.font.size = Pt(12)
            elif part.startswith('__') and part.endswith('__'):
                run = paragraph.add_run(part[2:-2])
                run.bold = True
                if set_font:
                    run.font.name = 'Aptos'
                    run.font.size = Pt(12)
            elif part.startswith('*') and part.endswith('*'):
                run = paragraph.add_run(part[1:-1])
                run.italic = True
                if set_font:
                    run.font.name = 'Aptos'
                    run.font.size = Pt(12)
            elif part.startswith('_') and part.endswith('_'):
                run = paragraph.add_run(part[1:-1])
                run.italic = True
                if set_font:
                    run.font.name = 'Aptos'
                    run.font.size = Pt(12)
            else:
                # Handle parenthesized Hebrew with grapheme cluster reversal + LRO
                # This prevents punctuation from being reversed or moved around
                hebrew_paren_pattern = r'\(([\u0590-\u05FF\u05B0-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C7\s]+)\)'
                if re.search(hebrew_paren_pattern, part):
                    LRO = '\u202D'  # LEFT-TO-RIGHT OVERRIDE
                    PDF = '\u202C'  # POP DIRECTIONAL FORMATTING

                    def reverse_hebrew_match(match):
                        hebrew_text = match.group(1)
                        # Reverse by grapheme clusters (keeps nikud attached)
                        reversed_hebrew = self._reverse_hebrew_by_clusters(hebrew_text)
                        # Wrap with LRO to force LTR display
                        return f'{LRO}({reversed_hebrew}){PDF}'

                    modified_part = re.sub(hebrew_paren_pattern, reverse_hebrew_match, part)
                    run = paragraph.add_run(modified_part)
                else:
                    run = paragraph.add_run(part)

                if set_font:
                    run.font.name = 'Aptos'
                    run.font.size = Pt(12)

    def _add_commentary_with_bullets(self, text: str, style: str = 'Normal'):
        """
        Add commentary text with proper bullet formatting.
        Handles both regular text and bullet points.
        """
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip horizontal rule markers (---, ___, ***)
            if line in ('---', '___', '***', '—', '–'):
                continue

            # Check if this is a bullet point
            if line.startswith('- '):
                # Create a bulleted paragraph
                paragraph = self.document.add_paragraph(style='List Bullet')
                self._set_paragraph_ltr(paragraph)
                line_without_bullet = line[2:]  # Remove "- "
                # Process with proper formatting
                self._process_markdown_formatting(paragraph, line_without_bullet, set_font=True)
            else:
                # Regular paragraph
                self._add_paragraph_with_markdown(line, style=style)

    def _add_summary_paragraph(self, text: str):
        """Add a summary paragraph with the SummaryText style."""
        self._add_paragraph_with_markdown(text, style='SummaryText')

    def _parse_verse_commentary(self, content: str, psalm_text_data: Dict[int, Dict[str, str]]) -> List[Dict[str, str]]:
        """Parses the verse-by-verse commentary file."""
        verses = []
        # Try both formats: "**Verse X**" (expected format) and "Verse X" (fallback format)
        # First try the expected format with bold markdown, allowing for trailing whitespace
        verse_blocks = re.split(r'(?=^\*\*Verse \d+\*\*\s*\n)', content, flags=re.MULTILINE)

        # If no verses found with bold format, try the fallback format without bold
        if len(verse_blocks) <= 1:  # Only one block means no splits occurred
            verse_blocks = re.split(r'(?=^Verse \d+\s*\n)', content, flags=re.MULTILINE)

        for block in verse_blocks:
            block = block.strip()
            if not block.strip():
                continue

            lines = block.strip().split('\n', 1)  # Split only on the first newline

            # Try both formats for verse number matching, allowing for trailing whitespace
            verse_num_match = re.match(r'^\*\*Verse (\d+)\*\*\s*', lines[0])
            if not verse_num_match:
                verse_num_match = re.match(r'^Verse (\d+)\s*', lines[0])

            if not verse_num_match:
                continue

            verse_num = verse_num_match.group(1)
            commentary_text = '\n'.join(lines[1:]).strip()

            # Get Hebrew/English text from the database data
            verse_info = psalm_text_data.get(int(verse_num), {})
            hebrew_text = verse_info.get('hebrew', '[Hebrew text not found]')
            english_text = verse_info.get('english', '[English text not found]')
            verses.append({
                "number": verse_num,
                "hebrew": hebrew_text,
                "english": english_text,
                "commentary": commentary_text
            })
        return verses

    def _format_psalm_text(self, psalm_num: int, psalm_text_data: Dict[int, Dict[str, str]]):
        """Formats the full psalm text with Hebrew and English side-by-side."""
        self.document.add_heading(f"Psalm {psalm_num}", level=2)

        # Create a table with 2 columns
        table = self.document.add_table(rows=0, cols=2)
        table.autofit = True

        for verse_num in sorted(psalm_text_data.keys()):
            hebrew = psalm_text_data[verse_num].get('hebrew', '')
            english = psalm_text_data[verse_num].get('english', '')
            # Strip any footnote markers from the English text
            english = strip_sefaria_footnotes(english)
            modified_hebrew = self.modifier.modify_text(hebrew)

            row_cells = table.add_row().cells

            # Hebrew cell (left, but text is RTL)
            p_heb = row_cells[0].paragraphs[0]
            p_heb.add_run(f"{verse_num}. ").bold = True
            p_heb.add_run(modified_hebrew).font.rtl = True

            # English cell (right)
            p_eng = row_cells[1].paragraphs[0]
            run_eng = p_eng.add_run(english)
            run_eng.font.name = 'Cambria'

    def _extract_liturgical_section(self, intro_content: str) -> str:
        """
        Extracts the 'Modern Jewish Liturgical Use' section from the intro content.
        Returns the section content or empty string if not found.
        """
        # Look for the section header
        match = re.search(r'## Modern Jewish Liturgical Use\s*\n(.*)', intro_content, re.DOTALL | re.IGNORECASE)
        if match:
            return "## Modern Jewish Liturgical Use\n" + match.group(1).strip()
        return ""

    def _format_bibliographical_summary(self, stats: Dict[str, Any]) -> str:
        """Formats the stats dictionary into a readable string for the document."""
        # --- Analysis & Research Inputs ---
        analysis_data = stats.get('analysis', {}) or {}
        verse_count = analysis_data.get('verse_count', 'N/A')

        research_data = stats.get('research', {})
        ugaritic_count = len(research_data.get('ugaritic_parallels', []))
        lexicon_count = research_data.get('lexicon_entries_count', 'N/A')

        commentaries = research_data.get('commentary_counts', {})
        total_commentaries = sum(commentaries.values()) if commentaries else 'N/A'
        commentary_details = ""
        if commentaries:
            commentary_lines = [f"{c} ({n})" for c, n in sorted(commentaries.items())]
            commentary_details = f" ({'; '.join(commentary_lines)})"

        concordance_total = sum((research_data.get('concordance_results', {}) or {}).values())

        figurative_results = research_data.get('figurative_results', {}) or {}
        figurative_total = figurative_results.get('total_instances_used', 0) if isinstance(figurative_results, dict) else 0

        sacks_count = research_data.get('sacks_references_count', 0)
        related_psalms_count = research_data.get('related_psalms_count', 0)
        related_psalms_list = research_data.get('related_psalms_list', [])

        # Format related psalms display: count and list
        if related_psalms_count > 0 and related_psalms_list:
            psalms_list_str = ', '.join(str(p) for p in related_psalms_list)
            related_psalms_str = f"{related_psalms_count} (Psalms {psalms_list_str})"
        elif related_psalms_count > 0:
            related_psalms_str = str(related_psalms_count)
        else:
            related_psalms_str = 'N/A'

        master_editor_stats = stats.get('steps', {}).get('master_editor', {})
        prompt_chars = master_editor_stats.get('input_char_count', 'N/A')
        if isinstance(prompt_chars, int):
            prompt_chars_str = f"{prompt_chars:,} characters"
        else:
            prompt_chars_str = f"{prompt_chars} characters"

        # --- Models Used --- (This section will be built from the markdown in the generate() method)
        models_used_str = "### Models Used"

        summary = f"""
Methodological & Bibliographical Summary

### Research & Data Inputs
**Psalm Verses Analyzed**: {verse_count}
**LXX (Septuagint) Texts Reviewed**: {verse_count}
**Phonetic Transcriptions Generated**: {verse_count}
**Ugaritic Parallels Reviewed**: {ugaritic_count}
**Lexicon Entries (BDB\\Klein) Reviewed**: {lexicon_count}
**Traditional Commentaries Reviewed**: {total_commentaries}{commentary_details}
**Concordance Entries Reviewed**: {concordance_total if concordance_total > 0 else 'N/A'}
**Figurative Language Instances Reviewed**: {figurative_total if figurative_total > 0 else 'N/A'}
**Rabbi Jonathan Sacks References Reviewed**: {sacks_count if sacks_count > 0 else 'N/A'}
**Similar Psalms Analyzed**: {related_psalms_str}
**Master Editor Prompt Size**: {prompt_chars_str}

{models_used_str}
        """.strip()
        return summary

    def _add_em_dash_separator(self):
        """
        Adds an em dash separator between main and college commentary.
        """
        paragraph = self.document.add_paragraph(style='BodySans')
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run('—')  # Em dash
        run.font.name = 'Aptos'
        run.font.size = Pt(12)

    def _add_horizontal_border(self):
        """
        Adds a horizontal border line between verses.
        """
        paragraph = self.document.add_paragraph()
        pPr = paragraph._element.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')

        # Add bottom border
        bottom = OxmlElement('w:bottom')
        bottom.set(ns.qn('w:val'), 'single')
        bottom.set(ns.qn('w:sz'), '12')  # Size in 1/8 pt
        bottom.set(ns.qn('w:space'), '1')
        bottom.set(ns.qn('w:color'), '000000')

        pBdr.append(bottom)
        pPr.append(pBdr)

    def generate(self):
        """Main method to generate the combined .docx file."""
        # Fetch psalm text data from the database first
        db = TanakhDatabase()
        psalm_data = db.get_psalm(self.psalm_num)
        if not psalm_data:
            raise FileNotFoundError(f"Psalm {self.psalm_num} not found in database.")
        psalm_text_data = {v.verse: {'hebrew': v.hebrew, 'english': v.english} for v in psalm_data.verses}

        # 1. Add Title
        self.document.add_heading(f'Commentary on Psalm {self.psalm_num}', level=1)
        # Adjust spacing after the main title for a "softer" break
        title_style = self.document.styles['Heading 1']
        title_style.paragraph_format.space_after = Pt(12)

        # 2. Add Full Psalm Text
        self._format_psalm_text(self.psalm_num, psalm_text_data)

        # Add a page break after the psalm text table
        self.document.add_paragraph() # Add a paragraph to attach the break to
        self.document.add_page_break()

        # 3. Add Main Introduction
        self.document.add_heading('Introduction', level=2)
        main_intro_content = self.main_intro_path.read_text(encoding='utf-8')

        # Extract liturgical section from main intro before processing
        liturgical_section = self._extract_liturgical_section(main_intro_content)

        # Remove liturgical section from main intro
        main_intro_without_liturgical = re.sub(
            r'## Modern Jewish Liturgical Use.*',
            '',
            main_intro_content,
            flags=re.DOTALL | re.IGNORECASE
        ).strip()

        # Add main intro paragraphs
        for para in main_intro_without_liturgical.strip().split('\n'):
            if para.strip():
                self._add_paragraph_with_markdown(para, style='BodySans')

        # 4. Add College Introduction with green "College" in heading
        college_heading = self.document.add_heading('', level=2)
        college_heading.add_run('Introduction - ')
        college_run = college_heading.add_run('College')
        college_run.font.color.rgb = RGBColor(0, 128, 0)  # Green color
        college_heading.add_run(' version')

        college_intro_content = self.college_intro_path.read_text(encoding='utf-8')

        # Remove liturgical section from college intro if present
        college_intro_without_liturgical = re.sub(
            r'## Modern Jewish Liturgical Use.*',
            '',
            college_intro_content,
            flags=re.DOTALL | re.IGNORECASE
        ).strip()

        # Add college intro paragraphs
        for para in college_intro_without_liturgical.strip().split('\n'):
            if para.strip():
                self._add_paragraph_with_markdown(para, style='BodySans')

        # 5. Add Modern Jewish Liturgical Use section (from main version)
        if liturgical_section:
            self.document.add_heading('Modern Jewish Liturgical Use', level=2)
            # Remove the heading from the section content
            liturgical_content = re.sub(r'^## Modern Jewish Liturgical Use\s*\n', '', liturgical_section).strip()
            for para in liturgical_content.split('\n'):
                if para.strip():
                    # Handle subheadings
                    if para.strip().startswith('####'):
                        self.document.add_heading(para.strip().replace('####', '').strip(), level=4)
                    elif para.strip().startswith('###'):
                        self.document.add_heading(para.strip().replace('###', '').strip(), level=3)
                    else:
                        self._add_paragraph_with_markdown(para, style='BodySans')

        # 6. Add Verse-by-Verse Commentary with both versions
        verse_heading = self.document.add_heading('', level=2)
        verse_heading.add_run('Verse-by-verse commentary: Main and ')
        college_word = verse_heading.add_run('College')
        college_word.font.color.rgb = RGBColor(0, 128, 0)  # Green color
        verse_heading.add_run(' versions')

        # Parse both verse files
        main_verses_content = self.modifier.modify_text(self.main_verses_path.read_text(encoding='utf-8'))
        college_verses_content = self.modifier.modify_text(self.college_verses_path.read_text(encoding='utf-8'))

        main_parsed_verses = self._parse_verse_commentary(main_verses_content, psalm_text_data)
        college_parsed_verses = self._parse_verse_commentary(college_verses_content, psalm_text_data)

        # Create a mapping for easy lookup
        college_verse_map = {v['number']: v for v in college_parsed_verses}

        for i, main_verse in enumerate(main_parsed_verses):
            verse_num = main_verse['number']

            # Add verse heading
            self.document.add_heading(f'Verse {verse_num}', level=3)

            # Add main commentary
            self._add_commentary_with_bullets(main_verse["commentary"], style='BodySans')

            # Add college commentary if it exists
            if verse_num in college_verse_map:
                # Add em dash separator between main and college
                self._add_em_dash_separator()
                college_verse = college_verse_map[verse_num]
                college_commentary = college_verse["commentary"]

                # Remove any leading Hebrew verse lines
                # College commentary often starts with the Hebrew verse (like "לַמְנַצֵּחַ...")
                # We want to skip those and start with the English commentary
                lines = college_commentary.split('\n')
                commentary_lines = []
                started_english = False

                for line in lines:
                    line_stripped = line.strip()
                    if not line_stripped:
                        if started_english:
                            commentary_lines.append(line)
                        continue

                    # Check if line starts with Hebrew (skip if it does and we haven't started English yet)
                    if not started_english and re.match(r'^[\u0590-\u05FF]', line_stripped):
                        continue  # Skip Hebrew verse lines at the beginning

                    # If we're here, we've hit English commentary
                    started_english = True
                    commentary_lines.append(line)

                # Join the English commentary lines
                english_commentary = '\n'.join(commentary_lines).strip()

                if english_commentary:
                    # Now add the commentary with green/bold first word
                    lines = english_commentary.split('\n')
                    first_word_done = False

                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue

                        # Skip horizontal rule markers (---, ___, ***)
                        if line in ('---', '___', '***', '—', '–'):
                            continue

                        # Process first non-empty line specially
                        if not first_word_done:
                            # Handle bullet or regular line
                            is_bullet = line.startswith('- ')
                            if is_bullet:
                                line = line[2:]  # Remove bullet marker

                            # Split on first whitespace to get first word
                            words = line.split(None, 1)
                            if words:
                                first_word = words[0]
                                rest_of_line = words[1] if len(words) > 1 else ""

                                # Create paragraph
                                if is_bullet:
                                    paragraph = self.document.add_paragraph(style='List Bullet')
                                else:
                                    paragraph = self.document.add_paragraph(style='BodySans')

                                self._set_paragraph_ltr(paragraph)

                                # Add first word with green and bold
                                first_run = paragraph.add_run(first_word + (' ' if rest_of_line else ''))
                                first_run.font.color.rgb = RGBColor(0, 128, 0)  # Green
                                first_run.bold = True
                                first_run.font.name = 'Aptos'
                                first_run.font.size = Pt(12)

                                # Add rest of line with normal formatting
                                if rest_of_line:
                                    self._process_markdown_formatting(paragraph, rest_of_line, set_font=True)

                                first_word_done = True
                            else:
                                # Shouldn't happen, but add normally if it does
                                self._add_paragraph_with_markdown(line, style='BodySans')
                                first_word_done = True
                        else:
                            # Not first line, add normally
                            if line.startswith('- '):
                                paragraph = self.document.add_paragraph(style='List Bullet')
                                self._set_paragraph_ltr(paragraph)
                                self._process_markdown_formatting(paragraph, line[2:], set_font=True)
                            else:
                                self._add_paragraph_with_markdown(line, style='BodySans')

            # Add horizontal border between verses (except after the last verse)
            if i < len(main_parsed_verses) - 1:
                self._add_horizontal_border()

        # 7. Add Methodological Summary
        if self.stats_path.exists():
            self.document.add_page_break()
            self.document.add_heading('Methodological & Bibliographical Summary', level=2)
            stats_data = json.loads(self.stats_path.read_text(encoding='utf-8'))
            summary_text = self._format_bibliographical_summary(stats_data)

            # Manually add the Models Used section text to the summary string
            model_usage = stats_data.get('model_usage', {})
            if model_usage:
                summary_text += f"\n**Structural Analysis (Macro)**: {model_usage.get('macro_analysis', 'N/A')}"
                summary_text += f"\n**Verse Discovery (Micro)**: {model_usage.get('micro_analysis', 'N/A')}"
                summary_text += f"\n**Commentary Synthesis**: {model_usage.get('synthesis', 'N/A')}"
                summary_text += f"\n**Editorial Review**: {model_usage.get('master_editor', 'N/A')}"
            else:
                summary_text += "\nModel attribution data not available."

            # Now, add the Date Produced section heading and data
            summary_text += "\n\n### Date Produced"
            master_editor_stats = stats_data.get('steps', {}).get('master_editor', {})
            completion_date_str = master_editor_stats.get('completion_date')
            if completion_date_str:
                from datetime import datetime
                dt = datetime.fromisoformat(completion_date_str.replace('Z', '+00:00'))
                date_str = dt.strftime('%B %d, %Y')
                summary_text += f"\n{date_str}"
            else:
                summary_text += "\nDate not available."

            # Parse the summary text and add it with basic formatting
            for line in summary_text.split('\n'):
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                if stripped_line.startswith('###'):
                    self.document.add_heading(line.replace('###', '').strip(), level=3)
                elif stripped_line.startswith('##'):
                     self.document.add_heading(line.replace('##', '').strip(), level=2)
                elif "Methodological & Bibliographical Summary" in stripped_line:
                    continue  # Skip the redundant title line
                elif stripped_line.startswith('- '): # Old format
                    self._add_summary_paragraph(stripped_line.lstrip('- '))
                elif stripped_line:
                    self._add_summary_paragraph(stripped_line)

        # 8. Add Page Numbers to Footer
        section = self.document.sections[0]
        footer = section.footer
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        add_page_number(p)

        # 9. Save Document
        self.document.save(self.output_path)
        print(f"Successfully generated combined Word document: {self.output_path}")


def main():
    """Command-line interface for the combined document generator."""
    parser = argparse.ArgumentParser(
        description='Generate a combined .docx file with main and college commentaries.'
    )
    parser.add_argument('psalm_number', type=int, help='Psalm number to generate')
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('output'),
        help='Output directory (default: output/)'
    )

    args = parser.parse_args()
    psalm_num = args.psalm_number
    psalm_num_str = f"{psalm_num:03d}"

    # Construct paths
    psalm_dir = args.output_dir / f"psalm_{psalm_num}"
    main_intro_path = psalm_dir / f"psalm_{psalm_num_str}_edited_intro.md"
    main_verses_path = psalm_dir / f"psalm_{psalm_num_str}_edited_verses.md"
    college_intro_path = psalm_dir / f"psalm_{psalm_num_str}_edited_intro_college.md"
    college_verses_path = psalm_dir / f"psalm_{psalm_num_str}_edited_verses_college.md"
    stats_path = psalm_dir / f"psalm_{psalm_num_str}_pipeline_summary.json"
    output_path = psalm_dir / f"psalm_{psalm_num_str}_commentary_combined.docx"

    # Check that all required files exist
    required_files = [
        main_intro_path, main_verses_path,
        college_intro_path, college_verses_path
    ]
    missing_files = [f for f in required_files if not f.exists()]

    if missing_files:
        print(f"Error: Missing required files:")
        for f in missing_files:
            print(f"  - {f}")
        return 1

    # Generate the combined document
    generator = CombinedDocumentGenerator(
        psalm_num=psalm_num,
        main_intro_path=main_intro_path,
        main_verses_path=main_verses_path,
        college_intro_path=college_intro_path,
        college_verses_path=college_verses_path,
        stats_path=stats_path,
        output_path=output_path
    )

    generator.generate()
    return 0


if __name__ == '__main__':
    sys.exit(main())
