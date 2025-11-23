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
- **Bullet style**: Automatic from style definition
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

## Verification Checklist

Before finalizing a document, verify:

- [ ] Document has exactly 1 Heading 1 paragraph (specialty name)
- [ ] Document has ~10 Heading 2 paragraphs (use cases)
- [ ] All headings use proper heading styles (not direct formatting)
- [ ] Headers appear in Word's Navigation Pane
- [ ] "At a practice level:" and "At the individual patient level:" are NOT headings
- [ ] All bullet points use List Paragraph style
- [ ] No direct font/size/color formatting on headings
- [ ] When you click a heading, the Styles panel shows the heading style name

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
