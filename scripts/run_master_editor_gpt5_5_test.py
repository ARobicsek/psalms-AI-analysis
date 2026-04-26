"""
Test script for running the new GPT-5.5 Pro model as Master Editor.

This script uses the existing research bundle from a previous pipeline run
to avoid regenerating macro, micro, and research outputs.
It outputs to a segregated test directory so production outputs are not overwritten.

Usage:
    python scripts/run_master_editor_gpt5_5_test.py PSALM_NUMBER

Example:
    python scripts/run_master_editor_gpt5_5_test.py 51
"""

import sys
import argparse
import time
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.master_editor import MasterEditor
from src.agents.copy_editor import CopyEditor
from src.utils.commentary_formatter import CommentaryFormatter
from src.utils.logger import get_logger
from src.utils.cost_tracker import CostTracker
from src.utils.combined_document_generator import CombinedDocumentGenerator

def main():
    parser = argparse.ArgumentParser(description="Test GPT-5.5 Pro as Master Editor")
    parser.add_argument("psalm", type=int, help="Psalm number to process")
    args = parser.parse_args()
    
    psalm_number = args.psalm
    logger = get_logger("gpt5_5_test")
    cost_tracker = CostTracker()
    
    # Input files from production output
    prod_output_path = Path(f"output/psalm_{psalm_number}")
    macro_file = prod_output_path / f"psalm_{psalm_number:03d}_macro.json"
    micro_file = prod_output_path / f"psalm_{psalm_number:03d}_micro_v2.json"
    research_file = prod_output_path / f"psalm_{psalm_number:03d}_research_v2.md"
    insights_file = prod_output_path / f"psalm_{psalm_number:03d}_insights.json"
    reader_questions_file = prod_output_path / f"psalm_{psalm_number:03d}_reader_questions.json"
    
    # Validate inputs exist
    for f in [macro_file, micro_file, research_file]:
        if not f.exists():
            logger.error(f"Required input file missing: {f}")
            logger.error("Please run the standard pipeline first up to the research phase.")
            return 1
            
    # Output files in test directory
    test_output_path = Path(f"output/test_gpt5_5_psalm_{psalm_number:03d}")
    test_output_path.mkdir(parents=True, exist_ok=True)
    
    edited_intro_file = test_output_path / f"psalm_{psalm_number:03d}_edited_intro.md"
    edited_verses_file = test_output_path / f"psalm_{psalm_number:03d}_edited_verses.md"
    edited_assessment_file = test_output_path / f"psalm_{psalm_number:03d}_assessment.md"
    print_ready_file = test_output_path / f"psalm_{psalm_number:03d}_print_ready.md"
    docx_output_file = test_output_path / f"psalm_{psalm_number:03d}_commentary.docx"
    
    logger.info(f"========== TESTING GPT-5.5 PRO ON PSALM {psalm_number} ==========")
    logger.info(f"Using inputs from: {prod_output_path}")
    logger.info(f"Saving outputs to: {test_output_path}")
    
    # 1. Run Master Editor
    logger.info("--- Step 1: Master Editor ---")
    step_start = time.time()
    
    master_editor = MasterEditor(
        main_model="gpt-5.5-pro",
        cost_tracker=cost_tracker
    )
    
    try:
        response_file = Path(f"output/debug/master_writer_v4_response_psalm_{psalm_number}.txt")
        if response_file.exists():
            logger.info("Using cached API response text...")
            response_text = response_file.read_text(encoding='utf-8')
            result = master_editor._parse_writer_response(response_text, psalm_number)
        else:
            logger.info("No cached response found, calling API...")
            result = master_editor.write_commentary(
                macro_file=macro_file,
                micro_file=micro_file,
                research_file=research_file,
                insights_file=insights_file if insights_file.exists() else None,
                psalm_number=psalm_number,
                reader_questions_file=reader_questions_file if reader_questions_file.exists() else None,
                suppress_questions=False
            )
    except Exception as e:
        logger.error(f"Master Editor failed: {e}")
        return 1
        
    with open(edited_assessment_file, 'w', encoding='utf-8') as f:
        f.write(f"# Editorial Assessment - Psalm {psalm_number}\n\n")
        f.write(result.get('assessment', 'No separate assessment provided by V4 prompt.'))
    with open(edited_intro_file, 'w', encoding='utf-8') as f:
        f.write(result.get('introduction', ''))
    with open(edited_verses_file, 'w', encoding='utf-8') as f:
        f.write(result.get('verse_commentary', ''))
        
    logger.info(f"Master Editor completed in {time.time() - step_start:.1f}s")
    
    # 2. Formatter
    logger.info("--- Step 2: Formatter ---")
    formatter = CommentaryFormatter()
    
    summary_file = prod_output_path / f"psalm_{psalm_number:03d}_pipeline_stats.json"
    with open(summary_file, 'r', encoding='utf-8') as f:
        summary_data = json.load(f)
        
    from src.data_sources.tanakh_database import TanakhDatabase
    db = TanakhDatabase(Path("database/tanakh.db"))
    psalm_data = db.get_psalm(psalm_number)
    psalm_text_data = {v.verse: {'hebrew': v.hebrew, 'english': v.english} for v in psalm_data.verses}
        
    formatted_commentary = formatter.format_commentary(
        psalm_num=psalm_number,
        intro_text=result.get('introduction', ''),
        verses_text=result.get('verse_commentary', ''),
        summary_data=summary_data,
        psalm_text_data=psalm_text_data
    )
    with open(print_ready_file, 'w', encoding='utf-8') as f:
        f.write(formatted_commentary)
        
    # 3. Copy Editor
    logger.info("--- Step 3: Copy Editor ---")
    copy_editor = CopyEditor(model="gpt-5.5-pro", logger=logger)
    try:
        copy_edit_result = copy_editor.edit_commentary(
            psalm_number=psalm_number,
            input_file=print_ready_file,
            output_dir=test_output_path
        )
        final_md_file = Path(copy_edit_result['edited_file'])
    except Exception as e:
        logger.error(f"Copy Editor failed: {e}")
        logger.info("Falling back to pre-copy-edit file for docx generation")
        final_md_file = print_ready_file

    # 4. DOCX Generator
    logger.info("--- Step 4: DOCX Generation ---")
    from src.utils.document_generator import DocumentGenerator
    doc_gen = DocumentGenerator(
        psalm_num=psalm_number,
        intro_path=edited_intro_file,
        verses_path=final_md_file,
        stats_path=summary_file,
        output_path=docx_output_file
    )
    doc_gen.generate()
    logger.info(f"DOCX generated at {docx_output_file}")
    
    # Cost tracking printout
    logger.info("========== COST SUMMARY ==========")
    for model, usage in cost_tracker.usage.items():
        logger.info(f"Model: {model}")
        logger.info(f"  Input Tokens:  {usage['input']:,}")
        logger.info(f"  Output Tokens: {usage['output']:,}")
        logger.info(f"  Thinking Tokens: {usage.get('thinking', 0):,}")
        logger.info(f"  Cost: ${usage['cost']:.4f}")
    
    logger.info(f"Total Cost: ${cost_tracker.get_total_cost():.4f}")

if __name__ == '__main__':
    sys.exit(main())
