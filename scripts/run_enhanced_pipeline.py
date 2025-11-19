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
import json
import argparse
from pathlib import Path
import subprocess
import openai

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.macro_analyst import MacroAnalyst
from src.agents.micro_analyst import MicroAnalystV2
from src.agents.synthesis_writer import SynthesisWriter
from src.agents.master_editor import MasterEditor
from src.schemas.analysis_schemas import MacroAnalysis, MicroAnalysis, VerseCommentary, StructuralDivision, load_macro_analysis
from src.utils.logger import get_logger
from src.utils.pipeline_summary import PipelineSummaryTracker


def _parse_related_psalms_from_markdown(markdown_content: str) -> list:
    """
    Parse the related psalms section from a research bundle markdown file.

    Extracts psalm numbers from the "Related Psalms Analysis" section.
    Expected format: "### Psalm XX (Connection Score: ...)"

    Args:
        markdown_content: The full research bundle markdown text

    Returns:
        List of psalm numbers (as integers)
    """
    import re

    related_psalms = []

    # Look for the "Related Psalms Analysis" section
    if "## Related Psalms Analysis" not in markdown_content:
        return related_psalms

    # Find the section start
    start_match = re.search(r'## Related Psalms Analysis', markdown_content)
    if not start_match:
        return related_psalms

    start_pos = start_match.end()

    # Find the next ## heading (exactly ##, not ###, ####, etc.)
    end_match = re.search(r'\n## [^#]', markdown_content[start_pos:])
    if end_match:
        end_pos = start_pos + end_match.start()
        related_section = markdown_content[start_pos:end_pos]
    else:
        # No next section found, go to end of document
        related_section = markdown_content[start_pos:]

    # Find all psalm headers: "### Psalm XX (Connection Score: ...)"
    psalm_matches = re.findall(r'### Psalm (\d+)', related_section)

    for psalm_num_str in psalm_matches:
        try:
            psalm_num = int(psalm_num_str)
            related_psalms.append(psalm_num)
        except ValueError:
            pass

    return related_psalms


