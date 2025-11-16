"""
Test script for SynthesisWriter agent (Pass 3)
Tests commentary generation for Psalm 29 using existing analysis files
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.synthesis_writer import SynthesisWriter
from src.utils.logger import get_logger

def test_psalm_29_synthesis():
    """
    Test SynthesisWriter on Psalm 29 using Phase 3 test outputs.
    """
    # Ensure UTF-8 encoding for Hebrew output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 80)
    print("SYNTHESIS WRITER TEST: PSALM 29")
    print("=" * 80)
    print()

    # Setup paths
    test_dir = project_root / "output" / "phase3_test"
    macro_file = test_dir / "psalm_029_macro.json"
    micro_file = test_dir / "psalm_029_micro_v2.json"
    research_file = test_dir / "psalm_029_research_v2.md"

    # Check files exist
    for file_path in [macro_file, micro_file, research_file]:
        if not file_path.exists():
            print(f"ERROR: Required file not found: {file_path}")
            return 1

    print("Input files found:")
    print(f"  Macro:    {macro_file.name}")
    print(f"  Micro:    {micro_file.name}")
    print(f"  Research: {research_file.name}")
    print()

    # Initialize writer
    logger = get_logger("test_synthesis")
    writer = SynthesisWriter(logger=logger)

    print("Generating commentary synthesis...")
    print("This will make 2 API calls:")
    print("  1. Introduction essay (800-1200 words)")
    print("  2. Verse commentary (11 verses x 150-300 words)")
    print()
    print("Estimated time: 60-120 seconds")
    print()

    # Generate commentary
    try:
        commentary = writer.write_and_save(
            macro_file=str(macro_file),
            micro_file=str(micro_file),
            research_file=str(research_file),
            output_dir=str(test_dir),
            output_name="psalm_029_synthesis"
        )

        print("=" * 80)
        print("SYNTHESIS COMPLETE!")
        print("=" * 80)
        print()
        print(f"Psalm Number: {commentary['psalm_number']}")
        print()

        # Stats
        intro_words = len(commentary['introduction'].split())
        verse_words = len(commentary['verse_commentary'].split())

        print("INTRODUCTION ESSAY:")
        print(f"  Length: {intro_words} words ({len(commentary['introduction'])} chars)")
        print(f"  Target: 800-1200 words")
        print()

        print("VERSE COMMENTARY:")
        print(f"  Length: {verse_words} words ({len(commentary['verse_commentary'])} chars)")
        print(f"  Average per verse: ~{verse_words // 11} words (target: 150-300)")
        print()

        # Preview
        print("INTRODUCTION PREVIEW (first 300 chars):")
        print("-" * 80)
        print(commentary['introduction'][:300] + "...")
        print("-" * 80)
        print()

        print("VERSE COMMENTARY PREVIEW (first 300 chars):")
        print("-" * 80)
        print(commentary['verse_commentary'][:300] + "...")
        print("-" * 80)
        print()

        print("OUTPUT FILES:")
        print(f"  {test_dir / 'psalm_029_synthesis.md'}")
        print(f"  {test_dir / 'psalm_029_synthesis_intro.md'}")
        print(f"  {test_dir / 'psalm_029_synthesis_verses.md'}")
        print()
        print("=" * 80)
        print("TEST PASSED!")
        print("=" * 80)

        return 0

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(test_psalm_29_synthesis())
