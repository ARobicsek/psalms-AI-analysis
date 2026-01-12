"""
Engagement Test Pipeline Runner

This script runs the synthesis and master editor steps with MODIFIED PROMPTS
for A/B testing of engagement improvements. It generates outputs with "_test" suffix.

Usage:
    python scripts/run_engagement_test.py PSALM_NUMBER

Example:
    python scripts/run_engagement_test.py 27

The script will:
- Load existing macro/micro analysis and research bundle
- Run synthesis with modified prompts (hook-first, unique findings)
- Run master editor with modified prompts (hook-first, question harmonization)
- Generate outputs with "_test" suffix for comparison
"""

import sys
import os
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.synthesis_writer import SynthesisWriter, INTRODUCTION_ESSAY_PROMPT, VERSE_COMMENTARY_PROMPT
from src.agents.master_editor import MasterEditorV2, MASTER_EDITOR_PROMPT_V2, COLLEGE_EDITOR_PROMPT_V2
from src.schemas.analysis_schemas import load_macro_analysis, load_micro_analysis
from src.utils.logger import get_logger
from src.utils.cost_tracker import CostTracker


# =============================================================================
# MODIFIED PROMPTS (Engagement Improvements)
# =============================================================================

# Hook instruction to prepend to synthesis introduction prompt
HOOK_INSTRUCTION = """
**HOOK FIRST—AND CONNECT TO READER QUESTIONS**: Open with something surprising, counterintuitive, or puzzling about this psalm—an oddity in the text, a tension between verses, an unexpected image. Look at the READER QUESTIONS provided—your hook should set up one or more of these questions. Avoid bland summary openings like "Psalm 24 is a threshold poem..."

"""

# Unique findings instruction to add after item 7 in synthesis prompt
UNIQUE_FINDINGS_INSTRUCTION = """
8. **SURFACE UNIQUE FINDINGS** (the "only here" factor)
   - When the research reveals something rare (hapax, unusual construction, "appears nowhere else"), HIGHLIGHT it
   - When liturgical usage recontextualizes the verse surprisingly, SHOW the surprise
   - These moments make this commentary distinctive

"""

# Strengthened verse relationship note
VERSE_RELATIONSHIP_REPLACEMENT = """- **Relationship to Introduction Essay**: Your verse commentary should COMPLEMENT (not repeat) the introduction. If the intro made a point about a verse, add something NEW here—a different commentator's view, a liturgical deployment not mentioned, a textual variant, a specific philological oddity. Ask: "What can I say that the intro didn't?"
"""

# Question rewriting instruction for Master Editor
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


def extract_refined_questions(verse_content: str) -> list:
    """
    Extract refined reader questions from Master Editor verse commentary output.
    
    Looks for a section starting with "### REFINED READER QUESTIONS" and extracts
    numbered questions from it.
    
    Returns:
        List of question strings, or empty list if none found.
    """
    import re
    
    # Look for the refined questions section
    marker = "### REFINED READER QUESTIONS"
    if marker not in verse_content:
        return []
    
    # Extract the section after the marker
    parts = verse_content.split(marker)
    if len(parts) < 2:
        return []
    
    questions_section = parts[1]
    
    # Find numbered questions (1. Question text, 2. Question text, etc.)
    # Stop at the next section header (##) or end of content
    next_header = re.search(r'\n##', questions_section)
    if next_header:
        questions_section = questions_section[:next_header.start()]
    
    # Extract numbered lines
    questions = []
    for line in questions_section.strip().split('\n'):
        line = line.strip()
        # Match lines starting with a number and period
        match = re.match(r'^(\d+)\.\s+(.+)$', line)
        if match:
            question_text = match.group(2).strip()
            if question_text and len(question_text) > 10:  # Filter out placeholder text
                questions.append(question_text)
    
    return questions


