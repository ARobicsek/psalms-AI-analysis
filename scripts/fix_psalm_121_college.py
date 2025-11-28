#!/usr/bin/env python3
"""
Repair script for Psalm 121 college edition files.

Issue: College editor wrote "## REVISED VERSE-BY-VERSE COMMENTARY" instead of
"## REVISED VERSE COMMENTARY", causing parser to fail and leave
psalm_121_edited_verses_college.md empty.

This script re-parses the existing college editor response (saved in debug
output) using the updated parser logic that handles both format variations.

Similar to Session 145's fix_psalm_11_college.py
"""

import re
from pathlib import Path

def parse_editorial_response(response_text: str) -> tuple[str, str, str]:
    """
    Parse editorial response into three sections.
    Updated to handle both "REVISED VERSE COMMENTARY" and "REVISED VERSE-BY-VERSE COMMENTARY".

    Returns:
        tuple: (assessment, revised_introduction, revised_verses)
    """
    # Default values
    assessment = ""
    revised_introduction = ""
    revised_verses = ""

    # Find section positions - match both ## and ### variants
    # Also handle LLM variations like "REVISED VERSE-BY-VERSE COMMENTARY"
    assessment_match = re.search(r'^#{2,3} EDITORIAL ASSESSMENT\s*$', response_text, re.MULTILINE)
    intro_match = re.search(r'^#{2,3} REVISED INTRODUCTION\s*$', response_text, re.MULTILINE)
    verses_match = re.search(r'^#{2,3} REVISED VERSE(?:-BY-VERSE)? COMMENTARY\s*$', response_text, re.MULTILINE)

    # Extract assessment (from EDITORIAL ASSESSMENT to REVISED INTRODUCTION)
    if assessment_match and intro_match:
        assessment = response_text[assessment_match.end():intro_match.start()].strip()
    elif assessment_match:
        assessment = response_text[assessment_match.end():].strip()

    # Extract introduction (from REVISED INTRODUCTION to REVISED VERSE COMMENTARY)
    if intro_match and verses_match:
        revised_introduction = response_text[intro_match.end():verses_match.start()].strip()
    elif intro_match:
        revised_introduction = response_text[intro_match.end():].strip()

    # Extract verse commentary (from REVISED VERSE COMMENTARY to end)
    if verses_match:
        revised_verses = response_text[verses_match.end():].strip()

    # Replace the liturgical marker with proper markdown header
    liturgical_markers = [
        "---LITURGICAL-SECTION-START---",
        "—LITURGICAL-SECTION-START—",
        "— LITURGICAL-SECTION-START—",
        "—LITURGICAL-SECTION-START —"
    ]

    for marker in liturgical_markers:
        if marker in revised_introduction:
            revised_introduction = revised_introduction.replace(
                marker,
                "## Modern Jewish Liturgical Use"
            )
            print(f"[OK] Liturgical section marker '{marker}' found and replaced")
            break

    return assessment, revised_introduction, revised_verses


def main():
    # Paths
    response_file = Path("output/debug/college_editor_response_psalm_121.txt")
    output_dir = Path("output/psalm_121")

    assessment_file = output_dir / "psalm_121_assessment_college.md"
    intro_file = output_dir / "psalm_121_edited_intro_college.md"
    verses_file = output_dir / "psalm_121_edited_verses_college.md"

    # Check that response file exists
    if not response_file.exists():
        print(f"ERROR: Response file not found: {response_file}")
        return 1

    # Read the saved response
    print(f"Reading college editor response from {response_file}...")
    response_text = response_file.read_text(encoding='utf-8')
    print(f"  Response length: {len(response_text)} characters")

    # Parse with updated logic
    print("\nParsing response with updated parser...")
    assessment, revised_introduction, revised_verses = parse_editorial_response(response_text)

    # Report extraction results
    print(f"\nExtraction results:")
    print(f"  Assessment: {len(assessment)} characters")
    print(f"  Introduction: {len(revised_introduction)} characters")
    print(f"  Verses: {len(revised_verses)} characters")

    if not revised_verses:
        print("\nERROR: Verse commentary section still empty after parsing!")
        print("This suggests the regex pattern still doesn't match the LLM output.")
        return 1

    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write assessment file
    print(f"\nWriting {assessment_file}...")
    assessment_file.write_text(assessment, encoding='utf-8')
    print(f"  [OK] Wrote {len(assessment)} characters")

    # Write introduction file
    print(f"Writing {intro_file}...")
    intro_file.write_text(revised_introduction, encoding='utf-8')
    print(f"  [OK] Wrote {len(revised_introduction)} characters")

    # Write verses file
    print(f"Writing {verses_file}...")
    verses_file.write_text(revised_verses, encoding='utf-8')
    print(f"  [OK] Wrote {len(revised_verses)} characters")

    print("\n[SUCCESS] Psalm 121 college files regenerated.")
    print("\nFixed files:")
    print(f"  - {assessment_file}")
    print(f"  - {intro_file}")
    print(f"  - {verses_file}")

    return 0


if __name__ == '__main__':
    exit(main())
