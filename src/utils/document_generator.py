"""
Generates a print-ready Microsoft Word (.docx) document from the pipeline outputs.
This is designed to mirror the structure and content of the print_ready.md file.

This script takes the final edited introduction and verse commentaries,
parses them, and uses the python-docx library to create a well-formatted
Word document that preserves bidirectional text formatting for Hebrew and English.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from docx import Document
from docx.shared import Pt, RGBColor
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

class DocumentGenerator:
    """Generates a .docx commentary from pipeline artifacts."""

    def __init__(self, psalm_num: int, intro_path: Path, verses_path: Path, stats_path: Path, output_path: Path, reader_questions_path: Optional[Path] = None):
        self.psalm_num = psalm_num
        self.intro_path = intro_path
        self.verses_path = verses_path
        self.stats_path = stats_path
        self.output_path = output_path
        self.reader_questions_path = reader_questions_path
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
        # Base: Hebrew letter (U+05D0-U+05EA), maqqef (U+05BE), or space
        # Combining: U+0591-U+05BD, U+05BF, U+05C1-U+05C2, U+05C4-U+05C7
        cluster_pattern = r'[\u05D0-\u05EA\u05BE\s][\u0591-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C7]*'
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
        clusters = DocumentGenerator._split_into_grapheme_clusters(hebrew_text)
        # Reverse the order of clusters (but keep each cluster intact)
        reversed_clusters = clusters[::-1]
        return ''.join(reversed_clusters)

    @staticmethod
    def _is_primarily_hebrew(text: str) -> bool:
        """
        Detect if a line is a standalone Hebrew verse line (not mixed Hebrew/English).
        
        A line is a standalone Hebrew verse if:
        - Contains sof-pasuq (׃) - the Hebrew end-of-verse marker
        - Has very few or no ASCII letters (< 5% of total letters)
        
        This is intentionally strict to avoid triggering on English commentary
        paragraphs that contain many Hebrew quotations.
        """
        if not text.strip():
            return False
        
        # Must have sof-pasuq to be considered a complete Hebrew verse line
        has_sof_pasuq = '׃' in text
        if not has_sof_pasuq:
            return False
        
        # Count Hebrew letters (U+05D0-U+05EA)
        hebrew_letters = len(re.findall(r'[\u05D0-\u05EA]', text))
        # Count ASCII letters
        ascii_letters = len(re.findall(r'[a-zA-Z]', text))
        
        total_letters = hebrew_letters + ascii_letters
        if total_letters == 0:
            return False
        
        # Require very low ASCII ratio (< 5%) to be considered primarily Hebrew
        # This excludes mixed paragraphs like "This is the psalm's theological center..."
        ascii_ratio = ascii_letters / total_letters
        
        return ascii_ratio < 0.05

    @staticmethod
    def _reverse_primarily_hebrew_line(text: str) -> str:
        """
        Reverse an entire primarily-Hebrew line for correct RTL display in LTR paragraphs.
        
        Handles:
        - Hebrew words (reversed by grapheme clusters)
        - Punctuation mirroring (brackets/parentheses swap directions)
        - Spaces and separators
        
        The approach: split by spaces, reverse each Hebrew word, reverse the word order,
        mirror bracket characters.
        """
        LRO = '\u202D'  # LEFT-TO-RIGHT OVERRIDE
        PDF = '\u202C'  # POP DIRECTIONAL FORMATTING
        
        # Mirror map for brackets/parentheses - these need to swap in RTL
        MIRROR_MAP = {
            '(': ')',
            ')': '(',
            '[': ']',
            ']': '[',
            '{': '}',
            '}': '{',
            '<': '>',
            '>': '<',
        }
        
        # Pattern to split on word boundaries while keeping delimiters
        # This captures spaces, semicolons, parentheses, brackets
        tokens = re.split(r'(\s+|[;:,.()\[\]׃])', text)
        
        reversed_tokens = []
        for token in tokens:
            if not token:
                continue
            # If token contains Hebrew letters, reverse by grapheme clusters
            if re.search(r'[\u05D0-\u05EA]', token):
                reversed_token = DocumentGenerator._reverse_hebrew_by_clusters(token)
                reversed_tokens.append(reversed_token)
            elif token in MIRROR_MAP:
                # Mirror brackets/parentheses for RTL display
                reversed_tokens.append(MIRROR_MAP[token])
            else:
                # Keep other punctuation and spaces as-is
                reversed_tokens.append(token)
        
        # Reverse the entire token list to get RTL word order
        reversed_tokens.reverse()
        
        # Join and wrap with LRO to force display in reversed order
        result = ''.join(reversed_tokens)
        return f'{LRO}{result}{PDF}'

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
        """
        Explicitly set paragraph direction to LTR at the XML level.
        This prevents Word's bidi algorithm from reordering runs when there's mixed Hebrew/English.
        """
        pPr = paragraph._element.get_or_add_pPr()

        # Set bidi to 0 (LTR) - if the element exists and is 1, it means RTL
        bidi_elem = pPr.find(ns.qn('w:bidi'))
        if bidi_elem is not None:
            pPr.remove(bidi_elem)
        # Not setting w:bidi or setting it to 0 means LTR
        # We'll explicitly set it to 0 for clarity
        bidi_elem = OxmlElement('w:bidi')
        bidi_elem.set(ns.qn('w:val'), '0')
        pPr.append(bidi_elem)

    def _set_run_font_xml(self, run, font_name='Aptos', font_size=12):
        """
        Set font and size at the XML level for comprehensive coverage.
        This ensures the font applies to all character ranges (ASCII, complex script, etc.).
        This approach is more reliable than the high-level API for Hebrew text.
        """
        rPr = run._element.get_or_add_rPr()

        # Set rFonts element with all font attributes
        rFonts = rPr.find(ns.qn('w:rFonts'))
        if rFonts is None:
            rFonts = OxmlElement('w:rFonts')
            rPr.insert(0, rFonts)

        # Set font for all ranges: ascii, hAnsi (high ANSI), and cs (complex scripts)
        rFonts.set(ns.qn('w:ascii'), font_name)
        rFonts.set(ns.qn('w:hAnsi'), font_name)
        rFonts.set(ns.qn('w:cs'), font_name)

        # Set size at XML level
        sz = rPr.find(ns.qn('w:sz'))
        if sz is None:
            sz = OxmlElement('w:sz')
            rPr.append(sz)
        sz.set(ns.qn('w:val'), str(font_size * 2))  # Word uses half-points

        # Set complex script size
        szCs = rPr.find(ns.qn('w:szCs'))
        if szCs is None:
            szCs = OxmlElement('w:szCs')
            rPr.append(szCs)
        szCs.set(ns.qn('w:val'), str(font_size * 2))  # Word uses half-points

    def _add_paragraph_with_markdown(self, text: str, style: str = 'Normal'):
        """Adds a paragraph, parsing basic markdown for bold/italics, including nested formatting."""
        # Apply divine name modification to the entire paragraph text first.
        modified_text = self.modifier.modify_text(text)

        # Handle markdown headers first (check from most specific to least specific)
        if modified_text.startswith('####'):
            self.document.add_heading(modified_text.replace('####', '').strip(), level=4)
            return
        elif modified_text.startswith('###'):
            self.document.add_heading(modified_text.replace('###', '').strip(), level=3)
            return
        elif modified_text.startswith('##'):
            self.document.add_heading(modified_text.replace('##', '').strip(), level=2)
            return

        # Handle bullet lists (lines starting with "- ")
        is_bullet = False
        if modified_text.startswith('- '):
            modified_text = modified_text[2:]  # Remove "- " prefix
            is_bullet = True

        # Handle block quotes (lines starting with ">")
        is_quote = False
        if modified_text.startswith('>'):
            # Check if it's an empty quote line (just ">" with optional spaces)
            quote_text = modified_text[1:].lstrip()  # Remove ">" and any leading spaces
            if not quote_text:
                # Empty quote line - just add a blank paragraph and return
                self.document.add_paragraph()
                return
            modified_text = quote_text
            is_quote = True

        p = self.document.add_paragraph(style=style)

        # Apply bullet formatting if this is a list item
        if is_bullet:
            p.style = 'List Bullet'

        # Apply quote formatting if this is a block quote
        if is_quote:
            from docx.shared import Inches
            p.paragraph_format.left_indent = Inches(0.5)

        # Explicitly set paragraph to LTR to prevent Word's bidi algorithm from reordering runs
        self._set_paragraph_ltr(p)

        # Use the centralized formatting method with font setting for bullets
        self._process_markdown_formatting(p, modified_text, set_font=is_bullet)

        # Make block quotes italic
        if is_quote:
            for run in p.runs:
                run.italic = True

    def _process_introduction_content(self, text: str, style: str = 'Normal'):
        """
        Process introduction content, preserving headers while properly handling blockquotes.
        This method processes line by line, treating headers specially but using
        _add_commentary_with_bullets logic for blockquotes.
        """
        lines = text.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Handle liturgical section marker - convert to proper heading
            if line == '---LITURGICAL-SECTION-START---':
                self.document.add_heading('Modern Jewish Liturgical Use', level=2)
                i += 1
                continue

            # Handle headers
            if line.startswith('####'):
                self.document.add_heading(line.replace('####', '').strip(), level=4)
                i += 1
                continue
            elif line.startswith('###'):
                self.document.add_heading(line.replace('###', '').strip(), level=3)
                i += 1
                continue
            elif line.startswith('##'):
                self.document.add_heading(line.replace('##', '').strip(), level=2)
                i += 1
                continue

            # Handle blockquotes - collect consecutive blockquote lines
            if line.startswith('>'):
                quote_block = []
                while i < len(lines) and lines[i].strip() and lines[i].strip().startswith('>'):
                    quote_text = lines[i].strip()[1:].lstrip()  # Remove ">" and leading spaces
                    if quote_text:  # Only add non-empty quote lines
                        quote_block.append(quote_text)
                    i += 1

                # Add quote block as indented italic paragraphs
                from docx.shared import Inches
                for quote_text in quote_block:
                    p = self.document.add_paragraph(style=style)
                    p.paragraph_format.left_indent = Inches(0.5)
                    self._set_paragraph_ltr(p)
                    self._process_markdown_formatting(p, quote_text, set_font=True)
                    # Make the entire quote italic
                    for run in p.runs:
                        run.italic = True
                continue

            # Handle regular paragraphs
            # Only treat as bullet if it's a true markdown list item with clear list markers
            # and not regular text that happens to start with dash
            # True bullets typically are short, start with lowercase, or are part of a clear list pattern
            original_line = lines[i]  # Keep original line for indentation detection
            is_true_bullet = (
                original_line.lstrip().startswith('- ') and
                len(original_line.strip()) > 5 and
                # Don't treat as bullet if it starts with uppercase letter followed by common sentence patterns
                not (
                    original_line.lstrip()[2:3].isupper() and
                    (':' in original_line[:50] or 'In ' in original_line[:10] or 'As ' in original_line[:10] or 'For ' in original_line[:10])
                )
            )

            if is_true_bullet:
                # Bullet point - detect leading indentation
                leading_spaces = len(original_line) - len(original_line.lstrip())
                p = self.document.add_paragraph(style='List Bullet')
                self._set_paragraph_ltr(p)

                # Apply indentation if present (convert spaces to inches)
                if leading_spaces > 0:
                    from docx.shared import Inches
                    # Approximately 6 spaces = 0.25 inch, scale accordingly
                    indent_inches = leading_spaces * 0.04  # Rough conversion: 1 space ≈ 0.04 inches
                    p.paragraph_format.left_indent = Inches(indent_inches)

                bullet_text = original_line.lstrip()[2:]  # Remove leading spaces and "- " prefix
                self._process_markdown_formatting(p, bullet_text, set_font=True)
            else:
                # Regular paragraph - use _add_paragraph_with_markdown which handles dash characters properly
                self._add_paragraph_with_markdown(line, style=style)

            i += 1

    def _add_commentary_with_bullets(self, text: str, style: str = 'Normal'):
        """
        Adds commentary text, intelligently handling bullet lists and regular text.
        Bullet list items (lines starting with "- ") are converted to proper Word bullets.
        Regular text blocks use soft breaks, with empty lines creating paragraph breaks.
        """
        lines = text.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this is an empty line (paragraph break)
            if not line.strip():
                i += 1
                continue

            # Check if this is a true bullet item (not just regular text starting with dash)
            original_line = line  # Keep original line for indentation detection
            line_stripped = line.strip()
            is_true_bullet = (
                line_stripped.startswith('- ') and
                len(line_stripped) > 5 and
                # Don't treat as bullet if it starts with uppercase letter followed by common sentence patterns
                not (
                    line_stripped[2:3].isupper() and
                    (':' in line_stripped[:50] or 'In ' in line_stripped[:10] or 'As ' in line_stripped[:10] or 'For ' in line_stripped[:10])
                )
            )

            if is_true_bullet:
                # Collect consecutive bullet items with indentation info
                bullet_block = []
                while i < len(lines) and lines[i].strip() and lines[i].lstrip().startswith('- '):
                    # Apply same logic to consecutive lines
                    bullet_line = lines[i]
                    bullet_stripped = bullet_line.strip()
                    is_consecutive_bullet = (
                        len(bullet_stripped) > 5 and
                        not (
                            bullet_stripped[2:3].isupper() and
                            (':' in bullet_stripped[:50] or 'In ' in bullet_stripped[:10] or 'As ' in bullet_stripped[:10] or 'For ' in bullet_stripped[:10])
                        )
                    )
                    if is_consecutive_bullet:
                        # Store both the bullet text and indentation info
                        leading_spaces = len(bullet_line) - len(bullet_line.lstrip())
                        bullet_text = bullet_line.lstrip()[2:]  # Remove "- " prefix
                        bullet_block.append((bullet_text, leading_spaces))
                        i += 1
                    else:
                        break

                # Add each bullet as a separate paragraph with proper indentation
                for bullet_text, leading_spaces in bullet_block:
                    p = self.document.add_paragraph(style='List Bullet')
                    # Explicitly set paragraph to LTR to prevent Word's bidi algorithm from reordering runs
                    self._set_paragraph_ltr(p)

                    # Apply indentation if present (convert spaces to inches)
                    if leading_spaces > 0:
                        from docx.shared import Inches
                        # Approximately 6 spaces = 0.25 inch, scale accordingly
                        indent_inches = leading_spaces * 0.04  # Rough conversion: 1 space ≈ 0.04 inches
                        p.paragraph_format.left_indent = Inches(indent_inches)

                    # Process markdown formatting in bullet text with explicit font
                    self._process_markdown_formatting(p, bullet_text, set_font=True)
            # Check if this is a markdown heading (###, ##, ####)
            elif line_stripped.startswith('#'):
                # Parse heading level and text
                heading_match = re.match(r'^(#{1,6})\s+(.+)$', line_stripped)
                if heading_match:
                    hashes = heading_match.group(1)
                    heading_text = heading_match.group(2)
                    # Map markdown heading levels to Word heading levels
                    # ## = Heading 2, ### = Heading 3, #### = Heading 4
                    level = len(hashes)
                    word_heading_level = min(level, 4)  # Cap at Heading 4

                    # Add as a Word heading
                    p = self.document.add_heading(heading_text, level=word_heading_level)
                    self._set_paragraph_ltr(p)
                else:
                    # Malformed heading, treat as normal text
                    p = self.document.add_paragraph(style=style)
                    self._set_paragraph_ltr(p)
                    self._process_markdown_formatting(p, line_stripped, set_font=False)
                i += 1
            # Check if this is a block quote
            elif line_stripped.startswith('>'):
                # Collect consecutive block quote lines
                quote_block = []
                while i < len(lines) and lines[i].strip() and lines[i].strip().startswith('>'):
                    # Remove ">" and any leading spaces after it
                    quote_text = lines[i].strip()[1:].lstrip()
                    quote_block.append(quote_text)
                    i += 1

                # Add each quote line as a separate paragraph with indentation and italic
                from docx.shared import Inches
                for quote_text in quote_block:
                    if not quote_text:
                        # Empty quote line - add a blank paragraph
                        self.document.add_paragraph()
                    else:
                        # Non-empty quote line
                        p = self.document.add_paragraph(style=style)
                        p.paragraph_format.left_indent = Inches(0.5)
                        # Explicitly set paragraph to LTR to prevent Word's bidi algorithm from reordering runs
                        self._set_paragraph_ltr(p)
                        # Process markdown formatting in quote text with explicit font
                        self._process_markdown_formatting(p, quote_text, set_font=True)
                        # Make the entire quote italic
                        for run in p.runs:
                            run.italic = True
            else:
                # Collect consecutive non-bullet, non-quote, non-empty lines until we hit an empty line or special formatting
                text_block = []
                while i < len(lines) and lines[i].strip():
                    original_line = lines[i]
                    line_stripped = original_line.strip()
                    # Apply same bullet detection logic
                    is_bullet = (
                        line_stripped.startswith('- ') and
                        len(line_stripped) > 5 and
                        not (
                            line_stripped[2:3].isupper() and
                            (':' in line_stripped[:50] or 'In ' in line_stripped[:10] or 'As ' in line_stripped[:10] or 'For ' in line_stripped[:10])
                        )
                    )

                    # Stop if we hit a bullet, quote, or markdown heading
                    if not is_bullet and not line_stripped.startswith('>') and not line_stripped.startswith('#'):
                        text_block.append(original_line)
                        i += 1
                    else:
                        break

                # Add as a paragraph with soft breaks
                if text_block:
                    self._add_paragraph_with_soft_breaks('\n'.join(text_block), style=style)

    def _process_markdown_formatting(self, paragraph, text, set_font=False):
        """
        Process markdown formatting (bold, italic, etc.) and add runs to the given paragraph.
        This is a helper for adding formatted text to an existing paragraph.

        Args:
            paragraph: The paragraph to add runs to
            text: The text to process
            set_font: If True, explicitly set Aptos 12pt font on all runs (for bullet lists)
        """
        modified_text = self.modifier.modify_text(text)
        # Match bold (**...**) and italic (*...*) patterns
        # Order matters: match ** before * to avoid incorrect splits
        parts = re.split(r'(\*\*.*?\*\*|__.*?__|\*.*?\*|_.*?_|`.*?`)', modified_text)

        for part in parts:
            if not part:
                continue
            if part.startswith('**') and part.endswith('**'):
                # Bold text - recursively process inner content for nested formatting
                inner_content = part[2:-2]
                self._add_formatted_content(paragraph, inner_content, bold=True, italic=False, set_font=set_font)
            elif part.startswith('__') and part.endswith('__'):
                # Bold text - recursively process inner content for nested formatting
                inner_content = part[2:-2]
                self._add_formatted_content(paragraph, inner_content, bold=True, italic=False, set_font=set_font)
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
            elif part.startswith('`') and part.endswith('`'):
                inner_content = part[1:-1]
                self._add_nested_formatting(paragraph, inner_content, base_italic=True)
                # Note: nested formatting handles its own font settings
            else:
                # Check if this is a primarily-Hebrew line (like a verse text)
                # If so, apply full-line RTL reversal for correct display
                if self._is_primarily_hebrew(part):
                    modified_part = self._reverse_primarily_hebrew_line(part)
                    run = paragraph.add_run(modified_part)
                else:
                    # Handle parenthesized Hebrew with grapheme cluster reversal + LRO
                    # Solution: Reverse Hebrew by clusters, then apply LEFT-TO-RIGHT OVERRIDE
                    # This keeps text inside parentheses with correct RTL appearance
                    hebrew_paren_pattern = r'\(([\u0590-\u05FF\u05B0-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C7\s]+)\)'
                    # Also handle square brackets (used for Ketiv/Qere textual variants)
                    hebrew_bracket_pattern = r'\[([\u0590-\u05FF\u05B0-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C7\s]+)\]'
                    
                    modified_part = part
                    LRO = '\u202D'  # LEFT-TO-RIGHT OVERRIDE
                    PDF = '\u202C'  # POP DIRECTIONAL FORMATTING
                    
                    if re.search(hebrew_paren_pattern, modified_part):
                        def reverse_hebrew_paren(match):
                            hebrew_text = match.group(1)
                            reversed_hebrew = self._reverse_hebrew_by_clusters(hebrew_text)
                            return f'{LRO}({reversed_hebrew}){PDF}'
                        modified_part = re.sub(hebrew_paren_pattern, reverse_hebrew_paren, modified_part)
                    
                    if re.search(hebrew_bracket_pattern, modified_part):
                        def reverse_hebrew_bracket(match):
                            hebrew_text = match.group(1)
                            reversed_hebrew = self._reverse_hebrew_by_clusters(hebrew_text)
                            return f'{LRO}[{reversed_hebrew}]{PDF}'
                        modified_part = re.sub(hebrew_bracket_pattern, reverse_hebrew_bracket, modified_part)
                    
                    run = paragraph.add_run(modified_part)

                if set_font:
                    run.font.name = 'Aptos'
                    run.font.size = Pt(12)

    def _add_formatted_content(self, paragraph, text, bold=False, italic=False, set_font=False):
        """
        Add text content with specified formatting, recursively processing any nested markdown.
        This handles cases like **bold (*italic inside bold*)**.

        Args:
            paragraph: The paragraph to add runs to
            text: The text content to add
            bold: Whether the text should be bold
            italic: Whether the text should be italic
            set_font: If True, explicitly set Aptos 12pt font
        """
        # Check if there's nested formatting to process
        if '*' in text or '_' in text or '`' in text:
            # Split on italic markers to handle nested formatting
            parts = re.split(r'(\*.*?\*|_.*?_|`.*?`)', text)
            for part in parts:
                if not part:
                    continue
                if part.startswith('*') and part.endswith('*') and not part.startswith('**'):
                    # Nested italic
                    run = paragraph.add_run(part[1:-1])
                    run.bold = bold
                    run.italic = True  # Nested italic
                    if set_font:
                        run.font.name = 'Aptos'
                        run.font.size = Pt(12)
                elif part.startswith('_') and part.endswith('_') and not part.startswith('__'):
                    # Nested italic
                    run = paragraph.add_run(part[1:-1])
                    run.bold = bold
                    run.italic = True  # Nested italic
                    if set_font:
                        run.font.name = 'Aptos'
                        run.font.size = Pt(12)
                elif part.startswith('`') and part.endswith('`'):
                    # Nested backtick - process with _add_nested_formatting but apply bold too
                    inner_content = part[1:-1]
                    # For backticks, we need to handle bold + italic
                    nested_parts = re.split(r'(\*\*.*?\*\*)', inner_content)
                    for nested_part in nested_parts:
                        if nested_part.startswith('**') and nested_part.endswith('**'):
                            run = paragraph.add_run(nested_part[2:-2])
                            run.bold = True
                            run.italic = True
                        else:
                            run = paragraph.add_run(nested_part)
                            run.bold = bold
                            run.italic = True
                        if set_font:
                            run.font.name = 'Aptos'
                            run.font.size = Pt(12)
                else:
                    # Regular text with base formatting
                    # Check if primarily Hebrew and apply full-line reversal
                    if self._is_primarily_hebrew(part):
                        modified_part = self._reverse_primarily_hebrew_line(part)
                        run = paragraph.add_run(modified_part)
                    else:
                        # Handle parenthesized/bracketed Hebrew with grapheme cluster reversal + LRO
                        hebrew_paren_pattern = r'\(([\u0590-\u05FF\u05B0-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C7\s]+)\)'
                        hebrew_bracket_pattern = r'\[([\u0590-\u05FF\u05B0-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C7\s]+)\]'
                        
                        modified_part = part
                        LRO = '\u202D'  # LEFT-TO-RIGHT OVERRIDE
                        PDF = '\u202C'  # POP DIRECTIONAL FORMATTING
                        
                        if re.search(hebrew_paren_pattern, modified_part):
                            def reverse_hebrew_paren(match):
                                hebrew_text = match.group(1)
                                reversed_hebrew = self._reverse_hebrew_by_clusters(hebrew_text)
                                return f'{LRO}({reversed_hebrew}){PDF}'
                            modified_part = re.sub(hebrew_paren_pattern, reverse_hebrew_paren, modified_part)
                        
                        if re.search(hebrew_bracket_pattern, modified_part):
                            def reverse_hebrew_bracket(match):
                                hebrew_text = match.group(1)
                                reversed_hebrew = self._reverse_hebrew_by_clusters(hebrew_text)
                                return f'{LRO}[{reversed_hebrew}]{PDF}'
                            modified_part = re.sub(hebrew_bracket_pattern, reverse_hebrew_bracket, modified_part)
                        
                        run = paragraph.add_run(modified_part)
                    run.bold = bold
                    run.italic = italic
                    if set_font:
                        run.font.name = 'Aptos'
                        run.font.size = Pt(12)
        else:
            # No nested formatting - just add with base formatting
            # Check if primarily Hebrew and apply full-line reversal
            if self._is_primarily_hebrew(text):
                modified_text = self._reverse_primarily_hebrew_line(text)
                run = paragraph.add_run(modified_text)
            else:
                # Handle parenthesized/bracketed Hebrew with grapheme cluster reversal + LRO
                hebrew_paren_pattern = r'\(([\u0590-\u05FF\u05B0-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C7\s]+)\)'
                hebrew_bracket_pattern = r'\[([\u0590-\u05FF\u05B0-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C7\s]+)\]'
                
                modified_text = text
                LRO = '\u202D'  # LEFT-TO-RIGHT OVERRIDE
                PDF = '\u202C'  # POP DIRECTIONAL FORMATTING
                
                if re.search(hebrew_paren_pattern, modified_text):
                    def reverse_hebrew_paren(match):
                        hebrew_text = match.group(1)
                        reversed_hebrew = self._reverse_hebrew_by_clusters(hebrew_text)
                        return f'{LRO}({reversed_hebrew}){PDF}'
                    modified_text = re.sub(hebrew_paren_pattern, reverse_hebrew_paren, modified_text)
                
                if re.search(hebrew_bracket_pattern, modified_text):
                    def reverse_hebrew_bracket(match):
                        hebrew_text = match.group(1)
                        reversed_hebrew = self._reverse_hebrew_by_clusters(hebrew_text)
                        return f'{LRO}[{reversed_hebrew}]{PDF}'
                    modified_text = re.sub(hebrew_bracket_pattern, reverse_hebrew_bracket, modified_text)
                
                run = paragraph.add_run(modified_text)
            run.bold = bold
            run.italic = italic
            if set_font:
                run.font.name = 'Aptos'
                run.font.size = Pt(12)

    def _add_paragraph_with_soft_breaks(self, text: str, style: str = 'Normal'):
        """Adds a single paragraph, treating newlines as soft breaks, with nested formatting support."""
        modified_text = self.modifier.modify_text(text)
        p = self.document.add_paragraph(style=style)

        # Explicitly set paragraph to LTR to prevent Word's bidi algorithm from reordering runs
        self._set_paragraph_ltr(p)

        # Split the entire text by markdown markers first
        parts = re.split(r'(\$\$|__.*?__|\*.*?\*|_.*?_|`.*?`)', modified_text)

        for part in parts:
            is_bold = (part.startswith('**') and part.endswith('**')) or \
                      (part.startswith('__') and part.endswith('__'))
            is_backtick = part.startswith('`') and part.endswith('`')
            is_italic = (part.startswith('*') and part.endswith('*')) or \
                        (part.startswith('_') and part.endswith('_')) or \
                        is_backtick

            content = part[2:-2] if is_bold else (part[1:-1] if is_italic else part)

            # Handle backticks with nested bold (for stressed syllables)
            if is_backtick:
                self._add_nested_formatting_with_breaks(p, content, base_italic=True)
            else:
                # Handle soft breaks within the content
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line:
                        # Check if this is a primarily-Hebrew line (like a verse text)
                        if self._is_primarily_hebrew(line):
                            modified_line = self._reverse_primarily_hebrew_line(line)
                            run = p.add_run(modified_line)
                        else:
                            # Handle parenthesized/bracketed Hebrew with grapheme cluster reversal + LRO
                            hebrew_paren_pattern = r'\(([\u0590-\u05FF\u05B0-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C7\s]+)\)'
                            hebrew_bracket_pattern = r'\[([\u0590-\u05FF\u05B0-\u05BD\u05BF\u05C1-\u05C2\u05C4-\u05C7\s]+)\]'
                            
                            modified_line = line
                            LRO = '\u202D'  # LEFT-TO-RIGHT OVERRIDE
                            PDF = '\u202C'  # POP DIRECTIONAL FORMATTING
                            
                            if re.search(hebrew_paren_pattern, modified_line):
                                def reverse_hebrew_paren(match):
                                    hebrew_text = match.group(1)
                                    reversed_hebrew = self._reverse_hebrew_by_clusters(hebrew_text)
                                    return f'{LRO}({reversed_hebrew}){PDF}'
                                modified_line = re.sub(hebrew_paren_pattern, reverse_hebrew_paren, modified_line)
                            
                            if re.search(hebrew_bracket_pattern, modified_line):
                                def reverse_hebrew_bracket(match):
                                    hebrew_text = match.group(1)
                                    reversed_hebrew = self._reverse_hebrew_by_clusters(hebrew_text)
                                    return f'{LRO}[{reversed_hebrew}]{PDF}'
                                modified_line = re.sub(hebrew_bracket_pattern, reverse_hebrew_bracket, modified_line)
                            
                            run = p.add_run(modified_line)
                        run.bold = is_bold
                        run.italic = is_italic
                    if i < len(lines) - 1:
                        p.add_run().add_break()

    def _add_nested_formatting(self, paragraph, text: str, base_italic: bool = False):
        """
        Add text with nested formatting (e.g., **BOLD** inside italic context).
        Used for phonetic transcriptions where stressed syllables are in **BOLD CAPS**.

        Args:
            paragraph: The docx paragraph object to add runs to
            text: The text content (e.g., "tə-**HIL**-lāh")
            base_italic: Whether the base text should be italic (True for backtick context)
        """
        # Split by bold markers
        parts = re.split(r'(\$\$|\*\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                # Bold text (stressed syllable)
                run = paragraph.add_run(part[2:-2])
                run.bold = True
                run.italic = base_italic  # Maintain italic if in backtick context
            else:
                # Regular text
                run = paragraph.add_run(part)
                run.italic = base_italic

    def _add_nested_formatting_with_breaks(self, paragraph, text: str, base_italic: bool = False):
        """
        Add text with nested formatting AND support for soft breaks.
        Used for phonetic transcriptions in verse commentary.

        Args:
            paragraph: The docx paragraph object to add runs to
            text: The text content with possible newlines
            base_italic: Whether the base text should be italic
        """
        # First split by newlines
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if line:
                # Then handle bold within each line
                parts = re.split(r'(\$\$|\*\*)', line)
                for part in parts:
                    if part.startswith('**') and part.endswith('**'):
                        run = paragraph.add_run(part[2:-2])
                        run.bold = True
                        run.italic = base_italic
                    else:
                        run = paragraph.add_run(part)
                        run.italic = base_italic
            if i < len(lines) - 1:
                paragraph.add_run().add_break()

    def _add_bilingual_verse(self, hebrew: str, english: str):
        """Adds a formatted bilingual verse line with Hebrew (RTL) and English (LTR)."""
        p = self.document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # Apply divine name modification to the Hebrew text
        modified_hebrew = self.modifier.modify_text(hebrew)

        # Add Hebrew text with RTL properties
        hebrew_run = p.add_run(modified_hebrew)
        hebrew_run.font.name = 'SBL Hebrew'
        hebrew_run.font.size = Pt(14)
        hebrew_run.font.rtl = True

        # Add separator (tabs work well in Word)
        p.add_run('\t\t')

        # Add English text
        english_run = p.add_run(english)
        english_run.font.name = 'Times New Roman'
        english_run.font.size = Pt(12)
        english_run.italic = True

    def _parse_verse_commentary(self, content: str, psalm_text_data: Dict[int, Dict[str, str]]) -> List[Dict[str, str]]:
        """Parses the verse-by-verse commentary file.

        Handles both single verses (Verse 1) and verse ranges (Verses 21-25).
        For ranges, returns a single entry with 'number' as the range string (e.g., '21-25')
        and 'verse_range' as a tuple (start, end).
        """
        verses = []
        # Try multiple formats: "**Verse(s) X(-Y)**" (main format), "### Verse(s) X(-Y)" (college format), "Verse(s) X(-Y)" (fallback)
        # First try the expected bold format - matches both single and range verses
        verse_blocks = re.split(r'(?=^\*\*Verses? [\d\-–]+.*?\*\*\s*\n)', content, flags=re.MULTILINE)

        # If no verses found with bold format, try heading format (college uses this)
        if len(verse_blocks) <= 1:
            verse_blocks = re.split(r'(?=^#{2,} Verses? [\d\-–]+)', content, flags=re.MULTILINE)

        # If still no verses found, try plain format without any markdown
        if len(verse_blocks) <= 1:
            verse_blocks = re.split(r'(?=^Verses? [\d\-–]+)', content, flags=re.MULTILINE)

        for block in verse_blocks:
            block = block.strip()
            if not block.strip():
                continue

            lines = block.strip().split('\n', 1)  # Split only on the first newline

            # Try all formats for verse number matching (single or range)
            # Matches: **Verse 1**, **Verses 21-25**, **Verses 21–25 (description)**, etc.
            verse_num_match = re.match(r'^\*\*Verses? ([\d]+)(?:[\-–]([\d]+))?\s*.*?\*\*', lines[0])  # Bold format
            if not verse_num_match:
                # Heading format: ### Verse 1, ### Verses 21-25 (description), etc.
                verse_num_match = re.match(r'^#{2,} Verses? ([\d]+)(?:[\-–]([\d]+))?\s*', lines[0])
            if not verse_num_match:
                # Plain format: Verse 1, Verses 21-25, etc.
                verse_num_match = re.match(r'^Verses? ([\d]+)(?:[\-–]([\d]+))?\s*', lines[0])

            if not verse_num_match:
                continue

            start_verse = verse_num_match.group(1)
            end_verse = verse_num_match.group(2)  # None if single verse

            if end_verse:
                # It's a range
                verse_num = f"{start_verse}-{end_verse}"
                verse_range = (int(start_verse), int(end_verse))
            else:
                # Single verse
                verse_num = start_verse
                verse_range = None

            commentary_text = '\n'.join(lines[1:]).strip()

            # Get Hebrew/English text from the database data
            # For ranges, we'll get the first verse's text as representative
            verse_info = psalm_text_data.get(int(start_verse), {})
            hebrew_text = verse_info.get('hebrew', '[Hebrew text not found]')
            english_text = verse_info.get('english', '[English text not found]')

            verse_entry = {
                "number": verse_num,
                "hebrew": hebrew_text,
                "english": english_text,
                "commentary": commentary_text
            }

            if verse_range:
                verse_entry["verse_range"] = verse_range

            verses.append(verse_entry)

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

        # Figurative parallels breakdown
        figurative_parallels = research_data.get('figurative_parallels_reviewed', {})
        figurative_breakdown_str = ""
        if figurative_parallels:
            items = [f"{v} ({c})" for v, c in sorted(figurative_parallels.items())]
            figurative_breakdown_str = f" ({'; '.join(items)})"

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

        # Deep Web Research status
        deep_research_available = research_data.get('deep_research_available', False)
        deep_research_included = research_data.get('deep_research_included', False)
        deep_research_removed = research_data.get('deep_research_removed_for_space', False)

        if deep_research_included:
            deep_research_str = "Yes"
        elif deep_research_removed:
            deep_research_str = "No (removed for space)"
        elif deep_research_available:
            deep_research_str = "No (available but not included)"
        else:
            deep_research_str = "No"

        # Sections trimmed for context length
        sections_trimmed = research_data.get('sections_trimmed', [])
        if sections_trimmed:
            sections_trimmed_str = ", ".join(sections_trimmed)
        else:
            sections_trimmed_str = "None"

        # --- Models Used --- (This section will be built from the markdown in the generate() method)
        models_used_str = "### Models Used"

        summary = f"""