def patch_synthesis_prompt(original_prompt: str, reader_questions: str = "") -> str:
    """
    Modify the synthesis introduction prompt with engagement improvements.
    """
    # Find where "## YOUR TASK: WRITE INTRODUCTION ESSAY" starts
    task_marker = "## YOUR TASK: WRITE INTRODUCTION ESSAY"
    if task_marker not in original_prompt:
        # Fallback: just prepend the hook instruction
        return HOOK_INSTRUCTION + original_prompt
    
    # Insert hook instruction right after the task section header
    parts = original_prompt.split(task_marker)
    
    # Find the first numbered item and insert before it
    after_task = parts[1]
    lines = after_task.split("\n")
    
    # Find line with "1. **Engages" and insert before
    new_lines = []
    inserted = False
    for line in lines:
        if not inserted and "1. **Engages" in line:
            new_lines.append(HOOK_INSTRUCTION.strip())
            new_lines.append("")
            inserted = True
        new_lines.append(line)
    
    # Also add unique findings instruction after item 7
    result_text = "\n".join(new_lines)
    
    # Find "7. **SHOWS evidence" and insert unique findings after its block
    if "7. **SHOWS evidence through generous quotation**" in result_text:
        # Insert after the quotation section (before "8. **Writes for")
        result_text = result_text.replace(
            "8. **Writes for an educated general reader**",
            UNIQUE_FINDINGS_INSTRUCTION + "\n9. **Writes for an educated general reader**"
        )
    
    # Add reader questions to the end of research materials section
    if reader_questions and "### RESEARCH MATERIALS" in result_text:
        result_text = result_text.replace(
            "### RESEARCH MATERIALS",
            f"### READER QUESTIONS\n{reader_questions}\n\n### RESEARCH MATERIALS"
        )
    
    return parts[0] + task_marker + result_text


def patch_verse_commentary_prompt(original_prompt: str) -> str:
    """
    Strengthen the verse/intro relationship note in verse commentary prompt.
    """
    # Replace the weak relationship note with the stronger one
    old_note = "- **Relationship to Introduction Essay**: You have the complete introduction essay. Your verse commentary should COMPLEMENT (not repeat) the introduction."
    
    if old_note in original_prompt:
        return original_prompt.replace(old_note, VERSE_RELATIONSHIP_REPLACEMENT.strip())
    
    return original_prompt


def patch_master_editor_prompt(original_prompt: str, reader_questions: str = "") -> str:
    """
    Modify the master editor prompt with engagement improvements.
    """
    modified = original_prompt
    
    # Add hook requirement at top of "Create an essay that:" list
    hook_line = "- **Opens with a hook related to READER QUESTIONS**—a puzzle or paradox that sets up the questions readers have seen\n"
    
    if "Create an essay that:" in modified:
        modified = modified.replace(
            "Create an essay that:\n- Gives readers",
            f"Create an essay that:\n{hook_line}- Gives readers"
        )
    
    # Add hook check to editorial criteria (section 4. STRUCTURAL ISSUES)
    if "- Introduction and verse commentary repeat each other" in modified:
        modified = modified.replace(
            "- Introduction and verse commentary repeat each other (they should complement)",
            "- Introduction and verse commentary repeat each other (they should complement—check that verse commentaries add NEW information not covered in intro)\n- Does the introduction open with a hook/puzzle (not a bland summary)?"
        )
    
    # Add reader questions more prominently
    if reader_questions and "### READER QUESTIONS" in modified:
        # Already has reader questions section - make it more prominent
        pass
    elif reader_questions:
        # Add reader questions section before research bundle
        modified = modified.replace(
            "### FULL RESEARCH BUNDLE",
            f"### ORIGINAL READER QUESTIONS (from early analysis - you may refine these)\n{reader_questions}\n\n### FULL RESEARCH BUNDLE"
        )
    
    # Add question rewriting instruction before the output format section
    if "## OUTPUT FORMAT" in modified:
        modified = modified.replace(
            "## OUTPUT FORMAT",
            QUESTION_REWRITING_INSTRUCTION + "\n\n## OUTPUT FORMAT"
        )
    
    # Update the output format to include refined questions
    if "### REVISED VERSE COMMENTARY" in modified and "### REFINED READER QUESTIONS" not in modified:
        if "[Continue for all verses...]" in modified:
            modified = modified.replace(
                "[Continue for all verses...]",
                "[Continue for all verses...]\n\n### REFINED READER QUESTIONS\n1. [First refined question]\n2. [Second refined question]\n..."
            )
    
    return modified


