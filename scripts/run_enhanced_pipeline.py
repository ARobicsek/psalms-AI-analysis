"""
Enhanced Pipeline Runner (Phase 4)

Complete psalm commentary generation pipeline with all enhancements:
1. MacroAnalyst - Structural analysis
2. MicroAnalyst v2 - Discovery-driven research (with enhanced figurative search)
3. SynthesisWriter - Introduction + verse commentary (with enhanced prompts)
4. MasterEditor (GPT-5) - Editorial review and revision to "National Book Award" level
5. Print-Ready Formatting - Final output with Hebrew/English text

Usage:
    python scripts/run_enhanced_pipeline.py PSALM_NUMBER [options]

Example:
    python scripts/run_enhanced_pipeline.py 23 --output-dir output/psalm_23

The script will:
- Generate all intermediate files
- Handle rate limiting with appropriate delays
- Produce final master-edited commentary
- Create print-ready formatted output

Author: Claude (Anthropic)
Date: 2025-10-18
"""

import sys
import os
import time
import argparse
from pathlib import Path
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.macro_analyst import MacroAnalyst
from src.agents.micro_analyst import MicroAnalystV2
from src.agents.synthesis_writer import SynthesisWriter
from src.agents.master_editor import MasterEditor
from src.schemas.analysis_schemas import load_macro_analysis
from src.utils.logger import get_logger


