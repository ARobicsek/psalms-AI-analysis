"""
Create Print-Ready Commentary
Generates final print-ready Psalm commentary with:
1. Verse text (Hebrew + English)
2. Divine names modifications applied throughout
3. Introduction essay + verse-by-verse commentary

Usage:
    python scripts/create_print_ready_commentary.py --psalm 29

Author: Claude (Anthropic)
Date: 2025-10-17
"""

import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.commentary_formatter import CommentaryFormatter
from src.utils.logger import get_logger


def create_print_ready_commentary(
    psalm_number: int,
    test_dir: str = "output/phase3_test",
    output_name: Optional[str] = None
):
    """
    Create print-ready commentary for a psalm.

    Args:
        psalm_number: Psalm number
        test_dir: Directory containing synthesis output files
        output_name: Output filename (default: psalm_NNN_print_ready.md)
    """
    print("=" * 80)
    print("CREATE PRINT-READY COMMENTARY")
    print("=" * 80)
    print()

    # Setup paths
    test_path = project_root / test_dir
    intro_file = test_path / f"psalm_{psalm_number:03d}_synthesis_intro.md"
    verses_file = test_path / f"psalm_{psalm_number:03d}_synthesis_verses.md"

    # Check files exist
    if not intro_file.exists():
        print(f"ERROR: Introduction file not found: {intro_file}")
        return 1

    if not verses_file.exists():
        print(f"ERROR: Verse commentary file not found: {verses_file}")
        return 1

    print(f"Psalm Number: {psalm_number}")
    print(f"Introduction: {intro_file.name}")
    print(f"Verses:       {verses_file.name}")
    print()

    # Determine output path
    if not output_name:
        output_name = f"psalm_{psalm_number:03d}_print_ready.md"
    output_file = test_path / output_name

    print("Processing:")
    print("  1. Loading introduction essay")
    print("  2. Loading verse commentary")
    print("  3. Fetching Hebrew and English verse text from database")
    print("  4. Applying divine names modifications to ALL Hebrew text")
    print("  5. Formatting final print-ready document")
    print()

    # Initialize formatter
    logger = get_logger("print_ready")
    formatter = CommentaryFormatter(logger=logger)

    # Format commentary
    try:
        formatter.format_from_files(
            intro_file=str(intro_file),
            verses_file=str(verses_file),
            psalm_number=psalm_number,
            output_file=str(output_file),
            apply_divine_names=True
        )

        print("=" * 80)
        print("SUCCESS!")
        print("=" * 80)
        print()
        print("Print-ready commentary created:")
        print(f"  {output_file}")
        print()
        print("Features:")
        print("  ✓ Introduction essay (800-1200 words)")
        print("  ✓ Verse-by-verse commentary with Hebrew and English text")
        print("  ✓ Divine names modified (יהוה → ה׳, אלהים → אלקים, etc.)")
        print("  ✓ Ready for publication/distribution")
        print()
        print("=" * 80)

        return 0

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Command-line interface."""
    import argparse

    # Ensure UTF-8 for Hebrew output
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Create print-ready Psalm commentary with verse text and divine names modifications'
    )
    parser.add_argument('--psalm', type=int, required=True,
                       help='Psalm number')
    parser.add_argument('--test-dir', type=str, default='output/phase3_test',
                       help='Directory containing synthesis files (default: output/phase3_test)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output filename (default: psalm_NNN_print_ready.md)')

    args = parser.parse_args()

    return create_print_ready_commentary(
        psalm_number=args.psalm,
        test_dir=args.test_dir,
        output_name=args.output
    )


if __name__ == '__main__':
    sys.exit(main())
