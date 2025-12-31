"""
Tribal Blessings Analyzer - Analyze figurative language in Genesis 49

This script uses the TribalCurator to analyze Jacob's tribal blessings,
searching the figurative concordance for similar vehicles and targets,
and generating scholarly insights for each tribe.

Usage:
    python scripts/tribal_blessings_analyzer.py --tribe Judah
    python scripts/tribal_blessings_analyzer.py --all
    python scripts/tribal_blessings_analyzer.py --tribe Judah --verbose
    python scripts/tribal_blessings_analyzer.py --all --dry-run

Author: Claude Code
Date: 2025-12-30
"""

import argparse
import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding for Hebrew output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

from src.agents.tribal_curator import (
    TribalCurator,
    GENESIS_49_CONFIG,
    SegmentAnalysisOutput,
    FullAnalysisOutput
)


def format_segment_output(output: SegmentAnalysisOutput) -> str:
    """Format a single segment's analysis as markdown."""
    lines = []

    lines.append(f"# {output.segment_name}")
    lines.append(f"\n**Genesis 49:{min(output.verses)}-{max(output.verses)}**\n")

    # Source text
    lines.append("## The Blessing Text\n")
    lines.append("**Hebrew:**")
    lines.append(f"```")
    lines.append(output.source_text_hebrew)
    lines.append(f"```\n")
    lines.append("**English:**")
    lines.append(f"> {output.source_text_english.replace(chr(10), chr(10) + '> ')}\n")

    # Vehicles identified
    if output.vehicles_identified:
        lines.append("## Vehicles Identified\n")
        for v in output.vehicles_identified:
            lines.append(f"- {v}")
        lines.append("")

    # Search results summary
    lines.append("## Search Results Summary\n")
    for term, count in output.vehicle_search_results.items():
        status = "+" if count > 0 else "-"
        lines.append(f"- {status} **{term}**: {count} results")
    lines.append(f"- **{output.segment_name} as target**: {output.target_search_results} results")
    lines.append("")

    # Main insight
    lines.append("## Scholarly Insight\n")
    lines.append(output.insight_text)
    lines.append("")

    # Curated examples
    if output.curated_examples:
        lines.append("## Key Biblical Parallels\n")
        for i, ex in enumerate(output.curated_examples, 1):
            ref = ex.get("reference", "Unknown")
            hebrew = ex.get("hebrew", "")
            english = ex.get("english", "")
            why = ex.get("why_relevant", "")

            lines.append(f"### {i}. {ref}\n")
            if hebrew:
                lines.append(f"**Hebrew:** {hebrew}\n")
            if english:
                lines.append(f"**English:** {english}\n")
            if why:
                lines.append(f"*Relevance:* {why}\n")

    # Tribe as target examples
    if output.tribe_as_target_examples:
        lines.append(f"## {output.segment_name} as Figurative Target Elsewhere\n")
        for i, ex in enumerate(output.tribe_as_target_examples, 1):
            ref = ex.get("reference", "Unknown")
            context = ex.get("context", "")
            hebrew = ex.get("hebrew", "")
            english = ex.get("english", "")
            significance = ex.get("significance", "")

            lines.append(f"### {i}. {ref}\n")
            if context:
                lines.append(f"*Context:* {context}\n")
            if hebrew:
                lines.append(f"**Hebrew:** {hebrew}\n")
            if english:
                lines.append(f"**English:** {english}\n")
            if significance:
                lines.append(f"*Significance:* {significance}\n")

    # Metadata
    lines.append("---\n")
    lines.append("## Analysis Metadata\n")
    lines.append(f"- Iterations: {output.iteration_count}")
    total_tokens = output.token_usage.get('input', 0) + output.token_usage.get('output', 0) + output.token_usage.get('thinking', 0)
    lines.append(f"- Total tokens: {total_tokens:,}")
    lines.append(f"- Cost: ${output.token_usage.get('cost', 0):.4f}")

    return "\n".join(lines)


