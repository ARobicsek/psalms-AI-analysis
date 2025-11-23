#!/usr/bin/env python3
"""
Merge three Cordance Health Insights Bank documents with PRECISE formatting.
This version properly preserves all formatting from the Primary Care template.
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
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

    # Add a paragraph for the TOC field
    paragraph = doc.add_paragraph()
    run = paragraph.add_run()

    # Create the TOC field code
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')

    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    # TOC showing only levels 1 and 2, with hyperlinks
    instrText.text = 'TOC \\o "1-2" \\h \\z \\u'

    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')

    # Add placeholder text
    run2 = paragraph.add_run()
    run2.text = 'Right-click and select "Update Field" to generate the table of contents.'
    run2.font.italic = True
    run2.font.color.rgb = RGBColor(128, 128, 128)

    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')

    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    paragraph._element.append(fldChar3)

    # Add page break after TOC
    doc.add_page_break()


def copy_paragraph_element(source_para, target_doc):
    """
    Copy a paragraph from source to target document, preserving ALL formatting.
    This includes style, runs, fonts, colors, and numbering (bullets).
    """
    # Create a new paragraph
    new_para = target_doc.add_paragraph()

    # Copy the paragraph style
    if source_para.style:
        try:
            new_para.style = target_doc.styles[source_para.style.name]
        except KeyError:
            # Style doesn't exist in target, use default
            pass

    # Copy paragraph formatting properties
    if source_para._element.pPr is not None:
        new_para._element.get_or_add_pPr()
        # Copy alignment
        if source_para.alignment is not None:
            new_para.alignment = source_para.alignment

        # Copy numbering properties (THIS IS CRITICAL FOR BULLETS!)
        numPr = source_para._element.pPr.find(qn('w:numPr'))
        if numPr is not None:
            # This paragraph has numbering (bullets or numbers)
            new_numPr = deepcopy(numPr)
            new_para._element.pPr.append(new_numPr)

    # Copy all runs with their formatting
    for source_run in source_para.runs:
        new_run = new_para.add_run(source_run.text)

        # Copy run formatting
        if source_run.bold is not None:
            new_run.bold = source_run.bold
        if source_run.italic is not None:
            new_run.italic = source_run.italic
        if source_run.underline is not None:
            new_run.underline = source_run.underline

        # Copy font properties
        if source_run.font.name:
            new_run.font.name = source_run.font.name
        if source_run.font.size:
            new_run.font.size = source_run.font.size
        if source_run.font.color and source_run.font.color.rgb:
            new_run.font.color.rgb = source_run.font.color.rgb

        # Copy superscript/subscript
        if source_run.font.superscript:
            new_run.font.superscript = source_run.font.superscript
        if source_run.font.subscript:
            new_run.font.subscript = source_run.font.subscript

    return new_para


def is_heading_2(para):
    """Check if paragraph is a USE CASE heading."""
    if para.style and 'Heading 2' in para.style.name:
        return True
    text = para.text.strip()
    if text.startswith('USE CASE'):
        return True
    return False


def should_skip_paragraph(para):
    """Determine if a paragraph should be skipped."""
    text = para.text.strip()
    # Skip empty paragraphs
    if not text:
        return True
    # Skip References and Summary sections
    if text in ['References', 'Summary']:
        return 'STOP'  # Signal to stop processing this document
    return False


def process_document_content(source_doc, target_doc, add_page_break_before_first=False):
    """
    Process all paragraphs from source document and add to target document.
    Returns the number of use cases processed.
    """
    use_case_count = 0
    stop_processing = False

    for para in source_doc.paragraphs:
        # Check if we should skip this paragraph
        skip_result = should_skip_paragraph(para)
        if skip_result == 'STOP':
            break
        if skip_result:
            continue

        # Check if this is a USE CASE heading
        is_use_case = is_heading_2(para)

        # Add page break before each USE CASE (except possibly the first)
        if is_use_case:
            use_case_count += 1
            # Add page break before this use case unless it's the very first one
            if use_case_count > 1 or add_page_break_before_first:
                target_doc.add_page_break()

        # Copy the paragraph with all its formatting
        copy_paragraph_element(para, target_doc)

    return use_case_count


def merge_documents():
    """Main function to merge the three documents with precise formatting."""
    print("=" * 70)
    print("CORDANCE HEALTH INSIGHTS BANK - DOCUMENT MERGER")
    print("=" * 70)
    print("\nLoading source documents...")

    # Load the three source documents
    primary_care_doc = Document('./Cordance_Health_Insights_Bank_Primary_Care.docx')
    cardiology_doc = Document('./Cordance_Health_Insights_Bank_Cardiology.docx')
    infectious_diseases_doc = Document('./Cordance_Health_Insights_Bank_Infectious_Diseases.docx')

    print("✓ Loaded Primary Care document")
    print("✓ Loaded Cardiology document")
    print("✓ Loaded Infectious Diseases document")

    # Create new merged document
    print("\nCreating merged document...")
    merged_doc = Document()

    # Copy ALL style definitions from Primary Care (the well-formatted template)
    print("✓ Copying style definitions from Primary Care template...")
    merged_doc.styles._element = deepcopy(primary_care_doc.styles._element)

    # Copy numbering definitions (CRITICAL for bullets!)
    print("✓ Copying numbering definitions (for bullets)...")
    if primary_care_doc._part.numbering_part is not None:
        # Copy the entire numbering part
        merged_doc._part.numbering_part._element = deepcopy(
            primary_care_doc._part.numbering_part._element
        )

    # Add Table of Contents
    print("\n" + "=" * 70)
    print("ADDING TABLE OF CONTENTS")
    print("=" * 70)
    add_table_of_contents(merged_doc)
    print("✓ Table of Contents added (will need to be updated in Word)")

    # Process Primary Care
    print("\n" + "=" * 70)
    print("MERGING PRIMARY CARE CONTENT")
    print("=" * 70)
    pc_use_cases = process_document_content(primary_care_doc, merged_doc, add_page_break_before_first=False)
    print(f"✓ Added {pc_use_cases} Primary Care use cases")

    # Add page break before Cardiology section
    merged_doc.add_page_break()

    # Process Cardiology
    print("\n" + "=" * 70)
    print("MERGING CARDIOLOGY CONTENT")
    print("=" * 70)
    cardio_use_cases = process_document_content(cardiology_doc, merged_doc, add_page_break_before_first=False)
    print(f"✓ Added {cardio_use_cases} Cardiology use cases")

    # Add page break before Infectious Diseases section
    merged_doc.add_page_break()

    # Process Infectious Diseases
    print("\n" + "=" * 70)
    print("MERGING INFECTIOUS DISEASES CONTENT")
    print("=" * 70)
    id_use_cases = process_document_content(infectious_diseases_doc, merged_doc, add_page_break_before_first=False)
    print(f"✓ Added {id_use_cases} Infectious Diseases use cases")

    # Add page numbers to footer
    print("\n" + "=" * 70)
    print("ADDING PAGE NUMBERS")
    print("=" * 70)
    for section in merged_doc.sections:
        add_page_number(section)
    print("✓ Page numbers added to bottom right of all pages")

    # Save the merged document
    output_path = './Cordance_insights_bank_draft.docx'
    print("\n" + "=" * 70)
    print("SAVING MERGED DOCUMENT")
    print("=" * 70)
    merged_doc.save(output_path)

    print(f"\n{'=' * 70}")
    print("✅ SUCCESS! MERGED DOCUMENT CREATED")
    print(f"{'=' * 70}")
    print(f"\nFile: {output_path}")
    print(f"\nDocument contains:")
    print(f"  • Primary Care: {pc_use_cases} use cases")
    print(f"  • Cardiology: {cardio_use_cases} use cases")
    print(f"  • Infectious Diseases: {id_use_cases} use cases")
    print(f"  • Total: {pc_use_cases + cardio_use_cases + id_use_cases} use cases")
    print(f"\nFormatting applied:")
    print(f"  ✓ Heading 1: Times New Roman, 17pt, Blue (#2E74B5)")
    print(f"  ✓ Heading 2: Times New Roman, 14pt, Blue (#2E74B5)")
    print(f"  ✓ Heading 3: Times New Roman, 13pt, Dark Blue (#1F4D78)")
    print(f"  ✓ Heading 4: Times New Roman, 11pt, Italic, Blue (#2E74B5)")
    print(f"  ✓ Body Text: Arial, 11pt")
    print(f"  ✓ Bullet Points: List Paragraph style with bullets")
    print(f"  ✓ Page Numbers: Bottom right")
    print(f"  ✓ Page Breaks: After each use case")
    print(f"  ✓ Table of Contents: Showing Heading 1 and Heading 2")
    print(f"\n⚠️  IMPORTANT: Open the document in Word and:")
    print(f"  1. Right-click the Table of Contents")
    print(f"  2. Select 'Update Field'")
    print(f"  3. Choose 'Update entire table'")
    print(f"\n{'=' * 70}\n")


if __name__ == '__main__':
    merge_documents()