Methodological & Bibliographical Summary

### Research & Data Inputs
**Psalm Verses Analyzed**: {verse_count}
**LXX (Septuagint) Verses Reviewed**: {verse_count}
**Phonetic Transcriptions Generated**: {verse_count}
**Ugaritic Parallels Reviewed**: {ugaritic_count}
**Lexicon Entries (BDB/Klein) Reviewed**: {lexicon_count}
**Traditional Commentaries Reviewed**: {total_commentaries}{commentary_details}
**Concordance Entries Reviewed**: {concordance_total if concordance_total > 0 else 'N/A'}
**Figurative Concordance Matches Reviewed**: {figurative_total if figurative_total > 0 else 'N/A'}{figurative_breakdown_str}
**Rabbi Jonathan Sacks References Reviewed**: {sacks_count if sacks_count > 0 else 'N/A'}
**Similar Psalms Analyzed**: {related_psalms_str}
**Deep Web Research**: {deep_research_str}
**Sections Trimmed for Context**: {sections_trimmed_str}
**Master Editor Prompt Size**: {prompt_chars_str}

{models_used_str}
        """.strip()
        return summary

    def _add_summary_paragraph(self, line: str):
        """Adds a paragraph to the summary, bolding the label."""
        p = self.document.add_paragraph(style='SummaryText')
        if ':' in line:
            label, value = line.split(':', 1)
            p.add_run(label.strip().strip('**')).bold = True
            p.add_run(f":{value}")
        else:
            p.add_run(line)

    def generate(self):
        """Main method to generate the .docx file, mirroring print_ready.md structure."""
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

        # 2b. Add Questions for the Reader (if available)
        if self.reader_questions_path and self.reader_questions_path.exists():
            try:
                questions_data = json.loads(self.reader_questions_path.read_text(encoding='utf-8'))
                questions = questions_data.get('curated_questions', [])
                if questions:
                    self.document.add_heading('Questions for the Reader', level=2)
                    
                    # Add introductory italic text
                    intro_p = self.document.add_paragraph(style='BodySans')
                    intro_run = intro_p.add_run('Before reading this commentary, consider the following questions:')
                    intro_run.italic = True
                    
                    # Add each question as a numbered paragraph
                    for i, question in enumerate(questions, 1):
                        q_p = self.document.add_paragraph(style='BodySans')
                        q_p.add_run(f"{i}. ").bold = True
                        self._process_markdown_formatting(q_p, question, set_font=False)
                    
                    # Add spacing after questions
                    self.document.add_paragraph()
            except Exception as e:
                # Log but don't fail if questions can't be loaded
                print(f"Warning: Could not load reader questions: {e}")

        # 3. Add Introduction
        self.document.add_heading('Introduction', level=2)
        intro_content = self.intro_path.read_text(encoding='utf-8')
        # Use _add_commentary_with_bullets to properly handle blockquotes while preserving headers
        self._process_introduction_content(intro_content.strip(), style='BodySans')

        # 4. Add Verse-by-Verse Commentary
        self.document.add_heading('Verse-by-Verse Commentary', level=2)
        verses_content = self.modifier.modify_text(self.verses_path.read_text(encoding='utf-8'))
        parsed_verses = self._parse_verse_commentary(verses_content, psalm_text_data)

        for verse in parsed_verses:
            self.document.add_heading(f'Verse {verse["number"]}', level=3)

            # Commentary now includes the verse text with punctuation from the LLM
            self._add_commentary_with_bullets(verse["commentary"], style='BodySans')

        # 5. Add Methodological Summary
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
                
                if 'liturgical_librarian' in model_usage:
                    summary_text += f"\n**Liturgical Librarian**: {model_usage.get('liturgical_librarian', 'N/A')}"
                
                if 'figurative_curator' in model_usage:
                    summary_text += f"\n**Figurative Curator**: {model_usage.get('figurative_curator', 'N/A')}"
                
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

        # 6. Add Page Numbers to Footer
        section = self.document.sections[0]
        footer = section.footer
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        add_page_number(p)

        # 6. Save Document
        self.document.save(self.output_path)
        print(f"Successfully generated Word document: {self.output_path}")


def main():
    """Command-line interface for the document generator."""
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Generate a .docx commentary from pipeline outputs.")
    parser.add_argument("--psalm", type=int, required=True, help="Psalm number.")
    parser.add_argument("--intro", type=Path, required=True, help="Path to the edited introduction markdown file.")
    parser.add_argument("--verses", type=Path, required=True, help="Path to the edited verses markdown file.")
    parser.add_argument("--stats", type=Path, required=True, help="Path to the pipeline_stats.json file.")
    parser.add_argument("--output", type=Path, required=True, help="Path to save the final .docx file.")
    args = parser.parse_args()

    if not args.intro.exists():
        print(f"Error: Introduction file not found at {args.intro}")
        sys.exit(1)
    if not args.verses.exists():
        print(f"Error: Verses file not found at {args.verses}")
        sys.exit(1)
    if not args.stats.exists():
        print(f"Warning: Stats file not found at {args.stats}. Bibliographical summary will be skipped.")

    generator = DocumentGenerator(
        psalm_num=args.psalm,
        intro_path=args.intro,
        verses_path=args.verses,
        stats_path=args.stats,
        output_path=args.output
    )
    generator.generate()


if __name__ == "__main__":
    main()
