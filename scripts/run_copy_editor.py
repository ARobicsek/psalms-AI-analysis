"""
Standalone Copy Editor Runner

Run the copy editor agent against an existing psalm commentary to check for
and correct the 6 categories of error defined in Copy_editor_plan.md.

Usage:
    python scripts/run_copy_editor.py 38
    python scripts/run_copy_editor.py 38 --dry-run
    python scripts/run_copy_editor.py 38 --input-file output/psalm_38/psalm_038_print_ready.md

The copy editor produces three output files in the psalm's output directory:
    psalm_NNN_copy_edited.md     — full corrected commentary
    psalm_NNN_copy_edit_changes.md — list of changes with category labels
    psalm_NNN_copy_edit_diff.md  — unified diff for quick review
"""

import argparse
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.copy_editor import CopyEditor
from src.utils.logger import get_logger


def main():
    parser = argparse.ArgumentParser(
        description="Run copy editor on an existing psalm commentary",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Error Categories:
  1. False structural claims (chiasmus, inclusio, merism)
  2. Internal inconsistencies
  3. Form/content confusion (phonosemantic overreach)
  4. Negative or empty citations
  5. Hebrew script integrity
  6. Weak cross-cultural parallels

Examples:
  python scripts/run_copy_editor.py 38
  python scripts/run_copy_editor.py 36 37 38
  python scripts/run_copy_editor.py 38 --dry-run
  python scripts/run_copy_editor.py 38 --model claude-sonnet-4-20250514
"""
    )
    parser.add_argument(
        "psalms",
        type=int,
        nargs="+",
        help="Psalm number(s) to process (e.g., 38 or 36 37 38)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without calling the API"
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        help="Override the default input file path"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Override the default output directory"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override the model (default: claude-opus-4-6)"
    )

    args = parser.parse_args()
    logger = get_logger("run_copy_editor")

    # Validate psalm numbers
    for ps in args.psalms:
        if ps < 1 or ps > 150:
            logger.error(f"Invalid psalm number: {ps} (must be 1-150)")
            return 1

    # Initialize editor
    editor = CopyEditor(model=args.model, logger=logger)

    results = []
    errors = []

    for psalm_num in args.psalms:
        # Resolve input file
        if args.input_file:
            input_file = args.input_file
        else:
            input_file = Path(f"output/psalm_{psalm_num}/psalm_{psalm_num:03d}_print_ready.md")

        if not input_file.exists():
            logger.error(f"File not found: {input_file}")
            errors.append(psalm_num)
            continue

        # Dry run — just show what would be processed
        if args.dry_run:
            text = input_file.read_text(encoding='utf-8')
            print(f"\n{'═' * 60}")
            print(f"  DRY RUN — Psalm {psalm_num}")
            print(f"{'═' * 60}")
            print(f"  Input: {input_file}")
            print(f"  Size: {len(text):,} chars / {len(text.splitlines())} lines")

            # Parse zones to show structure
            zones = editor._parse_zones(text, psalm_num)
            editable = editor._assemble_editable_content(zones)
            print(f"  Editable content: {len(editable):,} chars")
            print(f"  Protected content: {len(text) - len(editable):,} chars")
            print(f"  Model: {editor.model}")
            print(f"{'═' * 60}\n")
            continue

        # Run the editor
        try:
            logger.info(f"\n{'═' * 60}")
            logger.info(f"Processing Psalm {psalm_num}...")
            logger.info(f"{'═' * 60}")

            result = editor.edit_commentary(
                psalm_number=psalm_num,
                input_file=input_file,
                output_dir=args.output_dir,
            )
            results.append((psalm_num, result))
        except Exception as e:
            logger.error(f"Error processing Psalm {psalm_num}: {e}")
            errors.append(psalm_num)
            import traceback
            traceback.print_exc()

    # Print final summary for multi-psalm runs
    if len(args.psalms) > 1 and not args.dry_run:
        print(f"\n{'═' * 60}")
        print(f"  BATCH SUMMARY")
        print(f"{'═' * 60}")
        for psalm_num, result in results:
            print(f"  ✅ Psalm {psalm_num}")
            print(f"     Edited:  {result['edited_file']}")
            print(f"     Changes: {result['changes_file']}")
            print(f"     Diff:    {result['diff_file']}")
        for psalm_num in errors:
            print(f"  ❌ Psalm {psalm_num} — FAILED")
        print(f"{'═' * 60}\n")

    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
