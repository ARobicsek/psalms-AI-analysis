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
from typing import Any, Dict, List

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, ns 

# Handle imports for both module and script usage
if __name__ == '__main__' and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from src.data_sources.tanakh_database import TanakhDatabase
    from src.utils.divine_names_modifier import DivineNamesModifier
else:
    from ..data_sources.tanakh_database import TanakhDatabase
    from .divine_names_modifier import DivineNamesModifier


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

    def __init__(self, psalm_num: int, intro_path: Path, verses_path: Path, stats_path: Path, output_path: Path):
        self.psalm_num = psalm_num
        self.intro_path = intro_path
        self.verses_path = verses_path
        self.stats_path = stats_path
        self.output_path = output_path
        self.document = Document()
        self._set_default_styles()
        self.modifier = DivineNamesModifier()

    def _set_default_styles(self):
        """Set default font for the document."""
        # Set default font
        font = self.document.styles['Normal'].font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        
        # Create a new style for the sans-serif body text
        style = self.document.styles.add_style('BodySans', 1) # 1 for paragraph style
        style.base_style = self.document.styles['Normal']
        style.font.name = 'Aptos'
        style.font.size = Pt(11) # Aptos is a bit larger, so 11pt is a good equivalent to 12pt Times

        # Set spacing for all heading levels to be tighter
        for i in range(1, 5):
            style = self.document.styles[f'Heading {i}']
            style.paragraph_format.space_before = Pt(12)
            style.paragraph_format.space_after = Pt(4)

        # Set paragraph spacing to be tighter (soft breaks)
        style = self.document.styles['Normal']
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(8)

    def _add_paragraph_with_markdown(self, text: str, style: str = 'Normal'):
        """Adds a paragraph, parsing basic markdown for bold/italics."""
        # Apply divine name modification to the entire paragraph text first.
        modified_text = self.modifier.modify_text(text)

        p = self.document.add_paragraph(style=style)
        # Split by bold/italic markers
        parts = re.split(r'(\*\*.*?\*\*|__.*?__|\*.*?\*|_.*?_|`.*?`)', modified_text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                run = p.add_run(part[2:-2])
                run.bold = True
            elif part.startswith('__') and part.endswith('__'):
                run = p.add_run(part[2:-2])
                run.bold = True
            elif part.startswith('*') and part.endswith('*'):
                run = p.add_run(part[1:-1])
                run.italic = True
            elif part.startswith('_') and part.endswith('_'):
                run = p.add_run(part[1:-1])
                run.italic = True
            elif part.startswith('`') and part.endswith('`'):
                run = p.add_run(part[1:-1])
                run.italic = True
            else:
                p.add_run(part)

    def _add_paragraph_with_soft_breaks(self, text: str, style: str = 'Normal'):
        """Adds a single paragraph, treating newlines as soft breaks."""
        modified_text = self.modifier.modify_text(text)
        p = self.document.add_paragraph(style=style)
        
        # Split the entire text by markdown markers first
        parts = re.split(r'(\*\*.*?\*\*|__.*?__|\*.*?\*|_.*?_|`.*?`)', modified_text)
        
        for part in parts:
            is_bold = (part.startswith('**') and part.endswith('**')) or \
                      (part.startswith('__') and part.endswith('__'))
            is_italic = (part.startswith('*') and part.endswith('*')) or \
                        (part.startswith('_') and part.endswith('_')) or \
                        (part.startswith('`') and part.endswith('`'))

            content = part[2:-2] if is_bold else (part[1:-1] if is_italic else part)
            
            # Now, handle soft breaks within the content
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line:
                    run = p.add_run(line)
                    run.bold = is_bold
                    run.italic = is_italic
                if i < len(lines) - 1:
                    p.add_run().add_break()

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
        """Parses the verse-by-verse commentary file."""
        verses = []
        # Regex to find verse blocks, which start with "**Verse X**"
        verse_blocks = re.split(r'(?=^\*\*Verse \d+\*\*\n)', content, flags=re.MULTILINE)

        for block in verse_blocks:
            block = block.strip()
            if not block.strip():
                continue

            lines = block.strip().split('\n', 1)  # Split only on the first newline
            verse_num_match = re.match(r'^\*\*Verse (\d+)\*\*', lines[0])
            if not verse_num_match:
                continue

            verse_num = verse_num_match.group(1)
            commentary_text = "\n".join(lines[1:]).strip()

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
**Lexicon Entries (BDB/Klein) Reviewed**: {lexicon_count}
**Traditional Commentaries Reviewed**: {total_commentaries}{commentary_details}
**Concordance Entries Reviewed**: {concordance_total if concordance_total > 0 else 'N/A'}
**Figurative Language Instances Reviewed**: {figurative_total if figurative_total > 0 else 'N/A'}
**Master Editor Prompt Size**: {prompt_chars_str}

{models_used_str}
        """.strip()
        return summary

    def _add_summary_paragraph(self, line: str):
        """Adds a paragraph to the summary, bolding the label."""
        p = self.document.add_paragraph()
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
        

        # 2. Add Introduction
        self.document.add_heading('Introduction', level=2)
        intro_content = self.intro_path.read_text(encoding='utf-8')
        # Use single newline split to match print_ready.md formatting
        for para in intro_content.strip().split('\n'):
            if para.strip():
                self._add_paragraph_with_markdown(para, style='BodySans')

        # 3. Add Full Psalm Text
        self.document.add_page_break()
        self._format_psalm_text(self.psalm_num, psalm_text_data)
        
        # Add a page break after the psalm text table
        self.document.add_paragraph() # Add a paragraph to attach the break to
        self.document.add_page_break()

        # 4. Add Verse-by-Verse Commentary
        self.document.add_heading('Verse-by-Verse Commentary', level=2)
        verses_content = self.modifier.modify_text(self.verses_path.read_text(encoding='utf-8'))
        parsed_verses = self._parse_verse_commentary(verses_content, psalm_text_data)

        for verse in parsed_verses:
            self.document.add_heading(f'Verse {verse["number"]}', level=3)
            self._add_paragraph_with_soft_breaks(verse["commentary"], style='BodySans')

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
                date_str = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
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