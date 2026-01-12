"""
Generate ONLY the verse commentary for a psalm (when intro already exists).
Useful when hitting rate limits.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.synthesis_writer import SynthesisWriter
from src.utils.logger import get_logger

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate only verse commentary (separate from intro)'
    )
    parser.add_argument('--macro', type=str, required=True)
    parser.add_argument('--micro', type=str, required=True)
    parser.add_argument('--research', type=str, required=True)
    parser.add_argument('--output-dir', type=str, default='output')
    parser.add_argument('--output-name', type=str, default=None)

    args = parser.parse_args()

    # Initialize writer
    writer = SynthesisWriter()
    logger = get_logger("verse_commentary_only")

    print("=" * 80)
    print("VERSE COMMENTARY GENERATOR")
    print("=" * 80)
    print()
    print(f"Macro:    {args.macro}")
    print(f"Micro:    {args.micro}")
    print(f"Research: {args.research}")
    print()

    # Load files
    logger.info("Loading input files...")
    macro_analysis = writer._load_macro_analysis(Path(args.macro))
    micro_analysis = writer._load_micro_analysis(Path(args.micro))
    research_bundle = writer._load_research_bundle(Path(args.research))

    psalm_number = macro_analysis.get('psalm_number', 0)
    logger.info(f"Processing Psalm {psalm_number}")

    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    output_name = args.output_name or f"psalm_{psalm_number:03d}_commentary"

    # Generate verse commentary
    print("-" * 80)
    print("Generating Verse Commentary...")
    print("This may take 60-90 seconds...")
    print("-" * 80)

    verse_commentary = writer._generate_verse_commentary(
        psalm_number=psalm_number,
        macro_analysis=macro_analysis,
        micro_analysis=micro_analysis,
        research_bundle=research_bundle,
        max_tokens=16000
    )

    # Save verse commentary
    verse_path = output_path / f"{output_name}_verses.md"
    verse_path.write_text(verse_commentary, encoding='utf-8')
    logger.info(f"✓ Verse commentary saved: {verse_path}")
    print()
    print(f"✓ Verse commentary complete: {len(verse_commentary)} chars")
    print(f"✓ Saved to: {verse_path}")
    print()

    # Show preview
    print("=" * 80)
    print("PREVIEW")
    print("=" * 80)
    lines = verse_commentary.split('\n')
    for line in lines[:30]:
        print(line)
    if len(lines) > 30:
        print(f"\n... ({len(lines) - 30} more lines)")
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
