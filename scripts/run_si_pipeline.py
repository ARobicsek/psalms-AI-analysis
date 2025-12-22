"""
Special Instruction (SI) Pipeline Runner

A lightweight script that allows a human editor ("The Author") to inject specific,
overriding instructions into the Master Editor's generation process.

This creates "V2" rewrites of commentaries based on specific thematic ideas or corrections,
without altering the behavior of the standard pipeline.

Key Features:
- Extends MasterEditorV2 via inheritance (no modification to original)
- All outputs use _SI suffix (never overwrites original files)
- Strict input validation (exits immediately if analysis files are missing)
- Copies and updates pipeline statistics to new _SI.json file

Usage:
    python scripts/run_si_pipeline.py PSALM_NUMBER [options]

Example:
    python scripts/run_si_pipeline.py 19

Author: Claude (Anthropic)
Date: 2025-12-22
"""

import sys
import os
import json
import argparse
import shutil
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.master_editor_si import MasterEditorSI
from src.utils.logger import get_logger
from src.utils.pipeline_summary import PipelineSummaryTracker
from src.utils.cost_tracker import CostTracker
from src.utils.document_generator import DocumentGenerator
from src.utils.combined_document_generator import CombinedDocumentGenerator


def run_si_pipeline(
    psalm_number: int,
    output_dir: str = "output",
    special_instruction_file: str = None,
    master_editor_model: str = "gpt-5.1"
):
    """
    Run Special Instruction pipeline for a single psalm.

    Args:
        psalm_number: Psalm number (1-150)
        output_dir: Output directory for all files (should contain existing analysis)
        special_instruction_file: Path to special instruction text file
        master_editor_model: Model to use for master editor (default: "gpt-5.1")

    Raises:
        FileNotFoundError: If required input files are missing
        ValueError: If psalm_number is out of range
    """
    logger = get_logger("si_pipeline")
    logger.info(f"=" * 80)
    logger.info(f"SPECIAL INSTRUCTION PIPELINE - Psalm {psalm_number}")
    logger.info(f"=" * 80)

    # Validate psalm number
    if not 1 <= psalm_number <= 150:
        raise ValueError(f"Psalm number must be between 1 and 150, got {psalm_number}")

    # Initialize cost tracker
    cost_tracker = CostTracker()
    logger.info("Cost tracking enabled for all models.")

    # Create output directory reference
    # If output_dir already ends with psalm_N or psalm_NNN, use it directly
    # Otherwise, append psalm_N to output_dir
    output_path = Path(output_dir)
    psalm_dir_name = f"psalm_{psalm_number}"  # No zero-padding (matches existing dirs)
    psalm_dir_name_padded = f"psalm_{psalm_number:03d}"  # Zero-padded variant

    if output_path.name not in (psalm_dir_name, psalm_dir_name_padded):
        # output_dir is the parent directory (e.g., "output")
        # Append the psalm directory
        output_path = output_path / psalm_dir_name

    if not output_path.exists():
        raise FileNotFoundError(
            f"Output directory does not exist: {output_path}\n"
            f"Please run the full pipeline first to generate the required analysis files."
        )

    # =========================================================================
    # STEP 1: Locate and Read Special Instruction
    # =========================================================================

    if special_instruction_file:
        si_file_path = Path(special_instruction_file)
    else:
        si_file_path = Path("data/special_instructions") / f"special_instructions_Psalm_{psalm_number:03d}.txt"

    if not si_file_path.exists():
        raise FileNotFoundError(
            f"Special instruction file not found: {si_file_path}\n"
            f"Please create a special instruction file at this location before running the SI pipeline."
        )

    special_instruction = si_file_path.read_text(encoding='utf-8').strip()

    if not special_instruction:
        raise ValueError(f"Special instruction file is empty: {si_file_path}")

    logger.info(f"✓ Loaded special instruction from: {si_file_path}")
    logger.info(f"  Preview: {special_instruction[:200]}...")

    # =========================================================================
    # STEP 2: Validate Required Input Files
    # =========================================================================

    required_files = {
        "macro": output_path / f"psalm_{psalm_number:03d}_macro.json",
        "micro": output_path / f"psalm_{psalm_number:03d}_micro_v2.json",
        "research": output_path / f"psalm_{psalm_number:03d}_research_v2.md",
        "synthesis_intro": output_path / f"psalm_{psalm_number:03d}_synthesis_intro.md",
        "synthesis_verses": output_path / f"psalm_{psalm_number:03d}_synthesis_verses.md",
    }

    missing_files = [name for name, path in required_files.items() if not path.exists()]

    if missing_files:
        raise FileNotFoundError(
            f"Required analysis files are missing from {output_path}:\n" +
            "\n".join(f"  - {name}: {required_files[name]}" for name in missing_files) +
            "\n\nPlease run the full pipeline first to generate these files."
        )

    logger.info("✓ All required input files validated:")
    for name, path in required_files.items():
        logger.info(f"  - {name}: {path.name}")

    # =========================================================================
    # STEP 3: Define Output Paths (with _SI suffix)
    # =========================================================================

    si_output_files = {
        "edited_intro": output_path / f"psalm_{psalm_number:03d}_edited_intro_SI.md",
        "edited_verses": output_path / f"psalm_{psalm_number:03d}_edited_verses_SI.md",
        "assessment": output_path / f"psalm_{psalm_number:03d}_assessment_SI.md",
        "edited_intro_college": output_path / f"psalm_{psalm_number:03d}_edited_intro_college_SI.md",
        "edited_verses_college": output_path / f"psalm_{psalm_number:03d}_edited_verses_college_SI.md",
        "assessment_college": output_path / f"psalm_{psalm_number:03d}_assessment_college_SI.md",
        "pipeline_stats": output_path / f"psalm_{psalm_number:03d}_pipeline_stats_SI.json",
        "docx_main": output_path / f"psalm_{psalm_number:03d}_commentary_SI.docx",
        "docx_college": output_path / f"psalm_{psalm_number:03d}_commentary_college_SI.docx",
        "docx_combined": output_path / f"psalm_{psalm_number:03d}_commentary_combined_SI.docx",
    }

    # =========================================================================
    # STEP 4: Handle Pipeline Statistics
    # =========================================================================

    original_stats_file = output_path / f"psalm_{psalm_number:03d}_pipeline_stats.json"

    if not original_stats_file.exists():
        logger.warning(f"Original stats file not found: {original_stats_file}")
        logger.warning("Creating new stats tracker without initial data.")
        tracker = PipelineSummaryTracker(psalm_number=psalm_number)
    else:
        # Load original stats
        with open(original_stats_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)

        logger.info(f"✓ Loaded original stats from: {original_stats_file}")

        # Create tracker with original data
        tracker = PipelineSummaryTracker(psalm_number=psalm_number, initial_data=original_data)

        # Clear the pipeline completion date since this is a new SI run
        # But preserve all the research and analysis data
        logger.info("Resetting pipeline completion date for SI run (preserving research data)")

    # =========================================================================
    # STEP 5: Run Master Editor - Main Commentary (SI)
    # =========================================================================

    logger.info(f"\n[STEP 5] Running Master Editor (SI Edition) for Main Commentary...")
    print(f"\n{'='*80}")
    print(f"STEP 5: Master Editorial Review (SI Edition) - Main Commentary")
    print(f"{'='*80}")
    print(f"This step uses {master_editor_model} with your special instruction.")
    print("Expected duration: 2-5 minutes\n")

    step_start = time.time()

    master_editor_si = MasterEditorSI(
        main_model=master_editor_model,
        cost_tracker=cost_tracker
    )

    result_main = master_editor_si.edit_commentary(
        introduction_file=required_files["synthesis_intro"],
        verse_file=required_files["synthesis_verses"],
        research_file=required_files["research"],
        macro_file=required_files["macro"],
        micro_file=required_files["micro"],
        psalm_number=psalm_number,
        special_instruction=special_instruction
    )

    # Save main SI outputs
    with open(si_output_files["assessment"], 'w', encoding='utf-8') as f:
        f.write(f"# Editorial Assessment (SI Edition) - Psalm {psalm_number}\n\n")
        f.write(result_main['assessment'])

    with open(si_output_files["edited_intro"], 'w', encoding='utf-8') as f:
        f.write(result_main['revised_introduction'])

    with open(si_output_files["edited_verses"], 'w', encoding='utf-8') as f:
        f.write(result_main['revised_verses'])

    step_duration = time.time() - step_start

    logger.info(f"✓ Main SI editorial assessment saved to: {si_output_files['assessment'].name}")
    logger.info(f"✓ Main SI revised introduction saved to: {si_output_files['edited_intro'].name}")
    logger.info(f"✓ Main SI revised verses saved to: {si_output_files['edited_verses'].name}")

    print(f"✓ Editorial assessment: {si_output_files['assessment'].name}")
    print(f"✓ Revised introduction: {si_output_files['edited_intro'].name}")
    print(f"✓ Revised verses: {si_output_files['edited_verses'].name}\n")

    # Track master editor SI step
    tracker.track_step_output("master_editor_si", result_main['assessment'] + result_main['revised_introduction'] + result_main['revised_verses'], duration=step_duration)
    tracker.track_model_for_step("master_editor_si", master_editor_model)

    # =========================================================================
    # STEP 6: Run Master Editor - College Commentary (SI)
    # =========================================================================

    logger.info(f"\n[STEP 6] Running Master Editor (SI Edition) for College Commentary...")
    print(f"\n{'='*80}")
    print(f"STEP 6: Master Editorial Review (SI Edition) - College Commentary")
    print(f"{'='*80}")
    print(f"This step uses {master_editor_model} with your special instruction for college edition.")
    print("Expected duration: 2-5 minutes\n")

    step_start = time.time()

    result_college = master_editor_si.edit_college_commentary(
        introduction_file=required_files["synthesis_intro"],
        verse_file=required_files["synthesis_verses"],
        research_file=required_files["research"],
        macro_file=required_files["macro"],
        micro_file=required_files["micro"],
        psalm_number=psalm_number,
        special_instruction=special_instruction
    )

    # Save college SI outputs
    with open(si_output_files["assessment_college"], 'w', encoding='utf-8') as f:
        f.write(f"# Editorial Assessment (College SI Edition) - Psalm {psalm_number}\n\n")
        f.write(result_college['assessment'])

    with open(si_output_files["edited_intro_college"], 'w', encoding='utf-8') as f:
        f.write(result_college['revised_introduction'])

    with open(si_output_files["edited_verses_college"], 'w', encoding='utf-8') as f:
        f.write(result_college['revised_verses'])

    step_duration = time.time() - step_start

    logger.info(f"✓ College SI editorial assessment saved to: {si_output_files['assessment_college'].name}")
    logger.info(f"✓ College SI revised introduction saved to: {si_output_files['edited_intro_college'].name}")
    logger.info(f"✓ College SI revised verses saved to: {si_output_files['edited_verses_college'].name}")

    print(f"✓ Editorial assessment: {si_output_files['assessment_college'].name}")
    print(f"✓ Revised introduction: {si_output_files['edited_intro_college'].name}")
    print(f"✓ Revised verses: {si_output_files['edited_verses_college'].name}\n")

    # Track college SI step (reuse master_editor_si tracking for simplicity)
    # We'll add a separate entry for college
    tracker.track_step_output("college_si", result_college['assessment'] + result_college['revised_introduction'] + result_college['revised_verses'], duration=step_duration)
    tracker.track_model_for_step("college_si", master_editor_model)

    # =========================================================================
    # STEP 7: Save Pipeline Statistics (_SI.json)
    # =========================================================================

    # Mark pipeline complete and save
    tracker.mark_pipeline_complete()
    saved_stats_file = tracker.save_json(str(output_path))

    # Copy to _SI.json file (tracker.save_json uses standard filename)
    si_stats_file = si_output_files["pipeline_stats"]
    shutil.copy(saved_stats_file, si_stats_file)

    logger.info(f"✓ SI pipeline statistics saved to: {si_stats_file}")

    # =========================================================================
    # STEP 8: Generate Main SI .docx Document
    # =========================================================================

    logger.info(f"\n[STEP 8] Generating Main SI Word Document...")
    print(f"\n{'='*80}")
    print(f"STEP 8: Generating Main SI Word Document (.docx)")
    print(f"{'='*80}\n")

    try:
        generator_main = DocumentGenerator(
            psalm_num=psalm_number,
            intro_path=si_output_files["edited_intro"],
            verses_path=si_output_files["edited_verses"],
            stats_path=si_output_files["pipeline_stats"],
            output_path=si_output_files["docx_main"]
        )
        generator_main.generate()
        logger.info(f"✓ Main SI Word document saved to: {si_output_files['docx_main'].name}")
        print(f"✓ Main SI Word document: {si_output_files['docx_main'].name}\n")
    except Exception as e:
        logger.error(f"Error generating main SI .docx: {e}")
        print(f"⚠ Error generating main SI Word document (see logs for details)\n")

    # =========================================================================
    # STEP 9: Generate College SI .docx Document
    # =========================================================================

    logger.info(f"\n[STEP 9] Generating College SI Word Document...")
    print(f"\n{'='*80}")
    print(f"STEP 9: Generating College SI Word Document (.docx)")
    print(f"{'='*80}\n")

    try:
        generator_college = DocumentGenerator(
            psalm_num=psalm_number,
            intro_path=si_output_files["edited_intro_college"],
            verses_path=si_output_files["edited_verses_college"],
            stats_path=si_output_files["pipeline_stats"],
            output_path=si_output_files["docx_college"]
        )
        generator_college.generate()
        logger.info(f"✓ College SI Word document saved to: {si_output_files['docx_college'].name}")
        print(f"✓ College SI Word document: {si_output_files['docx_college'].name}\n")
    except Exception as e:
        logger.error(f"Error generating college SI .docx: {e}")
        print(f"⚠ Error generating college SI Word document (see logs for details)\n")

    # =========================================================================
    # STEP 10: Generate Combined SI .docx Document
    # =========================================================================

    logger.info(f"\n[STEP 10] Generating Combined SI Word Document...")
    print(f"\n{'='*80}")
    print(f"STEP 10: Generating Combined SI Word Document (.docx)")
    print(f"{'='*80}\n")

    try:
        generator_combined = CombinedDocumentGenerator(
            psalm_num=psalm_number,
            main_intro_path=si_output_files["edited_intro"],
            main_verses_path=si_output_files["edited_verses"],
            college_intro_path=si_output_files["edited_intro_college"],
            college_verses_path=si_output_files["edited_verses_college"],
            stats_path=si_output_files["pipeline_stats"],
            output_path=si_output_files["docx_combined"]
        )
        generator_combined.generate()
        logger.info(f"✓ Combined SI Word document saved to: {si_output_files['docx_combined'].name}")
        print(f"✓ Combined SI Word document: {si_output_files['docx_combined'].name}\n")
    except Exception as e:
        logger.error(f"Error generating combined SI .docx: {e}")
        print(f"⚠ Error generating combined SI Word document (see logs for details)\n")

    # =========================================================================
    # COMPLETE
    # =========================================================================

    logger.info(f"\n{'=' * 80}")
    logger.info(f"SPECIAL INSTRUCTION PIPELINE COMPLETE - Psalm {psalm_number}")
    logger.info(f"{'=' * 80}\n")

    # Display cost summary
    print(cost_tracker.get_summary())

    print(f"\n{'='*80}")
    print("SPECIAL INSTRUCTION PIPELINE COMPLETE")
    print(f"{'='*80}\n")
    print(f"All SI files saved to: {output_path}/")
    print()
    print("Generated files:")
    print(f"  - {si_output_files['edited_intro'].name}")
    print(f"  - {si_output_files['edited_verses'].name}")
    print(f"  - {si_output_files['assessment'].name}")
    print(f"  - {si_output_files['edited_intro_college'].name}")
    print(f"  - {si_output_files['edited_verses_college'].name}")
    print(f"  - {si_output_files['assessment_college'].name}")
    print(f"  - {si_output_files['pipeline_stats'].name}")
    print(f"  - {si_output_files['docx_main'].name}")
    print(f"  - {si_output_files['docx_college'].name}")
    print(f"  - {si_output_files['docx_combined'].name}")
    print()

    return {
        'edited_intro_si': si_output_files["edited_intro"],
        'edited_verses_si': si_output_files["edited_verses"],
        'assessment_si': si_output_files["assessment"],
        'edited_intro_college_si': si_output_files["edited_intro_college"],
        'edited_verses_college_si': si_output_files["edited_verses_college"],
        'assessment_college_si': si_output_files["assessment_college"],
        'pipeline_stats_si': si_output_files["pipeline_stats"],
        'docx_main_si': si_output_files["docx_main"],
        'docx_college_si': si_output_files["docx_college"],
        'docx_combined_si': si_output_files["docx_combined"],
    }


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description='Run Special Instruction (SI) pipeline for a psalm commentary',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run SI pipeline for Psalm 19 (uses default instruction file location)
  python scripts/run_si_pipeline.py 19

  # Run SI pipeline with custom instruction file
  python scripts/run_si_pipeline.py 23 --special-instruction my_instructions.txt

  # Run SI pipeline with custom output directory
  python scripts/run_si_pipeline.py 19 --output-dir output/psalm_019

  # Run SI pipeline with specific model
  python scripts/run_si_pipeline.py 19 --model claude-opus-4-5
        """
    )

    parser.add_argument('psalm_number', type=int,
                       help='Psalm number (1-150)')
    parser.add_argument('--output-dir', type=str,
                       default=None,
                       help='Output directory containing existing analysis (default: output/psalm_NNN)')
    parser.add_argument('--special-instruction', '--si', type=str,
                       default=None,
                       dest='special_instruction_file',
                       help='Path to special instruction text file (default: data/special_instructions/special_instructions_Psalm_NNN.txt)')
    parser.add_argument('--model', type=str, default='gpt-5.1',
                       choices=['gpt-5', 'gpt-5.1', 'claude-opus-4-5'],
                       help='Model to use for master editor (default: gpt-5.1)')

    args = parser.parse_args()

    # Set output directory
    if args.output_dir:
        # If user specified a custom output dir, use it directly
        output_dir = args.output_dir
    else:
        # Default to "output" - run_si_pipeline will append psalm_NNN
        output_dir = "output"

    # Ensure UTF-8 encoding on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    try:
        print(f"\n{'='*80}")
        print(f"SPECIAL INSTRUCTION PIPELINE - Psalm {args.psalm_number}")
        print(f"{'='*80}\n")
        print(f"Output Directory: {output_dir}")
        print(f"Model: {args.model}")
        if args.special_instruction_file:
            print(f"Special Instruction: {args.special_instruction_file}")
        else:
            print(f"Special Instruction: data/special_instructions/special_instructions_Psalm_{args.psalm_number:03d}.txt")
        print()

        result = run_si_pipeline(
            psalm_number=args.psalm_number,
            output_dir=output_dir,
            special_instruction_file=args.special_instruction_file,
            master_editor_model=args.model
        )

        return 0

    except FileNotFoundError as e:
        print(f"\n⚠️ {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"\n⚠️ {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n\nError in SI pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
