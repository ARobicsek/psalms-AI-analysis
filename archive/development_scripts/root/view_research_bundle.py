"""
View Liturgical Librarian Research Bundle

This script generates and displays the complete research bundle that would be
provided to the commentary generation agents (Master Editor and Synthesis Writer).

The research bundle is MINIMAL by design - it contains ONLY:
- Psalm chapter number
- Full psalm summary (if the psalm is recited in full)
- Phrase groups: each with phrase text, verse range, and LLM summary

No metadata, no match details - just the scholarly summaries needed for commentary.

Usage:
    python view_research_bundle.py [psalm_number] [--format json|text|both]

Examples:
    python view_research_bundle.py 1
    python view_research_bundle.py 23 --format json
    python view_research_bundle.py 145 --format both

Output:
    - Console: Summary and overview
    - File: Complete research bundle in chosen format(s)
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents.liturgical_librarian import LiturgicalLibrarian


def format_text_output(bundle: dict, psalm_num: int) -> str:
    """Format the research bundle as readable text"""
    lines = []

    lines.append("=" * 80)
    lines.append(f"LITURGICAL RESEARCH BUNDLE FOR PSALM {psalm_num}")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("This is the EXACT research bundle passed to commentary generation agents.")
    lines.append("It contains ONLY phrase/verse identifiers and LLM-generated summaries.")
    lines.append("")

    # Summary statistics
    lines.append("-" * 80)
    lines.append("BUNDLE CONTENTS")
    lines.append("-" * 80)
    has_full_psalm = bool(bundle.get('full_psalm_summary', '').strip())
    lines.append(f"Full Psalm Summary: {'Yes' if has_full_psalm else 'No'}")
    lines.append(f"Phrase Groups: {len(bundle.get('phrase_groups', []))}")
    lines.append("")

    # Full psalm summary
    if has_full_psalm:
        lines.append("")
        lines.append("=" * 80)
        lines.append("FULL PSALM SUMMARY")
        lines.append("=" * 80)
        lines.append("")
        lines.append("Identifier: [Full Psalm Recitation]")
        lines.append("")
        lines.append("Summary:")
        lines.append("-" * 80)
        lines.append(bundle.get('full_psalm_summary', ''))
        lines.append("")

    # Phrase groups
    phrase_groups = bundle.get('phrase_groups', [])
    if phrase_groups:
        lines.append("")
        lines.append("=" * 80)
        lines.append("PHRASE GROUPS")
        lines.append("=" * 80)
        lines.append(f"Total phrase groups: {len(phrase_groups)}")
        lines.append("")

        for i, group in enumerate(phrase_groups, 1):
            lines.append("")
            lines.append("=" * 80)
            lines.append(f"PHRASE GROUP {i} of {len(phrase_groups)}")
            lines.append("=" * 80)
            lines.append("")
            lines.append(f"Identifier:")
            lines.append(f"  Verse Range: {group.get('verses', 'Unknown')}")
            lines.append(f"  Hebrew Phrase: {group.get('phrase', 'N/A')}")
            lines.append("")
            lines.append("Summary:")
            lines.append("-" * 80)
            lines.append(group.get('summary', 'No summary available'))
            lines.append("")

    # Footer
    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF RESEARCH BUNDLE")
    lines.append("=" * 80)
    lines.append("")
    lines.append("This research bundle contains everything needed for commentary generation:")
    lines.append("- Each phrase/verse is identified")
    lines.append("- Each has a scholarly LLM-generated summary of its liturgical usage")
    lines.append("- No raw data or metadata - just the curated summaries")
    lines.append("")

    return "\n".join(lines)


def format_json_output(bundle: dict, psalm_num: int) -> str:
    """Format the research bundle as JSON"""
    # The bundle is already in the right format - just add metadata
    json_bundle = {
        'psalm_chapter': psalm_num,
        'generated': datetime.now().isoformat(),
        'full_psalm_summary': bundle.get('full_psalm_summary', ''),
        'phrase_groups': bundle.get('phrase_groups', [])
    }

    return json.dumps(json_bundle, ensure_ascii=False, indent=2)


def main():
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python view_research_bundle.py [psalm_number] [--format json|text|both]")
        print()
        print("Examples:")
        print("  python view_research_bundle.py 1")
        print("  python view_research_bundle.py 23 --format json")
        print("  python view_research_bundle.py 145 --format both")
        sys.exit(1)

    try:
        psalm_num = int(sys.argv[1])
        if psalm_num < 1 or psalm_num > 150:
            print(f"Error: Psalm number must be between 1 and 150")
            sys.exit(1)
    except ValueError:
        print(f"Error: '{sys.argv[1]}' is not a valid psalm number")
        sys.exit(1)

    # Get format option
    output_format = 'text'  # default
    if len(sys.argv) >= 4 and sys.argv[2] == '--format':
        output_format = sys.argv[3].lower()
        if output_format not in ['text', 'json', 'both']:
            print(f"Error: Format must be 'text', 'json', or 'both'")
            sys.exit(1)

    # Generate research bundle
    print(f"Generating research bundle for Psalm {psalm_num}...")
    print("=" * 80)
    print()

    librarian = LiturgicalLibrarian(verbose=True)
    bundle = librarian.generate_research_bundle(psalm_chapter=psalm_num)

    print()
    print("=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print()

    # Display summary
    has_full_psalm = bool(bundle.get('full_psalm_summary', '').strip())
    num_phrases = len(bundle.get('phrase_groups', []))

    print("SUMMARY:")
    print(f"  Full Psalm Summary: {'Yes' if has_full_psalm else 'No'}")
    print(f"  Phrase Groups: {num_phrases}")
    if has_full_psalm:
        print(f"  Full Psalm Summary Length: {len(bundle.get('full_psalm_summary', ''))} chars")
    print()

    # Write outputs
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if output_format in ['text', 'both']:
        text_file = f"research_bundle_psalm{psalm_num}_{timestamp}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(format_text_output(bundle, psalm_num))
        print(f"Text output written to: {text_file}")

    if output_format in ['json', 'both']:
        json_file = f"research_bundle_psalm{psalm_num}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            f.write(format_json_output(bundle, psalm_num))
        print(f"JSON output written to: {json_file}")

    print()
    print("=" * 80)
    print("WHAT'S IN THE BUNDLE:")
    print("=" * 80)
    print()
    print("The research bundle contains ONLY:")
    print("  1. Psalm chapter number")
    if has_full_psalm:
        print("  2. Full psalm summary (scholarly narrative)")
    print(f"  {3 if has_full_psalm else 2}. {num_phrases} phrase group(s), each with:")
    print("     - Hebrew phrase text")
    print("     - Verse range")
    print("     - LLM-generated scholarly summary")
    print()
    print("NO metadata, NO raw matches, NO prayer names - just the summaries")
    print("that the Master Editor and Synthesis Writer need for commentary.")
    print()


if __name__ == "__main__":
    main()
