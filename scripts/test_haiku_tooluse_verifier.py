"""
Haiku Tool-Use Citation Verifier — Test Script (Session 312)

Tests the tool-use architecture where Haiku identifies citations, calls
lookup_verse to get actual text from tanakh.db, and judges matches — all
in a single conversation turn.

Compares results against the existing regex verifier for validation.

Usage:
    python scripts/test_haiku_tooluse_verifier.py 41
    python scripts/test_haiku_tooluse_verifier.py 41 --verbose
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.scripture_verifier import (
    verify_citations,
    verify_citations_tooluse,
    format_verification_report,
)


def main():
    parser = argparse.ArgumentParser(description="Test Haiku tool-use citation verifier")
    parser.add_argument("psalm", type=int, help="Psalm number to verify")
    parser.add_argument("--db-path", default="database/tanakh.db")
    parser.add_argument("--input-file", type=Path, help="Override input file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    # Load text
    if args.input_file:
        input_file = args.input_file
    else:
        psalm_dir = Path(f"output/psalm_{args.psalm}")
        input_file = psalm_dir / f"psalm_{args.psalm:03d}_print_ready.md"
        if not input_file.exists():
            input_file = psalm_dir / f"psalm_{args.psalm:03d}_copy_edited.md"

    if not input_file.exists():
        print(f"ERROR: File not found: {input_file}")
        return 1

    text = input_file.read_text(encoding="utf-8")
    print(f"Input: {input_file}")
    print(f"Size: {len(text):,} chars / {len(text.splitlines())} lines")

    # --- Run tool-use verifier ---
    print(f"\n{'=' * 60}")
    print(f"  HAIKU TOOL-USE VERIFIER")
    print(f"{'=' * 60}")

    tooluse_issues, tooluse_stats = verify_citations_tooluse(
        text, db_path=args.db_path, psalm_number=args.psalm
    )

    print(f"\n  Turns: {tooluse_stats.get('turns', '?')}")
    print(f"  Lookups: {tooluse_stats.get('lookups_performed', '?')}")
    print(f"  Citations found: {tooluse_stats.get('total_citations_found', '?')}")
    print(f"  Auto-passed: {tooluse_stats.get('auto_passed', '?')}")
    print(f"  Skipped: {tooluse_stats.get('skipped', '?')}")
    print(f"  Mismatches (before filter): {tooluse_stats.get('mismatches_before_filter', '?')}")
    print(f"  Filtered as false positive: {tooluse_stats.get('filtered_count', '?')}")
    print(f"  Tokens: {tooluse_stats['input_tokens']:,} in / {tooluse_stats['output_tokens']:,} out")
    cache_read = tooluse_stats.get('cache_read_tokens', 0)
    cache_create = tooluse_stats.get('cache_creation_tokens', 0)
    if cache_read or cache_create:
        print(f"  Cache: {cache_read:,} read / {cache_create:,} creation")
    print(f"  Cost: ${tooluse_stats['cost']:.4f}  (extraction: ${tooluse_stats.get('extraction_cost', 0):.4f}, filter: ${tooluse_stats.get('filter_cost', 0):.4f})")
    print(f"  Time: {tooluse_stats.get('elapsed', 0):.1f}s")

    if tooluse_issues:
        print(f"\n  Genuine errors found: {len(tooluse_issues)}")
        for i, issue in enumerate(tooluse_issues, 1):
            print(f"\n  {i}. {issue.citation_ref}")
            print(f"     Location: {issue.location_hint}")
            print(f"     Quoted:   {issue.quoted_hebrew[:80]}")
            print(f"     Actual:   {issue.actual_hebrew[:80]}")
            if issue.normalized_quoted:
                print(f"     Details:  {issue.normalized_quoted[:100]}")
    else:
        print(f"\n  No genuine errors found.")

    # --- Run regex verifier for comparison ---
    print(f"\n{'=' * 60}")
    print(f"  REGEX VERIFIER (comparison)")
    print(f"{'=' * 60}")

    regex_issues = verify_citations(text, db_path=args.db_path, psalm_number=args.psalm)
    print(f"\n  Issues found (before Haiku filter): {len(regex_issues)}")
    for i, issue in enumerate(regex_issues, 1):
        print(f"    {i}. {issue.citation_ref}: {issue.quoted_hebrew[:60]}...")
        if args.verbose and issue.normalized_quoted:
            diff = ""
            if issue.normalized_actual:
                from src.utils.scripture_verifier import _describe_difference
                diff = _describe_difference(issue.normalized_quoted, issue.normalized_actual)
            print(f"       → {diff or issue.issue_type}")

    # --- Comparison ---
    print(f"\n{'=' * 60}")
    print(f"  COMPARISON")
    print(f"{'=' * 60}")

    def _normalize_ref(ref: str) -> str:
        """Normalize citation references for comparison."""
        import re
        ref = ref.strip("()")
        # Normalize numbered books: "2 Samuel" → "II Samuel", "1 Kings" → "I Kings"
        ref = re.sub(r'^2\s+', 'II ', ref)
        ref = re.sub(r'^1\s+', 'I ', ref)
        # Normalize "Psalm" → "Psalms"
        ref = re.sub(r'^Psalm\b', 'Psalms', ref)
        # Normalize abbreviations
        ref = re.sub(r'^Ps\b', 'Psalms', ref)
        ref = re.sub(r'^Ex\b', 'Exodus', ref)
        ref = re.sub(r'^Gen\b', 'Genesis', ref)
        ref = re.sub(r'^Jer\b', 'Jeremiah', ref)
        # Strip verse ranges (–N) for matching
        ref = re.sub(r'[–\-]\d+$', '', ref)
        return ref

    tooluse_refs = {_normalize_ref(issue.citation_ref) for issue in tooluse_issues}
    regex_refs = {_normalize_ref(issue.citation_ref) for issue in regex_issues}

    both = tooluse_refs & regex_refs
    tooluse_only = tooluse_refs - regex_refs
    regex_only = regex_refs - tooluse_refs

    print(f"\n  Found by both:      {len(both)}")
    for ref in sorted(both):
        print(f"    - {ref}")

    print(f"  Tool-use only:      {len(tooluse_only)}")
    for ref in sorted(tooluse_only):
        print(f"    + {ref}")

    print(f"  Regex only:         {len(regex_only)}")
    for ref in sorted(regex_only):
        print(f"    - {ref}")

    print(f"\n  Total cost: ${tooluse_stats['cost']:.4f}")
    print(f"{'=' * 60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