def run_engagement_test(psalm_number: int, output_dir: str = None):
    """
    Run synthesis and master editor with modified prompts for engagement testing.
    """
    logger = get_logger("engagement_test")
    logger.info(f"=" * 80)
    logger.info(f"ENGAGEMENT TEST PIPELINE - Psalm {psalm_number}")
    logger.info(f"=" * 80)
    
    # Initialize cost tracker
    cost_tracker = CostTracker()
    
    # Determine output directory
    if not output_dir:
        output_dir = f"output/psalm_{psalm_number}"
    output_path = Path(output_dir)
    
    if not output_path.exists():
        logger.error(f"Output directory does not exist: {output_path}")
        print(f"ERROR: Output directory does not exist: {output_path}")
        print("Run the regular pipeline first to generate macro/micro analysis.")
        sys.exit(1)
    
    # Check required files
    macro_file = output_path / f"psalm_{psalm_number:03d}_macro.json"
    micro_file = output_path / f"psalm_{psalm_number:03d}_micro_v2.json"
    research_file = output_path / f"psalm_{psalm_number:03d}_research_v2.md"
    reader_questions_file = output_path / f"psalm_{psalm_number:03d}_reader_questions.json"
    
    missing_files = []
    for f in [macro_file, micro_file, research_file]:
        if not f.exists():
            missing_files.append(str(f))
    
    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        print(f"ERROR: Missing required files:")
        for f in missing_files:
            print(f"  - {f}")
        print("\nRun the regular pipeline first to generate these files.")
        sys.exit(1)
    
    # Load existing analysis
    logger.info("Loading existing analysis files...")
    macro_analysis = load_macro_analysis(str(macro_file))
    micro_analysis = load_micro_analysis(str(micro_file))
    
    with open(research_file, 'r', encoding='utf-8') as f:
        research_bundle_content = f.read()
    
    # Load reader questions if available
    reader_questions = ""
    if reader_questions_file.exists():
        with open(reader_questions_file, 'r', encoding='utf-8') as f:
            rq_data = json.load(f)
        questions = rq_data.get('curated_questions', [])
        if questions:
            reader_questions = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
            logger.info(f"Loaded {len(questions)} reader questions")
    
    # =========================================================================
    # Patch the prompts at module level
    # =========================================================================
    import src.agents.synthesis_writer as sw_module
    import src.agents.master_editor as me_module
    
    # Store originals
    original_intro_prompt = sw_module.INTRODUCTION_ESSAY_PROMPT
    original_verse_prompt = sw_module.VERSE_COMMENTARY_PROMPT
    original_master_prompt = me_module.MASTER_EDITOR_PROMPT_V2
    original_college_prompt = me_module.COLLEGE_EDITOR_PROMPT_V2
    
    # Apply patches
    sw_module.INTRODUCTION_ESSAY_PROMPT = patch_synthesis_prompt(original_intro_prompt, reader_questions)
    sw_module.VERSE_COMMENTARY_PROMPT = patch_verse_commentary_prompt(original_verse_prompt)
    me_module.MASTER_EDITOR_PROMPT_V2 = patch_master_editor_prompt(original_master_prompt, reader_questions)
    me_module.COLLEGE_EDITOR_PROMPT_V2 = patch_master_editor_prompt(original_college_prompt, reader_questions)
    
    logger.info("Applied prompt modifications for engagement testing")
    
    # Test output file paths
    synthesis_intro_test = output_path / f"psalm_{psalm_number:03d}_synthesis_intro_test.md"
    synthesis_verses_test = output_path / f"psalm_{psalm_number:03d}_synthesis_verses_test.md"
    edited_intro_test = output_path / f"psalm_{psalm_number:03d}_edited_intro_test.md"
    edited_verses_test = output_path / f"psalm_{psalm_number:03d}_edited_verses_test.md"
    edited_assessment_test = output_path / f"psalm_{psalm_number:03d}_assessment_test.md"
    edited_intro_college_test = output_path / f"psalm_{psalm_number:03d}_edited_intro_college_test.md"
    edited_verses_college_test = output_path / f"psalm_{psalm_number:03d}_edited_verses_college_test.md"
    combined_docx_test = output_path / f"psalm_{psalm_number:03d}_commentary_combined_test.docx"
    stats_test_file = output_path / f"psalm_{psalm_number:03d}_pipeline_stats_test.json"
    
    try:
        # =====================================================================
        # STEP 1: Synthesis with modified prompts
        # =====================================================================
        print(f"\n{'='*80}")
        print(f"ENGAGEMENT TEST - Step 1: Synthesis (Modified Prompts)")
        print(f"{'='*80}\n")
        
        synthesis_writer = SynthesisWriter(cost_tracker=cost_tracker)
        commentary = synthesis_writer.write_commentary(
            macro_analysis=macro_analysis,
            micro_analysis=micro_analysis,
            research_bundle_content=research_bundle_content,
            psalm_number=psalm_number
        )
        
        # Save synthesis outputs
        with open(synthesis_intro_test, 'w', encoding='utf-8') as f:
            f.write(commentary['introduction'])
        with open(synthesis_verses_test, 'w', encoding='utf-8') as f:
            f.write(commentary['verse_commentary'])
        
        logger.info(f"✓ Synthesis intro saved: {synthesis_intro_test}")
        logger.info(f"✓ Synthesis verses saved: {synthesis_verses_test}")
        print(f"✓ Synthesis complete (test outputs)")
        
        # Rate limit delay
        print("Waiting 120 seconds before master editor...")
        time.sleep(120)
        
        # =====================================================================
        # STEP 2: Master Editor with modified prompts
        # =====================================================================
        print(f"\n{'='*80}")
        print(f"ENGAGEMENT TEST - Step 2: Master Editor (Modified Prompts)")
        print(f"{'='*80}\n")
        
        # Need to re-import the class with patched prompts
        from src.agents.master_editor import MasterEditorV2
        
        # Also create psalm text file if needed
        psalm_text_file = output_path / f"psalm_{psalm_number:03d}_text.md"
        
        master_editor = MasterEditorV2(main_model="gpt-5.1", cost_tracker=cost_tracker)
        result = master_editor.edit_commentary(
            introduction_file=synthesis_intro_test,
            verse_file=synthesis_verses_test,
            research_file=research_file,
            macro_file=macro_file,
            micro_file=micro_file,
            psalm_text_file=psalm_text_file if psalm_text_file.exists() else None,
            psalm_number=psalm_number,
            reader_questions_file=reader_questions_file if reader_questions_file.exists() else None
        )
        
        # Save main outputs
        with open(edited_intro_test, 'w', encoding='utf-8') as f:
            f.write(result['revised_introduction'])
        with open(edited_verses_test, 'w', encoding='utf-8') as f:
            f.write(result['revised_verses'])
        with open(edited_assessment_test, 'w', encoding='utf-8') as f:
            f.write(result['assessment'])
        
        # Extract and save refined reader questions
        refined_questions_file = output_path / f"psalm_{psalm_number:03d}_reader_questions_test.json"
        refined_questions = extract_refined_questions(result['revised_verses'])
        
        if refined_questions:
            logger.info(f"  ✓ Extracted {len(refined_questions)} refined questions from Master Editor output")
            # Save refined questions
            with open(refined_questions_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'psalm_number': psalm_number,
                    'curated_questions': refined_questions,
                    'source': 'master_editor_refined'
                }, f, ensure_ascii=False, indent=2)
            print(f"✓ Refined questions saved: {refined_questions_file}")
        else:
            logger.warning("No refined questions found in Master Editor output")
            # Fall back to original questions for combined doc
            refined_questions_file = reader_questions_file
        
        logger.info(f"✓ Main intro saved: {edited_intro_test}")
        logger.info(f"✓ Main verses saved: {edited_verses_test}")
        print(f"✓ Main edition complete (test outputs)")
        
        # Rate limit delay
        print("Waiting 120 seconds before college edition...")
        time.sleep(120)
        
        # =====================================================================
        # STEP 3: College Edition with modified prompts
        # =====================================================================
        print(f"\n{'='*80}")
        print(f"ENGAGEMENT TEST - Step 3: College Edition (Modified Prompts)")
        print(f"{'='*80}\n")
        
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
        print(f"✓ College edition complete (test outputs)")
        
        # =====================================================================
        # STEP 4: Generate Combined DOCX
        # =====================================================================
        print(f"\n{'='*80}")
        print(f"ENGAGEMENT TEST - Step 4: Combined DOCX")
        print(f"{'='*80}\n")
        
        from src.utils.combined_document_generator import CombinedDocumentGenerator
        
        # Load stats from original pipeline run
        original_stats_file = output_path / f"psalm_{psalm_number:03d}_pipeline_stats.json"
        if original_stats_file.exists():
            with open(original_stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
        else:
            stats = {}
        
        # Save test stats
        with open(stats_test_file, 'w', encoding='utf-8') as f:
            test_stats = stats.copy() if stats else {}
            test_stats['test_run'] = True
            test_stats['prompt_modifications'] = ['hook-first', 'unique-findings', 'verse-relationship', 'question-harmonization']
            json.dump(test_stats, f, ensure_ascii=False, indent=2)
        
        generator = CombinedDocumentGenerator(
            psalm_num=psalm_number,
            main_intro_path=edited_intro_test,
            main_verses_path=edited_verses_test,
            college_intro_path=edited_intro_college_test,
            college_verses_path=edited_verses_college_test,
            stats_path=stats_test_file,
            output_path=combined_docx_test,
            reader_questions_path=refined_questions_file if refined_questions_file.exists() else None
        )
        generator.generate()
        
        logger.info(f"✓ Combined DOCX saved: {combined_docx_test}")
        print(f"✓ Combined DOCX: {combined_docx_test}")
        
        # =====================================================================
        # Summary
        # =====================================================================
        print(f"\n{'='*80}")
        print(f"ENGAGEMENT TEST COMPLETE")
        print(f"{'='*80}\n")
        print(f"Test outputs (compare with baseline):")
        print(f"  Main intro:    {edited_intro_test}")
        print(f"  Main verses:   {edited_verses_test}")
        print(f"  College intro: {edited_intro_college_test}")
        print(f"  College verses:{edited_verses_college_test}")
        print(f"  Combined DOCX: {combined_docx_test}")
        print()
        print("Cost summary:")
        cost_tracker.print_summary()
        
    finally:
        # Restore original prompts
        sw_module.INTRODUCTION_ESSAY_PROMPT = original_intro_prompt
        sw_module.VERSE_COMMENTARY_PROMPT = original_verse_prompt
        me_module.MASTER_EDITOR_PROMPT_V2 = original_master_prompt
        me_module.COLLEGE_EDITOR_PROMPT_V2 = original_college_prompt
        logger.info("Restored original prompts")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run engagement test pipeline with modified prompts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_engagement_test.py 27
  python scripts/run_engagement_test.py 27 --output-dir output/psalm_27
        """
    )
    
    parser.add_argument('psalm_number', type=int, help='Psalm number (1-150)')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory (default: output/psalm_NNN)')
    
    args = parser.parse_args()
    
    # Ensure UTF-8 encoding on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    
    try:
        run_engagement_test(args.psalm_number, args.output_dir)
        return 0
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n\nError in test: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
