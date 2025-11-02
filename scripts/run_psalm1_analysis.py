"""
Run Psalm 1 through the complete Liturgical Librarian pipeline.

This script runs the analysis on Psalm 1 and saves a clean output file.
"""

import sys
import os

# Configure UTF-8 output for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.agents.liturgical_librarian import LiturgicalLibrarian

if __name__ == "__main__":
    print("=" * 70)
    print("PSALM 1 LITURGICAL ANALYSIS")
    print("=" * 70)
    print()

    # Initialize librarian with LLM summaries
    librarian = LiturgicalLibrarian(
        use_llm_summaries=True,
        verbose=False  # Set to True to see prompts/responses
    )

    # Run analysis for Psalm 1
    print("Analyzing Psalm 1...")
    results = librarian.find_liturgical_usage_by_phrase(
        psalm_chapter=1,
        min_confidence=0.75,
        include_raw_matches=True,
        separate_full_psalm=True
    )

    # Save to output file
    output_file = "output/psalm1_liturgy_analysis.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("LITURGICAL USAGE: PSALM 1\n")
        f.write("=" * 70 + "\n\n")

        if not results:
            f.write("No liturgical usage found for Psalm 1.\n")
        else:
            total_occurrences = sum(r.occurrence_count for r in results)
            f.write(f"Found {len(results)} distinct phrase(s) with {total_occurrences} total occurrence(s):\n\n")

            for i, match in enumerate(results, 1):
                f.write(f"{i}. Phrase: {match.psalm_phrase_hebrew}\n")
                f.write(f"   Verse: {match.psalm_verse_range}\n")
                f.write(f"   Occurrences: {match.occurrence_count} across {match.unique_prayer_contexts} prayer context(s)\n")
                f.write(f"   Confidence: {int(match.confidence_avg * 100)}%\n")
                f.write(f"\n")

                # LLM summary
                f.write(f"   {match.liturgical_summary}\n")
                f.write(f"\n")

                # Prayer contexts
                f.write(f"   Prayer contexts:\n")
                for ctx in match.prayer_contexts[:10]:
                    f.write(f"     - {ctx}\n")
                if len(match.prayer_contexts) > 10:
                    f.write(f"     ... and {len(match.prayer_contexts) - 10} more\n")
                f.write(f"\n")

                # Detailed matches if available
                if match.raw_matches:
                    f.write(f"   Detailed matches ({len(match.raw_matches)}):\n")
                    for j, raw in enumerate(match.raw_matches[:5], 1):
                        f.write(f"     {j}. {raw.canonical_prayer_name or raw.canonical_L3_signpost} ({raw.nusach})\n")
                        liturgy_excerpt = raw.liturgy_context[:100] + "..." if len(raw.liturgy_context) > 100 else raw.liturgy_context
                        f.write(f"        Context: {liturgy_excerpt}\n")
                    if len(match.raw_matches) > 5:
                        f.write(f"     ... and {len(match.raw_matches) - 5} more\n")
                    f.write(f"\n")

                f.write("-" * 70 + "\n\n")

    print(f"\n✓ Analysis complete! Results saved to: {output_file}")
    print(f"  Total phrases found: {len(results)}")
    print(f"  Total occurrences: {sum(r.occurrence_count for r in results)}")
