"""
Quick script to complete the engagement test by running only:
1. College edition (Step 3)
2. Combined DOCX generation (Step 4)

This assumes synthesis and main editor already completed.
"""

import sys
import os
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.master_editor import MasterEditorV2
from src.utils.combined_document_generator import CombinedDocumentGenerator
from src.utils.logger import get_logger
from src.utils.cost_tracker import CostTracker


# Prompt modifications for engagement
QUESTION_REWRITING_INSTRUCTION = """
### STAGE 4: REFINED READER QUESTIONS (NEW)

Based on your full editorial review, generate **4-6 refined "Questions for the Reader"** that will appear BEFORE the commentary.

You have access to the ORIGINAL questions (from early analysis) plus the FULL research bundle (traditional commentaries, reception history, liturgical use, etc.). Use this broader context to craft questions that:

1. **Hook curiosity** — Make readers eager to dig into the text
2. **Set up insights** — Prime readers for the "aha!" moments you discovered in editing  
3. **Include specifics** — Reference specific verses, Hebrew terms, or textual puzzles
4. **Span multiple angles** — Cover language, structure, theology, reception, liturgy

You may keep, rework, or replace the original questions entirely. Your goal is the BEST possible set of reader-priming questions based on everything you now know about this psalm.

**Output format:** After your REVISED VERSE COMMENTARY section, add:

### REFINED READER QUESTIONS
1. [Question 1]
2. [Question 2]
3. [Question 3]
4. [Question 4]
5. [Question 5 - optional]
6. [Question 6 - optional]
"""


def patch_college_prompt(original_prompt: str, reader_questions: str = "") -> str:
    """Patch the college editor prompt with engagement improvements."""
    modified = original_prompt
    
    # Add hook requirement
    hook_line = "- **Opens with a hook related to READER QUESTIONS**—a puzzle or paradox that sets up the questions readers have seen\n"
    if "Create commentary that:" in modified:
        modified = modified.replace(
            "Create commentary that:",
            f"Create commentary that:\n{hook_line}"
        )
    
    # Add reader questions
    if reader_questions:
        modified = modified.replace(
            "### FULL RESEARCH BUNDLE",
            f"### ORIGINAL READER QUESTIONS\n{reader_questions}\n\n### FULL RESEARCH BUNDLE"
        )
    
    # Add question rewriting instruction
    if "## OUTPUT FORMAT" in modified:
        modified = modified.replace(
            "## OUTPUT FORMAT",
            QUESTION_REWRITING_INSTRUCTION + "\n\n## OUTPUT FORMAT"
        )
    
    return modified


def main():
    logger = get_logger("complete_test")
    cost_tracker = CostTracker()
    
    psalm_number = 27
    output_path = Path("output/psalm_27")
    
    # File paths
    synthesis_intro_test = output_path / "psalm_027_synthesis_intro_test.md"
    synthesis_verses_test = output_path / "psalm_027_synthesis_verses_test.md"
    research_file = output_path / "psalm_027_research_v2.md"
    macro_file = output_path / "psalm_027_macro.json"
    micro_file = output_path / "psalm_027_micro_v2.json"
    edited_intro_college_test = output_path / "psalm_027_edited_intro_college_test.md"
    edited_verses_college_test = output_path / "psalm_027_edited_verses_college_test.md"
    reader_questions_file = output_path / "psalm_027_reader_questions.json"
    refined_questions_file = output_path / "psalm_027_reader_questions_test.json"
    edited_intro_test = output_path / "psalm_027_edited_intro_test.md"
    edited_verses_test = output_path / "psalm_027_edited_verses_test.md"
    combined_docx_test = output_path / "psalm_027_commentary_combined_test.docx"
    stats_test_file = output_path / "psalm_027_pipeline_stats_test.json"
    
    # Load reader questions
    reader_questions = ""
    if reader_questions_file.exists():
        with open(reader_questions_file, 'r', encoding='utf-8') as f:
            rq_data = json.load(f)
        questions = rq_data.get('curated_questions', [])
        if questions:
            reader_questions = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
            logger.info(f"Loaded {len(questions)} reader questions")
    
    # Patch prompts at module level
    import src.agents.master_editor as me_module
    original_college_prompt = me_module.COLLEGE_EDITOR_PROMPT_V2
    me_module.COLLEGE_EDITOR_PROMPT_V2 = patch_college_prompt(original_college_prompt, reader_questions)
    logger.info("Applied prompt modifications for college edition")
    
    try:
        # =========================================================================
        # STEP 3: College Edition
        # =========================================================================
        print(f"\n{'='*80}")
        print("COMPLETING TEST - Step 3: College Edition")
        print(f"{'='*80}\n")
        
        master_editor = MasterEditorV2(main_model="gpt-5.1", cost_tracker=cost_tracker)
        
        college_result = master_editor.edit_college_commentary(
            introduction_file=synthesis_intro_test,
            verse_file=synthesis_verses_test,
            research_file=research_file,
            macro_file=macro_file,
            micro_file=micro_file,
            psalm_number=psalm_number
        )
        
        # Save college outputs
        with open(edited_intro_college_test, 'w', encoding='utf-8') as f:
            f.write(college_result['revised_introduction'])
        with open(edited_verses_college_test, 'w', encoding='utf-8') as f:
            f.write(college_result['revised_verses'])
        
        logger.info(f"✓ College intro saved: {edited_intro_college_test}")
        logger.info(f"✓ College verses saved: {edited_verses_college_test}")
        print("✓ College edition complete")
        
        # =========================================================================
        # STEP 4: Combined DOCX
        # =========================================================================
        print(f"\n{'='*80}")
        print("COMPLETING TEST - Step 4: Combined DOCX")
        print(f"{'='*80}\n")
        
        # Create/update stats file
        original_stats_file = output_path / "psalm_027_pipeline_stats.json"
        if original_stats_file.exists():
            with open(original_stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
        else:
            stats = {}
        
        with open(stats_test_file, 'w', encoding='utf-8') as f:
            test_stats = stats.copy() if stats else {}
            test_stats['test_run'] = True
            test_stats['prompt_modifications'] = ['hook-first', 'unique-findings', 'verse-relationship', 'question-rewriting']
            json.dump(test_stats, f, ensure_ascii=False, indent=2)
        
        # Generate combined docx
        generator = CombinedDocumentGenerator(
            psalm_num=psalm_number,
            main_intro_path=edited_intro_test,
            main_verses_path=edited_verses_test,
            college_intro_path=edited_intro_college_test,
            college_verses_path=edited_verses_college_test,
            stats_path=stats_test_file,
            output_path=combined_docx_test,
            reader_questions_path=refined_questions_file if refined_questions_file.exists() else reader_questions_file
        )
        generator.generate()
        
        logger.info(f"✓ Combined DOCX saved: {combined_docx_test}")
        print(f"✓ Combined DOCX: {combined_docx_test}")
        
        # Summary
        print(f"\n{'='*80}")
        print("TEST COMPLETE")
        print(f"{'='*80}\n")
        print(f"Output: {combined_docx_test}")
        print("\nCost summary:")
        cost_tracker.print_summary()
        
    finally:
        me_module.COLLEGE_EDITOR_PROMPT_V2 = original_college_prompt
        logger.info("Restored original prompts")


if __name__ == '__main__':
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    main()
