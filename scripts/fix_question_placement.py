"""
Regenerate combined_test.docx with proper question handling:
1. Extract refined questions from main AND college verse commentaries
2. Strip the embedded REFINED READER QUESTIONS sections from verse content
3. Place main refined questions before main intro
4. Place college refined questions before college intro
"""

import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

from src.data_sources.tanakh_database import TanakhDatabase
from src.utils.divine_names_modifier import DivineNamesModifier


def extract_refined_questions(verse_content: str) -> tuple:
    """
    Extract refined reader questions from verse commentary and return
    (questions_list, content_without_questions).
    """
    marker = "### REFINED READER QUESTIONS"
    if marker not in verse_content:
        return [], verse_content
    
    parts = verse_content.split(marker)
    content_before = parts[0].strip()
    questions_section = parts[1] if len(parts) > 1 else ""
    
    # Find where questions end (next ## header or end)
    next_header = re.search(r'\n##', questions_section)
    if next_header:
        questions_text = questions_section[:next_header.start()]
        content_after = questions_section[next_header.start():]
    else:
        questions_text = questions_section
        content_after = ""
    
    # Extract numbered questions
    questions = []
    for line in questions_text.strip().split('\n'):
        line = line.strip()
        match = re.match(r'^(\d+)\.\s+(.+)$', line)
        if match:
            q = match.group(2).strip()
            if q and len(q) > 10:
                questions.append(q)
    
    # Combine content without questions
    clean_content = content_before + content_after
    
    return questions, clean_content


def main():
    psalm_number = 27
    output_path = Path("output/psalm_27")
    
    # Read all files
    main_intro = (output_path / "psalm_027_edited_intro_test.md").read_text(encoding='utf-8')
    main_verses = (output_path / "psalm_027_edited_verses_test.md").read_text(encoding='utf-8')
    college_intro = (output_path / "psalm_027_edited_intro_college_test.md").read_text(encoding='utf-8')
    college_verses = (output_path / "psalm_027_edited_verses_college_test.md").read_text(encoding='utf-8')
    
    # Extract refined questions from verse files
    main_questions, main_verses_clean = extract_refined_questions(main_verses)
    college_questions, college_verses_clean = extract_refined_questions(college_verses)
    
    print(f"Main refined questions: {len(main_questions)}")
    print(f"College refined questions: {len(college_questions)}")
    
    # Save cleaned verse files
    main_verses_clean_path = output_path / "psalm_027_edited_verses_test_clean.md"
    college_verses_clean_path = output_path / "psalm_027_edited_verses_college_test_clean.md"
    main_verses_clean_path.write_text(main_verses_clean, encoding='utf-8')
    college_verses_clean_path.write_text(college_verses_clean, encoding='utf-8')
    
    # Save question files 
    main_q_file = output_path / "psalm_027_reader_questions_test.json"
    college_q_file = output_path / "psalm_027_reader_questions_college_test.json"
    
    main_q_file.write_text(json.dumps({
        'psalm_number': psalm_number,
        'curated_questions': main_questions,
        'source': 'master_editor_refined'
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    
    college_q_file.write_text(json.dumps({
        'psalm_number': psalm_number,
        'curated_questions': college_questions,
        'source': 'college_editor_refined'
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print(f"Saved main questions to: {main_q_file}")
    print(f"Saved college questions to: {college_q_file}")
    
    # Now regenerate combined docx using our custom logic
    from src.utils.combined_document_generator import CombinedDocumentGenerator
    
    # Use the cleaned verse files and proper question file
    stats_file = output_path / "psalm_027_pipeline_stats_test.json"
    combined_docx = output_path / "psalm_027_commentary_combined_test.docx"
    
    # Generate with both main and college questions
    generator = CombinedDocumentGenerator(
        psalm_num=psalm_number,
        main_intro_path=output_path / "psalm_027_edited_intro_test.md",
        main_verses_path=main_verses_clean_path,
        college_intro_path=output_path / "psalm_027_edited_intro_college_test.md", 
        college_verses_path=college_verses_clean_path,
        stats_path=stats_file,
        output_path=combined_docx,
        reader_questions_path=main_q_file,
        college_questions_path=college_q_file
    )
    generator.generate()
    
    print(f"\n✓ Generated: {combined_docx}")
    print("\nNote: College questions need to be manually reviewed in the docx")
    print(f"College questions ({len(college_questions)}):")
    for i, q in enumerate(college_questions, 1):
        print(f"  {i}. {q[:80]}...")


if __name__ == '__main__':
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    main()
