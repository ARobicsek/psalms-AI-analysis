#!/usr/bin/env python3
"""Test script to run Master Editor only on existing Psalm 1 files."""

from pathlib import Path
from src.agents.master_editor import MasterEditor

def main():
    psalm_num = 1

    # Input files (already exist)
    intro_file = Path(f"output/psalm_{psalm_num}/psalm_001_synthesis_intro.md")
    verses_file = Path(f"output/psalm_{psalm_num}/psalm_001_synthesis_verses.md")
    research_file = Path(f"output/psalm_{psalm_num}/psalm_001_research_v2.md")
    macro_file = Path(f"output/psalm_{psalm_num}/psalm_001_macro.json")
    micro_file = Path(f"output/psalm_{psalm_num}/psalm_001_micro_v2.json")

    # Output files
    assessment_file = Path(f"output/psalm_{psalm_num}/psalm_001_assessment.md")
    edited_intro_file = Path(f"output/psalm_{psalm_num}/psalm_001_edited_intro.md")
    edited_verses_file = Path(f"output/psalm_{psalm_num}/psalm_001_edited_verses.md")

    print(f"Running Master Editor for Psalm {psalm_num}...")
    print(f"This will generate debug files in output/debug/")

    # Initialize Master Editor
    editor = MasterEditor(model="gpt-5")

    # Run editorial review
    result = editor.edit_commentary(
        introduction_file=intro_file,
        verse_file=verses_file,
        research_file=research_file,
        macro_file=macro_file,
        micro_file=micro_file,
        psalm_number=psalm_num
    )

    # Save results
    assessment_file.write_text(result['assessment'], encoding='utf-8')
    edited_intro_file.write_text(result['revised_introduction'], encoding='utf-8')
    edited_verses_file.write_text(result['revised_verses'], encoding='utf-8')

    print(f"\n✓ Master Editor complete!")
    print(f"  Assessment: {assessment_file}")
    print(f"  Intro: {edited_intro_file}")
    print(f"  Verses: {edited_verses_file}")
    print(f"\n✓ Debug files saved:")
    print(f"  Prompt: output/debug/master_editor_prompt_psalm_{psalm_num}.txt")
    print(f"  Response: output/debug/master_editor_response_psalm_{psalm_num}.txt")

if __name__ == "__main__":
    main()
