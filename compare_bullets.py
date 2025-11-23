#!/usr/bin/env python3
"""
Compare bullet definitions between template and draft.
"""
from docx import Document

def get_numbering_info(doc_path):
    """Extract numbering definition info from a document."""
    doc = Document(doc_path)
    info = {
        'path': doc_path,
        'abstract_nums': []
    }

    if hasattr(doc, '_part') and hasattr(doc._part, 'numbering_part'):
        try:
            numbering_part = doc._part.numbering_part
            if numbering_part:
                numbering_xml = numbering_part._element
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                abstract_nums = numbering_xml.findall('.//w:abstractNum', ns)

                for abs_num in abstract_nums:
                    abs_num_id = abs_num.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}abstractNumId')
                    abs_info = {'id': abs_num_id, 'levels': []}

                    levels = abs_num.findall('.//w:lvl', ns)
                    for lvl in levels:
                        ilvl = lvl.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ilvl')

                        # Get bullet text
                        lvl_text = lvl.find('.//w:lvlText', ns)
                        lvl_text_val = lvl_text.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') if lvl_text is not None else None

                        # Get font formatting
                        r_pr = lvl.find('.//w:rPr', ns)
                        font_size = None
                        font_name = None

                        if r_pr is not None:
                            sz = r_pr.find('.//w:sz', ns)
                            if sz is not None:
                                font_size = sz.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')

                            r_fonts = r_pr.find('.//w:rFonts', ns)
                            if r_fonts is not None:
                                font_name = r_fonts.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii')

                        abs_info['levels'].append({
                            'ilvl': ilvl,
                            'bullet': lvl_text_val,
                            'font_size': font_size,
                            'font_name': font_name
                        })

                    info['abstract_nums'].append(abs_info)
        except Exception as e:
            info['error'] = str(e)

    return info

if __name__ == "__main__":
    template_path = "/home/user/psalms-AI-analysis/docs/Cordance/Cordance_Health_Insights_Bank_Cardiology.docx"
    draft_path = "/home/user/psalms-AI-analysis/docs/Cordance/Cordance_insights_bank_draft.docx"

    print("=" * 80)
    print("COMPARING BULLET DEFINITIONS")
    print("=" * 80)

    print("\n### CARDIOLOGY TEMPLATE (CORRECT) ###")
    template_info = get_numbering_info(template_path)
    for abs_num in template_info['abstract_nums']:
        print(f"\nAbstract Num ID: {abs_num['id']}")
        for lvl in abs_num['levels']:
            print(f"  Level {lvl['ilvl']}: bullet='{lvl['bullet']}' font={lvl['font_name']} size={lvl['font_size']}")

    print("\n### DRAFT DOCUMENT (CURRENT) ###")
    draft_info = get_numbering_info(draft_path)
    for abs_num in draft_info['abstract_nums']:
        print(f"\nAbstract Num ID: {abs_num['id']}")
        for lvl in abs_num['levels']:
            print(f"  Level {lvl['ilvl']}: bullet='{lvl['bullet']}' font={lvl['font_name']} size={lvl['font_size']}")

    # Compare
    print("\n### DIFFERENCES ###")
    if len(template_info['abstract_nums']) > 0 and len(draft_info['abstract_nums']) > 0:
        template_lvl0 = template_info['abstract_nums'][0]['levels'][0]
        draft_lvl0 = draft_info['abstract_nums'][0]['levels'][0]

        if template_lvl0['bullet'] != draft_lvl0['bullet']:
            print(f"❌ Bullet character mismatch: template='{template_lvl0['bullet']}' vs draft='{draft_lvl0['bullet']}'")
        if template_lvl0['font_size'] != draft_lvl0['font_size']:
            print(f"❌ Font size mismatch: template={template_lvl0['font_size']} vs draft={draft_lvl0['font_size']}")
        if template_lvl0['font_name'] != draft_lvl0['font_name']:
            print(f"❌ Font name mismatch: template={template_lvl0['font_name']} vs draft={draft_lvl0['font_name']}")

        if (template_lvl0['bullet'] == draft_lvl0['bullet'] and
            template_lvl0['font_size'] == draft_lvl0['font_size'] and
            template_lvl0['font_name'] == draft_lvl0['font_name']):
            print("✓ Bullet definitions match!")

    print("\n" + "=" * 80)