def run_enhanced_pipeline(
    psalm_number: int,
    output_dir: str = "output",
    db_path: str = "database/tanakh.db",
    delay_between_steps: int = 120,
    skip_macro: bool = False,
    skip_micro: bool = False,
    skip_synthesis: bool = False,
    skip_master_edit: bool = False,
    skip_print_ready: bool = False
):
    """
    Run complete enhanced pipeline for a single psalm.

    Args:
        psalm_number: Psalm number (1-150)
        output_dir: Output directory for all files
        db_path: Path to Tanakh database
        delay_between_steps: Seconds to wait between API-heavy steps (for rate limits)
        skip_macro: Skip macro analysis (use existing file)
        skip_micro: Skip micro analysis (use existing file)
        skip_synthesis: Skip synthesis (use existing file)
        skip_master_edit: Skip master editing (use existing file)
        skip_print_ready: Skip print-ready formatting
    """
    logger = get_logger("enhanced_pipeline")
    logger.info(f"=" * 80)
    logger.info(f"ENHANCED PIPELINE - Psalm {psalm_number}")
    logger.info(f"=" * 80)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # File paths
    macro_file = output_path / f"psalm_{psalm_number:03d}_macro.json"
    micro_file = output_path / f"psalm_{psalm_number:03d}_micro_v2.json"
    research_file = output_path / f"psalm_{psalm_number:03d}_research_v2.md"
    synthesis_intro_file = output_path / f"psalm_{psalm_number:03d}_synthesis_intro.md"
    synthesis_verses_file = output_path / f"psalm_{psalm_number:03d}_synthesis_verses.md"
    edited_intro_file = output_path / f"psalm_{psalm_number:03d}_edited_intro.md"
    edited_verses_file = output_path / f"psalm_{psalm_number:03d}_edited_verses.md"
    edited_assessment_file = output_path / f"psalm_{psalm_number:03d}_assessment.md"
    print_ready_file = output_path / f"psalm_{psalm_number:03d}_print_ready.md"

    # =====================================================================
    # STEP 1: Macro Analysis
    # =====================================================================
    if not skip_macro or not macro_file.exists():
        logger.info("\n[STEP 1] Running MacroAnalyst...")
        print(f"\n{'='*80}")
        print(f"STEP 1: Macro Analysis (Structural Thesis)")
        print(f"{'='*80}\n")

        macro_analyst = MacroAnalyst()
        macro_analysis = macro_analyst.analyze_psalm(psalm_number)

        # Save macro analysis
        from src.schemas.analysis_schemas import save_analysis
        save_analysis(macro_analysis, str(macro_file), format="json")

        logger.info(f"✓ Macro analysis saved to {macro_file}")
        print(f"✓ Macro analysis complete: {macro_file}\n")

        # Rate limit delay
        time.sleep(delay_between_steps)
    else:
        logger.info(f"[STEP 1] Skipping macro analysis (using existing {macro_file})")
        print(f"\nSkipping Step 1 (using existing macro analysis)\n")

    # Load macro analysis
    macro_analysis = load_macro_analysis(str(macro_file))

    # =====================================================================
    # STEP 2: Micro Analysis (Enhanced Figurative Search)
    # =====================================================================
    if not skip_micro or not micro_file.exists():
        logger.info("\n[STEP 2] Running MicroAnalyst v2 (with enhanced figurative search)...")
        print(f"\n{'='*80}")
        print(f"STEP 2: Micro Analysis (Discovery + Enhanced Research)")
        print(f"{'='*80}\n")

        micro_analyst = MicroAnalystV2(db_path=db_path)
        micro_analysis, research_bundle = micro_analyst.analyze_psalm(
            psalm_number,
            macro_analysis
        )

        # Save outputs
        from src.schemas.analysis_schemas import save_analysis
        save_analysis(micro_analysis, str(micro_file), format="json")

        with open(research_file, 'w', encoding='utf-8') as f:
            f.write(research_bundle.to_markdown())

        logger.info(f"✓ Micro analysis saved to {micro_file}")
        logger.info(f"✓ Research bundle saved to {research_file}")
        print(f"✓ Micro analysis complete: {micro_file}")
        print(f"✓ Research bundle complete: {research_file}\n")

        # Rate limit delay
        time.sleep(delay_between_steps)
    else:
        logger.info(f"[STEP 2] Skipping micro analysis (using existing {micro_file})")
        print(f"\nSkipping Step 2 (using existing micro analysis)\n")

    # =====================================================================
    # STEP 3: Synthesis (Enhanced Prompts)
    # =====================================================================
    if not skip_synthesis or not synthesis_intro_file.exists():
        logger.info("\n[STEP 3] Running SynthesisWriter (with enhanced prompts)...")
        print(f"\n{'='*80}")
        print(f"STEP 3: Synthesis (Introduction + Verse Commentary)")
        print(f"{'='*80}\n")

        synthesis_writer = SynthesisWriter()
        commentary = synthesis_writer.write_commentary(
            macro_file=macro_file,
            micro_file=micro_file,
            research_file=research_file,
            psalm_number=psalm_number
        )

        # Save outputs
        with open(synthesis_intro_file, 'w', encoding='utf-8') as f:
            f.write(commentary['introduction'])

        with open(synthesis_verses_file, 'w', encoding='utf-8') as f:
            f.write(commentary['verse_commentary'])

        logger.info(f"✓ Introduction saved to {synthesis_intro_file}")
        logger.info(f"✓ Verse commentary saved to {synthesis_verses_file}")
        print(f"✓ Introduction complete: {synthesis_intro_file}")
        print(f"✓ Verse commentary complete: {synthesis_verses_file}\n")

        # Rate limit delay
        time.sleep(delay_between_steps)
    else:
        logger.info(f"[STEP 3] Skipping synthesis (using existing {synthesis_intro_file})")
        print(f"\nSkipping Step 3 (using existing synthesis)\n")

    # =====================================================================
    # STEP 4: Master Editor (GPT-5) - NEW!
    # =====================================================================
    if not skip_master_edit or not edited_intro_file.exists():
        logger.info("\n[STEP 4] Running MasterEditor (GPT-5) for final editorial review...")
        print(f"\n{'='*80}")
        print(f"STEP 4: Master Editorial Review (GPT-5)")
        print(f"{'='*80}\n")
        print("This step uses GPT-5 to elevate the commentary from 'good' to 'excellent'")
        print("Expected duration: 2-5 minutes\n")

        master_editor = MasterEditor()
        result = master_editor.edit_commentary(
            introduction_file=synthesis_intro_file,
            verse_file=synthesis_verses_file,
            research_file=research_file,
            macro_file=macro_file,
            micro_file=micro_file,
            psalm_number=psalm_number
        )

        # Save outputs
        with open(edited_assessment_file, 'w', encoding='utf-8') as f:
            f.write(f"# Editorial Assessment - Psalm {psalm_number}\n\n")
            f.write(result['assessment'])

        with open(edited_intro_file, 'w', encoding='utf-8') as f:
            f.write(result['revised_introduction'])

        with open(edited_verses_file, 'w', encoding='utf-8') as f:
            f.write(result['revised_verses'])

        logger.info(f"✓ Editorial assessment saved to {edited_assessment_file}")
        logger.info(f"✓ Revised introduction saved to {edited_intro_file}")
        logger.info(f"✓ Revised verses saved to {edited_verses_file}")
        print(f"✓ Editorial assessment: {edited_assessment_file}")
        print(f"✓ Revised introduction: {edited_intro_file}")
        print(f"✓ Revised verses: {edited_verses_file}\n")

        # Rate limit delay
        time.sleep(delay_between_steps)
    else:
        logger.info(f"[STEP 4] Skipping master edit (using existing {edited_intro_file})")
        print(f"\nSkipping Step 4 (using existing master-edited files)\n")

    # =====================================================================
    # STEP 5: Print-Ready Formatting
    # =====================================================================
    if not skip_print_ready:
        logger.info("\n[STEP 5] Creating print-ready formatted output...")
        print(f"\n{'='*80}")
        print(f"STEP 5: Print-Ready Formatting")
        print(f"{'='*80}\n")

        # Call the print-ready script with master-edited files
        # Note: The script expects files named psalm_NNN_synthesis_intro.md and psalm_NNN_synthesis_verses.md
        # So we need to temporarily rename our edited files or modify the formatter call

        # Direct Python call instead of subprocess to avoid file naming issues
        from src.utils.commentary_formatter import CommentaryFormatter

        formatter = CommentaryFormatter(logger=logger)

        try:
            formatter.format_from_files(
                intro_file=str(edited_intro_file),
                verses_file=str(edited_verses_file),
                psalm_number=psalm_number,
                output_file=str(print_ready_file),
                apply_divine_names=True
            )
            result_success = True
        except Exception as e:
            logger.error(f"Error creating print-ready commentary: {e}")
            result_success = False

        if result_success:
            logger.info(f"✓ Print-ready commentary saved to {print_ready_file}")
            print(f"✓ Print-ready commentary: {print_ready_file}\n")
        else:
            print(f"⚠ Error in print-ready formatting (see logs)\n")
    else:
        logger.info(f"[STEP 5] Skipping print-ready formatting")
        print(f"\nSkipping Step 5 (print-ready formatting)\n")

    # =====================================================================
    # COMPLETE
    # =====================================================================
    logger.info(f"\n{'=' * 80}")
    logger.info(f"ENHANCED PIPELINE COMPLETE - Psalm {psalm_number}")
    logger.info(f"{'=' * 80}\n")

    print(f"\n{'='*80}")
    print(f"ENHANCED PIPELINE COMPLETE")
    print(f"{'='*80}\n")
    print(f"Final Output: {print_ready_file}")
    print(f"\nAll files saved to: {output_path}/\n")

    return {
        'macro': macro_file,
        'micro': micro_file,
        'research': research_file,
        'synthesis_intro': synthesis_intro_file,
        'synthesis_verses': synthesis_verses_file,
        'edited_assessment': edited_assessment_file,
        'edited_intro': edited_intro_file,
        'edited_verses': edited_verses_file,
        'print_ready': print_ready_file
    }


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description='Run enhanced commentary generation pipeline (Phase 4)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate complete commentary for Psalm 23
  python scripts/run_enhanced_pipeline.py 23

  # Custom output directory
  python scripts/run_enhanced_pipeline.py 51 --output-dir output/psalm_51

  # Resume from synthesis step (skip macro and micro)
  python scripts/run_enhanced_pipeline.py 1 --skip-macro --skip-micro

  # Skip master editing (use existing synthesis)
  python scripts/run_enhanced_pipeline.py 2 --skip-master-edit
        """
    )

    parser.add_argument('psalm_number', type=int,
                       help='Psalm number (1-150)')
    parser.add_argument('--output-dir', type=str,
                       default=None,
                       help='Output directory (default: output/test_psalm_NNN)')
    parser.add_argument('--db-path', type=str,
                       default='database/tanakh.db',
                       help='Database path (default: database/tanakh.db)')
    parser.add_argument('--delay', type=int,
                       default=120,
                       help='Delay between API-heavy steps in seconds (default: 120)')
    parser.add_argument('--skip-macro', action='store_true',
                       help='Skip macro analysis (use existing file)')
    parser.add_argument('--skip-micro', action='store_true',
                       help='Skip micro analysis (use existing file)')
    parser.add_argument('--skip-synthesis', action='store_true',
                       help='Skip synthesis (use existing file)')
    parser.add_argument('--skip-master-edit', action='store_true',
                       help='Skip master editing (use existing file)')
    parser.add_argument('--skip-print-ready', action='store_true',
                       help='Skip print-ready formatting')

    args = parser.parse_args()

    # Set output directory
    if not args.output_dir:
        args.output_dir = f"output/test_psalm_{args.psalm_number}"

    # Ensure UTF-8 encoding on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    try:
        print(f"\n{'='*80}")
        print(f"ENHANCED COMMENTARY PIPELINE - Psalm {args.psalm_number}")
        print(f"{'='*80}\n")
        print(f"Output Directory: {args.output_dir}")
        print(f"Database: {args.db_path}")
        print(f"Rate Limit Delay: {args.delay} seconds\n")

        result = run_enhanced_pipeline(
            psalm_number=args.psalm_number,
            output_dir=args.output_dir,
            db_path=args.db_path,
            delay_between_steps=args.delay,
            skip_macro=args.skip_macro,
            skip_micro=args.skip_micro,
            skip_synthesis=args.skip_synthesis,
            skip_master_edit=args.skip_master_edit,
            skip_print_ready=args.skip_print_ready
        )

        return 0

    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n\nError in pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
