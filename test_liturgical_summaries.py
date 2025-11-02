"""
Test Liturgical Librarian LLM Summaries for Specific Psalms

This script runs the liturgical librarian for Psalms 1, 2, 20, and 145
with verbose mode enabled to show:
1. What data the LLM receives in its prompts
2. The LLM's responses
3. The final formatted output

Outputs are saved to output/liturgical_test_ps{N}.txt for each psalm.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.liturgical_librarian import LiturgicalLibrarian


def test_psalm_liturgy(psalm_number: int, output_dir: str = "output"):
    """Test liturgical librarian for a specific psalm."""

    print("\n" + "=" * 80)
    print(f"TESTING LITURGICAL LIBRARIAN FOR PSALM {psalm_number}")
    print("=" * 80)

    # Create output directory if needed
    Path(output_dir).mkdir(exist_ok=True)

    # Initialize librarian with verbose mode and LLM summaries enabled
    print("\nInitializing LiturgicalLibrarian with verbose=True, use_llm_summaries=True...")
    librarian = LiturgicalLibrarian(
        use_llm_summaries=True,
        verbose=True  # This will print LLM prompts and responses
    )

    # Get phrase-based results (this is what the commentary pipeline uses)
    print(f"\nQuerying liturgical usage for Psalm {psalm_number}...")
    print("(LLM prompts and responses will be shown below)")
    print("-" * 80)

    results = librarian.find_liturgical_usage_by_phrase(
        psalm_chapter=psalm_number,
        psalm_verses=None,  # Entire psalm
        min_confidence=0.75,
        include_raw_matches=True,  # Include details for inspection
        separate_full_psalm=True
    )

    print("\n" + "=" * 80)
    print(f"FINAL OUTPUT FOR PSALM {psalm_number}")
    print("=" * 80)

    # Prepare output
    output_lines = []
    output_lines.append(f"LITURGICAL USAGE SUMMARY: PSALM {psalm_number}\n")
    output_lines.append("=" * 80 + "\n")

    if not results:
        msg = f"No liturgical usage found for Psalm {psalm_number}.\n"
        print(msg)
        output_lines.append(msg)
    else:
        total_occurrences = sum(r.occurrence_count for r in results)
        summary = f"Found {len(results)} distinct phrase(s) with {total_occurrences} total occurrence(s):\n"
        print(summary)
        output_lines.append(summary)
        output_lines.append("\n")

        # Show each phrase result
        for i, match in enumerate(results, 1):
            # Header
            header = f"\n{i}. {match.psalm_phrase_hebrew}\n"
            content_info = f"   Content of Psalm Used: {match.content_used_description}\n"
            verse_ref = f"   Verse Reference: {match.psalm_verse_range}\n"
            occurrence_info = f"   Occurrences: {match.occurrence_count} across {match.unique_prayer_contexts} prayer context(s)\n"
            confidence_info = f"   Confidence: {int(match.confidence_avg * 100)}%\n"

            print(header, end='')
            print(content_info, end='')
            print(verse_ref, end='')
            print(occurrence_info, end='')
            print(confidence_info, end='')

            output_lines.append(header)
            output_lines.append(content_info)
            output_lines.append(verse_ref)
            output_lines.append(occurrence_info)
            output_lines.append(confidence_info)

            # LLM Summary (this is what goes into the research bundle)
            summary_section = f"\n   LITURGICAL SUMMARY (LLM-generated):\n   {match.liturgical_summary}\n"
            print(summary_section)
            output_lines.append(summary_section)

            # Prayer contexts
            contexts_header = f"\n   PRAYER CONTEXTS:\n"
            print(contexts_header, end='')
            output_lines.append(contexts_header)

            for ctx in match.prayer_contexts[:10]:
                ctx_line = f"     - {ctx}\n"
                print(ctx_line, end='')
                output_lines.append(ctx_line)

            if len(match.prayer_contexts) > 10:
                more_line = f"     ... and {len(match.prayer_contexts) - 10} more\n"
                print(more_line, end='')
                output_lines.append(more_line)

            # Show a few raw matches for inspection
            if match.raw_matches:
                raw_header = f"\n   SAMPLE RAW MATCHES (first 3):\n"
                print(raw_header, end='')
                output_lines.append(raw_header)

                for j, raw in enumerate(match.raw_matches[:3], 1):
                    raw_info = f"     {j}. Prayer: {raw.canonical_prayer_name or raw.prayer_name or 'Unknown'}\n"
                    location_info = f"        Location: {raw.canonical_location_description[:200] if raw.canonical_location_description else 'N/A'}...\n"
                    l1_info = f"        L1 Occasion: {raw.canonical_L1_Occasion or 'N/A'}\n"
                    l2_info = f"        L2 Service: {raw.canonical_L2_Service or 'N/A'}\n"
                    l3_info = f"        L3 Signpost: {raw.canonical_L3_Signpost or 'N/A'}\n"
                    context_info = f"        Liturgy Context: {raw.liturgy_context[:150]}...\n"

                    print(raw_info, end='')
                    print(location_info, end='')
                    print(l1_info, end='')
                    print(l2_info, end='')
                    print(l3_info, end='')
                    print(context_info, end='')

                    output_lines.append(raw_info)
                    output_lines.append(location_info)
                    output_lines.append(l1_info)
                    output_lines.append(l2_info)
                    output_lines.append(l3_info)
                    output_lines.append(context_info)

            print("\n" + "-" * 80)
            output_lines.append("\n" + "-" * 80 + "\n")

    # Save to file
    output_file = Path(output_dir) / f"liturgical_test_ps{psalm_number}.txt"
    output_file.write_text("".join(output_lines), encoding='utf-8')
    print(f"\n[OK] Output saved to: {output_file}")

    return results


def main():
    """Test liturgical librarian for Psalms 1, 2, 20, and 145."""

    # Configure UTF-8 output for Windows console
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    test_psalms = [1, 2, 20, 145]

    print("\n" + "=" * 80)
    print("LITURGICAL LIBRARIAN LLM SUMMARY TEST")
    print("=" * 80)
    print("\nThis script will test the liturgical librarian for Psalms 1, 2, 20, and 145.")
    print("You will see:")
    print("  1. The prompts sent to the LLM (Claude Haiku 4.5)")
    print("  2. The LLM's responses")
    print("  3. The final formatted output")
    print("\nOutputs will be saved to output/liturgical_test_ps{N}.txt")
    print("\n" + "=" * 80)

    results_summary = {}

    for psalm_num in test_psalms:
        try:
            results = test_psalm_liturgy(psalm_num)
            results_summary[psalm_num] = {
                'success': True,
                'phrase_count': len(results),
                'total_occurrences': sum(r.occurrence_count for r in results)
            }
        except Exception as e:
            print(f"\n[ERROR] Failed to process Psalm {psalm_num}: {e}")
            import traceback
            traceback.print_exc()
            results_summary[psalm_num] = {
                'success': False,
                'error': str(e)
            }

    # Final summary
    print("\n\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)

    for psalm_num, summary in results_summary.items():
        if summary['success']:
            print(f"Psalm {psalm_num}: [OK] {summary['phrase_count']} phrases, "
                  f"{summary['total_occurrences']} total occurrences")
        else:
            print(f"Psalm {psalm_num}: [ERROR] {summary['error']}")

    print("\n" + "=" * 80)
    print("All outputs saved to output/liturgical_test_ps{N}.txt")
    print("=" * 80)


if __name__ == "__main__":
    main()
