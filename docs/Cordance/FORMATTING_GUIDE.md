# Cordance Health Insights Bank - Document Formatting Guide

This guide documents the **exact formatting specifications** for all Cordance Health Insights Bank documents to ensure consistency across all specialty areas (Cardiology, Primary Care, etc.).

## Document Structure

Each Cordance Health Insights Bank document follows this hierarchy:

```
Heading 1: [Specialty Name]
  └─ Heading 2: USE CASE N: [Title]
       ├─ Heading 3: Clinical Scenario
       ├─ Heading 3: Current State Challenges
       │    ├─ Normal Text: At a practice level:
       │    │    └─ List Paragraph: [bullet points]
       │    └─ Normal Text: At the individual patient level:
       │         └─ List Paragraph: [bullet points]
       ├─ Heading 3: Cordance Solution
       │    ├─ Heading 4: Before Encounter
       │    │    └─ List Paragraph: [bullet points]
       │    ├─ Heading 4: During Encounter
       │    │    └─ List Paragraph: [bullet points]
       │    └─ Heading 4: After Encounter
       │         └─ List Paragraph: [bullet points]
       ├─ Heading 3: Impact on Three Pillars
       │    ├─ Heading 4: Economics (Value-Based Care & Fee-for-Service)
       │    │    └─ List Paragraph: [bullet points]
       │    ├─ Heading 4: Quality & Safety
       │    │    └─ List Paragraph: [bullet points]
       │    └─ Heading 4: Population Health & Outcomes
       │         └─ List Paragraph: [bullet points]
       ├─ Heading 3: Physician Value Proposition
       │    └─ List Paragraph: [bullet points]
       └─ Heading 3: Implementation Considerations
            └─ List Paragraph: [bullet points]
```

## Critical Formatting Rules

### ⚠️ MOST IMPORTANT: Use Style Inheritance, NOT Direct Formatting

**DO NOT apply direct formatting** (font, size, color, bold) to heading paragraphs. Instead:

1. **Apply ONLY the heading style** (Heading 1, Heading 2, Heading 3, or Heading 4)
2. **Let the style definition control all formatting** (font, size, color, bold)

This ensures:
- Consistent formatting across all documents
- Proper navigation pane functionality in Word
- Easy updates if style definitions change
- Matching the Cardiology template exactly

### Heading Styles

#### Heading 1
- **Used for**: Specialty name (e.g., "Cardiology", "Primary Care")
- **Style**: Heading 1
- **Font**: Times New Roman, 17pt, Bold
- **Color**: #2E74B5 (blue)
- **Direct formatting**: Apply font/size/color directly (no style inheritance needed)
- **Navigation level**: Top level
- **Count per document**: 1

#### Heading 2
- **Used for**: USE CASE titles
- **Style**: Heading 2
- **Font**: Times New Roman, 14pt, Bold
- **Color**: #2E74B5 (blue)
- **Direct formatting**: Apply font/size/color directly (no style inheritance needed)
- **Pattern**: "USE CASE N: [Description]" where N is 1-10
- **Navigation level**: Second level
- **Count per document**: ~10

#### Heading 3
- **Used for**: Major section headings
- **Style**: Heading 3
- **Font**: Times New Roman, 13pt, Bold
- **Color**: #1F4D78 (darker blue)
- **Direct formatting**: Apply font/size/color directly (no style inheritance needed)
- **Examples**:
  - Clinical Scenario
  - Current State Challenges
  - Cordance Solution
  - Impact on Three Pillars
  - Physician Value Proposition
  - Implementation Considerations
  - Quantified Impact
  - Patient-Facing Value
- **Navigation level**: Third level
- **Count per document**: ~60-70

#### Heading 4
- **Used for**: Subsection headings
- **Style**: Heading 4
- **Font**: Times New Roman, 11pt, Italic (not bold)
- **Color**: #2E74B5 (blue)
- **Direct formatting**: Apply font/size/color directly (no style inheritance needed)
- **Examples**:
  - Before Encounter
  - During Encounter
  - After Encounter
  - Economics (Value-Based Care & Fee-for-Service)
  - Quality & Safety
  - Population Health & Outcomes
- **Navigation level**: Fourth level
- **Count per document**: ~60

### Normal Text Styles

#### Body Text
- **Font**: Arial, 11pt
- **Color**: Black (default)
- **Used for**: All regular paragraph text, including Clinical Scenario descriptions
- **Count per document**: ~100-200 paragraphs

#### "At a/the ... level:" Lines
- **Style**: Normal (No Style) or Body Text
- **Font**: Arial, 11pt
- **NOT Heading 4** - these are introductory text, not section headings
- **Examples**:
  - "At a practice level:"
  - "At the individual patient level:"

#### List Paragraph (Bulleted Lists)
- **Style**: List Paragraph
- **Font**: Arial, 11pt
- **Used for**: All bullet point content
- **Bullet style**: Small bullet (• character), not oversized
- **Bullet size**: Should be proportional to 11pt text (not enlarged)
- **Indentation**: 0.25" hanging indent
- **Count per document**: ~450-500

