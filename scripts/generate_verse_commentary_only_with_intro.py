"""
Generate verse commentary only, using existing introduction essay.
This allows the verse commentator to see the introduction essay.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.synthesis_writer import SynthesisWriter
from src.utils.logger import get_logger

def main():
    import argparse

    # Ensure UTF-8 encoding for output
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Generate verse commentary with access to introduction essay'
    )
    parser.add_argument('--macro', type=str, required=True,
                       help='Path to macro analysis JSON')
    parser.add_argument('--micro', type=str, required=True,
                       help='Path to micro analysis JSON')
    parser.add_argument('--research', type=str, required=True,
                       help='Path to research bundle markdown')
    parser.add_argument('--introduction', type=str, required=True,
                       help='Path to existing introduction essay')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Output directory')
    parser.add_argument('--output-name', type=str, default=None,
                       help='Base name for output files')

    args = parser.parse_args()

    # Initialize writer
    writer = SynthesisWriter()
    logger = get_logger("verse_only")

    print("=" * 80)
    print("VERSE COMMENTARY GENERATOR (with Introduction Context)")
    print("=" * 80)
    print()
    print(f"Macro:        {args.macro}")
    print(f"Micro:        {args.micro}")
    print(f"Research:     {args.research}")
    print(f"Introduction: {args.introduction}")
    print()

    # Load files
    logger.info("Loading input files...")
    macro_analysis = writer._load_macro_analysis(Path(args.macro))
    micro_analysis = writer._load_micro_analysis(Path(args.micro))
    research_bundle = writer._load_research_bundle(Path(args.research))

    # Load existing introduction
    intro_path = Path(args.introduction)
    introduction = intro_path.read_text(encoding='utf-8')
    logger.info(f"Loaded introduction: {len(introduction)} chars")

    psalm_number = macro_analysis.get('psalm_number', 0)
    logger.info(f"Processing Psalm {psalm_number}")

    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    output_name = args.output_name or f"psalm_{psalm_number:03d}_commentary"

    # Generate verse commentary
    print("-" * 80)
    print("Generating Verse Commentary (with introduction context)...")
    print("-" * 80)
    verse_commentary = writer._generate_verse_commentary(
        psalm_number=psalm_number,
        macro_analysis=macro_analysis,
        micro_analysis=micro_analysis,
        research_bundle=research_bundle,
        max_tokens=16000,
        introduction_essay=introduction
    )

    # Save verse commentary
    verse_path = output_path / f"{output_name}_verses.md"
    verse_path.write_text(verse_commentary, encoding='utf-8')
    logger.info(f"Verse commentary saved: {verse_path}")
    print(f"✓ Verse commentary complete: {len(verse_commentary)} chars")
    print(f"✓ Saved to: {verse_path}")
    print()

    print("=" * 80)
    print("SUCCESS!")
    print("=" * 80)
    print()
    print("Preview:")
    print(verse_commentary[:500] + "...")
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
