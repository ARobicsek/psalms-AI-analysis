#!/usr/bin/env python3
"""
Run Liturgical Librarian with Verbose Output

This script runs the liturgical librarian for specified psalms and outputs
detailed results including:
1. All phrase matches found
2. LLM validation results (what was filtered and why)
3. Final summaries with Hebrew quotes and translations
4. Statistics

Usage:
    python run_liturgical_librarian.py --psalms 1 2 20 145 150 --output output/liturgy_results.txt
    python run_liturgical_librarian.py --psalm 23 --output output/psalm23_verbose.txt
"""

import sys
import argparse
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from agents.liturgical_librarian import LiturgicalLibrarian


def format_phrase_result(phrase_match, index):
    """Format a single phrase match result for output."""
    output = []
    output.append(f"\n{'='*80}")
    output.append(f"PHRASE {index}: {phrase_match.psalm_phrase_hebrew}")
    output.append(f"{'='*80}")
    output.append(f"Verse Range: {phrase_match.psalm_verse_range}")
    output.append(f"Phrase Length: {phrase_match.phrase_length} words")
    output.append(f"Total Occurrences: {phrase_match.occurrence_count}")
    output.append(f"Unique Prayer Contexts: {phrase_match.unique_prayer_contexts}")
    output.append(f"Average Confidence: {phrase_match.confidence_avg:.2%}")
    output.append(f"Match Types: {', '.join(phrase_match.match_types)}")

    if phrase_match.validation_notes:
        output.append(f"\n⚠️  VALIDATION WARNING: {phrase_match.validation_notes}")

    output.append(f"\n--- LITURGICAL SUMMARY ---")
    output.append(phrase_match.liturgical_summary)

    output.append(f"\n--- PRAYER CONTEXTS ---")
    for i, ctx in enumerate(phrase_match.prayer_contexts, 1):
        output.append(f"  {i}. {ctx}")

    if phrase_match.occasions:
        output.append(f"\n--- OCCASIONS ---")
        output.append(f"  {', '.join(phrase_match.occasions)}")

    if phrase_match.services:
        output.append(f"\n--- SERVICES ---")
        output.append(f"  {', '.join(phrase_match.services)}")

    if phrase_match.nusachs:
        output.append(f"\n--- TRADITIONS (NUSACH) ---")
        output.append(f"  {', '.join(phrase_match.nusachs)}")

    return "\n".join(output)


def run_librarian_for_psalm(librarian, psalm_num, output_file):
    """Run librarian for a single psalm and write results to file."""

    output_file.write(f"\n\n{'#'*80}\n")
    output_file.write(f"# PSALM {psalm_num}\n")
    output_file.write(f"{'#'*80}\n\n")

    print(f"\n{'='*80}")
    print(f"Processing Psalm {psalm_num}")
    print(f"{'='*80}\n")

    # Get phrase-based results with verbose output
    print(f"Querying database for Psalm {psalm_num}...")
    results = librarian.find_liturgical_usage_by_phrase(
        psalm_chapter=psalm_num,
        psalm_verses=None,
        min_confidence=0.75,
        include_raw_matches=True,
        separate_full_psalm=True
    )

    if not results:
        msg = f"No liturgical usage found for Psalm {psalm_num}.\n"
        print(msg)
        output_file.write(msg)
        return

    # Write summary statistics
    total_occurrences = sum(r.occurrence_count for r in results)
    summary = f"""
SUMMARY STATISTICS FOR PSALM {psalm_num}
{'='*80}
Total distinct phrases found: {len(results)}
Total occurrences across all prayers: {total_occurrences}
Average occurrences per phrase: {total_occurrences / len(results):.1f}

"""
    print(summary)
    output_file.write(summary)

    # Write each phrase result
    for i, phrase_match in enumerate(results, 1):
        result_text = format_phrase_result(phrase_match, i)
        print(f"\nProcessed phrase {i}/{len(results)}: {phrase_match.psalm_phrase_hebrew[:50]}...")
        output_file.write(result_text)
        output_file.write("\n")
        output_file.flush()  # Flush after each phrase so progress is visible

    print(f"\n✅ Completed Psalm {psalm_num}: {len(results)} phrases written to output")