def format_combined_output(output: FullAnalysisOutput) -> str:
    """Format the complete analysis as a combined markdown document."""
    lines = []

    lines.append(f"# {output.passage_name}")
    lines.append(f"\n**{output.book} {output.chapter}**\n")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

    # Overview
    lines.append("## Overview\n")
    lines.append(f"This document contains figurative language analysis for all {len(output.segments)} tribal blessings in Genesis 49, ")
    lines.append("examining the vehicles (concrete images) used to describe each tribe and finding parallels throughout Scripture.\n")

    # Cost summary
    lines.append("### Cost Summary\n")
    total = output.total_token_usage
    lines.append(f"- Input tokens: {total.get('input', 0):,}")
    lines.append(f"- Output tokens: {total.get('output', 0):,}")
    lines.append(f"- Thinking tokens: {total.get('thinking', 0):,}")
    all_tokens = total.get('input', 0) + total.get('output', 0) + total.get('thinking', 0)
    lines.append(f"- **Total tokens: {all_tokens:,}**")
    lines.append(f"- **Total cost: ${output.total_cost:.4f}**\n")

    # Table of contents
    lines.append("## Table of Contents\n")
    for i, name in enumerate(output.segments.keys(), 1):
        lines.append(f"{i}. [{name}](#{name.lower().replace(' ', '-')})")
    lines.append("\n---\n")

    # Each segment
    for segment_name, segment_output in output.segments.items():
        lines.append(format_segment_output(segment_output))
        lines.append("\n---\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze figurative language in Genesis 49 tribal blessings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/tribal_blessings_analyzer.py --tribe Judah
    python scripts/tribal_blessings_analyzer.py --tribe "Simeon and Levi"
    python scripts/tribal_blessings_analyzer.py --all
    python scripts/tribal_blessings_analyzer.py --all --verbose
    python scripts/tribal_blessings_analyzer.py --tribe Judah --dry-run
        """
    )

    # What to analyze
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tribe", type=str, help="Analyze a specific tribe")
    group.add_argument("--all", action="store_true", help="Analyze all 12 tribes")
    group.add_argument("--list", action="store_true", help="List available tribes")

    # Options
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed progress")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts without calling LLM")
    parser.add_argument("--output-dir", type=str, help="Output directory (default: output/genesis_49)")
    parser.add_argument("--deep-research", type=str, help="Path to deep research file")

    args = parser.parse_args()

    # List tribes
    if args.list:
        print("\nAvailable tribes in Genesis 49:\n")
        for name, config in GENESIS_49_CONFIG.segments.items():
            verses = f"{min(config.verses)}-{max(config.verses)}"
            print(f"  {name:<20} (verses {verses})")
        print()
        return 0

    # Set output directory
    output_dir = Path(args.output_dir) if args.output_dir else (PROJECT_ROOT / "output" / "genesis_49")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find deep research file
    deep_research_path = None
    if args.deep_research:
        deep_research_path = Path(args.deep_research)
        if not deep_research_path.exists():
            print(f"[WARNING] Specified deep research file not found: {deep_research_path}")
            deep_research_path = None
    else:
        # Check default locations (txt first, then md)
        default_path_txt = PROJECT_ROOT / "data" / "deep_research" / "Genesis_49.txt"
        default_path_md = PROJECT_ROOT / "data" / "deep_research" / "Genesis_49.md"

        if default_path_txt.exists():
            deep_research_path = default_path_txt
        elif default_path_md.exists():
            deep_research_path = default_path_md

    if deep_research_path and deep_research_path.exists():
        file_size = deep_research_path.stat().st_size
        print(f"[INFO] Found deep research file: {deep_research_path} ({file_size:,} bytes)")
    else:
        print(f"[INFO] No deep research file found (checked data/deep_research/Genesis_49.txt and .md)")

    # Initialize curator
    curator = TribalCurator(
        config=GENESIS_49_CONFIG,
        verbose=args.verbose,
        dry_run=args.dry_run,
        deep_research_path=deep_research_path
    )

    print(f"\n{'='*60}")
    print("GENESIS 49 TRIBAL BLESSINGS ANALYZER")
    print(f"{'='*60}")
    print(f"Model: {curator.active_model}")
    print(f"Output: {output_dir}")
    if deep_research_path:
        print(f"Deep research: {deep_research_path}")
    print(f"{'='*60}\n")

    if args.tribe:
        # Analyze single tribe
        tribe_name = args.tribe

        # Validate tribe name
        if tribe_name not in GENESIS_49_CONFIG.segments:
            print(f"Error: Unknown tribe '{tribe_name}'")
            print(f"Use --list to see available tribes")
            return 1

        print(f"Analyzing: {tribe_name}")

        try:
            output = curator.analyze_segment(tribe_name)
        except Exception as e:
            print(f"\nError during analysis: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1

        # Format and save
        formatted = format_segment_output(output)

        safe_name = tribe_name.lower().replace(" ", "_").replace("and_", "")
        output_path = output_dir / f"tribe_{safe_name}.md"
        output_path.write_text(formatted, encoding='utf-8')

        print(f"\nOutput written to: {output_path}")

        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Tribe: {output.segment_name}")
        print(f"Vehicles: {', '.join(output.vehicles_identified)}")
        print(f"Iterations: {output.iteration_count}")
        total_tokens = sum(output.token_usage.get(k, 0) for k in ['input', 'output', 'thinking'])
        print(f"Total tokens: {total_tokens:,}")
        print(f"Cost: ${output.token_usage.get('cost', 0):.4f}")

        if not args.dry_run:
            print(f"\nInsight preview:")
            print("-" * 40)
            preview = output.insight_text[:500] + "..." if len(output.insight_text) > 500 else output.insight_text
            print(preview)

    else:
        # Analyze all tribes
        print(f"Analyzing all {len(GENESIS_49_CONFIG.segments)} tribes...")

        try:
            output = curator.analyze_all()
        except Exception as e:
            print(f"\nError during analysis: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1

        # Save individual files
        for segment_name, segment_output in output.segments.items():
            formatted = format_segment_output(segment_output)
            safe_name = segment_name.lower().replace(" ", "_").replace("and_", "")
            output_path = output_dir / f"tribe_{safe_name}.md"
            output_path.write_text(formatted, encoding='utf-8')
            print(f"  Saved: {output_path.name}")

        # Save combined file
        combined = format_combined_output(output)
        combined_path = output_dir / "tribal_analysis_summary.md"
        combined_path.write_text(combined, encoding='utf-8')
        print(f"\nCombined output: {combined_path}")

        # Save stats
        stats = {
            "generated": datetime.now().isoformat(),
            "passage": output.passage_name,
            "tribes_analyzed": len(output.segments),
            "total_token_usage": output.total_token_usage,
            "total_cost": output.total_cost,
            "segments": {
                name: {
                    "verses": seg.verses,
                    "vehicles": seg.vehicles_identified,
                    "iterations": seg.iteration_count,
                    "tokens": seg.token_usage
                }
                for name, seg in output.segments.items()
            }
        }
        stats_path = output_dir / "analysis_stats.json"
        stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"Stats: {stats_path}")

        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Tribes analyzed: {len(output.segments)}")
        total = output.total_token_usage
        all_tokens = total.get('input', 0) + total.get('output', 0) + total.get('thinking', 0)
        print(f"Total tokens: {all_tokens:,}")
        print(f"Total cost: ${output.total_cost:.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
