"""
Quick fix to reprocess Psalm 11 college edition files
with the updated parser that handles ## and ### headers.
"""
import re
from pathlib import Path

def parse_editorial_response(response_text: str) -> dict:
    """Parse response with flexible header matching (## or ###)."""
    # Find section positions - match both ## and ### variants
    assessment_match = re.search(r'^#{2,3} EDITORIAL ASSESSMENT\s*$', response_text, re.MULTILINE)
    intro_match = re.search(r'^#{2,3} REVISED INTRODUCTION\s*$', response_text, re.MULTILINE)
    verses_match = re.search(r'^#{2,3} REVISED VERSE COMMENTARY\s*$', response_text, re.MULTILINE)

    # Extract assessment
    if assessment_match and intro_match:
        assessment = response_text[assessment_match.end():intro_match.start()].strip()
    elif assessment_match:
        assessment = response_text[assessment_match.end():].strip()
    else:
        assessment = ""

    # Extract introduction
    if intro_match and verses_match:
        revised_introduction = response_text[intro_match.end():verses_match.start()].strip()
    elif intro_match:
        revised_introduction = response_text[intro_match.end():].strip()
    else:
        revised_introduction = ""

    # Extract verse commentary
    if verses_match:
        revised_verses = response_text[verses_match.end():].strip()
    else:
        revised_verses = ""

    return {
        'assessment': assessment,
        'revised_introduction': revised_introduction,
        'revised_verses': revised_verses
    }

# Load the raw response
response_file = Path("output/debug/college_editor_response_psalm_11.txt")
print(f"Loading response from: {response_file}")
response_text = response_file.read_text(encoding='utf-8')

# Parse it
result = parse_editorial_response(response_text)

# Save the extracted sections
output_path = Path("output/psalm_11")

intro_file = output_path / "psalm_011_edited_intro_college.md"
verses_file = output_path / "psalm_011_edited_verses_college.md"
assessment_file = output_path / "psalm_011_assessment_college.md"

print(f"\nExtracted sections:")
print(f"  Assessment: {len(result['assessment'])} chars")
print(f"  Introduction: {len(result['revised_introduction'])} chars")
print(f"  Verses: {len(result['revised_verses'])} chars")

# Write intro
with open(intro_file, 'w', encoding='utf-8') as f:
    f.write(result['revised_introduction'])
print(f"\n[OK] Saved introduction to: {intro_file}")

# Write verses
with open(verses_file, 'w', encoding='utf-8') as f:
    f.write(result['revised_verses'])
print(f"[OK] Saved verses to: {verses_file}")

# Update assessment file (rewrite with correct format)
with open(assessment_file, 'w', encoding='utf-8') as f:
    f.write(f"# Editorial Assessment (College Edition) - Psalm 11\n\n")
    f.write(result['assessment'])
print(f"[OK] Saved assessment to: {assessment_file}")

print(f"\n[SUCCESS] Psalm 11 college files successfully regenerated!")