def main():
    parser = argparse.ArgumentParser(
        description='Run Liturgical Librarian with verbose output',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process multiple psalms
  python run_liturgical_librarian.py --psalms 1 2 20 145 150 --output output/results.txt

  # Process a single psalm
  python run_liturgical_librarian.py --psalm 23 --output output/psalm23.txt

  # Process with custom confidence threshold
  python run_liturgical_librarian.py --psalm 23 --min-confidence 0.8 --output output/psalm23_high_conf.txt
        """
    )

    parser.add_argument(
        '--psalm',
        type=int,
        help='Process a single psalm'
    )
    parser.add_argument(
        '--psalms',
        type=int,
        nargs='+',
        help='Process multiple psalms (space-separated)'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output file path'
    )
    parser.add_argument(
        '--min-confidence',
        type=float,
        default=0.75,
        help='Minimum confidence threshold (0.0-1.0, default: 0.75)'
    )
    parser.add_argument(
        '--no-llm',
        action='store_true',
        help='Disable LLM summaries (use code-only)'
    )

    args = parser.parse_args()

    # Determine which psalms to process
    if args.psalm:
        psalms = [args.psalm]
    elif args.psalms:
        psalms = args.psalms
    else:
        parser.error("Must specify either --psalm or --psalms")

    # Validate psalm numbers
    for ps in psalms:
        if ps < 1 or ps > 150:
            parser.error(f"Invalid psalm number: {ps}. Must be between 1 and 150.")

    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize librarian with verbose mode
    print("Initializing Liturgical Librarian...")
    print(f"  LLM Summaries: {'Disabled' if args.no_llm else 'Enabled (Claude Haiku 4.5)'}")
    print(f"  Min Confidence: {args.min_confidence}")
    print(f"  Verbose Mode: ON (showing LLM prompts/responses)")
    print(f"  Output File: {output_path}")

    librarian = LiturgicalLibrarian(
        use_llm_summaries=not args.no_llm,
        verbose=True  # Show LLM prompts and responses
    )

    # Process each psalm
    with open(output_path, 'w', encoding='utf-8') as output_file:
        # Write header
        header = f"""
LITURGICAL LIBRARIAN VERBOSE OUTPUT
Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Configuration:
  Psalms: {', '.join(map(str, psalms))}
  LLM Summaries: {'Disabled' if args.no_llm else 'Enabled (Claude Haiku 4.5)'}
  Min Confidence: {args.min_confidence}
  Verbose Mode: ON

This output includes:
  1. All phrase matches found in the liturgy index
  2. LLM validation results (filtered phrases are marked)
  3. Detailed summaries with Hebrew quotes and translations
  4. Prayer contexts, occasions, services, and traditions
  5. Statistics for each psalm

{'='*80}

"""
        output_file.write(header)

        # Process each psalm
        for psalm_num in psalms:
            try:
                run_librarian_for_psalm(librarian, psalm_num, output_file)
            except Exception as e:
                error_msg = f"\n❌ ERROR processing Psalm {psalm_num}: {str(e)}\n"
                print(error_msg)
                output_file.write(error_msg)
                import traceback
                traceback.print_exc()

        # Write footer
        footer = f"""

{'='*80}
PROCESSING COMPLETE
{'='*80}

Total psalms processed: {len(psalms)}
Output file: {output_path}

Note: Filtered phrases (marked with ⚠️ VALIDATION WARNING) were identified by the
LLM as potentially being from other psalms or non-psalm content and are included
in this verbose output for review.

"""
        output_file.write(footer)

    print(f"\n{'='*80}")
    print(f"✅ ALL PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"\nOutput written to: {output_path}")
    print(f"Total psalms processed: {len(psalms)}")
    print("\nYou can now review the output file for:")
    print("  • Detailed phrase-by-phrase analysis")
    print("  • LLM-generated summaries with quotes and translations")
    print("  • Validation warnings for filtered phrases")
    print("  • Complete liturgical context information")


if __name__ == "__main__":
    main()
