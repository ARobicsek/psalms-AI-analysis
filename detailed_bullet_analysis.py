#!/usr/bin/env python3
"""
Detailed bullet formatting analysis.
"""
from docx import Document
from docx.shared import Pt
from docx.oxml import parse_xml
from lxml import etree

def analyze_bullets(doc_path):
    """Analyze bullet formatting in detail."""
    doc = Document(doc_path)

    print("=" * 80)
    print("DETAILED BULLET ANALYSIS")
    print("=" * 80)

    # Find all List Paragraph paragraphs
    list_paras = []
    for idx, para in enumerate(doc.paragraphs):
        style_name = para.style.name if para.style else "No Style"
        if style_name == 'List Paragraph':
            list_paras.append((idx, para))

    print(f"\nFound {len(list_paras)} List Paragraph paragraphs")

    # Analyze numbering definitions
    print("\n### NUMBERING DEFINITIONS ###")
    if hasattr(doc, '_part') and hasattr(doc._part, 'numbering_part'):
        try:
            numbering_part = doc._part.numbering_part
            if numbering_part:
                numbering_xml = numbering_part._element
                print("Numbering definitions exist in document")

                # Print raw XML for first few abstract numbering definitions
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                abstract_nums = numbering_xml.findall('.//w:abstractNum', ns)
                print(f"Found {len(abstract_nums)} abstract numbering definitions")

                for i, abs_num in enumerate(abstract_nums[:3]):  # First 3
                    abs_num_id = abs_num.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}abstractNumId')
                    print(f"\nAbstract Num ID: {abs_num_id}")

                    # Look for level definitions
                    levels = abs_num.findall('.//w:lvl', ns)
                    for lvl in levels:
                        ilvl = lvl.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ilvl')

                        # Get bullet text (lvlText)
                        lvl_text = lvl.find('.//w:lvlText', ns)
                        if lvl_text is not None:
                            lvl_text_val = lvl_text.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        else:
                            lvl_text_val = None

                        # Get font info (rPr)
                        r_pr = lvl.find('.//w:rPr', ns)
                        font_info = {}
                        if r_pr is not None:
                            # Font size
                            sz = r_pr.find('.//w:sz', ns)
                            if sz is not None:
                                font_info['size'] = sz.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')

                            # Font name
                            r_fonts = r_pr.find('.//w:rFonts', ns)
                            if r_fonts is not None:
                                font_info['font'] = r_fonts.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii')

                        if lvl_text_val:
                            print(f"  Level {ilvl}: bullet='{lvl_text_val}' font_info={font_info}")
        except Exception as e:
            print(f"Error accessing numbering: {e}")
    else:
        print("No numbering part found")

    # Sample some List Paragraph paragraphs
    print("\n### SAMPLE LIST PARAGRAPHS ###")
    for idx, para in list_paras[:5]:  # First 5
        print(f"\nPara {idx}: '{para.text[:60]}...'")
        print(f"  Style: {para.style.name if para.style else 'No Style'}")

        # Check paragraph numbering properties
        if para._element.pPr is not None:
            numPr = para._element.pPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}numPr')
            if numPr is not None:
                numId = numPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}numId')
                ilvl = numPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ilvl')
                if numId is not None:
                    print(f"  numId: {numId.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')}")
                if ilvl is not None:
                    print(f"  ilvl: {ilvl.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')}")

        # Check run formatting
        for run_idx, run in enumerate(para.runs[:2]):  # First 2 runs
            font_size = run.font.size.pt if run.font.size else "Unknown"
            font_name = run.font.name or "Unknown"
            print(f"  Run {run_idx}: text='{run.text[:20]}' font={font_name} size={font_size}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    doc_path = "/home/user/psalms-AI-analysis/docs/Cordance/Cordance_insights_bank_draft.docx"
    analyze_bullets(doc_path)
