"""
Standalone Scripture Citation Verifier

Run the scripture citation verifier against psalm commentary output to check
for misquoted biblical verses. Optionally triggers a targeted copy editor
fix pass for detected errors.

Usage:
    python scripts/run_scripture_verifier.py 41
    python scripts/run_scripture_verifier.py 41 --fix
    python scripts/run_scripture_verifier.py 36 37 38
    python scripts/run_scripture_verifier.py 41 --input-file output/psalm_41/psalm_041_print_ready.md

The verifier produces a report file in the psalm's output directory:
    psalm_NNN_citation_verification.md
"""

import argparse
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.scripture_verifier import (
    verify_citations,
    format_verification_report,
    format_fix_prompt,
)
from src.utils.logger import get_logger


def main():
    parser = argparse.ArgumentParser(
        description="Verify scripture citations in psalm commentary output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_scripture_verifier.py 41
  python scripts/run_scripture_verifier.py 41 --fix
  python scripts/run_scripture_verifier.py 36 37 38
  python scripts/run_scripture_verifier.py 41 --input-file output/psalm_41/psalm_041_print_ready.md
"""
    )
    parser.add_argument(
        "psalms",
        type=int,
        nargs="+",
        help="Psalm number(s) to verify (e.g., 41 or 36 37 38)"
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        help="Override the default input file path"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="database/tanakh.db",
        help="Path to tanakh.db (default: database/tanakh.db)"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Run a targeted copy editor fix pass for detected errors"
    )
    parser.add_argument(
        "--copy-model",
        type=str,
        default="gpt-5.4",
        help="Model for copy editor fix pass (default: gpt-5.4)"
    )

    args = parser.parse_args()
    logger = get_logger("run_scripture_verifier")

    # Ensure UTF-8 on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    # Validate psalm numbers
    for ps in args.psalms:
        if ps < 1 or ps > 150:
            logger.error(f"Invalid psalm number: {ps} (must be 1-150)")
            return 1

    results = []
    errors = []

    for psalm_num in args.psalms:
        # Resolve input file
        psalm_dir = Path(f"output/psalm_{psalm_num}")
        if args.input_file:
            input_file = args.input_file
        else:
            # Prefer copy-edited, fall back to print-ready
            copy_edited = psalm_dir / f"psalm_{psalm_num:03d}_copy_edited.md"
            print_ready = psalm_dir / f"psalm_{psalm_num:03d}_print_ready.md"
            if copy_edited.exists():
                input_file = copy_edited
            elif print_ready.exists():
                input_file = print_ready
            else:
                logger.error(f"No commentary file found for Psalm {psalm_num}")
                errors.append(psalm_num)
                continue

        print(f"\n{'═' * 60}")
        print(f"  SCRIPTURE CITATION VERIFIER — Psalm {psalm_num}")
        print(f"{'═' * 60}")
        print(f"  Input: {input_file}")

        # Read the file
        text = input_file.read_text(encoding='utf-8')
        print(f"  Size: {len(text):,} chars / {len(text.splitlines())} lines")

        # Run verification
        issues = verify_citations(text, db_path=args.db_path, psalm_number=psalm_num)

        # Generate report
        report = format_verification_report(issues, psalm_number=psalm_num)

        # Save report
        report_path = psalm_dir / f"psalm_{psalm_num:03d}_citation_verification.md"
        report_path.write_text(report, encoding='utf-8')

        # Display results
        if not issues:
            print(f"  ✅ All citations verified — no misquotes detected")
        else:
            print(f"  ⚠️  {len(issues)} issue(s) detected:")
            for i, issue in enumerate(issues, 1):
                type_icon = {
                    "NOT_SUBSTRING": "❌",
                    "BOOK_NOT_IN_DB": "❓",
                }[issue.issue_type]
                print(f"    {type_icon} [{issue.issue_type}] {issue.citation_ref} "
                      f"at {issue.location_hint} (line ~{issue.line_number})")
                if issue.issue_type == "NOT_SUBSTRING":
                    print(f"       Quoted: {issue.quoted_hebrew}")
                    print(f"       Actual: {issue.actual_hebrew}")

        print(f"  Report: {report_path}")
        print(f"{'═' * 60}\n")

        results.append((psalm_num, issues, input_file))

        # Fix pass
        if args.fix and issues:
            fixable = [i for i in issues if i.issue_type == "NOT_SUBSTRING"]
            if fixable:
                print(f"  🔧 Running copy editor fix pass for {len(fixable)} fixable issue(s)...")
                try:
                    from src.agents.copy_editor import CopyEditor
                    from src.utils.cost_tracker import CostTracker

                    cost_tracker = CostTracker()
                    editor = CopyEditor(model=args.copy_model, cost_tracker=cost_tracker)

                    # Generate fix prompt
                    fix_prompt = format_fix_prompt(fixable)

                    # Run fix pass using the copy editor
                    result = editor.edit_commentary(
                        psalm_number=psalm_num,
                        input_file=input_file,
                    )

                    print(f"  ✅ Fix pass complete: {result['edited_file']}")
                    print(f"  {cost_tracker.get_summary()}")

                except Exception as e:
                    logger.error(f"Fix pass failed: {e}", exc_info=True)
                    print(f"  ❌ Fix pass error: {e}")

    # Batch summary
    if len(args.psalms) > 1:
        print(f"\n{'═' * 60}")
        print(f"  BATCH SUMMARY")
        print(f"{'═' * 60}")
        total_issues = 0
        for psalm_num, issues, _ in results:
            total_issues += len(issues)
            status = "✅" if not issues else f"⚠️  {len(issues)} issue(s)"
            print(f"  Psalm {psalm_num}: {status}")
        for psalm_num in errors:
            print(f"  Psalm {psalm_num}: ❌ FILE NOT FOUND")
        print(f"  Total issues: {total_issues}")
        print(f"{'═' * 60}\n")

    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