def run_enhanced_pipeline(
    psalm_number: int,
    output_dir: str = "output",
    db_path: str = "database/tanakh.db",
    delay_between_steps: int = 120,
    skip_macro: bool = False,
    skip_micro: bool = False,
    skip_synthesis: bool = False,
    skip_master_edit: bool = False,
    skip_print_ready: bool = False,
    skip_word_doc: bool = False,
    smoke_test: bool = False,
    skip_default_commentaries: bool = False
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
        skip_word_doc: Skip .docx generation
        smoke_test: Run in smoke test mode (generates dummy data, no API calls)
        skip_default_commentaries: Use selective commentary mode (only request for specific verses)
    """
    logger = get_logger("enhanced_pipeline")
    logger.info(f"=" * 80)
    logger.info(f"ENHANCED PIPELINE - Psalm {psalm_number}")
    if smoke_test:
        logger.info("SMOKE TEST MODE ENABLED - NO API CALLS WILL BE MADE")
    logger.info(f"=" * 80)

    # --- Initialize Pipeline Summary Tracker (with resume capability) ---
    output_path = Path(output_dir)
    summary_json_file = output_path / f"psalm_{psalm_number:03d}_pipeline_stats.json"
    
    # Check if we are resuming a run (any skip flag is true)
    is_resuming = any([skip_macro, skip_micro, skip_synthesis, skip_master_edit, skip_print_ready, skip_word_doc]) and not smoke_test

    initial_data = None
    if is_resuming and summary_json_file.exists():
        try:
            logger.info(f"Resuming pipeline run. Loading existing stats from {summary_json_file}")
            with open(summary_json_file, 'r', encoding='utf-8') as f:
                initial_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing stats file, starting fresh. Error: {e}")

    tracker = PipelineSummaryTracker(psalm_number=psalm_number, initial_data=initial_data)
    logger.info("Pipeline summary tracking enabled.")

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
    docx_output_file = output_path / f"psalm_{psalm_number:03d}_commentary.docx"

    # =====================================================================
    # STEP 1: Macro Analysis
    # =====================================================================
    if smoke_test:
        logger.info("\n[STEP 1] SMOKE TEST: Generating dummy MacroAnalyst output...")
        print(f"\n{'='*80}")
        print(f"STEP 1: SMOKE TEST - Macro Analysis")
        print(f"{'='*80}\n")
        step_start = time.time()

        dummy_macro = MacroAnalysis(
            psalm_number=psalm_number,
            thesis_statement="This is a smoke test thesis.",
            genre="Smoke Test Genre",
            historical_context="Smoke test historical context.",
            structural_outline=[StructuralDivision(section="v. 1", theme="Smoke test theme")],
            research_questions=["Is this a smoke test?"]
        )
        from src.schemas.analysis_schemas import save_analysis
        save_analysis(dummy_macro, str(macro_file), format="json")

        tracker.track_verse_count(5) # Dummy value
        tracker.track_step_input("macro_analysis", "Smoke test input")
        macro_output = dummy_macro.to_markdown()
        step_duration = time.time() - step_start
        tracker.track_step_output("macro_analysis", macro_output, duration=step_duration)
        tracker.track_model_for_step("macro_analysis", "smoke-test-model-macro")
        tracker.track_macro_questions(dummy_macro.research_questions)

        logger.info(f"✓ SMOKE TEST: Dummy macro analysis saved to {macro_file}")
        print(f"✓ SMOKE TEST: Dummy macro analysis complete: {macro_file}\n")

    elif not skip_macro or not macro_file.exists():
        logger.info("\n[STEP 1] Running MacroAnalyst...")
        print(f"\n{'='*80}")
        print(f"STEP 1: Macro Analysis (Structural Thesis)")
        print(f"{'='*80}\n")

        step_start = time.time()

        # Get psalm text for input tracking
        from src.data_sources.tanakh_database import TanakhDatabase
        db = TanakhDatabase(Path(db_path))
        psalm = db.get_psalm(psalm_number)
        if psalm:
            tracker.track_verse_count(len(psalm.verses))
            # Track approximate input (psalm text)
            psalm_text = "\n".join([f"{v.verse}: {v.hebrew} / {v.english}" for v in psalm.verses])
            tracker.track_step_input("macro_analysis", psalm_text)

        macro_analyst = MacroAnalyst()
        macro_model = macro_analyst.model
        macro_analysis = macro_analyst.analyze_psalm(psalm_number)

        # Save macro analysis
        from src.schemas.analysis_schemas import save_analysis
        save_analysis(macro_analysis, str(macro_file), format="json")

        # Track output
        macro_output = macro_analysis.to_markdown()
        step_duration = time.time() - step_start
        tracker.track_step_output("macro_analysis", macro_output, duration=step_duration)
        tracker.track_model_for_step("macro_analysis", macro_model)

        # Track macro questions
        if macro_analysis.research_questions:
            tracker.track_macro_questions(macro_analysis.research_questions)

        logger.info(f"✓ Macro analysis saved to {macro_file}")
        print(f"✓ Macro analysis complete: {macro_file}\n")

        # Rate limit delay
        time.sleep(delay_between_steps)
    else:
        logger.info(f"[STEP 1] Skipping macro analysis (using existing {macro_file})")
        print(f"\nSkipping Step 1 (using existing macro analysis)\n")
        # Still need to get model name for tracking
        macro_analyst = MacroAnalyst()
        macro_model = macro_analyst.model
        tracker.track_model_for_step("macro_analysis", macro_model)

    # Load macro analysis
    macro_analysis = load_macro_analysis(str(macro_file))

    # =====================================================================
    # STEP 2: Micro Analysis (Enhanced Figurative Search)
    # =====================================================================
    if smoke_test:
        logger.info("\n[STEP 2] SMOKE TEST: Generating dummy MicroAnalyst output...")
        print(f"\n{'='*80}")
        print(f"STEP 2: SMOKE TEST - Micro Analysis")
        print(f"{'='*80}\n")
        step_start = time.time()

        dummy_micro = MicroAnalysis(
            psalm_number=psalm_number,
            verse_commentaries=[VerseCommentary(verse_number=1, commentary="Smoke test commentary.")],
            thematic_threads=["Smoke test theme"],
            interesting_questions=["Is this a smoke test?"]
        )
        dummy_research_bundle = "# Smoke Test Research Bundle\n\nThis is a dummy research bundle."

        from src.schemas.analysis_schemas import save_analysis
        save_analysis(dummy_micro, str(micro_file), format="json")
        with open(research_file, 'w', encoding='utf-8') as f:
            f.write(dummy_research_bundle)

        tracker.track_step_input("micro_analysis", "Smoke test input")
        micro_output = dummy_micro.to_markdown() + "\n\n" + dummy_research_bundle
        step_duration = time.time() - step_start
        tracker.track_step_output("micro_analysis", micro_output, duration=step_duration)
        tracker.track_model_for_step("micro_analysis", "smoke-test-model-micro")
        # Dummy tracking for research bundle
        # The following line is commented out because the track_research_bundle expects a ResearchBundle object
        # and creating one would require more imports and setup. For a smoke test, this is not essential.
        # tracker.track_research_bundle(dummy_research_bundle) 
        tracker.track_research_bundle_size(len(dummy_research_bundle), len(dummy_research_bundle) // 3)
        tracker.track_micro_questions(dummy_micro.interesting_questions)

        logger.info(f"✓ SMOKE TEST: Dummy micro analysis saved to {micro_file}")
        logger.info(f"✓ SMOKE TEST: Dummy research bundle saved to {research_file}")
        print(f"✓ SMOKE TEST: Dummy micro analysis complete: {micro_file}")
        print(f"✓ SMOKE TEST: Dummy research bundle complete: {research_file}\n")

    elif not skip_micro or not micro_file.exists():
        logger.info("\n[STEP 2] Running MicroAnalyst v2 (with enhanced figurative search)...")
        print(f"\n{'='*80}")
        print(f"STEP 2: Micro Analysis (Discovery + Enhanced Research)")
        print(f"{'='*80}\n")

        step_start = time.time()

        # Track input (macro analysis)
        tracker.track_step_input("micro_analysis", macro_analysis.to_markdown())

        # Determine commentary mode based on flag
        commentary_mode = "selective" if skip_default_commentaries else "all"
        logger.info(f"  Using commentary mode: {commentary_mode}")

        micro_analyst = MicroAnalystV2(db_path=db_path, commentary_mode=commentary_mode)
        micro_model = micro_analyst.model
        micro_analysis, research_bundle = micro_analyst.analyze_psalm(
            psalm_number,
            macro_analysis
        )

        # Save outputs
        from src.schemas.analysis_schemas import save_analysis
        save_analysis(micro_analysis, str(micro_file), format="json")

        with open(research_file, 'w', encoding='utf-8') as f:
            f.write(research_bundle.to_markdown())

        # Track output
        micro_output = micro_analysis.to_markdown() + "\n\n" + research_bundle.to_markdown()
        step_duration = time.time() - step_start
        tracker.track_step_output("micro_analysis", micro_output, duration=step_duration)
        tracker.track_model_for_step("micro_analysis", micro_model)

        # Track research requests and bundle
        tracker.track_research_requests(research_bundle.request)
        tracker.track_research_bundle(research_bundle)

        # Track research bundle size
        research_bundle_text = research_bundle.to_markdown()
        tracker.track_research_bundle_size(
            len(research_bundle_text),
            len(research_bundle_text) // 3  # Estimate ~3 chars per token
        )

        # Track micro questions
        if micro_analysis.interesting_questions:
            tracker.track_micro_questions(micro_analysis.interesting_questions)

        logger.info(f"✓ Micro analysis saved to {micro_file}")
        logger.info(f"✓ Research bundle saved to {research_file}")
        print(f"✓ Micro analysis complete: {micro_file}")
        print(f"✓ Research bundle complete: {research_file}\n")

        # Rate limit delay
        time.sleep(delay_between_steps)
    else:
        logger.info(f"[STEP 2] Skipping micro analysis (loading existing files)")
        print(f"\nSkipping Step 2 (using existing micro analysis)\n")
        # Still need to get model name for tracking
        commentary_mode = "selective" if skip_default_commentaries else "all"
        micro_analyst = MicroAnalystV2(db_path=db_path, commentary_mode=commentary_mode)
        micro_model = micro_analyst.model
        tracker.track_model_for_step("micro_analysis", micro_model)
    
    # Always load the definitive micro_analysis and research_bundle for subsequent steps
    try:
        from src.schemas.analysis_schemas import load_micro_analysis
        micro_analysis = load_micro_analysis(str(micro_file))
        with open(research_file, 'r', encoding='utf-8') as f:
            research_bundle_content = f.read()
        logger.info(f"Successfully loaded {micro_file} and {research_file} for subsequent steps.")

        # If we skipped micro analysis, we need to manually extract related psalms data from the markdown
        # so it gets captured in pipeline stats
        if skip_micro:
            related_psalms = _parse_related_psalms_from_markdown(research_bundle_content)
            if related_psalms:
                tracker.research.related_psalms_count = len(related_psalms)
                tracker.research.related_psalms_list = related_psalms
                logger.info(f"Extracted {len(related_psalms)} related psalms from research bundle markdown")
                # Save immediately so the update persists
                tracker.save_json(str(output_path))
                logger.info(f"Saved updated stats with related psalms data")
    except Exception as e:
        logger.error(f"FATAL: Could not load micro analysis or research file: {e}")
        print(f"⚠ FATAL: Could not load required analysis files. Exiting.")
        sys.exit(1)


    # =====================================================================
    # STEP 3: Synthesis (Enhanced Prompts)
    # =====================================================================
    if smoke_test:
        logger.info("\n[STEP 3] SMOKE TEST: Generating dummy SynthesisWriter output...")
        print(f"\n{'='*80}")
        print(f"STEP 3: SMOKE TEST - Synthesis")
        print(f"{'='*80}\n")
        step_start = time.time()

        dummy_intro = "# Smoke Test Introduction\n\nThis is a dummy introduction."
        dummy_verses = "# Smoke Test Verse Commentary\n\nThis is dummy verse commentary."

        with open(synthesis_intro_file, 'w', encoding='utf-8') as f:
            f.write(dummy_intro)
        with open(synthesis_verses_file, 'w', encoding='utf-8') as f:
            f.write(dummy_verses)

        tracker.track_step_input("synthesis", "Smoke test input")
        synthesis_output = dummy_intro + "\n\n" + dummy_verses
        step_duration = time.time() - step_start
        tracker.track_step_output("synthesis", synthesis_output, duration=step_duration)
        tracker.track_model_for_step("synthesis", "smoke-test-model-synthesis")

        logger.info(f"✓ SMOKE TEST: Dummy introduction saved to {synthesis_intro_file}")
        logger.info(f"✓ SMOKE TEST: Dummy verse commentary saved to {synthesis_verses_file}")
        print(f"✓ SMOKE TEST: Dummy introduction complete: {synthesis_intro_file}")
        print(f"✓ SMOKE TEST: Dummy verse commentary complete: {synthesis_verses_file}\n")

    elif not skip_synthesis or not synthesis_intro_file.exists():
        logger.info("\n[STEP 3] Running SynthesisWriter (with enhanced prompts)...")
        print(f"\n{'='*80}")
        print(f"STEP 3: Synthesis (Introduction + Verse Commentary)")
        print(f"{'='*80}\n")

        step_start = time.time()

        # Track input (macro + micro + research)
        synthesis_input = macro_analysis.to_markdown() + "\n\n" + micro_analysis.to_markdown() + "\n\n" + research_bundle_content
        tracker.track_step_input("synthesis", synthesis_input)

        synthesis_writer = SynthesisWriter()
        synthesis_model = synthesis_writer.model
        commentary = synthesis_writer.write_commentary(
            macro_analysis=macro_analysis,
            micro_analysis=micro_analysis,
            research_bundle_content=research_bundle_content,
            psalm_number=psalm_number
        )

        # Save outputs
        with open(synthesis_intro_file, 'w', encoding='utf-8') as f:
            f.write(commentary['introduction'])

        with open(synthesis_verses_file, 'w', encoding='utf-8') as f:
            f.write(commentary['verse_commentary'])

        # Track output
        synthesis_output = commentary['introduction'] + "\n\n" + commentary['verse_commentary']
        step_duration = time.time() - step_start
        tracker.track_step_output("synthesis", synthesis_output, duration=step_duration)
        tracker.track_model_for_step("synthesis", synthesis_model)

        logger.info(f"✓ Introduction saved to {synthesis_intro_file}")
        logger.info(f"✓ Verse commentary saved to {synthesis_verses_file}")
        print(f"✓ Introduction complete: {synthesis_intro_file}")
        print(f"✓ Verse commentary complete: {synthesis_verses_file}\n")

        # Rate limit delay
        time.sleep(delay_between_steps)
    else:
        logger.info(f"[STEP 3] Skipping synthesis (using existing {synthesis_intro_file})")
        print(f"\nSkipping Step 3 (using existing synthesis)\n")
        # Still need to get model name for tracking
        synthesis_writer = SynthesisWriter()
        synthesis_model = synthesis_writer.model
        tracker.track_model_for_step("synthesis", synthesis_model)

    # =====================================================================
    # STEP 4: Master Editor (GPT-5) - NEW!
    # =====================================================================
    if smoke_test:
        logger.info("\n[STEP 4] SMOKE TEST: Generating dummy MasterEditor output...")
        print(f"\n{'='*80}")
        print(f"STEP 4: SMOKE TEST - Master Editor")
        print(f"{'='*80}\n")
        step_start = time.time()

        dummy_assessment = "# Smoke Test Assessment\n\nThis is a dummy assessment."
        dummy_revised_intro = "# Smoke Test Revised Introduction\n\nThis is a dummy revised introduction."
        dummy_revised_verses = "# Smoke Test Revised Verse Commentary\n\nThis is dummy revised verse commentary."

        with open(edited_assessment_file, 'w', encoding='utf-8') as f:
            f.write(dummy_assessment)
        with open(edited_intro_file, 'w', encoding='utf-8') as f:
            f.write(dummy_revised_intro)
        with open(edited_verses_file, 'w', encoding='utf-8') as f:
            f.write(dummy_revised_verses)

        tracker.track_step_input("master_editor", "Smoke test input")
        editor_output = dummy_assessment + "\n\n" + dummy_revised_intro + "\n\n" + dummy_revised_verses
        step_duration = time.time() - step_start
        tracker.track_step_output("master_editor", editor_output, duration=step_duration)
        tracker.track_model_for_step("master_editor", "smoke-test-model-editor")

        logger.info(f"✓ SMOKE TEST: Dummy assessment saved to {edited_assessment_file}")
        logger.info(f"✓ SMOKE TEST: Dummy revised introduction saved to {edited_intro_file}")
        logger.info(f"✓ SMOKE TEST: Dummy revised verses saved to {edited_verses_file}")
        print(f"✓ SMOKE TEST: Dummy assessment complete: {edited_assessment_file}")
        print(f"✓ SMOKE TEST: Dummy revised introduction complete: {edited_intro_file}")
        print(f"✓ SMOKE TEST: Dummy revised verses complete: {edited_verses_file}\n")

        tracker.mark_pipeline_complete()
        summary_json_file = tracker.save_json(str(output_path))
        logger.info(f"Analysis complete. Statistics with completion date saved to {summary_json_file}")

    elif not skip_master_edit or not edited_intro_file.exists():
        logger.info("\n[STEP 4] Running MasterEditor (GPT-5) for final editorial review...")
        print(f"\n{'='*80}")
        print(f"STEP 4: Master Editorial Review (GPT-5)")
        print(f"{'='*80}\n")
        print("This step uses GPT-5 to elevate the commentary from 'good' to 'excellent'")
        print("Expected duration: 2-5 minutes\n")

        step_start = time.time()

        # Track input (ALL materials provided to master editor)
        # The master editor receives:
        # 1. Synthesis output (intro + verses)
        # 2. Full research bundle
        # 3. Macro analysis JSON
        # 4. Micro analysis JSON
        # 5. Psalm text (Hebrew/English/LXX from database)

        # Load synthesis output
        with open(synthesis_intro_file, 'r', encoding='utf-8') as f:
            intro_content = f.read()
        with open(synthesis_verses_file, 'r', encoding='utf-8') as f:
            verses_content = f.read()

        # Load research bundle
        with open(research_file, 'r', encoding='utf-8') as f:
            research_content = f.read()

        # Load and format macro and micro analyses to match what the MasterEditor actually receives
        from src.agents.master_editor import MasterEditor as EditorFormatter
        formatter = EditorFormatter() # Use a dummy instance for formatting
        with open(macro_file, 'r', encoding='utf-8') as f:
            macro_data = json.load(f)
            macro_formatted_content = formatter._format_analysis_for_prompt(macro_data, "macro")
        with open(micro_file, 'r', encoding='utf-8') as f:
            micro_data = json.load(f)
            micro_formatted_content = formatter._format_analysis_for_prompt(micro_data, "micro")

        # Get psalm text (same as master editor does)
        from src.data_sources.tanakh_database import TanakhDatabase
        from src.agents.rag_manager import RAGManager
        db = TanakhDatabase(Path(db_path))
        rag = RAGManager("docs")
        psalm = db.get_psalm(psalm_number)
        rag_context = rag.get_rag_context(psalm_number)
        psalm_text_content = ""
        if psalm:
            psalm_lines = [f"# Psalm {psalm_number}\n"]
            lxx_verses = {}
            if rag_context and rag_context.lxx_text:
                for line in rag_context.lxx_text.split('\n'):
                    if line.startswith('v'):
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            verse_num = int(parts[0][1:])
                            lxx_verses[verse_num] = parts[1].strip()
            for verse in psalm.verses:
                psalm_lines.append(f"\n## Verse {verse.verse}")
                psalm_lines.append(f"**Hebrew:** {verse.hebrew}")
                psalm_lines.append(f"**English:** {verse.english}")
                if verse.verse in lxx_verses:
                    psalm_lines.append(f"**LXX (Greek):** {lxx_verses[verse.verse]}")
            psalm_text_content = "\n".join(psalm_lines)

        # Get analytical framework content (same as master editor does)
        analytical_framework_content = ""
        try:
            analytical_framework_content = rag.get_analytical_framework()
        except Exception as e:
            logger.warning(f"Could not load analytical framework for tracking: {e}")

        # Combine ALL inputs that master editor receives
        editor_input = (
            intro_content + "\n\n" +
            verses_content + "\n\n" +
            research_content + "\n\n" +
            macro_formatted_content + "\n\n" +
            micro_formatted_content + "\n\n" +
            psalm_text_content + "\n\n" +
            analytical_framework_content
        )
        tracker.track_step_input("master_editor", editor_input)

        master_editor = MasterEditor()
        editor_model = master_editor.model
        try:
            result = master_editor.edit_commentary(
                introduction_file=synthesis_intro_file,
                verse_file=synthesis_verses_file,
                research_file=research_file,
                macro_file=macro_file,
                micro_file=micro_file,
                psalm_number=psalm_number
            )
        except openai.RateLimitError as e:
            logger.error(f"PIPELINE HALTED: OpenAI API quota exceeded during Master Editor step. {e}")
            print(f"\n⚠️ PIPELINE HALTED: OpenAI API quota exceeded. Please check your plan and billing details.")
            sys.exit(1) # Exit gracefully

        # Save outputs
        with open(edited_assessment_file, 'w', encoding='utf-8') as f:
            f.write(f"# Editorial Assessment - Psalm {psalm_number}\n\n")
            f.write(result['assessment'])

        with open(edited_intro_file, 'w', encoding='utf-8') as f:
            f.write(result['revised_introduction'])

        with open(edited_verses_file, 'w', encoding='utf-8') as f:
            f.write(result['revised_verses'])

        # Track output
        editor_output = result['assessment'] + "\n\n" + result['revised_introduction'] + "\n\n" + result['revised_verses']
        step_duration = time.time() - step_start
        tracker.track_step_output("master_editor", editor_output, duration=step_duration)
        tracker.track_model_for_step("master_editor", editor_model)

        logger.info(f"✓ Editorial assessment saved to {edited_assessment_file}")
        logger.info(f"✓ Revised introduction saved to {edited_intro_file}")
        logger.info(f"✓ Revised verses saved to {edited_verses_file}")
        print(f"✓ Editorial assessment: {edited_assessment_file}")
        print(f"✓ Revised introduction: {edited_intro_file}")
        print(f"✓ Revised verses: {edited_verses_file}\n")

        # Rate limit delay
        time.sleep(delay_between_steps)

        # --- Mark analysis complete and save stats ---
        # This is the correct place to set the "Date Produced" timestamp,
        # as the MasterEditor has just finished its work.
        tracker.mark_pipeline_complete()
        summary_json_file = tracker.save_json(str(output_path))
        logger.info(f"Analysis complete. Statistics with completion date saved to {summary_json_file}")
    else:
        logger.info(f"[STEP 4] Skipping master edit (using existing {edited_intro_file})")
        print(f"\nSkipping Step 4 (using existing master-edited files)\n")
        # Still need to get model name for tracking
        master_editor = MasterEditor()
        editor_model = master_editor.model
        tracker.track_model_for_step("master_editor", editor_model)

        # If resuming, preserve the original completion date
        if is_resuming and initial_data:
            existing_date = initial_data.get('steps', {}).get('master_editor', {}).get('completion_date')
            if existing_date:
                logger.info(f"Preserving existing completion date: {existing_date}")
                tracker.track_completion_date(existing_date)

    # If skipping, we still need to ensure the summary file is defined for later steps
    if not summary_json_file.exists():
        logger.warning(f"Stats file {summary_json_file} not found. Saving current tracker state.")
        summary_json_file = tracker.save_json(str(output_path))
        
    # =====================================================================
    # STEP 5: Print-Ready Formatting
    # =====================================================================
    if not skip_print_ready:
        summary_json_file = output_path / f"psalm_{psalm_number:03d}_pipeline_stats.json"
        if not summary_json_file.exists():
            # If it doesn't exist, generate a temporary one.
            logger.warning(f"Pipeline summary JSON not found at {summary_json_file}. Generating temporary summary for formatter.")
            tracker.save_json(str(output_path))

        # Define paths for the formatter
        print_ready_file = output_path / f"psalm_{psalm_number:03d}_print_ready.md"

        logger.info("\n[STEP 5] Creating print-ready formatted output...")
        print(f"\n{'='*80}")
        print(f"STEP 5: Print-Ready Formatting")
        print(f"{'='*80}\n")

        intro_to_format = edited_intro_file if edited_intro_file.exists() else synthesis_intro_file
        verses_to_format = edited_verses_file if edited_verses_file.exists() else synthesis_verses_file

        command = [
            sys.executable,
            str(Path(__file__).parent.parent / "src" / "utils" / "commentary_formatter.py"),
            "--psalm", str(psalm_number),
            "--intro", str(intro_to_format),
            "--verses", str(verses_to_format),
            "--summary", str(summary_json_file),
            "--output", str(print_ready_file),
            "--db-path", db_path
        ]

        try:
            logger.info(f"Running formatter command: {' '.join(command)}")
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            logger.info("Formatter stdout:\n" + result.stdout)
            if result.stderr:
                logger.warning("Formatter stderr:\n" + result.stderr)
            logger.info(f"✓ Print-ready commentary saved to {print_ready_file}")
            print(f"✓ Print-ready commentary: {print_ready_file}\n")
        except Exception as e:
            logger.error(f"Error creating print-ready commentary: {e}", exc_info=True)
            if isinstance(e, subprocess.CalledProcessError):
                logger.error(f"Formatter failed with stdout:\n{e.stdout}")
                logger.error(f"Formatter failed with stderr:\n{e.stderr}")
            print(f"⚠ Error in print-ready formatting (see logs for details)\n")
    else:
        logger.info(f"[STEP 5] Skipping print-ready formatting")
        print_ready_file = output_path / f"psalm_{psalm_number:03d}_print_ready.md" # Define for return dict
        print(f"\nSkipping Step 5 (print-ready formatting)\n")

    # =====================================================================
    # STEP 6: Generate .docx Document
    # =====================================================================
    if not skip_word_doc:
        logger.info("\n[STEP 6] Creating .docx document...")
        print(f"\n{'='*80}")
        print(f"STEP 6: Generating Word Document (.docx)")
        print(f"{'='*80}\n")

        from src.utils.document_generator import DocumentGenerator

        summary_json_file = output_path / f"psalm_{psalm_number:03d}_pipeline_stats.json"

        # Use the same logic as the print-ready formatter to select input files
        intro_for_docx = edited_intro_file if edited_intro_file.exists() else synthesis_intro_file
        verses_for_docx = edited_verses_file if edited_verses_file.exists() else synthesis_verses_file

        if intro_for_docx.exists() and verses_for_docx.exists() and summary_json_file.exists():
            try:
                generator = DocumentGenerator(
                    psalm_num=psalm_number,
                    intro_path=intro_for_docx,
                    verses_path=verses_for_docx,
                    stats_path=summary_json_file,
                    output_path=docx_output_file
                )
                generator.generate()
                logger.info(f"Successfully generated Word document for Psalm {psalm_number}.")
                print(f"✓ Word document commentary: {docx_output_file}\n")
            except Exception as e:
                logger.error(f"Failed to generate .docx file for Psalm {psalm_number}: {e}", exc_info=True)
                print(f"⚠ Error in Word document generation (see logs for details)\n")
        else:
            logger.warning("Skipping .docx generation because input files (markdown or stats) were not found.")
            print(f"⚠ Skipping Word document generation: input files not found.\n")
    else:
        logger.info(f"[STEP 6] Skipping .docx generation")
        print(f"\nSkipping Step 6 (.docx generation)\n")



    # =====================================================================
    # COMPLETE - Generate Pipeline Summary
    # FINAL REPORTING
    # =====================================================================
    logger.info(f"\n{'=' * 80}")
    logger.info(f"ENHANCED PIPELINE COMPLETE - Psalm {psalm_number}")
    logger.info(f"{'=' * 80}\n")

    logger.info("\n[SUMMARY] Generating pipeline summary report...")
    try:
        summary_file = tracker.save_report(str(output_path))
        logger.info(f"✓ Pipeline summary saved to {summary_file}")
        # The final stats JSON is already saved in the Master Editor step
        summary_json = summary_json_file
        logger.info(f"✓ Pipeline statistics can be found at {summary_json}")
        print(f"\n✓ Pipeline summary: {summary_file}")
        print(f"✓ Pipeline statistics: {summary_json}")
    except Exception as e:
        logger.error(f"Error generating pipeline summary: {e}")
        print(f"\n⚠ Warning: Could not generate pipeline summary: {e}")

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
        'print_ready': print_ready_file,
        'word_document': docx_output_file,
        'pipeline_summary': str(summary_json_file).replace('.json', '.md'),
        'pipeline_stats': str(summary_json_file)
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
    parser.add_argument('--skip-word-doc', action='store_true',
                       help='Skip the final .docx generation step')
    parser.add_argument('--smoke-test', action='store_true',
                       help='Run in smoke test mode (generates dummy data, no API calls)')
    parser.add_argument('--skip-default-commentaries', action='store_true',
                       help='Use selective commentary mode (only request commentaries for specific verses instead of all verses)')

    args = parser.parse_args()

    # Set output directory
    if not args.output_dir:
        args.output_dir = f"output/psalm_{args.psalm_number}"

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
            skip_print_ready=args.skip_print_ready,
            skip_word_doc=args.skip_word_doc,
            smoke_test=args.smoke_test,
            skip_default_commentaries=args.skip_default_commentaries
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
