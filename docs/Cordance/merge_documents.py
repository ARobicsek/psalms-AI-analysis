#!/usr/bin/env python3
"""
Merge three Cordance Health Insights Bank documents with precise formatting.
Follows the FORMATTING_GUIDE.md specifications exactly.
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from copy import deepcopy
import re


def add_page_number(section):
    """Add page numbers to the bottom right of all pages."""
    footer = section.footer
    footer_para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    footer_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Add page number field
    run = footer_para.add_run()
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')

    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'PAGE'

    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')

    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)

    # Set font
    run.font.name = 'Arial'
    run.font.size = Pt(11)


def add_table_of_contents(doc):
    """Add a table of contents showing only Heading 1 and Heading 2."""
    # Add TOC title
    toc_title = doc.add_paragraph('Table of Contents')
    toc_title.style = doc.styles['Heading 1']

    # Add the TOC field
    paragraph = doc.add_paragraph()
    run = paragraph.add_run()

    fldChar = OxmlElement('w:fldChar')
    fldChar.set(qn('w:fldCharType'), 'begin')

    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    # TOC showing only levels 1 and 2
    instrText.text = 'TOC \\o "1-2" \\h \\z \\u'

    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')

    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')

    run._r.append(fldChar)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)

    # Add page break after TOC
    doc.add_page_break()


def clean_paragraph_text(para):
    """Extract clean text from a paragraph."""
    return para.text.strip()


def is_heading_1(para):
    """Check if paragraph is Heading 1 style."""
    if para.style and 'Heading 1' in para.style.name:
        return True
    # Also check if it's formatted like H1 (specialty name like "Primary Care", "Cardiology")
    text = para.text.strip()
    if len(text) < 50 and not text.startswith('USE CASE'):
        # Check if bold and larger font
        if para.runs:
            first_run = para.runs[0]
            if first_run.bold and first_run.font.size and first_run.font.size >= Pt(16):
                return True
    return False


def is_heading_2(para):
    """Check if paragraph is Heading 2 style (USE CASE titles)."""
    if para.style and 'Heading 2' in para.style.name:
        return True
    text = para.text.strip()
    if text.startswith('USE CASE'):
        return True
    return False


def is_heading_3(para):
    """Check if paragraph is Heading 3 style."""
    if para.style and 'Heading 3' in para.style.name:
        return True
    text = para.text.strip()
    # Known Heading 3 titles
    h3_titles = [
        'Clinical Scenario', 'Current State Challenges', 'Cordance Solution',
        'Impact on Three Pillars', 'Physician Value Proposition',
        'Implementation Considerations', 'Quantified Impact', 'Patient-Facing Value'
    ]
    if text in h3_titles:
        return True
    return False


def is_heading_4(para):
    """Check if paragraph is Heading 4 style."""
    if para.style and 'Heading 4' in para.style.name:
        return True
    text = para.text.strip()
    # Known Heading 4 titles
    h4_titles = [
        'Before Encounter', 'During Encounter', 'After Encounter',
        'Economics (Value-Based Care & Fee-for-Service)',
        'Quality & Safety', 'Population Health & Outcomes'
    ]
    if text in h4_titles:
        return True
    return False


def is_list_paragraph(para):
    """Check if paragraph is a list/bullet point."""
    # Check style
    if para.style and 'List' in para.style.name:
        return True
    # Check if it has bullet formatting
    if para._element.pPr is not None:
        numPr = para._element.pPr.find(qn('w:numPr'))
        if numPr is not None:
            return True
    return False


def copy_paragraph_with_format(source_para, target_doc):
    """Copy a paragraph from source to target document with formatting."""
    text = clean_paragraph_text(source_para)

    # Determine the correct style and create paragraph
    if is_heading_1(source_para):
        para = target_doc.add_paragraph(text)
        para.style = target_doc.styles['Heading 1']
    elif is_heading_2(source_para):
        para = target_doc.add_paragraph(text)
        para.style = target_doc.styles['Heading 2']
    elif is_heading_3(source_para):
        para = target_doc.add_paragraph(text)
        para.style = target_doc.styles['Heading 3']
    elif is_heading_4(source_para):
        para = target_doc.add_paragraph(text)
        para.style = target_doc.styles['Heading 4']
    elif is_list_paragraph(source_para):
        para = target_doc.add_paragraph(text)
        para.style = target_doc.styles['List Paragraph']
    else:
        # Regular body text
        para = target_doc.add_paragraph(text)
        # Don't set a style - let it use Normal/Body Text

    return para


def extract_use_cases(doc):
    """Extract all use cases from a document as groups of paragraphs."""
    use_cases = []
    current_use_case = []
    in_use_case = False

    for para in doc.paragraphs:
        text = clean_paragraph_text(para)

        # Check if this is a USE CASE heading
        if is_heading_2(para) and text.startswith('USE CASE'):
            # Save previous use case if exists
            if current_use_case:
                use_cases.append(current_use_case)
            # Start new use case
            current_use_case = [para]
            in_use_case = True
        elif in_use_case:
            # Add paragraph to current use case
            current_use_case.append(para)

            # Check if we've reached a section that indicates end of use cases
            if text in ['Summary', 'References']:
                in_use_case = False

    # Add the last use case
    if current_use_case:
        use_cases.append(current_use_case)

    return use_cases


def process_document_content(source_doc, merged_doc, is_first=False):
    """Process paragraphs from source document and add to merged document."""
    previous_was_use_case = False
    use_case_count = 0

    for para in source_doc.paragraphs:
        text = clean_paragraph_text(para)
        if not text:
            continue

        # Skip References, Summary and everything after
        if text in ['References', 'Summary']:
            break

        # Check if this is a USE CASE heading
        is_use_case = is_heading_2(para) and text.startswith('USE CASE')

        # Add page break before USE CASE (except the very first use case in the document)
        if is_use_case:
            use_case_count += 1
            if not (is_first and use_case_count == 1):  # Don't add page break before first use case
                merged_doc.add_page_break()

        # Copy paragraph with proper formatting
        copy_paragraph_with_format(para, merged_doc)

        previous_was_use_case = is_use_case

    return use_case_count


def merge_documents():
    """Main function to merge the three documents."""
    print("Loading documents...")

    # Load the three source documents
    primary_care_doc = Document('./Cordance_Health_Insights_Bank_Primary_Care.docx')
    cardiology_doc = Document('./Cordance_Health_Insights_Bank_Cardiology.docx')
    infectious_diseases_doc = Document('./Cordance_Health_Insights_Bank_Infectious_Diseases.docx')

    # Create new document and copy style definitions from Primary Care (well-formatted)
    print("Creating merged document with consistent formatting...")
    merged_doc = Document()
    merged_doc.styles._element = deepcopy(primary_care_doc.styles._element)

    # Add Table of Contents
    print("Adding table of contents...")
    add_table_of_contents(merged_doc)

    # Process Primary Care
    print("Adding Primary Care content...")
    process_document_content(primary_care_doc, merged_doc, is_first=True)

    # Process Cardiology
    print("Adding Cardiology content...")
    merged_doc.add_page_break()  # Page break before specialty section
    process_document_content(cardiology_doc, merged_doc, is_first=False)

    # Process Infectious Diseases
    print("Adding Infectious Diseases content...")
    merged_doc.add_page_break()  # Page break before specialty section
    process_document_content(infectious_diseases_doc, merged_doc, is_first=False)

    # Add page numbers to footer
    print("Adding page numbers...")
    for section in merged_doc.sections:
        add_page_number(section)

    # Save the merged document
    output_path = './Cordance_insights_bank_draft.docx'
    print(f"Saving merged document to {output_path}...")
    merged_doc.save(output_path)

    print(f"\n✅ Successfully created {output_path}")
    print(f"   - Merged 3 specialty documents (Primary Care, Cardiology, Infectious Diseases)")
    print(f"   - Applied consistent formatting from Primary Care template")
    print(f"   - Added table of contents (Heading 1 and Heading 2 only)")
    print(f"   - Added page numbers at bottom right")
    print(f"   - Added page breaks after each use case")


if __name__ == '__main__':
    merge_documents()