#### Reference Markers
- **Format**: Superscript
- **Font**: Arial, 9pt (smaller than body text)
- **Used for**: Citation markers like [1], [2], [3], etc.
- **Example**: "reduces mortality by 33%[1]" where [1] is superscript
- **Count per document**: ~60-80 references

## How to Create a New Document

### Method 1: Using Python (Recommended)

```python
from docx import Document
from copy import deepcopy

# 1. Load the Cardiology template
template_doc = Document('Cordance_Health_Insights_Bank_Cardiology.docx')

# 2. Create new document
new_doc = Document()

# 3. Copy style definitions from template
new_doc.styles._element = deepcopy(template_doc.styles._element)

# 4. Add content with proper styles (NO direct formatting)
# Heading 1
p = new_doc.add_paragraph('Your Specialty Name')
p.style = new_doc.styles['Heading1']  # or 'Heading 1'

# Heading 2
p = new_doc.add_paragraph('USE CASE 1: Your Use Case Title')
p.style = new_doc.styles['Heading2']

# Heading 3
p = new_doc.add_paragraph('Clinical Scenario')
p.style = new_doc.styles['Heading3']

# Normal paragraph
p = new_doc.add_paragraph('Regular text content...')
# Don't set style - uses default

# List Paragraph
p = new_doc.add_paragraph('First bullet point')
p.style = new_doc.styles['List Paragraph']

# 5. Save
new_doc.save('Cordance_Health_Insights_Bank_Your_Specialty.docx')
```

### Method 2: Using Word

1. **Start with Cardiology template**:
   - Make a copy of `Cordance_Health_Insights_Bank_Cardiology.docx`
   - Rename it to your specialty

2. **Delete all content** except keep one paragraph of each type as examples

3. **Add new content**:
   - Select the example heading
   - Type your new heading text
   - The style is automatically applied
   - **Do NOT**:
     - Change font manually
     - Change size manually
     - Change color manually
     - Apply bold manually
   - These all come from the style definition

4. **For bullets**:
   - Use the List Paragraph style
   - Word will automatically add bullets

### Method 3: Find and Replace

1. Open the Cardiology document
2. Replace all content text (keep the heading structures)
3. Ensure no direct formatting is accidentally applied

## Comprehensive Verification Checklist

### Pre-Merge Checklist
Before running the merge script:

- [ ] All source documents are in the correct directory
- [ ] Primary Care document is the well-formatted template
- [ ] Python environment has python-docx installed
- [ ] Backup of existing files created (if applicable)

### Post-Merge Technical Verification

Run these checks programmatically after merging:

#### Document Structure
- [ ] Document has 3 Heading 1 paragraphs (one per specialty: Primary Care, Cardiology, Infectious Diseases)
- [ ] Document has ~23 total Heading 2 paragraphs (USE CASE N: titles)
  - [ ] Primary Care: 10 use cases
  - [ ] Cardiology: 8 use cases
  - [ ] Infectious Diseases: 5 use cases
- [ ] All use case sections have consistent structure:
  - [ ] Clinical Scenario (H3)
  - [ ] Current State Challenges (H3)
  - [ ] Cordance Solution (H3) with Before/During/After (H4)
  - [ ] Impact on Three Pillars (H3) with Economics/Quality/Population (H4)
  - [ ] Physician Value Proposition (H3)
  - [ ] Implementation Considerations (H3)

