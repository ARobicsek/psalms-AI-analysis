"""
Helper script to run synthesis with delay between intro and verse commentary
to avoid rate limit issues (30K tokens/minute limit).
"""

import sys
import time
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
        description='Run synthesis with rate-limit-friendly delays'
    )
    parser.add_argument('--macro', type=str, required=True)
    parser.add_argument('--micro', type=str, required=True)
    parser.add_argument('--research', type=str, required=True)
    parser.add_argument('--output-dir', type=str, default='output')
    parser.add_argument('--output-name', type=str, default=None)
    parser.add_argument('--delay', type=int, default=75,
                       help='Seconds to wait between intro and verse calls (default: 75)')

    args = parser.parse_args()

    # Initialize writer
    writer = SynthesisWriter()
    logger = get_logger("synthesis_with_delay")

    print("=" * 80)
    print("SYNTHESIS WRITER WITH RATE-LIMIT DELAYS")
    print("=" * 80)
    print()
    print(f"Macro:    {args.macro}")
    print(f"Micro:    {args.micro}")
    print(f"Research: {args.research}")
    print(f"Delay:    {args.delay} seconds between calls")
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

    # STEP 1: Generate introduction
    print("-" * 80)
    print("STEP 1: Generating Introduction Essay...")
    print("-" * 80)
    introduction = writer._generate_introduction(
        psalm_number=psalm_number,
        macro_analysis=macro_analysis,
        micro_analysis=micro_analysis,
        research_bundle=research_bundle,
        max_tokens=4000
    )

    # Save introduction immediately
    intro_path = output_path / f"{output_name}_intro.md"
    intro_path.write_text(introduction, encoding='utf-8')
    logger.info(f"✓ Introduction saved: {intro_path}")
    print(f"✓ Introduction complete: {len(introduction)} chars")
    print()

    # STEP 2: Wait for rate limit
    print("-" * 80)
    print(f"STEP 2: Waiting {args.delay} seconds for rate limit reset...")
    print("-" * 80)
    for i in range(args.delay, 0, -5):
        print(f"  {i} seconds remaining...", end='\r')
        time.sleep(5)
    print("  Ready!                   ")
    print()

    # STEP 3: Generate verse commentary (now with introduction context)
    print("-" * 80)
    print("STEP 3: Generating Verse Commentary (with introduction context)...")
    print("-" * 80)
    verse_commentary = writer._generate_verse_commentary(
        psalm_number=psalm_number,
        macro_analysis=macro_analysis,
        micro_analysis=micro_analysis,
        research_bundle=research_bundle,
        max_tokens=16000,
        introduction_essay=introduction  # Pass the introduction for context
    )

    # Save verse commentary
    verse_path = output_path / f"{output_name}_verses.md"
    verse_path.write_text(verse_commentary, encoding='utf-8')
    logger.info(f"✓ Verse commentary saved: {verse_path}")
    print(f"✓ Verse commentary complete: {len(verse_commentary)} chars")
    print()

    # STEP 4: Save combined file
    print("-" * 80)
    print("STEP 4: Creating Combined Commentary...")
    print("-" * 80)
    full_path = output_path / f"{output_name}.md"
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(f"# Commentary on Psalm {psalm_number}\n\n")
        f.write("## Introduction\n\n")
        f.write(introduction)
        f.write("\n\n---\n\n")
        f.write("## Verse-by-Verse Commentary\n\n")
        f.write(verse_commentary)

    logger.info(f"✓ Complete commentary saved: {full_path}")
    print(f"✓ Complete commentary saved: {full_path}")
    print()

    print("=" * 80)
    print("SUCCESS!")
    print("=" * 80)
    print()
    print("Preview:")
    print(introduction[:300] + "...")
    print()

    return 0

if __name__ == '__main__':
    sys.exit(main())