#### Heading Formatting
- [ ] **Heading 1**: Times New Roman, 17pt, Bold, Blue (#2E74B5)
  - [ ] Verify: "Primary Care" heading
  - [ ] Verify: "Cardiology" heading
  - [ ] Verify: "Infectious Diseases" heading
- [ ] **Heading 2**: Times New Roman, 14pt, Bold, Blue (#2E74B5)
  - [ ] Verify: First USE CASE in Primary Care
  - [ ] Verify: First USE CASE in Cardiology
  - [ ] Verify: First USE CASE in Infectious Diseases
- [ ] **Heading 3**: Times New Roman, 13pt, Bold, Dark Blue (#1F4D78)
  - [ ] Verify: "Clinical Scenario" in each section
  - [ ] Verify: "Cordance Solution" in each section
- [ ] **Heading 4**: Times New Roman, 11pt, Italic (not bold), Blue (#2E74B5)
  - [ ] Verify: "Before Encounter" in each section
  - [ ] Verify: "Economics (Value-Based Care & Fee-for-Service)" in each section

#### Body Text Formatting
- [ ] **Normal paragraphs**: Arial, 11pt, Black
  - [ ] Verify: Clinical Scenario description paragraphs
  - [ ] Verify: "At a practice level:" lines (NOT headings)
  - [ ] Verify: "At the individual patient level:" lines (NOT headings)
- [ ] **List Paragraph (bullets)**: Arial, 11pt with proper bullets
  - [ ] Bullets are present (not missing)
  - [ ] Bullet size is proportional (not oversized)
  - [ ] Bullets use • character
  - [ ] Proper hanging indent (0.25")
  - [ ] Verify bullets in Primary Care "Current State Challenges"
  - [ ] Verify bullets in Cardiology "Cordance Solution - Before Encounter"
  - [ ] Verify bullets in Infectious Diseases "Impact on Three Pillars"

#### Navigation and Structure
- [ ] All headings appear in Word's Navigation Pane
- [ ] Navigation Pane shows proper hierarchy (H1 > H2 > H3 > H4)
- [ ] Table of Contents field is present at document start
- [ ] TOC includes instruction to update field
- [ ] Page breaks exist between use cases
- [ ] Page numbers appear at bottom right of all pages (except possibly first page)

### Manual Verification in Microsoft Word

Open the merged document and verify:

#### Style Application
- [ ] Click on "Primary Care" heading → Styles panel shows "Heading 1"
- [ ] Click on any USE CASE heading → Styles panel shows "Heading 2"
- [ ] Click on "Clinical Scenario" → Styles panel shows "Heading 3"
- [ ] Click on "Before Encounter" → Styles panel shows "Heading 4"
- [ ] Click on a bullet point → Styles panel shows "List Paragraph"
- [ ] Click on body text → Styles panel shows "Normal" or no style

#### Visual Verification
- [ ] Specialty names (H1) are largest and blue
- [ ] USE CASE titles (H2) are large and blue
- [ ] Section headings (H3) are medium and dark blue
- [ ] Subsection headings (H4) are smaller, italic, and blue
- [ ] Body text is Arial (not Cambria, not Calibri)
- [ ] Header text is Times New Roman (not Arial, not Calibri)
- [ ] Bullets are present and properly sized (not missing, not huge)
- [ ] All three specialty sections have consistent formatting

#### Table of Contents
- [ ] Right-click on Table of Contents placeholder
- [ ] Select "Update Field"
- [ ] Choose "Update entire table"
- [ ] Verify all Heading 1 entries appear
- [ ] Verify all Heading 2 entries appear
- [ ] Verify page numbers are correct
- [ ] Verify only H1 and H2 appear (no H3 or H4)

#### Page Breaks
- [ ] Each USE CASE starts on a new page (or follows directly after previous)
- [ ] Page breaks don't create extra blank pages
- [ ] Specialty sections start on new pages

### Common Issues to Check

#### Font Issues
- [ ] NO Calibri font anywhere (common Word default)
- [ ] NO Cambria font anywhere (common Word default)
- [ ] Headers use Times New Roman consistently
- [ ] Body and bullets use Arial consistently

#### Bullet Issues
- [ ] Bullets are not missing
- [ ] Bullets are not oversized (comically large)
- [ ] Bullets align properly with text
- [ ] Bullet character is • (not →, ▪, or other symbols)

#### Heading Issues
- [ ] "At a practice level:" is NOT formatted as Heading 4
- [ ] "At the individual patient level:" is NOT formatted as Heading 4
- [ ] No direct formatting applied to headings (only style inheritance)

### Troubleshooting Failed Checks

If any check fails:

1. **Headers wrong font/size**: Remove direct formatting, reapply style
2. **Bullets missing**: Check numbering definitions were copied from template
3. **Bullets oversized**: Check bullet font size in numbering definition
4. **Wrong body font**: Verify styles._element was deep copied from template
5. **Headings not in Navigation**: Style not properly applied, reapply heading style
6. **TOC not visible**: Field code present but not rendered, update field in Word

## Troubleshooting

### Problem: Headers don't appear in Navigation Pane
**Cause**: Paragraphs are using direct formatting instead of heading styles
**Solution**: Apply the correct heading style to each paragraph, remove direct formatting

### Problem: Headers are wrong size/color
**Cause**: Direct formatting is overriding the style
**Solution**: Remove all direct formatting from heading paragraphs

### Problem: Bullets don't appear
**Cause**: Not using List Paragraph style
**Solution**: Apply List Paragraph style to bullet points

### How to Remove Direct Formatting

**In Python**:
```python
from docx.oxml import OxmlElement

def remove_run_formatting(run):
    """Remove all direct formatting from a run."""
    r_pr = run._element.rPr
    if r_pr is not None:
        run._element.remove(r_pr)
        run._element.insert(0, OxmlElement('w:rPr'))

# Apply to all runs in heading paragraphs
for para in doc.paragraphs:
    if para.style and para.style.name in ['Heading 1', 'Heading 2', 'Heading 3', 'Heading 4']:
        for run in para.runs:
            remove_run_formatting(run)
```

**In Word**:
1. Select the heading text
2. Press Ctrl+Spacebar (Windows) or Cmd+Spacebar (Mac) to clear formatting
3. The heading will now use only the style formatting

## Template Files

The official template is:
- `Cordance_Health_Insights_Bank_Cardiology.docx`

All new documents should copy this template's style definitions.

## Questions?

If you're unsure about formatting:
1. Open the Cardiology document
2. Click on a heading
3. Check the Styles panel - it should show ONLY the style name (e.g., "Heading 1")
4. If it shows additional formatting, the template may need to be fixed

---

**Last Updated**: 2025-11-23
**Template Version**: Cardiology v1.0
